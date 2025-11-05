import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import json
from openai import OpenAI 
from fpdf import FPDF 
import io 

# --- (V23) CSV/PDF 헬퍼 함수들 (변경 없음) ---
@st.cache_data
def to_csv(df):
    """데이터프레임을 CSV (UTF-8) 바이트로 변환"""
    return df.to_csv(index=False).encode('utf-8-sig') 

class PDF(FPDF):
    """PDF 보고서 생성을 위한 FPDF 클래스"""
    def header(self):
        self.set_font('MalgunGothic', 'B', 15)
        self.cell(0, 10, 'AI 인플루언서 마케팅 보고서 (DRAFT)', 0, 1, 'C')
        self.ln(10)
    def chapter_title(self, title):
        self.set_font('MalgunGothic', 'B', 12)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(2)
    def chapter_body(self, body, font_size=10):
        self.set_font('MalgunGothic', '', font_size)
        self.multi_cell(0, 6, body)
        self.ln()
    def add_korean_fonts(self):
        try:
            self.add_font('MalgunGothic', '', 'MALGUN.TTF') 
            self.add_font('MalgunGothic', 'B', 'MALGUNBD.TTF')
        except Exception:
            self.set_font('Arial', 'B', 10) 

@st.cache_data
def generate_pdf_report(df_seeding_list, insight_report_content, brand_fit_result, persona_context, filter_report_content, analysis_report_content, influencer_name):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.add_korean_fonts()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.chapter_title(f"인플루언서 마케팅 최종 분석 보고서 - {influencer_name}")
    pdf.chapter_title("1. AI 통합 분석 및 최종 제언")
    pdf.chapter_body(insight_report_content)
    pdf.ln(5)
    pdf.chapter_title("2. 브랜드 핏 평가 (Soft Fit)")
    if brand_fit_result:
        fit_score = brand_fit_result.get('brand_fit_score', 'N/A')
        fit_reason = brand_fit_result.get('reason', '분석 결과 없음')
        pdf.chapter_body(f"평가 점수: {fit_score} / 100점")
        pdf.chapter_body(f"평가 근거: {fit_reason}")
    else:
        pdf.chapter_body("브랜드 핏 분석이 수행되지 않았습니다. (4.2 섹션 참조)")
    pdf.ln(5)
    pdf.chapter_title("3. 캠페인 목표 및 분석 맥락")
    pdf.chapter_body(f"캠페인 페르소나: {persona_context[:150]}...")
    pdf.chapter_body(f"1차 참고 보고서: {filter_report_content[:150]}...")
    pdf.chapter_body(f"추가 참고 보고서: {analysis_report_content[:150]}...")
    pdf.ln(5)
    pdf.chapter_title(f"4. 첨부 파일: 최종 시딩 후보군 목록 ({len(df_seeding_list)}명)")
    pdf.chapter_body(f"최종 시딩 후보군 목록 파일은 CSV로 별도 첨부됩니다.", font_size=8)
    return bytes(pdf.output(dest='S')) 


# --- (V23) 글로벌 상수 및 DB 기준 정의 (변경 없음) ---
ALL_COUNTRIES = ['USA', 'Germany', 'Russia', 'France', 'UK', 'Japan', 'South Korea']
ALL_CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Berlin', 'Hamburg', 'Munich', 'Cologne', 'Frankfurt', 'Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg', 'Paris', 'London', 'Tokyo', 'Seoul']
ALL_INTERESTS = sorted([
    'Skincare', 'K-Beauty', 'Makeup', 'Fashion', 'Lifestyle', 'Gaming', 'Tech',
    'Fitness', 'Wellness', 'Food', 'Travel', 'Music', 'K-Pop', 'Tiktok', 'Dance',
    'Vegan', 'Eco-friendly', 'Luxury', 'Minimalism', 'Art', 'Photography' 
])
ALL_AGES = ['under_18', '18-24', '25-34', '35-44', '45-54', '55_plus'] 
ALL_GENDERS = ['Female', 'Male', 'Mixed'] 

ALL_PLATFORMS = ['Any', 'Instagram', 'Tiktok', 'YouTube']
ALL_GENDERS_OPTIONS = ['Any', 'Female (80% 이상)', 'Male (80% 이상)', 'Mixed (50/50)']


# --- (V23) 가상 데이터 생성 함수 (Top N 컬럼 추가) ---
def create_mock_data(filename="influencers_v23.csv"):
    """
    10,000개의 '비율 기반' 가상 인플루언서 데이터를 생성 (Top N 컬럼 추가)
    """
    st.toast("비율 기반 가상 데이터 파일을 생성합니다... (10,000건)")
    num_rows = 10000
    
    def get_random_dist(options):
        dist = np.random.rand(len(options))
        dist /= dist.sum()
        return {option: round(val, 3) for option, val in zip(options, dist)}

    data = []
    for i in range(num_rows):
        row = {
            'influencer_name': f'influencer_{i}',
            'platform': np.random.choice(['Instagram', 'Tiktok', 'YouTube']),
            'followers': np.random.randint(10000, 1000000),
            'engagement_rate_pct': np.round(np.random.uniform(1.0, 10.0), 1),
            'fake_followers_pct': np.round(np.random.uniform(0.5, 30.0), 1)
        }
        
        # Age/Gender
        age_dist = get_random_dist(ALL_AGES)
        for age_range, val in age_dist.items():
            row[f'age_{age_range}'] = val
        gender_dist = get_random_dist(ALL_GENDERS)
        for gender, val in gender_dist.items():
            row[f'gender_{gender}'] = val
        
        # Country/City/Interests (JSON)
        country_dist_dict = get_random_dist(ALL_COUNTRIES)
        city_dist_dict = get_random_dist(ALL_CITIES)
        interest_dist_dict = get_random_dist(ALL_INTERESTS)
        
        row['audience_country_dist'] = json.dumps(country_dist_dict)
        row['audience_city_dist'] = json.dumps(city_dist_dict)
        row['audience_interest_dist'] = json.dumps(interest_dist_dict)
        
        # [V23] Top N 컬럼 추가 (UI 가독성용)
        row['top_country'] = max(country_dist_dict, key=country_dist_dict.get)
        row['top_city'] = max(city_dist_dict, key=city_dist_dict.get)
        row['top_age_range'] = max(age_dist, key=age_dist.get)
        row['top_gender'] = max(gender_dist, key=gender_dist.get)
        row['top_interest'] = max(interest_dist_dict, key=interest_dist_dict.get)

        # 비용 지표
        row['estimated_cpm'] = np.round(np.random.uniform(5.0, 50.0), 2)
        row['estimated_cpv'] = np.round(np.random.uniform(0.01, 0.50), 2)
        row['estimated_cpe'] = np.round(np.random.uniform(0.10, 2.00), 2)
        
        data.append(row)
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    st.toast(f"'{filename}' 생성 완료! (10,000건)")


# --- (V23) GPT-4 API 호출 함수 1: AI 통역 필터 추출용 (논리 오류 수정) ---
def query_openai_api_for_filters(report_text, model_name="gpt-4-turbo-2024-04-09"): 
    """
    OpenAI GPT-4 API를 호출하여 보고서 텍스트를 '추론'하고 '통역'하여 
    DB 필터링이 가능한 9가지 기준의 JSON을 추출합니다.
    """
    
    if "OPENAI_API_KEY" not in st.secrets:
        raise Exception("OpenAI API 키가 secrets.toml에 없습니다. (OPENAI_API_KEY)")
    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    valid_countries_str = ", ".join(ALL_COUNTRIES)
    valid_cities_str = ", ".join(ALL_CITIES)
    
    system_prompt = f"""
    You are an expert marketing data analyst. Your task is to analyze the user's report text (in Korean or English), 
    understand the intent, and translate it into a structured JSON object based on the 9 criteria below.

    CRUCIAL: You MUST translate the user's intent (e.g., '미국 서부', '서울') into the specific, 
    valid database values provided below. Do not output the user's original abstract words.
    DO NOT extract or infer 'Target Interests' or 'Hot Interests'. They are not part of your task.

    --- Valid Database Values (Your 'Answer Sheet') ---
    Valid Countries: [{valid_countries_str}]
    Valid Cities: [{valid_cities_str}]
    Valid Platforms: ["Instagram", "Tiktok", "YouTube"]
    --- End of Valid Values ---

    Rules for Translation and Extraction:
    1.  **Country/City:** Translate user intent into values from the Valid lists only.
    2.  **[V23 LOGIC FIX]** If a specific **Target City** (e.g., 'New York') is extracted, 
        DO NOT extract its parent **Target Country** (e.g., 'USA'). Only extract the most specific location.
        -   User: "미국 뉴욕" -> `Target City: ["New York"]` (O), `Target Country: []` (O)
        -   User: "미국" -> `Target City: []` (O), `Target Country: ["USA"]` (O)
        -   User: "미국 서부" -> `Target City: ["Los Angeles", "Phoenix"]` (O), `Target Country: []` (O)
    3.  **Age/Platform/Gender:** Extract string values (e.g., "35 to 43", "female", "30s").
    4.  **Followers/Engagement:** Extract numeric concepts (e.g., "50K", "5%").
    5.  **Empty Values:** If not found, use `""` for strings or `[]` for lists.
    6.  **Output:** You MUST respond ONLY with the valid JSON object.

    JSON Format:
    {{
      "Target Age": "", "Target Gender": "", "Target Country": [], "Target City": [], 
      "Target Platform": "", "Min Followers (K)": "", "Max Followers (K)": "",     
      "Min Engagement (%)": "", "Max Fake Followers (%)": ""
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": report_text}],
            response_format={"type": "json_object"}, 
            temperature=0.0
        )
        
        ai_response_string = response.choices[0].message.content
        filters = json.loads(ai_response_string)
        
        print("--- AI Raw JSON Start (V23 - Filters) ---")
        print(ai_response_string)
        print("--- AI Raw JSON End (V23 - Filters) ---")
        
        return filters

    except Exception as e:
        raise Exception(f"OpenAI (Filter) API 호출 오류: {e}")

# --- (V21) GPT-4 API 호출 함수 2: Soft Brand Fit (변경 없음) ---
def query_openai_api_for_brand_fit(brand_keywords_str, audience_interest_dist_json, persona_input, brand_guideline_input, model_name="gpt-4-turbo-2024-04-09"):
    if "OPENAI_API_KEY" not in st.secrets:
        raise Exception("OpenAI API 키가 secrets.toml에 없습니다. (OPENAI_API_KEY)")
    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    system_prompt = f"""
    You are an expert brand marketer. Your task is to evaluate the semantic relevance (Soft Fit) between a brand's core keywords and an influencer's audience interests, **given our brand persona and the audience's full interest distribution.**
    
    - Brand Persona: The target customer profile.
    - Brand Guidelines: The brand's tone & manner.
    - Brand Core Keywords: These define the brand's identity.
    - Influencer Audience Interests (Distribution): A JSON showing the percentage breakdown of all audience interests.
    
    Your goal is to score this fit from 0 to 100 based on how well the audience's interests align with the brand's identity, **the target persona, and the brand guidelines.**
    
    You MUST respond ONLY with a JSON object in the following format:
    {{
      "brand_fit_score": <score_int>,
      "reason": "<one_sentence_reason_in_Korean_analyzing_the_distribution>"
    }}
    """
    
    user_prompt = f"""
    - **Brand Persona Context:** "{persona_input}"
    - **Brand Guideline Context:** "{brand_guideline_input}"
    - Brand Core Keywords: [{brand_keywords_str}]
    - **Influencer Audience Interest Distribution (JSON):** {audience_interest_dist_json}
    
    Please analyze the semantic relevance **considering ALL context (Persona, Guidelines)**, and provide the Brand Fit score and reason in the specified JSON format.
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        ai_response_string = response.choices[0].message.content
        fit_result = json.loads(ai_response_string)
        return fit_result

    except Exception as e:
        raise Exception(f"OpenAI (Brand Fit) API 호출 오류: {e}")


# --- (V16) GPT-4 API 호출 함수 3: 통합 인사이트 리포트용 (변경 없음) ---
def query_openai_api_for_insight(cpm, cpv, cpe, influencer_name, brand_fit_result, 
                                 persona_input, filter_report_content, analysis_report_content, 
                                 benchmark_cpm=15.0, benchmark_cpe=1.0): 
    
    if "OPENAI_API_KEY" not in st.secrets:
        raise Exception("OpenAI API 키가 secrets.toml에 없습니다. (OPENAI_API_KEY)")
    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    model_name = "gpt-4-turbo-2024-04-09" 

    cpm_insight = "저렴합니다." if cpm <= benchmark_cpm else "다소 비쌉니다."
    cpe_insight = "매우 효율적입니다." if cpe <= benchmark_cpe else "다소 비효율적입니다."

    prompt = f"""
    --- Full Context ---
    **1. Our Campaign Goal (Persona):** "{persona_input}"
    **2. External Market Situation (Report File from Step 1):** "{filter_report_content}"
    **3. Additional Data (Report File from Step 3):** "{analysis_report_content}"
    --- End of Context ---

    --- Influencer Data ---
    Influencer: {influencer_name}
    Estimated CPM: ${cpm:.2f} (Market Benchmark: ${benchmark_cpm:.2f})
    Estimated CPV: ${cpv:.2f}
    Estimated CPE: ${cpe:.2f} (Market Benchmark: ${benchmark_cpe:.2f})
    """
    
    if brand_fit_result:
        prompt += f"""
        Brand Fit Score: {brand_fit_result['brand_fit_score']}/100
        Brand Fit Reason: {brand_fit_result['reason']}
        """
    else:
        prompt += "Brand Fit Score: (Not Assessed)\n"
        
    prompt += """
    --- Your Task ---
    Based on **all the context provided above (Goal, Market Reports 1 & 2, and Data)**, write a comprehensive 'Strategic Insight Report' in Korean for a marketing executive.
    
    1.  Start with a clear **Recommendation:** (e.g., "계약 강력 추천.", "전략적 재고 필요.").
    2.  Analyze the **Cost Efficiency (CPM/CPE)**.
    3.  Analyze the **Brand Fit** score (if provided) in the context of our **Campaign Goal (Persona)**.
    4.  Incorporate insights from **both report files** (if they are not 'N/A').
    5.  Provide a final, concise justification for your recommendation.
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400 
        )
        
        insight_report = response.choices[0].message.content
        return insight_report

    except Exception as e:
        raise Exception(f"OpenAI (Insight) API 호출 오류: {e}")

# --- (V19) GPT-4 API 호출 함수 4: 계약서 초안 생성용 (변경 없음) ---
def query_openai_api_for_contract(influencer_name, proposed_cost, campaign_period, content_guideline, model_name="gpt-4-turbo-2024-04-09"):
    if "OPENAI_API_KEY" not in st.secrets:
        raise Exception("OpenAI API 키가 secrets.toml에 없습니다. (OPENAI_API_KEY)")
    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    system_prompt = f"""
    You are an AI legal assistant specializing in marketing contracts. 
    Your task is to draft a clear and professional influencer marketing contract (MOU) in **Korean** suitable for a PDF printout.
    The draft must be based **only** on the 4 variables provided by the user.
    Start with the title: '인플루언서 마케팅 캠페인 계약서 (초안)'.
    Use clear section headers (e.g., '제 1조 계약 당사자', '제 2조 계약 개요').
    """
    
    user_prompt = f"""
    Draft a professional contract (MOU) in **Korean** using the following details:

    1.  **Influencer (을):** {influencer_name}
    2.  **Brand (갑):** d'Alba
    3.  **Proposed Cost (지급 비용):** {proposed_cost}
    4.  **Campaign Period (계약 기간):** {campaign_period}
    5.  **Content Guidelines (주요 콘텐츠 가이드라인):**
        {content_guideline}
    
    Please structure the output clearly.
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.3, 
            max_tokens=1000 
        )
        
        contract_draft = response.choices[0].message.content
        return contract_draft

    except Exception as e:
        raise Exception(f"OpenAI (Contract) API 호출 오류: {e}")


# --- (V22) '번역' 헬퍼 함수들 (변경 없음) ---
def translate_age_to_cols(ai_age_str):
    if not ai_age_str: return []
    if isinstance(ai_age_str, list): ai_age_str = str(ai_age_str[0]) if ai_age_str else ""
    if not ai_age_str: return []
    
    target_cols = []
    age_lower = str(ai_age_str).lower()
    
    match = re.search(r'(\d+)\s*(-|to)\s*(\d+)', age_lower)
    if match:
        min_age = int(match.group(1)); max_age = int(match.group(3))
        if min_age <= 17: target_cols.append('age_under_18')
        if min_age <= 24 and max_age >= 18: target_cols.append('age_18-24')
        if min_age <= 34 and max_age >= 25: target_cols.append('age_25-34')
        if min_age <= 44 and max_age >= 35: target_cols.append('age_35-44')
        if min_age <= 54 and max_age >= 45: target_cols.append('age_45-54')
        if max_age >= 55: target_cols.append('age_55_plus')
        
    if "30대" in age_lower or "30s" in age_lower: target_cols.extend(['age_25-34', 'age_35-44'])
    if "20대" in age_lower or "20s" in age_lower: target_cols.extend(['age_18-24', 'age_25-34'])
    if "40대" in age_lower or "40s" in age_lower: target_cols.extend(['age_35-44', 'age_45-54'])
        
    return list(set(target_cols)) 


def translate_gender_to_cols(ai_gender_str):
    if not ai_gender_str: return []
    if isinstance(ai_gender_str, list): ai_gender_str = str(ai_gender_str[0]) if ai_gender_str else ""
    if not ai_gender_str: return []

    gender_lower = str(ai_gender_str).lower()
    if "female" in gender_lower or "여성" in gender_lower or "여자" in gender_lower or "women" in gender_lower: return ['gender_Female']
    elif "male" in gender_lower or "남성" in gender_lower or "남자" in gender_lower or "men" in gender_lower: return ['gender_Male']
    elif "mixed" in gender_lower or "혼합" in gender_lower: return ['gender_Mixed']
    return []

def translate_platform_to_val(ai_platform_str):
    if not ai_platform_str: return 'Any'
    if isinstance(ai_platform_str, list): ai_platform_str = ai_platform_str[0] if ai_platform_str else ""
    if not ai_platform_str: return 'Any'
    
    platform_lower = str(ai_platform_str).lower()
    if "instagram" in platform_lower: return 'Instagram'
    elif "tiktok" in platform_lower or "틱톡" in platform_lower: return 'Tiktok'
    elif "youtube" in platform_lower or "유튜브" in platform_lower: return 'YouTube'
    return 'Any'
    

def to_float(value, default=0.0):
    if value is None: return default
    if isinstance(value, list): value = value[0] if value else None
    if value is None: return default
    try:
        clean_value = str(value).lower().replace('%', '').replace('k', '').strip() 
        return float(clean_value)
    except (ValueError, TypeError):
        return default


# --- (V21) AI 응답 '번역' 콜백 함수 (비율 기반 필터링 로직) ---
def apply_filters_from_report():
    """파일과 텍스트를 취합, AI 호출, 결과를 '번역'하여 session_state에 저장합니다."""
    
    combined_text = ""
    if st.session_state.persona_input:
        combined_text += "## Campaign Persona ##\n" + st.session_state.persona_input + "\n"
    
    if st.session_state.filter_report_file is not None:
        combined_text += "## Market Report File Content ##\n" + st.session_state.filter_report_file.getvalue().decode("utf-8") + "\n"
        
    if st.session_state.other_requirements_input:
        combined_text += "## Other Requirements ##\n" + st.session_state.other_requirements_input + "\n"

    if not combined_text.strip():
        st.session_state.filter_error_message = "1. 타겟 고객 프로필 또는 2. 기타 요구사항 중 하나 이상을 입력해야 합니다."
        return

    st.session_state.brand_fit_result = None
    
    try:
        model_name = "gpt-4-turbo-2024-04-09" 
        with st.spinner(f"OpenAI GPT-4 ({model_name})가 보고서를 분석 및 통역 중입니다..."):
            filters = query_openai_api_for_filters(combined_text, model_name) 
        
        if not filters:
            st.session_state.filter_error_message = "AI가 보고서에서 유효한 필터 키워드를 추출하지 못했습니다."
            return

        st.session_state.target_countries = filters.get("Target Country")
        st.session_state.target_cities = filters.get("Target City")
        st.session_state.target_age_cols = translate_age_to_cols(filters.get("Target Age")) 
        st.session_state.target_gender_cols = translate_gender_to_cols(filters.get("Target Gender"))
        st.session_state.platform = translate_platform_to_val(filters.get('Target Platform'))
        st.session_state.min_followers = to_float(filters.get('Min Followers (K)')) * 1000
        st.session_state.max_followers = to_float(filters.get('Max Followers (K)'), 1000.0) * 1000 
        st.session_state.min_engagement = to_float(filters.get("Min Engagement (%)"), 0.0)
        st.session_state.max_fake_followers = to_float(filters.get("Max Fake Followers (%)"), 30.0)
        
        st.session_state.filter_applied_success = True
        st.session_state.filter_result_json = filters 
        
    except Exception as e:
        st.session_state.filter_error_message = f"AI 처리 오류 발생: {e}"


# --- (V23) 메인 앱 실행 함수 (UX/UI 개선) ---
def run_app(df):
    
    st.title("d'Alba AI Seeding Platform (V23 - UX/UI 완성)")

    # --- (V23) 사이드바 필터 (도움말 추가) ---
    st.sidebar.header("Seeding Criteria (AI 자동 입력 및 수동 조작)")
    
    st.sidebar.multiselect("Target Country (국가)", ALL_COUNTRIES, key='target_countries')
    st.sidebar.multiselect("Target City (도시)", ALL_CITIES, key='target_cities')
    
    age_cols = [f'age_{age}' for age in ALL_AGES] 
    st.sidebar.multiselect("Target Age (연령)", age_cols, key='target_age_cols')
    
    gender_cols = [f'gender_{g}' for g in ALL_GENDERS]
    st.sidebar.multiselect("Target Gender (성별)", gender_cols, key='target_gender_cols')
    
    st.sidebar.radio("Target Platform", ALL_PLATFORMS, key='platform') 
    st.sidebar.number_input("Min Followers (K)", min_value=0, step=1000, key='min_followers') 
    st.sidebar.number_input("Max Followers (K)", min_value=0, step=1000, key='max_followers')
    
    # [V23] 도움말(help) 추가
    st.sidebar.slider("Min Engagement (%)", 0.0, 10.0, key='min_engagement', step=0.1,
                      help="**최소 참여율 (품질 보증):** 이 비율이 높을수록 '진성 팬'이 많음을 의미합니다. (권장: 2.5% 이상)")
    st.sidebar.slider("Max Fake Followers (%)", 0.0, 30.0, key='max_fake_followers', step=0.5,
                      help="**최대 가짜 팔로워 (위험 회피):** 이 비율이 높을수록 '부실 자산(봇)'이 많음을 의미합니다. (권장: 15% 이하)")

    st.sidebar.slider("최소 타겟 일치 비율 (%)", 0, 100, 30, key='target_threshold_pct',
                      help="AI 필터링 시, 이 비율(%) 이상을 차지하는 오디언스만 검색합니다. (기본값 30%)")


    # --- (V22) 1. AI 캠페인 기획 및 필터링 ---
    st.subheader("1. AI 캠페인 기획 및 필터링")
    
    st.text_area("1.1 타겟 고객 프로필 (페르소나)", key='persona_input', 
                 placeholder="[우리가 누구에게 팔 것인가?] \n예: 미국 동부에 거주하는 30대 여성, 럭셔리 스킨케어에 관심이 많음...")
    
    st.text_area("1.2 기타 요구사항 (AI 필터링용)", key='other_requirements_input', 
                 placeholder="[기술적인 필터 조건은?] \n예: 틱톡커만, 최소 팔로워 50K, 최대 300K, 참여율 5% 이상")

    st.file_uploader("1.3 참고 보고서 파일 (선택 사항)", type="txt", key='filter_report_file') 
    
    st.button("AI 보고서로 자동 필터링 적용", 
              on_click=apply_filters_from_report, 
              type="primary", 
              use_container_width=True)
    
    if 'filter_applied_success' in st.session_state and st.session_state.filter_applied_success:
        st.success("AI가 보고서를 분석하여 사이드바의 Criteria를 자동 적용했습니다! (수정 가능)")
        with st.expander("AI가 추출한 원본 JSON 보기 (디버깅용)"):
            st.json(st.session_state.get('filter_result_json', {}))
        st.session_state.filter_applied_success = False 
            
    if 'filter_error_message' in st.session_state and st.session_state.filter_error_message:
        st.error(st.session_state.filter_error_message)
        st.session_state.filter_error_message = None 

    st.divider()

    # --- (V23) 2. 필터링된 인플루언서 목록 (UX/UI 개선) ---
    st.subheader("2. 필터링된 인플루언서 목록 ('Like' 하려면 ✅ Select)")

    filtered_df = df.copy()
    
    threshold = st.session_state.target_threshold_pct / 100.0
    
    # [필터링 로직]
    if st.session_state.target_age_cols:
        filtered_df = filtered_df[filtered_df[st.session_state.target_age_cols].sum(axis=1) >= threshold]
    if st.session_state.target_gender_cols:
        filtered_df = filtered_df[filtered_df[st.session_state.target_gender_cols].sum(axis=1) >= threshold]
    if st.session_state.target_countries:
        def check_dist(dist_dict, keys, threshold):
            total = sum(dist_dict.get(key, 0) for key in keys)
            return total >= threshold
            
        filtered_df = filtered_df[st.session_state.country_dist_loaded.apply(
            check_dist, args=(st.session_state.target_countries, threshold)
        )]
    if st.session_state.target_cities and not filtered_df.empty:
        filtered_df = filtered_df[st.session_state.city_dist_loaded.loc[filtered_df.index].apply(
            check_dist, args=(st.session_state.target_cities, threshold)
        )]
    if st.session_state.platform != 'Any':
        filtered_df = filtered_df[filtered_df['platform'] == st.session_state.platform]
    filtered_df = filtered_df[
        (filtered_df['followers'] >= st.session_state.min_followers) &
        (filtered_df['followers'] <= st.session_state.max_followers) 
    ]
    filtered_df = filtered_df[
        (filtered_df['engagement_rate_pct'] >= st.session_state.min_engagement) &
        (filtered_df['fake_followers_pct'] <= st.session_state.max_fake_followers)
    ]

    st.info(f"총 {len(df)}명의 인플루언서 중 {len(filtered_df)}명이 필터링되었습니다. (기준 비율: {st.session_state.target_threshold_pct}%)")

    if not filtered_df.empty:
        # [V23] 'Like All' / 'Unlike All' 버튼
        col1_all, col2_all = st.columns(2)
        if col1_all.button("✅ Like All (전체 선택)", use_container_width=True):
            st.session_state.liked_influencers.update(filtered_df['influencer_name'])
            st.rerun() 
        if col2_all.button("❌ Unlike All (전체 해제)", use_container_width=True):
            st.session_state.liked_influencers.difference_update(filtered_df['influencer_name'])
            st.rerun() 

        filtered_df['✅ Select'] = filtered_df['influencer_name'].apply(
            lambda x: x in st.session_state.liked_influencers
        )
        
        # [V23] UI 정리: top_ 컬럼만 노출
        cols_to_display = ['✅ Select', 'influencer_name', 'platform', 'followers', 'engagement_rate_pct', 
                           'fake_followers_pct', 'top_country', 'top_city', 'top_age_range', 'top_gender', 'top_interest']
        
        edited_df = st.data_editor(
            filtered_df[cols_to_display],
            key='selection_editor',
            disabled=[col for col in cols_to_display if col != '✅ Select']
        )
        
        # [V23.1] 무한 루프 수정 (Rerun 로직 간소화)
        current_view_names = set(filtered_df['influencer_name'])
        edited_likes = set(edited_df[edited_df['✅ Select'] == True]['influencer_name'])
        
        unliked_in_view = current_view_names - edited_likes
        st.session_state.liked_influencers.difference_update(unliked_in_view)
        st.session_state.liked_influencers.update(edited_likes)
        
    else:
        st.dataframe(filtered_df) 

    st.divider()

    # --- (V23) 3, 4, 5단계 통합 탭 구조 ---
    liked_names_list = list(st.session_state.liked_influencers)
    
    if not liked_names_list:
        st.warning("먼저 '2. 필터링된 인플루언서 목록'에서 '✅ Select'로 분석할 인플루언서를 1명 이상 선택해주세요.")
        return

    # [V23] 탭 밖(상단)으로 Selectbox 이동
    selected_influencer_name = st.selectbox(
        "분석할 'Like' 인플루언서를 선택하세요:", 
        options=liked_names_list,
        key="analysis_selector_master",
        help="여기서 선택하면 3, 4, 5번 탭의 내용이 모두 연동됩니다."
    )

    if not selected_influencer_name:
        st.info("분석할 인플루언서를 선택해주세요.")
        return
        
    influencer_data = df[df['influencer_name'] == selected_influencer_name].iloc[0]

    tab_efficiency, tab_analysis, tab_contract = st.tabs([
        "💰 3. 상세 분석 & 비용 확인",
        "💎 4. AI 심층 분석 & 보고",
        "✍️ 5. 최종 계약 및 결재"
    ])


    # =========================================================================
    # 💰 탭 3. 상세 분석 및 비용 확인
    # =========================================================================
    with tab_efficiency:
        st.subheader(f"3.1 {selected_influencer_name} (기본 정보)")

        cpm = influencer_data['estimated_cpm']
        cpv = influencer_data['estimated_cpv']
        cpe = influencer_data['estimated_cpe']
        
        st.markdown("#### 비용 지표 (Estimated)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Estimated CPM", f"${cpm:.2f}")
        col2.metric("Estimated CPV", f"${cpv:.2f}")
        col3.metric("Estimated CPE", f"${cpe:.2f}")
        
        st.markdown("---")

        # [V23] 상세 분포 (시각화)
        st.markdown("#### 📈 오디언스 상세 분포 (Raw Data)")
        
        with st.expander("클릭하여 모든 오디언스 비율 차트 확인"):
            
            # [V23] Age/Gender (Bar Chart)
            st.markdown("##### 🎂 연령 및 성별 분포 (Top 5)")
            age_data = {col.split('_')[1]: influencer_data[col] for col in df.columns if col.startswith('age_')}
            gender_data = {col.split('_')[1]: influencer_data[col] for col in df.columns if col.startswith('gender_')}
            
            df_age = pd.DataFrame.from_dict(age_data, orient='index', columns=['Percentage']).nlargest(5, 'Percentage')
            df_gender = pd.DataFrame.from_dict(gender_data, orient='index', columns=['Percentage']).nlargest(5, 'Percentage')
            
            st.bar_chart(df_age)
            st.bar_chart(df_gender)

            st.markdown("##### 🌍 국가 및 도시 분포 (Top 5)")
            country_dist = json.loads(influencer_data['audience_country_dist'])
            city_dist = json.loads(influencer_data['audience_city_dist'])
            
            df_country = pd.DataFrame.from_dict(country_dist, orient='index', columns=['Percentage']).nlargest(5, 'Percentage')
            df_city = pd.DataFrame.from_dict(city_dist, orient='index', columns=['Percentage']).nlargest(5, 'Percentage')

            st.bar_chart(df_country)
            st.bar_chart(df_city)

            st.markdown("##### 🎨 관심사 분포 (Top 5)")
            interest_dist = json.loads(influencer_data['audience_interest_dist'])
            df_interest = pd.DataFrame.from_dict(interest_dist, orient='index', columns=['Percentage']).nlargest(5, 'Percentage')
            st.bar_chart(df_interest)
            
        # [V23] Unlike 버튼
        st.markdown("---")
        def unlike_selected_influencer_3():
            st.session_state.liked_influencers.discard(selected_influencer_name)
            st.session_state.brand_fit_result = None
            st.rerun() 
        
        st.button(f"💔 **{selected_influencer_name}**을(를) 'Like' 목록에서 제거 (Unlike)", 
                  type="secondary", 
                  use_container_width=True,
                  on_click=unlike_selected_influencer_3,
                  key="unlike_button_3")

    # =========================================================================
    # 💎 탭 4. AI 심층 분석 & 보고
    # =========================================================================
    with tab_analysis:
        st.subheader(f"4.1 {selected_influencer_name} (AI 심층 분석)")
        
        persona_context = st.session_state.persona_input
        
        st.markdown("#### 4.2 분석 맥락 제공")
        if persona_context:
            st.info(f"**적용된 페르소나 (1단계 자동 로드):**\n\n {persona_context}")
        else:
            st.error("경고: '1.1 타겟 고객 프로필'이 비어있습니다. AI 분석 퀄리티가 낮아집니다.")

        st.multiselect(
            "A. 브랜드 핵심 키워드 (Soft Fit 평가용)", 
            options=ALL_INTERESTS, 
            key='brand_keywords_input_4',
            help="d'Alba 브랜드와 가장 연관성이 높다고 생각하는 키워드를 모두 선택하세요."
        )
        st.text_area("B. 브랜드 가이드라인 (선택 사항)", key='analysis_brand_guideline_input', 
                     placeholder="예: d'Alba는 '우아함', '이탈리아', '비건'을 중요시하는 럭셔리 톤앤매너를 가집니다.")
        
        st.file_uploader("C. 추가 참고 보고서 (내부 성과/경쟁사 자료)", type="txt", key='analysis_report_file') 

        brand_keywords_list = st.session_state.brand_keywords_input_4 
        if st.button("GPT-4로 브랜드 핏 평가", key="fit_button_4", use_container_width=False):
            if not brand_keywords_list: st.error("브랜드 핵심 키워드를 1개 이상 선택해주세요.")
            elif not persona_context: st.error("브랜드 핏을 평가하려면 '1.1 타겟 고객 프로필'을 먼저 입력해주세요.")
            else:
                with st.spinner("GPT-4가 적합도를 분석 중입니다..."):
                    try:
                        brand_keywords_str_for_api = ", ".join(brand_keywords_list) 
                        
                        fit_result = query_openai_api_for_brand_fit(
                            brand_keywords_str_for_api, 
                            influencer_data['audience_interest_dist'],
                            st.session_state.persona_input, 
                            st.session_state.analysis_brand_guideline_input 
                        )
                        st.session_state.brand_fit_result = (selected_influencer_name, fit_result)
                    except Exception as e:
                        st.error(f"브랜드 핏 분석 중 오류 발생: {e}")

        if st.session_state.brand_fit_result and st.session_state.brand_fit_result[0] == selected_influencer_name:
            fit_data = st.session_state.brand_fit_result[1]
            st.markdown("#### AI Brand Fit Score")
            st.metric("점수", f"{fit_data['brand_fit_score']} / 100")
            st.info(f"**AI 분석:** {fit_data['reason']}")
        else:
             st.warning("먼저 'GPT-4로 브랜드 핏 평가' 버튼을 눌러주세요.")

        st.markdown("---")
        
        st.markdown("#### 4.3 통합 인사이트 리포트")
        if st.button("GPT-4로 통합 인사이트 보고서 생성", type="primary", use_container_width=True):
            if not persona_context: 
                st.error("통합 보고서를 생성하려면 '1.1 타겟 고객 프로필'을 반드시 입력해야 합니다.")
            else:
                with st.spinner("GPT-4가 모든 맥락을 통합 분석 중입니다..."):
                    try:
                        benchmark_cpm = 15.0 
                        benchmark_cpe = 1.0
                        
                        brand_fit_result_data = st.session_state.brand_fit_result[1] if st.session_state.brand_fit_result and st.session_state.brand_fit_result[0] == selected_influencer_name else None
                        
                        filter_report_content = "N/A (1차 보고서 없음)"
                        if st.session_state.filter_report_file is not None:
                            filter_report_content = st.session_state.filter_report_file.getvalue().decode("utf-8")

                        analysis_report_content = "N/A (추가 보고서 없음)"
                        if st.session_state.analysis_report_file is not None:
                            analysis_report_content = st.session_state.analysis_report_file.getvalue().decode("utf-8")
                        
                        insight_report = query_openai_api_for_insight(
                            influencer_data['estimated_cpm'], influencer_data['estimated_cpv'], influencer_data['estimated_cpe'], selected_influencer_name,
                            brand_fit_result_data,
                            st.session_state.persona_input, 
                            filter_report_content, 
                            analysis_report_content, 
                            benchmark_cpm, benchmark_cpe
                        )
                        st.session_state.insight_report = (selected_influencer_name, insight_report) 
                        st.markdown("##### 💡 GPT-4 최종 분석 리포트")
                        st.success(insight_report)
                    except Exception as e:
                        st.error(f"인사이트 생성 중 오류 발생: {e}")

        st.markdown("---")
        def unlike_selected_influencer_4():
            st.session_state.liked_influencers.discard(selected_influencer_name)
            st.session_state.brand_fit_result = None
            st.rerun() 
        
        st.button(f"💔 **{selected_influencer_name}**을(를) 'Like' 목록에서 제거 (Unlike)", 
                  type="secondary", 
                  use_container_width=True,
                  on_click=unlike_selected_influencer_4,
                  key="unlike_button_4")


    # =========================================================================
    # ✍️ 탭 5. 최종 계약서 작성 및 보고서 다운로드
    # =========================================================================
    with tab_contract:
        st.subheader("5.1 팀장 결재 및 보고서 다운로드")
        
        seeding_list_df = df[df['influencer_name'].isin(liked_names_list)].copy()
        
        st.info(f"결재 요청할 최종 후보 인플루언서: {len(seeding_list_df)}명")

        st.markdown("#### A. 최종 시딩 목록 (CSV 파일)")
        
        available_cols = list(seeding_list_df.columns)
        default_cols = ['influencer_name', 'platform', 'followers', 'estimated_cpm', 'estimated_cpe', 'top_country', 'top_city']
        valid_default_cols = [col for col in default_cols if col in available_cols]
        
        cols_to_export = st.multiselect(
            "시딩 목록에서 내보낼 컬럼 선택", 
            options=available_cols, 
            default=valid_default_cols,
            key="export_multiselect" 
        )
        
        if not seeding_list_df.empty and cols_to_export:
            seeding_list_to_export = seeding_list_df[cols_to_export]
            
            st.download_button(
                label="✅ 최종 시딩 목록 CSV 다운로드",
                data=to_csv(seeding_list_to_export),
                file_name="team_report_seeding_list.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.markdown("---")
        
        st.markdown("#### B. AI 통합 분석 리포트 (PDF)")
        
        if st.session_state.insight_report:
            report_name, insight_content = st.session_state.insight_report
            
            if report_name == selected_influencer_name:
                filter_report_content = "N/A (1차 보고서 없음)"
                if st.session_state.filter_report_file is not None:
                    filter_report_content = st.session_state.filter_report_file.getvalue().decode("utf-8")
                analysis_report_content = "N/A (추가 보고서 없음)"
                if st.session_state.analysis_report_file is not None:
                    analysis_report_content = st.session_state.analysis_report_file.getvalue().decode("utf-8")
                
                pdf_bytes = generate_pdf_report(
                    seeding_list_df, insight_content, st.session_state.brand_fit_result[1] if st.session_state.brand_fit_result and st.session_state.brand_fit_result[0] == report_name else None,
                    st.session_state.persona_input, filter_report_content, analysis_report_content, report_name
                )
                
                st.download_button(
                    label=f"✅ 통합 리포트 PDF 다운로드 (for {report_name})",
                    data=pdf_bytes,
                    file_name=f"strategic_report_{report_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning(f"'4. AI 심층 분석' 탭에서 현재 선택된 '{selected_influencer_name}'의 리포트를 먼저 생성해주세요.")
        else:
            st.warning("먼저 '4. AI 심층 분석' 탭에서 '통합 인사이트 보고서'를 생성해야 합니다.")

        st.divider()

        st.subheader("5.2 인플루언서 계약서 초안 작성")
        
        st.info(f"계약 대상: **{selected_influencer_name}**")
        
        st.text_input("1. 제안 비용 (e.g., $500 USD)", key='proposed_cost')
        st.text_input("2. 캠페인 기간 (e.g., 2025-12-01 ~ 2025-12-15)", key='campaign_period')
        st.text_area("3. 콘텐츠 가이드라인", key='content_guideline', 
                         placeholder="예: 12월 10일까지 틱톡 영상 1건, 인스타그램 릴스 1건. 제품을 자연스럽게 노출하며...")

        if st.button("AI로 계약서 초안 생성하기", type="primary", use_container_width=True):
            cost = st.session_state.proposed_cost
            period = st.session_state.campaign_period
            guideline = st.session_state.content_guideline
            
            if not cost or not period or not guideline:
                st.error("비용, 기간, 가이드라인을 모두 입력해야 계약서를 생성할 수 있습니다.")
            else:
                with st.spinner("GPT-4가 d'Alba와 인플루언서 간의 계약서 초안을 작성 중입니다..."):
                    try:
                        contract_draft = query_openai_api_for_contract(
                            selected_influencer_name, cost, period, guideline
                        )
                        st.session_state.generated_contract = (selected_influencer_name, contract_draft)
                    except Exception as e:
                        st.error(f"계약서 생성 중 오류 발생: {e}")

        if st.session_state.generated_contract and st.session_state.generated_contract[0] == selected_influencer_name:
            st.markdown("---")
            st.markdown("##### 💡 AI가 생성한 계약서 초안")
            contract_name, contract_text = st.session_state.generated_contract
            st.text_area("Generated Contract", value=contract_text, height=400)
            
            pdf_contract = PDF(orientation='P', unit='mm', format='A4')
            pdf_contract.add_korean_fonts()
            pdf_contract.add_page()
            pdf_contract.chapter_body(contract_text)
            pdf_contract_bytes = bytes(pdf_contract.output(dest='S')) 

            st.download_button(
                label=f"✍️ {contract_name} 계약서 초안 PDF 다운로드",
                data=pdf_contract_bytes,
                file_name=f"contract_draft_{contract_name}.pdf",
                mime="application/pdf",
                use_container_width=True
            )


# --- (V23) 메인 실행 로직 ---
def main():
    st.set_page_config(layout="wide")

    tab1, tab2 = st.tabs(["🚀 시딩 플랫폼 (V23.1)", "⚙️ 가상 데이터 생성"])

    # --- 세션 상태 초기화 (V23) ---
    if 'target_countries' not in st.session_state: st.session_state.target_countries = []
    if 'target_cities' not in st.session_state: st.session_state.target_cities = []
    if 'target_age_cols' not in st.session_state: st.session_state.target_age_cols = []
    if 'target_gender_cols' not in st.session_state: st.session_state.target_gender_cols = []
    if 'platform' not in st.session_state: st.session_state.platform = 'Any' 
    if 'min_followers' not in st.session_state: st.session_state.min_followers = 0 
    if 'max_followers' not in st.session_state: st.session_state.max_followers = 1000000 
    if 'min_engagement' not in st.session_state: st.session_state.min_engagement = 0.0
    if 'max_fake_followers' not in st.session_state: st.session_state.max_fake_followers = 30.0
    if 'target_threshold_pct' not in st.session_state: st.session_state.target_threshold_pct = 30.0 
    
    if 'persona_input' not in st.session_state: st.session_state.persona_input = ""
    if 'other_requirements_input' not in st.session_state: st.session_state.other_requirements_input = ""
    
    if 'brand_keywords_input_4' not in st.session_state: st.session_state.brand_keywords_input_4 = [] 
    if 'analysis_brand_guideline_input' not in st.session_state: st.session_state.analysis_brand_guideline_input = ""
    
    if 'proposed_cost' not in st.session_state: st.session_state.proposed_cost = ""
    if 'campaign_period' not in st.session_state: st.session_state.campaign_period = ""
    if 'content_guideline' not in st.session_state: st.session_state.content_guideline = ""
    if 'generated_contract' not in st.session_state: st.session_state.generated_contract = None
    
    if 'brand_fit_result' not in st.session_state: st.session_state.brand_fit_result = None
    if 'liked_influencers' not in st.session_state: st.session_state.liked_influencers = set()
    if 'insight_report' not in st.session_state: st.session_state.insight_report = None
    
    if 'country_dist_loaded' not in st.session_state: st.session_state.country_dist_loaded = None
    if 'city_dist_loaded' not in st.session_state: st.session_state.city_dist_loaded = None


    data_file = "influencers_v23.csv" 
    
    try:
        FPDF(orientation='P', unit='mm', format='A4').add_font('MalgunGothic', '', 'MALGUN.TTF')
        FPDF(orientation='P', unit='mm', format='A4').add_font('MalgunGothic', 'B', 'MALGUNBD.TTF')
    except Exception:
        st.warning("⚠️ **PDF 생성을 위해 한글 폰트 설정이 필요합니다.** 'MALGUN.TTF'와 'MALGUNBD.TTF' 파일을 실행 폴더에 넣어주세요. 현재는 기본 폰트로 출력됩니다.")
        
    try:
        df = pd.read_csv(data_file)
        
        if st.session_state.country_dist_loaded is None:
            st.session_state.country_dist_loaded = df['audience_country_dist'].apply(json.loads)
        if st.session_state.city_dist_loaded is None:
            st.session_state.city_dist_loaded = df['audience_city_dist'].apply(json.loads)

        if 'age_under_18' not in df.columns or 'top_country' not in df.columns: 
            st.error(f"데이터 파일({data_file})이 V23 형식(Top N, Age 확장 포함)과 맞지 않습니다. '가상 데이터 생성' 탭에서 데이터를 재생성해주세요.")
            with tab1:
                st.warning("'⚙️ 가상 데이터 생성' 탭에서 데이터를 먼저 재생성해주세요.")
            with tab2:
                st.warning("데이터 파일 형식이 다릅니다. 데이터를 덮어쓰세요.")
                if st.button("가상 데이터 재생성 (V23 형식 덮어쓰기)"):
                    st.session_state.country_dist_loaded = None
                    st.session_state.city_dist_loaded = None
                    create_mock_data(data_file)
                    st.rerun()
        else:
            with tab1:
                run_app(df)
            with tab2:
                st.success(f"'{data_file}' 파일이 로드되었습니다. (V23 형식)")
                if st.button("가상 데이터 재생성 (덮어쓰기)"):
                    st.session_state.country_dist_loaded = None
                    st.session_state.city_dist_loaded = None
                    create_mock_data(data_file)
                    st.rerun() 
                st.dataframe(df.head())
                
    except FileNotFoundError:
        with tab2:
            st.warning(f"'{data_file}' 파일이 없습니다. 먼저 가상 데이터를 생성해주세요.")
            if st.button("가상 인플루언서 10,000명 데이터 생성하기"):
                create_mock_data(data_file)
                st.rerun() 
        with tab1:
            st.info("'⚙️ 가상 데이터 생성' 탭에서 데이터를 먼저 생성해주세요.")


if __name__ == "__main__":
    main()