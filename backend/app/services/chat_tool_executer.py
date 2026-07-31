from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from backend.app.tools.base_tool import BaseTool
from backend.app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ChatToolExecutor:
    """
    Executes registered chat tools.

    Responsibilities
    ----------------
    - Resolve tool names
    - Inject shared dependencies
    - Execute registered tools
    - Normalize responses
    - Handle execution errors
    - Log execution metrics

    Contains no business logic.
    """

    def __init__(self, db: Session):
        self.db = db

    async def execute(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Executes a registered tool by name with provided arguments.
        """
        tool: BaseTool | None = ToolRegistry.get(tool_name)

        if tool is None:
            logger.warning("Unknown tool requested: %s", tool_name)
            return {
                "success": False,
                "tool": tool_name,
                "result": None,
                "error": f"Unknown tool '{tool_name}'.",
                "execution_time_ms": 0,
            }

        start = time.perf_counter()

        try:
            logger.info("Executing tool: %s", tool_name)

            # Inject DB session into kwargs if not explicitly supplied
            if "db" not in kwargs:
                kwargs["db"] = self.db
            required_args = {
    "send_reply": ["draft_id"],
    "update_draft": ["draft_id"],
    "save_draft": [],
    "approve_draft": ["draft_id"],
    "reject_draft": ["draft_id"],
    "get_email": ["email_id"],
    "generate_reply": ["email_id"],
}


            missing = [
    arg 
    for arg in required_args.get(tool_name, [])
    if kwargs.get(arg) is None
]

            if missing:
                return {
        "success": False,
        "tool": tool_name,
        "result": None,
        "error": f"Missing required arguments: {missing}",
        "execution_time_ms": 0,
    }
            result = await tool.execute(**kwargs)

            elapsed = round((time.perf_counter() - start) * 1000, 2)
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "error": None,
                "execution_time_ms": elapsed,
            }

        except Exception as exc:
            self.db.rollback()

            elapsed = round((time.perf_counter() - start) * 1000, 2)

            logger.exception("Tool '%s' failed execution.", tool_name)

            return {
        "success": False,
        "tool": tool_name,
        "result": None,
        "error": str(exc),
        "execution_time_ms": elapsed,
    }