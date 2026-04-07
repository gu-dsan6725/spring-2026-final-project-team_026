import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import py_compile


@dataclass
class _LintRun:
    ok: bool
    issues_count: int
    issues_by_symbol: Dict[str, int]
    raw: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class Verifier:
    """
    Verifier agent: compares "before" (original) vs "after" (modernized) artifacts.

    This agent does NOT propose fixes. It produces evidence that changes are safe and
    (optionally) improve static-analysis signals.

    Checks implemented:
      - Python syntax/bytecode compile check (py_compile)
      - Optional pylint JSON output comparison when pylint is installed
    """

    def __init__(
        self,
        before_dir: str,
        after_dir: str,
        lint_tool: str = "pylint",
        timeout_s: int = 120,
    ) -> None:
        self.before_dir = Path(before_dir)
        self.after_dir = Path(after_dir)
        self.lint_tool = lint_tool
        self.timeout_s = timeout_s

    def _py_compile_ok(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        try:
            py_compile.compile(str(file_path), doraise=True)
            return True, None
        except Exception as e:
            return False, str(e)

    def _pylint_available(self) -> bool:
        return shutil.which(self.lint_tool) is not None

    def _run_pylint_json(self, file_path: Path) -> _LintRun:
        if not self._pylint_available():
            return _LintRun(
                ok=False,
                issues_count=0,
                issues_by_symbol={},
                raw=None,
                error=f"{self.lint_tool} not found in PATH",
            )

        cmd = [
            self.lint_tool,
            "--output-format=json",
            "--score=n",
            str(file_path),
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )
        except Exception as e:
            return _LintRun(
                ok=False,
                issues_count=0,
                issues_by_symbol={},
                raw=None,
                error=f"pylint execution failed: {e}",
            )

        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()

        # pylint returns non-zero when issues exist; JSON is still in stdout.
        if not stdout:
            return _LintRun(
                ok=False,
                issues_count=0,
                issues_by_symbol={},
                raw=None,
                error=f"pylint returned empty output (stderr={stderr!r})",
            )

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            return _LintRun(
                ok=False,
                issues_count=0,
                issues_by_symbol={},
                raw=None,
                error=f"failed to parse pylint JSON: {e} (stderr={stderr!r})",
            )

        # Expected: list of dicts. Be defensive.
        issues: List[Dict[str, Any]] = data if isinstance(data, list) else []
        by_symbol: Dict[str, int] = {}
        for item in issues:
            symbol = str(item.get("symbol") or item.get("message-id") or "unknown")
            by_symbol[symbol] = by_symbol.get(symbol, 0) + 1

        return _LintRun(
            ok=True,
            issues_count=len(issues),
            issues_by_symbol=dict(sorted(by_symbol.items(), key=lambda kv: (-kv[1], kv[0]))),
            raw=issues,
            error=None,
        )

    def _resolve_after_path(self, file_rel: str, execution_results: Optional[Dict] = None) -> Optional[Path]:
        """
        Resolve the modernized file path.

        Priority:
          1) execution_results["executions"][...]["output_path"] when present
          2) after_dir / file_rel fallback
        """
        if execution_results:
            for e in execution_results.get("executions", []):
                if e.get("file") == file_rel and e.get("status") == "succeeded":
                    out = e.get("output_path")
                    if out:
                        return Path(out)
        return self.after_dir / file_rel

    def verify_all(
        self,
        execution_results: Optional[Dict] = None,
        files: Optional[List[str]] = None,
        is_test: bool = True,
    ) -> Dict:
        """
        Verify a list of files (relative paths) or infer from execution_results.

        Returns:
          {
            "verifications": [
               {
                 "file": "...",
                 "before": {...},
                 "after": {...},
                 "improvement": {...}
               }, ...
            ],
            "summary": {
              "files_checked": int,
              "syntax_pass": int,
              "syntax_pass_rate": float,
              "lint_tool": "pylint" | null,
              "total_improvement": int | null
            }
          }
        """
        if files is None:
            if execution_results:
                files = [e["file"] for e in execution_results.get("executions", []) if e.get("status") == "succeeded"]
            else:
                files = []

        files = list(dict.fromkeys(files))  # de-dupe, preserve order
        if is_test:
            files = files[:3]

        verifications: List[Dict[str, Any]] = []
        total_improvement: Optional[int] = 0 if self._pylint_available() else None
        syntax_pass = 0

        for file_rel in files:
            before_path = self.before_dir / file_rel
            after_path = self._resolve_after_path(file_rel, execution_results=execution_results)

            entry: Dict[str, Any] = {"file": file_rel}

            if not before_path.exists():
                entry["status"] = "skipped"
                entry["error"] = f"before file not found: {before_path}"
                verifications.append(entry)
                continue

            if after_path is None or not after_path.exists():
                entry["status"] = "skipped"
                entry["error"] = f"after file not found: {after_path}"
                verifications.append(entry)
                continue

            before_syntax_ok, before_syntax_err = self._py_compile_ok(before_path)
            after_syntax_ok, after_syntax_err = self._py_compile_ok(after_path)

            if before_syntax_ok and after_syntax_ok:
                syntax_pass += 1

            before_lint = self._run_pylint_json(before_path) if self._pylint_available() else None
            after_lint = self._run_pylint_json(after_path) if self._pylint_available() else None

            improvement = None
            if before_lint and after_lint and before_lint.ok and after_lint.ok:
                improvement = before_lint.issues_count - after_lint.issues_count
                if total_improvement is not None:
                    total_improvement += improvement

            entry.update(
                {
                    "status": "checked",
                    "before": {
                        "path": str(before_path),
                        "syntax_ok": before_syntax_ok,
                        "syntax_error": before_syntax_err,
                        "lint": None
                        if before_lint is None
                        else {
                            "ok": before_lint.ok,
                            "issues_count": before_lint.issues_count,
                            "issues_by_symbol": before_lint.issues_by_symbol,
                            "error": before_lint.error,
                        },
                    },
                    "after": {
                        "path": str(after_path),
                        "syntax_ok": after_syntax_ok,
                        "syntax_error": after_syntax_err,
                        "lint": None
                        if after_lint is None
                        else {
                            "ok": after_lint.ok,
                            "issues_count": after_lint.issues_count,
                            "issues_by_symbol": after_lint.issues_by_symbol,
                            "error": after_lint.error,
                        },
                    },
                    "improvement": {
                        "lint_issue_reduction": improvement,
                    },
                }
            )

            verifications.append(entry)

        files_checked = sum(1 for v in verifications if v.get("status") == "checked")
        syntax_pass_rate = round(syntax_pass / files_checked, 3) if files_checked else 0.0

        return {
            "verifications": verifications,
            "summary": {
                "files_checked": files_checked,
                "syntax_pass": syntax_pass,
                "syntax_pass_rate": syntax_pass_rate,
                "lint_tool": self.lint_tool if self._pylint_available() else None,
                "total_improvement": total_improvement,
            },
        }

