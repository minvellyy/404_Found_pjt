import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- [1] 모든 CSV 데이터 로드 (v1과 동일) ---
@st.cache_data
def load_all_data():
    try:
        base_path = 'table/'
        df_perf = pd.read_csv(base_path + 'campaign_performance.csv')
        df_camp = pd.read_csv(base_path + 'campaign_master.csv')
        df_prod = pd.read_csv(base_path + 'product_master.csv')
        df_inf = pd.read_csv(base_path + 'influencer_master.csv')
        return df_perf, df_camp, df_prod, df_inf
    except FileNotFoundError as e:
        st.error(f"😭 데이터 파일({e.filename})을 찾을 수 없습니다! 'table' 폴더에 모든 CSV가 있는지 확인해주세요.")
        return None, None, None, None
    except Exception as e:
        st.error(f"파일 로드 중 오류 발생: {e}")
        return None, None, None, None

df_perf, df_camp, df_prod, df_inf = load_all_data()

if any(df is None for df in [df_perf, df_camp, df_prod, df_inf]):
    st.stop()

st.title("📊 성과 분석 대시보드 (v2)")
st.markdown("캠페인별, 인플루언서별 성과를 다각도로 분석합니다.")

# --- [2] 데이터 전처리: JOIN 및 타입 변환 (v1보다 개선) ---
try:
    # 2-1. 모든 테이블 JOIN
    df_merged = pd.merge(df_perf, df_camp, on='campaign_id', how='left')
    df_merged = pd.merge(df_merged, df_prod, on='product_id', how='left')
    df_merged = pd.merge(df_merged, df_inf, on='inf_id', how='left', suffixes=('_perf', '_inf')) # 컬럼명 중복 방지

    # 2-2. [v2 신규] 날짜 데이터 변환 (시계열 분석용)
    # (errors='coerce'는 잘못된 날짜 형식이면 NaT(결측치)로 만듦)
    df_merged['post_date'] = pd.to_datetime(df_merged['post_date'], errors='coerce')

except Exception as e:
    st.error(f"데이터 병합(JOIN) 또는 날짜 변환 중 오류 발생: {e}")
    st.stop()


# --- [3] 대시보드 필터 (v1과 동일) ---
st.sidebar.header("📊 성과 필터")

# 3-1. 캠페인 필터
df_camp['campaign_display_name'] = df_camp['campaign_name'] + " (" + df_camp['campaign_id'] + ")"
all_campaigns = df_camp['campaign_display_name'].unique()
selected_campaigns = st.sidebar.multiselect(
    '캠페인 선택',
    options=all_campaigns,
    default=list(all_campaigns)
)
selected_campaign_ids = df_camp[df_camp['campaign_display_name'].isin(selected_campaigns)]['campaign_id'].tolist()

# 3-2. 제품 필터
all_products = df_prod['product_name'].dropna().unique()
selected_products = st.sidebar.multiselect(
    '제품 선택',
    options=all_products,
    default=list(all_products)
)

# 3-3. [v2 신규] 날짜 범위 필터
st.sidebar.divider()
min_date = df_merged['post_date'].dropna().min()
max_date = df_merged['post_date'].dropna().max()

if pd.isna(min_date) or pd.isna(max_date):
    st.sidebar.warning("날짜 데이터가 없어 날짜 필터를 사용할 수 없습니다.")
    selected_date_range = (None, None)
else:
    selected_date_range = st.sidebar.date_input(
        "포스팅 날짜 범위 선택",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# --- [4] 필터링된 데이터로 분석 ---
if not selected_campaign_ids or not selected_products:
    st.warning("사이드바에서 하나 이상의 캠페인과 제품을 선택해주세요.")
    st.stop()

# 메인 데이터 필터링
filtered_data = df_merged[
    (df_merged['campaign_id'].isin(selected_campaign_ids)) &
    (df_merged['product_name'].isin(selected_products))
]

# [v2 신규] 날짜 필터링 적용
if selected_date_range[0] and selected_date_range[1]:
    start_date = pd.to_datetime(selected_date_range[0])
    end_date = pd.to_datetime(selected_date_range[1])
    filtered_data = filtered_data[
        (filtered_data['post_date'] >= start_date) &
        (filtered_data['post_date'] <= end_date)
    ]

if filtered_data.empty:
    st.warning("선택한 조건에 해당하는 성과 데이터가 없습니다.")
    st.stop()

st.divider()

# --- [5] 핵심 성과 지표 (KPI) 표시 (v2 대폭 수정) ---
st.subheader(f"📈 총괄 성과 요약 (선택된 필터 기준)")

# 5-1. KPI 계산
total_revenue = filtered_data['revenue'].sum()
total_cost = filtered_data['actual_cost'].sum()
total_clicks = filtered_data['clicks'].sum()
total_conversions = filtered_data['conversions'].sum()
total_impressions = filtered_data['impressions'].sum() # [v2 신규]

# 5-2. 0으로 나누기 방지
roas = (total_revenue / total_cost) if total_cost > 0 else 0
cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
cpa = (total_cost / total_conversions) if total_conversions > 0 else 0
ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0 # [v2 신규]
cvr = (total_conversions / total_clicks) if total_clicks > 0 else 0      # [v2 신규]
aov = (total_revenue / total_conversions) if total_conversions > 0 else 0 # [v2 신규]

# 5-3. 3x2 그리드로 KPI 표시
kpi_cols = st.columns(3)
kpi_cols[0].metric("💰 총 매출 (Revenue)", f"{total_revenue:,.0f} 원")
kpi_cols[1].metric("💸 총 비용 (Cost)", f"{total_cost:,.0f} 원")
kpi_cols[2].metric("📈 총 ROAS", f"{roas:.2%}")

kpi_cols = st.columns(3)
kpi_cols[0].metric("🖱️ 클릭 대비 전환율 (CVR)", f"{cvr:.2%}")
kpi_cols[1].metric("🎯 노출 대비 클릭률 (CTR)", f"{ctr:.2%}")
kpi_cols[2].metric("🛍️ 평균 객단가 (AOV)", f"{aov:,.0f} 원")

kpi_cols = st.columns(3)
kpi_cols[0].metric("🫰 클릭당 비용 (CPC)", f"{cpc:,.1f} 원")
kpi_cols[1].metric("🫰 전환당 비용 (CPA)", f"{cpa:,.1f} 원")


# --- [6] 시각화 (Charts) (v2 대폭 수정) ---
st.divider()
st.subheader("📊 상세 분석 차트")

# 6-1. [v2 신규] 날짜별 매출 추이 (Line Chart)
st.markdown("#### 1. 날짜별 매출 추이")
time_series_data = filtered_data.groupby(filtered_data['post_date'].dt.date)['revenue'].sum().reset_index()
time_series_data = time_series_data.rename(columns={'post_date': '날짜', 'revenue': '매출액'})

if time_series_data.empty:
    st.info("시계열 차트를 그릴 날짜 데이터가 부족합니다.")
else:
    fig_time = px.line(
        time_series_data, 
        x='날짜', 
        y='매출액', 
        title='날짜별 매출 발생 추이',
        markers=True,
        template='plotly_white'
    )
    st.plotly_chart(fig_time, use_container_width=True)


# 6-2. [v2 신규] 비용-매출 효율성 분석 (Scatter Plot)
st.markdown("#### 2. 인플루언서 효율성 분석 (비용 vs 매출)")
inf_perf_agg = filtered_data.groupby('inf_name').agg(
    total_cost=('actual_cost', 'sum'),
    total_revenue=('revenue', 'sum'),
    platform=('platform', 'first') # 플랫폼별로 색상 구분
).reset_index()

fig_scatter = px.scatter(
    inf_perf_agg,
    x='total_cost',
    y='total_revenue',
    color='platform', # 플랫폼별로 색상 구분
    hover_name='inf_name', # 마우스 올리면 이름 표시
    title='인플루언서별 비용 vs 매출 (효율성 사분면)',
    labels={'total_cost': '총 집행 비용 (원)', 'total_revenue': '총 발생 매출 (원)'},
    template='plotly_white'
)
fig_scatter.add_hline(y=inf_perf_agg['total_revenue'].mean(), line_dash="dot", annotation_text="평균 매출")
fig_scatter.add_vline(x=inf_perf_agg['total_cost'].mean(), line_dash="dot", annotation_text="평균 비용")
st.plotly_chart(fig_scatter, use_container_width=True)


# 6-3. [v2 신규] 플랫폼별 / 카테고리별 성과 (Bar/Pie Charts)
st.markdown("#### 3. 플랫폼 및 카테고리별 성과 분석")
col1, col2 = st.columns(2)

with col1:
    # 플랫폼별 ROAS (Bar Chart)
    platform_perf = filtered_data.groupby('platform').agg(
        revenue=('revenue', 'sum'),
        actual_cost=('actual_cost', 'sum')
    ).reset_index()
    platform_perf['ROAS'] = (platform_perf['revenue'] / platform_perf['actual_cost']).fillna(0)
    platform_perf = platform_perf.sort_values(by='ROAS', ascending=False)
    
    fig_platform = px.bar(
        platform_perf,
        x='platform',
        y='ROAS',
        title='플랫폼별 ROAS',
        labels={'platform': '플랫폼', 'ROAS': 'ROAS'},
        template='plotly_white',
        color='platform'
    )
    fig_platform.update_yaxes(tickformat=".1%")
    st.plotly_chart(fig_platform, use_container_width=True)

with col2:
    # 제품 카테고리별 매출 비중 (Pie Chart)
    category_perf = filtered_data.groupby('category').agg(
        revenue=('revenue', 'sum')
    ).reset_index()
    
    fig_category = px.pie(
        category_perf,
        names='category',
        values='revenue',
        title='제품 카테고리별 매출 비중',
        hole=0.3, # 도넛 차트
        template='plotly_white'
    )
    st.plotly_chart(fig_category, use_container_width=True)


# 6-4. 기존 차트 (인플루언서/캠페인별 랭킹)
st.markdown("#### 4. 성과 랭킹 (Top 10)")
col1, col2 = st.columns(2)

with col1:
    # 인플루언서별 매출 랭킹 (v1과 동일)
    inf_performance = filtered_data.groupby('inf_name').agg(
        revenue=('revenue', 'sum'),
        actual_cost=('actual_cost', 'sum')
    ).reset_index()
    inf_performance = inf_performance.sort_values(by='revenue', ascending=False)

    fig_inf = px.bar(
        inf_performance.head(10),
        x='inf_name', y='revenue',
        title='인플루언서별 발생 매출 (Top 10)',
        labels={'inf_name': '인플루언서', 'revenue': '발생 매출'},
        template='plotly_white'
    )
    st.plotly_chart(fig_inf, use_container_width=True)

with col2:
    # 캠페인별 ROAS 랭킹 (v1과 동일)
    camp_performance = filtered_data.groupby('campaign_name').agg(
        revenue=('revenue', 'sum'),
        actual_cost=('actual_cost', 'sum')
    ).reset_index()
    camp_performance['ROAS'] = (camp_performance['revenue'] / camp_performance['actual_cost']).fillna(0)
    camp_performance = camp_performance.sort_values(by='ROAS', ascending=False)

    fig_camp = px.bar(
        camp_performance.head(10),
        x='campaign_name', y='ROAS',
        title='캠페인별 ROAS (Top 10)',
        labels={'campaign_name': '캠페인', 'ROAS': 'ROAS'},
        template='plotly_white'
    )
    fig_camp.update_yaxes(tickformat=".1%")
    st.plotly_chart(fig_camp, use_container_width=True)


# 6-5. 원본 데이터 보여주기 (옵션)
with st.expander("📂 필터링된 원본 데이터 보기 (Merged Data)"):
    st.dataframe(filtered_data, use_container_width=True)