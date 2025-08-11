from agents.base.agent_factory import build_agent
from utils.prompts import load_prompt

import os

def get_stock_agent(llm):
    from .tools import tools    
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.md")
    prompt_text = load_prompt(prompt_path)

    return build_agent(
        llm=llm,
        tools=tools,
        extra_tools=[],
        prompt=prompt_text,
        name="stock_agent"
    )
