from fastapi import Request


class WorkflowService:
    @classmethod
    async def run_email_workflow(
        cls,
        state: dict,
        config: dict,
        request: Request,
    ):
        graph = request.app.state.graph

        graph_config = {
            "configurable": {
                "thread_id": str(state["email_id"]),
                **config.get("configurable", {}),
            }
        }

        return await graph.ainvoke(
            state,
            config=graph_config,
        )