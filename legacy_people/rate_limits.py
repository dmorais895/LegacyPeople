"""Trusted client identification and database-backed, atomic request limits."""

import ipaddress
from datetime import timedelta

from django.conf import settings
from django.db.models import F
from django.utils import timezone

from .models import RateLimit


def get_client_ip(request):
    """Walk forwarded addresses only while the current hop is a trusted proxy."""
    try:
        peer = ipaddress.ip_address(request.META.get("REMOTE_ADDR", "0.0.0.0"))
    except ValueError:
        return "0.0.0.0"
    trusted_networks = [ipaddress.ip_network(cidr) for cidr in settings.TRUSTED_PROXY_CIDRS]
    current = peer
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        for hop in reversed(forwarded.split(",")):
            if not any(current in network for network in trusted_networks):
                break
            try:
                current = ipaddress.ip_address(hop.strip())
            except ValueError:
                return str(peer)
    return str(current)


def consume_attempt(key, limit, window_seconds):
    """Reserve one attempt using conditional SQL updates; never exceed the limit."""
    now = timezone.now()
    expires_at = now + timedelta(seconds=window_seconds)
    RateLimit.objects.get_or_create(key=key, defaults={"expires_at": expires_at})
    counters = RateLimit.objects.filter(key=key)
    # Only one worker can reset an expired window; subsequent workers increment it.
    if counters.filter(expires_at__lte=now).update(attempts=1, expires_at=expires_at):
        return True
    return bool(counters.filter(expires_at__gt=now, attempts__lt=limit).update(attempts=F("attempts") + 1))


def get_attempts(key):
    """Read the active window's count without extending its expiry."""
    return RateLimit.objects.filter(key=key, expires_at__gt=timezone.now()).values_list(
        "attempts", flat=True
    ).first() or 0


def clear_attempts(key):
    """Reset a client's failed login count after successful authentication."""
    RateLimit.objects.filter(key=key).delete()
