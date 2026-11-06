"""Train and evaluate the TensorWage salary model using only Python's stdlib.

Run from the repository root: python backend/train_model.py
"""

import csv
import hashlib
import json
import pickle
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from salary_model import fit_ridge


HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "Salary Data.csv"
MODEL_PATH = HERE / "model.pkl"
INFO_PATH = HERE / "model_info.json"
MODEL_FEATURES = ("Years of Experience", "Education Level", "Job Title")
REQUIRED_FIELDS = ("Age", "Gender", *MODEL_FEATURES, "Salary")
MIN_ANNUAL_SALARY = 10_000


def load_records():
    with DATA_PATH.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        records = []
        missing_rows = 0
        for raw in reader:
            record = {key.strip(): (value or "").strip() for key, value in raw.items() if key}
            if not all(record.get(field) for field in REQUIRED_FIELDS):
                missing_rows += 1
                continue
            try:
                record["Age"] = int(float(record["Age"]))
                record["Years of Experience"] = float(record["Years of Experience"])
                record["Salary"] = float(record["Salary"])
            except (TypeError, ValueError):
                missing_rows += 1
                continue
            records.append(record)
    return records, missing_rows


def signature(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def metrics(rows, model):
    actual = [float(row["Salary"]) for row in rows]
    predicted = [model.predict_one(row) for row in rows]
    errors = [prediction - observed for prediction, observed in zip(predicted, actual)]
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = (sum(error * error for error in errors) / len(errors)) ** 0.5
    mean = sum(actual) / len(actual)
    total = sum((value - mean) ** 2 for value in actual)
    residual = sum(error * error for error in errors)
    return {
        "rows": len(rows),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(1.0 - residual / total, 4) if total else None,
    }, predicted


def grouped_mae(rows, predicted, key_fn, minimum_group_size=8):
    grouped = defaultdict(list)
    for row, estimate in zip(rows, predicted):
        grouped[key_fn(row)].append(abs(estimate - float(row["Salary"])))
    return {
        key: {"rows": len(values), "mae": round(sum(values) / len(values), 2)}
        for key, values in sorted(grouped.items())
        if key and len(values) >= minimum_group_size
    }


def main():
    raw_records, missing_rows = load_records()
    exact_unique = {}
    for record in raw_records:
        exact_unique.setdefault(signature(record), record)
    unique_records = list(exact_unique.values())
    outliers = [record for record in unique_records if record["Salary"] < MIN_ANNUAL_SALARY]
    eligible_records = [record for record in unique_records if record["Salary"] >= MIN_ANNUAL_SALARY]

    train_records = []
    test_records = []
    for record in eligible_records:
        bucket = int(hashlib.sha256(signature(record).encode("utf-8")).hexdigest()[:8], 16) % 5
        (test_records if bucket == 0 else train_records).append(record)
    if len(train_records) < 30 or len(test_records) < 10:
        raise RuntimeError("Not enough distinct records for a useful holdout evaluation.")

    model = fit_ridge(train_records)
    holdout, predictions = metrics(test_records, model)
    group_metrics = {
        "gender_audit_only": grouped_mae(test_records, predictions, lambda row: row["Gender"]),
        "age_band_audit_only": grouped_mae(
            test_records,
            predictions,
            lambda row: "23-34" if row["Age"] <= 34 else "35-44" if row["Age"] <= 44 else "45-53",
        ),
    }
    title_counts = Counter(record["Job Title"] for record in eligible_records)
    file_hash = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    info = {
        "model_name": "TensorWage Ridge salary baseline",
        "model_version": "1.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "algorithm": "Ridge regression with one-hot job title and education features",
        "features_used": list(MODEL_FEATURES),
        "demographic_fields_used_for_prediction": [],
        "evaluation": {
            "method": "Deterministic 80/20 holdout grouped by exact record; metrics are diagnostics, not a guarantee.",
            "holdout": holdout,
            "group_error_audit": group_metrics,
        },
        "data": {
            "source": "Salary Data.csv supplied with this project",
            "source_provenance": "Original publisher and license are not recorded in the project.",
            "sha256": file_hash,
            "raw_rows": len(raw_records) + missing_rows,
            "rows_missing_or_invalid": missing_rows,
            "valid_rows_before_deduplication": len(raw_records),
            "exact_duplicate_rows_removed": len(raw_records) - len(unique_records),
            "distinct_records_after_deduplication": len(unique_records),
            "training_records_after_quality_screen": len(eligible_records),
            "holdout_records": len(test_records),
            "job_title_count": len(title_counts),
            "job_titles_with_fewer_than_five_records": sum(count < 5 for count in title_counts.values()),
            "excluded_records": [
                {
                    "job_title": record["Job Title"],
                    "salary_value": record["Salary"],
                    "reason": "Below the $10,000 annual-salary quality floor; retained in source file, excluded from training and averages.",
                }
                for record in outliers
            ],
            "currency": "Not specified in supplied file; the UI's USD display is provisional.",
            "geography": "Not present in supplied file; no local-market claim is supported.",
            "company_and_level": "Not present in supplied file.",
            "data_as_of": None,
            "status": "Demo data only; not a current or geographically scoped market benchmark.",
        },
    }

    with MODEL_PATH.open("wb") as output:
        pickle.dump(model, output, protocol=pickle.HIGHEST_PROTOCOL)
    INFO_PATH.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"model": MODEL_PATH.name, "metadata": INFO_PATH.name, "evaluation": holdout, "group_error_audit": group_metrics, "data": info["data"]}, indent=2))


if __name__ == "__main__":
    main()
