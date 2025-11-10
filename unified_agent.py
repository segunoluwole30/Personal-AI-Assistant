import asyncio
import os
import re
import sys
import io
import subprocess
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, HostedMCPTool, Runner, OpenAIConversationsSession, function_tool, OpenAIChatCompletionsModel

# --- Load environment variables ---
load_dotenv()
ZAPIER_TOKEN = os.getenv("ZAPIER_MCP_TOKEN")
FIRECRAWL_TOKEN = os.getenv("FIRECRAWL_API_KEY")

# --- Ensure UTF-8 Output ---
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ==============================================================
# 🔹 1. Define the Pizza Agent
# ==============================================================

@function_tool
def pizza_order_tool_wrapper(address: str, city: str, state: str, zip_code: str, pizzas: list):
    """Schema for pizza ordering"""
    pass

pizza_model = OpenAIChatCompletionsModel(
    model="gpt-oss-20b-pruned-10.2b",
    openai_client=AsyncOpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lmstudio")
)

pizza_agent = Agent(
    name="PizzaOrderingAgent",
    instructions=(
        "You are an agent that generates **valid, runnable Python 3 code** to place pizza orders.\n"
        "Your code must include:\n"
        "import time\n"
        "from playwright.sync_api import sync_playwright\n"
        "from pizza_order_browser import order_pizzas\n\n"
        "Then call:\n"
        "order_pizzas(address, city, state, zip_code, pizzas)\n\n"
        "Example:\n"
        "from pizza_order_browser import order_pizzas\n"
        "order_pizzas('161 Wellborn Road', 'College Station', 'TX', '77840', [('Ultimate Pepperoni', 2)])\n\n"
        "Do **not** generate the code until you have all required information (address, city, state, zip, pizzas).\n"
        "If information is missing, ask the user questions to gather it before generating any code."
        "When all info is known, output **only raw Python code** — no markdown fences, comments, or explanations."
    ),
    tools=[pizza_order_tool_wrapper],
    model=pizza_model
)

# ==============================================================
# 🔹 2. Define the Cloud Assistant Agent
# ==============================================================

zapier_tool = HostedMCPTool(tool_config={
    "type": "mcp",
    "server_label": "zapier",
    "server_url": "https://mcp.zapier.com/api/mcp/mcp",
    "headers": {"Authorization": f"Bearer {ZAPIER_TOKEN}"},
    "require_approval": "never"
})

firecrawl_tool = HostedMCPTool(tool_config={
    "type": "mcp",
    "server_label": "firecrawl",
    "server_url": f"https://mcp.firecrawl.dev/{FIRECRAWL_TOKEN}/v2/mcp",
    "require_approval": "never"
})

assistant_agent = Agent(
    name="PersonalAssistant",
    instructions=(
        "You are an intelligent multi-domain assistant. "
        "If the user asks to order pizza, delegate the conversation to the 'PizzaOrderingAgent'. "
        "Otherwise, handle the task using your available MCP tools (Zapier or Firecrawl). "
        "Be concise and helpful."
    ),
    tools=[zapier_tool, firecrawl_tool],
)

# ==============================================================
# 🔹 3. Utility Functions for Pizza Execution
# ==============================================================

def clean_code_block(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:python|py)?", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    return cleaned.strip()

async def try_execute_script(code: str) -> tuple[bool, str]:
    try:
        code = clean_code_block(code)
        code = code.replace("\u202f", " ").replace("\xa0", " ")

        if "order_pizzas" not in code:
            code = "from pizza_order_browser import order_pizzas\n" + code

        script_file = "generated_pizza_order.py"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(code + "\n")

        print(f"\n🚀 Running generated script:\n{code}\n---")

        completed = subprocess.run(
            [sys.executable, script_file],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if completed.returncode != 0:
            error_output = (completed.stderr or completed.stdout or "").strip()
            print(f"❌ Script failed:\n{error_output}\n")
            return False, error_output

        return True, ""
    except Exception as e:
        return False, str(e)

# ==============================================================
# 🔹 4. Multi-Agent Control Flow
# ==============================================================

async def main():
    print("🤖 Unified Assistant running. Type your messages (Ctrl+C to quit).")
    session = OpenAIConversationsSession()

    while True:
        user_input = input("You: ")

        # 🔍 Detect if the user is ordering pizza
        if re.search(r"\b(pizza|pepperoni|order|delivery|domino|hungry)\b", user_input, re.I):
            print("🍕 Switching to Pizza Ordering Agent...\n")
            result = await Runner.run(pizza_agent, user_input)
            code = result.final_output.strip()

            if not re.search(r"order_pizzas\s*\(", code):
                print("PizzaAgent:", code)
                continue

            success, last_error = await try_execute_script(code)
            if success:
                print("✅ Pizza order executed successfully!")
            else:
                print("❌ Pizza script failed. Error:", last_error)
        else:
            # Default to cloud assistant
            result = await Runner.run(assistant_agent, user_input, session=session)
            print("Assistant:", result.final_output)

# ==============================================================
# 🔹 Entry Point
# ==============================================================

if __name__ == "__main__":
    asyncio.run(main())
