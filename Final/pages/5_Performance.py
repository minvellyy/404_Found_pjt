import streamlit as st
import pandas as pd
from typing import Set, Tuple
import numpy as np
import json
from openai import OpenAI
import pandas as pd
# 🔹 'create_engine', 'os', 'load_dotenv'는 더 이상 필요 없으므로 삭제

# 🔹 DB 접속 정보를 secrets.toml에서 자동으로 가져오므로 관련 코드 삭제

# 2) products 불러오기
query_products = """
SELECT
    p.product_id        AS 제품ID,
    p.brand_name        AS 브랜드명,
    p.product_name      AS 제품명,
    p.category          AS 카테고리,
    p.price             AS 가격,
    p.text_keyword      AS `핵심_성분/키워드`,
    p.visual_keyword    AS 브랜드_이미지_태그,
    p.effect_keyword    AS 효과_키워드,
    p.keyword_tag       AS 통합_키워드
FROM products p;
"""

# 3) influencers 불러오기
query_influencers = """
SELECT
    i.influencer_id     AS ID,
    i.influencer_name   AS 이름,
    i.handle            AS 계정핸들,
    i.platform          AS 플랫폼,
    i.account_category  AS 계정_카테고리,
    i.niche             AS 니치,
    i.follower_count    AS `팔로워 수`,
    i.avg_likes         AS 평균_좋아요,
    i.avg_comments      AS 평균_댓글,
    i.quality_grade     AS 품질등급,
    i.account_keywords  AS 주요_콘텐츠_키워드,
    i.email             AS 이메일
FROM influencers i;
"""

# 4) 캠페인 성과 데이터 불러오기
query_results = """
SELECT
    cp.post_id                       AS Post_ID,
    c.campaign_id                    AS Campaign_ID,
    c.campaign_name                  AS 캠페인명,
    c.objective                      AS 캠페인목적,
    cp.influencer_id                 AS Influencer_ID,
    i.influencer_name                AS 인플루언서명,
    i.handle                         AS 계정핸들,
    i.platform                       AS 플랫폼,
    i.follower_count                 AS 팔로워수,
    i.quality_grade                  AS 인플루언서등급,
    cp.product_id                    AS 제품ID,
    p.brand_name                     AS 브랜드명,
    p.product_name                   AS 제품명,
    p.category                       AS 제품카테고리,
    cp.post_date                     AS 게시일,
    cp.post_url                      AS 게시URL,
    cp.views                         AS 조회수,
    cp.likes                         AS 좋아요수,
    cp.comments                      AS 댓글수,
    cp.saves                         AS 저장수,
    cp.cost                          AS 총비용,
    (cp.likes + cp.comments + cp.saves) / cp.views * 100    AS 전환율,
    cp.saves / cp.views * 100                               AS 긍정_감정비율,
    cp.likes / cp.views * 100                               AS 클릭률,
    cp.cost / cp.likes                                      AS 클릭당비용,
    cp.views                                                AS 노출수,
    cp.views * 0.8                                          AS 도달수
FROM campaign_posts cp
JOIN campaigns   c ON cp.campaign_id   = c.campaign_id
JOIN influencers i ON cp.influencer_id = i.influencer_id
JOIN products    p ON cp.product_id    = p.product_id;
"""

# --- dotenv 로드 (삭제) ---

# -----------------------------------------------------------
# LLM Client 초기화 (🔹 수정됨)
# -----------------------------------------------------------
@st.cache_resource
def get_openai_client():
    try:
        # 🟢 [수정] st.secrets에서 "OPENAI_API_KEY" (대문자)를 바로 읽어옴
        api_key = st.secrets["OPENAI_API_KEY"]
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY가 .streamlit/secrets.toml에 설정되지 않았습니다."
            )
        client = OpenAI(api_key=api_key)
        return client
    except KeyError: # 🟢 'KeyError'를 잡아서 명확한 에러 메시지 제공
        st.error(
            "❌ OpenAI 클라이언트 초기화 실패: .streamlit/secrets.toml 파일에 'OPENAI_API_KEY'가 없습니다. 파일 이름을 확인해주세요."
        )
        st.stop()
    except Exception as e:
        st.error(
            f"❌ OpenAI 클라이언트 초기화 실패: {e}. .streamlit/secrets.toml 파일을 확인해주세요."
        )
        st.stop()

# -----------------------------------------------------------
# 1. LLM API 호출 함수: 마케팅 요청 분석
# -----------------------------------------------------------
@st.cache_data(show_spinner="🧠 LLM이 마케팅 요청을 분석 중입니다...")
def call_llm_for_analysis(
    prompt: str, df_products: pd.DataFrame
) -> Tuple[Set[str], Set[str], str]:
    client = get_openai_client()

    SYSTEM_PROMPT = """
    당신은 K-Beauty 브랜드의 시니어 마케팅 AI 어시스턴트입니다.
    사용자의 요청(prompt)을 분석하여 가장 적합한 제품 키워드와 시각적 감성 태그를 추출해야 합니다.
    출력은 반드시 다음 JSON 스키마를 준수해야 합니다:
    {
      "text_keywords": ["키워드1", "키워드2", "키워드3", ...],
      "visual_tags": ["태그1", "태그2", "태그3", ...]
    }

    키워드는 제품 성분/효능(예: 히알루론산, 수분, 미백)과 관련되어야 하며,
    태그는 브랜드 이미지/피드 감성(예: 시크, 저채도, 트렌디)과 관련되어야 합니다.
    키워드와 태그는 각각 최소 3개, 최대 5개를 추출해 주세요.
    """

    product_list = df_products[
        ["제품명", "핵심_성분/키워드", "브랜드_이미지_태그"]
    ].to_string(index=False)

    USER_PROMPT = f"""
    [마케터 요청]: {prompt}

    [참조 가능한 K-Beauty 제품 목록]:
    {product_list}

    위 요청에 가장 부합하는 'text_keywords'와 'visual_tags'를 JSON 형태로만 출력해 주세요.
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT},
            ],
            response_format={"type": "json_object"},
        )

        json_output = completion.choices[0].message.content
        analysis_result = json.loads(json_output)

        text_keywords_set = set(analysis_result.get("text_keywords", []))
        visual_tags_set = set(analysis_result.get("visual_tags", []))

        llm_summary = """**[LLM 분석 요약]**
GenAI 모델 (**GPT-4o**)이 마케터님의 요청을 분석했습니다.
추출된 파라미터는 인플루언서 매칭에 즉시 사용됩니다.
"""

        return text_keywords_set, visual_tags_set, llm_summary

    except Exception as e:
        st.error(f"❌ LLM API 호출 중 오류가 발생했습니다: {e}. GPT-4o 모델 호출에 실패했습니다.")
        return (
            {"AI_실패", "기본_수분", "트렌디"},
            {"시크", "미니멀", "저채도"},
            "**[LLM 분석 실패]** API 호출 실패. 안전을 위해 기본 키워드로 대체합니다.",
        )


# -----------------------------------------------------------
# 2. LLM API 호출 함수: 성장 진단 리포트 생성
# -----------------------------------------------------------
def call_llm_for_growth_analysis(influencer_data: pd.Series) -> str:
    client = get_openai_client()

    er = (
        (
            influencer_data.get("평균_좋아요", 1000)
            + influencer_data.get("평균_댓글", 100)
        )
        / influencer_data["팔로워 수"]
        * 100
    )

    SYSTEM_PROMPT = "당신은 인플루언서의 캠페인 성과 데이터와 콘텐츠 특성을 기반으로, 성장 잠재력과 구체적인 액션 플랜을 제시하는 전문 컨설턴트입니다. 톤은 전문적이고 독려하는 방식이어야 하며, 보고서 형태로 상세하게 (한국어 Markdown으로) 작성해야 합니다."

    USER_DATA = f"""
    [인플루언서 데이터]:
    이름: {influencer_data['이름']}
    팔로워: {influencer_data['팔로워 수']:,}명
    플랫폼: {influencer_data['플랫폼']}
    캠페인 참여 횟수: {influencer_data['캠페인_참여_횟수']}회
    평균 참여율(ER): {er:.2f}%
    평균 전환율: {influencer_data['평균_전환율']:.2f}%
    평균 CTR: {influencer_data['평균_CTR']:.2f}%
    평균 CPC: {influencer_data['평균_CPC']:.0f}원
    평균 CPA: {influencer_data['평균_CPA']:.0f}원
    평균 CPR: {influencer_data['평균_CPR']:.0f}원
    주요 콘텐츠 키워드: {influencer_data['주요_콘텐츠_키워드']}
    평균 피드 감성 태그: {influencer_data['평균_피드_감성_태그']}

    위 데이터를 기반으로 다음 구성으로 '성장 잠재력 진단 리포트'를 250자 내외로 상세하게 작성해 주세요:
    1. 핵심 콘텐츠 강점 (데이터 기반의 성과)
    2. 콘텐츠 약점 및 성장 제안 (구체적인 Action Plan 포함)
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_DATA},
            ],
        )
        return completion.choices[0].message.content

    except Exception as e:
        return (
            f"## ⚠️ AI 진단 실패\nLLM API 호출 실패: {e}\n(데이터 기반 성장 진단에 실패했습니다.)"
        )


# -----------------------------------------------------------
# 3. LLM API 호출 함수: 전체 KPI 요약 보고서 생성
# -----------------------------------------------------------
@st.cache_data(show_spinner="✍️ LLM이 전체 KPI 요약 보고서를 작성 중입니다...")
def call_llm_for_kpi_summary(df_influencers: pd.DataFrame, w_config: dict) -> str:
    client = get_openai_client()

    # 전략적_성과_점수를 기준으로 정렬 (df_influencers에는 이미 점수가 들어있다고 가정)
    df_sorted = df_influencers.sort_values(
        "전략적_성과_점수", ascending=False
    )

    top_kpi_data = df_sorted.head(5)[
        ["이름", "평균_CPR", "평균_CPA", "평균_전환율", "주요_콘텐츠_키워드"]
    ].to_string(index=False)
    bottom_kpi_data = df_sorted.tail(5)[
        ["이름", "평균_CPR", "평균_CPA", "평균_전환율", "주요_콘텐츠_키워드"]
    ].to_string(index=False)

    SYSTEM_PROMPT = "당신은 K-Beauty 브랜드의 CMO(최고 마케팅 책임자)에게 보고하는 데이터 사이언티스트입니다. 제공된 데이터를 기반으로 마케팅 효율성, 비용 성과(CPA/CPR), 그리고 콘텐츠 트렌드에 대한 핵심 통찰력을 담아 전문적인 (한국어 Markdown으로) 요약 보고서를 500자 내외로 상세하게 작성해야 합니다."

    USER_DATA = f"""
    [현재 마케팅 전략 가중치]:
    - 참여율(ER): {w_config['w_er']:.2f}, CPR: {w_config['w_cpr']:.2f}, 도달수: {w_config['w_reach']:.2f},
    - CPA: {w_config['w_cpa']:.2f}, CPM: {w_config['w_cpm']:.2f}

    [최종 효율성 순위 Top 5 인플루언서 데이터 요약]:
    {top_kpi_data}

    [최종 효율성 순위 Bottom 5 인플루언서 데이터 요약]:
    {bottom_kpi_data}

    위 데이터를 분석하여, **'현재 전략에 따른 마케팅 효율성 진단'**과 **'향후 캠페인 방향성에 대한 핵심 제안'**을 포함하는 보고서를 작성해 주세요.
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_DATA},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        return (
            f"## ⚠️ AI 보고서 생성 실패\nLLM API 호출 실패: {e}\n(전체 KPI 분석 보고서 생성에 실패했습니다.)"
        )


# --- 데이터 로드 함수 (🔹 수정됨) ---
@st.cache_data
def load_data():
    try:
        # 🔹 st.connection을 사용하여 secrets.toml의 "mysql_db" 연결 정보를 사용
        conn = st.connection("mysql_db", type="sql")
        
        # 🔹 conn.query()를 사용해 DataFrame으로 바로 로드
        df_products = conn.query(query_products)
        df_influencers = conn.query(query_influencers)
        df_results = conn.query(query_results)

        # 누락된 컬럼 추가
        df_influencers['평균_피드_감성_태그'] = df_influencers['주요_콘텐츠_키워드']
        
        def keyword_to_set(keyword_str):
            if isinstance(keyword_str, str):
                return set(keyword_str.replace(" ", "").split(","))
            return set()

        df_products["텍스트_키워드_SET"] = df_products["핵심_성분/키워드"].apply(
            keyword_to_set
        )
        df_products["시각_키워드_SET"] = df_products["브랜드_이미지_태그"].apply(
            keyword_to_set
        )
        df_influencers["텍스트_키워드_SET"] = df_influencers["주요_콘텐츠_키워드"].apply(
            keyword_to_set
        )
        df_influencers["시각_키워드_SET"] = df_influencers["평균_피드_감성_태그"].apply(
            keyword_to_set
        )

        df_influencers_with_results = df_influencers.merge(
            df_results.groupby("Influencer_ID").agg(
                캠페인_참여_횟수=("Campaign_ID", "count"),
                평균_전환율=("전환율", "mean"),
                평균_긍정_감정비율=("긍정_감정비율", "mean"),
                평균_CTR=("클릭률", "mean"),
                평균_CPC=("클릭당비용", "mean"),
                평균_노출수=("노출수", "mean"),
                평균_도달수=("도달수", "mean"),
                평균_총비용=("총비용", "mean"),
            ).reset_index(),
            left_on="ID",
            right_on="Influencer_ID",
            how="left",
        ).fillna(0)

        df_influencers_with_results["평균_CPM"] = (
            df_influencers_with_results["평균_총비용"]
            / df_influencers_with_results["평균_노출수"]
        ).replace([np.inf, -np.inf], 0).fillna(0) * 1000
        
        df_influencers_with_results["평균_CPR"] = (
            df_influencers_with_results["평균_총비용"]
            / df_influencers_with_results["평균_도달수"]
        ).replace([np.inf, -np.inf], 0).fillna(0)
        
        safe_conversion = df_influencers_with_results["평균_도달수"] * (
            df_influencers_with_results["평균_전환율"] / 100
        )
        safe_conversion = safe_conversion.replace(0, 1e-6)
        df_influencers_with_results["평균_CPA"] = (
            df_influencers_with_results["평균_총비용"] / safe_conversion
        ).replace([np.inf, -np.inf], 0).fillna(0)

        # 🔥 진정성 지수 계산 (참여율, 전환율, 긍정 감정 비율 기반)
        # 참여율 계산
        er = (
            (df_influencers_with_results["평균_좋아요"] + df_influencers_with_results["평균_댓글"])
            / df_influencers_with_results["팔로워 수"]
            * 100
        )
        
        # 진정성 지수 = (참여율 정규화 * 0.4) + (전환율 정규화 * 0.3) + (긍정감정 정규화 * 0.3)
        # 각 지표를 0-100 범위로 정규화
        er_normalized = np.minimum(er / 10 * 100, 100)  # ER 10%를 100점으로
        conversion_normalized = np.minimum(df_influencers_with_results["평균_전환율"] / 5 * 100, 100)  # 전환율 5%를 100점으로
        sentiment_normalized = df_influencers_with_results["평균_긍정_감정비율"]  # 이미 0-100 범위
        
        df_influencers_with_results["진정성_지수"] = (
            er_normalized * 0.4 + 
            conversion_normalized * 0.3 + 
            sentiment_normalized * 0.3
        ).fillna(50)  # 캠페인 이력이 없으면 기본값 50
        
        # 0-100 범위로 클리핑
        df_influencers_with_results["진정성_지수"] = df_influencers_with_results["진정성_지수"].clip(0, 100)

        cost_cols = ["평균_CPM", "평균_CPR", "평균_CPA"]
        for col in cost_cols:
            if (
                df_influencers_with_results[col]
                .replace([np.inf, -np.inf], 0)
                .max()
                > 0
            ):
                no_history_value = (
                    df_influencers_with_results[
                        df_influencers_with_results["캠페인_참여_횟수"] > 0
                    ][col]
                    .replace([np.inf, -np.inf], 0)
                    .max()
                    * 1.1
                )
                df_influencers_with_results.loc[
                    df_influencers_with_results["캠페인_참여_횟수"] == 0, col
                ] = no_history_value if no_history_value > 0 else 1000000
            else:
                df_influencers_with_results.loc[
                    df_influencers_with_results["캠페인_참여_횟수"] == 0, col
                ] = 1000000

        df_influencers_with_results.loc[
            df_influencers_with_results["캠페인_참여_횟수"] == 0,
            ["평균_도달수", "평균_총비용", "평균_노출수"],
        ] = 0
        df_influencers_with_results = df_influencers_with_results.fillna(0)

        # 초기화용 컬럼
        df_influencers_with_results["전략적_성과_점수"] = 0.0

        return df_products, df_influencers_with_results
    
    # 🔹 에러 핸들링 수정
    except Exception as e:
        st.error(f"데이터베이스 연결 또는 쿼리 실패: {e}")
        st.error("'.streamlit/secrets.toml' 파일의 [connections.mysql_db] 설정을 확인해주세요.")
        return pd.DataFrame(), pd.DataFrame()


# --- 공통 함수 ---
def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    if not set1 and not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union


# --- 탭 1: 매칭 모듈 ---
# (이 코드는 존재하지만, 아래 app() 정의에서 호출되지 않음)
def matching_module(df_products: pd.DataFrame, df_influencers: pd.DataFrame):
    st.title("🧠 생성형 AI 기반 맞춤형 인플루언서 매칭")
    st.markdown(
        "마케팅 요청을 자연어로 입력하면, **GPT-4o**가 자동으로 키워드와 감성을 추출하여 인플루언서를 추천합니다."
    )
    st.markdown("---")

    W_CONTENT = 0.6
    W_STRATEGY = 0.4

    w_er = st.session_state.get("w_er", 0.35)
    w_cpr = st.session_state.get("w_cpr", 0.25)
    w_reach = st.session_state.get("w_reach", 0.20)
    w_cpa = st.session_state.get("w_cpa", 0.10)
    w_cpm = st.session_state.get("w_cpm", 0.10)

    left_col, right_col = st.columns([1, 2])

    with left_col:
        st.header("1. 마케팅 요구사항 입력 (LLM Prompt)")
        prompt = st.text_area(
            "원하는 제품/브랜드 이미지에 대해 설명하세요:",
            value="요즘 MZ 세대를 타겟으로, 수분 보충이 확실하고 인스타 감성이 잘 맞는 시크한 무드의 마이크로 인플루언서를 추천해줘.",
            height=150,
        )

        if not prompt:
            st.warning("마케팅 요구사항을 입력해 주세요.")
            return

        text_keywords_set, visual_tags_set, llm_summary = call_llm_for_analysis(
            prompt, df_products
        )

        st.markdown("---")
        st.header("2. LLM 분석 결과")
        st.markdown(llm_summary)
        st.markdown(f"**텍스트 키워드:** `{', '.join(text_keywords_set)}`")
        st.markdown(f"**시각적 감성 태그:** `{', '.join(visual_tags_set)}`")
        st.markdown("---")

        st.subheader("3. 현재 적용된 매칭 전략")
        st.info(
            f"**콘텐츠 적합도({W_CONTENT*100:.0f}%)**와 **전략적 성과({W_STRATEGY*100:.0f}%)**를 합산합니다."
        )
        st.markdown(
            f"**전략적 성과 가중치:** ER({w_er:.2f}), CPR({w_cpr:.2f}), 도달({w_reach:.2f}), CPA({w_cpa:.2f}), CPM({w_cpm:.2f})"
        )
        st.markdown("이 가중치는 **'📊 성과 분석 대시보드' 탭**에서 조정할 수 있습니다.")

    with right_col:
        df_valid = (
            df_influencers[df_influencers["캠페인_참여_횟수"] > 0]
            .replace([np.inf, -np.inf], np.nan)
            .dropna(subset=["평균_CPR", "평균_CPA", "평균_CPM", "평균_도달수"])
        )
        min_cpr, max_cpr = df_valid["평균_CPR"].min(), df_valid["평균_CPR"].max()
        min_cpa, max_cpa = df_valid["평균_CPA"].min(), df_valid["평균_CPA"].max()
        min_cpm, max_cpm = df_valid["평균_CPM"].min(), df_valid["평균_CPM"].max()
        min_reach, max_reach = (
            df_valid["평균_도달수"].min(),
            df_valid["평균_도달수"].max(),
        )
        er_max_limit = 10.0

        results = []
        for _, influencer in df_influencers.iterrows():
            text_score = (
                calculate_jaccard_similarity(
                    text_keywords_set, influencer["텍스트_키워드_SET"]
                )
                * 100
            )
            visual_score = (
                calculate_jaccard_similarity(
                    visual_tags_set, influencer["시각_키워드_SET"]
                )
                * 100
            )
            final_matching_score = (W_CONTENT * text_score) + (
                (1.0 - W_CONTENT) * visual_score
            )

            matched_text_keywords = text_keywords_set.intersection(
                influencer["텍스트_키워드_SET"]
            )
            matched_visual_tags = visual_tags_set.intersection(
                influencer["시각_키워드_SET"]
            )

            er = (
                (
                    influencer.get("평균_좋아요", 1000)
                    + influencer.get("평균_댓글", 100)
                )
                / influencer["팔로워 수"]
                * 100
            )
            er_score = np.minimum((er / er_max_limit) * 100, 100)

            if (
                influencer["캠페인_참여_횟수"] > 0
                and max_cpr > min_cpr
                and max_cpa > min_cpa
                and max_cpm > min_cpm
            ):
                cpr_score = (
                    1 - (influencer["평균_CPR"] - min_cpr) / (max_cpr - min_cpr)
                ) * 100
                cpa_score = (
                    1 - (influencer["평균_CPA"] - min_cpa) / (max_cpa - min_cpa)
                ) * 100
                cpm_score = (
                    1 - (influencer["평균_CPM"] - min_cpm) / (max_cpm - min_cpm)
                ) * 100
                reach_score = (
                    influencer["평균_도달수"] / max_reach * 100 if max_reach > 0 else 0
                )
            else:
                cpr_score, cpa_score, cpm_score = 0, 0, 0
                reach_score = 0

            strategy_score = (
                er_score * w_er
                + cpr_score * w_cpr
                + reach_score * w_reach
                + cpa_score * w_cpa
                + cpm_score * w_cpm
            )

            final_total_score = (
                final_matching_score * W_CONTENT + strategy_score * W_STRATEGY
            )

            results.append(
                {
                    "이름": influencer["이름"],
                    "플랫폼": influencer["플랫폼"],
                    "팔로워 수": influencer["팔로워 수"],
                    "참여율 (ER)": f"{er:.2f}%",
                    "콘텐츠_적합도": final_matching_score,
                    "전략적_성과_점수": strategy_score,
                    "최종_종합_점수": final_total_score,
                    "일치_키워드": ", ".join(matched_text_keywords)
                    if matched_text_keywords
                    else "없음",
                    "일치_감성_태그": ", ".join(matched_visual_tags)
                    if matched_visual_tags
                    else "없음",
                    "ID": influencer["ID"],
                }
            )

        df_results_match = pd.DataFrame(results)
        df_results_sorted = df_results_match.sort_values(
            by="최종_종합_점수", ascending=False
        )

        st.header("✨ AI 매칭 결과: 인플루언서 추천 리스트")

        top_5 = df_results_sorted.head(5).copy()
        top_5.index = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        st.subheader("⭐ 추천 인플루언서 (Top 5)")
        st.dataframe(
            top_5[
                [
                    "이름",
                    "최종_종합_점수",
                    "콘텐츠_적합도",
                    "전략적_성과_점수",
                    "참여율 (ER)",
                    "일치_키워드",
                    "일치_감성_태그",
                ]
            ],
            column_config={
                "최종_종합_점수": st.column_config.ProgressColumn(
                    "최종 점수 (100)",
                    format="%.1f점",
                    min_value=0,
                    max_value=100,
                    help="콘텐츠 적합도와 전략적 성과의 가중 평균",
                ),
                "콘텐츠_적합도": st.column_config.NumberColumn(
                    "콘텐츠 적합도", format="%.1f점"
                ),
                "전략적_성과_점수": st.column_config.NumberColumn(
                    "전략적 성과", format="%.1f점"
                ),
                "참여율 (ER)": st.column_config.TextColumn("참여율 (ER)"),
            },
            width='stretch',
        )

        # 제품 선택 섹션 (selected_product 오류 수정 버전 그대로 유지)
        st.markdown("---")
        st.subheader("📦 이번 캠페인에서 사용할 제품 선택")

        product_names = df_products["제품명"].unique().tolist()
        if product_names:
            if "selected_product" not in st.session_state:
                st.session_state.selected_product = product_names[0]

            default_index = (
                product_names.index(st.session_state.selected_product)
                if st.session_state.selected_product in product_names
                else 0
            )

            selected_product = st.selectbox(
                "캠페인 제품을 선택하세요:",
                product_names,
                index=default_index,
                key="selected_product",
            )

            st.caption(f"선택된 제품: **{selected_product}**")
        else:
            st.info("등록된 제품 데이터가 없습니다.")


# --- 탭 2: 성과 분석 대시보드 ---
def kpi_dashboard_module(df_influencers: pd.DataFrame):
    st.title("📊 Performance")
    st.markdown(
        "KPI 정의를 확인하고, 인플루언서 매칭에 반영될 **전략적 성과 가중치**를 조정합니다. **가중치에 따라 순위가 변경**됩니다."
    )
    st.markdown("---")

    
    st.header("1. 전략적 성과 가중치 설정")
    st.markdown(
        "인플루언서 매칭 시, KPI 중 어떤 지표의 효율을 더 중요하게 평가할지 결정합니다. (총합 1.00)"
    )

    if "w_er" not in st.session_state:
        st.session_state.w_er = 0.35
        st.session_state.w_cpr = 0.25
        st.session_state.w_reach = 0.20
        st.session_state.w_cpa = 0.10
        st.session_state.w_cpm = 0.10

    w_er = st.slider(
        "참여율(ER) 가중치", 0.0, 1.0, st.session_state.w_er, 0.05, key="slider_er"
    )
    w_cpr = st.slider(
        "CPR 가중치", 0.0, 1.0, st.session_state.w_cpr, 0.05, key="slider_cpr"
    )
    w_reach = st.slider(
        "도달수 가중치",
        0.0,
        1.0,
        st.session_state.w_reach,
        0.05,
        key="slider_reach",
    )
    w_cpa = st.slider(
        "CPA 가중치", 0.0, 1.0, st.session_state.w_cpa, 0.05, key="slider_cpa"
    )
    w_cpm = st.slider(
        "CPM 가중치", 0.0, 1.0, st.session_state.w_cpm, 0.05, key="slider_cpm"
    )

    total_w = w_er + w_cpr + w_reach + w_cpa + w_cpm
    if total_w > 0:
        st.session_state.w_er = w_er / total_w
        st.session_state.w_cpr = w_cpr / total_w
        st.session_state.w_reach = w_reach / total_w
        st.session_state.w_cpa = w_cpa / total_w
        st.session_state.w_cpm = w_cpm / total_w
    else:
        st.session_state.w_er = 0.2
        st.session_state.w_cpr = 0.2
        st.session_state.w_reach = 0.2
        st.session_state.w_cpa = 0.2
        st.session_state.w_cpm = 0.2

    st.success(
        f"**총 가중치 합계:** {st.session_state.w_er + st.session_state.w_cpr + st.session_state.w_reach + st.session_state.w_cpa + st.session_state.w_cpm:.2f} (자동 정규화)"
    )

    st.markdown("---")

    # --- 3. 가중치 기반 인플루언서 효율성 순위 ---
    st.header("2. 전략적 가중치 기반 인플루언서 효율성 순위 (Top 10)")

    df_temp = df_influencers.copy()
    df_temp = df_temp[df_temp["캠페인_참여_횟수"] > 0]

    if not df_temp.empty:
        df_valid = (
            df_temp.replace([np.inf, -np.inf], np.nan)
            .dropna(subset=["평균_CPR", "평균_CPA", "평균_CPM", "평균_도달수"])
        )
        min_cpr, max_cpr = df_valid["평균_CPR"].min(), df_valid["평균_CPR"].max()
        min_cpa, max_cpa = df_valid["평균_CPA"].min(), df_valid["평균_CPA"].max()
        min_cpm, max_cpm = df_valid["평균_CPM"].min(), df_valid["평균_CPM"].max()
        min_reach, max_reach = (
            df_valid["평균_도달수"].min(),
            df_valid["평균_도달수"].max(),
        )
        er_max_limit = 10.0

        er = (
            (
                df_temp.get("평균_좋아요", 1000)
                + df_temp.get("평균_댓글", 100)
            )
            / df_temp["팔로워 수"]
            * 100
        )
        er_score = np.minimum((er / er_max_limit) * 100, 100)

        cpr_score = (
            (1 - (df_temp["평균_CPR"] - min_cpr) / (max_cpr - min_cpr)) * 100
            if max_cpr > min_cpr
            else 0
        )
        cpa_score = (
            (1 - (df_temp["평균_CPA"] - min_cpa) / (max_cpa - min_cpa)) * 100
            if max_cpa > min_cpa
            else 0
        )
        cpm_score = (
            (1 - (df_temp["평균_CPM"] - min_cpm) / (max_cpm - min_cpm)) * 100
            if max_cpm > min_cpm
            else 0
        )
        reach_score = (
            df_temp["평균_도달수"] / max_reach * 100 if max_reach > 0 else 0
        )

        df_temp["전략적_성과_점수"] = (
            er_score * st.session_state.w_er
            + cpr_score * st.session_state.w_cpr
            + reach_score * st.session_state.w_reach
            + cpa_score * st.session_state.w_cpa
            + cpm_score * st.session_state.w_cpm
        )

        df_sorted_strategy = df_temp.sort_values(
            "전략적_성과_점수", ascending=False
        )

        st.dataframe(
            df_sorted_strategy[
                ["이름", "팔로워 수", "전략적_성과_점수", "평균_CPR", "평균_CPA", "평균_전환율"]
            ].head(10),
            column_config={
                "전략적_성과_점수": st.column_config.ProgressColumn(
                    "전략적 효율성 (100)",
                    format="%.1f점",
                    min_value=0,
                    max_value=100,
                    help="설정한 가중치에 따른 종합 성과 점수",
                ),
                "평균_CPR": st.column_config.NumberColumn(
                    "평균 CPR (원)", format="%.0f"
                ),
                "평균_CPA": st.column_config.NumberColumn(
                    "평균 CPA (원)", format="%.0f"
                ),
                "평균_전환율": st.column_config.NumberColumn(
                    "평균 CR (%)", format="%.2f"
                ),
            },
            hide_index=True,
            width='stretch',
        )
    else:
        st.info("캠페인 이력이 있는 인플루언서 데이터가 없어 순위를 매길 수 없습니다.")

    st.markdown("---")

    # --- 4. GenAI KPI 요약 보고서 ---
    st.header("3. 📝 전체 KPI 요약 및 마케팅 전략 제언")

    kpi_summary_key = "kpi_summary_report"
    if kpi_summary_key not in st.session_state:
        st.session_state[kpi_summary_key] = None

    with st.form(key="kpi_summary_form"):
        submitted = st.form_submit_button("요약 보고서 생성 (현재 가중치 기반)")
        if submitted:
            if df_temp.empty:
                st.error("캠페인 이력이 있는 인플루언서가 없어 요약 보고서를 생성할 수 없습니다.")
            else:
                with st.spinner(
                    "AI가 전체 마케팅 성과를 분석하고 보고서를 작성 중입니다..."
                ):
                    w_config = {
                        "w_er": st.session_state.w_er,
                        "w_cpr": st.session_state.w_cpr,
                        "w_reach": st.session_state.w_reach,
                        "w_cpa": st.session_state.w_cpa,
                        "w_cpm": st.session_state.w_cpm,
                    }
                    # 🔹 3번에서 계산한 df_temp(전략적_성과_점수 포함)를 그대로 전달
                    st.session_state[kpi_summary_key] = call_llm_for_kpi_summary(
                        df_temp, w_config
                    )

    if st.session_state[kpi_summary_key]:
        st.success("✅ 마케팅 전략 보고서가 생성되었습니다!")
        st.markdown(st.session_state[kpi_summary_key])


# --- 탭 3: 포트폴리오 모듈 ---
def portfolio_module(df_influencers: pd.DataFrame):
    st.title("🤝 Win-Win 협업 제안: 인플루언서 데이터 포트폴리오")
    st.markdown(
        "단순 팔로워 수가 아닌, 데이터로 증명된 **진정한 영향력**을 보여줌으로써 투명한 협업 관계를 구축합니다."
    )
    st.markdown("---")

    influencer_names = df_influencers["이름"].unique().tolist()
    selected_influencer_name = st.selectbox(
        "데이터 포트폴리오를 확인할 인플루언서를 선택하세요:", influencer_names
    )

    selected_data = df_influencers[
        df_influencers["이름"] == selected_influencer_name
    ].iloc[0]

    st.subheader(f"✨ {selected_influencer_name} 님의 협업 가치 리포트")
    st.markdown(
        """
> **핵심 메시지:** 이 리포트는 **진정성, 참여율, 실제 전환 기여도**를 객관적으로 증명하여  
> 향후 브랜드와의 협상력을 높이는 포트폴리오 자료로 활용될 수 있습니다.  
> 우리는 당신의 진정한 영향력에 투자합니다.
"""
    )
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    er = (
        (
            selected_data.get("평균_좋아요", 1000)
            + selected_data.get("평균_댓글", 100)
        )
        / selected_data["팔로워 수"]
        * 100
    )

    col1.metric("팔로워 수", f"{selected_data['팔로워 수']:,} 명")
    col2.metric(
        "평균 참여율 (ER)",
        f"{er:.2f}%",
        help="팔로워 대비 좋아요/댓글 수로 계산된 활동성 지표입니다.",
    )
    col3.metric("진정성 지수", f"{selected_data['진정성_지수']:.0f} 점")
    col4.metric("캠페인 참여 횟수", f"{selected_data['캠페인_참여_횟수']:.0f} 회")

    st.markdown("---")

    st.subheader("📊 비즈니스 기여도 분석 (Campaign Performance)")
    col5, col6, col7, col8 = st.columns(4)
    if selected_data["캠페인_참여_횟수"] > 0:
        col5.metric("평균 전환율 (CR)", f"{selected_data['평균_전환율']:.2f} %")
        col6.metric("평균 클릭률 (CTR)", f"{selected_data['평균_CTR']:.2f} %")
        col7.metric("평균 CPC", f"{selected_data['평균_CPC']:.0f} 원")
        col8.metric("평균 긍정 감성 기여", f"{selected_data['평균_긍정_감정비율']:.1f} %")

        st.markdown("---")
        st.markdown("**주요 비용 효율 지표**")
        col9, col10, col11 = st.columns(3)
        col9.metric("평균 CPA", f"{selected_data['평균_CPA']:.0f} 원")
        col10.metric("평균 CPR", f"{selected_data['평균_CPR']:.0f} 원")
        col11.metric("평균 CPM", f"{selected_data['평균_CPM']:.0f} 원")
    else:
        st.info("이 인플루언서의 캠페인 성과 데이터는 아직 없습니다.")

    st.markdown("---")

    st.subheader("💡 데이터 기반 성장 진단 및 Action Plan")
    growth_key = f"growth_report_{selected_data['ID']}"
    if growth_key not in st.session_state:
        st.session_state[growth_key] = None

    with st.form(key=f"growth_form_{selected_data['ID']}"):
        submitted = st.form_submit_button("AI 성장 진단 리포트 생성")
        if submitted:
            with st.spinner(
                f"AI가 {selected_influencer_name}님의 성장 잠재력을 분석 중입니다..."
            ):
                st.session_state[growth_key] = call_llm_for_growth_analysis(
                    selected_data
                )

    if st.session_state[growth_key]:
        st.success("✅ 성장 진단 리포트가 생성되었습니다!")
        st.markdown(st.session_state[growth_key])


# --- Streamlit 앱 정의 (🔹 수정됨) ---
# 🔹 st.set_page_config는 Home.py에만 있어야 하므로 삭제
# 🔹 if __name__ == "__main__": 및 app() 호출부 삭제
# 🔹 app() 함수의 내용만 남겨서 페이지가 바로 실행되도록 함

df_products, df_influencers = load_data()

# 🔹 데이터 로드 실패 시 페이지 실행 중단
if df_products.empty or df_influencers.empty:
    st.error("데이터 로딩에 실패하여 페이지를 표시할 수 없습니다.")
    st.stop()

# 🔹 탭을 2개만 사용 (원래 코드의 app() 함수 내용)
tab1, tab2 = st.tabs(
    ["📊 성과 분석 대시보드", "🤝 Win-Win 포트폴리오 제안"]
)

df_influencers_copy = df_influencers.copy()

# 🔹 첫 번째 탭: 성과 분석 대시보드
with tab1:
    kpi_dashboard_module(df_influencers_copy)

# 🔹 두 번째 탭: 포트폴리오 모듈
with tab2:
    portfolio_module(df_influencers_copy)