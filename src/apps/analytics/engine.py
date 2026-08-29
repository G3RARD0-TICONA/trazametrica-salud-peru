from __future__ import annotations

import math
import statistics
from collections import defaultdict
from collections.abc import Sequence


def _numbers(values: Sequence[float], *, minimum: int = 1) -> list[float]:
    normalized = [float(value) for value in values]
    if len(normalized) < minimum:
        raise ValueError(f"Se requieren al menos {minimum} observaciones.")
    if not all(math.isfinite(value) for value in normalized):
        raise ValueError("Las observaciones deben ser números finitos.")
    return normalized


def _rounded(value: float) -> float:
    return round(float(value), 10)


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def descriptive_statistics(values: Sequence[float]) -> dict[str, object]:
    data = _numbers(values)
    ordered = sorted(data)
    q1 = _percentile(ordered, 0.25)
    q3 = _percentile(ordered, 0.75)
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    outliers = [
        {"index": index, "value": _rounded(value)}
        for index, value in enumerate(data)
        if value < lower_fence or value > upper_fence
    ]
    return {
        "count": len(data),
        "mean": _rounded(statistics.fmean(data)),
        "median": _rounded(statistics.median(data)),
        "minimum": _rounded(min(data)),
        "maximum": _rounded(max(data)),
        "range": _rounded(max(data) - min(data)),
        "population_stddev": _rounded(statistics.pstdev(data)),
        "q1": _rounded(q1),
        "q3": _rounded(q3),
        "iqr": _rounded(iqr),
        "lower_fence": _rounded(lower_fence),
        "upper_fence": _rounded(upper_fence),
        "outliers": outliers,
    }


def pareto_analysis(
    categories: Sequence[str], weights: Sequence[float] | None = None
) -> dict[str, object]:
    if not categories:
        raise ValueError("Pareto requiere al menos una categoría.")
    normalized_weights = _numbers(weights or [1.0] * len(categories))
    if len(categories) != len(normalized_weights):
        raise ValueError("Categorías y pesos deben tener la misma longitud.")
    if any(weight < 0 for weight in normalized_weights):
        raise ValueError("Los pesos de Pareto no pueden ser negativos.")
    totals: defaultdict[str, float] = defaultdict(float)
    for category, weight in zip(categories, normalized_weights, strict=True):
        key = str(category).strip() or "SIN-CATEGORIA"
        totals[key] += weight
    total = sum(totals.values())
    if total <= 0:
        raise ValueError("Pareto requiere un peso total mayor que cero.")
    cumulative = 0.0
    rows: list[dict[str, object]] = []
    for category, weight in sorted(totals.items(), key=lambda item: (-item[1], item[0])):
        cumulative += weight
        rows.append(
            {
                "category": category,
                "weight": _rounded(weight),
                "percentage": _rounded(weight * 100 / total),
                "cumulative_percentage": _rounded(cumulative * 100 / total),
            }
        )
    return {"total": _rounded(total), "categories": rows}


def control_chart(values: Sequence[float]) -> dict[str, object]:
    data = _numbers(values, minimum=2)
    center = statistics.fmean(data)
    sigma = statistics.pstdev(data)
    lower = center - 3 * sigma
    upper = center + 3 * sigma
    signals = [
        {"index": index, "value": _rounded(value)}
        for index, value in enumerate(data)
        if value < lower or value > upper
    ]
    return {
        "count": len(data),
        "center_line": _rounded(center),
        "lower_control_limit": _rounded(lower),
        "upper_control_limit": _rounded(upper),
        "population_sigma": _rounded(sigma),
        "signals": signals,
    }


def moving_average(values: Sequence[float], *, window: int) -> dict[str, object]:
    data = _numbers(values)
    if window < 2 or window > len(data):
        raise ValueError("La ventana debe estar entre 2 y la cantidad de observaciones.")
    points = [
        {"index": index, "value": _rounded(statistics.fmean(data[index - window : index]))}
        for index in range(window, len(data) + 1)
    ]
    return {
        "window": window,
        "points": points,
        "forecast_next": points[-1]["value"],
    }


def _split_count(count: int, test_fraction: float) -> int:
    if not 0.1 <= test_fraction <= 0.4:
        raise ValueError("La fracción de prueba debe estar entre 0.1 y 0.4.")
    train_count = int(count * (1 - test_fraction))
    if train_count < 4 or count - train_count < 2:
        raise ValueError("La separación requiere al menos 4 filas de entrenamiento y 2 de prueba.")
    return train_count


def _regression_metrics(actual: Sequence[float], predicted: Sequence[float]) -> dict[str, float]:
    errors = [observed - estimate for observed, estimate in zip(actual, predicted, strict=True)]
    mae = statistics.fmean(abs(error) for error in errors)
    mse = statistics.fmean(error * error for error in errors)
    mean_actual = statistics.fmean(actual)
    total = sum((value - mean_actual) ** 2 for value in actual)
    residual = sum(error * error for error in errors)
    r2 = 0.0 if total == 0 else 1 - residual / total
    return {"mae": _rounded(mae), "rmse": _rounded(math.sqrt(mse)), "r2": _rounded(r2)}


def linear_regression(
    x_values: Sequence[float], y_values: Sequence[float], *, test_fraction: float = 0.2
) -> dict[str, object]:
    x_data = _numbers(x_values, minimum=6)
    y_data = _numbers(y_values, minimum=6)
    if len(x_data) != len(y_data):
        raise ValueError("Las variables de regresión deben tener la misma longitud.")
    train_count = _split_count(len(x_data), test_fraction)
    x_train, y_train = x_data[:train_count], y_data[:train_count]
    x_test, y_test = x_data[train_count:], y_data[train_count:]
    x_mean = statistics.fmean(x_train)
    y_mean = statistics.fmean(y_train)
    denominator = sum((value - x_mean) ** 2 for value in x_train)
    if denominator == 0:
        raise ValueError("La variable explicativa no tiene variación.")
    slope = (
        sum(
            (x_value - x_mean) * (y_value - y_mean)
            for x_value, y_value in zip(x_train, y_train, strict=True)
        )
        / denominator
    )
    intercept = y_mean - slope * x_mean
    predicted = [intercept + slope * value for value in x_test]
    baseline = [y_mean] * len(y_test)
    metrics = _regression_metrics(y_test, predicted)
    baseline_metrics = _regression_metrics(y_test, baseline)
    return {
        "algorithm": "ordinary_least_squares",
        "intercept": _rounded(intercept),
        "slope": _rounded(slope),
        "train_count": train_count,
        "test_count": len(y_test),
        "metrics": metrics,
        "baseline_metrics": baseline_metrics,
        "quality_gate_passed": metrics["rmse"] <= baseline_metrics["rmse"],
        "predictions": [_rounded(value) for value in predicted],
    }


def _sigmoid(value: float) -> float:
    if value >= 0:
        exponential = math.exp(-value)
        return 1 / (1 + exponential)
    exponential = math.exp(value)
    return exponential / (1 + exponential)


def _classification_metrics(actual: Sequence[int], predicted: Sequence[int]) -> dict[str, object]:
    true_positive = sum(a == 1 and p == 1 for a, p in zip(actual, predicted, strict=True))
    true_negative = sum(a == 0 and p == 0 for a, p in zip(actual, predicted, strict=True))
    false_positive = sum(a == 0 and p == 1 for a, p in zip(actual, predicted, strict=True))
    false_negative = sum(a == 1 and p == 0 for a, p in zip(actual, predicted, strict=True))
    precision = (
        true_positive / (true_positive + false_positive) if true_positive + false_positive else 0
    )
    recall = (
        true_positive / (true_positive + false_negative) if true_positive + false_negative else 0
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {
        "accuracy": _rounded((true_positive + true_negative) / len(actual)),
        "precision": _rounded(precision),
        "recall": _rounded(recall),
        "f1": _rounded(f1),
        "confusion_matrix": {
            "true_positive": true_positive,
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
        },
    }


def logistic_regression(
    x_values: Sequence[float],
    labels: Sequence[int],
    *,
    test_fraction: float = 0.2,
    iterations: int = 500,
    learning_rate: float = 0.1,
) -> dict[str, object]:
    x_data = _numbers(x_values, minimum=10)
    y_data = [int(label) for label in labels]
    if len(x_data) != len(y_data) or any(label not in {0, 1} for label in y_data):
        raise ValueError("La regresión logística requiere etiquetas binarias alineadas.")
    train_count = _split_count(len(x_data), test_fraction)
    x_train, y_train = x_data[:train_count], y_data[:train_count]
    x_test, y_test = x_data[train_count:], y_data[train_count:]
    if len(set(y_train)) < 2:
        raise ValueError("El entrenamiento requiere ambas clases.")
    if not 50 <= iterations <= 2000 or not 0 < learning_rate <= 0.5:
        raise ValueError("Los hiperparámetros logísticos están fuera del rango aprobado.")
    mean_x = statistics.fmean(x_train)
    sigma_x = statistics.pstdev(x_train)
    if sigma_x == 0:
        raise ValueError("La variable explicativa no tiene variación.")
    standardized_train = [(value - mean_x) / sigma_x for value in x_train]
    intercept = 0.0
    coefficient = 0.0
    for _ in range(iterations):
        probabilities = [_sigmoid(intercept + coefficient * value) for value in standardized_train]
        intercept_gradient = statistics.fmean(
            probability - label for probability, label in zip(probabilities, y_train, strict=True)
        )
        coefficient_gradient = statistics.fmean(
            (probability - label) * value
            for probability, label, value in zip(
                probabilities, y_train, standardized_train, strict=True
            )
        )
        intercept -= learning_rate * intercept_gradient
        coefficient -= learning_rate * coefficient_gradient
    standardized_test = [(value - mean_x) / sigma_x for value in x_test]
    probabilities = [_sigmoid(intercept + coefficient * value) for value in standardized_test]
    predicted = [int(probability >= 0.5) for probability in probabilities]
    metrics = _classification_metrics(y_test, predicted)
    majority = int(sum(y_train) >= len(y_train) / 2)
    baseline_metrics = _classification_metrics(y_test, [majority] * len(y_test))
    brier = statistics.fmean(
        (probability - label) ** 2 for probability, label in zip(probabilities, y_test, strict=True)
    )
    metrics["brier"] = _rounded(brier)
    accuracy = metrics["accuracy"]
    baseline_accuracy = baseline_metrics["accuracy"]
    if not isinstance(accuracy, (int, float)) or not isinstance(baseline_accuracy, (int, float)):
        raise ValueError("Las métricas de clasificación no son numéricas.")
    return {
        "algorithm": "binary_logistic_gradient_descent",
        "intercept": _rounded(intercept),
        "coefficient": _rounded(coefficient),
        "train_count": train_count,
        "test_count": len(y_test),
        "metrics": metrics,
        "baseline_metrics": baseline_metrics,
        "quality_gate_passed": accuracy >= baseline_accuracy,
        "probabilities": [_rounded(value) for value in probabilities],
    }
