from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from profile_system.design_tokens import load_design_token_snapshot
from profile_system.frontend_design_tokens import (
    render_frontend_design_css,
    render_frontend_design_typescript,
    resolve_frontend_design_tokens,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TOKEN_SOURCE = REPOSITORY_ROOT / "profile/design-tokens.json"


class FrontendDesignTokenTests(unittest.TestCase):
    def setUp(self) -> None:
        snapshot = load_design_token_snapshot(TOKEN_SOURCE)
        self.tokens = resolve_frontend_design_tokens(snapshot)

    def test_semantic_roles_resolve_once(self) -> None:
        self.assertEqual("#05080d", self.tokens.semantic["surface"]["canvas"].value)
        self.assertEqual("color", self.tokens.semantic["surface"]["canvas"].kind)
        self.assertEqual(56, self.tokens.semantic["spacing"]["section"].value)
        self.assertEqual(
            "layout.sectionGap",
            self.tokens.semantic["spacing"]["section"].source_token_id,
        )

    def test_fingerprint_is_stable_sha256(self) -> None:
        duplicate = resolve_frontend_design_tokens(
            load_design_token_snapshot(TOKEN_SOURCE)
        )

        self.assertRegex(self.tokens.fingerprint, r"^[0-9a-f]{64}$")
        self.assertEqual(self.tokens.fingerprint, duplicate.fingerprint)

    def test_fingerprint_changes_with_resolved_content(self) -> None:
        document = json.loads(TOKEN_SOURCE.read_text(encoding="utf-8"))
        palette = document["palette"]
        assert isinstance(palette, dict)
        accent = palette["accent"]
        assert isinstance(accent, dict)
        accent["critical"] = "#e36d73"

        with tempfile.TemporaryDirectory() as temporary_directory:
            changed_source = Path(temporary_directory) / "tokens.json"
            changed_source.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            changed = resolve_frontend_design_tokens(
                load_design_token_snapshot(changed_source)
            )

        self.assertNotEqual(self.tokens.fingerprint, changed.fingerprint)

    def test_css_uses_explicit_units_and_semantic_names(self) -> None:
        document = render_frontend_design_css(self.tokens)

        self.assertIn("--cr-surface-canvas: #05080d;", document)
        self.assertIn("--cr-spacing-section: 3.5rem;", document)
        self.assertIn("--cr-motion-fast: 120ms;", document)
        self.assertIn("--cr-stroke-hairline: 1px;", document)
        self.assertIn(
            '--cr-font-technical: "SFMono-Regular", Consolas, '
            '"Liberation Mono", monospace;',
            document,
        )
        self.assertNotIn("semantic.surface.canvas", document)

    def test_css_contains_stable_source_metadata(self) -> None:
        document = render_frontend_design_css(self.tokens)

        self.assertIn("/* schema-version: 2 */", document)
        self.assertIn("/* theme-id: planetary-observatory */", document)
        self.assertIn(f"/* fingerprint: {self.tokens.fingerprint} */", document)
        self.assertNotRegex(document, r"20\d{2}-\d{2}-\d{2}")

    def test_typescript_is_readonly_literal_data(self) -> None:
        document = render_frontend_design_typescript(self.tokens)

        self.assertIn("export const designTokens =", document)
        self.assertIn(f'fingerprint: "{self.tokens.fingerprint}"', document)
        self.assertIn('"canvas": "#05080d"', document)
        self.assertIn('"section": "3.5rem"', document)
        self.assertIn("} as const;", document)
        self.assertIn("export type SemanticDesignTokens", document)
        self.assertNotIn("resolve", document)

    def test_css_declaration_names_are_unique(self) -> None:
        document = render_frontend_design_css(self.tokens)
        names = re.findall(r"^\s*(--cr-[a-z0-9-]+):", document, re.MULTILINE)

        self.assertTrue(names)
        self.assertEqual(len(names), len(set(names)))

    def test_rendering_is_byte_stable(self) -> None:
        self.assertEqual(
            render_frontend_design_css(self.tokens),
            render_frontend_design_css(self.tokens),
        )
        self.assertEqual(
            render_frontend_design_typescript(self.tokens),
            render_frontend_design_typescript(self.tokens),
        )


if __name__ == "__main__":
    unittest.main()
