import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import altair as alt

# --- 페이지 설정 ---
st.set_page_config(page_title="WOS Analysis Dashboard", layout="wide")

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

    column_mapping = {
        'Authors': 'AU', 'AU': 'AU', 'Article Title': 'TI', 'TI': 'TI', 'Source Title': 'SO', 'SO': 'SO',
        'Author Keywords': 'DE', 'DE': 'DE', 'Keywords Plus': 'ID', 'ID': 'ID', 'Abstract': 'AB', 'AB': 'AB',
        'Cited References': 'CR', 'CR': 'CR', 'Publication Year': 'PY', 'PY': 'PY', 'Times Cited, All Databases': 'TC', 'TC': 'TC'
    }
    df = df_raw.copy()
    rename_dict = {col: standard_col for col, standard_col in column_mapping.items() if col in df.columns}
    df.rename(columns=rename_dict, inplace=True)

    if st.button("분석 및 변환 시작 / Start Analysis & Conversion"):
        with st.spinner("분석 중... / Analyzing..."):
            
            # 1. 논문 분류
            df['Classification'] = df.apply(classify_article, axis=1)
            
            # 2. '관련연구' 그룹 키워드 전처리
            stop_words = set(stopwords.words('english'))
            custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article'}
            stop_words.update(custom_stop_words)
            lemmatizer = WordNetLemmatizer()
            include_mask = df['Classification'] == 'Include (관련연구)'
            if 'DE' in df.columns:
                df.loc[include_mask, 'DE_cleaned'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))
            if 'ID' in df.columns:
                df.loc[include_mask, 'ID_cleaned'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))

            st.success("✅ 분석 및 변환 완료! / Process Complete!")

            # --- 3. 결과 요약 및 시각화 (복원된 부분) ---
            st.subheader("분석 결과 요약 / Analysis Summary")
            col1, col2 = st.columns([1, 2])

            with col1:
                st.write("#### 논문 분류 결과")
                classification_counts = df['Classification'].value_counts().reset_index()
                classification_counts.columns = ['Classification', 'Count']
                st.dataframe(classification_counts)

            with col2:
                chart = alt.Chart(classification_counts).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Classification", type="nominal", title="분류"),
                    tooltip=['Classification', 'Count']
                ).properties(
                    title='논문 분류 분포'
                )
                st.altair_chart(chart, use_container_width=True)

            st.markdown("---")
            st.write("#### '관련연구(Include)' 주요 키워드 분석")
            
            # 키워드 집계
            all_keywords = []
            if 'DE_cleaned' in df.columns:
                all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'DE_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
            if 'ID_cleaned' in df.columns:
                all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'ID_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
            
            if all_keywords:
                keyword_counts = Counter(all_keywords)
                top_n = 20
                top_keywords = keyword_counts.most_common(top_n)
                df_keywords = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])

                keyword_chart = alt.Chart(df_keywords).mark_bar().encode(
                    x=alt.X('Frequency:Q', title='빈도'),
                    y=alt.Y('Keyword:N', title='키워드', sort='-x'),
                    tooltip=['Keyword', 'Frequency']
                ).properties(
                    title=f'상위 {top_n} 키워드 빈도'
                )
                st.altair_chart(keyword_chart, use_container_width=True)
            else:
                st.warning("'관련연구'로 분류된 논문에서 유효한 키워드를 찾을 수 없습니다.")


            # --- 4. 최종 출력 파일 생성 ---
            st.markdown("---")
            st.subheader("데이터 다운로드 / Download Data")
            df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
            
            # 원본 DE, ID 필드로 복원 (전처리된 DE_cleaned, ID_cleaned는 출력 파일에 미포함)
            if 'DE' in df.columns:
                df.loc[include_mask, 'DE'] = df.loc[include_mask, 'DE_cleaned']
            if 'ID' in df.columns:
                 df.loc[include_mask, 'ID'] = df.loc[include_mask, 'ID_cleaned']

            final_columns = ['AU', 'TI', 'SO', 'PY', 'DE', 'ID', 'AB', 'CR']
            existing_final_columns = [col for col in final_columns if col in df_final.columns]
            df_final_output = df_final[existing_final_columns]
            
            st.metric("최종 분석 대상 논문 수 (Include + Review)", len(df_final))
            st.dataframe(df_final_output.head(10))

            @st.cache_data
            def convert_df_to_text(df_to_convert):
                return df_to_convert.to_csv(sep='\t', index=False, encoding='utf-8-sig').encode('utf-8-sig')

            text_data = convert_df_to_text(df_final_output)
            st.download_button(
                label="📥 최종 파일 다운로드 (.txt for SciMAT)",
                data=text_data,
                file_name="wos_processed_for_scimat.txt",
                mime="text/plain",
            )
