import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import io
import altair as alt

# --- 페이지 설정 (Page Config) ---
st.set_page_config(page_title="WOS Analysis Dashboard", layout="centered")

# --- NLTK 리소스 다운로드 (캐시 활용) ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 데이터 로드 함수 (인코딩 문제 해결) ---
@st.cache_data
def load_data(uploaded_file):
    encodings_to_try = ['utf-8', 'latin1', 'cp949', 'utf-8-sig']
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep='\t', encoding=encoding)
            if df.shape[1] > 2: return df
        except Exception:
            continue
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=encoding)
            if df.shape[1] > 2: return df
        except Exception:
            continue
    return None

# --- 핵심 기능 함수 정의 (Core Functions) ---
def classify_article(row):
    inclusion_keywords = [
        'user', 'viewer', 'audience', 'streamer', 'consumer', 'participant',
        'behavior', 'experience', 'engagement', 'interaction', 'motivation',
        'psychology', 'social', 'community', 'cultural', 'society',
        'commerce', 'marketing', 'business', 'brand', 'purchase', 'monetization',
        'education', 'learning', 'influencer'
    ]
    exclusion_keywords = [
        'protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer',
        'packet dropping', 'bandwidth', 'fec', 'arq', 'goodput',
        'sensor data', 'geoscience', 'environmental data', 'wlan',
        'ofdm', 'error correction', 'tcp', 'udp', 'network traffic'
    ]
    title = str(row.get('Article Title', row.get('TI', ''))).lower()
    abstract = str(row.get('Abstract', row.get('AB', ''))).lower()
    author_keywords = str(row.get('Author Keywords', row.get('DE', ''))).lower()
    keywords_plus = str(row.get('Keywords Plus', row.get('ID', ''))).lower()
    full_text = ' '.join([title, abstract, author_keywords, keywords_plus])
    if any(keyword in full_text for keyword in exclusion_keywords):
        return 'Exclude (제외연구)'
    if any(keyword in full_text for keyword in inclusion_keywords):
        return 'Include (관련연구)'
    return 'Review (검토필요)'

def preprocess_keywords(row, stop_words, lemmatizer):
    if row['Classification'] == 'Include (관련연구)':
        author_keywords = str(row.get('Author Keywords', row.get('DE', ''))).lower()
        keywords_plus = str(row.get('Keywords Plus', row.get('ID', ''))).lower()
        all_keywords_str = author_keywords + ';' + keywords_plus
        all_keywords = all_keywords_str.split(';')
        cleaned_keywords = set()
        for keyword in all_keywords:
            keyword = keyword.strip().replace('-', ' ')
            keyword = re.sub(r'[^a-z\s]', '', keyword)
            final_words = [lemmatizer.lemmatize(w) for w in keyword.split() if w not in stop_words and len(w) > 2]
            if final_words:
                cleaned_keywords.add(" ".join(final_words))
        return '; '.join(sorted(list(cleaned_keywords)))
    return None

# --- 카드 스타일을 위한 CSS ---
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
        border: 1px solid #e6e6e6; border-radius: 10px; padding: 25px; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.05); background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- Streamlit UI 및 실행 로직 ---
st.title("WOS 데이터 분석 대시보드")
st.caption("WOS Data Analysis Dashboard")

uploaded_file = st.file_uploader(
    "WoS Raw Data 파일(CSV/TXT)을 업로드하세요 / Upload your WoS Raw Data file (CSV/TXT)", 
    type=['csv', 'txt']
)

# --- 파일 업로드 시 자동 분석 실행 ---
if uploaded_file is not None:
    df_raw = load_data(uploaded_file)
    
    if df_raw is None:
        st.error("파일을 읽을 수 없습니다. 파일 형식을 확인해주세요.")
        st.stop()

    with st.spinner("파일을 분석 중입니다... / Analyzing file..."):
        # 원본 데이터프레임 복사하여 분석 진행
        df = df_raw.copy()

        # 1. 논문 분류 실행
        df['Classification'] = df.apply(classify_article, axis=1)
        
        # 2. 키워드 전처리 실행
        stop_words = set(stopwords.words('english'))
        custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article', 'articles', 'based', 'using'}
        stop_words.update(custom_stop_words)
        lemmatizer = WordNetLemmatizer()
        df['Cleaned_Keywords'] = df.apply(lambda row: preprocess_keywords(row, stop_words, lemmatizer), axis=1)

    st.success("✅ 분석 완료! / Analysis Complete!")
    
    # --- 결과 표시 ---
    st.markdown("---")
    with st.container():
        st.subheader("1. 분석 결과 요약")
        st.caption("Analysis Summary")
        
        classification_summary = df['Classification'].value_counts()
        
        # '관련연구'에서 정제된 키워드 수 계산
        all_cleaned_keywords = []
        df[df['Classification'] == 'Include (관련연구)']['Cleaned_Keywords'].dropna().apply(lambda x: all_cleaned_keywords.extend(x.split(';') if isinstance(x, str) else []))
        all_cleaned_keywords = [kw.strip() for kw in all_cleaned_keywords if kw.strip()]
        num_unique_keywords = len(set(all_cleaned_keywords))

        # 2x2 그리드로 요약 정보 표시
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        
        with col1:
            st.metric("▶️ 관련연구 / Include", classification_summary.get('Include (관련연구)', 0))
        with col2:
            st.metric("▶️ 제외연구 / Exclude", classification_summary.get('Exclude (제외연구)', 0))
        with col3:
            st.metric("▶️ 검토필요 / Review", classification_summary.get('Review (검토필요)', 0))
        with col4:
            st.metric("▶️ 정제된 키워드 수 / Unique Keywords", num_unique_keywords)


    st.markdown("---")
    with st.container():
        st.subheader("2. '관련연구' 핵심 키워드")
        st.caption("Core Keywords from 'Include' Group (Top 20)")
        
        keyword_counts = Counter(all_cleaned_keywords)
        
        if keyword_counts:
            top_keywords_df = pd.DataFrame(keyword_counts.most_common(20), columns=['Keyword', 'Frequency'])
            
            chart = alt.Chart(top_keywords_df).mark_bar(
                cornerRadius=3, height=20 
            ).encode(
                x=alt.X('Frequency:Q', title='빈도 (Frequency)'),
                y=alt.Y('Keyword:N', title='키워드 (Keyword)', sort='-x'),
                color=alt.value('#4F8BFF'), 
                tooltip=['Keyword', 'Frequency']
            ).properties(
                title='핵심 키워드 상위 20개 (Top 20 Core Keywords)'
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("'관련연구'로 분류된 데이터에서 키워드를 찾을 수 없습니다.")

    # --- 다운로드 버튼 ---
    st.markdown("---")
    @st.cache_data
    def convert_df_to_csv(df_to_convert):
        return df_to_convert.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

    csv_data = convert_df_to_csv(df)
    
    st.download_button(
       label="📥 처리된 전체 파일 다운로드 / Download Processed File (CSV)",
       data=csv_data,
       file_name="wos_processed_data.csv",
       mime="text/csv",
    )
