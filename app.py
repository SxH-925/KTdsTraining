import os
import re
import json
import streamlit as st
from streamlit_ace import st_ace
from config import load_system_prompt, load_rule_list, search_endpoint, search_api_key, index_name
from parser import parse_markdown_response
from llm import get_openai_response, regenerate_fix_code
from config import load_system_prompt

system_prompt = load_system_prompt()

st.set_page_config(page_title="CodeEyes Assistant", layout="wide")

# --- 사이드바 ---
st.sidebar.image("data/logo.png", width=100)
if st.sidebar.button("🧰 MVP 과제", use_container_width=True):
    st.session_state.menu = "mvp"

# --- 헤더 ---
st.markdown("""
<style>
@keyframes wave {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.wave-header {
  animation: wave 8s ease-in-out infinite;
  background: linear-gradient(270deg, #EEAECA, #94BBE9);
  background-size: 400% 400%;
  padding: 1.5rem 1rem;
  border-radius: 0.75rem;
}
.wave-header h1 {
  color: white;
  font-size: 2.2rem;
  margin-bottom: 0.5rem;
}
.wave-header p {
  color: #f0f0f0;
  font-size: 1.1rem;
}
</style>

<div class='wave-header'>
  <h1>⌨️ CodeEyes Assistant</h1>
  <p>💡 SonarQube 룰 기반 코드 품질 분석 및 수정 코드 제안을 도와드립니다.</p>
</div>
""", unsafe_allow_html=True)


st.divider()


# --- 세션 초기화 ---
if "messages" not in st.session_state:
    st.session_state.followup_response = ""
    st.session_state.messages = [{"role": "system", "content": load_system_prompt()}]

# --- 입력 UI ---
with st.expander("🛠 분석 정보 입력", expanded=True):
    col_lang, col_rule = st.columns([1, 3])
    with col_lang:
        language = st.selectbox("언어", ["Python", "Java", "JavaScript"], index=0)
        language = language.lower()  # RAG 처리 및 룰 필터링 일관성 확보

    with col_rule:
        rule_list = load_rule_list(language)
        rule_titles = [f"{r['title']}" for r in rule_list]
        selected_rule = st.selectbox("룰 선택 (입력 시 자동 검색)", options=rule_titles)

    rulename = selected_rule.split(" - ")[0] if selected_rule else ""

    st.markdown("**🔤 분석할 코드를 입력하세요:**") 
    dark_mode = st.toggle("🌙 에디터 다크 모드", value=True)
    theme = "dracula" if dark_mode else "github"
    code = st_ace(language=language.lower(), theme=theme, height=300, key="ace_input", auto_update=True)

    analyze_button = st.button("🚀 Analyze", use_container_width=True, disabled=not (rulename.strip() and code and code.strip()))

    if analyze_button:
        st.session_state.followup_response = ""
        with st.spinner("분석 중입니다..."):
            st.session_state.messages.append({
                "role": "user",
                "content": f"language: {language}\nrulename: {rulename}\ncode:\n{code}"
            })
            result_markdown = get_openai_response(
                messages=st.session_state.messages,
                use_rag=True,
                search_endpoint=search_endpoint,
                search_api_key=search_api_key,
                index_name=index_name
            )
            parsed_result = parse_markdown_response(result_markdown)

            if parsed_result.get("parse_error"):
                st.markdown("#### [디버그] 응답 원문")
                st.code(result_markdown)
                st.error(f"❌ 분석 결과를 정상적으로 이해하지 못했습니다. 원인: {parsed_result['parse_error']}")
                st.stop()

            st.session_state.analysis_result = parsed_result

# --- 분석 결과 ---
if "analysis_result" in st.session_state:
    # st.write("💬 요청 메시지:", st.session_state.messages)
    st.markdown("---")
    st.markdown("#### 📊 분석 결과")

    result = st.session_state.analysis_result
    st.subheader(f"🧾 룰명: {result['rule']}")
    st.markdown(f"**등급**: {result['severity']}")
    st.markdown(f"**범주**: {result['category']}")
    st.markdown(f"**설명**: {result['description'] if result['description'] else 'N/A'}")

    relevance = result.get("relevance", "").strip()
    if relevance not in ["높음", "중간", "낮음", "없음"]:
        st.warning(f"⚠️ 알 수 없는 관련성 값: `{relevance}` (GPT 응답 이상 가능성)")
    elif relevance in ["없음", "낮음"]:
        st.warning("⚠️ 선택한 룰과 입력한 코드 사이의 관련성이 낮거나 없습니다. GPT의 응답이 부정확할 수 있습니다.")

    if result['verdict']:
        st.markdown(f"**🧠 정탐/오탐 여부**: :{'green' if result['verdict']=='정탐' else 'orange'}[`{result['verdict']}`]")
        if result['verdict'] == "정탐" and result.get("difficulty"):
            st.markdown(f"**🛠️ 수정 난이도**: `{result['difficulty']}`")
            st.info("⚠️ 생성된 코드는 AI가 제안한 예시이며, 개발자의 검토 후 반영되어야 합니다.")
    
    # 수정 코드 및 다운로드 버튼
    if result['verdict'] == "정탐":
        if result['fix_code']:
            st.markdown("### ✅ 수정 코드 제안")
            st.code(result['fix_code'], language=language.lower())
        else:
            st.warning("✅ 정탐으로 판단되었지만, 수정 코드가 제공되지 않았습니다. 추가 질문으로 요청해 보세요.")

        btn_dl, btn_regen = st.columns(2)
        with btn_dl:
            st.download_button("📥 분석 결과 다운로드", json.dumps(result, ensure_ascii=False, indent=2), file_name="analysis_result.json", mime="application/json", use_container_width=True)
        with btn_regen:
            if st.button("🔄 수정 코드 다시 만들기", use_container_width=True):
                with st.spinner("수정 코드 다시 생성 중..."):
                    regenerated = regenerate_fix_code(st.session_state.messages)
                    st.session_state.regenerated_code = regenerated

    if "regenerated_code" in st.session_state:
        st.markdown("### 🔄 새로 생성된 수정 코드")
        st.code(st.session_state.regenerated_code, language=language.lower())

    st.markdown("---")
    followup = st.text_area("💬 추가 질문을 입력하세요", key="followup_input")

    if followup:
        st.markdown("---")
        st.markdown("#### 💬 추가 질문에 대한 AI의 답변")

        # 시스템 프롬프트를 다시 포함한 메시지 재구성
        followup_messages = [
            {"role": "system", "content": system_prompt},  # 다시 주입
        ] + st.session_state.messages[1:]  # 기존 user-assistant 기록 유지

        followup_messages.append({"role": "user", "content": followup + "\n\n이 질문에 대한 답변만 해주고, 다른 분석 결과 항목은 반복하지 않아도 됩니다."})

        with st.spinner("답변 생성 중..."):
            followup_response = get_openai_response(followup_messages, use_rag=True)

        st.session_state.messages.append({"role": "assistant", "content": followup_response})
        st.session_state.followup_response = followup_response

    if "followup_response" in st.session_state:
        answer = st.session_state.followup_response
        if "The requested information is not found" in answer:
            answer = "**죄송합니다. 이 AI는 SonarQube 기반 코드 품질 점검과 룰 설명에만 응답합니다.**"
        st.markdown("**AI 답변:**")
        st.markdown(answer)
