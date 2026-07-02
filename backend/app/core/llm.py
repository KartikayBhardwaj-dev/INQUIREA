from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_groq import ChatGroq

from backend.app.core.config import (
    get_settings,
)

settings = get_settings()

# Setup a global rate-limiting queue. 
# 0.35 requests per second ensures that multiple agents executing steps 
# in parallel will queue up gracefully instead of bursting over the 6,000 TPM limit.
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.35,
    check_every_n_seconds=0.1,
    max_bucket_size=2,
)

llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",
    temperature=0,
    max_retries=5,
    rate_limiter=rate_limiter,  # Safely handles parallel worker bursts natively
)