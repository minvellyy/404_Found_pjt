import streamlit as st
import pandas as pd
from datetime import datetime
import openai
import json
import io
import os
import altair as alt # Altair 임포트 추가 (혹시 몰라)

# ============================================================================
# 유틸리티, DB 및 API 클라이언트 초기화 함수 (통합 프로젝트 공통)
# ============================================================================

# [통합 DB 연결] secrets.toml 파일 참조
@st.cache_resource
def get_db_connection():
    """Streamlit secrets.toml에 정의된 단일 MySQL DB 연결을 반환"""
    return st.connection("mysql_db", type="sql") 

# [통합 API 클라이언트] 키 오류 발생 시 즉시 감지 및 처리
@st.cache_resource
def get_openai_client():
    """OpenAI API 키를 사용하여 클라이언트를 초기화"""
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
        if not api_key or len(api_key) < 20: 
            st.error("❌ secrets.toml에 OPENAI_API_KEY가 비어있거나 너무 짧습니다. 키를 확인해주세요.")
            return None
        return openai.OpenAI(api_key=api_key)
    except KeyError:
        st.error("❌ secrets.toml 파일에 'OPENAI_API_KEY' 섹션이 없습니다.")
        return None
    except Exception as e:
        st.error(f"OpenAI 클라이언트 초기화 오류: {e}")
        return None

# 제품 목록 가져오기 함수 (DB에서 minji 테이블 조회)
@st.cache_data(ttl=300)
def get_minji():
    """DB에서 제품 목록 조회 (minji 테이블 사용)"""
    try:
        db_conn = get_db_connection()
        query = "SELECT id, name, category, description, ingredients FROM minji"
        df = db_conn.query(query)
        return df
    except Exception as e:
        st.error(f"제품 조회 실패. DB 연결 정보 및 'minji' 테이블을 확인하세요: {e}")
        return pd.DataFrame()


# AI 타겟 분석 함수
def analyze_target_with_ai(product_info):
    """OpenAI를 사용한 제품 타겟 분석"""
    client = get_openai_client()
    if client is None:
        return None
        
    try:
        prompt = f"""
다음 제품 정보를 분석하여 타겟 고객을 상세히 분석해주세요.

제품명: {product_info['name']}
카테고리: {product_info.get('category', 'N/A')}
설명: {product_info.get('description', 'N/A')}
성분: {product_info.get('ingredients', 'N/A')}

다음 형식의 JSON으로 응답해주세요:
{{
    "countries": ["국가1", "국가2", "국가3"],
    "cities": ["도시1", "도시2", "도시3"],
    "age_groups": ["연령대1", "연령대2"],
    "skin_types": ["피부타입1", "피부타입2"],
    "scent_preferences": ["향 선호도1", "향 선호도2"],
    "analysis_summary": "분석 요약"
}}

연령대는 "20대 초반", "30대", "40-50대" 형식으로,
피부타입은 "지성", "건성", "복합성", "민감성" 등으로,
향 선호도는 "플로럴", "시트러스", "우디", "프레시" 등으로 작성해주세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o", # [핵심 수정] JSON 호환성을 위해 gpt-4o로 변경
            messages=[
                {"role": "system", "content": "당신은 화장품 시장 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except openai.AuthenticationError:
        st.error("❌ AI 분석 실패: OpenAI API 키가 유효하지 않거나 만료되었습니다. secrets.toml을 확인해주세요. (Error 401)")
        return None
    except Exception as e:
        st.error(f"AI 분석 실패: {e}")
        return None

# 유사 제품 추천 함수
def recommend_similar_minji(target_product, all_minji, n=5):
    """타겟 제품과 유사한 제품 추천"""
    client = get_openai_client()
    if client is None:
        return []
        
    try:
        minji_list = all_minji[all_minji['id'] != target_product['id']][['name', 'category', 'description']].to_dict('records')
        
        prompt = f"""
타겟 제품:
- 이름: {target_product['name']}
- 카테고리: {target_product.get('category', 'N/A')}
- 설명: {target_product.get('description', 'N/A')}

다음 제품 목록에서 타겟 제품과 가장 유사한 제품 {n}개를 추천해주세요:
{json.dumps(minji_list[:20], ensure_ascii=False)}

다음 형식의 JSON으로 응답해주세요:
{{
    "recommendations": [
        {{
            "product_name": "제품명",
            "similarity_score": 85,
            "reason": "유사한 이유"
        }}
    ]
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o", # [핵심 수정] JSON 호환성을 위해 gpt-4o로 변경
            messages=[
                {"role": "system", "content": "당신은 제품 추천 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('recommendations', [])
        
    except openai.AuthenticationError:
        st.error("❌ 제품 추천 실패: OpenAI API 키가 유효하지 않거나 만료되었습니다. secrets.toml을 확인해주세요. (Error 401)")
        return []
    except Exception as e:
        st.error(f"제품 추천 실패: {e}")
        return []

# 엑셀 파일 생성 함수
def create_excel_report(product_info, target_analysis, similar_minji):
    """분석 결과를 엑셀 파일로 생성"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 제품 정보 시트
        product_df = pd.DataFrame([product_info])
        product_df.to_excel(writer, sheet_name='제품정보', index=False)
        
        # 타겟 분석 시트
        target_data = {
            '분석 항목': ['국가', '도시', '연령층', '피부타입', '향 선호도'],
            '타겟': [
                ', '.join(target_analysis.get('countries', [])),
                ', '.join(target_analysis.get('cities', [])),
                ', '.join(target_analysis.get('age_groups', [])),
                ', '.join(target_analysis.get('skin_types', [])),
                ', '.join(target_analysis.get('scent_preferences', []))
            ]
        }
        target_df = pd.DataFrame(target_data)
        target_df.to_excel(writer, sheet_name='타겟분석', index=False)
        
        # 분석 요약 시트
        summary_df = pd.DataFrame([{'분석 요약': target_analysis.get('analysis_summary', '')}])
        summary_df.to_excel(writer, sheet_name='분석요약', index=False)
        
        # 유사 제품 시트
        if similar_minji:
            similar_df = pd.DataFrame(similar_minji)
            similar_df.to_excel(writer, sheet_name='유사제품추천', index=False)
    
    output.seek(0)
    return output

# 메인 앱
def main():
    st.title("Ingredients  &  Insight")
    st.markdown("---")
    
    # 사이드바: 데이터베이스 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        st.info("DB 및 API 설정은 secrets.toml 파일을 참조합니다.")
        
        if st.button("🔄 제품 목록 새로고침"):
            st.cache_data.clear()
            st.rerun()
    
    # 제품 목록 로드
    minji = get_minji()
    
    if minji.empty:
        st.warning("제품 데이터를 불러올 수 없습니다. DB 연결(secrets.toml) 및 'minji' 테이블을 확인하세요.")
        st.info("→ 만약 'minji' 테이블이 없다면, MySQL Workbench에서 SQL 스크립트를 실행해주세요.")
        return
    
    # 제품 선택
    st.subheader("1️⃣ 분석할 제품 선택")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_product_name = st.selectbox(
            "제품을 선택하세요",
            minji['name'].tolist(),
            index=0
        )
    
    selected_product = minji[minji['name'] == selected_product_name].iloc[0].to_dict()
    
    with col2:
        st.metric("전체 제품 수", len(minji))
    
    # 선택된 제품 정보 표시
    with st.expander("📦 선택된 제품 상세 정보", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**제품명:** {selected_product['name']}")
            st.write(f"**카테고리:** {selected_product.get('category', 'N/A')}")
        with col2:
            st.write(f"**설명:** {selected_product.get('description', 'N/A')}")
            st.write(f"**성분:** {selected_product.get('ingredients', 'N/A')}")
    
    st.markdown("---")
    
    # 분석 실행
    st.subheader("2️⃣ 타겟 분석 실행")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        analyze_button = st.button("🤖 AI 타겟 분석 시작", type="primary", use_container_width=True)
    
    with col2:
        recommend_similar = st.checkbox("유사 제품 추천 포함", value=True)
    
    # 분석 결과 세션 상태에 저장 
    if 'analysis_result_1' not in st.session_state:
        st.session_state.analysis_result_1 = None
        st.session_state.product_name_1 = None

    if analyze_button or (st.session_state.product_name_1 == selected_product_name and st.session_state.analysis_result_1 is not None):
        
        # 버튼을 누르거나, 세션 상태에 저장된 결과가 현재 제품과 다르면 재분석
        if analyze_button or st.session_state.product_name_1 != selected_product_name:
            # 기존 결과를 지우고 스피너 실행
            st.session_state.analysis_result_1 = None 
            target_analysis = None
            
            with st.spinner("AI가 제품을 분석 중입니다..."):
                target_analysis = analyze_target_with_ai(selected_product)
                
                similar_minji = []
                if recommend_similar and target_analysis:
                    with st.spinner("유사 제품을 찾는 중..."):
                        similar_minji = recommend_similar_minji(selected_product, minji)
                        
                st.session_state.analysis_result_1 = (target_analysis, similar_minji)
                st.session_state.product_name_1 = selected_product_name
        
        # 세션 상태에서 결과 로드
        target_analysis, similar_minji = st.session_state.analysis_result_1
        
        if target_analysis:
            st.success("✅ 분석 완료!")
            
            # 결과 표시
            st.markdown("---")
            st.subheader("📊 타겟 분석 결과")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 🌍 국가/도시")
                st.write("**주요 국가:**")
                for country in target_analysis.get('countries', []):
                    st.write(f"- {country}")
                st.write("**주요 도시:**")
                for city in target_analysis.get('cities', []):
                    st.write(f"- {city}")
            
            with col2:
                st.markdown("### 👥 연령층 & 피부타입")
                st.write("**타겟 연령층:**")
                for age in target_analysis.get('age_groups', []):
                    st.write(f"- {age}")
                st.write("**적합 피부타입:**")
                for skin in target_analysis.get('skin_types', []):
                    st.write(f"- {skin}")
            
            with col3:
                st.markdown("### 🌸 향 선호도")
                for scent in target_analysis.get('scent_preferences', []):
                    st.write(f"- {scent}")
            
            # 분석 요약
            st.markdown("### 📝 분석 요약")
            st.info(target_analysis.get('analysis_summary', ''))
            
            # 유사 제품 추천 표시
            if recommend_similar and similar_minji:
                st.markdown("---")
                st.subheader("🔍 유사 제품 추천")
                
                if similar_minji:
                    for idx, product in enumerate(similar_minji, 1):
                        with st.expander(f"#{idx} {product['product_name']} (유사도: {product['similarity_score']}%)"):
                            st.write(f"**추천 이유:** {product['reason']}")
            
            # 엑셀 다운로드
            st.markdown("---")
            st.subheader("📥 결과 다운로드")
            
            excel_file = create_excel_report(selected_product, target_analysis, similar_minji)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"타겟분석_{selected_product['name']}_{timestamp}.xlsx"
            
            st.download_button(
                label="📊 엑셀 파일 다운로드",
                data=excel_file,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )


if __name__ == "__main__":
    main()
