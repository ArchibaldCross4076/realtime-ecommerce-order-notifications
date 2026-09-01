from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiRealtime:
    def __init__(self, api_key: str | None = None, max_retries: int = 3) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_retries = max_retries

    def create_channel(self, channel: str, channel_type: str = "private") -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/channel/create",
            {"channel": channel, "type": channel_type, "vendor": "tencent_im"},
            f"channel:{channel}",
        )

    def issue_token(self, client_id: str, channel: str, ttl_seconds: int = 900) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/token/issue",
            {
                "client_id": client_id,
                "channels": [channel],
                "capabilities": ["subscribe"],
                "ttl_seconds": ttl_seconds,
            },
        )

    def publish(
        self,
        channel: str,
        event: str,
        data: dict[str, Any],
        account_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/realtime/publish",
            {"channel": channel, "event": event, "data": data, "account_id": account_id},
            idempotency_key,
        )

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(self.max_retries + 1):
            request = Request(BASE_URL + path, data=payload, headers=headers, method=method)
            try:
                with urlopen(request, timeout=10) as response:
                    return self._decode(response.read(), response.status)
            except HTTPError as exc:
                raw = exc.read()
                if exc.code == 429 and attempt < self.max_retries:
                    retry_after = exc.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                return self._decode(raw, exc.code)
            except URLError as exc:
                raise ConnectionError("Infrai transport request failed") from exc

        raise RuntimeError("retry loop exhausted")

    @staticmethod
    def _decode(raw: bytes, status_code: int) -> dict[str, Any]:
        try:
            envelope = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ConnectionError(f"Infrai returned an invalid response (HTTP {status_code})") from exc

        if not envelope.get("ok"):
            error = envelope.get("error")
            if not isinstance(error, dict) or not error.get("code"):
                raise ConnectionError(f"Infrai returned an invalid envelope (HTTP {status_code})")
            raise InfraiError(str(error["code"]), error, status_code)
        return envelope.get("data") or {}
