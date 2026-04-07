import pandas as pd
import numpy as np

np.random.seed(0)

ZONES = {
    "north": ["S01", "S02", "S03", "S04", "S05"],
    "south": ["S06", "S07", "S08", "S09", "S10"],
    "east": ["S11", "S12", "S13", "S14", "S15"],
    "west": ["S16", "S17", "S18", "S19", "S20"],
}


PARK_STATIONS = {"S04", "S09", "S13"}  # systematically low PM2.5
OPEN_FIELD_STATIONS = {
    "S05",
    "S15",
}  # low PM2.5 only when wind > 4.0
FAULTY_STATIONS = {"S20"}  # frozen readings every 6h

stations_rows = []
for zone, ids in ZONES.items():
    for sid in ids:
        stations_rows.append(
            {
                "station_id": sid,
                "zone": zone,
                "elevation_m": np.random.randint(50, 350),
                "installed_year": np.random.randint(2008, 2026),
            }
        )

stations_df = pd.DataFrame(stations_rows)

dates = pd.date_range("2026-01-01", periods=7 * 24, freq="h")  # 7 days, hourly


def base_pm25(timestamp: pd.Timestamp):
    hour = timestamp.hour
    is_weekend = timestamp.dayofweek >= 5

    # morning peak 7-9h, evening peak 16-18h, low at night
    if hour in (7, 8, 9):
        level = 38.0
    elif hour in (16, 17, 18):
        level = 32.0
    elif 0 <= hour <= 5:
        level = 15.0
    else:
        level = 18.0

    if is_weekend:
        level -= 10.0

    return max(level, 2.0)


ZONE_FACTOR = {"north": 1.00, "south": 1.05, "east": 0.97, "west": 1.02}


def generate_wind(hour: int, is_open_field: bool):
    base = 3.5 * np.sin(2 * np.pi * hour / 24)
    wind = base + np.random.normal(0, 0.8)
    if is_open_field:
        wind *= 1.5
    return round(float(np.clip(wind, 0, 12)), 2)


def generate_temperature(hour: int):
    # Wroclaw january: daily avg 0 C, min -3 C at 6am, max +3 C at 2pm
    temp = 3.0 * np.sin(2 * np.pi * (hour - 6) / 24)
    return round(float(temp + np.random.normal(0, 1)), 2)


frozen_value = {}  # tracks frozen reading per faulty station

readings_rows = []

for zone, ids in ZONES.items():
    for sid in ids:
        frozen_pm25 = None
        frozen_counter = 0

        for ts in dates:
            hour = ts.hour
            is_open_field = sid in OPEN_FIELD_STATIONS
            wind = generate_wind(hour, is_open_field)
            temp = generate_temperature(hour)
            base = base_pm25(ts)

            if sid in FAULTY_STATIONS:
                # frozen reading: same value for 6h, then random jump
                if frozen_counter % 6 == 0:
                    frozen_pm25 = round(float(np.random.uniform(10, 70)), 2)
                pm25 = frozen_pm25
                frozen_counter += 1

            elif sid in PARK_STATIONS:
                # always underreports — trees filter air
                pm25 = base * 0.52 + np.random.normal(0, 1.5)

            elif sid in OPEN_FIELD_STATIONS:
                # underreports only when wind disperses pollution
                if wind > 4.0:
                    pm25 = base * 0.48 + np.random.normal(0, 2.0)
                else:
                    pm25 = base * 0.97 + np.random.normal(0, 2.0)

            else:
                # normal urban station with zone adjustment
                pm25 = base * ZONE_FACTOR[zone] + np.random.normal(0, 2.0)

            pm25 = round(float(max(pm25, 0.5)), 2)
            pm10 = round(
                float(
                    max(
                        pm25 * np.random.uniform(1.4, 1.8) + np.random.normal(0, 2), 0.5
                    )
                ),
                2,
            )

            readings_rows.append(
                {
                    "station_id": sid,
                    "timestamp": ts,
                    "pm25": pm25,
                    "pm10": pm10,
                    "wind_speed": wind,
                    "temperature": temp,
                }
            )

readings_df = pd.DataFrame(readings_rows)

stations_df.to_csv("./dataset/stations.csv", index=False)
readings_df.to_csv("./dataset/readings.csv", index=False)
