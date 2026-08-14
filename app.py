import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. 페이지 기본 설정 (와이드 모드)
st.set_page_config(page_title="실시간 정보 수집 대시보드", layout="wide")

st.title("🌐 실시간 정보 한눈에 모아보기 (무료 크롤러 버전)")
st.caption("구글 AI API 키 없이, 네이버 포털의 실시간 정보를 긁어와 대시보드를 구성합니다.")

# 2. 사용자 입력창 (API 키 요구 없음)
user_query = st.text_input("실시간으로 모아보고 싶은 키워드를 입력하세요:", placeholder="예: 인공지능 트렌드, 주식 시장, 맛집 탐방")

# 네이버 뉴스 크롤링 함수 정의
def fetch_naver_news(keyword):
    # 네이버 뉴스 검색 URL (최신순 정렬)
    url = f"https://naver.com{keyword}&sm=tab_opt&sort=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
        
    soup = BeautifulSoup(response.text, "html.parser")
    news_items = soup.select("ul.list_news > li.bx")
    
    results = []
    for item in news_items[:6]: # 최신 뉴스 6개 추출
        try:
            # 제목 및 링크 추출
            title_area = item.select_one("a.news_tit")
            title = title_area.text
            link = title_area["href"]
            
            # 언론사 추출
            press_area = item.select_one("a.info.press")
            press = press_area.text.replace("언론사 선정", "").strip() if press_area else "알 수 없음"
            
            # 본문 미리보기 추출
            dsc_area = item.select_one("div.news_dsc")
            summary = dsc_area.text if dsc_area else "본문 요약 없음"
            
            results.append({
                "언론사": press,
                "제목": title,
                "요약 내용": summary,
                "링크": link
            })
        except Exception:
            continue
    return results

# 3. 검색 버튼 클릭 시 시각화
if st.button("정보 수집 시작") and user_query:
    with st.spinner(f"'{user_query}'에 대한 최신 정보를 수집하는 중입니다..."):
        news_data = fetch_naver_news(user_query)
        
        if not news_data:
            st.error("데이터를 가져오지 못했습니다. 키워드를 다시 확인해 주세요.")
        else:
            # 데이터를 판다스 데이터프레임으로 변환
            df = pd.DataFrame(news_data)
            
            # 화면을 2개 구역(좌/우)으로 분할
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📊 데이터 구조화 그리드")
                # 링크를 제외한 표 형태 출력
                st.dataframe(df[["언론사", "제목", "요약 내용"]], use_container_width=True)
                
            with col2:
                st.subheader("📰 한눈에 보는 뉴스 피드")
                # 카드가 위아래로 쌓이도록 반복문 출력
                for item in news_data:
                    with st.expander(f"[{item['언론사']}] {item['제목']}"):
                        st.write(item['요약 내용'])
                        st.markdown(f"[🔗 원문 기사 읽기]({item['링크']})")
                        
            st.success("🎯 실시간 정보 수집이 완료되었습니다!")
