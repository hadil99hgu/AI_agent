from app.models import  Plan
from app.crm import get_customer, save_customer

def customer_exists(customer_id: str) -> bool:
    return get_customer(customer_id) is not None

def get_customer_plan(customer_id: str) -> Plan | None:
    customer = get_customer(customer_id)
    return customer.plan if customer else None

def is_upgrade_allowed(current_plan: Plan, new_plan: Plan) -> bool:
    plan_order = [Plan.BASIC, Plan.PLUS, Plan.PREMIUM]
    return plan_order.index(new_plan) > plan_order.index(current_plan)

def upgrade_customer_plan(customer_id: str, new_plan: Plan) -> bool:
    customer = get_customer(customer_id)
    if customer:
        if is_upgrade_allowed(customer.plan, new_plan):
            
            customer.plan = new_plan
            save_customer(customer)
            return True
    return False
    
        
    