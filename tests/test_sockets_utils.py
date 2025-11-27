import types
import pytest

from sockets.utils.auth import resolve_user
from sockets.utils.gates import should_prompt_login
from workflow_enums import WorkflowStage


def test_resolve_user_with_valid_token():
    token = "valid"

    def verify(tok):
        assert tok == token
        return {"sub": "user123", "name": "Test User"}

    user_id, profile, is_auth = resolve_user(token, None, "sid123", verify)
    assert user_id == "user123"
    assert profile == {"name": "Test User"}
    assert is_auth is True


def test_resolve_user_falls_back_to_anonymous_on_invalid_token():
    def verify(tok):
        return None

    user_id, profile, is_auth = resolve_user("bad", None, "sid9876543210", verify)
    assert user_id.startswith("anon_")
    assert profile is None
    assert is_auth is False


@pytest.mark.parametrize(
    "stage,has_brief,is_auth,expected",
    [
        (WorkflowStage.CREATOR_FINDER, True, False, True),
        (WorkflowStage.OUTREACH_MESSAGE, False, False, True),
        (None, True, False, True),
        (WorkflowStage.CAMPAIGN_BRIEF, False, False, False),
        (WorkflowStage.CREATOR_FINDER, False, True, False),
    ],
)
def test_should_prompt_login(stage, has_brief, is_auth, expected):
    assert should_prompt_login(stage, has_brief, is_auth) is expected
