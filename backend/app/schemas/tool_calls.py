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
    """Schema representing tool metadata used by LLM planners for discovery."""
    name: str = Field(..., description="Unique identifier for the tool")
    description: str = Field(..., description="Human-readable explanation of what the tool does")
    args_schema: Optional[dict[str, Any]] = Field(
        default=None, 
        description="JSON Schema or argument descriptions expected by the tool"
    )


class ToolCallRequest(BaseModel):
    """Structured request payload dispatched from QueryPlanner to ChatToolExecutor."""
    tool_name: str = Field(..., description="The name of the tool to be invoked")
    arguments: dict[str, Any] = Field(
        default_factory=dict, 
        description="Arguments dictionary passed to the tool function"
    )


class ToolErrorDetail(BaseModel):
    """Detailed error payload returned when a tool execution fails."""
    error_code: str = Field(..., description="Machine-readable error classification")
    message: str = Field(..., description="Human-readable explanation of the execution error")
    details: Optional[dict[str, Any]] = Field(
        default=None, 
        description="Optional diagnostic information or trace details"
    )


class ToolCallResponse(BaseModel):
    """Standardized output schema returned by ChatToolExecutor."""
    status: ToolExecutionStatus = Field(..., description="Status result of the tool execution")
    success: bool = Field(..., description="Boolean flag indicating overall execution success")
    tool_name: str = Field(..., description="The name of the executed tool")
    result: Optional[dict[str, Any]] = Field(
        default=None, 
        description="Execution output payload returned on success"
    )
    error: Optional[str] = Field(
        default=None, 
        description="Concise human-readable error summary"
    )
    error_detail: Optional[ToolErrorDetail] = Field(
        default=None, 
        description="Structured error details if execution failed"
    )

    class Config:
        use_enum_values = True


class ToolExecutionResult(BaseModel):
    """
    Standardized payload schema for raw tool execution return values 
    before being wrapped by ChatToolExecutor into a ToolCallResponse.
    """
    message: str = Field(..., description="Primary user-facing text or summary response")
    data: Optional[dict[str, Any]] = Field(default=None, description="Raw structured return data")
    emails_found: int = Field(default=0, description="Count of relevant emails processed or retrieved")
    retrieved_emails: list[dict[str, Any]] = Field(
        default_factory=list, 
        description="List of email metadata objects processed during tool call"
    )