import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(page_title="실시간 정보 수집 대시보드", layout="wide")

st.title("🌐 실시간 정보 한눈에 모아보기 (무료 크롤러 버전)")
st.caption("구글 AI API 키 없이 포털의 실시간 정보를 안전하게 수집하여 구성합니다.")

# 2. 사용자 입력창
user_query = st.text_input("실시간으로 모아보고 싶은 키워드를 입력하세요:", placeholder="예: 인공지능 트렌드, 주식 시장, 맛집 탐방")

# 네이버 뉴스 크롤링 함수 정의 (우회 기능 강화)
def fetch_naver_news(keyword):
    clean_keyword = keyword.strip()
    url = "https://search.naver.com/search.naver"
    
    params = {
        "where": "news",
        "query": clean_keyword,
        "sm": "tab_opt",
        "sort": "1"  # 최신순
    }
    
    # [우회 포인트 1] 일반 웹 브라우저(크롬)의 필수 데이터 요청 규격을 복제하여 봇 차단을 방지합니다.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # [우회 포인트 2] 네이버 개편에 대비하여 여러 종류의 기사 상자(태그) 형태를 동시에 탐색합니다.
        news_items = soup.select("ul.list_news > li.bx")
        if not news_items:
            news_items = soup.select(".news_wrap") # 대체 태그 검색 1
        if not news_items:
            news_items = soup.select("li[id^='sp_nws']") # 대체 태그 검색 2
            
        results = []
        for item in news_items[:6]: # 최신 뉴스 6개 추출
            try:
                # 1. 제목 및 링크 추출 (다양한 클래스 대응)
                title_area = item.select_one("a.news_tit") or item.select_one(".api_txt_lines.news_tit")
                if not title_area:
                    continue
                title = title_area.text.strip()
                link = title_area["href"]
                
                # 2. 언론사 추출
                press_area = item.select_one("a.info.press") or item.select_one(".press")
                press = press_area.text.replace("언론사 선정", "").strip() if press_area else "포털 종합"
                
                # 3. 본문 미리보기 추출
                dsc_area = item.select_one("div.news_dsc") or item.select_one(".news_dsc") or item.select_one(".dsc_wrap")
                summary = dsc_area.text.strip() if dsc_area else "본문 요약 및 미리보기를 제공하지 않는 기사입니다."
                
                results.append({
                    "언론사": press,
                    "제목": title,
                    "요약 내용": summary,
                    "링크": link
                })
            except Exception:
                continue
        return results
        
    except Exception as e:
        st.sidebar.error(f"연결 에러 세부 정보: {e}")
        return []

# 3. 검색 버튼 클릭 시 시각화
if st.button("정보 수집 시작") and user_query:
    if not user_query.strip():
        st.warning("⚠️ 유효한 검색어를 입력해 주세요.")
    else:
        with st.spinner(f"'{user_query.strip()}'에 대한 최신 정보를 안전하게 수집하는 중입니다..."):
            # 요청 간 약간의 지연(0.5초)을 주어 차단 가능성을 낮춥니다.
            time.sleep(0.5)
            news_data = fetch_naver_news(user_query)
            
            if not news_data:
                st.error("데이터를 수집하지 못했습니다. 포털 서버의 응답이 일시적으로 제한되었거나 검색 조건이 맞지 않습니다. 잠시 후 다시 검색해 주세요.")
                # 디버깅을 위해 빈 화면 대신 도움말 표시
                st.info("💡 팁: 검색어를 '인공지능'이나 '날씨' 같이 명확한 단어로 바꾸어 다시 시도해 보세요.")
            else:
                df = pd.DataFrame(news_data)
                
                # 화면 분할 레이아웃
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 데이터 구조화 그리드")
                    st.dataframe(df[["언론사", "제목", "요약 내용"]], use_container_width=True)
                    
                with col2:
                    st.subheader("📰 한눈에 보는 뉴스 피드")
                    for item in news_data:
                        with st.expander(f"[{item['언론사']}] {item['제목']}"):
                            st.write(item['요약 내용'])
                            st.markdown(f"[🔗 원문 기사 읽기]({item['링크']})")
                            
                st.success("🎯 실시간 정보 수집이 완료되었습니다!")
