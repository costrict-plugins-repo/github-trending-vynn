# Submit MCP Server: vynn-mcp

## Server Name
vynn-mcp

## Description
Self-improving AI workflows with backtesting, prompt optimization, and scheduling. 21 tools across 4 categories: workflows, self-improving, backtesting, and utilities.

## Repository
https://github.com/beee003/vynn-mcp

## Installation
```bash
pip install vynn-mcp
```

## Configuration
```json
{
  "mcpServers": {
    "vynn": {
      "command": "vynn-mcp",
      "env": {
        "VYNN_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Tools (21 total)

**Workflows (6):** list_workflows, get_workflow, create_workflow, run_workflow, get_runs, get_run_summary

**Self-Improving (9):** optimize_prompt, apply_prompt_optimization, get_model_recommendation, set_schedule, get_schedule, delete_schedule, create_trigger, list_triggers, get_analytics

**Backtesting (3):** backtest (natural language + structured JSON strategies), batch_backtest (parameter sweep), optimize_portfolio (mean-variance optimization)

**Utilities (3):** list_templates, clone_template, list_available_tools

## Key Features
- Natural language backtesting: "Buy when RSI(14) < 30, sell when RSI(14) > 70"
- AI-powered prompt optimization with up to 5 variants ranked by improvement
- Cron scheduling and webhook triggers for automated workflow execution
- Portfolio optimization (max Sharpe, min variance, risk budget, Black-Litterman)
- Works with Claude Code, Cursor, and any MCP-compatible client

## Transport
stdio (via PyPI package)

## Registry
Registered in official MCP Registry as `io.github.beee003/vynn-mcp`

## Links
- Website: https://the-vynn.com
- PyPI: https://pypi.org/project/vynn-mcp/
- Docs: https://the-vynn.com/docs
