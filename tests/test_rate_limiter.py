from fastapi import FastAPI
from fastapi.testclient import TestClient

from orchestrator.rate_limiter import RateLimiterMiddleware, RouteLimit


# -------------------------
# Fake Redis implementation
# (same shape as tests/test_unit_rate_limiter.py, but tracks a
#  separate counter PER redis_key, so /login and /users don't
#  share state -- matching real sliding-window behaviour)
# -------------------------
class FakeRedisRaw:
    def __init__(self, store):
        self.store = store

    def pipeline(self, transaction=False):
        return FakePipelineProxy(self.store)


class FakePipelineProxy:
    """Records whatever key is used on zremrangebyscore/zadd/etc, since
    the real redis-py pipeline takes the key as the first arg to each call."""

    def __init__(self, store):
        self.store = store
        self.key = None

    def zremrangebyscore(self, key, *args, **kwargs):
        self.key = key
        return self

    def zadd(self, key, *args, **kwargs):
        self.key = key
        self.store[key] = self.store.get(key, 0) + 1
        return self

    def zcard(self, key, *args, **kwargs):
        self.key = key
        return self

    def expire(self, key, *args, **kwargs):
        self.key = key
        return self

    def execute(self):
        count = self.store.get(self.key, 0)
        return [None, None, count, None]


class FakeRedisClient:
    def __init__(self, store):
        self.raw = FakeRedisRaw(store)


# -------------------------
# Helper
# -------------------------
def create_app(monkeypatch, route_limits=None, default_limit=100, default_window=60):
    from orchestrator import cache_manager

    store = {}  # shared counters across requests within one test
    monkeypatch.setattr(
        cache_manager,
        "get_redis_client",
        lambda: FakeRedisClient(store),
    )
    cache_manager.CacheManager._instance = None

    app = FastAPI()
    app.add_middleware(
        RateLimiterMiddleware,
        limit=default_limit,
        window_seconds=default_window,
        route_limits=route_limits,
    )

    @app.get("/login")
    async def login():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"ok": True}
    
    @app.get("/users")
    async def users():
        return {"ok": True}

    return TestClient(app)


# -------------------------
# Tests
# -------------------------
def test_login_hits_its_own_stricter_limit(monkeypatch):
    route_limits = {
        "/login": RouteLimit(limit=2, window_seconds=60),
        "/users": RouteLimit(limit=10, window_seconds=60),
    }
    client = create_app(monkeypatch, route_limits=route_limits)

    assert client.get("/login").status_code == 200
    assert client.get("/login").status_code == 200
    resp = client.get("/login")
    assert resp.status_code == 429


def test_users_is_unaffected_by_login_limit(monkeypatch):
    route_limits = {
        "/login": RouteLimit(limit=2, window_seconds=60),
        "/users": RouteLimit(limit=10, window_seconds=60),
    }
    client = create_app(monkeypatch, route_limits=route_limits)

    # Exhaust /login's limit
    client.get("/login")
    client.get("/login")

    resp = client.get("/login")
    assert resp.status_code == 429

    # /users has its own counter
    for _ in range(5):
        resp = client.get("/users")
        assert resp.status_code == 200


def test_users_enforces_its_own_looser_limit(monkeypatch):
    route_limits = {
        "/login": RouteLimit(limit=2, window_seconds=60),
        "/users": RouteLimit(limit=5, window_seconds=60),
    }
    client = create_app(monkeypatch, route_limits=route_limits)

    for _ in range(5):
        assert client.get("/users").status_code == 200

    resp = client.get("/users")
    assert resp.status_code == 429