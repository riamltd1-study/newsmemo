import streamlit as st
import os
import json
import re
import pandas as pd
from google import genai
from google.genai import types

# --- 1. 설정 및 API 키 확인 ---
def get_api_key():
    """GitHub Codespaces Secrets에서 API 키를 가져옵니다."""
    key = os.environ.get("GEMINI_API_KEY")
    return key

def init_page():
    """페이지 초기 설정"""
    st.set_page_config(page_title="Gemini 뉴스 검색기", page_icon="📰", layout="wide")
    st.title("📰 Gemini 뉴스 검색기")
    st.markdown("---")

# --- 2. Gemini AI를 이용한 뉴스 검색 및 요약 함수 ---
def search_news_with_gemini(keyword, api_key):
    """
    Gemini의 구글 검색 도구를 사용하여 실시간 뉴스를 검색하고 
    JSON 형식으로 결과를 받아옵니다.
    """
    try:
        # 새로운 SDK 방식으로 클라이언트 생성
        client = genai.Client(api_key=api_key)
        
        # AI에게 전달할 구체적인 요청서(프롬프트)
        prompt = f"""
        주제: "{keyword}"에 대한 가장 최신 뉴스 기사 5건을 검색해서 알려줘.
        
        각 기사에 대해 다음 정보를 반드시 포함해줘:
        1. 제목
        2. 언론사
        3. 발행일 (YYYY-MM-DD 형식)
        4. 원본 URL
        5. 3~4문장의 한국어 요약
        
        응답은 반드시 아래와 같은 순수한 JSON 배열 형식으로만 대답해. 
        다른 설명이나 인사말, ```json 같은 코드 표시도 절대 붙이지 마.
        
        [
          {{
            "title": "기사제목",
            "media": "언론사명",
            "date": "2024-05-20",
            "url": "https://...",
            "summary": "기사 요약 내용..."
          }},
          ...
        ]
        """

        # 구글 검색 도구 활성화 (Search Grounding)
        search_tool = types.Tool(google_search=types.GoogleSearchRetrieval())
        
        response = client.models.generate_content(
            model="gemini-2.0-flash", # 최신 고성능 모델 사용
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[search_tool],
                response_mime_type="application/json" # 응답을 JSON으로 강제
            )
        )

        # 결과 텍스트 추출 및 정제
        raw_text = response.text
        # 혹시 모를 코드 블록(```json) 제거
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        
        return json.loads(clean_json)

    except Exception as e:
        st.error(f"❌ AI 작업 중 오류가 발생했습니다: {str(e)}")
        return None

# --- 3. 화면에 기사 카드 그리기 ---
def render_article_card(idx, article):
    """기사 한 건을 예쁜 카드 형태로 화면에 표시합니다."""
    with st.container():
        st.markdown(f"""
        <div style="
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #ddd; 
            margin-bottom: 20px;
            background-color: #f9f9f9;
        ">
            <h3 style="margin-top:0;"><a href="{article['url']}" target="_blank" style="text-decoration:none; color:#1E88E5;">{article['title']}</a></h3>
            <p style="color:#666; font-size: 0.9rem;">🏢 {article['media']} | 📅 {article['date']}</p>
            <p style="font-size: 1rem; line-height: 1.6;">{article['summary']}</p>
        </div>
        """, unsafe_allow_html=True)

# --- 4. 메인 실행 로직 ---
def main():
    init_page()
    api_key = get_api_key()

    # API 키가 없는 경우 안내문 표시
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY를 찾을 수 없습니다!")
        st.info("""
        **[해결 방법]**
        1. GitHub Codespaces 설정에서 'Secrets'를 등록해야 합니다.
        2. Name: `GEMINI_API_KEY`
        3. Value: AI Studio에서 발급받은 키
        4. 등록 후 Codespace를 'Rebuild' 해주세요.
        """)
        st.stop()

    # 세션 상태 초기화 (검색 결과 유지용)
    if "search_results" not in st.session_state:
        st.session_state.search_results = None

    # 검색창 영역
    col1, col2 = st.columns([4, 1])
    with col1:
        keyword = st.text_input("검색어를 입력하세요", placeholder="예: 양자 컴퓨터 최신 기술")
    with col2:
        search_button = st.button("뉴스 검색 🔍", use_container_width=True)

    if search_button and keyword:
        with st.spinner("AI가 구글에서 뉴스를 찾아 요약 중입니다..."):
            results = search_news_with_gemini(keyword, api_key)
            if results:
                st.session_state.search_results = results

    # 결과 표시 영역
    if st.session_state.search_results:
        st.subheader(f"'{keyword}' 검색 결과")
        
        for idx, article in enumerate(st.session_state.search_results):
            render_article_card(idx, article)
        
        # CSV 다운로드 버튼
        df = pd.DataFrame(st.session_state.search_results)
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        
        st.download_button(
            label="📊 결과 CSV 다운로드",
            data=csv,
            file_name=f"news_{keyword}.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()