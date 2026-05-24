"""Ex5 tools. Four tools the agent uses to research an Edinburgh booking.

Each tool:
  1. Reads its fixture from sample_data/ (DO NOT modify the fixtures).
  2. Logs its arguments and output into _TOOL_CALL_LOG (see integrity.py).
  3. Returns a ToolResult with success=True/False, output=dict, summary=str.

The grader checks for:
  * Correct parallel_safe flags (reads True, generate_flyer False).
  * Every tool's results appear in _TOOL_CALL_LOG.
  * Tools fail gracefully on missing fixtures or bad inputs (ToolError,
    not RuntimeError).
"""

from __future__ import annotations

import json
from pathlib import Path

from sovereign_agent.errors import ToolError
from sovereign_agent.session.directory import Session
from sovereign_agent.tools.registry import ToolRegistry, ToolResult, _RegisteredTool

from starter.edinburgh_research.integrity import _TOOL_CALL_LOG, record_tool_call

_SAMPLE_DATA = Path(__file__).parent / "sample_data"


# ---------------------------------------------------------------------------
# TODO 1 — venue_search
# ---------------------------------------------------------------------------
def venue_search(near: str, party_size: int, budget_max_gbp: int = 1000) -> ToolResult:
    """Search for Edinburgh venues near <near> that can seat the party.

    Reads sample_data/venues.json. Filters by:
      * open_now == True
      * area contains <near> (case-insensitive substring match)
      * seats_available_evening >= party_size
      * hire_fee_gbp + min_spend_gbp <= budget_max_gbp

    Returns a ToolResult with:
      output: {"near": ..., "party_size": ..., "results": [<venue dicts>], "count": int}
      summary: "venue_search(<near>, party=<N>): <count> result(s)"

    MUST call record_tool_call(...) before returning so the integrity
    check can see what data was produced.
    """
    arguments = {"near": near, "party_size": party_size, "budget_max_gbp": budget_max_gbp}

    # Spiral guard — defense-in-depth against LLMs that keep re-searching
    # instead of using the results they already have. See
    # docs/real-mode-failures.md §"Ex5 — Qwen3-32B spiral".
    prior_searches = sum(1 for r in _TOOL_CALL_LOG if r.tool_name == "venue_search")
    if prior_searches >= 3:
        output = {"error": "too_many_searches", "count": prior_searches}
        summary = (
            f"STOP calling venue_search ({prior_searches} prior calls); "
            "use the results you already have."
        )
        record_tool_call("venue_search", arguments, output)
        return ToolResult(success=False, output=output, summary=summary)

    # Load fixture. Missing file is a dependency error, not a runtime crash.
    venues_path = _SAMPLE_DATA / "venues.json"
    if not venues_path.exists():
        raise ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"venues fixture not found: {venues_path}",
            context={"path": str(venues_path)},
        )

    try:
        venues = json.loads(venues_path.read_text())
    except json.JSONDecodeError as exc:
        raise ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"venues fixture is not valid JSON: {exc}",
            context={"path": str(venues_path)},
            cause=exc,
        ) from exc

    needle = (near or "").strip().lower()
    results = [
        v
        for v in venues
        if v.get("open_now") is True
        and needle in v.get("area", "").lower()
        and v.get("seats_available_evening", 0) >= party_size
        and v.get("hire_fee_gbp", 0) + v.get("min_spend_gbp", 0) <= budget_max_gbp
    ]

    output = {
        "near": near,
        "party_size": party_size,
        "results": results,
        "count": len(results),
    }
    summary = f"venue_search({near}, party={party_size}): {len(results)} result(s)"
    record_tool_call("venue_search", arguments, output)
    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 2 — get_weather
# ---------------------------------------------------------------------------
def get_weather(city: str, date: str) -> ToolResult:
    """Look up the scripted weather for <city> on <date> (YYYY-MM-DD).

    Reads sample_data/weather.json. Returns:
      output: {"city": str, "date": str, "condition": str, "temperature_c": int, ...}
      summary: "get_weather(<city>, <date>): <condition>, <temp>C"

    If the city or date is not in the fixture, return success=False with
    a clear ToolError (SA_TOOL_INVALID_INPUT). Do NOT raise.

    MUST call record_tool_call(...) before returning.
    """
    arguments = {"city": city, "date": date}

    weather_path = _SAMPLE_DATA / "weather.json"
    if not weather_path.exists():
        raise ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"weather fixture not found: {weather_path}",
            context={"path": str(weather_path)},
        )

    try:
        weather = json.loads(weather_path.read_text())
    except json.JSONDecodeError as exc:
        raise ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"weather fixture is not valid JSON: {exc}",
            context={"path": str(weather_path)},
            cause=exc,
        ) from exc

    city_key = (city or "").strip().lower()
    city_data = weather.get(city_key)
    if city_data is None:
        output = {"error": "city_not_found", "city": city, "date": date}
        summary = f"get_weather({city}, {date}): city not in fixture"
        record_tool_call("get_weather", arguments, output)
        return ToolResult(
            success=False,
            output=output,
            summary=summary,
            error=ToolError(
                code="SA_TOOL_INVALID_INPUT",
                message=f"unknown city: {city!r}",
                context={"city": city, "available": sorted(weather.keys())},
            ),
        )

    day = city_data.get(date)
    if day is None:
        output = {"error": "date_not_found", "city": city, "date": date}
        summary = f"get_weather({city}, {date}): date not in fixture"
        record_tool_call("get_weather", arguments, output)
        return ToolResult(
            success=False,
            output=output,
            summary=summary,
            error=ToolError(
                code="SA_TOOL_INVALID_INPUT",
                message=f"no weather for {city!r} on {date!r}",
                context={"city": city, "date": date, "available": sorted(city_data.keys())},
            ),
        )

    output = {"city": city, "date": date, **day}
    summary = f"get_weather({city}, {date}): {day['condition']}, {day['temperature_c']}C"
    record_tool_call("get_weather", arguments, output)
    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 3 — calculate_cost
# ---------------------------------------------------------------------------
def calculate_cost(
    venue_id: str,
    party_size: int,
    duration_hours: int,
    catering_tier: str = "bar_snacks",
) -> ToolResult:
    """Compute the total cost for a booking.

    Formula:
      base_per_head = base_rates_gbp_per_head[catering_tier]
      venue_mult    = venue_modifiers[venue_id]
      subtotal      = base_per_head * venue_mult * party_size * max(1, duration_hours)
      service       = subtotal * service_charge_percent / 100
      total         = subtotal + service + <venue's hire_fee_gbp + min_spend_gbp>
      deposit_rule  = per deposit_policy thresholds

    Returns:
      output: {
        "venue_id": str,
        "party_size": int,
        "duration_hours": int,
        "catering_tier": str,
        "subtotal_gbp": int,
        "service_gbp": int,
        "total_gbp": int,
        "deposit_required_gbp": int,
      }
      summary: "calculate_cost(<venue>, <party>): total £<N>, deposit £<M>"

    MUST call record_tool_call(...) before returning.
    """
    arguments = {
        "venue_id": venue_id,
        "party_size": party_size,
        "duration_hours": duration_hours,
        "catering_tier": catering_tier,
    }

    catering_path = _SAMPLE_DATA / "catering.json"
    venues_path = _SAMPLE_DATA / "venues.json"
    for p in (catering_path, venues_path):
        if not p.exists():
            raise ToolError(
                code="SA_TOOL_DEPENDENCY_MISSING",
                message=f"fixture not found: {p}",
                context={"path": str(p)},
            )

    try:
        catering = json.loads(catering_path.read_text())
        venues = json.loads(venues_path.read_text())
    except json.JSONDecodeError as exc:
        raise ToolError(
            code="SA_TOOL_DEPENDENCY_MISSING",
            message=f"fixture is not valid JSON: {exc}",
            context={"catering": str(catering_path), "venues": str(venues_path)},
            cause=exc,
        ) from exc

    base_rates = catering["base_rates_gbp_per_head"]
    venue_modifiers = catering["venue_modifiers"]
    service_charge_pct = catering["service_charge_percent"]

    if catering_tier not in base_rates:
        output = {"error": "unknown_catering_tier", "catering_tier": catering_tier}
        summary = f"calculate_cost: unknown catering_tier {catering_tier!r}"
        record_tool_call("calculate_cost", arguments, output)
        return ToolResult(
            success=False,
            output=output,
            summary=summary,
            error=ToolError(
                code="SA_TOOL_INVALID_INPUT",
                message=f"unknown catering_tier: {catering_tier!r}",
                context={"available": sorted(base_rates.keys())},
            ),
        )

    if venue_id not in venue_modifiers:
        output = {"error": "unknown_venue", "venue_id": venue_id}
        summary = f"calculate_cost: unknown venue_id {venue_id!r}"
        record_tool_call("calculate_cost", arguments, output)
        return ToolResult(
            success=False,
            output=output,
            summary=summary,
            error=ToolError(
                code="SA_TOOL_INVALID_INPUT",
                message=f"unknown venue_id: {venue_id!r}",
                context={"available": sorted(venue_modifiers.keys())},
            ),
        )

    venue = next((v for v in venues if v.get("id") == venue_id), None)
    if venue is None:
        output = {"error": "venue_not_in_venues_fixture", "venue_id": venue_id}
        summary = f"calculate_cost: venue {venue_id!r} missing from venues.json"
        record_tool_call("calculate_cost", arguments, output)
        return ToolResult(
            success=False,
            output=output,
            summary=summary,
            error=ToolError(
                code="SA_TOOL_INVALID_INPUT",
                message=f"venue_id {venue_id!r} not in venues fixture",
                context={"venue_id": venue_id},
            ),
        )

    base_per_head = base_rates[catering_tier]
    venue_mult = venue_modifiers[venue_id]
    effective_hours = max(1, duration_hours)
    subtotal = base_per_head * venue_mult * party_size * effective_hours
    service = subtotal * service_charge_pct / 100
    total = subtotal + service + venue.get("hire_fee_gbp", 0) + venue.get("min_spend_gbp", 0)

    if total < 300:
        deposit = 0
    elif total <= 1000:
        deposit = total * 0.20
    else:
        deposit = total * 0.30

    output = {
        "venue_id": venue_id,
        "party_size": party_size,
        "duration_hours": duration_hours,
        "catering_tier": catering_tier,
        "subtotal_gbp": int(round(subtotal)),
        "service_gbp": int(round(service)),
        "total_gbp": int(round(total)),
        "deposit_required_gbp": int(round(deposit)),
    }
    summary = (
        f"calculate_cost({venue_id}, party={party_size}): "
        f"total £{output['total_gbp']}, deposit £{output['deposit_required_gbp']}"
    )
    record_tool_call("calculate_cost", arguments, output)
    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# TODO 4 — generate_flyer
# ---------------------------------------------------------------------------
def generate_flyer(session: Session, event_details: dict) -> ToolResult:
    """Produce an HTML flyer and write it to workspace/flyer.html.

    event_details is expected to contain at least:
      venue_name, venue_address, date, time, party_size, condition,
      temperature_c, total_gbp, deposit_required_gbp

    Write a self-contained HTML flyer (inline CSS, no external assets). Tag every key fact with data-testid="<n>" so the integrity check can parse it.

    Write a formatted HTML flyer with an H1 title, the event
    facts, a weather summary, and the cost breakdown.

    Returns:
      output: {"path": "workspace/flyer.html", "bytes_written": int}
      summary: "generate_flyer: wrote <path> (<N> chars)"

    MUST call record_tool_call(...) before returning — the integrity
    check compares the flyer's contents against earlier tool outputs.

    IMPORTANT: this tool MUST be registered with parallel_safe=False
    because it writes a file.
    """
    arguments = {"event_details": dict(event_details)}

    def field_str(key: str, default: str = "") -> str:
        val = event_details.get(key, default)
        return "" if val is None else str(val)

    venue_name = field_str("venue_name")
    venue_address = field_str("venue_address")
    date = field_str("date")
    time = field_str("time")
    party_size = field_str("party_size")
    condition = field_str("condition")
    temperature_c = field_str("temperature_c")
    total_gbp = field_str("total_gbp")
    deposit_gbp = field_str("deposit_required_gbp")

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Event Flyer — {venue_name}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 2em auto; padding: 1em; color: #222; }}
  h1 {{ font-size: 1.8em; margin-bottom: 0.2em; }}
  dl {{ display: grid; grid-template-columns: max-content 1fr; gap: 0.4em 1em; }}
  dt {{ font-weight: 600; color: #555; }}
  section {{ margin-top: 1.5em; padding-top: 1em; border-top: 1px solid #ddd; }}
</style>
</head>
<body>
  <h1 data-testid="venue_name">{venue_name}</h1>
  <p data-testid="venue_address">{venue_address}</p>

  <section>
    <h2>Event</h2>
    <dl>
      <dt>Date</dt><dd data-testid="date">{date}</dd>
      <dt>Time</dt><dd data-testid="time">{time}</dd>
      <dt>Party size</dt><dd data-testid="party_size">{party_size}</dd>
    </dl>
  </section>

  <section>
    <h2>Weather</h2>
    <dl>
      <dt>Condition</dt><dd data-testid="condition">{condition}</dd>
      <dt>Temperature</dt><dd data-testid="temperature_c">{temperature_c}C</dd>
    </dl>
  </section>

  <section>
    <h2>Cost</h2>
    <dl>
      <dt>Total</dt><dd data-testid="total">£{total_gbp}</dd>
      <dt>Deposit required</dt><dd data-testid="deposit">£{deposit_gbp}</dd>
    </dl>
  </section>
</body>
</html>
"""

    flyer_path = session.path("workspace/flyer.html")
    flyer_path.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = flyer_path.write_text(html, encoding="utf-8")

    rel_path = "workspace/flyer.html"
    output = {"path": rel_path, "bytes_written": bytes_written}
    summary = f"generate_flyer: wrote {rel_path} ({len(html)} chars)"
    record_tool_call("generate_flyer", arguments, output)
    return ToolResult(success=True, output=output, summary=summary)


# ---------------------------------------------------------------------------
# Registry builder — DO NOT MODIFY the name, signature, or registration calls.
# The grader imports and calls this to pick up your tools.
# ---------------------------------------------------------------------------
def build_tool_registry(session: Session) -> ToolRegistry:
    """Build a session-scoped tool registry with all four Ex5 tools plus
    the sovereign-agent builtins (read_file, write_file, list_files,
    handoff_to_structured, complete_task).

    DO NOT change the tool names — the tests and grader call them by name.
    """
    from sovereign_agent.tools.builtin import make_builtin_registry

    reg = make_builtin_registry(session)

    # venue_search
    reg.register(
        _RegisteredTool(
            name="venue_search",
            description="Search Edinburgh venues by area, party size, and max budget.",
            fn=venue_search,
            parameters_schema={
                "type": "object",
                "properties": {
                    "near": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "budget_max_gbp": {"type": "integer", "default": 1000},
                },
                "required": ["near", "party_size"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # read-only
            examples=[
                {
                    "input": {"near": "Haymarket", "party_size": 6, "budget_max_gbp": 800},
                    "output": {"count": 1, "results": [{"id": "haymarket_tap"}]},
                }
            ],
        )
    )

    # get_weather
    reg.register(
        _RegisteredTool(
            name="get_weather",
            description="Get scripted weather for a city on a YYYY-MM-DD date.",
            fn=get_weather,
            parameters_schema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["city", "date"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # read-only
            examples=[
                {
                    "input": {"city": "Edinburgh", "date": "2026-04-25"},
                    "output": {"condition": "cloudy", "temperature_c": 12},
                }
            ],
        )
    )

    # calculate_cost
    reg.register(
        _RegisteredTool(
            name="calculate_cost",
            description="Compute total cost and deposit for a booking.",
            fn=calculate_cost,
            parameters_schema={
                "type": "object",
                "properties": {
                    "venue_id": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "duration_hours": {"type": "integer"},
                    "catering_tier": {
                        "type": "string",
                        "enum": ["drinks_only", "bar_snacks", "sit_down_meal", "three_course_meal"],
                        "default": "bar_snacks",
                    },
                },
                "required": ["venue_id", "party_size", "duration_hours"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=True,  # pure compute, no shared state
            examples=[
                {
                    "input": {
                        "venue_id": "haymarket_tap",
                        "party_size": 6,
                        "duration_hours": 3,
                    },
                    "output": {"total_gbp": 540, "deposit_required_gbp": 0},
                }
            ],
        )
    )

    # generate_flyer — parallel_safe=False because it writes a file
    def _flyer_adapter(event_details: dict) -> ToolResult:
        return generate_flyer(session, event_details)

    reg.register(
        _RegisteredTool(
            name="generate_flyer",
            description="Write an HTML flyer for the event to workspace/flyer.html.",
            fn=_flyer_adapter,
            parameters_schema={
                "type": "object",
                "properties": {"event_details": {"type": "object"}},
                "required": ["event_details"],
            },
            returns_schema={"type": "object"},
            is_async=False,
            parallel_safe=False,  # writes a file — MUST be False
            examples=[
                {
                    "input": {
                        "event_details": {
                            "venue_name": "Haymarket Tap",
                            "date": "2026-04-25",
                            "party_size": 6,
                        }
                    },
                    "output": {"path": "workspace/flyer.html"},
                }
            ],
        )
    )

    return reg


__all__ = [
    "build_tool_registry",
    "venue_search",
    "get_weather",
    "calculate_cost",
    "generate_flyer",
]
