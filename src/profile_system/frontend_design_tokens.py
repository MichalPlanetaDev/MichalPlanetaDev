from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType

from profile_system.design_tokens import DesignTokenSnapshot, TokenValue

CSS_IDENTIFIER_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")
ROOT_FONT_SIZE = Decimal("16")


@dataclass(frozen=True, slots=True)
class ResolvedFrontendToken:
    role: str
    source_token_id: str
    kind: str
    value: TokenValue


@dataclass(frozen=True, slots=True)
class FrontendDesignTokens:
    schema_version: int
    theme_id: str
    fingerprint: str
    raw: Mapping[str, Mapping[str, ResolvedFrontendToken]]
    semantic: Mapping[str, Mapping[str, ResolvedFrontendToken]]


def _json_value(value: TokenValue) -> str | int | float | list[str]:
    return list(value) if isinstance(value, tuple) else value


def _canonical_record(
    snapshot: DesignTokenSnapshot,
    raw: Mapping[str, Mapping[str, ResolvedFrontendToken]],
    semantic: Mapping[str, Mapping[str, ResolvedFrontendToken]],
) -> dict[str, object]:
    return {
        "raw": {
            group_id: {
                token_id: {
                    "kind": token.kind,
                    "sourceTokenId": token.source_token_id,
                    "value": _json_value(token.value),
                }
                for token_id, token in sorted(tokens.items())
            }
            for group_id, tokens in sorted(raw.items())
        },
        "schemaVersion": snapshot.schema_version,
        "semantic": {
            group_id: {
                role_id: {
                    "kind": token.kind,
                    "sourceTokenId": token.source_token_id,
                    "value": _json_value(token.value),
                }
                for role_id, token in sorted(tokens.items())
            }
            for group_id, tokens in sorted(semantic.items())
        },
        "themeId": snapshot.theme_id,
    }


def resolve_frontend_design_tokens(
    snapshot: DesignTokenSnapshot,
) -> FrontendDesignTokens:
    raw_groups: dict[str, Mapping[str, ResolvedFrontendToken]] = {}
    grouped_raw: dict[str, dict[str, ResolvedFrontendToken]] = {}

    for token_id, token in sorted(snapshot.raw_tokens.items()):
        group_id, _, role = token_id.partition(".")
        grouped_raw.setdefault(group_id, {})[role] = ResolvedFrontendToken(
            role=role,
            source_token_id=token.token_id,
            kind=token.kind,
            value=token.value,
        )

    for group_id, tokens in grouped_raw.items():
        raw_groups[group_id] = MappingProxyType(tokens)

    semantic_groups: dict[str, Mapping[str, ResolvedFrontendToken]] = {}

    for group_id, group in sorted(snapshot.semantic_groups.items()):
        resolved_roles: dict[str, ResolvedFrontendToken] = {}

        for role_id, reference in sorted(group.tokens.items()):
            source = snapshot.raw_tokens[reference.resolved_token_id]
            resolved_roles[role_id] = ResolvedFrontendToken(
                role=role_id,
                source_token_id=source.token_id,
                kind=reference.kind,
                value=source.value,
            )

        semantic_groups[group_id] = MappingProxyType(resolved_roles)

    raw = MappingProxyType(raw_groups)
    semantic = MappingProxyType(semantic_groups)
    canonical = json.dumps(
        _canonical_record(snapshot, raw, semantic),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    return FrontendDesignTokens(
        schema_version=snapshot.schema_version,
        theme_id=snapshot.theme_id,
        fingerprint=hashlib.sha256(canonical).hexdigest(),
        raw=raw,
        semantic=semantic,
    )


def _css_name(identifier: str) -> str:
    return CSS_IDENTIFIER_BOUNDARY.sub("-", identifier).replace(".", "-").lower()


def _decimal_text(value: int | float) -> str:
    decimal = Decimal(str(value)).normalize()
    text = format(decimal, "f")
    return "0" if text in {"-0", ""} else text


def _rem(value: int | float) -> str:
    decimal = Decimal(str(value)) / ROOT_FONT_SIZE
    text = format(decimal.normalize(), "f")
    return f"{text}rem"


def _css_value(token: ResolvedFrontendToken) -> str:
    value = token.value

    if token.kind == "font-stack":
        if not isinstance(value, tuple):
            raise TypeError(f"{token.source_token_id} must contain a font stack")
        return ", ".join(value)

    if token.kind == "color":
        if not isinstance(value, str):
            raise TypeError(f"{token.source_token_id} must contain a color")
        return value

    if isinstance(value, (str, tuple)):
        raise TypeError(f"{token.source_token_id} has incompatible {token.kind} data")

    if token.kind == "duration":
        return f"{_decimal_text(value)}ms"
    if token.kind == "length":
        if token.source_token_id.startswith("strokes."):
            return f"{_decimal_text(value)}px"
        return _rem(value)
    if token.kind == "tracking":
        return _rem(value)
    if token.kind in {"font-weight", "number", "opacity"}:
        return _decimal_text(value)

    raise ValueError(f"Unsupported frontend token kind: {token.kind}")


def _css_declarations(tokens: FrontendDesignTokens) -> list[tuple[str, str]]:
    declarations: list[tuple[str, str]] = []

    for group_id, group in sorted(tokens.raw.items()):
        for role_id, token in sorted(group.items()):
            declarations.append(
                (
                    f"--cr-raw-{_css_name(group_id)}-{_css_name(role_id)}",
                    _css_value(token),
                )
            )

    for group_id, group in sorted(tokens.semantic.items()):
        for role_id, token in sorted(group.items()):
            declarations.append(
                (
                    f"--cr-{_css_name(group_id)}-{_css_name(role_id)}",
                    _css_value(token),
                )
            )

    return declarations


def render_frontend_design_css(tokens: FrontendDesignTokens) -> str:
    lines = [
        "/* Generated by profile-system. Do not edit directly. */",
        f"/* schema-version: {tokens.schema_version} */",
        f"/* theme-id: {tokens.theme_id} */",
        f"/* fingerprint: {tokens.fingerprint} */",
        ":root {",
    ]
    lines.extend(f"  {name}: {value};" for name, value in _css_declarations(tokens))
    lines.extend(("}", ""))
    return "\n".join(lines)


def _typescript_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _typescript_object(
    groups: Mapping[str, Mapping[str, ResolvedFrontendToken]],
    *,
    indent: str,
    css_values: bool,
) -> list[str]:
    lines: list[str] = ["{"]

    for group_index, (group_id, group) in enumerate(sorted(groups.items())):
        group_suffix = "," if group_index < len(groups) - 1 else ""
        lines.append(f"{indent}{json.dumps(group_id)}: {{")

        entries = sorted(group.items())
        for role_index, (role_id, token) in enumerate(entries):
            suffix = "," if role_index < len(entries) - 1 else ""
            rendered = (
                _typescript_string(_css_value(token))
                if css_values
                else json.dumps(_json_value(token.value), ensure_ascii=False)
            )
            lines.append(f"{indent}  {json.dumps(role_id)}: {rendered}{suffix}")

        lines.append(f"{indent}}}{group_suffix}")

    lines.append(indent[:-2] + "}")
    return lines


def render_frontend_design_typescript(tokens: FrontendDesignTokens) -> str:
    raw_lines = _typescript_object(tokens.raw, indent="    ", css_values=False)
    semantic_lines = _typescript_object(
        tokens.semantic,
        indent="    ",
        css_values=True,
    )

    lines = [
        "// Generated by profile-system. Do not edit directly.",
        "",
        "export const designTokens = {",
        "  meta: {",
        f"    schemaVersion: {tokens.schema_version},",
        f"    themeId: {_typescript_string(tokens.theme_id)},",
        f"    fingerprint: {_typescript_string(tokens.fingerprint)},",
        "  },",
        "  raw: " + raw_lines[0],
        *raw_lines[1:-1],
        raw_lines[-1] + ",",
        "  semantic: " + semantic_lines[0],
        *semantic_lines[1:-1],
        semantic_lines[-1] + ",",
        "} as const;",
        "",
        "export type DesignTokens = typeof designTokens;",
        'export type SemanticDesignTokens = DesignTokens["semantic"];',
        "",
    ]
    return "\n".join(lines)
