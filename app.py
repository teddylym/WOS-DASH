import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import io
import altair as alt

# --- 페이지 설정 ---
st.set_page_config(page_title="WOS Analysis Dashboard", layout="centered")

# --- NLTK 리소스 다운로드 ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data(uploaded_file):
    encodings_to_try = ['utf-8', 'latin1', 'cp949', 'utf-8-sig']
    df = None
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df_try = pd.read_csv(uploaded_file, sep='\t', encoding=encoding)
            if df_try.shape[1] > 2: return df_try
        except Exception: continue
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df_try = pd.read_csv(uploaded_file, encoding=encoding)
            if df_try.shape[1] > 2: return df_try
        except Exception: continue
    return None

# --- 핵심 기능 함수 ---
def classify_article(row):
    inclusion_keywords = ['user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'behavior', 'experience', 'engagement', 'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 'society', 'commerce', 'marketing', 'business', 'brand', 'purchase', 'monetization', 'education', 'learning', 'influencer']
    exclusion_keywords = ['protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer', 'packet dropping', 'bandwidth', 'fec', 'arq', 'goodput', 'sensor data', 'geoscience', 'environmental data', 'wlan', 'ofdm', 'error correction', 'tcp', 'udp', 'network traffic']
    title = str(row.get('Article Title', row.get('TI', ''))).lower()
    source_title = str(row.get('Source Title', row.get('SO', ''))).lower()
    author_keywords = str(row.get('Author Keywords', row.get('DE', ''))).lower()
    keywords_plus = str(row.get('Keywords Plus', row.get('ID', ''))).lower()
    abstract = str(row.get('Abstract', row.get('AB', ''))).lower()
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    if any(keyword in full_text for keyword in exclusion_keywords): return 'Exclude (제외연구)'
    if any(keyword in full_text for keyword in inclusion_keywords): return 'Include (관련연구)'
    return 'Review (검토필요)'

# --- 수정된 키워드 전처리 함수 (단일 문자열 처리용) ---
def clean_keyword_string(keywords_str, stop_words, lemmatizer):
    if not isinstance(keywords_str, str):
        return ""
    all_keywords = keywords_str.lower().split(';')
    cleaned_keywords = set()
    for keyword in all_keywords:
        keyword = keyword.strip().replace('-', ' ')
        keyword = re.sub(r'[^a-z\s]', '', keyword)
        final_words = [lemmatizer.lemmatize(w) for w in keyword.split() if w not in stop_words and len(w) > 2]
        if final_words:
            cleaned_keywords.add(" ".join(final_words))
    return '; '.join(sorted(list(cleaned_keywords)))

# --- Streamlit UI 및 실행 로직 ---
st.title("WOS 데이터 분석 및 정제 도구")
st.caption("WOS Data Classifier & Preprocessor")

uploaded_file = st.file_uploader("WoS Raw Data 파일(CSV/TXT)을 업로드하세요", type=['csv', 'txt'])

if uploaded_file is not None:
    df_raw = load_data(uploaded_file)
    
    if df_raw is None:
        st.error("파일을 읽을 수 없습니다. 파일 형식을 확인해주세요.")
        st.stop()
    
    # WoS 원본 필드명과 표준 2자리 태그 매핑
    column_mapping = {
        'Authors': 'AU', 'AU': 'AU',
        'Article Title': 'TI', 'TI': 'TI',
        'Source Title': 'SO', 'SO': 'SO',
        'Author Keywords': 'DE', 'DE': 'DE',
        'Keywords Plus': 'ID', 'ID': 'ID',
        'Abstract': 'AB', 'AB': 'AB',
        'Cited References': 'CR', 'CR': 'CR',
        'Publication Year': 'PY', 'PY': 'PY',
        'Times Cited, All Databases': 'TC', 'TC': 'TC'
    }
    
    df = df_raw.copy()
    # 현재 데이터프레임에 있는 열만 골라서 이름 표준화
    rename_dict = {col: standard_col for col, standard_col in column_mapping.items() if col in df.columns}
    df.rename(columns=rename_dict, inplace=True)

    if st.button("분석 및 변환 시작 / Start Analysis & Conversion"):
        with st.spinner("분석 중... / Analyzing..."):
            
            # --- 1. 논문 분류 ---
            df['Classification'] = df.apply(classify_article, axis=1)
            
            # --- 2. '관련연구' 그룹의 DE, ID 필드 직접 전처리 ---
            stop_words = set(stopwords.words('english'))
            custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article'}
            stop_words.update(custom_stop_words)
            lemmatizer = WordNetLemmatizer()

            include_mask = df['Classification'] == 'Include (관련연구)'
            
            if 'DE' in df.columns:
                df.loc[include_mask, 'DE'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))
            if 'ID' in df.columns:
                df.loc[include_mask, 'ID'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))

            st.success("✅ 분석 및 변환 완료! / Process Complete!")
            
            # --- 3. 최종 출력 파일 생성 ---
            # 포함/검토필요 연구만 선택
            df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
            
            # 이미지에 명시된 9개 핵심 필드만 선택
            final_columns = ['AU', 'TI', 'SO', 'DE', 'ID', 'AB', 'CR', 'PY', 'TC']
            # 원본에 없는 열이 있을 경우를 대비하여, 있는 열만 선택
            existing_final_columns = [col for col in final_columns if col in df_final.columns]
            df_final_output = df_final[existing_final_columns]
            
            st.subheader("결과 요약 / Summary")
            st.metric("최종 분석 대상 논문 수 (Include + Review)", len(df_final))
            
            st.subheader("처리된 데이터 샘플 (상위 10개)")
            st.dataframe(df_final_output.head(10))

            # --- 다운로드 버튼 생성 ---
            @st.cache_data
            def convert_df_to_text(df_to_convert):
                # SciMAT 호환성을 위해 탭으로 구분된 텍스트로 변환
                return df_to_convert.to_csv(sep='\t', index=False, encoding='utf-8-sig').encode('utf-8-sig')

            text_data = convert_df_to_text(df_final_output)
            
            st.download_button(
               label="📥 최종 파일 다운로드 (.txt for SciMAT)",
               data=text_data,
               file_name="wos_processed_for_scimat.txt",
               mime="text/plain",
            )
