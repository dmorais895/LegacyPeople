"""Regression coverage for proxy trust, shared counters, and request quotas."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.db import connection, connections
from django.test import RequestFactory, SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Person, RateLimit
from .rate_limits import consume_attempt, get_attempts, get_client_ip


@override_settings(TRUSTED_PROXY_CIDRS=[])
class ClientIPTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_untrusted_peer_cannot_supply_forwarded_ip(self):
        request = self.factory.get("/", REMOTE_ADDR="8.8.8.8", HTTP_X_FORWARDED_FOR="1.1.1.1")
        self.assertEqual(get_client_ip(request), "8.8.8.8")

    @override_settings(TRUSTED_PROXY_CIDRS=["10.0.0.0/24"])
    def test_trusted_chain_stops_at_first_untrusted_hop(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="9.9.9.9, 8.8.8.8, 10.0.0.2"
        )
        self.assertEqual(get_client_ip(request), "8.8.8.8")

    @override_settings(TRUSTED_PROXY_CIDRS=["10.0.0.1/32"])
    def test_private_client_is_not_skipped(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="8.8.8.8, 192.168.1.10"
        )
        self.assertEqual(get_client_ip(request), "192.168.1.10")

    @override_settings(TRUSTED_PROXY_CIDRS=["10.0.0.1/32"])
    def test_malformed_forwarded_hop_falls_back_to_peer(self):
        for forwarded in ("invalid", "8.8.8.8,", "", "8.8.8.8:1234"):
            with self.subTest(forwarded=forwarded):
                request = self.factory.get("/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR=forwarded)
                self.assertEqual(get_client_ip(request), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_CIDRS=["2001:db8:1::/64"])
    def test_ipv6_addresses_are_canonicalized(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="2001:db8:1::1", HTTP_X_FORWARDED_FOR="2001:0db8:0002:0000::1"
        )
        self.assertEqual(get_client_ip(request), "2001:db8:2::1")

    def test_invalid_peer_uses_stable_fallback(self):
        request = self.factory.get("/", REMOTE_ADDR="invalid", HTTP_X_FORWARDED_FOR="1.1.1.1")
        self.assertEqual(get_client_ip(request), "0.0.0.0")


class CounterTests(TestCase):
    def test_limit_is_enforced_without_extending_window(self):
        start = timezone.now()
        with patch("legacy_people.rate_limits.timezone.now", return_value=start):
            self.assertTrue(consume_attempt("login_test", 5, 900))
        with patch("legacy_people.rate_limits.timezone.now", return_value=start + timedelta(seconds=100)):
            for _ in range(4):
                self.assertTrue(consume_attempt("login_test", 5, 900))
            self.assertFalse(consume_attempt("login_test", 5, 900))
        counter = RateLimit.objects.get(key="login_test")
        self.assertEqual(counter.attempts, 5)
        self.assertEqual(counter.expires_at, start + timedelta(seconds=900))

    def test_expired_window_resets_at_boundary(self):
        start = timezone.now()
        with patch("legacy_people.rate_limits.timezone.now", return_value=start):
            self.assertTrue(consume_attempt("login_test", 1, 900))
            self.assertFalse(consume_attempt("login_test", 1, 900))
        with patch("legacy_people.rate_limits.timezone.now", return_value=start + timedelta(seconds=900)):
            self.assertEqual(get_attempts("login_test"), 0)
            self.assertTrue(consume_attempt("login_test", 1, 900))
            self.assertFalse(consume_attempt("login_test", 1, 900))
        self.assertEqual(RateLimit.objects.get(key="login_test").attempts, 1)

    def test_cache_reset_does_not_reset_shared_counter(self):
        self.assertTrue(consume_attempt("login_test", 1, 900))
        cache.clear()
        self.assertEqual(get_attempts("login_test"), 1)
        self.assertFalse(consume_attempt("login_test", 1, 900))

    def test_scopes_and_clients_have_independent_limits(self):
        for key in ("login_8.8.8.8", "form_8.8.8.8", "login_1.1.1.1"):
            self.assertTrue(consume_attempt(key, 1, 900))
            self.assertFalse(consume_attempt(key, 1, 900))

    def test_cleanup_preserves_active_limits(self):
        RateLimit.objects.create(key="expired", attempts=5, expires_at=timezone.now() - timedelta(seconds=1))
        self.assertTrue(consume_attempt("active", 1, 900))
        call_command("cleanup_rate_limits", stdout=StringIO())
        self.assertFalse(RateLimit.objects.filter(key="expired").exists())
        self.assertFalse(consume_attempt("active", 1, 900))


class ConcurrentCounterTests(TransactionTestCase):
    def test_concurrent_workers_cannot_exceed_quota(self):
        if connection.vendor == "sqlite" and connection.creation.is_in_memory_db(connection.settings_dict["NAME"]):
            self.skipTest("SQLite concurrency needs a file-backed test database.")

        def reserve(_):
            try:
                return consume_attempt("concurrent_test", 5, 900)
            finally:
                connections.close_all()

        # Race creation as well as incrementing: all workers start with no counter.
        with ThreadPoolExecutor(max_workers=8) as workers:
            results = list(workers.map(reserve, range(20)))
        self.assertEqual(sum(results), 5)
        self.assertEqual(get_attempts("concurrent_test"), 5)


@override_settings(TRUSTED_PROXY_CIDRS=[])
class RequestRateLimitTests(TestCase):
    def test_form_rejects_twenty_first_submission_despite_spoofed_headers(self):
        data = {
            "name": "Rate Limit User", "email": "rate@example.com", "whatsapp": "+5511999999999",
            "time_lagoinha": "menos_6_meses", "feeling": "1",
            "has_gc": "no", "wants_chat": "no", "frequents_legacy": "yes",
        }
        for attempt in range(21):
            response = self.client.post(
                reverse("legacy_people:main_form"), data=data,
                REMOTE_ADDR="8.8.8.8", HTTP_X_FORWARDED_FOR=f"1.1.1.{attempt + 1}",
            )
            self.assertEqual(response.status_code, 302 if attempt < 20 else 429)
        self.assertEqual(Person.objects.count(), 20)

    def test_form_get_does_not_consume_quota(self):
        for _ in range(21):
            response = self.client.get(reverse("legacy_people:main_form"))
            self.assertEqual(response.status_code, 200)
        self.assertFalse(RateLimit.objects.exists())

    def test_invalid_form_posts_consume_quota(self):
        for _ in range(20):
            self.assertEqual(self.client.post(reverse("legacy_people:main_form")).status_code, 200)
        self.assertEqual(self.client.post(reverse("legacy_people:main_form")).status_code, 429)

    def test_login_spoofing_cannot_bypass_lockout(self):
        with patch("legacy_people.views.authenticate", return_value=None) as authenticate:
            for attempt in range(6):
                response = self.client.post(
                    reverse("legacy_people:login"), {"username": "admin", "password": "bad"},
                    REMOTE_ADDR="8.8.8.8", HTTP_X_FORWARDED_FOR=f"1.1.1.{attempt + 1}",
                )
            self.assertContains(response, "Bloqueado")
            self.assertEqual(authenticate.call_count, 5)

    @override_settings(TRUSTED_PROXY_CIDRS=["10.0.0.1/32"])
    def test_clients_behind_trusted_proxy_have_independent_quotas(self):
        with patch("legacy_people.views.authenticate", return_value=None) as authenticate:
            for _ in range(5):
                self.client.post(
                    reverse("legacy_people:login"), {"username": "admin", "password": "bad"},
                    REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="8.8.8.8",
                )
            response = self.client.post(
                reverse("legacy_people:login"), {"username": "admin", "password": "bad"},
                REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="1.1.1.1",
            )
            self.assertNotContains(response, "Bloqueado")
            self.assertEqual(authenticate.call_count, 6)
