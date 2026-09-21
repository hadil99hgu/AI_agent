from starlette.testclient import TestClient as TestClient
from app.crm import CUSTOMERS
from app.main import app
import pytest
from app.models import Plan

client = TestClient(app)
@pytest.fixture(autouse=True)
def reset_customers():
    CUSTOMERS['C01'].plan=Plan.BASIC
    CUSTOMERS['C02'].plan=Plan.PREMIUM
    CUSTOMERS['C03'].plan=Plan.PLUS



def test_chat_get_existing_customer_plan():
    response = client.post("/chat",
    json={"customer_id": "C01", "message": "What is my current plan?"})
    assert response.status_code == 200
    assert response.json() == {"response": "Your current plan is: Basic."}

def test_chat_get_unknown_customer():
    response = client.post("/chat",
    json={"customer_id": "unknown", "message": "what is my current plan?"})
    assert response.status_code == 200
    assert response.json() == {"response": "Customer not found."}

def test_chat_valid_upgrade():
    response = client.post("/chat",
    json={"customer_id": "C01", "message": "I want to upgrade to Premium"})
    assert response.status_code == 200
    assert response.json() == {"response": "Your plan has been upgraded to Premium."}
    assert CUSTOMERS["C01"].plan == Plan.PREMIUM

def test_get_existing_customer_plan():
    response = client.get("/customers/C01/plan")
    assert response.status_code == 200
    assert response.json() == {"customer_id": "C01", "plan": "Basic"}


def test_get_unknown_customer():
    response = client.get("/customers/unknown/plan")
    assert response.status_code == 404

def test_valid_upgrade():
    response = client.post("/customers/C01/upgrade", 
    json={"new_plan": "Premium"})
    assert response.status_code == 200
    assert response.json() == {"customer_id": "C01", "new_plan": "Premium"}

def test_invalid_upgrade():
     response = client.post("/customers/C02/upgrade", 
     json={"new_plan": "Basic"})
     assert response.status_code == 400
     assert response.json()['detail'] == "Upgrade not allowed"


def test_same_plan_rejected():
    response = client.post("/customers/C01/upgrade", 
    json={"new_plan": "Basic"})
    assert response.status_code == 400
    assert response.json()['detail'] == "Upgrade not allowed"

def test_invalid_plan_is_rejected_by_pydantic():
    response = client.post("/customers/C01/upgrade", 
    json={"new_plan": "InvalidPlan"})
    assert response.status_code == 422

