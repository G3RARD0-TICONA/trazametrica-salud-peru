from __future__ import annotations

import math

import pytest

from apps.analytics.engine import (
    control_chart,
    descriptive_statistics,
    linear_regression,
    logistic_regression,
    moving_average,
    pareto_analysis,
)


def test_descriptive_statistics_detects_tukey_outlier() -> None:
    result = descriptive_statistics([10, 11, 12, 12, 13, 14, 100])
    assert result["count"] == 7
    assert result["median"] == 12
    assert result["outliers"] == [{"index": 6, "value": 100.0}]


def test_descriptive_statistics_rejects_non_finite_input() -> None:
    with pytest.raises(ValueError, match="finitos"):
        descriptive_statistics([1, math.inf])


def test_pareto_orders_categories_and_calculates_cumulative_percentage() -> None:
    result = pareto_analysis(["B", "A", "B", "C"], [2, 6, 3, 1])
    rows = result["categories"]
    assert isinstance(rows, list)
    assert [row["category"] for row in rows] == ["A", "B", "C"]
    assert rows[0]["weight"] == 6
    assert rows[0]["percentage"] == 50
    assert rows[1]["cumulative_percentage"] == pytest.approx(91.6666666667)
    assert rows[-1]["cumulative_percentage"] == 100


def test_control_chart_marks_point_beyond_three_sigma() -> None:
    result = control_chart([0] * 20 + [100])
    assert result["signals"] == [{"index": 20, "value": 100.0}]


def test_control_chart_uses_population_three_sigma_limits() -> None:
    result = control_chart([2, 4, 6, 8])
    assert result["center_line"] == 5
    assert result["population_sigma"] == pytest.approx(math.sqrt(5))
    assert result["lower_control_limit"] == pytest.approx(5 - 3 * math.sqrt(5))
    assert result["upper_control_limit"] == pytest.approx(5 + 3 * math.sqrt(5))


def test_moving_average_is_deterministic() -> None:
    result = moving_average([1, 2, 3, 4, 5], window=3)
    assert result["points"] == [
        {"index": 3, "value": 2.0},
        {"index": 4, "value": 3.0},
        {"index": 5, "value": 4.0},
    ]
    assert result["forecast_next"] == 4


def test_linear_regression_uses_chronological_holdout_and_beats_baseline() -> None:
    result = linear_regression(list(range(1, 21)), [2 * value + 1 for value in range(1, 21)])
    assert result["train_count"] == 16
    assert result["test_count"] == 4
    assert result["slope"] == 2
    assert result["metrics"]["rmse"] == 0
    assert result["quality_gate_passed"] is True


def test_linear_regression_rejects_variable_without_variation() -> None:
    with pytest.raises(ValueError, match="no tiene variación"):
        linear_regression([1] * 10, list(range(10)))


def test_linear_regression_records_failed_quality_gate() -> None:
    result = linear_regression(list(range(1, 11)), [1, 2, 3, 4, 5, 6, 7, 8, 0, 0])
    assert result["quality_gate_passed"] is False
    assert result["metrics"]["rmse"] > result["baseline_metrics"]["rmse"]


def test_logistic_regression_reports_metrics_and_baseline() -> None:
    x_values = list(range(1, 31))
    labels = [0] * 15 + [1] * 15
    result = logistic_regression(x_values, labels)
    assert result["train_count"] == 24
    assert result["test_count"] == 6
    assert 0 <= result["metrics"]["accuracy"] <= 1
    assert result["quality_gate_passed"] is True


def test_logistic_regression_rejects_training_with_one_class() -> None:
    with pytest.raises(ValueError, match="ambas clases"):
        logistic_regression(list(range(20)), [0] * 20)
