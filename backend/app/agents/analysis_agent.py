from langchain_core.output_parsers import (
    JsonOutputParser,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from backend.app.agents.base_agent import (
    BaseAgent,
)
from backend.app.core.llm import llm


class AnalysisAgent(BaseAgent):

    name = "analysis_agent"

    async def execute(
        self,
        state,
    ):

        thread_context = state.get(
            "thread_context",
            "",
        )

        prompt = ChatPromptTemplate.from_template(
            """
You are an advanced production-grade AI Email Intelligence Engine. 
Your goal is to perform deep semantic analysis on ONE email, merging its immediate contents with the provided conversational thread history, and returning an actionable data object.

=========================
TARGET EMAIL DATA
=========================
Subject: {subject}
Sender: {sender}
Body:
{body}

=========================
HISTORICAL THREAD CONTEXT
=========================
{thread_context}

=========================
CRITICAL METADATA CLASSIFICATION SCHEMAS
=========================

1. Category Classification Rules (Choose exactly ONE string):
- "opportunity": New business leads, incoming sales proposals, raw contract discussions, client inquiries.
- "deadline": Explicit time-sensitive actions, project submissions, regulatory alerts, account expirations.
- "finance": Statements, invoices, payment confirmations, payroll receipts, structural bank notifications, renewal charges.
- "job": Employment applications, recruitment follow-ups, interviews, background tracks, offer letters.
- "internship": Apprenticeship tracks, internship outreach, university-partner coordination.
- "meeting": Calendar coordination, schedule requests, Zoom links, meeting adjustments, agendas.
- "reply_required": Casual or operational interpersonal conversations directly requesting a response from the recipient.
- "promotion": Newsletters, advertising campaigns, mass pricing pitches, product product update announcements.
- "automated_notification": Transactional logs, password updates, automated tracking reports, platform status checks.
- "personal": Non-commercial single-sender interpersonal communications (family, close acquaintances, individual peers).
- "other": Catch-all string constraint. Use ONLY if the email defies all structural parameters above.

2. Priority Level Metrics (Choose exactly ONE string):
- "urgent": Immediate action required today (e.g. system downtime, missed commitments, same-day adjustments).
- "high": High-value items, transactional demands, or strict deadlines closing within 48 hours.
- "medium": Active operational or personal text requiring human attention, but lacking immediate deadlines.
- "low": Archival data, mass marketing, cold outreach, transactional receipts, or informational logs requiring no immediate attention.

=========================
STRICT STRUCTURAL OUTPUT SCHEMA
=========================
Your output must match this structural JSON syntax exactly. Ensure all fields use the correct primitive types:

{{
    "category": "opportunity | deadline | finance | job | internship | meeting | reply_required | promotion | automated_notification | personal | other",
    "priority": "low | medium | high | urgent",
    "summary": "A clear, high-signal summary of this single email's primary intent.",
    "thread_summary": "A breakdown of the conversation arc. If thread context is empty, duplicate the main summary here.",
    "extracted_data": {{
        "dates": ["YYYY-MM-DD format if identifiable, otherwise verbatim text"],
        "deadlines": ["Identified target completion milestones"],
        "amounts": ["Extracted numeric currencies or monetary numbers"],
        "links": ["Valid explicit HTTP urls identified in the body"],
        "organizations": ["Companies, universities, or brand entities"],
        "contacts": ["Names, telephone numbers, or explicit email references"],
        "action_items": ["Granular tasks expected to be completed based on the text"],
        "requires_reply": false, 
        "key_facts": ["High-value contextual data points extracted for memory logging"]
    }}
}}

Return ONLY valid JSON. Do not include markdown code block wrapper markers, prefaces, or side-commentary.
"""
        )

        chain = (
            prompt
            | llm
            | JsonOutputParser()
        )

        result = await chain.ainvoke(
            {
                "subject": state["subject"],
                "sender": state["sender"],
                "body": state["body"][:3000],
                "thread_context": thread_context,
            }
        )

        state["category"] = result.get(
            "category"
        )

        state["priority"] = result.get(
            "priority"
        )

        state["summary"] = result.get(
            "summary"
        )

        state["thread_summary"] = result.get(
            "thread_summary"
        )

        state["extracted_data"] = result.get(
            "extracted_data",
            {},
        )

        return state