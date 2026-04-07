# Air Quality Station Audit - LLM Benchmark Task

A benchmark task designed to partially challenge large language models on multi-step data analysis. Claude Sonnet 4.6 was chosen as the primary target model — strong enough to solve most of the task but expected to miss the wind-dependent underreporting pattern (Definition 3). Claude Opus 4.6 was included as an upper bound reference.
Sonnet 4.6 scored **0.80**, Opus 4.6 scored **0.91**.

## Dataset

### `stations.csv` - 20 rows

| Column | Type | Description |
|---|---|---|
| `station_id` | string | S01–S20 |
| `zone` | string | `north` / `south` / `east` / `west` (5 stations each) |
| `elevation_m` | int | Elevation in meters - noise column, irrelevant |
| `installed_year` | int | Year of installation - noise column, irrelevant |

### `readings.csv` - 3 360 rows (20 stations × 7 days × 24h)

| Column | Type | Description |
|---|---|---|
| `station_id` | string | Foreign key to stations.csv |
| `timestamp` | datetime | Hourly, 2026-01-01 to 2026-01-07 |
| `pm25` | float | PM2.5 concentration in $\mu g/m^3$ - main variable |
| `pm10` | float | PM10 concentration - correlated with PM2.5 + noise |
| `wind_speed` | float | Wind speed in $m/s$ |
| `temperature` | float | Temperature in celcius C  - noise column, irrelevant |

The dataset covers Wrocław in January 2026. Temperature ranges from –6 C to +6 C.
PM2.5 follows a realistic daily cycle with morning (7–9h) and evening (16–18h) peaks,
and lower values on weekends.

---

## Ground truth (hidden from LLM)

```python
ANOMALOUS_STATIONS = {
    "S04": "park",        # Systematically low PM2.5 - trees filter air
    "S09": "park",
    "S13": "park",
    "S05": "open_field",  # Low PM2.5 only when wind_speed > 4.0 m/s
    "S15": "open_field",
    "S20": "faulty",      # Frozen sensor - same value for 6h blocks
}
```

The dataset does not contain a `location_type` column. The LLM must infer anomalous
stations purely from the numerical patterns in the readings.

---

## Task Prompt

The full prompt is in `task_prompt.md`. In short, the LLM is asked to identify stations
that should be excluded from official air quality reports, based on three definitions:

**Definition 1 - Frozen sensor**
A station reports the same PM2.5 value for 6 or more consecutive hours.

**Definition 2 - Systematic underreporting**
A station's median PM2.5 during peak hours (7–9h, 16–18h) at low wind (≤ 4.0 m/s)
is below **65%** of its zone's median under the same conditions.

**Definition 3 - Wind-dependent underreporting**
A station's median PM2.5 at wind > 4.0 m/s is below **75%** of its zone's median,
AND its median at wind ≤ 4.0 m/s is above **65%** of its zone's median.
This catches stations in exposed locations that read normally in calm conditions
but underreport when wind disperses pollution.

The expected output is a sorted Python list printed to stdout:
```
["S04", "S09", ...]
```

---

## Scoring

### Measure

**F1-score** over the set of 20 station IDs, treating anomaly detection as binary classification.

```python
from sklearn.metrics import f1_score

GROUND_TRUTH  = {"S04", "S05", "S09", "S13", "S15", "S20"}
ALL_STATIONS  = {f"S{i:02d}" for i in range(1, 21)}

def score(llm_answer: set) -> float:
    all_ids = sorted(ALL_STATIONS)
    y_true  = [1 if s in GROUND_TRUTH else 0 for s in all_ids]
    y_pred  = [1 if s in llm_answer   else 0 for s in all_ids]
    return round(f1_score(y_true, y_pred), 2)
```

F1 was chosen over accuracy because the dataset is imbalanced (6 anomalous out of 20)
and penalises both false positives and false negatives symmetrically.

### Score reference table

| Predicted | TP | FP | FN | F1 |
|---|---|---|---|---|
| All 6 correct | 6 | 0 | 0 | **1.00** |
| S04, S09, S13, S20 (LLM output) | 4 | 0 | 2 | **0.80** |
| S04, S09, S13, S05, S15 (parks + open_field, missing faulty) | 5 | 0 | 1 | 0.91 |
| S20 only | 1 | 0 | 5 | 0.29 |
| Empty | 0 | 0 | 6 | 0.00 |

### Why 0 < score < 1

Model correctly detects:
- **S20** - frozen readings are a well-known anomaly pattern
- **S04, S09, S13** - park stations have a strong and consistent PM2.5 deficit

But in some cases:
- Sonnet 4.6 misses **S05** and **S15.**
- Opus 4.6 finds S05 but misses **S15** — the harder of the two open_field stations.

---

## Benchmark Results

| Model | Output | Score |
|---|---|---|
| Claude Sonnet 4.6 (1x tokens) | `["S04", "S09", "S13", "S20"]` | 0.80 |
| Claude Opus 4.6 (3x tokens) | `["S04", "S05", "S09", "S13", "S20"]` | 0.91 |

 The task satisfies the requirement of
score $\in$ (0, 1) and requires only a single LLM run.

---

## Reproducing the dataset

```bash
uv run scripts/create_dataset.py
```

Requires: `pandas`, `numpy`. Uses `random.seed(0)` for reproducibility.

## Running the solution

```bash
uv run scripts/solution.py
```

Requires: `pandas`, `numpy`, `scikit-learn`.

## Evaluating with score.py

Pass the LLM's answer as a JSON array of flagged station IDs:

```bash
uv run scripts/score.py '["S04", "S09", "S13", "S20"]'
```

## Dataset design notes

- No demographic biases (no age, gender, race, or socioeconomic columns)
- No trademark names
- `elevation_m` `installed_year` are deliberate noise columns - they correlate
  with nothing and are designed to distract models that do feature selection
- `temperature` is realistic for Wrocław in January but has no causal relationship
  with PM2.5 in this dataset
- `location_type` was intentionally excluded - the LLM must detect anomaly type
  from behaviour, not from labels