import pandas as pd
from score import score

readings = pd.read_csv("./dataset/readings.csv", parse_dates=["timestamp"])
stations = pd.read_csv("./dataset/stations.csv")
zone_map = stations.set_index("station_id")["zone"].to_dict()


# Definition 1 - broken sensor
def max_frozen_run(series: pd.Series):
    max_run = current = 1
    for i in range(1, len(series)):
        current = current + 1 if series.iloc[i] == series.iloc[i - 1] else 1
        max_run = max(max_run, current)
    return max_run


frozen_runs = (
    readings.sort_values(["station_id", "timestamp"])
    .groupby("station_id")["pm25"]
    .apply(max_frozen_run)
)
faulty = set(frozen_runs[frozen_runs >= 6].index)

# Definition 2 - systematic underreporting
remaining = readings[~readings["station_id"].isin(faulty)]
peak = remaining[remaining["timestamp"].dt.hour.isin([7, 8, 9, 16, 17, 18])]
peak_not_windy = peak[peak["wind_speed"] <= 4.0]

station_median = peak_not_windy.groupby("station_id")["pm25"].median().reset_index()
station_median["zone"] = station_median["station_id"].map(zone_map)

z_med = station_median.groupby("zone")["pm25"].median().rename("zone_med")

station_median = station_median.join(z_med, on="zone")
station_median["ratio"] = station_median["pm25"] / station_median["zone_med"]
park_station = set(station_median[station_median["ratio"] < 0.65]["station_id"])

# Definition 3 - wind-dependent underreporting
remaining2 = readings[~readings["station_id"].isin(faulty | park_station)]


def zone_ratio(df, strong_wind: bool):
    sub = df[df["wind_speed"] > 4.0] if strong_wind else df[df["wind_speed"] <= 4.0]
    m = sub.groupby("station_id")["pm25"].median().reset_index()
    m["zone"] = m["station_id"].map(zone_map)
    zm = m.groupby("zone")["pm25"].median().rename("zm")
    m = m.join(zm, on="zone")
    m["ratio"] = m["pm25"] / m["zm"]
    return m.set_index("station_id")["ratio"]


hi = zone_ratio(remaining2, strong_wind=True)
lo = zone_ratio(remaining2, strong_wind=False)
open_field = set(hi[(hi < 0.75) & (lo > 0.65)].index)

anomalous = sorted(faulty | park_station | open_field)
print(f"Anomalie: {anomalous}, wynik: {score(anomalous)}")
