from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as element_tree
from pathlib import Path
from typing import cast

from profile_system.design_tokens import load_design_token_snapshot
from profile_system.observatory_scene import render_observatory_scene
from profile_system.scene import SceneDataError, load_observatory_scene
from profile_system.svg_kernel import SvgKernelError

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCENE_SOURCE = REPOSITORY_ROOT / "profile/scenes/planetary-observatory.json"
TOKEN_SOURCE = REPOSITORY_ROOT / "profile/design-tokens.json"
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


class ObservatorySceneTests(unittest.TestCase):
    def source_document(self) -> dict[str, object]:
        return json.loads(SCENE_SOURCE.read_text(encoding="utf-8"))

    def write_source(self, document: dict[str, object]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "scene.json"
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_repository_scene_loads_with_fixed_layer_order(self) -> None:
        scene = load_observatory_scene(SCENE_SOURCE)

        self.assertEqual("planetary-observatory", scene.scene_id)
        self.assertEqual((1200, 720), (scene.viewport.width, scene.viewport.height))
        self.assertEqual(56, scene.star_count)
        self.assertEqual(
            (
                "background",
                "stars",
                "window",
                "planet",
                "architecture",
                "console",
                "atmosphere",
                "foreground",
            ),
            scene.layer_order,
        )

    def test_unknown_scene_field_is_rejected(self) -> None:
        document = self.source_document()
        document["notes"] = "not part of the public contract"

        with self.assertRaisesRegex(
            SceneDataError,
            "contains unsupported fields: notes",
        ):
            load_observatory_scene(self.write_source(document))

    def test_layer_reordering_is_rejected(self) -> None:
        document = self.source_document()
        layers = list(cast(list[str], document["layerOrder"]))
        layers[0], layers[1] = layers[1], layers[0]
        document["layerOrder"] = layers

        with self.assertRaisesRegex(SceneDataError, "layerOrder must equal"):
            load_observatory_scene(self.write_source(document))

    def test_planet_outside_window_is_rejected(self) -> None:
        document = self.source_document()
        planet = dict(cast(dict[str, object], document["planet"]))
        planet["centerX"] = 40
        document["planet"] = planet

        with self.assertRaisesRegex(SceneDataError, "inside the observatory window"):
            load_observatory_scene(self.write_source(document))

    def test_renderer_is_deterministic_and_contains_required_layers(self) -> None:
        scene = load_observatory_scene(SCENE_SOURCE)
        tokens = load_design_token_snapshot(TOKEN_SOURCE)

        first = render_observatory_scene(scene, tokens)
        second = render_observatory_scene(scene, tokens)

        self.assertEqual(first, second)
        root = element_tree.fromstring(first)
        identifiers = {
            element.attrib["id"] for element in root.iter() if "id" in element.attrib
        }
        self.assertTrue(
            {
                "scene-background",
                "scene-stars",
                "scene-window",
                "scene-planet",
                "scene-architecture",
                "scene-console",
                "scene-atmosphere",
                "scene-foreground",
            }.issubset(identifiers)
        )
        self.assertEqual("0 0 1200 720", root.attrib["viewBox"])

    def test_rendered_star_count_matches_scene_contract(self) -> None:
        scene = load_observatory_scene(SCENE_SOURCE)
        tokens = load_design_token_snapshot(TOKEN_SOURCE)
        root = element_tree.fromstring(render_observatory_scene(scene, tokens))
        stars = root.find(f".//{{{SVG_NAMESPACE}}}g[@id='scene-stars']")

        self.assertIsNotNone(stars)
        assert stars is not None
        star_nodes = stars.findall(f"{{{SVG_NAMESPACE}}}circle")
        self.assertEqual(scene.star_count, len(star_nodes))

    def test_theme_mismatch_is_rejected(self) -> None:
        document = self.source_document()
        document["themeId"] = "different-theme"
        scene = load_observatory_scene(self.write_source(document))
        tokens = load_design_token_snapshot(TOKEN_SOURCE)

        with self.assertRaisesRegex(SvgKernelError, "does not match"):
            render_observatory_scene(scene, tokens)


if __name__ == "__main__":
    unittest.main()
