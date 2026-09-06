"""Deterministic synthetic data and transparent ML-math validation contracts.

This module is intentionally separate from the governed market-data path.  It
creates labelled development data for AI/ML experiments, edge-case handling,
and reproducible mathematical checks.  It never enables the optimizer feed and
never claims that synthetic observations are market or realized evidence.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import csv
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable


SYNTHETIC_SCHEMA_VERSION = "1.0"
DEFAULT_ROW_COUNT = 10_000
DEFAULT_SEED = 20260906
DATASET_ID = "AURUM-SYNTHETIC-ML-10000-V1"
ASSETS = (
    "SPY", "QQQ", "TLT", "GLD", "IWM", "EEM", "HYG", "LQD", "VNQ", "DBC",
    "XLK", "XLF", "XLE", "XLP", "XLU", "XLI", "XLC", "XLB", "XLY", "CASH",
)
REGIMES = ("NORMAL", "TREND_UP", "VOLATILITY_CLUSTER", "STRESS", "RECOVERY")
CASE_TYPES = (
    "clean",
    "sparse_history",
    "regime_boundary",
    "liquidity_shock",
    "outlier_return",
    "missing_feature",
    "stale_timestamp",
    "duplicate_observation",
    "nonpositive_price",
    "label_noise",
    "schema_drift",
)
INVALID_CASE_TYPES = {
    "sparse_history",
    "outlier_return",
    "missing_feature",
    "stale_timestamp",
    "duplicate_observation",
    "nonpositive_price",
    "label_noise",
}
FEATURE_FIELDS = ("rolling_vol_20", "momentum_20", "drawdown_60", "stress_score", "volume_zscore")
TARGET_FIELDS = ("target_return_1", "target_regime")
CSV_FIELDS = (
    "observation_id", "timestamp", "time_index", "asset", "regime", "case_type",
    "schema_variant", "open", "high", "low", "close", "volume", "log_return_1",
    "rolling_vol_20", "momentum_20", "drawdown_60", "stress_score", "volume_zscore",
    "target_return_1", "target_regime", "quality_flags", "valid_for_training",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _std(values: Iterable[float]) -> float:
    values = list(values)
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return f"{float(value):.10f}"


def _regime_for_step(step: int) -> str:
    phase = (step % 500) // 100
    return REGIMES[min(phase, len(REGIMES) - 1)]


def _case_for_row(index: int, step: int, asset_index: int, regime: str) -> str:
    if step < 20:
        return "sparse_history"
    if step in {100, 200, 300, 400} and asset_index % 4 == 0:
        return "regime_boundary"
    marker = (index * 17 + step * 11 + asset_index * 7) % 101
    cases = {
        0: "outlier_return",
        1: "missing_feature",
        2: "stale_timestamp",
        3: "duplicate_observation",
        4: "nonpositive_price",
        5: "label_noise",
        6: "schema_drift",
    }
    if regime == "STRESS" and marker % 29 == 0:
        return "liquidity_shock"
    return cases.get(marker, "clean")


def _regime_parameters(regime: str) -> tuple[float, float]:
    return {
        "NORMAL": (0.00025, 0.008),
        "TREND_UP": (0.00100, 0.011),
        "VOLATILITY_CLUSTER": (0.00005, 0.026),
        "STRESS": (-0.00250, 0.040),
        "RECOVERY": (0.00125, 0.022),
    }[regime]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _row_to_csv(row: dict[str, Any]) -> dict[str, str]:
    text_fields = {"observation_id", "timestamp", "asset", "regime", "case_type", "schema_variant", "target_regime", "quality_flags"}
    return {field: _fmt(row.get(field)) if field not in text_fields else str(row.get(field, "") or "") for field in CSV_FIELDS}


def generate_synthetic_rows(row_count: int = DEFAULT_ROW_COUNT, seed: int = DEFAULT_SEED) -> list[dict[str, Any]]:
    """Generate exactly row_count deterministic, labelled synthetic observations."""
    if row_count < len(ASSETS):
        raise ValueError(f"row_count must be at least {len(ASSETS)}")
    rng = random.Random(seed)
    steps = math.ceil(row_count / len(ASSETS))
    state: dict[str, dict[str, Any]] = {
        asset: {"price": 100.0 + index * 2.5, "prices": [], "returns": [], "volumes": []}
        for index, asset in enumerate(ASSETS)
    }
    rows: list[dict[str, Any]] = []
    start = datetime(2020, 1, 2, tzinfo=timezone.utc)
    for index in range(row_count):
        step = index // len(ASSETS)
        asset_index = index % len(ASSETS)
        asset = ASSETS[asset_index]
        regime = _regime_for_step(step)
        case_type = _case_for_row(index, step, asset_index, regime)
        drift, volatility = _regime_parameters(regime)
        if asset == "CASH":
            drift, volatility = 0.00005, 0.0002
        raw_return = drift + (asset_index - 9.5) * 0.00003 + rng.gauss(0.0, volatility)
        if case_type == "liquidity_shock":
            raw_return -= 0.012
        observed_return = raw_return * 8.0 if case_type == "outlier_return" else raw_return
        previous_price = state[asset]["price"]
        close = max(0.0001, previous_price * math.exp(observed_return))
        volume = max(1.0, 1_000_000.0 * (1.0 + rng.gauss(0.0, 0.08)) * (0.12 if case_type == "liquidity_shock" else 1.0))
        prices = state[asset]["prices"]
        returns = state[asset]["returns"]
        volumes = state[asset]["volumes"]
        prices.append(close)
        returns.append(observed_return)
        volumes.append(volume)
        recent_returns = returns[-20:]
        recent_prices = prices[-60:]
        recent_volumes = volumes[-20:]
        rolling_vol = _std(recent_returns) if len(recent_returns) >= 5 else None
        momentum = close / prices[-21] - 1.0 if len(prices) >= 21 else None
        drawdown = close / max(recent_prices) - 1.0 if recent_prices else None
        volume_zscore = ((volume - _mean(recent_volumes)) / _std(recent_volumes)) if len(recent_volumes) >= 5 and _std(recent_volumes) else 0.0
        stress_score = min(1.0, max(0.0, 0.65 * (rolling_vol or 0.0) / 0.04 + 0.35 * max(0.0, -(momentum or 0.0)) / 0.15))
        timestamp = start + timedelta(days=step)
        if case_type == "stale_timestamp":
            timestamp -= timedelta(days=7)
        observation_id = f"{timestamp.date().isoformat()}-{asset}-{index:05d}"
        if case_type == "duplicate_observation" and rows:
            observation_id = rows[-1]["observation_id"]
        quality_flags: list[str] = []
        if step < 20:
            quality_flags.append("INSUFFICIENT_HISTORY")
        if case_type in INVALID_CASE_TYPES:
            quality_flags.append(case_type.upper())
        if case_type == "schema_drift":
            quality_flags.append("OPTIONAL_FIELD_ADDED")
        if case_type == "regime_boundary":
            quality_flags.append("REGIME_TRANSITION")
        row = {
            "observation_id": observation_id,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "time_index": step,
            "asset": asset,
            "regime": regime,
            "case_type": case_type,
            "schema_variant": "v1" if case_type != "schema_drift" else "v1_optional_extension",
            "open": previous_price,
            "high": max(previous_price, close) * (1.0 + abs(raw_return) * 0.2),
            "low": min(previous_price, close) * max(0.0001, 1.0 - abs(raw_return) * 0.2),
            "close": 0.0 if case_type == "nonpositive_price" else close,
            "volume": volume,
            "log_return_1": observed_return,
            "rolling_vol_20": rolling_vol,
            "momentum_20": None if case_type == "missing_feature" else momentum,
            "drawdown_60": drawdown,
            "stress_score": stress_score,
            "volume_zscore": volume_zscore,
            "quality_flags": ";".join(quality_flags),
        }
        rows.append(row)
        state[asset]["price"] = close
    by_key = {(int(row["time_index"]), row["asset"]): row for row in rows}
    for row in rows:
        key = (int(row["time_index"]), row["asset"])
        future = by_key.get((key[0] + 1, key[1]))
        row["target_return_1"] = future.get("log_return_1") if future else None
        row["target_regime"] = future.get("regime") if future else None
        if row["case_type"] == "label_noise" and row["target_regime"]:
            row["target_regime"] = "STRESS" if row["target_regime"] != "STRESS" else "NORMAL"
        row["valid_for_training"] = bool(
            row["case_type"] not in INVALID_CASE_TYPES
            and row["target_return_1"] is not None
            and all(row.get(field) is not None for field in FEATURE_FIELDS)
        )
    return rows


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_synthetic_dataset(path: Path, expected_rows: int = DEFAULT_ROW_COUNT) -> dict[str, Any]:
    """Validate row count, feature shape, labels, and deliberately injected cases."""
    if not path.is_file():
        return {"status": "REQUIRED", "row_count": 0, "missing": True}
    rows = _read_rows(path)
    case_counts = Counter(row.get("case_type", "") for row in rows)
    regime_counts = Counter(row.get("regime", "") for row in rows)
    missing_columns = [field for field in CSV_FIELDS if not rows or field not in rows[0]]
    malformed = 0
    for row in rows:
        for field in ("open", "high", "low", "close", "volume", "log_return_1"):
            try:
                value = float(row.get(field, ""))
                if not math.isfinite(value):
                    malformed += 1
            except ValueError:
                malformed += 1
    required_cases = sorted(set(CASE_TYPES).difference(case_counts))
    checks = {
        "exact_row_count": len(rows) == expected_rows,
        "required_columns_present": not missing_columns,
        "known_case_labels": not required_cases and all(key in CASE_TYPES for key in case_counts),
        "known_regime_labels": set(regime_counts).issubset(REGIMES),
        "numeric_market_fields_finite": malformed == 0,
    }
    return {
        "schema_version": SYNTHETIC_SCHEMA_VERSION,
        "service": "AURUM synthetic ML dataset",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "data_class": "SIMULATED_SYNTHETIC_DATA",
        "row_count": len(rows),
        "expected_row_count": expected_rows,
        "asset_count": len(set(row.get("asset") for row in rows)),
        "case_counts": dict(sorted(case_counts.items())),
        "regime_counts": dict(sorted(regime_counts.items())),
        "missing_columns": missing_columns,
        "missing_case_labels": required_cases,
        "malformed_numeric_fields": malformed,
        "checks": checks,
        "optimizer_feed_enabled": False,
        "claim_boundary": "Synthetic rows support development, AI/ML math, stress testing, and replay only; they are not live, historical, customer, or realized-performance evidence.",
    }


def generate_synthetic_dataset(root: Path, row_count: int = DEFAULT_ROW_COUNT, seed: int = DEFAULT_SEED) -> dict[str, Any]:
    output_dir = root / "artifacts" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "synthetic_ml_dataset.csv"
    rows = generate_synthetic_rows(row_count=row_count, seed=seed)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(_row_to_csv(row) for row in rows)
    validation = validate_synthetic_dataset(csv_path, expected_rows=row_count)
    manifest = {
        "schema_version": SYNTHETIC_SCHEMA_VERSION,
        "service": "AURUM synthetic ML dataset manifest",
        "dataset_id": DATASET_ID,
        "generated_at_utc": _utc_now(),
        "generator": "src/institutional/synthetic_ml.py:generate_synthetic_dataset",
        "seed": seed,
        "requested_rows": row_count,
        "actual_rows": len(rows),
        "asset_count": len(ASSETS),
        "assets": list(ASSETS),
        "regimes": list(REGIMES),
        "case_types": list(CASE_TYPES),
        "feature_fields": list(FEATURE_FIELDS),
        "target_fields": list(TARGET_FIELDS),
        "row_counts": {"total": len(rows), "training_eligible": sum(bool(row["valid_for_training"]) for row in rows)},
        "case_counts": validation.get("case_counts", {}),
        "file": "artifacts/synthetic/synthetic_ml_dataset.csv",
        "sha256": _sha256(csv_path),
        "data_class": "SIMULATED_SYNTHETIC_DATA",
        "external_fetch_performed": False,
        "optimizer_feed_enabled": False,
        "purpose": ["AI/ML feature engineering", "math validation", "edge-case testing", "replayable stress scenarios"],
        "claim_boundary": "Synthetic data is intentionally non-market data and cannot support live, historical, customer, or realized-performance claims.",
    }
    manifest_path = output_dir / "synthetic_ml_dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def build_synthetic_dataset_status(root: Path) -> dict[str, Any]:
    path = root / "artifacts" / "synthetic" / "synthetic_ml_dataset.csv"
    status = validate_synthetic_dataset(path)
    status.update({
        "generated_at_utc": _utc_now(),
        "dataset_path": "artifacts/synthetic/synthetic_ml_dataset.csv",
        "manifest_path": "artifacts/synthetic/synthetic_ml_dataset_manifest.json",
        "data_class": "SIMULATED_SYNTHETIC_DATA",
        "optimizer_feed_enabled": False,
        "external_fetch_performed": False,
    })
    return status


def _safe_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    size = len(augmented)
    for column in range(size):
        pivot = max(range(column, size), key=lambda index: abs(augmented[index][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("singular normal-equation matrix")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [left - factor * right for left, right in zip(augmented[row], augmented[column])]
    return [augmented[index][-1] for index in range(size)]


def _standardize(train: list[list[float]], test: list[list[float]]) -> tuple[list[list[float]], list[list[float]], list[float], list[float]]:
    means = [_mean(row[index] for row in train) for index in range(len(train[0]))]
    scales = [(_std(row[index] for row in train) or 1.0) for index in range(len(train[0]))]
    transform = lambda rows: [[(value - means[index]) / scales[index] for index, value in enumerate(row)] for row in rows]
    return transform(train), transform(test), means, scales


def run_synthetic_ml_validation(root: Path, ridge_lambda: float = 0.1) -> dict[str, Any]:
    """Run chronological ridge regression and nearest-centroid classification."""
    path = root / "artifacts" / "synthetic" / "synthetic_ml_dataset.csv"
    rows = _read_rows(path)
    usable = []
    excluded = Counter()
    for row in rows:
        if row.get("valid_for_training") != "true":
            excluded[row.get("case_type", "unknown")] += 1
            continue
        features = [_safe_float(row.get(field)) for field in FEATURE_FIELDS]
        target = _safe_float(row.get("target_return_1"))
        if any(value is None for value in features) or target is None:
            excluded[row.get("case_type", "unknown")] += 1
            continue
        usable.append((int(row["time_index"]), [float(value) for value in features], target, row.get("target_regime", "UNKNOWN")))
    split = max((item[0] for item in usable), default=0) * 0.70
    train = [item for item in usable if item[0] <= split]
    test = [item for item in usable if item[0] > split]
    if not train or not test:
        raise ValueError("synthetic dataset does not contain both chronological train and test rows")
    train_features, test_features, means, scales = _standardize([item[1] for item in train], [item[1] for item in test])
    dimension = len(FEATURE_FIELDS) + 1
    normal = [[0.0] * dimension for _ in range(dimension)]
    target_vector = [0.0] * dimension
    for features, (_, target) in zip(train_features, [(item[0], item[2]) for item in train]):
        vector = [1.0] + features
        for row_index in range(dimension):
            target_vector[row_index] += vector[row_index] * target
            for column_index in range(dimension):
                normal[row_index][column_index] += vector[row_index] * vector[column_index]
    for index in range(1, dimension):
        normal[index][index] += ridge_lambda
    coefficients = _solve_linear_system(normal, target_vector)
    predictions = [sum(coefficient * value for coefficient, value in zip(coefficients, [1.0] + features)) for features in test_features]
    actual = [item[2] for item in test]
    mean_actual = _mean(actual)
    mse = _mean((prediction - observed) ** 2 for prediction, observed in zip(predictions, actual))
    mae = _mean(abs(prediction - observed) for prediction, observed in zip(predictions, actual))
    total_variance = sum((observed - mean_actual) ** 2 for observed in actual)
    r_squared = 1.0 - (mse * len(actual) / total_variance) if total_variance else 0.0

    labels = sorted({item[3] for item in train})
    centroids = {label: [_mean(row[index] for row, item in zip(train_features, train) if item[3] == label) for index in range(len(FEATURE_FIELDS))] for label in labels}
    predicted_labels = []
    for features in test_features:
        predicted_labels.append(min(labels, key=lambda label: sum((features[index] - centroids[label][index]) ** 2 for index in range(len(FEATURE_FIELDS)))))
    actual_labels = [item[3] for item in test]
    correct = sum(predicted == observed for predicted, observed in zip(predicted_labels, actual_labels))
    label_counts = Counter(actual_labels)
    balanced_scores = []
    confusion = {label: {other: 0 for other in labels} for label in labels}
    for predicted, observed in zip(predicted_labels, actual_labels):
        confusion.setdefault(observed, {}).setdefault(predicted, 0)
        confusion[observed][predicted] += 1
    for label in labels:
        total = label_counts.get(label, 0)
        balanced_scores.append((sum(confusion.get(label, {}).values() and [confusion[label].get(label, 0)]) / total) if total else 0.0)
    majority_label = Counter(item[3] for item in train).most_common(1)[0][0]
    majority_accuracy = sum(label == majority_label for label in actual_labels) / len(actual_labels)
    return {
        "schema_version": SYNTHETIC_SCHEMA_VERSION,
        "service": "AURUM synthetic ML math validation",
        "generated_at_utc": _utc_now(),
        "dataset_id": DATASET_ID,
        "data_class": "SIMULATED_SYNTHETIC_DATA",
        "split": {"method": "chronological", "train_max_time_index": split, "train_rows": len(train), "test_rows": len(test), "excluded_rows": sum(excluded.values()), "excluded_by_case": dict(sorted(excluded.items()))},
        "regression": {"model": "ridge_closed_form", "features": list(FEATURE_FIELDS), "ridge_lambda": ridge_lambda, "coefficients": coefficients, "mse": mse, "mae": mae, "r_squared": r_squared, "train_feature_means": means, "train_feature_scales": scales},
        "classification": {"model": "nearest_centroid", "features": list(FEATURE_FIELDS), "labels": labels, "accuracy": correct / len(actual_labels), "balanced_accuracy": _mean(balanced_scores), "majority_baseline_accuracy": majority_accuracy, "confusion_matrix": confusion},
        "checks": {"chronological_split": True, "no_external_fetch": True, "synthetic_only": True, "optimizer_feed_enabled": False, "baseline_reported": True},
        "promotion_state": "RESEARCH_ONLY",
        "execution_enabled": False,
        "claim_boundary": "Metrics are development baselines on deterministic synthetic data; they do not validate live-market performance, causality, or investment outcomes.",
    }


def write_synthetic_ml_validation(root: Path) -> dict[str, Any]:
    result = run_synthetic_ml_validation(root)
    path = root / "artifacts" / "synthetic" / "synthetic_ml_validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
