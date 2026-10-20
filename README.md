# vynn-mcp

mcp-name: io.github.beee003/vynn-mcp

MCP server for [Vynn](https://the-vynn.com) — self-improving AI workflows & backtesting.

## Tools

### Workflows
- `list_workflows` — List your workflows
- `get_workflow` — Get workflow details with steps
- `create_workflow` — Create a new workflow
- `run_workflow` — Execute a workflow
- `get_runs` / `get_run_summary` — View run history

### Self-Improving
- `optimize_prompt` — AI-powered prompt optimization for a step
- `apply_prompt_optimization` — Apply an optimized prompt
- `get_model_recommendation` — Get model swap recommendations
- `set_schedule` / `get_schedule` / `delete_schedule` — Cron scheduling
- `create_trigger` / `list_triggers` — Inbound webhook triggers

### Backtesting
- `backtest` — Run a backtest with natural language or structured strategies
- `batch_backtest` — Parameter sweep across strategy variations
- `optimize_portfolio` — Mean-variance portfolio optimization

### Utilities
- `list_templates` / `clone_template` — Workflow templates
- `list_available_tools` — Tools attachable to workflow steps
- `get_analytics` — Workflow performance analytics

## Setup

```bash
# Install
pip install vynn-mcp

# Or from source
pip install -e /path/to/vynn-mcp
```

Set your API key:
```bash
export VYNN_API_KEY="vynn_free_..."
```

## Usage with Claude Code

Add to your Claude Code MCP config (`~/.claude.json`):

```json
{
  "mcpServers": {
    "vynn": {
      "command": "vynn-mcp",
      "env": {
        "VYNN_API_KEY": "vynn_free_..."
      }
    }
  }
}
```

## Usage with Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "vynn": {
      "command": "vynn-mcp",
      "env": {
        "VYNN_API_KEY": "vynn_free_..."
      }
    }
  }
}
```

## Get an API Key

Sign up at [the-vynn.com](https://the-vynn.com) or:

```bash
curl -X POST https://the-vynn.com/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
```
