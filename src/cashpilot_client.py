"""
CashPilot API client for Telegram bot.

Handles all HTTP communication with CashPilot backend.
"""

import aiohttp
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)


class CashPilotClient:
    """Async HTTP client for CashPilot API."""

    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        Initialize client.

        Args:
            api_url: Base URL of CashPilot API (e.g., http://localhost:8000)
            api_key: Optional API key for authentication
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> None:
        """Create aiohttp session."""
        self.session = aiohttp.ClientSession()
        logger.info(f"Connected to CashPilot API: {self.api_url}")

    async def disconnect(self) -> None:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            logger.info("Disconnected from CashPilot API")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth if configured."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to CashPilot API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., /cash-sessions)
            json_data: Optional request body

        Returns:
            JSON response

        Raises:
            CashPilotAPIError: If request fails
        """
        # Auto-connect if not connected
        if not self.session:
            await self.connect()

        url = f"{self.api_url}{endpoint}"
        headers = self._get_headers()

        try:
            async with self.session.request(
                method=method,
                url=url,
                json=json_data,
                headers=headers,
            ) as response:
                data = await response.json()

                if response.status >= 400:
                    error_msg = data.get("message", data.get("detail", str(data)))
                    raise CashPilotAPIError(
                        status=response.status,
                        message=error_msg,
                        code=data.get("code", "UNKNOWN_ERROR"),
                    )

                return data

        except aiohttp.ClientError as e:
            raise CashPilotAPIError(
                status=0,
                message=f"Connection failed: {str(e)}",
                code="CONNECTION_ERROR",
            )

    async def open_cash_session(
        self,
        business_id: str,
        cashier_name: str,
        initial_cash: Decimal,
        shift_hours: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Open a new cash session.

        Args:
            business_id: UUID of the business
            cashier_name: Name of the cashier
            initial_cash: Initial cash amount in Gs
            shift_hours: Optional shift hours (e.g., "08:00-16:00")

        Returns:
            Session data with id, status, etc.

        Example response:
            {
                "id": "abc123-xyz",
                "business_id": "biz123",
                "status": "OPEN",
                "cashier_name": "María López",
                "initial_cash": "500000.00",
                "opened_at": "2025-11-03T08:00:00",
                ...
            }
        """
        payload = {
            "business_id": business_id,
            "cashier_name": cashier_name,
            "initial_cash": str(initial_cash),
            "shift_hours": shift_hours,
        }

        logger.info(f"Opening cash session for business {business_id}")
        return await self._request("POST", "/cash-sessions", payload)

    async def close_cash_session(
        self,
        session_id: str,
        final_cash: Decimal,
        envelope_amount: Decimal = Decimal("0.00"),
        credit_card_total: Decimal = Decimal("0.00"),
        debit_card_total: Decimal = Decimal("0.00"),
        bank_transfer_total: Decimal = Decimal("0.00"),
        closing_ticket: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Close a cash session.

        Args:
            session_id: UUID of the session to close
            final_cash: Final cash amount in Gs
            envelope_amount: Amount in envelope
            credit_card_total: Total credit card sales
            debit_card_total: Total debit card sales
            bank_transfer_total: Total bank transfers
            closing_ticket: Optional closing ticket number
            notes: Optional notes

        Returns:
            Updated session data with reconciliation info

        Example response:
            {
                "id": "abc123-xyz",
                "status": "CLOSED",
                "final_cash": "1200000.00",
                "closed_at": "2025-11-03T16:00:00",
                "cash_sales": "1000000.00",
                "total_sales": "2400000.00",
                "difference": "1400000.00",
                ...
            }
        """
        payload = {
            "final_cash": str(final_cash),
            "envelope_amount": str(envelope_amount),
            "credit_card_total": str(credit_card_total),
            "debit_card_total": str(debit_card_total),
            "bank_transfer_total": str(bank_transfer_total),
            "closing_ticket": closing_ticket,
            "notes": notes,
        }

        logger.info(f"Closing cash session {session_id}")
        return await self._request("PUT", f"/cash-sessions/{session_id}", payload)

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session details.

        Args:
            session_id: UUID of the session

        Returns:
            Session data
        """
        logger.info(f"Fetching session {session_id}")
        return await self._request("GET", f"/cash-sessions/{session_id}")

    async def list_sessions(
        self,
        business_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Dict[str, Any]]:
        """
        List cash sessions for a business.

        Args:
            business_id: Optional filter by business
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of sessions
        """
        endpoint = "/cash-sessions"
        params = []

        if business_id:
            params.append(f"business_id={business_id}")
        params.append(f"skip={skip}")
        params.append(f"limit={limit}")

        if params:
            endpoint += "?" + "&".join(params)

        logger.info(f"Listing sessions: {endpoint}")
        return await self._request("GET", endpoint)

    async def get_business(self, business_id: str) -> Dict[str, Any]:
        """
        Get business details.

        Args:
            business_id: UUID of the business

        Returns:
            Business data
        """
        logger.info(f"Fetching business {business_id}")
        return await self._request("GET", f"/businesses/{business_id}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            Health status
        """
        return await self._request("GET", "/health")


class CashPilotAPIError(Exception):
    """Exception raised when CashPilot API returns error."""

    def __init__(self, status: int, message: str, code: str):
        self.status = status
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}")
