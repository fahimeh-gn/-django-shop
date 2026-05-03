from cProfile import Profile
import json
import logging
from typing import Any, Dict, Optional, Tuple
import requests
from requests import Session
from django.conf import settings

from apps.payment.models import PaymentTransaction

logger = logging.getLogger(__name__)


class VandarApi:
    """
    Robust Vandar gateway client
    Reads sensitive configuration from environment variables via Django settings.
    """

    DEFAULT_BASE_URL = "https://ipg.vandar.io/api/v4"

    ENDPOINTS = {
        "send": "/send/",
        "verify": "/verify/",
        "transaction": "/transaction/",
    }

    def __init__(
        self,
        request=None,
        *,
        session: Optional[Session] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        callback_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:

        self.request = request
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries

        # Read from settings (.env)
        self.api_key = api_key or getattr(settings, "VANDAR_API_KEY", None)
        self.base_url = (base_url or getattr(settings, "VANDAR_BASE_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        self.callback_url = callback_url or getattr(settings, "VANDAR_CALLBACK_URL", None)

        if not self.api_key:
            raise ValueError("VANDAR_API_KEY is not configured")

        if not self.callback_url:
            raise ValueError("VANDAR_CALLBACK_URL is not configured")

           
    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    def _url(self, key: str) -> str:
        return f"{self.base_url}{self.ENDPOINTS[key]}"

    def _post(self, url: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:

        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.post(
                    url,
                    json=data,
                    headers=self._headers(),
                    timeout=self.timeout,
                )

                try:
                    body = resp.json()
                except json.JSONDecodeError:
                    body = {"raw": resp.text}

                if not (200 <= resp.status_code < 300):
                    logger.warning(
                        "VandarApi non-2xx response",
                        extra={
                            "status_code": resp.status_code,
                            "url": url,
                            "data": data,
                            "body": body,
                            "attempt": attempt,
                        },
                    )

                return resp.status_code, body

            except requests.RequestException as exc:
                last_exc = exc
                logger.warning(
                    "VandarApi request exception",
                    extra={
                        "url": url,
                        "data": data,
                        "attempt": attempt,
                        "error": str(exc),
                    },
                )

        logger.error(
            "VandarApi all retries failed",
            extra={"url": url, "data": data, "error": str(last_exc) if last_exc else None},
        )

        return 0, {"status": 400, "message": "Gateway connection error"}

    def _normalize_create_payload(self, order_id: int, amount: int) -> Dict[str, Any]:

        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "amount": int(amount),
            "callback_url": self.callback_url,
            "factorNumber": str(order_id),
        }

    

        return payload

    def _is_verify_success(self, body: Dict[str, Any]) -> bool:
        try:
            return int(body.get("status", 0)) == 1 and int(body.get("code", 0)) in {1, 2}
        except Exception:
            return False

    def create_transaction(self, order_id: int, amount: int) -> Dict[str, Any]:

        url = self._url("send")
        data = self._normalize_create_payload(order_id, amount)

        status, body = self._post(url, data)
        body.setdefault("_http_status", status)

        return body

    def verify_transaction(self, token: str) -> Dict[str, Any]:

        try:
            ow = PaymentTransaction.objects.get(mellipay_track_id=token)
        except PaymentTransaction.DoesNotExist:
            return {"status": 400, "message": "Transaction not found", "code": -1}

        url = self._url("verify")
        data = {
            "api_key": self.api_key,
            "token": token,
        }

        status, body = self._post(url, data)
        body.setdefault("_http_status", status)

        if self._is_verify_success(body):

            if ow.status != "100" or not ow.is_completed:
                ow.status = "100"
                ow.is_completed = True
                ow.save(update_fields=["status", "is_completed"])

        else:

            if not ow.is_completed:
                ow.is_completed = False
                ow.save(update_fields=["is_completed"])

        return body

    def inquiry_transaction(self, token: str) -> Dict[str, Any]:

        url = self._url("transaction")

        data = {
            "api_key": self.api_key,
            "token": token,
        }

        status, body = self._post(url, data)
        body.setdefault("_http_status", status)

        return body
