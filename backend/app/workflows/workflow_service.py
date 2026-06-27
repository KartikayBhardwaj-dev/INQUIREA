from backend.app.workflows.email_graph import (
    get_email_graph,
)


class WorkflowService:

    @classmethod
    async def run_email_workflow(
        cls,
        state,
    ):

        config = {
            "configurable": {
                "thread_id": str(
                    state["email_id"]
                )
            }
        }

        async with get_email_graph() as graph:

            result = await graph.ainvoke(
                state,
                config=config,
            )

        return result