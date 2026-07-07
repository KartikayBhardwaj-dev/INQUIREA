import asyncio
import logging
import time

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TokenRateLimiter:
    """
    Global rate limiter shared across all LLM requests.

    Controls:
    - Tokens per minute
    - Requests per minute

    Both buckets refill continuously.
    """

    def __init__(self):

        self.max_tokens = settings.LLM_TOKENS_PER_MINUTE
        self.max_requests = settings.LLM_REQUESTS_PER_MINUTE

        self.available_tokens = float(self.max_tokens)
        self.available_requests = float(self.max_requests)

        self.last_refill = time.monotonic()

        self.lock = asyncio.Lock()

    def _refill(self) -> None:
        """
        Continuously refill token and request buckets.
        """

        now = time.monotonic()

        elapsed = now - self.last_refill

        token_refill = (
            elapsed / 60
        ) * self.max_tokens

        request_refill = (
            elapsed / 60
        ) * self.max_requests

        self.available_tokens = min(
            self.max_tokens,
            self.available_tokens + token_refill,
        )

        self.available_requests = min(
            self.max_requests,
            self.available_requests + request_refill,
        )

        self.last_refill = now

    async def acquire(
        self,
        estimated_tokens: int,
    ) -> None:
        """
        Wait until both a request slot and token budget
        are available.
        """

        estimated_tokens = max(
            1,
            estimated_tokens,
        )

        while True:

            async with self.lock:

                self._refill()

                enough_tokens = (
                    self.available_tokens
                    >= estimated_tokens
                )

                enough_requests = (
                    self.available_requests >= 1
                )

                if (
                    enough_tokens
                    and enough_requests
                ):

                    self.available_tokens -= (
                        estimated_tokens
                    )

                    self.available_requests -= 1

                    logger.debug(
                        "Reserved %s tokens | %.0f tokens left | %.0f requests left",
                        estimated_tokens,
                        self.available_tokens,
                        self.available_requests,
                    )

                    return

                token_wait = 0.0

                if not enough_tokens:

                    shortage = (
                        estimated_tokens
                        - self.available_tokens
                    )

                    token_wait = (
                        shortage
                        / self.max_tokens
                    ) * 60

                request_wait = 0.0

                if not enough_requests:

                    request_wait = (
                        1
                        / self.max_requests
                    ) * 60

                wait_time = max(
                    token_wait,
                    request_wait,
                )

                logger.info(
                    "LLM rate limit reached. Waiting %.2fs.",
                    wait_time,
                )

            await asyncio.sleep(wait_time)

    async def refund(
        self,
        unused_tokens: int,
    ) -> None:
        """
        Refund unused reserved tokens.
        """

        if unused_tokens <= 0:
            return

        async with self.lock:

            self._refill()

            self.available_tokens = min(
                self.max_tokens,
                self.available_tokens
                + unused_tokens,
            )


token_rate_limiter = TokenRateLimiter()