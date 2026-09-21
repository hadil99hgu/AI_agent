from fastapi import FastAPI, HTTPException

from app.services import get_customer_plan, upgrade_customer_plan
from app.models import UpgradeRequest
from app.agent import handle_message
from app.models import ChatResponse, ChatRequest
from app.llm import decide_with_llm
from app.rag import initialize_rag
from app.tool import run_agent_with_tools

rag_state = initialize_rag("knowledge")

app=FastAPI()

@app.get("/customers/{customer_id}/plan")
def read_customer_plan(customer_id: str):
    plan=get_customer_plan(customer_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": customer_id, "plan": plan}

@app.post("/customers/{customer_id}/upgrade")
def upgrade_plan(customer_id : str,request:UpgradeRequest):
    success = upgrade_customer_plan(customer_id, request.new_plan)
    if not success:
        raise HTTPException(status_code=400, detail="Upgrade not allowed")
    return {"customer_id": customer_id, "new_plan": request.new_plan}



@app.post("/chat")
def chat_with_agent(request: ChatRequest) -> ChatResponse:

    response = run_agent_with_tools(
        customer_id=request.customer_id,
        message=request.message,
        rag_state=rag_state,
    )

   

    return ChatResponse(response=response)
