import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# 0. 기본 설정
fake = Faker('ko_KR')
N_PROD = 10
N_INF = 200
N_CAMP = 20
N_PERF = 1000
YEAR_START = datetime(2025, 1, 1)
YEAR_END = datetime(2025, 12, 31)

print("현실적인 더미 데이터 v3.2 생성을 시작합니다 (날짜 함수 오류 수정)")

# --- 1. Product_Master (제품 마스터) ---
print(f"1. Product_Master ({N_PROD}개) 생성 중...")
# (이전과 동일)
product_categories = ['세럼', '미스트', '크림', '선케어', '클렌저']
products = {
    'product_id': [f'dalba-prod-{i:03d}' for i in range(1, N_PROD + 1)],
    'product_name': [f'달바 {random.choice(product_categories)} {i}호' for i in range(1, N_PROD + 1)],
    'category': [random.choice(product_categories) for _ in range(N_PROD)],
    'price': np.random.randint(25000, 80000, N_PROD) // 100 * 100
}
df_products = pd.DataFrame(products)
product_id_list = df_products['product_id'].tolist()


# --- 2. Influencer_Master (인플루언서 마스터) ---
print(f"2. Influencer_Master ({N_INF}명) 생성 중...")
# (이전과 동일)
platforms = ['Instagram', 'YouTube', 'TikTok']
inf_categories = ['뷰티', '라이프스타일', '패션', '여행', '푸드']
influencers = {
    'inf_id': [f'{fake.user_name()}_{i}' for i in range(1, N_INF + 1)],
    'inf_name': [fake.name() for _ in range(N_INF)],
    'platform': [random.choice(platforms) for _ in range(N_INF)],
    'follower_count': np.random.randint(5000, 1500000, N_INF),
    'avg_engagement_rate': np.round(np.random.uniform(0.005, 0.15, N_INF), 4),
    'main_category': [random.choice(inf_categories) for _ in range(N_INF)],
    'estimated_cost_per_post': np.random.randint(50000, 10000000, N_INF) // 10000 * 10000,
    'genai_brand_fit_score': np.round(np.random.uniform(1.0, 5.0, N_INF), 1),
    'genai_brand_fit_reason': [f"{random.choice(['고급진', '영한', '전문적인', '클린한'])} 이미지." for _ in range(N_INF)]
}
df_influencers = pd.DataFrame(influencers)
inf_id_list = df_influencers['inf_id'].tolist()


# --- 3. Campaign_Master (캠페인 마스터) ---
print(f"3. Campaign_Master ({N_CAMP}개) 생성 중...")
campaigns = []
for i in range(1, N_CAMP + 1):
    # [!] v3.2 수정: fake.date_object() -> fake.date_between()
    start_date = fake.date_between(start_date=YEAR_START, end_date=YEAR_END - timedelta(days=60))
    
    # [!] v3.2 수정: end_date 계산 시 start_date가 date 객체임을 명시
    end_date = min(start_date + timedelta(days=random.randint(30, 60)), YEAR_END.date())
    
    campaigns.append({
        'campaign_id': f'DALBA-CAMP-25{i:03d}',
        'campaign_name': f'2025년 {start_date.month}월 {random.choice(product_categories)} 프로모션',
        'product_id': random.choice(product_id_list),
        'start_date': start_date,
        'end_date': end_date,
        'total_budget': np.random.randint(50000000, 300000000, 1)[0] // 100000 * 100000
    })
df_campaigns = pd.DataFrame(campaigns)
campaign_date_list = df_campaigns[['campaign_id', 'start_date', 'end_date']].to_dict('records')


# --- 4. Campaign_Performance (캠페인 성과) ---
print(f"4. Campaign_Performance ({N_PERF}건) 생성 중...")
performances = []
for i in range(1, N_PERF + 1):
    
    chosen_campaign = random.choice(campaign_date_list)
    chosen_camp_id = chosen_campaign['campaign_id']
    camp_start = chosen_campaign['start_date']
    camp_end = chosen_campaign['end_date']
    
    chosen_inf_id = random.choice(inf_id_list)
    
    # [!] v3.2 수정: fake.date_object() -> fake.date_between()
    post_date = fake.date_between(start_date=camp_start, end_date=camp_end)
    
    # (성과 데이터 생성)
    actual_cost = np.random.randint(50000, 5000000, 1)[0]
    impressions = np.random.randint(actual_cost // 100, actual_cost // 10, 1)[0]
    clicks = int(impressions * np.random.uniform(0.01, 0.05))
    conversions = int(clicks * np.random.uniform(0.005, 0.03))
    revenue = conversions * np.random.randint(30000, 60000, 1)[0]
    
    performances.append({
        'perf_id': i, 'campaign_id': chosen_camp_id, 'inf_id': chosen_inf_id,
        'post_date': post_date, 'post_url': f'https://instagram.com/p/{fake.password(length=11)}',
        'actual_cost': actual_cost, 'impressions': impressions, 'clicks': clicks,
        'conversions': conversions, 'revenue': revenue,
        'genai_comment_summary': f"긍정 {random.randint(70, 95)}%."
    })
df_performance = pd.DataFrame(performances)

print("\n--- 모든 데이터 생성 완료! (v3.2) ---")

# --- (필수) CSV 파일로 저장 (v3.1과 동일) ---
try:
    output_folder = 'table/'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"'{output_folder}' 폴더를 찾을 수 없어, 새로 생성했습니다.")

    df_products.to_csv(output_folder + 'product_master.csv', index=False)
    df_influencers.to_csv(output_folder + 'influencer_master.csv', index=False)
    df_campaigns.to_csv(output_folder + 'campaign_master.csv', index=False)
    df_performance.to_csv(output_folder + 'campaign_performance.csv', index=False)
    
    print(f"\n✅ CSV 파일 4개가 '{output_folder}' 폴더에 성공적으로 저장되었습니다.")
    print("이제 Streamlit 앱을 새로고침(R)하면 v3.2 데이터가 반영됩니다!")

except PermissionError:
    print(f"\n[오류] '{output_folder}' 폴더에 CSV를 쓸 '권한(Permission)'이 없습니다.")
    print("폴더가 읽기 전용이 아닌지, 혹은 다른 프로그램(엑셀)이 파일을 열고 있지 않은지 확인해주세요.")
except Exception as e:
    print(f"\n[오류] CSV 저장 중 알 수 없는 오류 발생: {e}")

print("\n--- 샘플 데이터 확인 (각 5줄) ---")
# (이전과 동일)
print(f"\n[Product_Master 샘플 (총 {N_PROD}개)]")
print(df_products.head())
print(f"\n[Campaign_Master 샘플 (총 {N_CAMP}개, 2025년도)]")
print(df_campaigns.head())
print(f"\n[Campaign_Performance 샘플 (총 {N_PERF}건, 캠페인 기간 내)]")
print(df_performance.head())