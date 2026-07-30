from __future__ import annotations

import json
import tempfile
import unittest
import xml.etree.ElementTree as element_tree
from pathlib import Path

from profile_system.design_tokens import load_design_token_snapshot
from profile_system.hero import HeroDataError, load_identity_hero
from profile_system.identity_hero import render_identity_hero
from profile_system.model import load_profile_snapshot
from profile_system.scene import load_observatory_scene

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROFILE_SOURCE = REPOSITORY_ROOT / "profile" / "profile.json"
TOKEN_SOURCE = REPOSITORY_ROOT / "profile" / "design-tokens.json"
SCENE_SOURCE = REPOSITORY_ROOT / "profile" / "scenes" / "planetary-observatory.json"
HERO_SOURCE = REPOSITORY_ROOT / "profile" / "hero.json"


class HeroIdentityTests(unittest.TestCase):
    def test_repository_hero_contract_loads(self) -> None:
        snapshot = load_identity_hero(HERO_SOURCE)

        self.assertEqual(1, snapshot.schema_version)
        self.assertEqual("identity-observatory", snapshot.hero_id)
        self.assertEqual("michal-planeta", snapshot.profile_id)
        self.assertEqual("planetary-observatory", snapshot.scene_id)
        self.assertEqual(("scene", "identity", "status"), snapshot.layer_order)
        self.assertEqual(500, snapshot.panel.width)

    def test_unknown_top_level_field_is_rejected(self) -> None:
        source = json.loads(HERO_SOURCE.read_text(encoding="utf-8"))
        source["unexpected"] = True

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "hero.json"
            path.write_text(json.dumps(source), encoding="utf-8")

            with self.assertRaisesRegex(
                HeroDataError,
                "unsupported fields: unexpected",
            ):
                load_identity_hero(path)

    def test_panel_must_remain_inside_viewport(self) -> None:
        source = json.loads(HERO_SOURCE.read_text(encoding="utf-8"))
        source["panel"]["x"] = 900

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "hero.json"
            path.write_text(json.dumps(source), encoding="utf-8")

            with self.assertRaisesRegex(
                HeroDataError,
                "panel must remain inside the viewport",
            ):
                load_identity_hero(path)

    def test_renderer_uses_exact_canonical_identity_copy(self) -> None:
        document = self.render_repository_hero()

        self.assertIn("Michał Planeta", document)
        self.assertIn("A — CINEMATIC SYSTEMS ENGINEER", document)
        self.assertIn(
            "Software engineer working across rendering, game systems,",
            document,
        )
        self.assertIn(
            "Build the system, understand the mechanism, verify the result.",
            document,
        )

    def test_renderer_adds_identity_and_status_layers(self) -> None:
        root = element_tree.fromstring(self.render_repository_hero())
        identifiers = {
            element.attrib["id"] for element in root.iter() if "id" in element.attrib
        }

        self.assertTrue(
            {
                "hero-identity",
                "hero-identity-panel",
                "hero-identity-name",
                "hero-identity-headline",
                "hero-identity-motto",
                "hero-status",
            }.issubset(identifiers)
        )

    def test_renderer_is_byte_deterministic(self) -> None:
        first = self.render_repository_hero()
        second = self.render_repository_hero()

        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_profile_and_hero_identifier_mismatch_is_rejected(self) -> None:
        hero_source = json.loads(HERO_SOURCE.read_text(encoding="utf-8"))
        hero_source["profileId"] = "different-profile"

        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "hero.json"
            path.write_text(json.dumps(hero_source), encoding="utf-8")
            hero = load_identity_hero(path)

            with self.assertRaisesRegex(
                HeroDataError,
                "profileId does not match",
            ):
                render_identity_hero(
                    load_profile_snapshot(PROFILE_SOURCE),
                    load_observatory_scene(SCENE_SOURCE),
                    load_design_token_snapshot(TOKEN_SOURCE),
                    hero,
                )

    def render_repository_hero(self) -> str:
        return render_identity_hero(
            load_profile_snapshot(PROFILE_SOURCE),
            load_observatory_scene(SCENE_SOURCE),
            load_design_token_snapshot(TOKEN_SOURCE),
            load_identity_hero(HERO_SOURCE),
        )


if __name__ == "__main__":
    unittest.main()
