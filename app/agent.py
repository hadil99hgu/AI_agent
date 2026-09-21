from app.models import Plan
from app.services import get_customer_plan, upgrade_customer_plan,customer_exists
from app.models import AgentDecision, Plan, ChatRequest

def handle_message2(
    customer_id: str,
    message: str,
) -> str:
    message_lower = message.lower()
    if not customer_exists(customer_id):
        return "Customer not found."
    
    if "upgrade" in message_lower:
        
        for plan in Plan:
             if plan.value.lower() in message_lower:
                  new_plan = plan   
                  break
        else:
            return "Please specify a valid plan to upgrade to (Basic, Plus, Premium)."

        success = upgrade_customer_plan(customer_id, new_plan)
        if success:
            return f"Your plan has been upgraded to {new_plan.value}."
        else:
            return "Upgrade not allowed. You can only upgrade to a higher plan."
    if "plan" in message_lower :
            plan = get_customer_plan(customer_id)
            return f"Your current plan is: {plan.value}."
    return "I can help you check or upgrade your plan."

def decision_action(message :str) -> AgentDecision:
    message_lower = message.lower()
    if "upgrade" in message_lower:
         for plan in Plan:
              if plan.value.lower() in message_lower:
                   new_plan=plan
                   return AgentDecision(action="UPGRADE_PLAN", target_plan=new_plan)
         else:
            return AgentDecision(action="ASK_UPGRADE_PLAN")
    if 'plan' in message_lower:
        return AgentDecision(action="GET_PLAN")
    return AgentDecision(action="FALLBACK")

def handle_message(customer_id: str, message: str,decision_function=decision_action) -> str:
  
     if not customer_exists(customer_id):
          return "Customer not found."
     
     decision = decision_function(message)

     if decision.action == "UPGRADE_PLAN":
          target_plan=decision.target_plan

          if target_plan is None:
              return "Please specify a valid plan to upgrade to (Basic, Plus, Premium)."
          upgrade_success = upgrade_customer_plan(customer_id, target_plan)

          if not upgrade_success:
            return "Upgrade not allowed. You can only upgrade to a higher plan."
          return f"Your plan has been upgraded to {target_plan.value}."
     
     elif decision.action == "ASK_UPGRADE_PLAN":
            return "Please specify a valid plan to upgrade to (Basic, Plus, Premium)."
    
     elif decision.action == "GET_PLAN":
            plan = get_customer_plan(customer_id)
            return f"Your current plan is: {plan.value}."
     
     return "I can help you check or upgrade your plan."