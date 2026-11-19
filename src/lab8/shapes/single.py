"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.trace import Trace


class _Trace:
    """Local alias so a crash can still flush. Wraps lab8.trace.Trace."""

    def __init__(self, run_id: str) -> None:
        self._inner = Trace(run_id)

    def add(self, kind: str, payload: dict) -> None:
        self._inner.add(kind, payload)

    def write(self) -> str:
        return self._inner.write()

    @property
    def run_id(self) -> str:
        return self._inner.run_id


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    run_id = make_run_id("single", claim_id, seed)
    trace = _Trace(run_id)

    # State carried across react steps
    context: dict[str, Any] = {
        "claim_id": claim_id,
        "principal_id": None,
        "order_id": None,
    }

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        # Count a model call on each decision step
        step_name = seen.get("last_tool") or "init"
        complete(budget, seed=seed, purpose="decide", prompt=f"step:{step_name}:{claim_id}")

        if "last_tool" not in seen:
            trace.add("thought", {"action": "fetch_claim", "claim_id": claim_id})
            return {"tool": "get_claim_view", "args": {"claim_id": claim_id}}

        last_tool = seen["last_tool"]
        last_result = seen.get("last_result") or {}

        if last_tool == "get_claim_view":
            if not last_result.get("found"):
                trace.add("error", {"reason": "unknown_claim"})
                return {"final": {"status": "failed", "error_reason": "unknown_claim"}}

            context["principal_id"] = last_result.get("principal_id")
            context["order_id"] = last_result.get("order_id")
            trace.add("claim_view", {"claim_id": claim_id, "found": True, "has_order": bool(context["order_id"])})

            if not context["order_id"]:
                trace.add("decision", {"status": "needs_info"})
                return {"final": {"status": "needs_info", "error_reason": "missing_order_id"}}

            trace.add("thought", {"action": "lookup_order", "order_id": context["order_id"]})
            return {
                "tool": "lookup_order",
                "args": {"order_id": context["order_id"], "principal_id": context["principal_id"]},
            }

        if last_tool == "lookup_order":
            trace.add("lookup_order", {"visible": last_result.get("visible"), "reason": last_result.get("reason")})
            if not last_result.get("visible"):
                return {"final": {"status": "escalated", "error_reason": last_result.get("reason")}}

            order = last_result["order"]
            trace.add("thought", {"action": "compute_compensation"})
            return {"tool": "compute_compensation", "args": {"order": order}}

        if last_tool == "compute_compensation":
            trace.add("quote", last_result)
            return {"final": {"status": "ready", "quote": last_result}}

        return {"final": {"status": "failed", "error_reason": f"unexpected_tool_{last_tool}"}}

    react_result = run_react(
        conn,
        budget,
        observation={"claim": {"claim_id": claim_id}},
        decide=decide,
        max_steps=8,
        worker=False,
    )

    if react_result.get("stopped") == "step_cap":
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="step_cap",
        )

    final = react_result.get("final") or {}
    status = final.get("status")

    if status == "failed":
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=final.get("error_reason"),
        )

    if status == "needs_info":
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=final.get("error_reason"),
        )

    if status == "escalated":
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=final.get("error_reason"),
        )

    if status == "ready":
        quote_payload = final["quote"]
        proposal = int(quote_payload["amount_vnd"])

        if proposal <= 0:
            return finish(
                conn,
                shape="single",
                claim_id=claim_id,
                seed=seed,
                status="denied",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason=quote_payload.get("reason"),
            )

        try:
            outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
        except InjectedCrash:
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise

        if not outcome["ok"]:
            end_status = "failed" if outcome.get("conflict") else "denied"
            return finish(
                conn,
                shape="single",
                claim_id=claim_id,
                seed=seed,
                status=end_status,
                proposal_amount=proposal,
                budget=budget,
                trace=trace,
                error_reason=outcome.get("reason"),
            )

        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="resolved",
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=None,
        )

    return finish(
        conn,
        shape="single",
        claim_id=claim_id,
        seed=seed,
        status="failed",
        proposal_amount=0,
        budget=budget,
        trace=trace,
        error_reason="invalid_state",
    )
