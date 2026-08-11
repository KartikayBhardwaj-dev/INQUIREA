from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from backend.app.schemas.tool_calls import (
    ToolCallResponse,
    ToolExecutionStatus,
)
from backend.app.tools.base_tool import BaseTool
from backend.app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ChatToolExecutor:
    """
    Executes registered chat tools.

    Responsibilities
    ----------------
    - Resolve tool names
    - Validate required tool arguments
    - Inject shared dependencies
    - Inject authenticated user_id
    - Execute registered tools
    - Normalize tool responses
    - Handle execution errors
    - Log execution metrics

    Contains no business logic.
    """

    REQUIRED_ARGS: dict[str, list[str]] = {
        "send_reply": [
            "draft_id",
        ],
        "update_draft": [
            "draft_id",
        ],
        "save_draft": [
            "draft_id",
        ],
        "approve_draft": [
            "draft_id",
        ],
        "reject_draft": [
            "draft_id",
        ],
        "get_email": [
            "email_id",
        ],
        "generate_reply": [
            "email_id",
        ],
        "rewrite_reply": [
            "draft_id",
        ],
        "edit_draft": [
            "draft_id",
            "content",
        ],
    }

    def __init__(self, db: Session):
        self.db = db

    async def execute(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a registered tool by name.

        The executor owns the tool execution contract.

        Individual tools return their raw result.
        The executor wraps that result into one consistent structure.
        """

        tool: BaseTool | None = ToolRegistry.get(tool_name)

        if tool is None:
            logger.warning(
                "Unknown tool requested: %s",
                tool_name,
            )

            response = ToolCallResponse(
                status=ToolExecutionStatus.INVALID_TOOL,
                success=False,
                tool_name=tool_name,
                result=None,
                error=f"Unknown tool '{tool_name}'.",
            )

            return response.model_dump()

        start = time.perf_counter()

        try:
            logger.info(
                "Executing tool: %s",
                tool_name,
            )

            # -------------------------------------------------
            # Dependency injection
            # -------------------------------------------------

            if "db" not in kwargs:
                kwargs["db"] = self.db

            # -------------------------------------------------
            # Required argument validation
            #
            # user_id is intentionally NOT part of this map.
            # It is injected from the authenticated request.
            # -------------------------------------------------

            required_args = self.REQUIRED_ARGS.get(
                tool_name,
                [],
            )

            missing = [
                argument
                for argument in required_args
                if kwargs.get(argument) is None
            ]

            if missing:
                elapsed = round(
                    (time.perf_counter() - start) * 1000,
                    2,
                )

                logger.warning(
                    "Tool '%s' missing required arguments: %s",
                    tool_name,
                    missing,
                )

                response = ToolCallResponse(
                    status=ToolExecutionStatus.VALIDATION_ERROR,
                    success=False,
                    tool_name=tool_name,
                    result=None,
                    error=(
                        "Missing required arguments: "
                        + ", ".join(missing)
                    ),
                )

                result = response.model_dump()

                # Keep execution time available for internal
                # debugging without changing the core tool contract.
                result["execution_time_ms"] = elapsed

                return result

            # -------------------------------------------------
            # Execute actual tool
            # -------------------------------------------------

            raw_result = await tool.execute(
                **kwargs,
            )

            elapsed = round(
                (time.perf_counter() - start) * 1000,
                2,
            )

            # -------------------------------------------------
            # Normalize tool result
            # -------------------------------------------------

            if isinstance(raw_result, dict):
                normalized_result = raw_result
            else:
                normalized_result = {
                    "data": raw_result,
                }

            response = ToolCallResponse(
                status=ToolExecutionStatus.SUCCESS,
                success=True,
                tool_name=tool_name,
                result=normalized_result,
                error=None,
                error_detail=None,
            )

            result = response.model_dump()

            result["execution_time_ms"] = elapsed

            logger.info(
                "Tool '%s' completed successfully in %sms.",
                tool_name,
                elapsed,
            )

            return result

        except Exception as exc:
            self.db.rollback()

            elapsed = round(
                (time.perf_counter() - start) * 1000,
                2,
            )

            logger.exception(
                "Tool '%s' failed execution.",
                tool_name,
            )

            response = ToolCallResponse(
                status=ToolExecutionStatus.FAILED,
                success=False,
                tool_name=tool_name,
                result=None,
                error=str(exc),
            )

            result = response.model_dump()

            result["execution_time_ms"] = elapsed

            return result