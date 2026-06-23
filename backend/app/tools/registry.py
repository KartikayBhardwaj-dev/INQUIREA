class ToolRegistry:

    _tools = {}

    @classmethod
    def register(
        cls,
        tool,
    ):
        cls._tools[
            tool.name
        ] = tool

    @classmethod
    def get(
        cls,
        name,
    ):
        return cls._tools.get(name)