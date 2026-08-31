from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from apps.indicators.models import IndicatorObservation

from .models import AnalysisRun, AnalysisType
from .services import MAX_ANALYSIS_ROWS, _observations, content_hash

_WIDTH = 960
_HEIGHT = 420
_LEFT = 78
_RIGHT = 155
_TOP = 36
_BOTTOM = 66


def _verified_rows(run: AnalysisRun) -> list[IndicatorObservation] | None:
    """Reload the immutable input set and reject a visual if provenance changed."""

    rows = list(
        _observations(run.definition, run.period_start, run.period_end)[: MAX_ANALYSIS_ROWS + 1]
    )
    if len(rows) != run.input_count or len(rows) > MAX_ANALYSIS_ROWS:
        return None
    input_payload = [
        {
            "id": str(row.pk),
            "period_end": row.period_end.isoformat(),
            "period_start": row.period_start.isoformat(),
            "service_id": str(row.service_id) if row.service_id else None,
            "site_id": str(row.site_id) if row.site_id else None,
            "value": str(row.value),
        }
        for row in rows
    ]
    return rows if content_hash(input_payload) == run.input_hash else None


def _chart_geometry(
    values: list[float], *, forced_domain: tuple[float, float] | None = None
) -> dict[str, object]:
    domain_min, domain_max = forced_domain or (min(values), max(values))
    if forced_domain is None:
        padding = max((domain_max - domain_min) * 0.08, 1.0)
        domain_min -= padding
        domain_max += padding
    plot_width = _WIDTH - _LEFT - _RIGHT
    plot_height = _HEIGHT - _TOP - _BOTTOM

    def y_for(value: float) -> float:
        return _TOP + (domain_max - value) * plot_height / (domain_max - domain_min)

    return {
        "width": _WIDTH,
        "height": _HEIGHT,
        "left": _LEFT,
        "right": _WIDTH - _RIGHT,
        "top": _TOP,
        "bottom": _HEIGHT - _BOTTOM,
        "plot_width": plot_width,
        "plot_height": plot_height,
        "domain_min": domain_min,
        "domain_max": domain_max,
        "y_for": y_for,
        "gridlines": [
            {
                "value": domain_max - (domain_max - domain_min) * index / 4,
                "y": round(_TOP + plot_height * index / 4, 2),
            }
            for index in range(5)
        ],
    }


def _line_points(
    values: list[float], geometry: Mapping[str, object], *, start: int = 0
) -> list[dict[str, object]]:
    plot_width = _number(geometry, "plot_width")
    y_for = geometry["y_for"]
    if not callable(y_for):
        return []
    denominator = max(len(values) - 1, 1)
    return [
        {
            "index": start + index + 1,
            "x": round(_LEFT + index * plot_width / denominator, 2),
            "y": round(y_for(value), 2),
            "value": value,
        }
        for index, value in enumerate(values)
    ]


def _series(points: Sequence[Mapping[str, object]]) -> str:
    return " ".join(f"{point['x']},{point['y']}" for point in points)


def _metric(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def analysis_presentation(run: AnalysisRun) -> dict[str, object] | None:
    """Create an explainable visual model for every analysis except the control chart."""

    if run.definition.analysis_type == AnalysisType.CONTROL_CHART:
        return None
    rows = _verified_rows(run)
    if not rows:
        return None
    values = [float(row.value) for row in rows]
    periods = [row.period_end.isoformat() for row in rows]
    result = run.result
    analysis_type = run.definition.analysis_type

    if analysis_type == AnalysisType.DESCRIPTIVE:
        keys = ("minimum", "q1", "median", "q3", "maximum")
        try:
            five = {key: _number(result, key) for key in keys}
        except ValueError:
            return None
        low, high = min(values), max(values)
        padding = max((high - low) * 0.08, 1.0)
        domain_min, domain_max = low - padding, high + padding
        plot_width = _WIDTH - _LEFT - 50

        def x_for(value: float) -> float:
            return _LEFT + (value - domain_min) * plot_width / (domain_max - domain_min)

        outlier_indexes = {
            int(item["index"])
            for item in result.get("outliers", [])
            if isinstance(item, Mapping) and isinstance(item.get("index"), int)
        }
        non_outlier_values = [
            value for index, value in enumerate(values) if index not in outlier_indexes
        ]
        whisker_min = min(non_outlier_values or values)
        whisker_max = max(non_outlier_values or values)
        return {
            "kind": "descriptive",
            "title": "Distribución y valores atípicos",
            "explanation": (
                "La caja muestra el 50 % central de los valores; la línea interior es la "
                "mediana y los puntos rojos son atípicos."
            ),
            "cards": [
                {"label": "Observaciones", "value": len(values), "format": "integer"},
                {"label": "Promedio", "value": _number(result, "mean"), "format": "number"},
                {"label": "Mediana", "value": five["median"], "format": "number"},
                {"label": "Atípicos", "value": len(outlier_indexes), "format": "integer"},
            ],
            "method": [
                "Promedio = suma de los valores ÷ número de observaciones.",
                "Los cuartiles se obtienen por interpolación lineal con posición (n − 1) × p.",
                "RIC = Q3 − Q1; límites de Tukey = Q1 − 1.5 × RIC y Q3 + 1.5 × RIC.",
                (
                    "Un valor fuera de esos límites se marca como atípico; no se elimina "
                    "automáticamente."
                ),
            ],
            "reference": "Criterio de valores atípicos de Tukey documentado por NIST/SEMATECH.",
            "box": {
                **{key: round(x_for(value), 2) for key, value in five.items()},
                "minimum": round(x_for(whisker_min), 2),
                "maximum": round(x_for(whisker_max), 2),
                "width": round(x_for(five["q3"]) - x_for(five["q1"]), 2),
            },
            "axis": [
                {
                    "x": round(_LEFT + plot_width * index / 4, 2),
                    "value": domain_min + (domain_max - domain_min) * index / 4,
                }
                for index in range(5)
            ],
            "outliers": [
                {"x": round(x_for(value), 2), "value": value, "period": periods[index]}
                for index, value in enumerate(values)
                if index in outlier_indexes
            ],
            "rows": [
                {
                    "period": period,
                    "value": value,
                    "status": "Atípico" if index in outlier_indexes else "Dentro del rango",
                }
                for index, (period, value) in enumerate(zip(periods, values, strict=True))
            ],
        }

    if analysis_type == AnalysisType.PARETO:
        all_categories = [
            item for item in result.get("categories", []) if isinstance(item, Mapping)
        ]
        if not all_categories:
            return None
        categories: list[Mapping[str, object]] = all_categories
        geometry = _chart_geometry(
            [_metric(item, "weight") for item in categories],
            forced_domain=(0.0, max(_metric(item, "weight") for item in categories) * 1.1 or 1.0),
        )
        slot = _number(geometry, "plot_width") / len(categories)
        y_for = geometry["y_for"]
        if not callable(y_for):
            return None
        cumulative = []
        bars = []
        for index, item in enumerate(categories):
            weight = _metric(item, "weight")
            x = _LEFT + index * slot + slot * 0.16
            bars.append(
                {
                    "x": round(x, 2),
                    "y": round(y_for(weight), 2),
                    "width": round(slot * 0.68, 2),
                    "height": round(_number(geometry, "bottom") - y_for(weight), 2),
                    "label": item.get("category", ""),
                    "value": weight,
                }
            )
            cumulative.append(
                {
                    "x": round(_LEFT + index * slot + slot / 2, 2),
                    "y": round(
                        _TOP
                        + (100 - _metric(item, "cumulative_percentage"))
                        * _number(geometry, "plot_height")
                        / 100,
                        2,
                    ),
                    "value": _metric(item, "cumulative_percentage"),
                }
            )
        top = categories[0]
        return {
            **{key: value for key, value in geometry.items() if key != "y_for"},
            "kind": "pareto",
            "title": "Pareto por servicio",
            "explanation": (
                "Las barras ordenan de mayor a menor la magnitud absoluta acumulada del KPI "
                "por servicio. La línea naranja muestra el porcentaje acumulado."
            ),
            "cards": [
                {
                    "label": "Magnitud total",
                    "value": _number(result, "total"),
                    "format": "number",
                },
                {"label": "Servicios", "value": len(all_categories), "format": "integer"},
                {
                    "label": "Mayor contribución",
                    "value": _metric(top, "percentage"),
                    "format": "percent",
                },
            ],
            "method": [
                "Se agrupan las observaciones por servicio.",
                "Contribución del servicio = suma de |valor KPI| de sus observaciones.",
                "Las contribuciones se ordenan de mayor a menor.",
                "Porcentaje = contribución ÷ contribución total × 100.",
                "Porcentaje acumulado = suma progresiva de los porcentajes ordenados.",
            ],
            "reference": (
                "Pareto ponderado: ASQ admite que la longitud de las barras represente "
                "frecuencia o una medida de impacto/costo."
            ),
            "bars": bars,
            "cumulative": cumulative,
            "cumulative_polyline": _series(cumulative),
            "rows": all_categories,
        }

    if analysis_type == AnalysisType.MOVING_AVERAGE:
        averages = [item for item in result.get("points", []) if isinstance(item, Mapping)]
        average_values = [_metric(item, "value") for item in averages]
        if not average_values:
            return None
        geometry = _chart_geometry(values + average_values)
        actual_points = _line_points(values, geometry)
        y_for = geometry["y_for"]
        if not callable(y_for):
            return None
        trend_plot_width = _number(geometry, "plot_width")
        average_points = [
            {
                "index": int(_metric(item, "index")),
                "x": round(
                    _LEFT
                    + (int(_metric(item, "index")) - 1)
                    * trend_plot_width
                    / max(len(values) - 1, 1),
                    2,
                ),
                "y": round(y_for(_metric(item, "value")), 2),
                "value": _metric(item, "value"),
            }
            for item in averages
        ]
        window = int(result.get("window", 0))
        return {
            **{key: value for key, value in geometry.items() if key != "y_for"},
            "kind": "moving_average",
            "title": "Tendencia y media móvil",
            "explanation": (
                "La línea azul muestra cada valor y la naranja suaviza cambios usando ventanas "
                f"de {window} observaciones."
            ),
            "cards": [
                {"label": "Observaciones", "value": len(values), "format": "integer"},
                {"label": "Ventana", "value": window, "format": "integer"},
                {
                    "label": "Siguiente referencia",
                    "value": _number(result, "forecast_next"),
                    "format": "number",
                },
            ],
            "method": [
                f"Para cada periodo se promedian las últimas {window} observaciones.",
                f"MA(t) = [X(t) + … + X(t − {window - 1})] ÷ {window}.",
                "La media móvil suaviza variación aleatoria; no demuestra causalidad.",
            ],
            "reference": "Media móvil simple según el NIST/SEMATECH e-Handbook.",
            "actual": actual_points,
            "actual_polyline": _series(actual_points),
            "secondary": average_points,
            "secondary_polyline": _series(average_points),
            "first_period": periods[0],
            "last_period": periods[-1],
            "rows": [
                {
                    "period": period,
                    "value": value,
                    "secondary": next(
                        (
                            _metric(item, "value")
                            for item in averages
                            if int(item.get("index", 0)) == index + 1
                        ),
                        None,
                    ),
                }
                for index, (period, value) in enumerate(zip(periods, values, strict=True))
            ],
        }

    if analysis_type == AnalysisType.LINEAR_REGRESSION:
        predictions = [
            float(value)
            for value in result.get("predictions", [])
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
        if not predictions or len(predictions) > len(values):
            return None
        actual = values[-len(predictions) :]
        test_periods = periods[-len(predictions) :]
        geometry = _chart_geometry(actual + predictions)
        actual_points = _line_points(actual, geometry, start=len(values) - len(predictions))
        predicted_points = _line_points(predictions, geometry, start=len(values) - len(predictions))
        metrics = result.get("metrics", {})
        metrics = metrics if isinstance(metrics, Mapping) else {}
        return {
            **{key: value for key, value in geometry.items() if key != "y_for"},
            "kind": "linear_regression",
            "title": "Regresión lineal: observado frente a estimado",
            "explanation": (
                "La línea azul contiene los valores reservados para prueba y la naranja lo que "
                "estimó el modelo sin haberlos usado para entrenar."
            ),
            "cards": [
                {"label": "R²", "value": _metric(metrics, "r2"), "format": "decimal"},
                {
                    "label": "Error medio absoluto",
                    "value": _metric(metrics, "mae"),
                    "format": "number",
                },
                {"label": "RMSE", "value": _metric(metrics, "rmse"), "format": "number"},
                {
                    "label": "Control de calidad",
                    "value": "Superado" if run.quality_gate_passed else "No superado",
                    "format": "text",
                },
            ],
            "method": [
                "Los datos se separan cronológicamente: entrenamiento primero y prueba después.",
                "La recta ŷ = intercepto + pendiente × tiempo se ajusta por mínimos cuadrados.",
                "MAE promedia |real − estimado|; RMSE es la raíz del error cuadrático medio.",
                "R² compara el error del modelo con la variación de los valores de prueba.",
            ],
            "reference": "Regresión lineal por mínimos cuadrados y evaluación fuera de muestra.",
            "actual": actual_points,
            "actual_polyline": _series(actual_points),
            "secondary": predicted_points,
            "secondary_polyline": _series(predicted_points),
            "first_period": test_periods[0],
            "last_period": test_periods[-1],
            "rows": [
                {"period": period, "value": observed, "secondary": predicted}
                for period, observed, predicted in zip(
                    test_periods, actual, predictions, strict=True
                )
            ],
        }

    if analysis_type == AnalysisType.LOGISTIC_REGRESSION:
        probabilities = [
            float(value)
            for value in result.get("probabilities", [])
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
        if not probabilities or len(probabilities) > len(values):
            return None
        test_periods = periods[-len(probabilities) :]
        geometry = _chart_geometry(probabilities + [0.0, 1.0], forced_domain=(0.0, 1.0))
        probability_points = _line_points(
            probabilities, geometry, start=len(values) - len(probabilities)
        )
        metrics = result.get("metrics", {})
        metrics = metrics if isinstance(metrics, Mapping) else {}
        matrix = metrics.get("confusion_matrix", {})
        matrix = matrix if isinstance(matrix, Mapping) else {}
        return {
            **{key: value for key, value in geometry.items() if key != "y_for"},
            "kind": "logistic_regression",
            "title": "Probabilidad estimada de cumplimiento",
            "explanation": (
                "Cada punto es una probabilidad. Por encima de 50 % el modelo clasifica "
                "cumplimiento; esta demostración no toma decisiones clínicas."
            ),
            "cards": [
                {
                    "label": "Exactitud",
                    "value": _metric(metrics, "accuracy") * 100,
                    "format": "percent",
                },
                {
                    "label": "Precisión",
                    "value": _metric(metrics, "precision") * 100,
                    "format": "percent",
                },
                {
                    "label": "Sensibilidad",
                    "value": _metric(metrics, "recall") * 100,
                    "format": "percent",
                },
                {"label": "F1", "value": _metric(metrics, "f1"), "format": "decimal"},
            ],
            "method": [
                (
                    "La meta aprobada del KPI convierte cada observación en cumple (1) o "
                    "no cumple (0)."
                ),
                "El modelo calcula p = 1 ÷ [1 + exp(−z)] después de estandarizar el tiempo.",
                "Con p ≥ 0.50 clasifica cumple; con p < 0.50 clasifica no cumple.",
                (
                    "Exactitud, precisión, sensibilidad y F1 se calculan desde la matriz de "
                    "clasificación."
                ),
            ],
            "reference": (
                "Regresión logística binaria con separación cronológica y comparación contra "
                "una línea base mayoritaria."
            ),
            "probabilities": probability_points,
            "probability_polyline": _series(probability_points),
            "threshold_y": round(_TOP + _number(geometry, "plot_height") / 2, 2),
            "first_period": test_periods[0],
            "last_period": test_periods[-1],
            "matrix": {
                "true_positive": int(_metric(matrix, "true_positive")),
                "true_negative": int(_metric(matrix, "true_negative")),
                "false_positive": int(_metric(matrix, "false_positive")),
                "false_negative": int(_metric(matrix, "false_negative")),
            },
            "rows": [
                {
                    "period": period,
                    "probability": probability,
                    "classification": "Cumple" if probability >= 0.5 else "No cumple",
                }
                for period, probability in zip(test_periods, probabilities, strict=True)
            ],
        }
    return None


def _number(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    raise ValueError(f"El resultado analítico no contiene {key}.")


def _weekly_summary(
    rows: list[IndicatorObservation], *, left: int, right: int, top: int, bottom: int
) -> dict[str, object]:
    weekly: dict[tuple[int, int], list[float]] = {}
    for row in rows:
        period = date.fromisoformat(row.period_end.isoformat())
        key = (period.isocalendar().year, period.isocalendar().week)
        weekly.setdefault(key, []).append(float(row.value))
    averages = [(key, sum(values) / len(values)) for key, values in weekly.items()]
    values = [value for _, value in averages]
    domain_min = min(min(values), 0.0)
    domain_max = max(max(values), 0.0)
    padding = max((domain_max - domain_min) * 0.08, 1.0)
    domain_min -= padding
    domain_max += padding
    plot_width = right - left
    plot_height = bottom - top
    slot_width = plot_width / len(averages)
    bar_width = max(slot_width * 0.62, 4)

    def y_for(value: float) -> float:
        return top + (domain_max - value) * plot_height / (domain_max - domain_min)

    baseline = y_for(0.0)
    bars = []
    for index, (key, value) in enumerate(averages):
        value_y = y_for(value)
        bars.append(
            {
                "label": f"S{key[1]:02d}",
                "value": value,
                "x": round(left + index * slot_width + (slot_width - bar_width) / 2, 2),
                "y": round(min(value_y, baseline), 2),
                "width": round(bar_width, 2),
                "height": round(abs(baseline - value_y), 2),
                "negative": value < 0,
            }
        )
    return {
        "bars": bars,
        "baseline": round(baseline, 2),
        "gridlines": [
            {
                "value": domain_max - (domain_max - domain_min) * index / 4,
                "y": round(top + plot_height * index / 4, 2),
            }
            for index in range(5)
        ],
    }


def control_chart_presentation(run: AnalysisRun) -> dict[str, object] | None:
    """Build a deterministic, accessible SVG projection for a completed control-chart run."""

    if run.definition.analysis_type != AnalysisType.CONTROL_CHART:
        return None
    rows = _verified_rows(run)
    if not rows:
        return None

    try:
        center = _number(run.result, "center_line")
        lower = _number(run.result, "lower_control_limit")
        upper = _number(run.result, "upper_control_limit")
    except ValueError:
        return None

    values = [float(row.value) for row in rows]
    domain_min = min(values + [lower])
    domain_max = max(values + [upper])
    padding = max((domain_max - domain_min) * 0.08, 1.0)
    domain_min -= padding
    domain_max += padding
    plot_width = _WIDTH - _LEFT - _RIGHT
    plot_height = _HEIGHT - _TOP - _BOTTOM

    def x_for(index: int) -> float:
        if len(rows) == 1:
            return float(_LEFT + plot_width / 2)
        return _LEFT + index * plot_width / (len(rows) - 1)

    def y_for(value: float) -> float:
        return _TOP + (domain_max - value) * plot_height / (domain_max - domain_min)

    signal_indexes = {
        int(item["index"])
        for item in run.result.get("signals", [])
        if isinstance(item, Mapping) and isinstance(item.get("index"), int)
    }
    points = [
        {
            "index": index + 1,
            "x": round(x_for(index), 2),
            "y": round(y_for(float(row.value)), 2),
            "value": float(row.value),
            "period": row.period_end.isoformat(),
            "signal": index in signal_indexes,
        }
        for index, row in enumerate(rows)
    ]
    gridlines = [
        {
            "value": domain_max - (domain_max - domain_min) * index / 4,
            "y": round(_TOP + plot_height * index / 4, 2),
        }
        for index in range(5)
    ]
    x_gridlines = [{"x": round(x_for(round((len(rows) - 1) * index / 4)), 2)} for index in range(5)]
    weekly_summary = _weekly_summary(
        rows, left=_LEFT, right=_WIDTH - _RIGHT, top=_TOP, bottom=_HEIGHT - _BOTTOM
    )
    return {
        "width": _WIDTH,
        "height": _HEIGHT,
        "left": _LEFT,
        "right": _WIDTH - _RIGHT,
        "top": _TOP,
        "bottom": _HEIGHT - _BOTTOM,
        "plot_width": plot_width,
        "plot_height": plot_height,
        "polyline": " ".join(f"{point['x']},{point['y']}" for point in points),
        "points": points,
        "gridlines": gridlines,
        "x_gridlines": x_gridlines,
        "guides": [
            {"label": "LSC", "value": upper, "y": round(y_for(upper), 2), "style": "limit"},
            {
                "label": "Línea central",
                "value": center,
                "y": round(y_for(center), 2),
                "style": "center",
            },
            {"label": "LIC", "value": lower, "y": round(y_for(lower), 2), "style": "limit"},
        ],
        "first_period": rows[0].period_end.isoformat(),
        "last_period": rows[-1].period_end.isoformat(),
        "minimum": domain_min,
        "maximum": domain_max,
        "signal_count": len(signal_indexes),
        "weekly_summary": weekly_summary,
    }
