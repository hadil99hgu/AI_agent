
from app.models import AgentDecision
from dotenv import load_dotenv
from openai import OpenAI
import os
load_dotenv()


def get_llm_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )



def build_decision_input(message: str) -> list:
    system_prompt = {
            "role": "system",
            "content": (
                "You classify telecom customer requests. "
                "Allowed actions are GET_PLAN, UPGRADE_PLAN, "
                "ASK_UPGRADE_PLAN, and FALLBACK. "

                "Use UPGRADE_PLAN only when the user explicitly asks to upgrade "
                "and names Basic, Plus, or Premium. "
                "For UPGRADE_PLAN, target_plan must be that named plan. "

                "Use ASK_UPGRADE_PLAN when the user wants to upgrade "
                "but does not specify a valid plan. "
                "For ASK_UPGRADE_PLAN, target_plan must be null. "

                "Use GET_PLAN when the user asks for their current plan. "
                "For GET_PLAN, target_plan must be null. "

                "Use FALLBACK otherwise. "
                "For FALLBACK, target_plan must be null. "
            ),
        }
    user_prompt = {
        "role": "user",
        "content": message,
    }
    return [system_prompt, user_prompt]


def parse_agent_decision(
    raw_output: dict,
) -> AgentDecision:
    
    return AgentDecision.model_validate(raw_output)
    


def decide_with_llm(
    message: str,
) -> AgentDecision:
    client = get_llm_client()
    decision_input = build_decision_input(message)
    response = client.responses.parse(
    model="google/gemma-4-26b-a4b-it:free",
    input=decision_input,
    text_format=AgentDecision,
)
    return response.output_parsed

if __name__ == "__main__":
    messages = [
        "What is my current plan?",
        "I want to upgrade to Premium",
        "I want to upgrade",
        "Hello, how are you?",
    ]

    for message in messages:
        decision = decide_with_llm(message)

        print(message)
        print(decision)
        print()

# app/llm.py

