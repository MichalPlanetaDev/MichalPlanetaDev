from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as element_tree
from pathlib import Path

from profile_system.design_tokens import load_design_token_snapshot
from profile_system.kernel_specimen import render_kernel_specimen
from profile_system.svg_kernel import (
    GradientStop,
    SvgDocument,
    SvgKernelError,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TOKEN_SOURCE = REPOSITORY_ROOT / "profile/design-tokens.json"
KERNEL_ARTIFACT = REPOSITORY_ROOT / "assets/generated/kernel/svg-renderer-kernel.svg"


class SvgKernelTests(unittest.TestCase):
    def test_duplicate_identifiers_are_rejected(self) -> None:
        document = SvgDocument(
            width=320,
            height=180,
            title="Kernel",
            description="Duplicate identifier test",
        )
        document.element(
            document.root,
            "g",
            {"id": "layer-signal"},
        )

        with self.assertRaisesRegex(
            SvgKernelError,
            "Duplicate SVG identifier: layer-signal",
        ):
            document.element(
                document.root,
                "g",
                {"id": "layer-signal"},
            )

    def test_external_reference_attributes_are_rejected(self) -> None:
        document = SvgDocument(
            width=320,
            height=180,
            title="Kernel",
            description="External reference test",
        )

        with self.assertRaisesRegex(
            SvgKernelError,
            "SVG href attributes are not permitted",
        ):
            document.element(
                document.root,
                "g",
                {"href": "https://example.invalid/asset.svg"},
            )

    def test_unresolved_local_references_are_rejected(self) -> None:
        document = SvgDocument(
            width=320,
            height=180,
            title="Kernel",
            description="Reference integrity test",
        )
        document.element(
            document.root,
            "rect",
            {
                "x": 0,
                "y": 0,
                "width": 40,
                "height": 40,
                "fill": "url(#missing-gradient)",
            },
        )

        with self.assertRaisesRegex(
            SvgKernelError,
            "Unresolved SVG references: missing-gradient",
        ):
            document.serialize()

    def test_gradient_offsets_are_strictly_validated(self) -> None:
        document = SvgDocument(
            width=320,
            height=180,
            title="Kernel",
            description="Gradient validation test",
        )

        with self.assertRaisesRegex(
            SvgKernelError,
            "Gradient stop offset must use an integer percentage",
        ):
            document.define_linear_gradient(
                "invalid-gradient",
                stops=(
                    GradientStop("10.5%", "#ffffff"),
                    GradientStop("100%", "#000000"),
                ),
            )

    def test_specimen_is_deterministic_and_token_driven(self) -> None:
        tokens = load_design_token_snapshot(TOKEN_SOURCE)
        first = render_kernel_specimen(tokens)
        second = render_kernel_specimen(tokens)

        self.assertEqual(first, second)

        color_values = {token.value for token in tokens.colors}
        used_colors = {value for value in color_values if value in first}

        self.assertGreaterEqual(len(used_colors), 9)
        self.assertIn(", ".join(tokens.font_stack), first)
        self.assertIn("TOKEN-DRIVEN SVG PRIMITIVES", first)

    def test_specimen_has_accessible_safe_structure(self) -> None:
        tokens = load_design_token_snapshot(TOKEN_SOURCE)
        document = render_kernel_specimen(tokens)
        root = element_tree.fromstring(document)

        self.assertEqual("img", root.attrib.get("role"))
        self.assertEqual("1200", root.attrib.get("width"))
        self.assertEqual("520", root.attrib.get("height"))
        self.assertEqual("0 0 1200 520", root.attrib.get("viewBox"))

        element_names = {element.tag.rsplit("}", 1)[-1] for element in root.iter()}
        forbidden = {
            "animate",
            "animateMotion",
            "animateTransform",
            "foreignObject",
            "image",
            "script",
            "set",
        }
        self.assertTrue(forbidden.isdisjoint(element_names))

        identifiers = {
            element.attrib["id"] for element in root.iter() if "id" in element.attrib
        }
        required = {
            "renderer-kernel-title",
            "renderer-kernel-description",
            "layer-background",
            "layer-grid",
            "layer-interface",
            "layer-primitives",
            "layer-typography",
            "layer-footer",
        }
        self.assertTrue(required.issubset(identifiers))

        references: set[str] = set()
        for element in root.iter():
            for value in element.attrib.values():
                references.update(re.findall(r"url\(#([a-z0-9-]+)\)", value))

        self.assertTrue(references.issubset(identifiers))

    def test_repository_artifact_matches_the_renderer(self) -> None:
        tokens = load_design_token_snapshot(TOKEN_SOURCE)
        expected = render_kernel_specimen(tokens)

        self.assertEqual(
            expected,
            KERNEL_ARTIFACT.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
