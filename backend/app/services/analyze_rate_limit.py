"""
In-memory rate and daily caps for /api/analyze-shade.

Not a substitute for reverse-proxy limits or OpenAI project spend caps —
this is a soft server-side brake before public exposure.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, datetime, timezone
from threading import Lock
from typing import Deque, Dict, Optional


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    detail: str
    status_code: int = 429


class AnalyzeRateLimiter:
    """Process-local IP hourly window + UTC daily global counter."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._ip_hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._day: Optional[date] = None
        self._daily_count: int = 0

    def reset(self) -> None:
        """Test helper — clear all counters."""
        with self._lock:
            self._ip_hits.clear()
            self._day = None
            self._daily_count = 0

    def check_and_record(
        self,
        *,
        client_ip: str,
        per_ip_hour: int,
        daily_cap: int,
        count_toward_daily: bool,
    ) -> RateLimitDecision:
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - 3600
        ip = (client_ip or "unknown").strip() or "unknown"

        with self._lock:
            if self._day != now.date():
                self._day = now.date()
                self._daily_count = 0

            hits = self._ip_hits[ip]
            while hits and hits[0] < cutoff:
                hits.popleft()

            if per_ip_hour > 0 and len(hits) >= per_ip_hour:
                return RateLimitDecision(
                    allowed=False,
                    detail=(
                        "Too many shade analysis requests from this network. "
                        "Please try again later."
                    ),
                )

            if count_toward_daily and daily_cap > 0 and self._daily_count >= daily_cap:
                return RateLimitDecision(
                    allowed=False,
                    detail=(
                        "Shade analysis is temporarily at capacity for today. "
                        "Please try again tomorrow, or use guided analysis without AI."
                    ),
                )

            hits.append(now.timestamp())
            if count_toward_daily and daily_cap > 0:
                self._daily_count += 1

            return RateLimitDecision(allowed=True, detail="", status_code=200)


# Shared singleton for the API process.
analyze_rate_limiter = AnalyzeRateLimiter()
