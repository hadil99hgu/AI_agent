from app.services import get_customer_plan, upgrade_customer_plan,customer_exists
from app.models import Plan
from app.llm import get_llm_client
import json
from app.rag import search_knowledge_tool
from rag_model import RAGState

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
        return {'success': False, 'error': "CUSTOMER_NOT_FOUND"}

    return {"success": True, "plan": plan.value}

def upgrade_plan_tool(
    customer_id: str,
    target_plan: Plan,
) -> dict:
    output = upgrade_customer_plan(customer_id, target_plan)
    if output:
        return {
            "success": True,
            "new_plan": target_plan.value,
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
                  
        "required":["customer_id","target_plan"],
        "additionalProperties": False,
        "strict" : True}
              
   }
   {
    "type": "function",
    "name": "search_knowledge_tool",
    "description": (
        "Search the telecom knowledge base for information about "
        "plans, roaming, billing, contracts, SIM/eSIM, security, "
        "and troubleshooting."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The question to search for in the knowledge base",
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "strict": True,
}
   ]   
    
def execute_tool(
    tool_name: str,
    arguments: dict,
    rag_state: RAGState,
) -> dict:
    if tool_name == "get_plan_tool":
        customer_id=arguments["customer_id"]
        return get_plan_tool( customer_id)
    elif tool_name=="upgrade_plan_tool":
        customer_id=arguments["customer_id"]
        target_name=Plan(arguments["target_plan"])
        return upgrade_plan_tool(customer_id,target_name)
    elif tool_name == "search_knowledge_tool":
        query = arguments["query"]

        return search_knowledge_tool(
            query=query,
            rag_state=rag_state,
            top_k=3,
        )

    return {
    "success": False,
    "error": "UNKNOWN_TOOL",
}




def run_agent_with_tools(
    customer_id: str,
    message: str,
    rag_state: RAGState,
) -> str:

    client = get_llm_client()

    response = client.responses.create(
        model="openrouter/free",
        input=message,
        tools=TOOL_DEFINITIONS,
    )

    while True:

        function_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # No more tools requested: final LLM answer
        if not function_calls:
            return response.output_text

        tool_outputs = []

        for item in function_calls:

            arguments = json.loads(item.arguments)

            # Identity is controlled by our application,
            # not by the LLM.
            if item.name in {
                "get_plan_tool",
                "upgrade_plan_tool",
            }:
                arguments["customer_id"] = customer_id

            result = execute_tool(
                tool_name=item.name,
                arguments=arguments,
                rag_state=rag_state,
            )

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(result),
            })

        response = client.responses.create(
            model="openrouter/free",
            previous_response_id=response.id,
            input=tool_outputs,
            tools=TOOL_DEFINITIONS,
        )
    # Python object
    #    ↓ json.dumps()
    # JSON string

    # JSON string
    #    ↓ json.loads()
    # Python object


if __name__=='__main__' :
    run_agent_with_tools('c01','I want to get my plan')
