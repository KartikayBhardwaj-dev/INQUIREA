from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolExecutionStatus(str, Enum):
    """Execution status for a tool call."""

    SUCCESS = "success"
    FAILED = "failed"
    INVALID_TOOL = "invalid_tool"
    VALIDATION_ERROR = "validation_error"


class ToolMetadata(BaseModel):
    """
    Schema representing tool metadata used by LLM planners
    for tool discovery.
    """

    name: str = Field(
        ...,
        description="Unique identifier for the tool.",
    )

    description: str = Field(
        ...,
        description="Human-readable explanation of what the tool does.",
    )

    args_schema: Optional[dict[str, Any]] = Field(
        default=None,
        description="JSON Schema or argument descriptions expected by the tool.",
    )


class ToolCallRequest(BaseModel):
    """
    Structured request dispatched from QueryPlanner
    to ChatToolExecutor.
    """

    tool_name: str = Field(
        ...,
        description="Name of the tool to invoke.",
    )

    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed to the tool.",
    )


class ToolErrorDetail(BaseModel):
    """
    Detailed error payload returned when tool execution fails.
    """

    error_code: str = Field(
        ...,
        description="Machine-readable error classification.",
    )

    message: str = Field(
        ...,
        description="Human-readable explanation of the error.",
    )

    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional diagnostic information.",
    )


class ToolCallResponse(BaseModel):
    """
    Standardized internal response returned by ChatToolExecutor.
    """

    status: ToolExecutionStatus = Field(
        ...,
        description="Status of the tool execution.",
    )

    success: bool = Field(
        ...,
        description="Whether the tool execution succeeded.",
    )

    tool_name: str = Field(
        ...,
        description="Name of the executed tool.",
    )

    result: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Structured result returned by the tool. "
            "For draft actions this contains draft_id, email_id, "
            "draft, approval status, Gmail state, etc."
        ),
    )

    error: Optional[str] = Field(
        default=None,
        description="Concise human-readable error summary.",
    )

    error_detail: Optional[ToolErrorDetail] = Field(
        default=None,
        description="Structured error details if execution failed.",
    )

    class Config:
        use_enum_values = True


class ToolExecutionResult(BaseModel):
    """
    Standardized payload returned by an individual tool
    before ChatToolExecutor wraps it in ToolCallResponse.

    The `data` field contains the structured action result.

    Example:

    {
        "message": "Draft generated successfully.",
        "data": {
            "draft_id": 12,
            "email_id": 45,
            "draft": "Hi Google Team...",
            "version": 1,
            "tone": "professional",
            "approval_status": "pending",
            "gmail_draft_id": "abc123",
            "is_sent": false
        }
    }
    """

    message: str = Field(
        ...,
        description="Primary user-facing message.",
    )

    data: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Structured action result returned by the tool."
        ),
    )

    emails_found: int = Field(
        default=0,
        ge=0,
        description="Number of emails processed or retrieved.",
    )

    retrieved_emails: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Email metadata returned by the tool.",
    )