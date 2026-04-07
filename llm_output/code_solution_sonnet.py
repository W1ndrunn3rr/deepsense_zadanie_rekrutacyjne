import pandas as pd

stations = pd.read_csv("/mnt/user-data/uploads/stations.csv")
readings = pd.read_csv("/mnt/user-data/uploads/readings.csv")
readings["timestamp"] = pd.to_datetime(readings["timestamp"])
readings["hour"] = readings["timestamp"].dt.hour

readings = readings.merge(stations[["station_id", "zone"]], on="station_id")

# Definition 1: Frozen sensor
frozen = set()
for sid, group in readings.sort_values("timestamp").groupby("station_id"):
    vals = group["pm25"].values
    count = 1
    for i in range(1, len(vals)):
        if vals[i] == vals[i - 1]:
            count += 1
            if count >= 6:
                frozen.add(sid)
                break
        else:
            count = 1

non_frozen_readings = readings[~readings["station_id"].isin(frozen)]

# Definition 2: Systematic underreporting
peak_hours = {7, 8, 9, 16, 17, 18}
calm = non_frozen_readings[
    (non_frozen_readings["wind_speed"] <= 4.0)
    & (non_frozen_readings["hour"].isin(peak_hours))
]

zone_median_peak = calm.groupby("zone")["pm25"].median()
station_median_peak = (
    calm.groupby(["station_id", "zone"])["pm25"].median().reset_index()
)
station_median_peak.columns = ["station_id", "zone", "st_median"]
station_median_peak["zone_median"] = station_median_peak["zone"].map(zone_median_peak)

underreporting = set(
    station_median_peak[
        station_median_peak["st_median"] < 0.65 * station_median_peak["zone_median"]
    ]["station_id"]
)

# Definition 3: Wind-dependent underreporting
windy = non_frozen_readings[non_frozen_readings["wind_speed"] > 4.0]
calm_all = non_frozen_readings[non_frozen_readings["wind_speed"] <= 4.0]

zone_med_windy = windy.groupby("zone")["pm25"].median()
zone_med_calm = calm_all.groupby("zone")["pm25"].median()

st_med_windy = windy.groupby(["station_id", "zone"])["pm25"].median().reset_index()
st_med_windy.columns = ["station_id", "zone", "st_median"]
st_med_windy["zone_median"] = st_med_windy["zone"].map(zone_med_windy)

st_med_calm = calm_all.groupby(["station_id", "zone"])["pm25"].median().reset_index()
st_med_calm.columns = ["station_id", "zone", "st_median"]
st_med_calm["zone_median"] = st_med_calm["zone"].map(zone_med_calm)

wind_dep = set()
for _, row in st_med_windy.iterrows():
    sid = row["station_id"]
    calm_row = st_med_calm[st_med_calm["station_id"] == sid]
    if len(calm_row) == 0:
        continue
    calm_row = calm_row.iloc[0]
    if (
        row["st_median"] < 0.75 * row["zone_median"]
        and calm_row["st_median"] >= 0.65 * calm_row["zone_median"]
    ):
        wind_dep.add(sid)

all_anomalous = sorted(frozen | underreporting | wind_dep)
print(all_anomalous)
