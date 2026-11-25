"""Phase 4.9 Member 2 Unit Tests — Adaptive Planning, Evaluation & SQLAlchemy Persistence."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.app.agents.autonomy.contracts import (
    AutonomousStepRecord,
    AutonomousWorkflowRequest,
    AutonomyPolicy,
    AutonomySecurityContext,
    EvaluationResult,
)
from backend.app.agents.autonomy.controller import AutonomousWorkflowController
from backend.app.agents.autonomy.evaluator import ProgressEvaluator
from backend.app.agents.autonomy.planner_adapter import AutonomyPlannerAdapter
from backend.app.agents.autonomy.repository import SqlAlchemyAutonomyRepository
from backend.app.db.base import Base
from backend.app.models import agent_autonomy  # noqa: F401


def _ctx(tenant: str = "tenant-a") -> AutonomySecurityContext:
    return AutonomySecurityContext(
        tenant_id=tenant,
        user_id="user-m2",
        roles=["analyst"],
        permissions=["agent.invoke", "agent.read"],
    )


@pytest.mark.asyncio
async def test_planner_adapter_proposes_bounded_churn_plan_and_write_markers():
    adapter = AutonomyPlannerAdapter()
    policy = AutonomyPolicy(max_steps=6, max_replans=2)
    steps = await adapter.propose_initial_plan(
        objective="Investigate sudden rise in customer churn in Q4",
        workflow_id="churn_investigation",
        policy=policy,
        security_context=_ctx(),
    )
    assert 1 <= len(steps) <= 6
    assert any("churn" in s.title.lower() or "evidence" in s.title.lower() for s in steps)
    assert all(not s.is_side_effecting for s in steps)

    write_steps = await adapter.propose_initial_plan(
        objective="Investigate churn and publish externally to partners",
        workflow_id="churn_investigation",
        policy=policy,
        security_context=_ctx(),
    )
    assert any(s.is_side_effecting for s in write_steps)


@pytest.mark.asyncio
async def test_planner_adapter_adaptive_replan_targets_missing_evidence():
    adapter = AutonomyPlannerAdapter()
    policy = AutonomyPolicy(max_steps=6, max_replans=2)
    eval_result = EvaluationResult(
        objective_satisfied=False,
        evidence_sufficient=False,
        should_replan=True,
        reasons=["Missing billing cancellation cohort metrics"],
        missing_evidence=["billing_cancellation_metrics"],
    )
    replanned = await adapter.propose_replan(
        objective="Investigate Q4 churn spike",
        evaluation=eval_result,
        completed_outputs=[{"step": "1", "note": "Partial support logs"}],
        failed_steps=[],
        policy=policy,
        next_step_order=3,
    )
    assert len(replanned) == 2
    assert replanned[0].step_order == 3
    assert "billing_cancellation_metrics" in replanned[0].description


def test_progress_evaluator_detects_missing_evidence_failure_and_completion():
    evaluator = ProgressEvaluator()
    # 1. Incomplete due to missing evidence
    s1 = AutonomousStepRecord(
        execution_id="auto_wf_1",
        tenant_id="tenant-a",
        step_order=1,
        title="Initial search",
        agent_id="research_agent",
        status="succeeded",
        outputs={"evidence_refs": []},
    )
    res_gap = evaluator.evaluate(
        objective="Investigate churn",
        steps=[s1],
        latest_outcome={"evidence_gap": True, "missing_evidence": ["usage_telemetry"]},
    )
    assert res_gap.objective_satisfied is False
    assert res_gap.evidence_sufficient is False
    assert res_gap.should_replan is True
    assert "usage_telemetry" in res_gap.missing_evidence

    # 2. Failed task triggers replan when budget available
    s2 = AutonomousStepRecord(
        execution_id="auto_wf_1",
        tenant_id="tenant-a",
        step_order=2,
        title="Cohort query",
        agent_id="knowledge_analysis",
        status="failed",
        error_code="STEP_TIMEOUT",
    )
    res_fail = evaluator.evaluate(
        objective="Investigate churn",
        steps=[s1, s2],
        latest_outcome={"status": "failed"},
    )
    assert res_fail.objective_satisfied is False
    assert res_fail.should_replan is True

    # 3. Complete with grounded evidence refs
    s3 = AutonomousStepRecord(
        execution_id="auto_wf_1",
        tenant_id="tenant-a",
        step_order=3,
        title="Synthesize findings",
        agent_id="knowledge_analysis",
        status="succeeded",
        outputs={"evidence_refs": ["doc:churn_q4:p1", "doc:billing_spike:p3"]},
    )
    res_done = evaluator.evaluate(
        objective="Investigate churn",
        steps=[s1, s3],
        latest_outcome={"status": "succeeded"},
    )
    assert res_done.objective_satisfied is True
    assert res_done.evidence_sufficient is True
    assert res_done.should_replan is False


@pytest.mark.asyncio
async def test_sqlalchemy_autonomy_repository_persists_across_session_restarts(tmp_path):
    db_file = tmp_path / "autonomy_restart.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repo1 = SqlAlchemyAutonomyRepository(session_factory=session_factory)
    controller1 = AutonomousWorkflowController(repo1)

    wf = await controller1.initialize_workflow(
        AutonomousWorkflowRequest(
            objective="Durable persistence check",
            workflow_id="autonomous_research",
            policy=AutonomyPolicy(max_steps=5, max_replans=1),
        ),
        _ctx("tenant-persist"),
    )
    await repo1.save_steps(
        wf.execution_id,
        "tenant-persist",
        [
            AutonomousStepRecord(
                execution_id=wf.execution_id,
                tenant_id="tenant-persist",
                step_order=1,
                title="Retrieve docs",
                agent_id="research_agent",
                status="succeeded",
                outputs={"evidence_refs": ["doc:1"]},
            )
        ],
    )
    await controller1.consume_step_budget(wf.execution_id, _ctx("tenant-persist"))

    # Simulate fresh process instantiation with new repository instance pointing to same SQLite file
    await engine.dispose()
    engine2 = create_async_engine(db_url, echo=False)
    session_factory2 = async_sessionmaker(engine2, expire_on_commit=False)
    repo2 = SqlAlchemyAutonomyRepository(session_factory=session_factory2)

    restored = await repo2.get_workflow(wf.execution_id, "tenant-persist")
    assert restored is not None
    assert restored.objective == "Durable persistence check"
    assert restored.budget is not None
    assert restored.budget.steps_consumed == 1

    restored_steps = await repo2.list_steps(wf.execution_id, "tenant-persist")
    assert len(restored_steps) == 1
    assert restored_steps[0].outputs == {"evidence_refs": ["doc:1"]}

    restored_events = await repo2.list_events(wf.execution_id, "tenant-persist")
    assert len(restored_events) >= 1

    # Cross-tenant isolation check on DB repository
    assert await repo2.get_workflow(wf.execution_id, "tenant-other") is None
    await engine2.dispose()
