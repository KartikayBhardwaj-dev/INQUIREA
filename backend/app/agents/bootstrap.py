from backend.app.agents.registry import (
    AgentRegistry,
)

from backend.app.agents.analysis_agent import (
    AnalysisAgent,
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
        AnalysisAgent()
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