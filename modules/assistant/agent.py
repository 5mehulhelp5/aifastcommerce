import asyncio
import json
from typing import List,TypedDict
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from langchain.schema import  BaseMessage
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain.tools import StructuredTool

from db.session import get_db
from modules.catalog.service import get_product_by_id
from modules.cart.service import add_to_cart
from modules.checkout.service import create_order
from modules.cart.schema import CartItemCreate
from modules.checkout.schema import OrderCreate, OrderItemCreate


# ---- Async DB Session Utility ----
@asynccontextmanager
async def get_db_session():
    async with get_db() as session:
        yield session


# ---- Tool Input Schemas ----
class AddToCartInput(BaseModel):
    user_id: int
    product_id: int
    quantity: int


class PlaceOrderItem(BaseModel):
    product_id: int
    quantity: int
    price: float


class PlaceOrderInput(BaseModel):
    user_id: int
    items: List[PlaceOrderItem]


# ---- Async Tool Implementations ----
async def async_view_product_tool(product_id: int):
    async with get_db_session() as db:
        product = await get_product_by_id(int(product_id), db)
        if product:
            return f"Product: {product.name}, Price: {product.price}, Stock: {product.stock}"
        return "Product not found."


async def async_add_to_cart_tool(user_id: int, product_id: int, quantity: int):
    async with get_db_session() as db:
        item = CartItemCreate(user_id=user_id, product_id=product_id, quantity=quantity)
        result = await add_to_cart(item, db)
        return f"Added to cart: Product {result.product_id} x {result.quantity}"


async def async_place_order_tool(user_id: int, items: List[dict]):
    async with get_db_session() as db:
        total = sum(item["price"] * item["quantity"] for item in items)
        order_items = [OrderItemCreate(**item) for item in items]
        order_data = OrderCreate(user_id=user_id, total_amount=total, items=order_items)
        order = await create_order(order_data, db)
        return f"Order placed! Order ID: {order.id}, Total: {order.total_amount}"


# ---- Define Tools ----
view_product_tool = StructuredTool.from_function(
    name="ViewProduct",
    description="View a product by its ID. Input: product_id: int.",
    func=async_view_product_tool,
)

add_to_cart_tool = StructuredTool.from_function(
    name="AddToCart",
    description="Add product to cart with user_id, product_id, quantity.",
    func=async_add_to_cart_tool,
    args_schema=AddToCartInput,
)

place_order_tool = StructuredTool.from_function(
    name="PlaceOrder",
    description="Place order with user_id and list of items (product_id, quantity, price).",
    func=async_place_order_tool,
    args_schema=PlaceOrderInput,
)

tools = [view_product_tool, add_to_cart_tool, place_order_tool]


# ---- Manual conversion to OpenAI function specs ----
def tool_to_openai_function(tool: StructuredTool):
    schema = tool.args_schema.schema() if tool.args_schema else {}
    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": {
            "type": "object",
            "properties": {
                k: {"type": "string"} for k in schema.get("properties", {})
            },
            "required": schema.get("required", []),
        },
    }


functions = [tool_to_openai_function(t) for t in tools]


# ---- Agent State ----
class AgentState(TypedDict):
    messages: List[BaseMessage]


# ---- LangChain / LangGraph Setup ----
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4o-mini",
    functions=functions,
    function_call="auto",
)

system_message = SystemMessage(
    content=(
        "You are an eCommerce assistant. "
        "You can use these tools: ViewProduct, AddToCart, PlaceOrder. "
        "Call them by name with correct parameters."
    )
)


async def call_model(state: AgentState) -> AgentState:
    messages = state["messages"] + [system_message]
    response = await llm.ainvoke(messages)
    messages.append(response)
    return AgentState(messages=messages)


def check_tool_needed(state: AgentState):
    last = state["messages"][-1]
    has_tool_calls = getattr(last, "tool_calls", None)
    has_function_call = "function_call" in getattr(last, "additional_kwargs", {})
    if has_tool_calls or has_function_call:
        return "tools"
    return "end"


async def call_tools(state: AgentState) -> AgentState:
    last = state["messages"][-1]
    tool_results = []

    tool_calls = getattr(last, "tool_calls", None)

    # If no tool_calls attribute or empty, check additional_kwargs for function_call
    if not tool_calls and "function_call" in getattr(last, "additional_kwargs", {}):
        func_call = last.additional_kwargs["function_call"]
        arguments = json.loads(func_call.get("arguments", "{}"))
        # Construct a dummy object with .name and .arguments for compatibility
        tool_calls = [type("ToolCall", (), {"name": func_call["name"], "arguments": arguments})()]

    if not tool_calls:
        return state

    for tool_call in tool_calls:
        name = tool_call.name
        args = tool_call.arguments

        if name == "ViewProduct":
            res = await view_product_tool.func(**args)
        elif name == "AddToCart":
            res = await add_to_cart_tool.func(**args)
        elif name == "PlaceOrder":
            res = await place_order_tool.func(**args)
        else:
            res = f"Unknown tool: {name}"

        tool_results.append(HumanMessage(content=res))

    new_messages = state["messages"]+ tool_results
    return AgentState(messages=new_messages)


workflow = StateGraph(state_schema=AgentState)
workflow.add_node("chat", call_model)
workflow.add_node("tools", call_tools)
workflow.set_entry_point("chat")
workflow.add_conditional_edges("chat", check_tool_needed, {"tools": "tools", "end": END})
workflow.add_edge("tools", "chat")

agent_graph = workflow.compile()


# ---- Final entry point to call in your FastAPI route ----
async def ecommerce_assistant(message: str) -> str:
    initial_state = AgentState(messages=[HumanMessage(content=message)])
  

    state = await agent_graph.ainvoke(initial_state)
    #print("Type of input to ainvoke:", type(state))
    #print("Messages:", state["messages"])
    # Return the last meaningful message content
    for msg in reversed(state["messages"]):
        if msg.content and msg.content.strip():
            return msg.content
    return "Sorry, I could not process your request."
