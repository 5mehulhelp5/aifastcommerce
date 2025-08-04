from agents.base.agent_factory import build_agent
from utils.prompts import load_prompt
import os


def get_shipment_agent(llm): 
    from .tools import tools
    from magento_tools.shared_order_tools import tools as order_tools   
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
    prompt_text = load_prompt(prompt_path)

    return build_agent(
        llm=llm,
        tools=tools,
        extra_tools=order_tools,
        prompt=prompt_text,
        name="shipment_agent"
    )
