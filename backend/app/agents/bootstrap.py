from backend.app.agents.analysis_agent import AnalysisAgent
from backend.app.agents.registry import AgentRegistry


def register_agents():

    if "analysis_agent" not in AgentRegistry.all():
        AgentRegistry.register(
            AnalysisAgent()
        )