from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from profile_system.design_tokens import (
    DesignTokenError,
    load_design_token_snapshot,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TOKEN_SOURCE = REPOSITORY_ROOT / "profile/design-tokens.json"


class DesignTokenTests(unittest.TestCase):
    def load_document(self) -> dict[str, object]:
        return json.loads(TOKEN_SOURCE.read_text(encoding="utf-8"))

    def write_document(
        self,
        document: dict[str, object],
        directory: Path,
    ) -> Path:
        path = directory / "tokens.json"
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_repository_contract_loads_with_verified_contrast(self) -> None:
        snapshot = load_design_token_snapshot(TOKEN_SOURCE)

        self.assertEqual("planetary-observatory", snapshot.theme_id)
        self.assertEqual(14, len(snapshot.colors))
        self.assertEqual(6, len(snapshot.type_sizes))
        self.assertEqual(8, len(snapshot.spacing_steps))
        self.assertEqual(3, len(snapshot.contrast_pairs))
        self.assertTrue(
            all(pair.actual >= pair.minimum for pair in snapshot.contrast_pairs)
        )

    def test_unknown_top_level_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = self.load_document()
            document["unexpected"] = True
            path = self.write_document(document, Path(temporary_directory))

            with self.assertRaisesRegex(
                DesignTokenError,
                "unsupported fields: unexpected",
            ):
                load_design_token_snapshot(path)

    def test_invalid_color_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = self.load_document()
            palette = document["palette"]
            assert isinstance(palette, dict)
            background = palette["background"]
            assert isinstance(background, dict)
            background["void"] = "black"
            path = self.write_document(document, Path(temporary_directory))

            with self.assertRaisesRegex(DesignTokenError, "lowercase six-digit hex"):
                load_design_token_snapshot(path)

    def test_duplicate_spacing_step_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = self.load_document()
            spacing = document["spacing"]
            assert isinstance(spacing, dict)
            spacing["steps"] = [4, 8, 12, 16, 24, 32, 48, 48]
            path = self.write_document(document, Path(temporary_directory))

            with self.assertRaisesRegex(DesignTokenError, "strictly increasing"):
                load_design_token_snapshot(path)

    def test_non_descending_type_scale_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = self.load_document()
            typography = document["typography"]
            assert isinstance(typography, dict)
            sizes = typography["sizes"]
            assert isinstance(sizes, dict)
            sizes["title"] = 64
            path = self.write_document(document, Path(temporary_directory))

            with self.assertRaisesRegex(DesignTokenError, "strictly descending"):
                load_design_token_snapshot(path)

    def test_unresolved_contrast_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = self.load_document()
            rules = document["rules"]
            assert isinstance(rules, dict)
            pairs = rules["contrastPairs"]
            assert isinstance(pairs, list)
            first = pairs[0]
            assert isinstance(first, dict)
            first["foreground"] = "text.missing"
            path = self.write_document(document, Path(temporary_directory))

            with self.assertRaisesRegex(DesignTokenError, "Unknown contrast color"):
                load_design_token_snapshot(path)

    def test_insufficient_contrast_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = self.load_document()
            palette = document["palette"]
            assert isinstance(palette, dict)
            text = palette["text"]
            background = palette["background"]
            assert isinstance(text, dict)
            assert isinstance(background, dict)
            text["primary"] = background["void"]
            path = self.write_document(document, Path(temporary_directory))

            with self.assertRaisesRegex(DesignTokenError, "does not meet minimum"):
                load_design_token_snapshot(path)

    def test_invalid_motion_policy_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            document = self.load_document()
            rules = document["rules"]
            assert isinstance(rules, dict)
            rules["motion"] = "ambient-loop"
            path = self.write_document(document, Path(temporary_directory))

            with self.assertRaisesRegex(DesignTokenError, "Unsupported motion policy"):
                load_design_token_snapshot(path)


if __name__ == "__main__":
    unittest.main()
