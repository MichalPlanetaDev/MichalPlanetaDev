from __future__ import annotations

import json

from profile_system import __version__
from profile_system.design_tokens import (
    DesignTokenSnapshot,
    NumericToken,
)


def _numeric_values(records: tuple[NumericToken, ...]) -> dict[str, int | float]:
    return {record.token_id: record.value for record in records}


def render_visual_grammar(snapshot: DesignTokenSnapshot) -> str:
    colors = {record.token_id: record.value for record in snapshot.colors}
    document = {
        "contrast": [
            {
                "actual": round(record.actual, 3),
                "background": record.background,
                "foreground": record.foreground,
                "minimum": record.minimum,
                "passes": record.actual >= record.minimum,
            }
            for record in snapshot.contrast_pairs
        ],
        "generator": {
            "name": "profile-system",
            "version": __version__,
        },
        "groups": {
            "colors": {
                "count": len(colors),
                "values": colors,
            },
            "effects": _numeric_values(snapshot.effects),
            "layout": _numeric_values(snapshot.layout),
            "opacity": _numeric_values(snapshot.opacity),
            "radii": _numeric_values(snapshot.radii),
            "spacing": {
                "steps": list(snapshot.spacing_steps),
                "unit": snapshot.spacing_unit,
            },
            "strokes": _numeric_values(snapshot.strokes),
            "typography": {
                "fontStack": list(snapshot.font_stack),
                "sizes": _numeric_values(snapshot.type_sizes),
                "tracking": _numeric_values(snapshot.tracking),
                "weights": _numeric_values(snapshot.type_weights),
            },
        },
        "rules": {
            "cornerLanguage": snapshot.corner_language,
            "density": snapshot.density,
            "motion": snapshot.motion,
        },
        "schemaVersion": snapshot.schema_version,
        "themeId": snapshot.theme_id,
    }

    return (
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
