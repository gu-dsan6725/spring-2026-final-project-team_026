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

class Planner():
    """
    This is a high level wrapper for planing tech debt fixing job of each file in directory
    and would generate a JSON file for each problem to guide further agent fixing
    """
    def __init__(
        self,
        dir_loader: DirectoryRAGAgent = None,
        directory_path: str = "old-demos/",
        model_id: str = "groq/llama-3.1-8b-instant",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        glob_patterns: Optional[List[str]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        temperature: float = 0,
        default_k: int = 10,
        use_mmr: bool = False,
        tech_debt_detected: str = "debt_detect_test.json", 
    ):
        if dir_loader is None:
            agent = DirectoryRAGAgent(
                directory_path,
                model_id,
                embedding_model_name,
                glob_patterns,
                chunk_size,
                chunk_overlap,
                temperature,
                default_k,
                use_mmr
            )
            # agent.initialize()
            self.agent = agent
            self.directory_path = directory_path
            self.file_ls = []
        else:
            self.agent = dir_loader
            self.directory_path = dir_loader.directory_path
            self.file_ls = []

        with open(tech_debt_detected, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def file_detector(self):
        """
        Scan directory and return all relevant files as relative paths.
        """

        if not self.directory_path:
            raise ValueError("directory_path is not set")

        root = Path(self.directory_path)

        allowed_suffixes = {".py", ".md", ".txt", ".sh"}

        file_list = []

        for path in root.rglob("*"):
            if path.is_file() and path.suffix in allowed_suffixes:
                # convert to relative path
                rel_path = path.relative_to(root)
                file_list.append(str(rel_path))

        # remove duplicates + sort
        file_list = sorted(set(file_list))
        self.file_ls = file_list

    def plan_all(self, is_test = True):
        """
        Generating plan to fix solution base on tech debt record detected by 
        debt_detector and overall tech debt assessment
        Extract each json finding with file path, combine with overall finding and stack to 
        llm for planing

        output one JSON file containing solution for each file.
        """

        self.file_detector()
        if is_test:
            ls = self.file_ls[:10]
            print("\n=== Tech debt solution planing  in these files: ===\n")
            print(ls)
        else:
            ls = self.file_ls
            print(f"\n=== Tech debt solution planing in ALL files (length = {len(ls)}): ===\n")

        overall_findings = sorted(
            [f for f in self.data["findings"] if f["file"] == "OVERALL"],
            key=lambda x: x["urgency"],
            reverse=True
        )
        all_plan = []
        for file in ls:
            file_findings = sorted([f for f in self.data["findings"] if f["file"] == file], key=lambda x: x["urgency"], reverse=True)

            plan_prompt = f"""
                You are a senior software engineer responsible for planning technical debt remediation.
                Your goal is to generate a clear, structured fix plan guiding for further fix for a specific file.

                ---
                Target file:
                {file}
                ---
                Findings specific to this file (sorted by urgency, IMPORTANT):
                {file_findings}
                ---
                Overall repository findings (sorted by urgency, should be use for only reference, DO NOT use it if not related, LESS IMPORTANT):
                {overall_findings}
                ---

                Instructions:

                1. Analyze the file-specific findings and identify the most critical issues.
                2. Use the overall repository findings to understand if any global issues affect this file.
                3. Do NOT blindly trust all findings — prioritize issues with clear evidence and higher urgency.
                4. Group related issues when possible (e.g., same root cause or same type).
                5. Move uncertain compatibility items out of “Recommended Fix Plan"
                6. Identify dependencies:

                * Which fixes must be done before others?
                * Which fixes depend on repo-wide changes?

                ---

                Output the plan in the following structure:

                ### 1. Summary

                Briefly describe the main technical debt problems in this file.

                ### 2. Recommended Fix Plan (ordered)

                List steps in execution order. For each step include:

                * What to fix
                * Why it matters
                * Related findings (by category or description)

                ### 3. Verification Required Before Fix

                For each step, list:

                * uncertain findings that need code inspection before any change
                * High changing risk part that need special attention and further assessment
                * Compatibility findings can never appear in “Recommended Fix Plan” unless the evidence contains an explicit deprecated API, removed syntax, or a concrete failing construct.

                ### 4. Risk Assessment

                For each step, label:

                * Low risk (local, safe change)
                * Medium risk (affects multiple functions)
                * High risk (cross-file or architectural)

                ### 5. Dependencies / Blockers

                * Any fixes that should happen before others
                * Any repo-wide issues affecting this file

                ### 6. Quick Wins

                List easy, low-risk improvements that can be done immediately.

                ---

                Be specific, actionable, and avoid vague statements.
                Since you don't see the code and only read previous finding,
                avoid having detailed code adjustment command.

            """
            answer = self.agent.llm.invoke(plan_prompt).content
            all_plan.append(answer)
        

        final_json = {
            "plans": []
        }

        for file, plan in zip(ls, all_plan):
            final_json["plans"].append({
                "file": file,
                "plan_content": plan
            })
        
        return final_json






        
