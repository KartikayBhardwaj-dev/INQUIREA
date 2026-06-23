from datetime import datetime

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from sqlalchemy.orm import Session

from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
)

from backend.app.core.config import get_settings
from backend.app.models.email import Email
from backend.app.models.email_intelligence import (
    EmailIntelligence,
)

settings = get_settings()


class EmailIntelligenceService:

    llm = ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name="llama-3.1-8b-instant",
        temperature=0,
    )

    @staticmethod
    @retry(
        wait=wait_exponential(
            multiplier=2,
            min=5,
            max=60,
        ),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def process_email(
        db: Session,
        email: Email,
    ):

        existing = (
            db.query(
                EmailIntelligence
            )
            .filter(
                EmailIntelligence.email_id
                == email.id
            )
            .first()
        )

        if existing:
            return existing

        email_content = f"""
Subject:
{email.subject}

Snippet:
{email.snippet}

Body:
{(email.body or '')[:2500]}
"""

        prompt = ChatPromptTemplate.from_template(
            """
You are an expert email intelligence engine.

Analyze the email.

Return ONLY raw JSON.

Do NOT use markdown.
Do NOT use ```json.
Do NOT use comments.
Do NOT explain anything.

Categories:

- opportunity
- deadline
- finance
- job
- internship
- meeting
- reply_required
- promotion
- personal
- other

Priority:

- low
- medium
- high
- urgent

EMAIL

{email_content}

Return exactly:

{{
    "category": "",
    "priority": "",
    "summary": "",
    "confidence": 0.0,
    "tags": [],
    "dates": [],
    "deadlines": [],
    "amounts": [],
    "links": [],
    "organizations": [],
    "contacts": [],
    "action_items": [],
    "requires_reply": false,
    "key_facts": [],
    "custom_entities": {{}}
}}
"""
        )

        chain = (
            prompt
            | EmailIntelligenceService.llm
            | JsonOutputParser()
        )

        result = await chain.ainvoke(
            {
                "email_content": email_content
            }
        )

        intelligence = EmailIntelligence(
            email_id=email.id,
            category=result.get(
                "category"
            ),
            priority=result.get(
                "priority"
            ),
            summary=result.get(
                "summary"
            ),
            confidence=result.get(
                "confidence"
            ),
            tags=result.get(
                "tags",
                [],
            ),
            extracted_data={
                "dates": result.get(
                    "dates",
                    [],
                ),
                "deadlines": result.get(
                    "deadlines",
                    [],
                ),
                "amounts": result.get(
                    "amounts",
                    [],
                ),
                "links": result.get(
                    "links",
                    [],
                ),
                "organizations": result.get(
                    "organizations",
                    [],
                ),
                "contacts": result.get(
                    "contacts",
                    [],
                ),
                "action_items": result.get(
                    "action_items",
                    [],
                ),
                "requires_reply": result.get(
                    "requires_reply",
                    False,
                ),
                "key_facts": result.get(
                    "key_facts",
                    [],
                ),
                "custom_entities": result.get(
                    "custom_entities",
                    {},
                ),
            },
            processed_at=datetime.utcnow(),
        )

        db.add(intelligence)

        email.is_processed = True

        db.commit()

        db.refresh(intelligence)

        return intelligence
    @staticmethod
    async def process_all_unprocessed(
    db: Session,
):
        emails = (
        db.query(Email)
        .filter(
            Email.is_processed == False
        )
        .all()
    )

        processed = 0

        for email in emails:

            try:

                result = await (
                EmailIntelligenceService
                .process_email(
                    db,
                    email,
                )
            )

                if result:
                    processed += 1

            except Exception as e:

                print(
                f"Email {email.id} failed: {e}"
            )

        return processed