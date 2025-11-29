from typing import Optional
from workflow_enums import WorkflowStage


def should_prompt_login(stage: Optional[WorkflowStage], has_brief: bool, is_authenticated: bool) -> bool:
    """Decide if login is required before proceeding with creator/outreach work."""
    if is_authenticated:
        return False
    if stage in {WorkflowStage.OUTREACH_MESSAGE}:
        return True
    if has_brief and stage is None:
        # Brief exists but stage not set yet; still require login before creator search
        return True
    return False
