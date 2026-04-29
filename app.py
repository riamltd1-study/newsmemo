import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- 화면 설정 ---
st.set_page_config(page_title="나만의 뉴스 비서", layout="wide")
st.title("📰 AI 뉴스 요약기")
st.write("키워드만 입력하면 최신 뉴스를 찾아 요약해 드립니다!")

# --- 사이드바: API 키 입력 ---
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Gemini API 키를 입력하세요", type="password")
    st.info("AI Studio에서 발급받은 키를 넣어주세요.")

# --- 뉴스 검색 및 요약 함수 ---
def get_news_and_summary(keyword, api_key):
    # 1. Gemini AI 설정
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    results = []
    # 2. 뉴스 검색 (DuckDuckGo 사용)
    with DDGS() as ddgs:
        search_results = list(ddgs.news(keyword, max_results=5))
    
    status_text = st.empty()
    
    for i, news in enumerate(search_results):
        status_text.write(f"{i+1}번째 기사 분석 중... 🕒")
        url = news['url']
        title = news['title']
        
        try:
            # 기사 본문 긁어오기 (간단한 버전)
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            # 본문이 있을 법한 p 태그들을 합침
            content = " ".join([p.text for p in soup.find_all('p')[:5]]) 
            
            # 3. Gemini에게 요약 요청
            prompt = f"다음 뉴스 기사 내용을 3줄 이내의 한글로 핵심만 요약해줘: {content}"
            summary_response = model.generate_content(prompt)
            summary = summary_response.text
        except:
            summary = "요약 실패 (기사 접근 제한 혹은 내용 부족)"
            
        results.append({"제목": title, "URL": url, "요약내용": summary})
    
    status_text.empty()
    return results

# --- 메인 화면 입력부 ---
keyword = st.text_input("궁금한 뉴스 키워드를 입력하세요 (예: 인공지능, 전기차)")

if st.button("뉴스 가져오기"):
    if not api_key:
        st.error("API 키를 먼저 입력해 주세요!")
    elif not keyword:
        st.warning("키워드를 입력해 주세요!")
    else:
        with st.spinner("뉴스를 찾고 요약하는 중입니다... 잠시만 기다려주세요!"):
            data = get_news_and_summary(keyword, api_key)
            df = pd.DataFrame(data)
            
            # 결과 테이블 표시
            st.table(df)
            
            # 4. CSV 다운로드 버튼
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="결과를 CSV 파일로 저장하기",
                data=csv,
                file_name=f"{keyword}_뉴스요약.csv",
                mime="text/csv"
            )
            st.success("완료되었습니다! 아래 버튼을 눌러 파일을 저장하세요.")