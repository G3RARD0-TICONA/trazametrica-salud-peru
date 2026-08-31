from __future__ import annotations

from collections.abc import Mapping
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
    if content_hash(input_payload) != run.input_hash:
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
    x_gridlines = [
        {"x": round(x_for(round((len(rows) - 1) * index / 4)), 2)}
        for index in range(5)
    ]
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
        "polyline": " ".join(f"{point['x']},\${point['y']}" for point in points),
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
