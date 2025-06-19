import os
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI 설정
openai_endpoint = os.getenv("OPENAI_ENDPOINT")
openai_api_key = os.getenv("OPENAI_API_KEY")
chat_model = os.getenv("CHAT_MODEL")

# Azure Cognitive Search 설정
search_endpoint = os.getenv("SEARCH_ENDPOINT")
search_api_key = os.getenv("SEARCH_API_KEY")
index_name = os.getenv("INDEX_NAME")

# 시스템 프롬프트 로드 함수
def load_system_prompt():
    with open("prompt/system_prompt.md", "r", encoding="utf-8") as f:
        return f.read()

# 룰 리스트 로드 함수
def load_rule_list(language):
    with open("data/rules_list.json", "r", encoding="utf-8") as f:
        rules = json.load(f)
    return rules.get(language, [])

