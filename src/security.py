"""
Request signature verification for Opal webhook calls.

Opal signs every request with HMAC-SHA256 using a shared secret.

  signing_string = "v0:{X-Opal-Request-Timestamp}:{raw_request_body}"
  X-Opal-Signature = HMAC-SHA256(OPAL_SIGNING_SECRET, signing_string)

Set OPAL_SIGNING_SECRET in your environment to the secret shown in
the Opal UI when you configure the custom connector.
"""

import hashlib
import hmac
import os
import time

from fastapi import Header, Request
from typing_extensions import Annotated

from exceptions import ErrorException

SIGNING_SECRET = os.environ.get("OPAL_SIGNING_SECRET", "")
# Reject requests older than 5 minutes to prevent replay attacks
MAX_AGE_SECONDS = 300


async def get_signature_headers(
    request: Request,
    x_opal_signature: Annotated[str, Header()],
    x_opal_request_timestamp: Annotated[str, Header()],
):
    if not x_opal_signature:
        raise ErrorException(code=401, message="X-Opal-Signature header is missing")
    if not x_opal_request_timestamp:
        raise ErrorException(code=401, message="X-Opal-Request-Timestamp header is missing")

    # Skip verification in local dev when no secret is configured
    if not SIGNING_SECRET:
        return

    try:
        ts = int(x_opal_request_timestamp)
    except ValueError:
        raise ErrorException(code=401, message="X-Opal-Request-Timestamp is not a valid integer")

    if abs(time.time() - ts) > MAX_AGE_SECONDS:
        raise ErrorException(code=401, message="Request timestamp is too old")

    body = await request.body()
    body_str = body.decode("utf-8").strip() if body else "{}"

    signing_string = f"v0:{x_opal_request_timestamp}:{body_str}"
    expected = hmac.new(
        SIGNING_SECRET.encode(),
        signing_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, x_opal_signature):
        raise ErrorException(code=401, message="X-Opal-Signature is invalid")
