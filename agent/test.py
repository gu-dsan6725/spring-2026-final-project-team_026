from dir_loader import DirectoryRAGAgent
from debt_detector import Debt_Detector
import json
import logging

logging.basicConfig(
    format='[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    level=logging.INFO
)

agent = Debt_Detector()
json_result = agent.debt_search(is_test=True)

print(json_result)

with open("debt_detect_test.json", "w", encoding="utf-8") as f:
    json.dump(json_result, f, indent=2, ensure_ascii=False)