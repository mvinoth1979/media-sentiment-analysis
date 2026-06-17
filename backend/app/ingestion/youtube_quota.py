import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)


class YouTubeQuotaManager:
    DAILY_LIMIT = 10_000
    SAFETY_MARGIN = 500   # never touch the last 500 units
    SEARCH_COST = 100
    OTHER_COST = 1

    def __init__(self) -> None:
        self._units_used = 0
        self._reset_date = datetime.now(timezone.utc).date()
        self._circuit_open = False

    def _reset_if_new_day(self) -> None:
        today = datetime.now(timezone.utc).date()
        if today > self._reset_date:
            self._units_used = 0
            self._reset_date = today
            self._circuit_open = False
            log.info("YouTube quota counter reset for %s", today)

    @property
    def _available(self) -> int:
        return self.DAILY_LIMIT - self.SAFETY_MARGIN - self._units_used

    def can_search(self) -> bool:
        self._reset_if_new_day()
        return not self._circuit_open and self._available >= self.SEARCH_COST

    def can_fetch(self) -> bool:
        self._reset_if_new_day()
        return not self._circuit_open and self._available >= self.OTHER_COST

    def record_search(self) -> None:
        self._units_used += self.SEARCH_COST

    def record_fetch(self) -> None:
        self._units_used += self.OTHER_COST

    def trip(self) -> None:
        self._circuit_open = True
        log.warning(
            "YouTube quota circuit breaker opened — %d units used today, "
            "skipping all YouTube collection until UTC midnight",
            self._units_used,
        )

    @property
    def units_used(self) -> int:
        return self._units_used

    @property
    def is_open(self) -> bool:
        return self._circuit_open


# Module-level singleton — mirrors the NLP circuit_breaker.py pattern
quota_manager = YouTubeQuotaManager()
