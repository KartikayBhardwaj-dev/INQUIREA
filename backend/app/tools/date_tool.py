from datetime import datetime

from backend.app.tools.base_tool import (
    BaseTool,
)


class DateTool(BaseTool):

    name = "date_tool"

    async def execute(
        self,
        **kwargs,
    ):

        return {
            "current_time":
            datetime.utcnow().isoformat()
        }
    

    