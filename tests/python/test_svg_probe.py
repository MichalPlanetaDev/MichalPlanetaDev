from __future__ import annotations

import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as element_tree
from pathlib import Path

from profile_system.probes import (
    ProbeDataError,
    load_svg_probe_snapshot,
)
from profile_system.svg_document import render_svg_probe

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROBE_SOURCE = REPOSITORY_ROOT / "profile" / "probes" / "github-svg-capabilities.json"
COMMITTED_SVG = (
    REPOSITORY_ROOT / "assets" / "generated" / "probes" / "github-svg-capabilities.svg"
)
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


class SvgProbeTests(unittest.TestCase):
    def test_repository_probe_is_deterministic_and_static(self) -> None:
        snapshot = load_svg_probe_snapshot(PROBE_SOURCE)
        first_document = render_svg_probe(snapshot)
        second_document = render_svg_probe(snapshot)

        self.assertEqual(
            first_document,
            second_document,
        )
        self.assertEqual(
            COMMITTED_SVG.read_text(encoding="utf-8"),
            first_document,
        )

        root = element_tree.fromstring(first_document)

        self.assertEqual(
            f"{{{SVG_NAMESPACE}}}svg",
            root.tag,
        )
        self.assertEqual(
            "1200",
            root.attrib["width"],
        )
        self.assertEqual(
            "620",
            root.attrib["height"],
        )
        self.assertEqual(
            "0 0 1200 620",
            root.attrib["viewBox"],
        )

        forbidden_elements = {
            "animate",
            "animateMotion",
            "animateTransform",
            "foreignObject",
            "image",
            "script",
            "set",
        }
        element_names: set[str] = set()
        identifiers: list[str] = []
        references: set[str] = set()

        for element in root.iter():
            element_name = element.tag.rsplit("}", 1)[-1]
            element_names.add(element_name)

            self.assertNotIn(
                element_name,
                forbidden_elements,
            )

            identifier = element.attrib.get("id")

            if identifier is not None:
                identifiers.append(identifier)

            for attribute_name, value in element.attrib.items():
                local_name = attribute_name.rsplit("}", 1)[-1]

                self.assertFalse(local_name.lower().startswith("on"))

                if local_name == "href":
                    self.assertFalse(
                        value.startswith(
                            (
                                "http:",
                                "https:",
                                "//",
                                "data:",
                            )
                        )
                    )

                references.update(
                    re.findall(
                        r"url\(#([a-z0-9-]+)\)",
                        value,
                    )
                )

        self.assertEqual(
            len(identifiers),
            len(set(identifiers)),
        )
        self.assertTrue(references.issubset(set(identifiers)))
        self.assertEqual(
            9,
            sum(identifier.startswith("capability-") for identifier in identifiers),
        )
        self.assertTrue(
            {
                "clipPath",
                "filter",
                "linearGradient",
                "mask",
                "radialGradient",
            }.issubset(element_names)
        )

    def test_duplicate_capability_ids_are_rejected(self) -> None:
        document = self._document()
        document["capabilities"] = [
            {
                "id": "solid",
                "label": "SOLID",
                "kind": "solid-geometry",
            },
            {
                "id": "solid",
                "label": "DUPLICATE",
                "kind": "path-geometry",
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "probe.json"
            self._write_document(source, document)

            with self.assertRaisesRegex(
                ProbeDataError,
                "Duplicate capability id: solid",
            ):
                load_svg_probe_snapshot(source)

    def test_unsupported_capability_kind_is_rejected(self) -> None:
        document = self._document()
        document["capabilities"] = [
            {
                "id": "motion",
                "label": "MOTION",
                "kind": "animation",
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "probe.json"
            self._write_document(source, document)

            with self.assertRaisesRegex(
                ProbeDataError,
                "Unsupported capability kind: animation",
            ):
                load_svg_probe_snapshot(source)

    @staticmethod
    def _document() -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "probeId": "github-svg-capabilities",
            "title": "Static SVG Surface Probe",
            "viewport": {
                "width": 1200,
                "height": 620,
            },
            "capabilities": [],
        }

    @staticmethod
    def _write_document(
        path: Path,
        document: dict[str, object],
    ) -> None:
        path.write_text(
            json.dumps(
                document,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
