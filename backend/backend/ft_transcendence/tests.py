import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


class AsgiImportTests(SimpleTestCase):
    def test_asgi_module_imports_without_prior_setup(self):
        # Plain daphne imports the module before Django is set up.
        # Importing models first used to raise AppRegistryNotReady.
        backend_dir = Path(__file__).resolve().parent.parent
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(backend_dir),
            "DJANGO_SETTINGS_MODULE": "ft_transcendence.settings",
            "DJANGO_SECRET_KEY": "test",
            "JWT_SECRET": "test",
        }
        result = subprocess.run(
            [sys.executable, "-c", "import ft_transcendence.asgi"],
            cwd="/", env=env, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
