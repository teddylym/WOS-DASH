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
st.set_page_config(
    page_title="WOS Prep | Professional Edition",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 커스텀 CSS 스타일 (기존과 동일) ---
st.markdown("""
<style>
    /* ... (이전과 동일한 CSS 내용) ... */
    .main-container { background: #f8f9fa; min-height: 100vh; }
    .metric-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e9ecef; margin-bottom: 16px; transition: all 0.3s ease; }
    .metric-card:hover { box-shadow: 0 4px 20px rgba(0,56,117,0.15); border-color: #003875; }
    .metric-value { font-size: 2.8rem; font-weight: 700; color: #003875; margin: 0; line-height: 1; }
    .metric-label { font-size: 1rem; color: #6c757d; margin: 8px 0 0 0; font-weight: 500; }
    /* ... (이하 모든 CSS는 이전 코드와 동일하게 유지) ... */
</style>
""", unsafe_allow_html=True)


# --- NLTK 리소스 다운로드 (캐시 유지) ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- [핵심 수정] 개념 정규화 사전 (Thesaurus) ---
@st.cache_data
def build_normalization_map():
    """Cobo(2012)의 개념 단위 통합 원칙에 기반한 정규화 사전"""
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
        "user behavior": ["consumer behavior"]
    }
    # 빠른 조회를 위한 역방향 맵 생성 (variation -> standard_form)
    reverse_map = {}
    for standard_form, variations in base_map.items():
        for variation in variations:
            reverse_map[variation.strip().lower()] = standard_form
        reverse_map[standard_form.strip().lower()] = standard_form
    return reverse_map

NORMALIZATION_MAP = build_normalization_map()

# --- 데이터 로드 함수 (기존과 동일) ---
def load_data(uploaded_file):
    # ... (이전과 동일한 인코딩 처리 로직) ...
    return pd.read_csv(uploaded_file) # 간소화된 예시, 실제 코드는 이전 버전의 로직 유지

# --- 핵심 기능 함수 ---
def classify_article(row):
    # ... (기존과 동일한 분류 로직) ...
    inclusion_keywords = ['user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'behavior', 'experience', 'engagement', 'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 'society', 'commerce', 'marketing', 'business', 'brand', 'purchase', 'monetization', 'education', 'learning', 'influencer']
    exclusion_keywords = ['protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer', 'packet dropping', 'bandwidth', 'fec', 'arq', 'goodput', 'sensor data', 'geoscience', 'environmental data', 'wlan', 'ofdm', 'error correction', 'tcp', 'udp', 'network traffic']
    title = str(row.get('TI', '')).lower()
    source_title = str(row.get('SO', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    if any(keyword in full_text for keyword in exclusion_keywords): return 'Exclude (제외연구)'
    if any(keyword in full_text for keyword in inclusion_keywords): return 'Include (관련연구)'
    return 'Review (검토필요)'

# --- [핵심 수정] 개선된 키워드 전처리 함수 ---
def clean_keyword_string(keywords_str, stop_words, lemmatizer, normalization_map):
    """개념 정규화가 포함된 키워드 정제 처리"""
    if pd.isna(keywords_str) or not isinstance(keywords_str, str):
        return ""

    all_keywords = keywords_str.split(';')
    cleaned_keywords = set()

    for keyword in all_keywords:
        keyword_clean = keyword.strip().lower()
        if not keyword_clean:
            continue

        # 1단계: 개념 정규화 (Normalization Map으로 변환 시도)
        normalized_phrase = normalization_map.get(keyword_clean, keyword_clean)
        
        # 2단계: 문자 정제 및 표제어 추출 (Cleaning & Lemmatization)
        normalized_phrase = normalized_phrase.replace('-', ' ')
        normalized_phrase = re.sub(r'[^a-z\s]', '', normalized_phrase)
        
        words = normalized_phrase.split()
        filtered_words = []
        for word in words:
            if word and len(word) > 2 and word not in stop_words:
                lemmatized_word = lemmatizer.lemmatize(word)
                filtered_words.append(lemmatized_word)

        if filtered_words:
            final_keyword = " ".join(filtered_words)
            cleaned_keywords.add(final_keyword)
            
    return '; '.join(sorted(list(cleaned_keywords)))

# --- SCIMAT 형식 변환 함수 (기존과 동일) ---
def convert_df_to_scimat_format(df_to_convert):
    # ... (이전과 동일한 SciMAT 변환 로직) ...
    return "\n".join(file_content).encode('utf-8')


# --- 메인 UI (기존과 동일) ---
# (이전 코드의 st.markdown(header), st.markdown(feature_grid) 등 모든 UI 요소는 그대로 유지)
# (파일 업로드 및 분석 로직도 그대로 유지, 단 clean_keyword_string 함수 호출 시 normalization_map 전달)

# --- 실행 로직 예시 (실제 앱에서는 UI 흐름에 따라 배치) ---
# df['Classification'] = df.apply(classify_article, axis=1)
# include_mask = df['Classification'] == 'Include (관련연구)'
# if 'DE' in df.columns:
#     df.loc[include_mask, 'DE_cleaned'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer, NORMALIZATION_MAP))
# if 'ID' in df.columns:
#     df.loc[include_mask, 'ID_cleaned'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer, NORMALIZATION_MAP))

# (이하 모든 UI 코드 및 로직은 기존 코드와 동일하게 유지됩니다)

st.markdown("이 코드는 설명을 위해 일부가 생략되었습니다. 실제 사용시에는 이전 버전의 전체 UI코드를 사용하십시오.")
