import asyncio
import logging
import random
import time
from email.utils import parsedate_to_datetime
from typing import Any

from httpx import HTTPStatusError

from backend.app.core.config import get_settings
from backend.app.services.token_estimator import (
    TokenEstimator,
)
from backend.app.services.token_rate_limiter import (
    token_rate_limiter,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """
    Central gateway for all LLM requests.

    Responsibilities:
    - Global concurrency limiting.
    - Global token rate limiting.
    - Automatic retry for provider rate limits.
    - Single entry point for every LLM call.
    """

    def __init__(self):
        self._semaphore = asyncio.Semaphore(
            settings.LLM_MAX_CONCURRENT_REQUESTS
        )
        self._current_concurrency = (
    settings.LLM_MAX_CONCURRENT_REQUESTS
)

        self._min_concurrency = max(
    1,
    settings.LLM_MIN_CONCURRENT_REQUESTS,
)
    def _decrease_concurrency(self) -> None:
        """
    Reduce concurrency after rate limiting.
    """

        if self._current_concurrency > self._min_concurrency:

            self._current_concurrency -= 1

            self._semaphore = asyncio.Semaphore(
            self._current_concurrency
        )

            logger.warning(
            "Reducing LLM concurrency to %s",
            self._current_concurrency,
        )


    def _increase_concurrency(self) -> None:
        """
    Slowly increase concurrency after successful requests.
        """

        if (
        self._current_concurrency
        < settings.LLM_MAX_CONCURRENT_REQUESTS
        ):
            self._current_concurrency += 1

            self._semaphore = asyncio.Semaphore(
            self._current_concurrency
        )

            logger.info(
            "Increasing LLM concurrency to %s",
            self._current_concurrency,
        )
    def _retry_after_seconds(
        self,
        exc: HTTPStatusError,
    ) -> float | None:
        """
        Parse Retry-After header if provided by the LLM provider.
        """

        response = exc.response

        if response is None:
            return None

        retry_after = response.headers.get(
            "Retry-After"
        )

        if retry_after is None:
            return None

        try:
            return float(retry_after)

        except ValueError:
            pass

        try:

            retry_time = parsedate_to_datetime(
                retry_after
            )

            return max(
                0.0,
                retry_time.timestamp()
                - time.time(),
            )

        except Exception:
            return None

    def _backoff(
        self,
        attempt: int,
    ) -> float:
        """
        Exponential backoff with jitter.
        """

        delay = min(
            settings.LLM_INITIAL_BACKOFF
            * (2**attempt),
            settings.LLM_MAX_BACKOFF,
        )

        jitter = random.uniform(
            0,
            delay * 0.2,
        )

        return delay + jitter

    async def ainvoke(
        self,
        chain: Any,
        inputs: dict,
        estimated_tokens: int | None = None,
    ):

        estimated_tokens = (
            estimated_tokens
            or TokenEstimator.estimate(inputs)
        )

        logger.debug(
            "Estimated request size: %s tokens",
            estimated_tokens,
        )

        for attempt in range(
            settings.LLM_MAX_RETRIES + 1
        ):

            await token_rate_limiter.acquire(
                estimated_tokens
            )

            try:

                async with self._semaphore:

                    logger.debug(
                        "Sending LLM request (attempt %s).",
                        attempt + 1,
                    )

                    result = await chain.ainvoke(inputs)

                    self._increase_concurrency()

                    return result

            except Exception as exc:

                wait = None

                if isinstance(
                    exc,
                    HTTPStatusError,
                ):

                    if (
                        exc.response is None
                        or exc.response.status_code != 429
                    ):
                        raise

                    wait = self._retry_after_seconds(
                        exc
                    )

                else:

                    status_code = getattr(
                        exc,
                        "status_code",
                        None,
                    )

                    if status_code != 429:
                        raise

                if wait is None:

                    wait = self._backoff(
                        attempt
                    )
                self._decrease_concurrency()

                logger.warning(
                    (
                        "%s rate limited. "
                        "Retrying in %.2f seconds "
                        "(attempt %s/%s)."
                    ),
                    settings.LLM_PROVIDER,
                    wait,
                    attempt + 1,
                    settings.LLM_MAX_RETRIES,
                )

                await asyncio.sleep(
                    wait
                )

        raise RuntimeError(
            "LLM retry limit exceeded."
        )
    


llm_service = LLMService()