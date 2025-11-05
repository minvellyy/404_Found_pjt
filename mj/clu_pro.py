import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import openai
import json
import io
import os
from dotenv import load_dotenv


# 페이지 설정
st.set_page_config(page_title="제품 타겟 분석 시스템", layout="wide")

# MySQL 연결 함수
@st.cache_resource
def get_db_connection():
    """MySQL 데이터베이스 연결"""
    try:
        # 직접 DB 정보 입력
        load_dotenv()
        conn = mysql.connector.connect(
            host=os.getenv("HOST", "localhost"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWD"),
            database=os.getenv("DB"),
            port=int(os.getenv("PORT", 3306))
        )
        return conn
    except Exception as e:
        st.error(f"데이터베이스 연결 실패: {e}")
        return None

# 제품 목록 가져오기
@st.cache_data(ttl=300)
def get_products():
    """DB에서 제품 목록 조회"""
    conn = get_db_connection()
    if conn:
        try:
            query = "SELECT id, name, category, description, ingredients FROM products"
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"제품 조회 실패: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

# AI 타겟 분석 함수
def analyze_target_with_ai(product_info):
    """OpenAI를 사용한 제품 타겟 분석"""
    try:
        # OpenAI API 키 직접 입력 (여기를 수정하세요!)
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            st.error("❌ .env 파일에 OPENAI_API_KEY가 설정되지 않았습니다.")
        else:
            st.success("✅ OpenAI API 키 불러오기 성공")
        
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
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 화장품 시장 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        st.error(f"AI 분석 실패: {e}")
        return None

# 유사 제품 추천 함수
def recommend_similar_products(target_product, all_products, n=5):
    """타겟 제품과 유사한 제품 추천"""
    try:
        # OpenAI API 키는 위에서 설정됨
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")

        
        products_list = all_products[all_products['id'] != target_product['id']][['name', 'category', 'description']].to_dict('records')
        
        prompt = f"""
타겟 제품:
- 이름: {target_product['name']}
- 카테고리: {target_product.get('category', 'N/A')}
- 설명: {target_product.get('description', 'N/A')}

다음 제품 목록에서 타겟 제품과 가장 유사한 제품 {n}개를 추천해주세요:
{json.dumps(products_list[:20], ensure_ascii=False)}

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
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 제품 추천 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        return result['recommendations']
        
    except Exception as e:
        st.error(f"제품 추천 실패: {e}")
        return []

# 엑셀 파일 생성 함수
def create_excel_report(product_info, target_analysis, similar_products):
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
        if similar_products:
            similar_df = pd.DataFrame(similar_products)
            similar_df.to_excel(writer, sheet_name='유사제품추천', index=False)
    
    output.seek(0)
    return output

# 메인 앱
def main():
    st.title("🎯 제품 타겟 분석 시스템")
    st.markdown("---")
    
    # 사이드바: 데이터베이스 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        st.info("코드 상단에서 DB 및 API 설정을 확인하세요.")
        
        if st.button("🔄 제품 목록 새로고침"):
            st.cache_data.clear()
            st.rerun()
    
    # 제품 목록 로드
    products = get_products()
    
    if products.empty:
        st.warning("제품 데이터를 불러올 수 없습니다. 데이터베이스 연결을 확인하세요.")
        st.info("""
        **코드 상단의 DB 설정을 확인하세요:**
        - host: MySQL 서버 주소
        - user: DB 사용자명
        - password: DB 비밀번호
        - database: DB 이름
        - OpenAI API 키도 확인하세요!
        """)
        return
    
    # 제품 선택
    st.subheader("1️⃣ 분석할 제품 선택")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_product_name = st.selectbox(
            "제품을 선택하세요",
            products['name'].tolist(),
            index=0
        )
    
    selected_product = products[products['name'] == selected_product_name].iloc[0].to_dict()
    
    with col2:
        st.metric("전체 제품 수", len(products))
    
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
    
    if analyze_button:
        with st.spinner("AI가 제품을 분석 중입니다..."):
            # 타겟 분석
            target_analysis = analyze_target_with_ai(selected_product)
            
            if target_analysis:
                st.success("✅ 분석 완료!")
                
                # 결과 표시
                st.markdown("---")
                st.subheader("📊 타겟 분석 결과")
                
                # 타겟 정보를 카드 형태로 표시
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
                
                # 유사 제품 추천
                similar_products = []
                if recommend_similar:
                    st.markdown("---")
                    st.subheader("🔍 유사 제품 추천")
                    
                    with st.spinner("유사 제품을 찾는 중..."):
                        similar_products = recommend_similar_products(selected_product, products)
                    
                    if similar_products:
                        for idx, product in enumerate(similar_products, 1):
                            with st.expander(f"#{idx} {product['product_name']} (유사도: {product['similarity_score']}%)"):
                                st.write(f"**추천 이유:** {product['reason']}")
                
                # 엑셀 다운로드
                st.markdown("---")
                st.subheader("📥 결과 다운로드")
                
                excel_file = create_excel_report(selected_product, target_analysis, similar_products)
                
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