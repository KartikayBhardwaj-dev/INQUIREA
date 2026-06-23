from backend.app.tools.registry import ToolRegistry

from backend.app.tools.date_tool import DateTool


def register_tools():

    ToolRegistry.register(
        DateTool()
    )