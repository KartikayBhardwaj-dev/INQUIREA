import math
from typing import Any


class TokenEstimator:
    """
    Lightweight token estimator for LLM requests.

    Uses a character-based approximation that works across
    providers (Gemini, OpenAI, Anthropic, etc.) without
    requiring provider-specific tokenizers.
    """

    CHARS_PER_TOKEN = 4

    DEFAULT_RESPONSE_TOKENS = 300

    @classmethod
    def estimate_prompt_tokens(
        cls,
        inputs: dict[str, Any],
    ) -> int:
        """
        Estimate prompt/input tokens.
        """

        total_chars = 0

        for value in inputs.values():

            if value is None:
                continue

            total_chars += len(str(value))

        return max(
            1,
            math.ceil(
                total_chars / cls.CHARS_PER_TOKEN
            ),
        )

    @classmethod
    def estimate_response_tokens(
        cls,
        expected_output_tokens: int | None = None,
    ) -> int:
        """
        Estimate response/output tokens.
        """

        return (
            expected_output_tokens
            or cls.DEFAULT_RESPONSE_TOKENS
        )

    @classmethod
    def estimate(
        cls,
        inputs: dict[str, Any],
        expected_output_tokens: int | None = None,
    ) -> int:
        """
        Estimate total request size.

        = Prompt + Expected Response
        """

        return (
            cls.estimate_prompt_tokens(inputs)
            + cls.estimate_response_tokens(
                expected_output_tokens
            )
        )