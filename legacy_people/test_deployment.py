"""Check container command selection and Django behavior behind HTTPS termination."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.test import SimpleTestCase, override_settings


class EntrypointTests(SimpleTestCase):
    def run_entrypoint(self, debug=None, command=(), secret_key="test-only", port="8000"):
        """Stub server commands so startup tests do not touch real databases or ports."""
        with TemporaryDirectory() as directory:
            log = Path(directory) / "commands.log"
            for executable in ("python", "gunicorn"):
                stub = Path(directory) / executable
                stub.write_text(f'#!/bin/sh\nprintf "%s\\n" "{executable} $*" >> "$STARTUP_LOG"\n')
                stub.chmod(0o755)
            environment = {
                "PATH": directory, "SECRET_KEY": secret_key, "STARTUP_LOG": str(log), "PORT": port,
            }
            if debug is not None:
                environment["DEBUG"] = debug
            result = subprocess.run(
                ["/bin/sh", str(settings.BASE_DIR / "devops" / "entrypoint.sh"), *command],
                env=environment, capture_output=True, text=True, check=False,
            )
            commands = log.read_text().splitlines() if log.exists() else []
        return result, commands

    def test_debug_starts_development_server_after_initialization(self):
        result, commands = self.run_entrypoint(debug="True")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(commands, [
            "python manage.py migrate --noinput",
            "python manage.py collectstatic --noinput",
            "python manage.py runserver 0.0.0.0:8000",
        ])

    def test_production_and_unset_debug_start_gunicorn(self):
        for debug in ("False", None, "true"):
            with self.subTest(debug=debug):
                result, commands = self.run_entrypoint(debug=debug)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(commands[-1], "gunicorn --bind 0.0.0.0:8000 core.wsgi:application")

    def test_explicit_command_takes_precedence(self):
        result, commands = self.run_entrypoint(debug="True", command=("python", "manage.py", "check"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(commands[-1], "python manage.py check")

    def test_configured_port_is_used(self):
        result, commands = self.run_entrypoint(debug="True", port="9000")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(commands[-1], "python manage.py runserver 0.0.0.0:9000")

    def test_missing_secret_stops_before_any_commands(self):
        result, commands = self.run_entrypoint(secret_key="")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SECRET_KEY", result.stdout)
        self.assertEqual(commands, [])


@override_settings(
    DEBUG=False, ALLOWED_HOSTS=["example.com"], SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=31536000,
)
class ProxyHTTPSTests(SimpleTestCase):
    def test_http_redirects_to_https(self):
        response = self.client.get("/", HTTP_HOST="example.com")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://example.com/")

    def test_forwarded_https_does_not_redirect_again(self):
        response = self.client.get("/", HTTP_HOST="example.com", HTTP_X_FORWARDED_PROTO="https")
        self.assertEqual(response.status_code, 200)
        self.assertIn("max-age=31536000", response["Strict-Transport-Security"])
