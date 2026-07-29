from backend.app.tools.registry import ToolRegistry

from backend.app.tools.date_tool import DateTool
from backend.app.tools.generate_reply_tool import GenerateReplyTool
from backend.app.tools.rewrite_reply_tool import RewriteReplyTool
from backend.app.tools.save_draft_tool import SaveDraftTool
from backend.app.tools.edit_draft_tool import EditDraftTool
from backend.app.tools.approve_draft_tool import ApproveDraftTool
from backend.app.tools.reject_draft_tool import RejectDraftTool
from backend.app.tools.send_reply_tool import SendReplyTool
from backend.app.tools.update_draft_tool import UpdateDraftTool


def register_tools() -> None:
    """
    Register all static chat tools.
    Dynamic or session-bound tools are looked up via registry when invoked.
    """
    ToolRegistry.register(DateTool())
    ToolRegistry.register(GenerateReplyTool())
    ToolRegistry.register(RewriteReplyTool())
    ToolRegistry.register(SaveDraftTool())
    ToolRegistry.register(EditDraftTool())
    ToolRegistry.register(ApproveDraftTool())
    ToolRegistry.register(RejectDraftTool())
    ToolRegistry.register(SendReplyTool())
    ToolRegistry.register(UpdateDraftTool())