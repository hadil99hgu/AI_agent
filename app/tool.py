from app.services import get_customer_plan, upgrade_customer_plan,customer_exists
from app.models import Plan
from app.llm import get_llm_client

# tool
# ├── type
# ├── name
# ├── description
# ├── parameters
# │   ├── type = object
# │   ├── properties
# │   ├── required
# │   └── additionalProperties
# └── strict


def get_plan_tool(customer_id: str) -> dict: 

    plan = get_customer_plan(customer_id)
    if plan is None:
        return {'success': False, 'error': "PLAN_NOT_FOUND"}

    return {"success": True, "plan": plan.value}

def upgrade_plan_tool(
    customer_id: str,
    target_plan: Plan,
) -> dict:
    output = upgrade_customer_plan(customer_id, target_plan)
    if output:
        return {
            "success": True,
            "new_plan": target_plan,
        }

    else:
        if not customer_exists(customer_id):
            return {'success': False, 'error': "CUSTOMER_NOT_FOUND"}
        else:
            return {'success': False, 'error': "UPGRADE_NOT_ALLOWED"}

 
TOOL_DEFINITIONS = [
    {
    "type": "function",
    "name": "get_plan_tool",
    "description": "Get the current plan of a customer",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "The ID of the customer",
                            }
                     },
        "required": ["customer_id"],
        "additionalProperties": False,
                },
    "strict": True
    },

    #Avec strict=True, OpenAI demande notamment 
    # additionalProperties: false dans l’objet parameters,
    #  et tous les champs de properties doivent être dans 
    # required
    

   {"type" : "function",
    "name" : 'upgrade_plan_tool',
    "description" : "Get the current plan of a customer",
    "parameters":{ 
           "type": "object",
           "properties" : {
                "customer_id" : {
                    "type" : 'string',
                    "description" : "ID of the client"

                                 },
                "target_plan":{
                           "type": "string",
                           "enum": ["Basic", "Plus", "Premium"],
                           "description": "plan to upgrade to"

                              },    
                         },
                  },
        "required":["customer_id","target_plan"],
        "additional properties": False,
        "strict" : True
              
   }
   ]   
    
def execute_tool(
    tool_name: str,
    arguments: dict,
) -> dict:
    if tool_name == "get_plan_tool":
        customer_id=arguments["customer_id"]
        return get_plan_tool( customer_id)
    elif tool_name=="upgrade_plan_tool":
        customer_id=arguments["customer_id"]
        target_name=Plan(arguments["targe_plan"])
        return upgrade_plan_tool(customer_id,target_name)
    return {
    "success": False,
    "error": "UNKNOWN_TOOL",
}


def run_agent_with_tools(
    customer_id: str,
    message: str,
) -> str:
    client=get_llm_client()
    response = client.responses.create(
         model="openrouter/free",
        input=message,
        tools=TOOL_DEFINITIONS,
        )
    print(response)
    print(response.output)


if __name__=='__main__' :
    run_agent_with_tools('c01','I want to get my plan')
