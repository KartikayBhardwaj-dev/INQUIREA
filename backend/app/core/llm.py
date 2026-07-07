from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from backend.app.core.config import get_settings

settings = get_settings()


def get_llm(
    temperature: float | None = None,
    max_output_tokens: int | None = None,
):
    """
    Create an LLM instance based on the configured provider.
    """

    provider = settings.LLM_PROVIDER.lower()

    temp = (
        temperature
        if temperature is not None
        else settings.LLM_TEMPERATURE
    )

    max_tokens = (
        max_output_tokens
        if max_output_tokens is not None
        else settings.LLM_MAX_OUTPUT_TOKENS
    )

    if provider == "google":
        return ChatGoogleGenerativeAI(
            google_api_key=settings.GOOGLE_API_KEY,
            model=settings.LLM_MODEL,
            temperature=temp,
            max_output_tokens=max_tokens,
        )

    elif provider == "groq":
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=temp,
            max_tokens=max_tokens,
        )

    raise ValueError(
        f"Unsupported LLM provider: {settings.LLM_PROVIDER}"
    )


# Shared default instance used by agents
llm = get_llm()