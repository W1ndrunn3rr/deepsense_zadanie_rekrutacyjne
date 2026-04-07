from sklearn.metrics import f1_score
import argparse
import json

ANOMALOUS_STATIONS = {"S04", "S09", "S13", "S05", "S15", "S20"}
ALL_STATIONS = {f"S{i:02d}" for i in range(1, 21)}


def score(llm_answer: set) -> float:
    """
    Compute F1 score between LLM answer and ground truth.
    llm_answer: set of station_id strings the LLM flagged as anomalous
    Returns float in [0.0, 1.0]
    """

    all_ids = sorted(ALL_STATIONS)
    y_true = [1 if s in ANOMALOUS_STATIONS else 0 for s in all_ids]
    y_pred = [1 if s in llm_answer else 0 for s in all_ids]
    return round(f1_score(y_true, y_pred), 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score LLM anomaly detection answer")
    parser.add_argument(
        "stations",
        metavar="JSON_ARRAY",
        help='JSON array of station IDs, e.g. \'["S06", "S11", "S20"]\'',
    )
    args = parser.parse_args()
    print(f"LLM task score: {score(set(json.loads(args.stations)))}")
