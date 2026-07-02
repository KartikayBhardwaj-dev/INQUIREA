from fastapi import Request


class WorkflowService:

    @classmethod
    async def run_email_workflow(
        cls,
        state,
        config: dict,  # Added config parameter to receive external setup (like the DB session)
        request: Request,
    ):

        graph = request.app.state.graph

        # Combine our thread tracking data safely with incoming configurable connections
        graph_config = {
            "configurable": {
                "thread_id": str(state["email_id"]),
                **config.get("configurable", {})  # Merges the live DB session cleanly
            }
        }

        result = await graph.ainvoke(
            state,
            config=graph_config,
        )

        return result