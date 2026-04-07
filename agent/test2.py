from dir_loader import DirectoryRAGAgent
from debt_detector import Debt_Detector
from planner import Planner
import json
import logging

logging.basicConfig(
    format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    level=logging.INFO
)

agent = Planner()
json_result = agent.plan_all(is_test=True)

print(json_result)

with open("plan_test.json", "w", encoding="utf-8") as f:
    json.dump(json_result, f, indent=2, ensure_ascii=False)