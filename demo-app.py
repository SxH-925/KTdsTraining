import os
import re
import json
from dotenv import load_dotenv
from openai import AzureOpenAI
import streamlit as st
from streamlit_ace import st_ace  # 추가

# Load environment variables
load_dotenv()

openai_endpoint = os.getenv("OPENAI_ENDPOINT")
openai_api_key = os.getenv("OPENAI_API_KEY")
chat_model = os.getenv("CHAT_MODEL")
search_endpoint = os.getenv("SEARCH_ENDPOINT")
search_api_key = os.getenv("SEARCH_API_KEY")
index_name = os.getenv("INDEX_NAME")

# Initialize Azure OpenAI client
chat_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=openai_endpoint,
    api_key=openai_api_key
)

st.set_page_config(page_title="SonarQube 룰 분석 Assistant", layout="wide")

# --- 사이드바 추가 ---
st.sidebar.image("data/logo.png", width=100)
st.sidebar.markdown("---")
st.sidebar.markdown("#### 메뉴")
if st.sidebar.button("✅ MVP 과제", use_container_width=True):
    st.session_state.menu = "mvp"

# --- 메인 화면 헤더 ---
st.title("⌨️ CodeEyes Assistant")
st.caption("💡 SonarQube 룰 기반 코드 품질 분석 및 수정 코드 제안을 도와드립니다.")

# --- Load system prompt from file ---
def load_system_prompt():
    with open("prompt/system_prompt.md", "r", encoding="utf-8") as f:
        return f.read()

# --- 초기 System Prompt 설정 ---
if "messages" not in st.session_state:
    st.session_state.followup_response = ""
    st.session_state.messages = [
        {
            "role": "system",
            "content": load_system_prompt()
        }
    ]

# --- LLM 응답 처리 함수 ---
def get_openai_response(use_rag=True):
    rag_params = {
        "data_sources": [
            {
                "type": "azure_search",
                "parameters": {
                    "endpoint": search_endpoint,
                    "index_name": index_name,
                    "authentication": {
                        "type": "api_key",
                        "key": search_api_key,
                    }
                }
            }
        ]
    } if use_rag else {}

    response = chat_client.chat.completions.create(
        model=chat_model,
        messages=st.session_state.messages,
        extra_body=rag_params
    )
    return response.choices[0].message.content

# --- Markdown 파싱 함수 ---
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
    parsed['severity'] = re.search(r"\*\*등급\*\*: *(.+)", markdown_text)
    parsed['category'] = re.search(r"\*\*범주\*\*: *(.+)", markdown_text)
    parsed['description'] = re.search(
      r"\*\*설명\*\*: *\n?(.+?)(?=\n\*\*오탐/정탐 여부\*\*:)", markdown_text, re.DOTALL)
    parsed['verdict'] = re.search(r"\*\*오탐/정탐 여부\*\*: *`?([^\n*`]+)`?", markdown_text)
    parsed['difficulty'] = re.search(r"\*\*수정 난이도\*\*: *`?([^\n*`]+)`?", markdown_text)
    parsed['fix_code'] = re.search(r"```(?:[a-zA-Z]+)?\n(.+?)\n```", markdown_text, re.DOTALL)

    return {
        "rule": parsed['rule'].group(1).strip() if parsed['rule'] else None,
        "severity": parsed['severity'].group(1).strip() if parsed['severity'] else None,
        "category": parsed['category'].group(1).strip() if parsed['category'] else None,
        "description": parsed['description'].group(1).strip() if parsed['description'] else None,
        "verdict": normalize_verdict(parsed['verdict'].group(1).strip()) if parsed['verdict'] else None,
        "difficulty": parsed['difficulty'].group(1).strip() if parsed['difficulty'] else None,
        "fix_code": parsed['fix_code'].group(1).strip() if parsed['fix_code'] else None,
    }

# --- Input UI + Result ---
with st.expander("🛠 분석 정보 입력", expanded=True):
    col_lang, col_rule = st.columns([1, 3])
    with col_lang:
        language = st.selectbox("언어", ["Python", "Java", "JavaScript"], index=0)

    with col_rule:
        with open("data/rules_list.json", "r", encoding="utf-8") as f:
            rule_db = json.load(f)
        rule_options = rule_db.get(language, [])
        rule_titles = [f"{r['title']}" for r in rule_options]
        selected_rule = st.selectbox("룰 선택 (입력 시 자동 검색)", options=rule_titles)

    rulename = selected_rule.split(" - ")[0] if selected_rule else ""

    # 코드 입력 및 미리보기: Ace editor 스타일 적용
    st.markdown("**🔤 분석할 코드를 입력하세요:**")
    code = st_ace(language=language.lower(), theme="monokai", height=300, key="ace_input", auto_update=True)

    analyze_button = st.button("🚀 Analyze", use_container_width=True, disabled=not (rulename.strip() and code and code.strip()))

    if analyze_button:
        st.session_state.followup_response = ""
        with st.spinner("분석 중입니다..."):
            st.session_state.messages.append({
                "role": "user",
                "content": f"language: {language}\nrulename: {rulename}\ncode:\n{code}"
            })
            result_markdown = get_openai_response()
            parsed_result = parse_markdown_response(result_markdown)

            if not parsed_result['rule']:
                st.markdown("#### [디버그] 응답 원문")
                st.code(result_markdown)
                st.error("❌ 분석 결과를 정상적으로 이해하지 못했습니다. 입력값을 다시 확인해 주세요.")
                st.stop()

            st.session_state.analysis_result = parsed_result

# --- 분석 결과 표시 ---
if "analysis_result" in st.session_state:
    st.markdown("---")
    st.markdown("#### 📊 분석 결과")

    result = st.session_state.analysis_result
    st.subheader(f"🧾 룰명: {result['rule']}")
    st.markdown(f"**등급**: {result['severity']}  ")
    st.markdown(f"**범주**: {result['category']}")
    st.markdown(f"**설명**: {result['description'] if result['description'] else 'N/A'}")

    if result['verdict']:
        if result['verdict'] == "정탐":
            st.markdown("**🧠 정탐/오탐 여부**: :green[`정탐`]")  
            if result.get("difficulty"):
                st.markdown(f"**🛠️ 수정 난이도**: `{result['difficulty']}`")
                st.info("⚠️ 생성된 코드는 AI가 제안한 예시이며, 개발자의 검토 후 반영되어야 합니다.")
        elif result['verdict'] == "오탐":
            st.markdown("**🧠 정탐/오탐 여부**: :orange[`오탐`]") 
        else:
            st.markdown("**🧠 정탐/오탐 여부**: :red[`알 수 없음`]")  
    else:
        st.markdown("**🧠 정탐/오탐 여부**: :red[`분석 실패 또는 미확인`]")  

    if result['verdict'] == "정탐":
        if result['fix_code']:
            st.markdown("### ✅ 수정 코드 제안")
            st.code(result['fix_code'], language=language.lower())
        else:
            st.warning("✅ 정탐으로 판단되었지만, 수정 코드가 제공되지 않았습니다. 추가 질문으로 요청해 보세요.")

    st.markdown("---")
    followup = st.text_area("💬 추가 질문을 입력하세요", key="followup_input")

    if followup:
        st.markdown("---")
        st.markdown("#### 💬 추가 질문에 대한 AI의 답변")
        st.session_state.messages.append({"role": "user", "content": followup})
        with st.spinner("답변 생성 중..."):
            followup_response = get_openai_response(use_rag=True)
        st.session_state.messages.append({"role": "assistant", "content": followup_response})
        st.session_state.followup_response = followup_response

    if "followup_response" in st.session_state:
        st.markdown("**AI 답변:**")
        st.markdown(st.session_state.followup_response)
