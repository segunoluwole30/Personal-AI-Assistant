# Personal AI Assistant — Multi-Agent MCP + Browser Automation

A terminal-based personal assistant that routes each request to the right agent. General tasks go to a
cloud agent with **Model Context Protocol (MCP)** tools for 7,000+ app integrations and web scraping.
Food orders go to a **locally hosted LLM** that writes and runs a browser-automation script to place a
real pizza order.

## Highlights

- **Multi-agent routing:** a lightweight intent router hands each turn to either the cloud assistant or
  the local ordering agent.
- **Hosted MCP tools:** the assistant connects to the [Zapier MCP](https://zapier.com/mcp) server (email,
  calendar, Slack, Sheets…) and the [Firecrawl MCP](https://firecrawl.dev) server (web search and
  scraping) through the OpenAI Agents SDK's `HostedMCPTool`.
- **Local, private LLM:** the ordering agent runs `gpt-oss-20b` (pruned to 10.2B parameters) on
  [LM Studio](https://lmstudio.ai) through an OpenAI-compatible endpoint, so order details stay on the
  machine.
- **Code generation → execution:** the ordering agent asks follow-up questions until it has every
  required field, then emits a Python script that calls a Playwright helper. The controller sanitizes the
  code, writes it to disk and runs it.
- **Real browser automation:** `pizza_order_browser.py` drives Chromium through the Domino's ordering
  flow with Playwright.

## Architecture

```
                         ┌──────────────────────────┐
  user input ──► intent ─┤ pizza|order|delivery|... ├──► PizzaOrderingAgent (local gpt-oss on LM Studio)
                 router  └────────────┬─────────────┘            │ asks for missing details
                                      │ otherwise                │ emits Python once complete
                                      ▼                          ▼
                           PersonalAssistant (cloud)     sanitize ► write ► subprocess.run
                           ├─ Zapier MCP                          │
                           └─ Firecrawl MCP                       ▼
                                                     pizza_order_browser.order_pizzas() (Playwright)
```

## Example session (illustrative)

```text
> Summarize the top 3 Hacker News stories and email them to me
[PersonalAssistant → Firecrawl scrape → Zapier Gmail send]

> I'm hungry, order two pepperoni pizzas
[PizzaOrderingAgent] What's the delivery address, city, state and ZIP?
> 161 Wellborn Road, College Station, TX 77840
[PizzaOrderingAgent] generated code:
    from pizza_order_browser import order_pizzas
    order_pizzas('161 Wellborn Road', 'College Station', 'TX', '77840', [('Ultimate Pepperoni', 2)])
[executing generated_pizza_order.py …]
```

## Getting started

### Prerequisites

- Python 3.10+
- [LM Studio](https://lmstudio.ai) serving a model at `http://127.0.0.1:1234/v1` (the ordering agent only)
- A Zapier MCP server token and a Firecrawl API key
- An OpenAI API key (for the cloud assistant)

### Install

```bash
git clone https://github.com/segunoluwole30/Personal-AI-Assistant.git
cd Personal-AI-Assistant
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt openai-agents
python -m playwright install chromium
```

### Configure

Create a `.env` file (never commit it):

```env
OPENAI_API_KEY=<your-key>
ZAPIER_MCP_TOKEN=<your-zapier-mcp-token>
FIRECRAWL_API_KEY=<your-firecrawl-key>
```

### Run

```bash
python unified_agent.py
```

## Project structure

| File                     | Description                                                       |
| ------------------------ | ----------------------------------------------------------------- |
| `unified_agent.py`       | Agent definitions, MCP tool setup, intent router and execution loop |
| `pizza_order_browser.py` | Playwright automation for the Domino's ordering flow              |
| `requirements.txt`       | Python dependencies                                                |

## Notes and limitations

- Generated code runs locally via `subprocess`. This is fine for a personal tool, but a production
  version should sandbox it.
- The browser automation depends on the Domino's site layout, so selectors may need updating if the site
  changes.
- Intent routing is keyword-based. An LLM-based classifier would handle ambiguous requests better.

## Tech stack

Python · OpenAI Agents SDK · Model Context Protocol (Zapier, Firecrawl) · LM Studio · gpt-oss · Playwright

---

Built for CSCE 689 (Programming Large Language Models) at Texas A&M University.
