import json
from collections import Counter, defaultdict
from typing import Dict, Optional


class Evaluator():
    """
    Evaluator agent: computes before/after metrics from the outputs of
    Debt_Detector, Executor (and optionally Verifier) to measure how much
    technical debt was addressed by the modernization pipeline.
    """

    def __init__(self):
        pass

    def compute_metrics(
        self,
        debt_findings: Dict,
        execution_results: Dict,
        verification_results: Optional[Dict] = None,
    ) -> Dict:
        """
        Compute evaluation metrics from pipeline outputs.

        Args:
            debt_findings: output of Debt_Detector.debt_search()
                           {"findings": [...], "failures": [...]}
            execution_results: output of Executor.execute_all()
                               {"executions": [...], "summary": {...}}
            verification_results: (optional) output of Verifier.verify_all()
                                  {"verifications": [...], "summary": {...}}

        Returns:
            dict of metrics
        """
        findings = debt_findings.get("findings", [])
        file_findings = [f for f in findings if f.get("file") != "OVERALL"]

        # --- Debt coverage metrics ---
        files_with_debt = len(set(f["file"] for f in file_findings))

        urgency_dist = Counter(f.get("urgency", 0) for f in file_findings)
        categories = Counter(f.get("category", "unknown") for f in file_findings)

        total_findings = len(file_findings)
        high_urgency_findings = sum(v for k, v in urgency_dist.items() if k >= 4)

        # --- Execution metrics ---
        exec_summary = execution_results.get("summary", {})
        executions = execution_results.get("executions", [])

        files_executed = exec_summary.get("total", 0)
        files_succeeded = exec_summary.get("succeeded", 0)
        files_failed = exec_summary.get("failed", 0)
        files_skipped = exec_summary.get("skipped", 0)

        execution_success_rate = (
            round(files_succeeded / files_executed, 3) if files_executed > 0 else 0.0
        )

        # Map succeeded files to their plans (for coverage analysis)
        succeeded_files = {e["file"] for e in executions if e["status"] == "succeeded"}
        files_with_debt_set = set(f["file"] for f in file_findings)
        debt_coverage = (
            round(len(succeeded_files & files_with_debt_set) / files_with_debt, 3)
            if files_with_debt > 0
            else 0.0
        )

        # --- Verification metrics (optional) ---
        syntax_pass_rate = None
        total_flake8_improvement = None
        if verification_results:
            ver_summary = verification_results.get("summary", {})
            files_checked = ver_summary.get("files_checked", 0)
            syntax_pass = ver_summary.get("syntax_pass", 0)
            syntax_pass_rate = (
                round(syntax_pass / files_checked, 3) if files_checked > 0 else 0.0
            )
            total_flake8_improvement = ver_summary.get("total_improvement", None)

        metrics = {
            "debt_analysis": {
                "files_with_debt": files_with_debt,
                "total_findings": total_findings,
                "high_urgency_findings": high_urgency_findings,
                "urgency_distribution": dict(sorted(urgency_dist.items())),
                "top_categories": dict(categories.most_common(5)),
            },
            "execution": {
                "files_executed": files_executed,
                "files_succeeded": files_succeeded,
                "files_failed": files_failed,
                "files_skipped": files_skipped,
                "execution_success_rate": execution_success_rate,
                "debt_coverage_rate": debt_coverage,
            },
        }

        if syntax_pass_rate is not None:
            metrics["verification"] = {
                "syntax_pass_rate": syntax_pass_rate,
                "total_flake8_improvement": total_flake8_improvement,
            }

        return metrics

    def generate_report(self, metrics: Dict) -> str:
        """
        Render a human-readable markdown evaluation report from metrics.
        """
        debt = metrics.get("debt_analysis", {})
        execution = metrics.get("execution", {})
        verification = metrics.get("verification", None)

        lines = [
            "# Codapter Evaluation Report",
            "",
            "## Tech Debt Analysis (Before Modernization)",
            "",
            f"- **Files with detected debt:** {debt.get('files_with_debt', 'N/A')}",
            f"- **Total findings:** {debt.get('total_findings', 'N/A')}",
            f"- **High-urgency findings (4-5):** {debt.get('high_urgency_findings', 'N/A')}",
            "",
            "### Urgency Distribution",
            "",
        ]

        urgency_dist = debt.get("urgency_distribution", {})
        for level in sorted(urgency_dist):
            bar = "█" * urgency_dist[level]
            lines.append(f"  - Urgency {level}: {urgency_dist[level]:>3}  {bar}")

        lines += [
            "",
            "### Top Debt Categories",
            "",
        ]
        for cat, count in debt.get("top_categories", {}).items():
            lines.append(f"  - {cat}: {count}")

        lines += [
            "",
            "## Execution Results",
            "",
            f"- **Files attempted:** {execution.get('files_executed', 'N/A')}",
            f"- **Successfully modernized:** {execution.get('files_succeeded', 'N/A')}",
            f"- **Failed:** {execution.get('files_failed', 'N/A')}",
            f"- **Skipped:** {execution.get('files_skipped', 'N/A')}",
            f"- **Execution success rate:** {execution.get('execution_success_rate', 'N/A'):.1%}"
                if isinstance(execution.get('execution_success_rate'), float)
                else f"- **Execution success rate:** {execution.get('execution_success_rate', 'N/A')}",
            f"- **Debt coverage rate:** {execution.get('debt_coverage_rate', 'N/A'):.1%}"
                if isinstance(execution.get('debt_coverage_rate'), float)
                else f"- **Debt coverage rate:** {execution.get('debt_coverage_rate', 'N/A')}",
        ]

        if verification:
            lines += [
                "",
                "## Verification Results",
                "",
                f"- **Syntax pass rate:** {verification.get('syntax_pass_rate', 'N/A'):.1%}"
                    if isinstance(verification.get('syntax_pass_rate'), float)
                    else f"- **Syntax pass rate:** {verification.get('syntax_pass_rate', 'N/A')}",
            ]
            if verification.get("total_flake8_improvement") is not None:
                lines.append(f"- **Total flake8 error reduction:** {verification['total_flake8_improvement']}")

        return "\n".join(lines)
