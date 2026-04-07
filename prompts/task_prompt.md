# Air Quality Station Audit

You are a senior data analyst auditing a network of air quality monitoring stations.
The network consists of 20 stations spread across 4 zones: north, south, east, west.

You have two files:
- `stations.csv` - static metadata about each station
- `readings.csv` - hourly PM2.5 readings for 7 days (January 2024)

## Context

City authorities suspect that some stations are producing **unreliable PM2.5 readings that underestimate actual pollution levels**. Your job is to identify which stations should be excluded from official air quality reports.

A station should be flagged as anomalous if it matches **any** of the following definitions:

---

### Definition 1 - Frozen sensor
A station has a malfunctioning sensor if it reports the **same PM2.5 value for 6 or more consecutive hours**.

---

### Definition 2 - Systematic underreporting
A station systematically underreports if its **median PM2.5 during peak pollution hours is below 65% of its zone's median**, where:
- Peak pollution hours are: 7, 8, 9, 16, 17, 18
- The comparison must be made **within the same zone** (north / south / east / west), not globally
- Only include readings where `wind_speed <= 4.0 m/s` to exclude natural wind dispersion effects

---

### Definition 3 - Wind-dependent underreporting
A station underreports due to its exposed location if **both** conditions hold:
- Its median PM2.5 when `wind_speed > 4.0 m/s` is **below 75% of its zone's median** at the same wind condition
- Its median PM2.5 when `wind_speed <= 4.0 m/s` is **above 65% of its zone's median** at the same wind condition

This identifies stations that read normally in calm conditions but underreport when it is windy.

---

## Instructions

1. Load both CSV files
2. Apply all three definitions independently
3. A station is anomalous if it matches **at least one** definition
4. Exclude stations already flagged as frozen (Definition 1) from the checks in Definitions 2 and 3

## Expected output

Print **only** a Python list of anomalous station IDs, sorted alphabetically, with no other text:

```
["S01", "S02", ...]
```