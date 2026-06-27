from backend.app.agents.registry import (
    AgentRegistry,
)

from backend.app.agents.classification_agent import (
    ClassificationAgent,
)

from backend.app.agents.extraction_agent import (
    ExtractionAgent,
)

from backend.app.agents.summary_agent import (
    SummaryAgent,
)

from backend.app.agents.memory_agent import (
    MemoryAgent,
)

from backend.app.agents.supervisor_agent import (
    SupervisorAgent,
)

from backend.app.agents.reply_agent import (
    ReplyAgent,
)


def register_agents():

    AgentRegistry.register(
        ClassificationAgent()
    )

    AgentRegistry.register(
        ExtractionAgent()
    )

    AgentRegistry.register(
        SummaryAgent()
    )

    AgentRegistry.register(
        MemoryAgent()
    )

    AgentRegistry.register(
        SupervisorAgent()
    )

    AgentRegistry.register(
        ReplyAgent()
    )