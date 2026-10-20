"""
Vynn MCP Server

Exposes self-improving AI workflows and backtesting as MCP tools
for use in Claude Code, Cursor, and other MCP-compatible clients.

Configuration:
  VYNN_API_KEY   — Your Vynn API key (vynn_free_... or vynn_pro_...)
  VYNN_API_URL   — API base URL (default: https://astrai-compute.fly.dev)
  VYNN_BACKTEST_URL — Backtest API URL (default: https://the-vynn.com)
"""

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Vynn",
    instructions="Self-improving AI workflows & backtesting. Use these tools to manage workflows, run backtests, optimize prompts, and set up schedules/triggers.",
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VYNN_API_URL = os.getenv("VYNN_API_URL", "https://astrai-compute.fly.dev")
VYNN_BACKTEST_URL = os.getenv("VYNN_BACKTEST_URL", "https://the-vynn.com")


def _load_config() -> dict:
    """Load ~/.vynn/config.json if it exists."""
    cfg = os.path.expanduser("~/.vynn/config.json")
    if os.path.exists(cfg):
        with open(cfg) as f:
            return json.load(f)
    return {}


def _vynn_key() -> str:
    """Get the Vynn API key (vynn_*) for backtest calls to the-vynn.com."""
    key = os.getenv("VYNN_API_KEY", "")
    if not key:
        key = _load_config().get("api_key", "")
    if not key:
        raise ValueError(
            "VYNN_API_KEY not set. Get one at https://the-vynn.com or set the env var."
        )
    return key


def _astrai_key() -> str:
    """Get the Astrai API key (sk-astrai-*) for workflow/inference calls.

    Falls back to the Vynn key if no Astrai key is configured.
    """
    key = os.getenv("ASTRAI_API_KEY", "")
    if not key:
        key = _load_config().get("astrai_api_key", "")
    if not key:
        key = _vynn_key()
    return key


def _headers() -> dict[str, str]:
    """Headers for workflow/inference calls to astrai-compute."""
    return {
        "Authorization": f"Bearer {_astrai_key()}",
        "Content-Type": "application/json",
        "User-Agent": "vynn-mcp/0.1.0",
    }


def _backtest_headers() -> dict[str, str]:
    """Headers for backtest calls to the-vynn.com."""
    return {
        "Authorization": f"Bearer {_vynn_key()}",
        "Content-Type": "application/json",
        "User-Agent": "vynn-mcp/0.1.0",
    }


async def _get(path: str, params: dict | None = None, base: str | None = None, headers: dict | None = None) -> Any:
    url = f"{base or VYNN_API_URL}{path}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.get(url, headers=headers or _headers(), params=params)
        r.raise_for_status()
        return r.json()


async def _post(path: str, body: dict | None = None, base: str | None = None, headers: dict | None = None) -> Any:
    url = f"{base or VYNN_API_URL}{path}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers or _headers(), json=body or {})
        r.raise_for_status()
        return r.json()


async def _put(path: str, body: dict) -> Any:
    url = f"{VYNN_API_URL}{path}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.put(url, headers=_headers(), json=body)
        r.raise_for_status()
        return r.json()


async def _delete(path: str) -> Any:
    url = f"{VYNN_API_URL}{path}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.delete(url, headers=_headers())
        r.raise_for_status()
        return r.json()


# ===================================================================
# WORKFLOW TOOLS
# ===================================================================


@mcp.tool()
async def list_workflows() -> str:
    """List all your Vynn workflows with their steps and status."""
    data = await _get("/v1/workflows", {"include_steps": "true"})
    workflows = data if isinstance(data, list) else data.get("workflows", data)
    if not workflows:
        return "No workflows found. Create one with create_workflow."
    lines = []
    for w in workflows:
        steps = w.get("steps", [])
        step_names = ", ".join(s.get("name", "?") for s in steps) if steps else "no steps"
        lines.append(
            f"- **{w['name']}** (id: {w['id']})\n"
            f"  {w.get('description', '')}\n"
            f"  Steps: {step_names}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_workflow(workflow_id: str) -> str:
    """Get full details of a workflow including all steps and their configuration.

    Args:
        workflow_id: UUID of the workflow
    """
    data = await _get(f"/v1/workflows/{workflow_id}", {"include_steps": "true"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def create_workflow(
    name: str,
    description: str,
    steps: list[dict] | None = None,
    email_recipients: list[str] | None = None,
    email_subject: str | None = None,
) -> str:
    """Create a new Vynn workflow.

    Args:
        name: Workflow name (e.g. "Daily Market Brief")
        description: What this workflow does
        steps: Optional list of step dicts, each with 'name' and 'description' (the system prompt).
               Example: [{"name": "Research", "description": "Find top news for {topic}"}]
        email_recipients: Optional list of email addresses to send workflow output to after each execution.
                          Example: ["maya@gmail.com", "bob@example.com"]
        email_subject: Optional custom email subject. Defaults to "Vynn: {workflow_name}".
    """
    body: dict[str, Any] = {"name": name, "description": description}
    if steps:
        body["steps"] = steps
    if email_recipients:
        body["email_recipients"] = email_recipients
    if email_subject:
        body["email_subject"] = email_subject
    data = await _post("/v1/workflows", body)
    wf_id = data.get("id", data.get("workflow_id", "unknown"))
    return f"Workflow created: **{name}** (id: {wf_id})\n\n{json.dumps(data, indent=2)}"


@mcp.tool()
async def run_workflow(workflow_id: str, input_text: str) -> str:
    """Execute a workflow with the given input and return results.

    Args:
        workflow_id: UUID of the workflow to run
        input_text: The input text/prompt to feed into the workflow
    """
    data = await _post(f"/v1/workflows/{workflow_id}/execute", {"input": input_text})
    # Format output nicely
    lines = [f"**Run ID:** {data.get('run_id', 'n/a')}"]
    steps = data.get("step_results", data.get("steps", []))
    if isinstance(steps, list):
        for s in steps:
            name = s.get("step_name", s.get("name", "Step"))
            output = s.get("output", s.get("result", ""))
            model = s.get("model_used", "")
            lines.append(f"\n### {name}" + (f" ({model})" if model else ""))
            lines.append(str(output))
    final = data.get("final_output", "")
    if final:
        lines.append(f"\n### Final Output\n{final}")
    # Check if email delivery was triggered (workflow has recipients configured)
    wf_data = await _get(f"/v1/workflows/{workflow_id}", {"include_steps": "false"})
    recipients = wf_data.get("email_recipients")
    if recipients:
        lines.append(f"\n**Email queued** to: {', '.join(recipients)}")
    return "\n".join(lines)


@mcp.tool()
async def get_runs(workflow_id: str, limit: int = 10) -> str:
    """Get recent run history for a workflow.

    Args:
        workflow_id: UUID of the workflow
        limit: Number of runs to return (default 10)
    """
    data = await _get(f"/v1/workflows/{workflow_id}/runs", {"limit": str(limit)})
    runs = data if isinstance(data, list) else data.get("runs", [])
    if not runs:
        return "No runs found for this workflow."
    lines = []
    for r in runs:
        run_id = r.get("id", r.get("run_id", "?"))
        status = r.get("status", "?")
        created = r.get("created_at", "")
        duration = r.get("duration_ms", "?")
        lines.append(f"- {run_id[:8]}... | {status} | {created} | {duration}ms")
    return "\n".join(lines)


@mcp.tool()
async def get_run_summary(run_id: str) -> str:
    """Get detailed summary of a specific workflow run.

    Args:
        run_id: UUID of the run
    """
    data = await _get(f"/v1/workflows/runs/{run_id}/summary")
    return json.dumps(data, indent=2)


# ===================================================================
# SELF-IMPROVING TOOLS
# ===================================================================


@mcp.tool()
async def optimize_prompt(workflow_id: str, step_id: str) -> str:
    """Analyze recent failures and generate optimized prompt variants for a workflow step.

    Uses LLM-powered analysis of inference logs to suggest better prompts.
    Returns up to 5 variants ranked by estimated improvement.

    Args:
        workflow_id: UUID of the workflow
        step_id: UUID of the step to optimize
    """
    data = await _post(f"/v1/workflows/{workflow_id}/steps/{step_id}/optimize-prompt")
    variants = data.get("variants", [])
    if not variants:
        return "No optimization variants generated. The step may not have enough run history yet."
    lines = ["**Prompt Optimization Variants:**\n"]
    for i, v in enumerate(variants, 1):
        lines.append(f"### Variant {i}")
        lines.append(f"**Reasoning:** {v.get('reasoning', 'n/a')}")
        lines.append(f"**Estimated improvement:** {v.get('estimated_improvement', 'n/a')}")
        lines.append(f"**Prompt:**\n```\n{v.get('prompt', '')}\n```\n")
    lines.append(
        "Use `apply_prompt_optimization` with the variant index to apply one."
    )
    return "\n".join(lines)


@mcp.tool()
async def apply_prompt_optimization(
    workflow_id: str, step_id: str, prompt: str
) -> str:
    """Apply an optimized prompt to a workflow step.

    Args:
        workflow_id: UUID of the workflow
        step_id: UUID of the step
        prompt: The new prompt text to apply
    """
    data = await _post(
        f"/v1/workflows/{workflow_id}/steps/{step_id}/apply-prompt",
        {"prompt": prompt},
    )
    return f"Prompt applied successfully.\n\n{json.dumps(data, indent=2)}"


@mcp.tool()
async def get_model_recommendation(workflow_id: str, step_id: str) -> str:
    """Get AI-powered model recommendation for a workflow step based on performance data.

    Args:
        workflow_id: UUID of the workflow
        step_id: UUID of the step
    """
    data = await _get(f"/v1/workflows/{workflow_id}/steps/{step_id}/recommendation")
    return json.dumps(data, indent=2)


@mcp.tool()
async def set_schedule(
    workflow_id: str,
    cron_expression: str,
    default_input: str,
    timezone: str = "UTC",
) -> str:
    """Schedule a workflow to run automatically on a cron schedule.

    Args:
        workflow_id: UUID of the workflow
        cron_expression: Cron expression (e.g. "0 8 * * 1-5" for weekdays at 8am)
        default_input: The input text to use for each scheduled run
        timezone: Timezone for the schedule (default: UTC)
    """
    data = await _post(
        f"/v1/workflows/{workflow_id}/schedule",
        {
            "cron_expression": cron_expression,
            "default_input": default_input,
            "timezone": timezone,
            "enabled": True,
        },
    )
    return f"Schedule set: `{cron_expression}` ({timezone})\n\n{json.dumps(data, indent=2)}"


@mcp.tool()
async def get_schedule(workflow_id: str) -> str:
    """Get the current schedule for a workflow.

    Args:
        workflow_id: UUID of the workflow
    """
    try:
        data = await _get(f"/v1/workflows/{workflow_id}/schedule")
        return json.dumps(data, indent=2)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return "No schedule set for this workflow."
        raise


@mcp.tool()
async def delete_schedule(workflow_id: str) -> str:
    """Remove the schedule from a workflow.

    Args:
        workflow_id: UUID of the workflow
    """
    await _delete(f"/v1/workflows/{workflow_id}/schedule")
    return "Schedule deleted."


@mcp.tool()
async def create_trigger(workflow_id: str, name: str = "default") -> str:
    """Create an inbound webhook trigger for a workflow.

    Returns a URL and secret that external services can POST to in order to fire the workflow.

    Args:
        workflow_id: UUID of the workflow
        name: Human-readable name for the trigger
    """
    data = await _post(
        f"/v1/workflows/{workflow_id}/triggers",
        {"name": name},
    )
    trigger_url = data.get("trigger_url", "")
    secret = data.get("secret", "")
    lines = [
        "**Webhook Trigger Created**",
        f"- **URL:** `{trigger_url}`",
        f"- **Secret:** `{secret}` (save this — shown only once)",
        f"- **Name:** {name}",
        "",
        "Fire it with:",
        f'```bash\ncurl -X POST "{trigger_url}" \\\n  -H "Content-Type: application/json" \\\n  -d \'{{"secret": "{secret}", "input": "your input here"}}\'\n```',
    ]
    return "\n".join(lines)


@mcp.tool()
async def list_triggers(workflow_id: str) -> str:
    """List all webhook triggers for a workflow.

    Args:
        workflow_id: UUID of the workflow
    """
    data = await _get(f"/v1/workflows/{workflow_id}/triggers")
    triggers = data if isinstance(data, list) else data.get("triggers", [])
    if not triggers:
        return "No triggers. Create one with create_trigger."
    lines = []
    for t in triggers:
        lines.append(
            f"- **{t.get('name', 'default')}** (id: {t['id']})\n"
            f"  Invocations: {t.get('total_invocations', 0)} | "
            f"Enabled: {t.get('enabled', True)}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_analytics(workflow_id: str) -> str:
    """Get performance analytics for a workflow — success rates, latency, cost, model usage.

    Args:
        workflow_id: UUID of the workflow
    """
    data = await _get(f"/v1/workflows/{workflow_id}/analytics")
    return json.dumps(data, indent=2)


# ===================================================================
# BACKTESTING TOOLS
# ===================================================================


@mcp.tool()
async def backtest(
    strategy: str,
    universe: list[str] | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    capital: float = 100000,
    benchmark: str = "SPY",
    walk_forward: bool = False,
    position_sizing: str = "equal",
    allow_short: bool = False,
) -> str:
    """Run a backtest on a trading strategy using natural language or structured rules.

    Args:
        strategy: Strategy description (e.g. "Buy when RSI(14) < 30, sell when RSI(14) > 70")
                  or JSON structured format {"entries":[...],"exits":[...]}
        universe: List of tickers (e.g. ["AAPL", "MSFT"]) or preset ("SP500", "MAGNIFICENT7").
                  Defaults to MAGNIFICENT7.
        period_start: Start date YYYY-MM-DD (default: 3 years ago)
        period_end: End date YYYY-MM-DD (default: today)
        capital: Starting capital (default: 100000)
        benchmark: Benchmark ticker (default: SPY)
        walk_forward: Enable walk-forward validation to detect overfitting
        position_sizing: "equal", "risk_parity", "vol_target", or "kelly"
        allow_short: Allow short selling
    """
    body: dict[str, Any] = {
        "strategy": strategy,
        "capital": capital,
        "benchmark": benchmark,
        "walk_forward": walk_forward,
        "position_sizing": position_sizing,
        "allow_short": allow_short,
    }
    if universe:
        body["universe"] = universe
    if period_start:
        body["period_start"] = period_start
    if period_end:
        body["period_end"] = period_end

    data = await _post("/v1/backtest", body, base=VYNN_BACKTEST_URL, headers=_backtest_headers())

    # Format key metrics
    metrics = data.get("metrics", {})
    bm = data.get("benchmark", {})
    lines = [
        f"**Backtest ID:** {data.get('backtest_id', 'n/a')}",
        f"**Strategy:** {data.get('strategy_parsed', strategy)}",
        "",
        "### Performance",
        f"- Total Return: {metrics.get('total_return_pct', '?')}%",
        f"- Annualized Return: {metrics.get('annualized_return_pct', '?')}%",
        f"- Sharpe Ratio: {metrics.get('sharpe_ratio', '?')}",
        f"- Sortino Ratio: {metrics.get('sortino_ratio', '?')}",
        f"- Max Drawdown: {metrics.get('max_drawdown_pct', '?')}%",
        f"- Volatility: {metrics.get('volatility_pct', '?')}%",
        f"- Win Rate: {metrics.get('win_rate', '?')}",
        f"- Total Trades: {metrics.get('total_trades', '?')}",
        f"- Profit Factor: {metrics.get('profit_factor', '?')}",
    ]
    if bm:
        lines.extend([
            "",
            "### vs Benchmark",
            f"- Alpha: {bm.get('alpha', '?')}",
            f"- Beta: {bm.get('beta', '?')}",
            f"- Information Ratio: {bm.get('information_ratio', '?')}",
        ])
    return "\n".join(lines)


@mcp.tool()
async def batch_backtest(
    base_strategy: str,
    parameter_grid: dict[str, list],
    universe: list[str] | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    capital: float = 100000,
    rank_by: str = "sharpe_ratio",
) -> str:
    """Run a parameter sweep across strategy variations and rank them.

    Args:
        base_strategy: Strategy template with {placeholders} (e.g. "Buy when RSI({period}) < {threshold}")
        parameter_grid: Dict of param name to list of values (e.g. {"period": [14, 21], "threshold": [25, 30, 35]})
        universe: List of tickers or preset
        period_start: Start date YYYY-MM-DD
        period_end: End date YYYY-MM-DD
        capital: Starting capital
        rank_by: Metric to rank by — "sharpe_ratio", "total_return_pct", or "max_drawdown_pct"
    """
    body: dict[str, Any] = {
        "base_strategy": base_strategy,
        "parameter_grid": parameter_grid,
        "capital": capital,
        "rank_by": rank_by,
    }
    if universe:
        body["universe"] = universe
    if period_start:
        body["period_start"] = period_start
    if period_end:
        body["period_end"] = period_end

    data = await _post("/v1/backtest/batch", body, base=VYNN_BACKTEST_URL, headers=_backtest_headers())

    results = data.get("results", [])
    lines = [
        f"**Batch ID:** {data.get('batch_id', 'n/a')}",
        f"**Variants tested:** {data.get('total_variants', len(results))}",
        f"**Ranked by:** {rank_by}",
        "",
    ]
    for i, r in enumerate(results[:10], 1):
        params = r.get("params", {})
        m = r.get("metrics", {})
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        lines.append(
            f"{i}. [{param_str}] — "
            f"Sharpe: {m.get('sharpe_ratio', '?')}, "
            f"Return: {m.get('total_return_pct', '?')}%, "
            f"DD: {m.get('max_drawdown_pct', '?')}%"
        )
    return "\n".join(lines)


@mcp.tool()
async def optimize_portfolio(
    universe: list[str],
    method: str = "max_sharpe",
    period_start: str | None = None,
    period_end: str | None = None,
    long_only: bool = True,
) -> str:
    """Optimize portfolio weights using mean-variance optimization.

    Args:
        universe: List of tickers (e.g. ["AAPL", "MSFT", "GOOGL", "TSLA"])
        method: "max_sharpe", "min_variance", "risk_budget", or "black_litterman"
        period_start: Start date YYYY-MM-DD
        period_end: End date YYYY-MM-DD
        long_only: Only allow long positions (default: true)
    """
    body: dict[str, Any] = {
        "universe": universe,
        "method": method,
        "long_only": long_only,
    }
    if period_start:
        body["period_start"] = period_start
    if period_end:
        body["period_end"] = period_end

    data = await _post("/v1/optimize", body, base=VYNN_BACKTEST_URL, headers=_backtest_headers())

    weights = data.get("optimal_weights", {})
    lines = [
        f"**Method:** {method}",
        f"**Expected Return:** {data.get('expected_return_pct', '?')}%",
        f"**Expected Volatility:** {data.get('expected_volatility_pct', '?')}%",
        f"**Expected Sharpe:** {data.get('expected_sharpe', '?')}",
        "",
        "### Optimal Weights",
    ]
    for ticker, weight in sorted(weights.items(), key=lambda x: -x[1]):
        pct = weight * 100
        lines.append(f"- {ticker}: {pct:.1f}%")
    return "\n".join(lines)


# ===================================================================
# UTILITY TOOLS
# ===================================================================


@mcp.tool()
async def list_templates() -> str:
    """List available workflow templates that you can clone."""
    data = await _get("/v1/workflows/templates/list")
    templates = data if isinstance(data, list) else data.get("templates", [])
    if not templates:
        return "No templates available."
    lines = []
    for t in templates:
        lines.append(
            f"- **{t.get('name', '?')}** (id: {t['id']})\n"
            f"  {t.get('description', '')}"
        )
    return "\n".join(lines)


@mcp.tool()
async def clone_template(template_id: str, name: str) -> str:
    """Clone a workflow template into your account.

    Args:
        template_id: UUID of the template
        name: Name for your new workflow
    """
    data = await _post(f"/v1/workflows/templates/{template_id}/clone", {"name": name})
    return f"Template cloned as **{name}**.\n\n{json.dumps(data, indent=2)}"


@mcp.tool()
async def list_available_tools() -> str:
    """List all tools that can be attached to workflow steps (web search, code exec, etc)."""
    data = await _get("/v1/workflows/tools/available")
    tools = data if isinstance(data, list) else data.get("tools", [])
    if not tools:
        return "No tools available."
    lines = []
    for t in tools:
        lines.append(f"- **{t.get('name', '?')}**: {t.get('description', '')}")
    return "\n".join(lines)


def main():
    """CLI entry point."""
    mcp.run()
