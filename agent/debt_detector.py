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

class Debt_Detector():
    """
    This is a high level wrapper for detecting all debt in directory
    and would generate a JSON file for all problem summary in all file inside directory
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
        quest_prompt_path: str = "debt_detector_prompt.txt", 
        quest_prompt_overall_path: str = "debt_detector_overall_prompt.txt", 
    ):
        if dir_loader == None:
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
            agent.initialize()
            self.agent = agent
            self.directory_path = directory_path
            self.file_ls = []
            with open(quest_prompt_path, "r", encoding="utf-8") as f:
                self.prompt = f.read()
            with open(quest_prompt_overall_path, "r", encoding="utf-8") as f:
                self.overall_prompt = f.read()
        else:
            self.agent = dir_loader
            self.directory_path = dir_loader.directory_path
            self.file_ls = []
            with open(quest_prompt_path, "r", encoding="utf-8") as f:
                self.prompt = f.read()
            with open(quest_prompt_overall_path, "r", encoding="utf-8") as f:
                self.overall_prompt = f.read()

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

    def fix_json_format(self, raw_text: str, fix_prompt: str) -> str:
        """
        Call LLM directly (no RAG) to fix malformed JSON output.
        """

        if not self.agent.llm:
            raise ValueError("LLM not initialized")

        full_prompt = f"""
            You are a JSON repair agent.

            Your job:
            Fix the following malformed JSON and return ONLY valid JSON.
            If the malformed JSON end at middle of somewhere, clean the broken part and output fixed JSON.

            Rules:
            - Do NOT add explanations
            - Do NOT wrap in markdown
            - Output must be valid JSON
            - Preserve as much original content as possible
            - If content is duplicated, remove duplicates
            - Ensure proper brackets and commas

            {fix_prompt}

            INPUT:
            {raw_text}

            OUTPUT:
        """

        response = self.agent.llm.invoke(full_prompt).content

        # ChatLiteLLM may return object or string depending on backend
        if hasattr(response, "content"):
            return response.content
        return str(response)
    
    def json_extractor(self, input: str):
        text = input
        fix_prompt = """
            The JSON must strictly follow this schema:

            {
            "findings": [
                {
                "file": "string",
                "category": "string",
                "issue": "string",
                "details": "string",
                "urgency": integer (1-5),
                "evidence": "string"
                }
            ]
            }

            Rules:
            - Output must be valid JSON
            - No markdown, no explanation
            - Top-level key must be exactly "findings"
            - "findings" must be a list
            - Each item must contain ALL required fields
            - Remove duplicate findings
            - Fix broken or incomplete objects
            - Remove invalid entries
            - Ensure "urgency" is integer between 1 and 5
            - If JSON is incomplete, reconstruct it logically
            - If trailing commas or syntax errors exist, fix them
        """
        for attempt in range(5):
            try:
                data = json.loads(text)
                return data
            except json.JSONDecodeError as e:
                text = self.fix_json_format(text, fix_prompt)

        raise ValueError("Failed to parse JSON after retries")

    def debt_search(self, is_test=True):
        # Only pick 10 file in list for test, 
        # I don't want to burn my wallet for simple test!
        """
        The debt search agent aim to provide both overall view across directory on tech debt
        and in detailed tech debt in each specific file.

        It will generate a JSON which contain both info above.
        """

        self.file_detector()
        if is_test:
            ls = self.file_ls[:10]
            print("\n=== Tech debt Search in these files: ===\n")
            print(ls)
        else:
            ls = self.file_ls
            print(f"\n=== Tech debt Search in ALL files (length = {len(ls)}): ===\n")

        all_findings = []
        failed_files = []

        # Overall assessment
        answer = self.agent.ask(self.overall_prompt)
        try:
            output = self.json_extractor(answer)
            findings = output.get("findings", [])
            all_findings.extend(findings)
        except Exception as e:
            print(f"\nFail to read output to JSON!! {e}")
            failed_files.append({"file": "OVERALL", "error": str(e)})

        for file in ls:
            file_path = Path(self.directory_path) / file

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            content = file_path.read_text(encoding="utf-8", errors="replace")
            full_prompt = content + self.prompt + f"\n File Directory: {file}\n"
            print(f"\n Start to detect tech debt in {file}")
            answer = self.agent.llm.invoke(full_prompt).content
            # print(answer)
            try:
                output = self.json_extractor(answer)
                findings = output.get("findings", [])
                all_findings.extend(findings)
            except Exception as e:
                print(f"\nFail to read output to JSON!! {e}")
                failed_files.append({"file": file, "error": str(e)})
            
        final_json = {
            "findings": all_findings,
            "failures": failed_files
        }
        print(f"\n Tech debt detection complete!!!")
        return final_json

        

