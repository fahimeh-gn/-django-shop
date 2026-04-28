import json
import logging
from typing import Any, Dict, Optional, Tuple

import requests
from requests import Session
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from account.models import Account_Vandar
from customer.models import Customer
from exchange.models import Site_Settings
from wallet.models import Online_Wallet

logger = logging.getLogger(__name__)


class VandarApi:
    """
    A robust, testable Vandar gateway client.
    - Uses dependency injection for HTTP session and config.
    - Provides typed, validated responses.
    - Centralized error handling and structured logging.
    """

    DEFAULT_BASE_URL = "https://ipg.vandar.io/api/v4"
    # Mapping for Vandar endpoints
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
        """
        Parameters
        ----------
        request : HttpRequest | None
            Optional Django request (used for user context).
        session : requests.Session | None
            Injectable HTTP session for testability and connection reuse.
        base_url : str | None
            Override base URL (useful for sandbox).
        api_key : str | None
            Override API key (useful for tests/alt-accounts).
        callback_url : str | None
            Override callback URL.
        timeout : int
            Request timeout (seconds).
        max_retries : int
            Max retry count for transient network errors.
        """
        self.request = request
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries

        # Resolve configuration from DB if not provided
        if api_key is None or base_url is None or callback_url is None:
            try:
                setting = Site_Settings.objects.get(code=1001)
                vandar = Account_Vandar.objects.get(code=1000)
            except ObjectDoesNotExist:
                logger.error("VandarApi: Required settings not found (Site_Settings code=1001 or Account_Vandar code=1000)")
                raise

            resolved_api_key = vandar.DecryptText.get("vandar_apikey")
            if not resolved_api_key:
                raise ValueError("VandarApi: 'vandar_apikey' missing in Account_Vandar.DecryptText")

            self.api_key = api_key or resolved_api_key
            self.base_url = (base_url or getattr(settings, "VANDAR_BASE_URL", self.DEFAULT_BASE_URL)).rstrip("/")
            # Ensure callback ends with a trailing slash if endpoint expects it
            base_site_url = getattr(settings, "SITE_BASE_URL", None) or getattr(setting, "url", "").rstrip("/")
            default_callback = f"{base_site_url}/customer/wallet/payment/verify/vandar/".replace("//", "/").replace(":/", "://")
            self.callback_url = (callback_url or getattr(settings, "VANDAR_CALLBACK_URL", default_callback))
        else:
            self.api_key = api_key
            self.base_url = base_url.rstrip("/")
            self.callback_url = callback_url

        # Optional user context
        self.mobile: Optional[str] = None
        self.national_id: Optional[str] = None

        if request and getattr(request, "user", None) and request.user.is_authenticated:
            try:
                customer = Customer.objects.get(req_user=request.user)
                self.mobile = customer.mobile or None
                self.national_id = customer.national_id or None
            except Customer.DoesNotExist:
                # Not critical for payment creation
                logger.info("VandarApi: Customer not found for user; proceeding without mobile/national_id")

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    def _url(self, key: str) -> str:
        return f"{self.base_url}{self.ENDPOINTS[key]}"

    def _post(self, url: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """
        Resilient POST with limited retries and structured logging.

        Returns
        -------
        (status_code, json_response)
        """
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.post(url, json=data, headers=self._headers(), timeout=self.timeout)
                # Best-effort JSON parsing
                try:
                    body = resp.json()
                except json.JSONDecodeError:
                    body = {"raw": resp.text}

                # Log non-2xx once
                if not (200 <= resp.status_code < 300):
                    logger.warning(
                        "VandarApi non-2xx",
                        extra={"status_code": resp.status_code, "url": url, "data": data, "body": body, "attempt": attempt},
                    )
                return resp.status_code, body
            except requests.RequestException as exc:
                last_exc = exc
                logger.warning(
                    "VandarApi request exception",
                    extra={"url": url, "data": data, "attempt": attempt, "error": str(exc)},
                )
        # All attempts failed
        logger.error("VandarApi: All retries failed", extra={"url": url, "data": data, "error": str(last_exc) if last_exc else None})
        return 0, {"status": 400, "message": "خطای اتصال به درگاه. لطفاً دوباره تلاش کنید."}

    def _normalize_create_payload(self, order_id: int, amount: int) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "amount": int(amount),
            "callback_url": self.callback_url,
            "factorNumber": str(order_id),
        }
        # If you want Vandar to pre-fill mobile/national id
        if self.mobile:
            payload["mobile_number"] = self.mobile
        if self.national_id:
            payload["national_code"] = self.national_id
        return payload

    def _is_verify_success(self, body: Dict[str, Any]) -> bool:
        """
        Based on Vandar v4 docs:
        - status == 1 and code in {1, 2} typically means success (paid/verified).
        """
        try:
            return int(body.get("status", 0)) == 1 and int(body.get("code", 0)) in {1, 2}
        except Exception:
            return False

    # -----------------------------
    # Public API
    # -----------------------------
    def create_transaction(self, order_id: int, amount: int) -> Dict[str, Any]:
        """
        Create a Vandar transaction and return gateway response.
        Expected success response should contain a token or link.
        """
        url = self._url("send")
        data = self._normalize_create_payload(order_id, amount)
        status, body = self._post(url, data)
        body.setdefault("_http_status", status)
        return body

    def verify_transaction(self, token: str) -> Dict[str, Any]:
        """
        Verify a Vandar transaction by token.
        Also updates Online_Wallet (idempotent).
        """
        try:
            ow = Online_Wallet.objects.get(mellipay_track_id=token)
        except Online_Wallet.DoesNotExist:
            return {"status": 400, "message": "تراکنش یافت نشد", "code": -1}

        url = self._url("verify")
        data = {"api_key": self.api_key, "token": token}
        status, body = self._post(url, data)
        body.setdefault("_http_status", status)

        # Update wallet state once based on response
        if self._is_verify_success(body):
            if ow.status != "100" or not ow.is_completed:
                ow.status = "100"
                ow.is_completed = True
                ow.save(update_fields=["status", "is_completed"])
        else:
            # Mark as failed only if not already completed
            if not ow.is_completed:
                ow.is_completed = False
                ow.save(update_fields=["is_completed"])

        return body

    def inquiry_transaction(self, token: str) -> Dict[str, Any]:
        """
        Fetch transaction info (transaction endpoint).
        """
        url = self._url("transaction")
        data = {"api_key": self.api_key, "token": token}
        status, body = self._post(url, data)
        body.setdefault("_http_status", status)
        return body
