import streamlit as st
from PIL import Image

# 페이지 설정
st.set_page_config(
    page_title="Kovue",
    page_icon="🎯",
    layout="centered"
)

# 세션 스테이트 초기화 (페이지 관리를 위해)
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# --- 1. 홈 페이지 함수 ---
def home_page():
    # 여백 추가
    st.markdown("<br>" * 3, unsafe_allow_html=True)

    # 로고를 중앙에 배치
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # 로고 이미지 로드 (Home.py와 같은 폴더에 'kovue_logo.jpg'가 있다고 가정)
        try:
            # 절대 경로 대신 상대 경로 'kovue_logo.jpg' 사용
            logo = Image.open("kovue_logo.jpg") 
            st.image(logo, use_container_width=True)
        except FileNotFoundError:
            # 로고 파일이 없을 경우 텍스트로 표시
            st.markdown(
                "<h1 style='text-align: center; font-size: 72px; color: #4CAF50;'>Kovue</h1>",
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"로고 로딩 오류: {e}")
            st.markdown(
                "<h1 style='text-align: center; font-size: 72px; color: #4CAF50;'>Kovue</h1>",
                unsafe_allow_html=True
            )

    # 여백 추가
    st.markdown("<br>" * 2, unsafe_allow_html=True)

    # 버튼을 중앙에 배치
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        # '시작하기' 버튼 클릭 시 세션 상태를 'select'로 변경
        if st.button("시작하기", type="primary", use_container_width=True):
            st.session_state.page = 'select' # 'next' 대신 'select'로 변경
            st.rerun() # 페이지를 새로고침하여 next_page() 함수를 호출

# --- 2. 페이지 선택 함수 (수정된 '다음 화면') ---
def select_page():
    st.title("🎯 Home ")
    st.write("아래 버튼을 클릭하여 원하는 분석 페이지로 이동하세요.")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 페이지 이동 버튼 (pages 폴더의 파일들)
    # 파일명에 오타가 있다면(예: Globlal, Gobal) 실제 파일명과 정확히 일치해야 합니다.
    
    if st.button("🧪 1. Ingredients & Insight", use_container_width=True):
        try:
            st.switch_page("pages/1_Ingredients& Insight.py")
        except Exception as e:
            st.error(f"페이지 이동 오류: {e}")
            st.info("'pages/1_Ingredients& Insight.py' 파일 경로와 이름을 확인하세요.")

    if st.button("📊 2. Globlal_Trend(reddit)", use_container_width=True):
        try:
            # 사용자가 올린 이미지의 파일명을 기준으로 작성 (오타가 있다면 수정 필요)
            st.switch_page("pages/2_Globlal_Trend(reddit).py")
        except Exception as e:
            st.error(f"페이지 이동 오류: {e}")
            st.info("'pages/2_Globlal_Trend(reddit).py' 파일 경로와 이름을 확인하세요.")

    if st.button("📈 3. Gobal_Tremd(youtube)", use_container_width=True):
        try:
            # 사용자가 올린 이미지의 파일명을 기준으로 작성 (오타가 있다면 수정 필요)
            st.switch_page("pages/3_Gobal_Tremd(youtube).py")
        except Exception as e:
            st.error(f"페이지 이동 오류: {e}")
            st.info("'pages/3_Gobal_Tremd(youtube).py' 파일 경로와 이름을 확인하세요.")
            
    if st.button("🌱 4. Seeding", use_container_width=True):
        try:
            st.switch_page("pages/4_Seeding.py")
        except Exception as e:
            st.error(f"페이지 이동 오류: {e}")
            st.info("'pages/4_Seeding.py' 파일 경로와 이름을 확인하세요.")
            
    if st.button("📉 5. Performance", use_container_width=True):
        try:
            st.switch_page("pages/5_Performance.py")
        except Exception as e:
            st.error(f"페이지 이동 오류: {e}")
            st.info("'pages/5_Performance.py' 파일 경로와 이름을 확인하세요.")

    st.markdown("---")
    
    # '홈으로 돌아가기' 버튼
    if st.button("← 홈으로 돌아가기"):
        st.session_state.page = 'home'
        st.rerun()

# --- 3. 페이지 라우팅 ---
# 세션 상태에 따라 표시할 함수를 결정
if st.session_state.page == 'home':
    home_page()
elif st.session_state.page == 'select':
    select_page()
else:
    home_page() # 기본값