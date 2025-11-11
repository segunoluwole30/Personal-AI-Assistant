# HW3 Unified Pizza + MCP Assistant

This README focuses ONLY on:
1. HW3_for_Programming_LLMs.pdf (assignment spec / context)
2. HW3_final_submission/unified_agent.py (multi‑agent executable)

## 1. Overview

`unified_agent.py` implements a terminal‑based unified assistant with two roles:
- PersonalAssistant (default) using hosted MCP tools (Zapier, Firecrawl).
- PizzaOrderingAgent (switches when user intent matches pizza/order keywords; generates runnable Python code to automate ordering via Playwright helper `pizza_order_browser.order_pizzas`).

## 2. Key File: unified_agent.py

Main components:
- Environment load (dotenv): expects `ZAPIER_MCP_TOKEN`, `FIRECRAWL_API_KEY`.
- Hosted MCP tools: Zapier + Firecrawl via `HostedMCPTool`.
- Pizza agent: local chat completions model (LM Studio endpoint) instructed to only emit raw Python when all pizza parameters collected.
- Conversation loop:
  - Regex intent detection: `pizza|pepperoni|order|delivery|domino|hungry`.
  - Delegates to pizza agent; if code includes `order_pizzas(` it is written to `generated_pizza_order.py` then executed.
  - Otherwise runs PersonalAssistant with MCP tool access.
- Code sanitation before execution (strip backticks, normalize quotes).
- UTF‑8 stdout wrapper.

Safety / assumptions:
- Playwright & `pizza_order_browser.py` must exist and be functional (selectors may break if site changes).
- Generated scripts run synchronously with `subprocess.run`.
- No persistent session for pizza agent (each turn independent until code emitted).

## 3. Environment Setup

```sh
python -m venv .venv
.venv\Scripts\activate
pip install -r HW3_final_submission/requirements.txt
python -m playwright install chromium
```
Configure MCP Server in Zapier and retrieve Authorization Token <br>
Register with Firecrawl and retrieve Authorization Token 

Create `.env` (do NOT commit real secrets):
```
ZAPIER_MCP_TOKEN=YOUR_TOKEN
FIRECRAWL_API_KEY=YOUR_TOKEN
OPENAI_API_KEY=DUMMY_OR_REQUIRED_FOR_OTHER TOOLS
```

(Optional) Start LM Studio model at: http://127.0.0.1:1234/v1 (api_key placeholder “lmstudio”).

## 4. Run

```sh
python HW3_final_submission/unified_agent.py
```

Sample interaction:
- Type a general query → handled by PersonalAssistant (may call Zapier / Firecrawl).
- Type “I want to order two pepperoni pizzas to 123 Main St” → switches to PizzaOrderingAgent, asks for missing fields, outputs raw Python, executes.

## 5. Extending

Minimal extension points:
- Add new intent keywords in regex.
- Swap local model by changing `OpenAIChatCompletionsModel` base_url.
- Add more MCP tools to `assistant_agent.tools`.

## 6. Troubleshooting

| Issue | Fix |
|-------|-----|
| Missing `agents` module | Ensure its package is installed/available in PYTHONPATH. |
| Playwright timeout | Re‑install browsers; verify network; update selectors. |
| Pizza agent outputs questions repeatedly | Provide all required fields (address, city, state, zip, pizzas list). |
| Unicode quote errors | Sanitizer already normalizes; check any pasted smart quotes. |
| Hosted MCP 401 | Regenerate Zapier / Firecrawl tokens; confirm `.env` loaded. |

<!-- ## 7. Security & Academic Integrity

- Remove or rotate any credentials contained in historical `.env`.
- Do not place actual orders while testing.
- PDF governs submission scope—limit modifications to required parts. -->

<!-- ## 8. File Reference (Focused)

- HW3_final_submission/unified_agent.py – executable multi‑agent loop.
- HW3_for_Programming_LLMs.pdf – assignment / specification.

All other files: out of scope for this focused README. -->

## 9. Minimal Code Execution Path (Pizza)

Generated snippet (example the agent may produce once info complete):
```python
from pizza_order_browser import order_pizzas
order_pizzas('161 Wellborn Road', 'College Station', 'TX', '77840', [('Ultimate Pepperoni', 2)])
```

The controller writes this to `generated_pizza_order.py` and runs it.

## 10. Notes

- Keep responses concise when interacting (agent instruction enforces it).
- Adjust regex if false positives occur.
- Goal was to demonstrate both MCP tool usage and pizza ordering functionality
