import json
import os
import sys
from datetime import datetime
from pathlib import Path


def _ensure_agent_importable(repo_root: Path) -> None:
    agent_dir = repo_root / "agent"
    if str(agent_dir) not in sys.path:
        sys.path.insert(0, str(agent_dir))


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    _ensure_agent_importable(repo_root)

    # Import after sys.path manipulation (agent/*.py uses non-package imports)
    from debt_detector import Debt_Detector
    from planner import Planner
    from executor import Executor
    from verifier import Verifier
    from evaluator import Evaluator

    before_dir = repo_root / "old-demos"
    after_dir = repo_root / "old-demos-modernized"

    if not before_dir.exists() or not any(before_dir.rglob("*")):
        print("ERROR: ./old-demos is missing or empty.")
        print("Run: ./scripts/fetch_sample_data.sh")
        return 1

    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY is not set.")
        print("Set it in your shell or a .env file, e.g.:")
        print('  export GROQ_API_KEY="your_key_here"')
        print("")
        print("Then rerun:")
        print("  python demo.py")
        return 1

    artifacts_dir = repo_root / "artifacts" / datetime.now().strftime("%Y%m%d_%H%M%S")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("STEP 1: Debt Detector")
    print("=" * 60)
    detector = Debt_Detector(directory_path=str(before_dir))
    debt_findings = detector.debt_search(is_test=True)
    debt_path = artifacts_dir / "debt_findings.json"
    debt_path.write_text(json.dumps(debt_findings, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {debt_path}")

    print("\n" + "=" * 60)
    print("STEP 2: Planner")
    print("=" * 60)
    planner = Planner(directory_path=str(before_dir), tech_debt_detected=str(debt_path))
    plan = planner.plan_all(is_test=True)
    plan_path = artifacts_dir / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {plan_path}")

    print("\n" + "=" * 60)
    print("STEP 3: Executor")
    print("=" * 60)
    executor = Executor(directory_path=str(before_dir), output_dir=str(after_dir), plan_json_path=str(plan_path))
    execution_results = executor.execute_all(is_test=True)
    exec_path = artifacts_dir / "execution.json"
    exec_path.write_text(json.dumps(execution_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {exec_path}")

    print("\n" + "=" * 60)
    print("STEP 4: Verifier")
    print("=" * 60)
    verifier = Verifier(before_dir=str(before_dir), after_dir=str(after_dir))
    verification_results = verifier.verify_all(execution_results=execution_results, is_test=True)
    ver_path = artifacts_dir / "verification.json"
    ver_path.write_text(json.dumps(verification_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {ver_path}")

    print("\n" + "=" * 60)
    print("STEP 5: Evaluator (report)")
    print("=" * 60)
    evaluator = Evaluator()
    metrics = evaluator.compute_metrics(
        debt_findings=debt_findings,
        execution_results=execution_results,
        verification_results=verification_results,
    )
    metrics_path = artifacts_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved: {metrics_path}")

    report = evaluator.generate_report(metrics)
    report_path = artifacts_dir / "eval_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Saved: {report_path}")

    print("\nDemo completed.")
    print(f"Artifacts: {artifacts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

