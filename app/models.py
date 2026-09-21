from pydantic import BaseModel,NonNegativeFloat
from enum import Enum
from typing import Literal

class Plan(str, Enum):
    BASIC = "Basic"
    PREMIUM = "Premium"
    PLUS = "Plus"

class Customer(BaseModel):
    customer_id: str
    name: str
    plan: Plan
    data_remaining_gb: NonNegativeFloat #   data_remaining_gb: float = Field(ge=0)

class UpgradeRequest(BaseModel):
    new_plan: Plan


class ChatRequest(BaseModel):
    customer_id: str
    message: str
    
class ChatResponse(BaseModel):
    response: str

class AgentDecision(BaseModel):
    action: Literal[
        "GET_PLAN", "UPGRADE_PLAN", "FALLBACK","ASK_UPGRADE_PLAN"]
    
    target_plan: Plan | None = None 

    #la variable plan peut contenir 
    # soit un objet de type Plan, 
    # soit None, et sa valeur par défaut est None.