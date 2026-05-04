from pydantic_ai import Agent, Tool
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from src.constants.llm_prompts import SYSTEM_INSTRUCTIONS
from src.schemas.agent_response_schema import AgentResponse
import asyncio
from dotenv import load_dotenv

load_dotenv()

settings = OpenRouterModelSettings(
    openrouter_reasoning={
        "effort": "low",
    },
    openrouter_usage={
        "include": True,
    },
)
model = OpenRouterModel("openai/gpt-oss-120b:free")
# gpt_agent_with_tools = Agent(
#     model, model_settings=settings, deps_type=str, tools=[Tool(get_name)]
# )
GPT_agent = Agent(
    model,
    model_settings=settings,
    instructions=SYSTEM_INSTRUCTIONS,
    output_type=AgentResponse,
)
