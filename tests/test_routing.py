from agent.config import settings
from agent.nodes.testing import route_after_tests


def test_pass_goes_to_reviewer():
    assert route_after_tests({"test_result": {"passed": True}, "fix_attempts": 0}) == "reviewer"


def test_fail_with_attempts_left_goes_to_fixer():
    assert route_after_tests({"test_result": {"passed": False}, "fix_attempts": 0}) == "fixer"


def test_fail_at_limit_goes_to_reviewer():
    s = {"test_result": {"passed": False}, "fix_attempts": settings.max_fix_attempts}
    assert route_after_tests(s) == "reviewer"
