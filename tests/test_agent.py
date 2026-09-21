import pytest
from app.agent import handle_message, decision_action
from app.crm import CUSTOMERS
from app.llm import decide_with_llm
from app.models import Plan


#python -m pytest tests/test_agent.py -v
@pytest.fixture(autouse=True)
def reset_customers():
    CUSTOMERS['C01'].plan = Plan.BASIC
    CUSTOMERS['C02'].plan = Plan.PREMIUM
    CUSTOMERS['C03'].plan = Plan.PLUS

def test_get_plan():
    response = handle_message("C01", "What is my current plan?")
    assert response == "Your current plan is: Basic."

def test_upgrade_success():
    response = handle_message("C01", "I want to upgrade to Premium")
    assert response == "Your plan has been upgraded to Premium."
    assert CUSTOMERS["C01"].plan == Plan.PREMIUM
def test_upgrade_refusal():
    response = handle_message("C02", "I want to upgrade to Basic")
    assert response == "Upgrade not allowed. You can only upgrade to a higher plan."
    assert CUSTOMERS["C02"].plan == Plan.PREMIUM
def test_unknown_customer():
    response = handle_message("C99", "What is my current plan?")
    assert response == "Customer not found."
def test_invalid_plan():
    response=handle_message("C01", "I want to upgrade to InvalidPlan")
    assert response == "Please specify a valid plan to upgrade to (Basic, Plus, Premium)."

def test_same_plan():
    response = handle_message("C01", "I want to upgrade to Basic")
    assert response == "Upgrade not allowed. You can only upgrade to a higher plan."
    assert CUSTOMERS["C01"].plan == Plan.BASIC

def test_fallback_message():
    response = handle_message("C01", "Hello, I need help.")
    assert response == "I can help you check or upgrade your plan."

def test_decision_get_plan():
    decision = decision_action("What is my current plan?")
    assert decision.action == "GET_PLAN"
    assert decision.target_plan is None


def test_decision_upgrade_plan():
    decision = decision_action("I want to upgrade to Premium")
    assert decision.action == "UPGRADE_PLAN"
    assert decision.target_plan == Plan.PREMIUM

def test_decision_ask_upgrade_plan():
    decision = decision_action("I want to upgrade")
    assert decision.action == "ASK_UPGRADE_PLAN"
    assert decision.target_plan is None

def test_decision_fallback():
    decision = decision_action("Hello, I need help.")
    assert decision.action == "FALLBACK"
    assert decision.target_plan is None