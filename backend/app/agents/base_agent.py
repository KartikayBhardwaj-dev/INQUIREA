from abc import ABC, abstractmethod
import logging

from backend.app.agents.state import AgentState
from backend.app.models.agent_run import AgentRun

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    name = "base"

    async def run(self, state: AgentState):
        db = state.get("db")

        try:
            result = await self.execute(state)

            if db is not None:
                db.add(
                    AgentRun(
                        agent_name=self.name,
                        email_id=state.get("email_id"),
                        success=True,
                        result=(
                            result.model_dump()
                            if hasattr(result, "model_dump")
                            else result
                        ),
                    )
                )

            return {
                "success": True,
                "agent": self.name,
                "result": result,
                "error": None,
            }

        except Exception as e:  # Added 'as e' to capture the exception instance
            logger.exception(
                "%s failed for email %s",
                self.name,
                state.get("email_id"),
            )

            if db is not None:
                db.add(
                    AgentRun(
                        agent_name=self.name,
                        email_id=state.get("email_id"),
                        success=False,
                        result={"error": str(e)},
                    )
                )

            state.setdefault("errors", []).append(str(e))

            return {
                "success": False,
                "agent": self.name,
                "result": None,
                "error": str(e),
            }

    @abstractmethod
    async def execute(self, state):
        pass