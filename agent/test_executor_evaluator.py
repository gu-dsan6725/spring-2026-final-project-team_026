"""
Quick end-to-end test for the Executor and Evaluator agents.

Run from the agent/ directory:
    python test_executor_evaluator.py

Uses cached debt_detect_test.json and plan_test.json (root of repo)
so no LLM calls are needed for detection/planning.
The Executor WILL call the LLM to apply fixes (requires GROQ_API_KEY in .env).
"""

import json
import os
import sys

# Run from agent/ dir; JSON artifacts live one level up
ROOT = os.path.join(os.path.dirname(__file__), "..")

from executor import Executor
from evaluator import Evaluator


def main():
    plan_path = os.path.join(ROOT, "plan_test.json")
    debt_path = os.path.join(ROOT, "debt_detect_test.json")
    directory_path = os.path.join(ROOT, "old-demos/")
    output_dir = os.path.join(ROOT, "old-demos-modernized/")

    # ── Step 1: Run Executor (test mode = first 3 files only) ──────────────
    print("=" * 60)
    print("STEP 1: Executor")
    print("=" * 60)

    executor = Executor(
        directory_path=directory_path,
        output_dir=output_dir,
        plan_json_path=plan_path,
    )
    execution_results = executor.execute_all(is_test=True)

    # Save execution results for inspection
    exec_out_path = os.path.join(ROOT, "execution_test.json")
    with open(exec_out_path, "w", encoding="utf-8") as f:
        json.dump(execution_results, f, indent=2, ensure_ascii=False)
    print(f"\nExecution results saved to: {exec_out_path}")

    # ── Step 2: Run Evaluator ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Evaluator")
    print("=" * 60)

    with open(debt_path, "r", encoding="utf-8") as f:
        debt_findings = json.load(f)

    evaluator = Evaluator()
    metrics = evaluator.compute_metrics(debt_findings, execution_results)
    report = evaluator.generate_report(metrics)

    print("\n" + report)

    # Save report for inspection
    report_path = os.path.join(ROOT, "eval_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nEvaluation report saved to: {report_path}")

    # ── Step 3: Spot-check one modernized file ─────────────────────────────
    succeeded = [e for e in execution_results["executions"] if e["status"] == "succeeded"]
    if succeeded:
        sample = succeeded[0]
        print("\n" + "=" * 60)
        print(f"STEP 3: Spot-check — {sample['file']}")
        print("=" * 60)

        original_path = os.path.join(directory_path, sample["file"])
        modernized_path = sample["output_path"]

        with open(original_path, encoding="utf-8", errors="replace") as f:
            original_lines = f.readlines()
        with open(modernized_path, encoding="utf-8", errors="replace") as f:
            modernized_lines = f.readlines()

        print(f"Original:   {len(original_lines)} lines")
        print(f"Modernized: {len(modernized_lines)} lines")
        print(f"Diff (line count change): {len(modernized_lines) - len(original_lines):+d}")
    else:
        print("\nNo files were successfully modernized — check execution_test.json for errors.")


if __name__ == "__main__":
    main()
