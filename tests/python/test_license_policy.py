from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LICENSE_PATH = REPOSITORY_ROOT / "LICENSE"


class LicensePolicyTests(unittest.TestCase):
    def test_license_allows_source_review_and_private_study(self) -> None:
        content = LICENSE_PATH.read_text(encoding="utf-8")

        self.assertIn("view and study the source code", content)
        self.assertIn("private, non-commercial review and education", content)
        self.assertIn("GitHub platform functionality", content)

    def test_license_reserves_reuse_and_redistribution_rights(self) -> None:
        content = LICENSE_PATH.read_text(encoding="utf-8")

        for restriction in (
            "incorporate any part of the Work into another project",
            "publish or distribute copies or derivative works",
            "sell, sublicense, or commercially exploit the Work",
            "represent the Work or any part of it as your own",
        ):
            self.assertIn(restriction, content)

    def test_license_uses_the_approved_owner_and_not_open_source_boilerplate(
        self,
    ) -> None:
        content = LICENSE_PATH.read_text(encoding="utf-8")

        self.assertIn("Copyright © 2026 Michał Planeta", content)
        self.assertIn("All rights reserved", content)
        self.assertNotIn("Permission is hereby granted, free of charge", content)
        self.assertNotIn("Licensed under the Apache License", content)
        self.assertNotIn("GNU GENERAL PUBLIC LICENSE", content)
