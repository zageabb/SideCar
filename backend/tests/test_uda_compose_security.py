"""Fail-closed UDA source-contract checks without Docker or real credentials."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker-compose.yml"


class ComposeSecurityReview(unittest.TestCase):
    def test_compose_never_supplies_known_default_credentials(self):
        content = COMPOSE.read_text(encoding="utf-8")
        self.assertNotIn("SIDECAR_PIN:-sidecar", content)
        self.assertNotIn("SIDECAR_SECRET:-change-this-secret", content)
        self.assertNotIn("SIDECAR_SECURE_COOKIE:-false", content)

    def test_missing_values_block_compose_interpolation(self):
        content = COMPOSE.read_text(encoding="utf-8")
        for name in ("SIDECAR_PIN", "SIDECAR_SECRET", "SIDECAR_SECURE_COOKIE"):
            with self.subTest(name=name):
                self.assertIn("${" + name + ":?", content)

    def test_existing_persistence_and_health_contract_remains(self):
        content = COMPOSE.read_text(encoding="utf-8")
        self.assertIn("sidecar-data:/data", content)
        self.assertIn("http://localhost:8000/api/health", content)


if __name__ == "__main__":
    unittest.main()
