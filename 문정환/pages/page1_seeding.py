import streamlit as st
import pandas as pd
import numpy as np

# --- [1] 데이터 로드 (CSV 파일 연동!) ---
@st.cache_data # 데이터를 캐시에 저장해서 매번 로드하지 않게 함
def load_influencer_data():
    file_path = 'table/influencer_master.csv'
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        # [!] 에러 메시지도 새 경로로 업데이트
        st.error(f"😭 '{file_path}' 파일을 찾을 수 없습니다! 'table' 폴더 안에 파일이 있는지 확인해주세요.")
        # ...
    except Exception as e:
        st.error(f"파일 로드 중 오류 발생: {e}")
        return pd.DataFrame()

# 데이터 로드
df = load_influencer_data()

# 데이터 로드에 실패하면 실행 중단
if df.empty:
    st.stop()

st.title("🎯 Seeding 평가 (인플루언서 선정)")
st.markdown("데이터에 기반해 캠페인에 적합한 인플루언서를 검색하고 선정합니다.")

# --- [2] 필터 (사이드바) ---
st.sidebar.header("🔍 Seeding 필터")

# 2-1. 카테고리 필터
# (결측치가 있을 경우를 대비해 .dropna() 추가)
categories = df['main_category'].dropna().unique() 
selected_categories = st.sidebar.multiselect(
    '메인 카테고리',
    options=categories,
    default=list(categories)  # 기본값은 전체 선택
)

# 2-2. 팔로워 수 필터
min_follower, max_follower = int(df['follower_count'].min()), int(df['follower_count'].max())
selected_follower_range = st.sidebar.slider(
    '팔로워 수',
    min_value=min_follower,
    max_value=max_follower,
    value=(min_follower, max_follower)
)

# 2-3. GenAI 적합도 점수 필터
min_score, max_score = float(df['genai_brand_fit_score'].min()), float(df['genai_brand_fit_score'].max())
selected_score_range = st.sidebar.slider(
    'GenAI 브랜드 적합도 점수 (1~5점)',
    min_value=min_score,
    max_value=max_score,
    value=(min_score, max_score),
    step=0.1
)

# --- [3] 필터링된 결과 표시 ---

# 3-1. 필터링 로직 (결측치에 안전하게)
if not selected_categories: # 만약 아무 카테고리도 선택 안 하면 빈 리스트 방지
    selected_categories = list(categories)

filtered_df = df[
    (df['main_category'].isin(selected_categories)) &
    (df['follower_count'] >= selected_follower_range[0]) &
    (df['follower_count'] <= selected_follower_range[1]) &
    (df['genai_brand_fit_score'] >= selected_score_range[0]) &
    (df['genai_brand_fit_score'] <= selected_score_range[1])
]

# 3-2. 결과 테이블 출력
st.subheader(f"📊 검색 결과: {len(filtered_df)}명 (총 {len(df)}명 중)")
st.dataframe(
    filtered_df,
    use_container_width=True,
    column_config={
        "inf_name": "이름", # 컬럼명 한글로
        "platform": "플랫폼",
        "follower_count": st.column_config.NumberColumn("팔로워", format="%d명"),
        "estimated_cost_per_post": st.column_config.NumberColumn("예상 비용", format="₩%d"),
        "avg_engagement_rate": st.column_config.ProgressColumn(
            "평균 참여율",
            format="%.2f%%",
            min_value=0, max_value=max(0.01, float(df['avg_engagement_rate'].max())) # 0으로 나누기 방지
        ),
        "genai_brand_fit_score": st.column_config.ProgressColumn(
            "GenAI 적합도",
            format="%.1f점",
            min_value=1, max_value=5
        ),
        "main_category": "카테고리",
        "genai_brand_fit_reason": "GenAI 분석 이유"
    },
    # 보여줄 컬럼 순서 지정 (inf_id는 숨김)
    column_order=["inf_name", "platform", "main_category", "follower_count", "avg_engagement_rate", "estimated_cost_per_post", "genai_brand_fit_score", "genai_brand_fit_reason"]
)