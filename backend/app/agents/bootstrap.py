from backend.app.agents.registry import AgentRegistry

from backend.app.agents.test_agent import TestAgent
from backend.app.agents.classification_agent import ClassificationAgent


def register_agents():

    AgentRegistry.register(
        TestAgent()
    )
    AgentRegistry.register(
    ClassificationAgent()
)