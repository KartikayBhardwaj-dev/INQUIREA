from langchain_groq import ChatGroq

from backend.app.core.config import (
    get_settings,
)

settings = get_settings()

llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",
    temperature=0,
)