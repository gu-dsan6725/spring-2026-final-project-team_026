from dir_loader import DirectoryRAGAgent
import logging
import os
from pathlib import Path
import json
from typing import List, Optional, Dict, Any

logging.basicConfig(
    format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    level=logging.INFO
)


class Executor():
    """
    Executor agent: takes the Planner's fix plans, reads each target file,
    prompts the LLM to apply the recommended changes, and writes modernized
    files to an output directory. The original files are never modified.
    """

    def __init__(
        self,
        dir_loader: DirectoryRAGAgent = None,
        directory_path: str = "old-demos/",
        output_dir: str = "old-demos-modernized/",
        model_id: str = "groq/llama-3.1-8b-instant",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        plan_json: Optional[Dict] = None,
        plan_json_path: str = "plan_test.json",
        temperature: float = 0.1,
    ):
        if dir_loader is None:
            agent = DirectoryRAGAgent(
                directory_path,
                model_id,
                embedding_model_name,
                temperature=temperature,
            )
            self.agent = agent
            self.directory_path = directory_path
        else:
            self.agent = dir_loader
            self.directory_path = dir_loader.directory_path

        self.output_dir = output_dir

        if plan_json is not None:
            self.plan_data = plan_json
        else:
            with open(plan_json_path, "r", encoding="utf-8") as f:
                self.plan_data = json.load(f)

    def execute_file(self, file: str, plan_content: str) -> Dict:
        """
        Read the original file, ask the LLM to apply the fix plan, and write
        the modernized version to output_dir.

        Returns a dict with keys: file, status, output_path, error.
        """
        src_path = Path(self.directory_path) / file
        if not src_path.exists():
            return {"file": file, "status": "skipped", "output_path": None, "error": f"Source file not found: {src_path}"}

        try:
            original_content = src_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"file": file, "status": "failed", "output_path": None, "error": f"Could not read file: {e}"}

        prompt = f"""You are a senior software engineer modernizing legacy Python code.

=== FILE: {file} ===
{original_content}
=== END FILE ===

=== FIX PLAN ===
{plan_content}
=== END PLAN ===

Instructions:
1. Apply the fixes described in the "Recommended Fix Plan" and "Quick Wins" sections.
2. Only apply LOW or MEDIUM risk changes. Skip HIGH risk or architectural changes entirely.
3. Preserve all existing functionality — do not change logic, only clean up tech debt.
4. Output ONLY the complete modernized file content.
5. Do NOT wrap the output in markdown code fences or add any explanation.

Output the complete modernized file:
"""

        try:
            response = self.agent.llm.invoke(prompt)
            modernized_content = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            return {"file": file, "status": "failed", "output_path": None, "error": f"LLM call failed: {e}"}

        # Strip accidental markdown fences the LLM may have included
        modernized_content = self._strip_fences(modernized_content)

        out_path = Path(self.output_dir) / file
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            out_path.write_text(modernized_content, encoding="utf-8")
        except Exception as e:
            return {"file": file, "status": "failed", "output_path": None, "error": f"Could not write output: {e}"}

        print(f"  [OK] {file} -> {out_path}")
        return {"file": file, "status": "succeeded", "output_path": str(out_path), "error": None}

    def _strip_fences(self, text: str) -> str:
        """Remove leading/trailing markdown code fences if present."""
        lines = text.strip().splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines)

    def execute_all(self, is_test: bool = True) -> Dict:
        """
        Iterate over all plans and apply each one. When is_test=True, only
        processes the first 3 plans to limit API usage.

        Returns:
            {
                "executions": [ {file, status, output_path, error}, ... ],
                "summary": {total, succeeded, failed, skipped}
            }
        """
        plans = self.plan_data.get("plans", [])

        if is_test:
            plans = plans[:3]
            print(f"\n=== Executor running on {len(plans)} files (test mode) ===\n")
        else:
            print(f"\n=== Executor running on ALL {len(plans)} files ===\n")

        executions = []
        for entry in plans:
            file = entry.get("file", "")
            plan_content = entry.get("plan_content", "")
            if not file or not plan_content:
                executions.append({"file": file, "status": "skipped", "output_path": None, "error": "Missing file or plan_content"})
                continue
            print(f"Executing fix for: {file}")
            result = self.execute_file(file, plan_content)
            executions.append(result)

        summary = {
            "total": len(executions),
            "succeeded": sum(1 for e in executions if e["status"] == "succeeded"),
            "failed": sum(1 for e in executions if e["status"] == "failed"),
            "skipped": sum(1 for e in executions if e["status"] == "skipped"),
        }

        print(f"\n=== Execution complete: {summary} ===\n")
        return {"executions": executions, "summary": summary}
