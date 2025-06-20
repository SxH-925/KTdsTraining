import re

def normalize_verdict(text):
    if not text:
        return None
    lowered = text.lower()
    if "정탐" in lowered:
        return "정탐"
    elif "오탐" in lowered:
        return "오탐"
    return None

def parse_markdown_response(markdown_text):
    parsed = {}

    parsed['rule'] = re.search(r"##+\s*(?:[\W_]*\s*)?Rule[:：]?\s*(.+)", markdown_text)
    parsed['severity'] = re.search(r"(?:\*\*등급\*\*|등급)[:：]?\s*(.+)", markdown_text)
    parsed['category'] = re.search(r"(?:\*\*범주\*\*|범주)[:：]?\s*(.+)", markdown_text)
    parsed['description'] = re.search(r"\*\*설명\*\*: *\n?(.+?)(?=\n\*\*오탐/정탐 여부\*\*:)", markdown_text, re.DOTALL)
    parsed['verdict'] = re.search(r"\*\*오탐/정탐 여부\*\*: *`?([^\n*`]+)`?", markdown_text)
    parsed['difficulty'] = re.search(r"\*\*수정 난이도\*\*: *`?([^\n*`]+)`?", markdown_text)
    parsed['fix_code'] = re.search(r"```(?:[a-zA-Z]+)?\n(.+?)\n```", markdown_text, re.DOTALL)
    parsed['relevance'] = re.search(r"\*\*관련성\*\*: *`?([^\n*`]+)`?", markdown_text)

    result = {
        "rule": parsed['rule'].group(1).strip() if parsed['rule'] else None,
        "severity": parsed['severity'].group(1).strip() if parsed['severity'] else None,
        "category": parsed['category'].group(1).strip() if parsed['category'] else None,
        "description": parsed['description'].group(1).strip() if parsed['description'] else None,
        "verdict": normalize_verdict(parsed['verdict'].group(1).strip()) if parsed['verdict'] else None,
        "difficulty": parsed['difficulty'].group(1).strip() if parsed['difficulty'] else None,
        "fix_code": parsed['fix_code'].group(1).strip() if parsed['fix_code'] else None,
        "relevance": parsed['relevance'].group(1).strip() if parsed['relevance'] else "없음"
    }

    if result["verdict"] == "정탐" and not result["fix_code"]:
        result["parse_error"] = "정탐인데 수정 코드가 없습니다"
    elif result["verdict"] == "오탐" and not result["difficulty"]:
        result["parse_error"] = "오탐인데 난이도 항목이 없습니다"
    elif not result["verdict"]:
        result["parse_error"] = "정탐/오탐 여부 항목이 응답에 포함되지 않았습니다. 프롬프트나 응답 형식을 확인하세요."

    return result
