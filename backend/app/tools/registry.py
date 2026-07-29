from __future__ import annotations

import logging
from typing import Any

from backend.app.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Global registry for Chat Tools (Level 2 AI Tool Calling).
    
    Provides both class-level singleton access and instance methods for tool lookup,
    existence validation, schema listing, and registration.
    """

    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """
        Register a tool instance globally by its unique name.
        """
        if not hasattr(tool, "name") or not tool.name:
            raise ValueError("Tool instance must have a valid non-empty 'name' attribute.")

        cls._tools[tool.name] = tool
        logger.info("Registered tool: '%s' (%s)", tool.name, tool.__class__.__name__)

    @classmethod
    def register_many(cls, tools: list[BaseTool]) -> None:
        """
        Batch register multiple tool instances.
        """
        for tool in tools:
            cls.register(tool)

    @classmethod
    def get(cls, name: str) -> BaseTool | None:
        """
        Retrieve a registered tool instance by name. Returns None if not found.
        """
        return cls._tools.get(name)

    @classmethod
    def exists(cls, name: str) -> bool:
        """
        Check whether a tool with the given name is registered.
        """
        return name in cls._tools

    @classmethod
    def all(cls) -> dict[str, BaseTool]:
        """
        Return a copy of all registered tool instances.
        """
        return cls._tools.copy()

    @classmethod
    def list_names(cls) -> list[str]:
        """
        Return a list of all registered tool names.
        """
        return list(cls._tools.keys())

    @classmethod
    def get_tool_definitions(cls) -> list[dict[str, Any]]:
        """
        Returns structured metadata for all registered tools.
        Used by LLM Planners to inspect available tools and their required arguments.
        """
        definitions: list[dict[str, Any]] = []
        for name, tool in cls._tools.items():
            definitions.append(
                {
                    "name": name,
                    "description": getattr(tool, "description", "No description provided."),
                    "args_schema": getattr(tool, "args_schema", None),
                }
            )
        return definitions

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered tools. Primarily used for unit testing reset cycles.
        """
        cls._tools.clear()
        logger.debug("ToolRegistry cleared.")

    @classmethod
    def get_instance(cls) -> ToolRegistry:
        """
        Returns the ToolRegistry singleton instance.
        """
        return cls()

    def get_tool(self, name: str) -> BaseTool | None:
        return self.get(name)

    def validate_tool_exists(self, name: str) -> bool:
        return self.exists(name)

    def list_tools(self) -> list[str]:
        return self.list_names()


registry = ToolRegistry()