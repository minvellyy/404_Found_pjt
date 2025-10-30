import streamlit as st
import pandas as pd
from datetime import date
import os 

# --- [1] 데이터 파일 경로 설정 ---
BASE_PATH = "table/"
PRODUCT_MASTER_FILE = os.path.join(BASE_PATH, 'product_master.csv')
CAMPAIGN_MASTER_FILE = os.path.join(BASE_PATH, 'campaign_master.csv')

# --- [2] 데이터 로드 함수들 (동일) ---
@st.cache_data
def load_product_data():
    """제품 마스터(CSV)를 읽어와서 드롭다운 목록을 만듭니다."""
    try:
        df_prod = pd.read_csv(PRODUCT_MASTER_FILE)
        return df_prod
    except FileNotFoundError:
        st.error(f"😭 '{PRODUCT_MASTER_FILE}' 파일을 찾을 수 없습니다!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"제품 파일 로드 중 오류 발생: {e}")
        return pd.DataFrame()

@st.cache_data
def load_campaign_data():
    """캠페인 마스터(CSV)를 읽어옵니다."""
    try:
        df_camp = pd.read_csv(CAMPAIGN_MASTER_FILE)
        return df_camp
    except FileNotFoundError:
        st.error(f"😭 '{CAMPAIGN_MASTER_FILE}' 파일을 찾을 수 없습니다!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"캠페인 파일 로드 중 오류 발생: {e}")
        return pd.DataFrame()

# --- [3] 데이터 로드 실행 ---
df_prod = load_product_data()
df_camp = load_campaign_data()

st.title("📝 기준 정보 관리")
st.markdown("새로운 캠페인, 제품, 인플루언서 정보를 등록/관리합니다.")

# --- [4] 신규 캠페인 등록 폼 (v3와 거의 동일) ---
st.divider()
st.subheader("신규 캠페인 등록")

with st.form(key="campaign_form"):
    
    if df_prod.empty:
        product_list = ['(제품 마스터 로드 실패)']
    else:
        product_list = df_prod['product_name'].unique().tolist()
        
    col1, col2 = st.columns(2)
    with col1:
        campaign_name = st.text_input(label="캠페인 이름 *")
        selected_product_name = st.selectbox(label="메인 제품 *", options=product_list) 
    with col2:
        start_date = st.date_input(label="시작일 *", value=date.today())
        end_date = st.date_input(label="종료일 *", value=date.today() + pd.Timedelta(days=30))
    
    total_budget = st.number_input(
        label="총 예산 (단위: 원) *", 
        min_value=0, 
        step=1000000, 
        format="%d"
    )
    
    submit_button = st.form_submit_button(label="💾 캠페인 '추가'하기")

# --- [5] '추가' 버튼 로직 (v3와 동일) ---
if submit_button:
    if not campaign_name or not selected_product_name or total_budget <= 0:
        st.error("모든 필수 필드(*)를 올바르게 입력해주세요. (예산은 0보다 커야 함)")
    elif end_date < start_date:
        st.error("종료일은 시작일보다 빠를 수 없습니다.")
    elif df_prod.empty or df_camp.empty:
        st.error("데이터 마스터 파일 로드에 실패하여 저장할 수 없습니다.")
    else:
        try:
            # (ID 생성 로직)
            last_id_num = df_camp['campaign_id'].str.split('-').str[-1].astype(int).max()
            new_id_num = last_id_num + 1
            new_campaign_id = f"DALBA-CAMP-{new_id_num:03d}"
            
            selected_product_id = df_prod[df_prod['product_name'] == selected_product_name]['product_id'].values[0]

            new_campaign_data = pd.DataFrame([{
                'campaign_id': new_campaign_id,
                'campaign_name': campaign_name,
                'product_id': selected_product_id,
                'start_date': str(start_date),
                'end_date': str(end_date),
                'total_budget': total_budget
            }])

            # (CSV에 Append)
            new_campaign_data.to_csv(
                CAMPAIGN_MASTER_FILE, 
                mode='a', header=False, index=False, encoding='utf-8'
            )
            
            # (캐시 지우기)
            st.cache_data.clear()

            st.success(f"✅ 캠페인 '{campaign_name}' (ID: {new_campaign_id})이(가) 'campaign_master.csv' 파일에 '추가'되었습니다!")
            st.balloons()
            # [!] st.rerun(): 페이지를 즉시 새로고침해서 아래 '삭제' 목록에도 바로 반영되게 함
            st.rerun() 

        except Exception as e:
            st.error(f"저장 중 심각한 오류 발생: {e}")

# --- [6] '삭제' 기능 (v4 신규 추가) ---
st.divider()
st.subheader("기존 캠페인 삭제")

if df_camp.empty:
    st.warning("삭제할 캠페인 목록을 불러올 수 없습니다.")
else:
    # 6-1. 삭제할 캠페인 선택 (드롭다운)
    # (제품 이름도 같이 보여줘야 구분하기 쉬움)
    df_camp_with_prod = pd.merge(df_camp, df_prod, on='product_id', how='left', suffixes=('', '_prod'))
    df_camp_with_prod['display_name'] = df_camp_with_prod['campaign_name'] + \
                                       " (" + df_camp_with_prod['product_name'] + \
                                       " | " + df_camp_with_prod['campaign_id'] + ")"
    
    campaign_list_to_delete = df_camp_with_prod['display_name'].tolist()
    
    selected_campaign_display_name = st.selectbox(
        "삭제할 캠페인을 선택하세요", 
        options=campaign_list_to_delete,
        index=None, # 기본값은 '선택 안 함'
        placeholder="삭제할 캠페인을 선택..."
    )

    # 6-2. '삭제' 버튼
    delete_button = st.button(label="🗑️ 선택한 캠페인 '삭제'하기", type="primary", disabled=(not selected_campaign_display_name))

    if delete_button:
        try:
            # 6-3. 선택한 display_name으로부터 '진짜 campaign_id' 찾아내기
            selected_campaign_id = df_camp_with_prod[
                df_camp_with_prod['display_name'] == selected_campaign_display_name
            ]['campaign_id'].values[0]

            # 6-4. [핵심] 삭제 로직
            # (1) 현재 캠페인 마스터(df_camp)에서 삭제할 ID를 '제외'한 나머지를 찾음
            df_remaining = df_camp[df_camp['campaign_id'] != selected_campaign_id]

            # (2) '제외된' 데이터프레임을 CSV 파일에 '전체 덮어쓰기(overwrite)'
            df_remaining.to_csv(
                CAMPAIGN_MASTER_FILE, 
                mode='w',          # 'w' = write (덮어쓰기)
                header=True,       # 덮어쓰는 거니까 header가 다시 필요함
                index=False,       # 인덱스 저장 안 함
                encoding='utf-8'
            )
            
            # (3) [매우 중요] 캐시 지우기
            st.cache_data.clear()

            st.success(f"✅ 캠페인 '{selected_campaign_display_name}' (ID: {selected_campaign_id})이(가) 'campaign_master.csv' 파일에서 '삭제'되었습니다!")
            st.info("이제 '성과 분석' 페이지로 이동하면, 삭제된 캠페인이 필터 목록에서 사라졌을 겁니다!")
            
            # [!] st.rerun(): 페이지를 즉시 새로고침해서 방금 삭제한 캠페인이
            # 이 '삭제' 드롭다운 목록에서도 바로 사라지게 함
            st.rerun()

        except Exception as e:
            st.error(f"삭제 중 심각한 오류 발생: {e}")
            st.error("CSV 파일이 다른 프로그램(예: 엑셀)에 의해 열려있는지 확인해보세요.")