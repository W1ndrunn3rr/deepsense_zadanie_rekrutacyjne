import pandas as pd

stations = pd.read_csv("/mnt/user-data/uploads/stations.csv")
readings = pd.read_csv("/mnt/user-data/uploads/readings.csv", parse_dates=["timestamp"])

readings = readings.merge(stations[["station_id", "zone"]], on="station_id")


# Definition 1: Frozen sensor (same PM2.5 for 6+ consecutive hours)
def has_frozen(group):
    vals = group.sort_values("timestamp")["pm25"].values
    count = 1
    for i in range(1, len(vals)):
        if vals[i] == vals[i - 1]:
            count += 1
            if count >= 6:
                return True
        else:
            count = 1
    return False


frozen = set(readings.groupby("station_id").filter(has_frozen)["station_id"].unique())

# Definitions 2 & 3 — exclude frozen stations
non_frozen = readings[~readings["station_id"].isin(frozen)]

# Definition 2: Systematic underreporting during peak hours, calm wind
peak_hours = [7, 8, 9, 16, 17, 18]
calm = non_frozen[
    (non_frozen["timestamp"].dt.hour.isin(peak_hours))
    & (non_frozen["wind_speed"] <= 4.0)
]

zone_medians_peak = calm.groupby("zone")["pm25"].median()
station_medians_peak = (
    calm.groupby(["station_id", "zone"])["pm25"].median().reset_index()
)
station_medians_peak["zone_median"] = station_medians_peak["zone"].map(
    zone_medians_peak
)
station_medians_peak["ratio"] = (
    station_medians_peak["pm25"] / station_medians_peak["zone_median"]
)

def2_flagged = set(
    station_medians_peak[station_medians_peak["ratio"] < 0.65]["station_id"]
)

# Definition 3: Wind-dependent underreporting
windy = non_frozen[non_frozen["wind_speed"] > 4.0]
calm_all = non_frozen[non_frozen["wind_speed"] <= 4.0]

zone_med_windy = windy.groupby("zone")["pm25"].median()
zone_med_calm = calm_all.groupby("zone")["pm25"].median()

stat_med_windy = windy.groupby(["station_id", "zone"])["pm25"].median().reset_index()
stat_med_calm = calm_all.groupby(["station_id", "zone"])["pm25"].median().reset_index()

stat_med_windy["zone_median"] = stat_med_windy["zone"].map(zone_med_windy)
stat_med_calm["zone_median"] = stat_med_calm["zone"].map(zone_med_calm)

stat_med_windy["ratio"] = stat_med_windy["pm25"] / stat_med_windy["zone_median"]
stat_med_calm["ratio"] = stat_med_calm["pm25"] / stat_med_calm["zone_median"]

merged3 = stat_med_windy[["station_id", "ratio"]].merge(
    stat_med_calm[["station_id", "ratio"]],
    on="station_id",
    suffixes=("_windy", "_calm"),
)

def3_flagged = set(
    merged3[(merged3["ratio_windy"] < 0.75) & (merged3["ratio_calm"] > 0.65)][
        "station_id"
    ]
)

anomalous = sorted(frozen | def2_flagged | def3_flagged)
print(anomalous)
