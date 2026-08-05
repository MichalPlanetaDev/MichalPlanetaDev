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
    semantic = {
        group_id: {
            role_id: {
                "kind": reference.kind,
                "reference": reference.reference,
                "resolvedToken": reference.resolved_token_id,
            }
            for role_id, reference in group.tokens.items()
        }
        for group_id, group in snapshot.semantic_groups.items()
    }
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
            "motion": {
                "duration": _numeric_values(snapshot.motion_durations),
            },
            "opacity": _numeric_values(snapshot.opacity),
            "radii": _numeric_values(snapshot.radii),
            "spacing": {
                "steps": list(snapshot.spacing_steps),
                "unit": snapshot.spacing_unit,
            },
            "strokes": _numeric_values(snapshot.strokes),
            "typography": {
                "fontStack": list(snapshot.font_stack),
                "monoStack": list(snapshot.mono_stack),
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
        "semantic": semantic,
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
