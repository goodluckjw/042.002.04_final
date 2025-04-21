import streamlit as st
import sys
import os
import importlib.util

# 🔐 현재 작업 디렉토리 기준으로 law_processor.py 절대경로 import
base_dir = os.path.abspath(os.path.join(os.getcwd(), "processing"))
processor_path = os.path.join(base_dir, "law_processor.py")
spec = importlib.util.spec_from_file_location("law_processor", processor_path)
law_processor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(law_processor)

# 🔁 함수 직접 연결
run_search_logic = law_processor.run_search_logic
run_amendment_logic = law_processor.run_amendment_logic

st.set_page_config(layout="wide")
st.title("📘 부칙개정 도우미")

with st.expander("ℹ️ 읽어주세요"):
    st.markdown("이 앱은 검색 기능과 개정문 자동생성 기능을 제공합니다.\n- 검색: 법령에서 특정 단어가 포함된 조문을 검색합니다.\n- 개정문 생성: 특정 단어를 다른 단어로 대체하는 부칙 개정문을 생성합니다.")

st.header("🔍 검색 기능")
search_query = st.text_input("검색어 입력", key="search_query")
search_col = st.columns([1, 1])
with search_col[0]:
    do_search = st.button("검색 시작")
with search_col[1]:
    do_reset = st.button("초기화")

search_unit = st.radio("다중검색 단위선택 (미선택시 법률 단위 필터링)", ["법률", "조", "항", "호", "목"], horizontal=True, index=0)
st.caption("※ 예: '행정 & 기본' → 선택된 단위 내에 두 검색어가 모두 포함될 때 결과 출력")

if do_search and search_query:
    with st.spinner("🔍 검색 중..."):
        search_result = run_search_logic(search_query, search_unit)
        st.success("검색 완료")
        for law_name, sections in search_result.items():
            with st.expander(f"📄 {law_name}"):
                for html in sections:
                    st.markdown(html, unsafe_allow_html=True)

st.header("✏️ 타법개정문 생성")
amend_cols = st.columns([4, 4, 1])
with amend_cols[0]:
    find_word = st.text_input("찾을 단어", key="find_word")
with amend_cols[1]:
    replace_word = st.text_input("바꿀 단어", key="replace_word")
with amend_cols[2]:
    do_amend = st.button("개정문 생성")

if do_amend and find_word and replace_word:
    with st.spinner("🛠 개정문 생성 중..."):
        amend_result = run_amendment_logic(find_word, replace_word)
        st.success("생성 완료")
        for amend in amend_result:
            st.markdown(f"➤ {amend}")