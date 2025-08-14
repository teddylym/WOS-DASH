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

# --- 1. [핵심 개선] 개념 정규화 사전 (Thesaurus) ---
# Cobo(2012)의 핵심 원칙인 '개념 단위' 통합을 위한 사용자 사전
@st.cache_data
def get_normalization_map():
    thesaurus = {
        "live commerce": ["live shopping", "social commerce", "livestream shopping", "e-commerce live streaming"],
        "user engagement": ["consumer engagement", "viewer engagement", "audience engagement"],
        "purchase intention": ["purchase intentions", "buying intention"],
        "user experience": ["consumer experience", "viewer experience"],
        "social presence": ["perceived social presence"],
        "influencer marketing": ["influencer", "digital celebrities", "wanghong"],
        "platform technology": ["streaming technology", "platform architecture", "streaming media"],
        "peer-to-peer": ["p2p", "peer to peer"]
    }
    # 빠른 조회를 위한 역방향 맵 생성
    normalization_map = {}
    for standard_term, variations in thesaurus.items():
        for variation in variations:
            normalization_map[variation] = standard_term
    return normalization_map

NORMALIZATION_MAP = get_normalization_map()

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data(uploaded_file):
    # ... (이전과 동일한 인코딩 처리 로직) ...
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
    # ... (기존과 동일한 분류 로직) ...
    inclusion_keywords = ['user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'behavior', 'experience', 'engagement', 'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 'society', 'commerce', 'marketing', 'business', 'brand', 'purchase', 'monetization', 'education', 'learning', 'influencer']
    exclusion_keywords = ['protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer', 'packet dropping', 'bandwidth', 'fec', 'arq', 'goodput', 'sensor data', 'geoscience', 'environmental data', 'wlan', 'ofdm', 'error correction', 'tcp', 'udp', 'network traffic']
    title = str(row.get('Article Title', row.get('TI', ''))).lower()
    abstract = str(row.get('Abstract', row.get('AB', ''))).lower()
    author_keywords = str(row.get('Author Keywords', row.get('DE', ''))).lower()
    keywords_plus = str(row.get('Keywords Plus', row.get('ID', ''))).lower()
    full_text = ' '.join([title, abstract, author_keywords, keywords_plus])
    if any(keyword in full_text for keyword in exclusion_keywords): return 'Exclude (제외연구)'
    if any(keyword in full_text for keyword in inclusion_keywords): return 'Include (관련연구)'
    return 'Review (검토필요)'

def preprocess_keywords(row, stop_words, lemmatizer, normalization_map):
    if row['Classification'] == 'Include (관련연구)':
        author_keywords = str(row.get('Author Keywords', row.get('DE', ''))).lower()
        keywords_plus = str(row.get('Keywords Plus', row.get('ID', ''))).lower()
        all_keywords_str = author_keywords + ';' + keywords_plus
        all_keywords = all_keywords_str.split(';')
        
        cleaned_keywords = set()
        for keyword in all_keywords:
            keyword = keyword.strip()
            if not keyword: continue

            # 1단계: 개념 정규화 (Normalization)
            normalized_keyword = normalization_map.get(keyword, keyword)
            
            # 2단계: 문자 정제 및 표제어 추출 (Cleaning & Lemmatization)
            normalized_keyword = normalized_keyword.replace('-', ' ')
            normalized_keyword = re.sub(r'[^a-z\s]', '', normalized_keyword)
            
            final_words = [lemmatizer.lemmatize(w) for w in normalized_keyword.split() if w not in stop_words and len(w) > 2]
            if final_words:
                cleaned_keywords.add(" ".join(final_words))
        
        return '; '.join(sorted(list(cleaned_keywords)))
    return None

# --- 카드 스타일 CSS ---
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
        border: 1px solid #e6e6e6; border-radius: 10px; padding: 25px; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.05); background-color: #ffffff;
    }
    .recommendation-box {
        border: 1px solid #cce5ff; border-radius: 10px; padding: 20px;
        background-color: #f8f9fa; margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Streamlit UI 및 실행 로직 ---
st.title("WOS 데이터 분석 및 정제 도구")
st.caption("WOS Data Classifier & Preprocessor")

uploaded_file = st.file_uploader(
    "WoS Raw Data 파일(CSV/TXT)을 업로드하세요", 
    type=['csv', 'txt']
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("파일을 읽을 수 없습니다. 파일 형식을 확인해주세요.")
        st.stop()
    
    if st.button("분석 시작 / Start Analysis"):
        with st.spinner("분석 중... / Analyzing..."):
            
            df['Classification'] = df.apply(classify_article, axis=1)
            
            stop_words = set(stopwords.words('english'))
            custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article'}
            stop_words.update(custom_stop_words)
            lemmatizer = WordNetLemmatizer()
            df['Cleaned_Keywords'] = df.apply(lambda row: preprocess_keywords(row, stop_words, lemmatizer, NORMALIZATION_MAP), axis=1)

            st.success("✅ 분석 완료! / Analysis Complete!")
            
            # --- 결과 표시 ---
            st.markdown("---")
            with st.container():
                st.subheader("1. 1차 분류 결과 요약")
                st.caption("Initial Classification Summary")
                classification_summary = df['Classification'].value_counts()
                st.metric("▶️ 관련연구 (Include)", classification_summary.get('Include (관련연구)', 0))
                st.metric("▶️ 제외연구 (Exclude)", classification_summary.get('Exclude (제외연구)', 0))
                st.metric("▶️ 검토필요 (Review)", classification_summary.get('Review (검토필요)', 0))

            st.markdown("---")
            with st.container():
                st.subheader("2. 정규화된 핵심 키워드 분석")
                st.caption("Normalized Core Keywords Analysis (Top 20)")
                
                all_cleaned_keywords = []
                df[df['Classification'] == 'Include (관련연구)']['Cleaned_Keywords'].dropna().apply(lambda x: all_cleaned_keywords.extend(x.split(';') if isinstance(x, str) else []))
                all_cleaned_keywords = [kw.strip() for kw in all_cleaned_keywords if kw.strip()]
                keyword_counts = Counter(all_cleaned_keywords)
                
                if keyword_counts:
                    top_keywords_df = pd.DataFrame(keyword_counts.most_common(20), columns=['Keyword', 'Frequency'])
                    chart = alt.Chart(top_keywords_df).mark_bar(cornerRadius=3, height=20).encode(
                        x=alt.X('Frequency:Q', title='빈도 (Frequency)'),
                        y=alt.Y('Keyword:N', title='키워드 (Keyword)', sort='-x'),
                        color=alt.value('#4F8BFF'), 
                        tooltip=['Keyword', 'Frequency']
                    ).properties(title='핵심 개념 상위 20개 (Top 20 Core Concepts)')
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.write("'관련연구'에서 키워드를 찾을 수 없습니다.")

            # --- 3. [핵심 개선] 방법론적 제언 ---
            st.markdown("---")
            with st.container():
                st.subheader("3. 다음 분석 단계를 위한 제언")
                st.caption("Recommendations for Next Analysis Steps (based on Cobo et al., 2012)")
                st.markdown("""
                <div class="recommendation-box">
                <h4>학술적 완성도를 높이기 위한 2가지 핵심 전략:</h4>
                <ol>
                    <li>
                        <strong>'관계의 강도' 측정 (Measuring Relational Strength):</strong>
                        <p>VOSviewer 또는 SciMAT 분석 시, 단순 동시출현 빈도(Co-occurrence) 대신 <strong>'Association Strength'</strong> 또는 <strong>'Equivalence Index'</strong>를 정규화(Normalization) 방식으로 사용하십시오. 이는 두 개념이 얼마나 독점적으로 강하게 연결되어 있는지 보여주어, 분석 결과의 신뢰도를 크게 높입니다.</p>
                    </li>
                    <li>
                        <strong>'클러스터 단위' 연구 제외 (Cluster-based Exclusion):</strong>
                        <p>현재의 '제외연구' 분류는 효율적인 1차 필터링입니다. 더 높은 객관성을 위해, <strong>'관련연구'와 '검토필요' 그룹 전체를 대상</strong>으로 VOSviewer에서 예비 클러스터링을 먼저 수행하십시오. 그 결과 명확하게 분리되는 '순수 네트워크 기술' 클러스터가 있다면, "데이터가 보여주는 구조에 근거하여 해당 클러스터 전체를 최종 분석에서 제외한다"고 결정할 수 있습니다. 이는 연구의 경계를 설정하는 가장 객관적이고 방어하기 용이한 방법입니다.</p>
                    </li>
                </ol>
                </div>
                """, unsafe_allow_html=True)

            # --- 다운로드 버튼 ---
            st.markdown("---")
            @st.cache_data
            def convert_df_to_csv(df_to_convert):
                return df_to_convert.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

            csv_data = convert_df_to_csv(df)
            st.download_button(
               label="📥 처리된 전체 파일 다운로드 (CSV)",
               data=csv_data,
               file_name="wos_processed_data.csv",
               mime="text/csv",
            )
