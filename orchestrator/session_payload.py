"""Serialization helpers for Redis-backed session metadata."""

import base64
import gzip
import json
from typing import Any

SESSION_COMPRESSION_THRESHOLD_BYTES = 32 * 1024
SESSION_COMPRESSED_PREFIX = "gzip:v1:"
# Place 1: Define default version constant under the compression prefix constants
DEFAULT_PAYLOAD_VERSION = "1.0"


def serialize_session_payload(
    session_data: dict[str, Any], version: str = DEFAULT_PAYLOAD_VERSION
) -> str:
    """Serialize session metadata for Redis, compressing only large payloads."""
    # Place 2: Copy dictionary and insert the version field at top of function
    payload = dict(session_data)
    if "version" not in payload:
        payload["version"] = version

    value = json.dumps(payload)
    raw = value.encode("utf-8")

    if len(raw) <= SESSION_COMPRESSION_THRESHOLD_BYTES:
        return value

    compressed = gzip.compress(raw, mtime=0)
    encoded = base64.b64encode(compressed).decode("ascii")
    return f"{SESSION_COMPRESSED_PREFIX}{encoded}"


def deserialize_session_payload(value: str | bytes) -> dict[str, Any]:
    """Deserialize session metadata from Redis, supporting legacy plain JSON."""
    if isinstance(value, bytes):
        value = value.decode("utf-8")

    if value.startswith(SESSION_COMPRESSED_PREFIX):
        encoded = value.removeprefix(SESSION_COMPRESSED_PREFIX)
        compressed = base64.b64decode(encoded.encode("ascii"), validate=True)
        value = gzip.decompress(compressed).decode("utf-8")

    data = json.loads(value)

    # Place 3: Attach default version to legacy payloads before returning
    if isinstance(data, dict) and "version" not in data:
        data["version"] = DEFAULT_PAYLOAD_VERSION

    return data