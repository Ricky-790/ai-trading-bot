from pydantic_ai import Agent, Tool
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
from src.constants.llm_prompts import SYSTEM_INSTRUCTIONS
from src.schemas.agent_response_schema import AgentResponse, CreatePositionSchema
import asyncio
from dotenv import load_dotenv

load_dotenv()

settings = OpenRouterModelSettings(
    openrouter_reasoning={
        "effort": "high",
    },
    openrouter_usage={
        "include": True,
    },
)
model = OpenRouterModel("tencent/hy3-preview:free")
# HY3_agent_with_tools = Agent(
#     model,
#     model_settings=settings,
#     system_prompt="Please respond in english only",
# )

HY3_agent = Agent(
    model,
    model_settings=settings,
    system_prompt="Please respond in english only",
    output_type=AgentResponse,
)
