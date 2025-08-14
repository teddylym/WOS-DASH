import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import altair as alt
import io

# --- 페이지 설정 ---
st.set_page_config(page_title="WOS Prep | Professional Edition", layout="wide", initial_sidebar_state="collapsed")

# --- 커스텀 CSS 스타일 ---
st.markdown("""
<style>
    /* 기존 CSS 유지, 생략 */
</style>
""", unsafe_allow_html=True)

# --- NLTK 리소스 다운로드 ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 키워드 정규화 사전 확장 ---
@st.cache_data
def build_normalization_map():
    base_map = {
        "live commerce": ["live shopping", "social commerce", "livestream shopping", "live video commerce", "e-commerce live streaming"],
        "live streaming": ["live-streaming", "livestreaming", "real time streaming", "live broadcast"],
        "user engagement": ["consumer engagement", "viewer engagement", "audience engagement", "customer engagement"],
        "purchase intention": ["purchase intentions", "buying intention", "purchase behavior"],
        "user experience": ["consumer experience", "viewer experience", "ux"],
        "social presence": ["perceived social presence"],
        "influencer marketing": ["influencer", "digital celebrities", "wanghong"],
        "platform technology": ["streaming technology", "platform architecture", "streaming media"],
        "peer-to-peer": ["p2p", "peer to peer"],
        "artificial intelligence": ["ai"],
        "user behavior": ["consumer behavior"],
        "vulnerability analysis": ["service quality", "platform adoption"]  # 추가: 상거래 관련 재분류
    }
    reverse_map = {}
    for standard_form, variations in base_map.items():
        for variation in variations:
            reverse_map[variation.strip().lower()] = standard_form
        reverse_map[standard_form.strip().lower()] = standard_form
    return reverse_map

NORMALIZATION_MAP = build_normalization_map()

# --- 데이터 로드 함수 ---
def load_data(uploaded_file):
    # 기존 로직 유지, 생략
    pass

# --- [재수정] 분류 함수: 상거래 중심으로 세분화 ---
def classify_article(row):
    strong_inclusion_keywords = [
        'live streaming commerce', 'social commerce', 'livestreaming commerce', 'purchase intention', 
        'customer engagement', 'consumer behavior', 'influencer marketing', 'brand engagement', 
        'online shopping', 'digital marketing', 'e-commerce', 'viewer engagement', 'user experience',
        'social motivations', 'parasocial interaction', 'virtual gift', 'fan engagement',
        'vulnerability analysis', 'service quality', 'platform adoption'  # 추가: 상거래 포착
    ]
    
    inclusion_keywords = [
        'user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'experience', 
        'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 
        'society', 'marketing', 'business', 'brand', 'monetization', 'education', 'learning'
    ]
    
    exclusion_keywords = [  # 세분화: 복합 키워드로 제한
        'protocol optimization', 'network coding scheme', 'wimax technology', 'ieee 802.16 standard',
        'mac layer protocol', 'packet dropping algorithm', 'bandwidth optimization', 
        'forward error correction scheme', 'sensor data processing', 'geoscience application'
    ]
    
    medical_keywords = ['surgical education', 'medical education', 'surgery', 'clinical learning']  # 추가: 의료 재검토
    
    title = str(row.get('TI', '')).lower()
    source_title = str(row.get('SO', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    
    # 1. 강력 포함 확인
    if any(keyword in full_text for keyword in strong_inclusion_keywords):
        return 'Include (관련연구)'
    
    # 2. 의료 교육 재검토
    if any(kw in full_text for kw in medical_keywords):
        if any(kw in full_text for kw in ['user experience', 'consumer engagement', 'e-commerce']):
            return 'Review (검토필요)'
        return 'Exclude (제외연구)'
    
    # 3. 명확 제외 확인 (복합 키워드 매칭)
    if any(keyword in full_text for keyword in exclusion_keywords):
        return 'Exclude (제외연구)'

    # 4. 일반 포함 확인
    if sum(1 for keyword in inclusion_keywords if keyword in full_text) >= 2:
        return 'Include (관련연구)'
    
    return 'Review (검토필요)'

# --- 키워드 전처리 함수 ---
def clean_keyword_string(keywords_str, stop_words, lemmatizer, normalization_map):
    # 기존 로직 유지, 생략
    pass

# --- SCIMAT 형식 변환 함수 ---
def convert_df_to_scimat_format(df_to_convert):
    # 기존 로직 유지, 생략
    pass

# --- 메인 헤더 및 기능 소개 ---
# 기존 HTML 유지, 생략

# --- 파일 업로드 및 처리 ---
uploaded_file = st.file_uploader(  # 기존 업로더
    "Tab-delimited, Plain Text, 또는 Excel 형식의 WOS 데이터 파일을 여기에 드래그하거나 선택하세요.",
    type=['csv', 'txt', 'xlsx', 'xls'],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("⚠️ 파일을 읽을 수 없습니다.")
        st.stop()

    # 컬럼 매핑 기존 유지

    with st.spinner("🔄 데이터를 분석하고 있습니다..."):
        # 기존 처리 로직

    # --- 분석 결과 요약 기존 유지 ---

    # --- [추가] Review 논문 UI ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">🔍 Review Needed Papers</div>
        <div class="section-subtitle">검토가 필요한 논문 목록</div>
    </div>
    """, unsafe_allow_html=True)
    
    review_papers = df[df['Classification'] == 'Review (검토필요)'].head(30)
    if not review_papers.empty:
        display_data = []
        for idx, row in review_papers.iterrows():
            display_data.append({
                '논문 제목': str(row.get('TI', 'No Title'))[:80],
                '저자': str(row.get('AU', 'Unknown')).split(';')[0],
                '연도': str(row.get('PY', 'N/A')),
                '저자 키워드': str(row.get('DE', 'N/A'))[:50]
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)
        for idx, row in review_papers.iterrows():
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Include: {row['TI'][:50]}", key=f"include_{idx}"):
                    df.loc[idx, 'Classification'] = 'Include (관련연구)'
            with col2:
                if st.button(f"Exclude: {row['TI'][:50]}", key=f"exclude_{idx}"):
                    df.loc[idx, 'Classification'] = 'Exclude (제외연구)'
    else:
        st.info("검토가 필요한 논문이 없습니다.")

    # --- 최종 파일 생성 및 다운로드 기존 유지 ---
