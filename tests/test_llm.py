from app.llm import decide_with_llm
from app.models import Plan


def test_llm_get_plan():
    decision = decide_with_llm(
        "What is my current plan?"
    )

    assert decision.action == "GET_PLAN"
    assert decision.target_plan is None


def test_llm_upgrade_plan():
    decision = decide_with_llm(
        "I want to upgrade to Premium"
    )

    assert decision.action == "UPGRADE_PLAN"
    assert decision.target_plan == Plan.PREMIUM


def test_llm_ask_upgrade_plan():
    decision = decide_with_llm(
        "I want to upgrade"
    )

    assert decision.action == "ASK_UPGRADE_PLAN"
    assert decision.target_plan is None


def test_llm_fallback():
    decision = decide_with_llm(
        "Hello, I need help."
    )

    assert decision.action == "FALLBACK"
    assert decision.target_plan is None