"""Per-profile cache with version-based invalidation.

Every cached entry of a profile embeds the profile's current version in its key. Bumping the version
(`invalidate_profile`) makes every entry of that profile unreachable at once, without having to know their keys;
the orphaned entries just expire by TTL.

The version is a random token, not a counter: if the version key is evicted, a counter would restart from the same
value and bring back stale entries, while a new random token never collides with an old one.
"""

import uuid
from collections.abc import Callable
from typing import Any

from django.core.cache import cache
from django.db import transaction

# Safety net for writes that bypass signals (queryset.update(), bulk_create(), raw SQL)
DEFAULT_TTL = 60 * 60


def _version_key(profile_id: int) -> str:
    return f"profile:{profile_id}:version"


def get_version(profile_id: int) -> str:
    """Current version of the profile's cache, created on first use."""
    version = cache.get(_version_key(profile_id))
    if version is None:
        cache.add(_version_key(profile_id), uuid.uuid4().hex, None)  # add(): never overwrite a concurrent winner
        version = cache.get(_version_key(profile_id)) or uuid.uuid4().hex
    return version


def _bump(profile_id: int) -> None:
    cache.set(_version_key(profile_id), uuid.uuid4().hex, None)


def invalidate_profile(profile_id: int) -> None:
    """Drop every cached entry of the profile.

    Bumps twice on purpose: right now (covers code running outside a transaction) and once the surrounding
    transaction commits (a reader between the first bump and the commit could otherwise cache the old data
    under the new version)."""
    _bump(profile_id)
    transaction.on_commit(lambda: _bump(profile_id))


def get_or_build(profile_id: int, name: str, *params: Any, build: Callable[[], Any], ttl: int = DEFAULT_TTL) -> Any:
    """Return the cached value for (profile, name, params), calling `build` on a miss.

    The version is read BEFORE building: if a write invalidates the profile meanwhile, the (possibly stale) result is
    stored under a version nobody reads anymore."""
    version = get_version(profile_id)
    key = ":".join(["profile", str(profile_id), version, name, *(str(param) for param in params)])

    value = cache.get(key)
    if value is None:
        value = build()
        cache.set(key, value, ttl)
    return value
