import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import altair as alt

# --- 페이지 설정 (세로형을 위한 centered 레이아웃 유지) ---
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
            if df_try.shape[1] < 2 and 'PT' not in df_try.columns:
                 continue
            return df_try
        except Exception:
            continue
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df_try = pd.read_csv(uploaded_file, encoding=encoding)
            if df_try.shape[1] > 2:
                return df_try
        except Exception:
            continue
    return None

# --- 핵심 기능 함수 ---
def classify_article(row):
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

# 수정: 파일 업로드 형식을 CSV와 TXT 모두 허용하도록 변경
uploaded_file = st.file_uploader("WoS Raw Data 파일(CSV/TXT)을 업로드하세요", type=['csv', 'txt'])

if uploaded_file is not None:
    df_raw = load_data(uploaded_file)
    if df_raw is None:
        st.error("파일을 읽을 수 없습니다. Web of Science에서 다운로드한 'Tab-delimited' 또는 'Plain Text' 형식의 파일이 맞는지 확인해주세요.")
        st.stop()

    df_raw.columns = [col.upper() for col in df_raw.columns]
    
    column_mapping = {
        'AUTHORS': 'AU', 'AUTHOR': 'AU', 'AU': 'AU', 'TITLE': 'TI', 'ARTICLE TITLE': 'TI', 'TI': 'TI',
        'SOURCE': 'SO', 'SOURCE TITLE': 'SO', 'SO': 'SO', 'AUTHOR KEYWORDS': 'DE', 'DE': 'DE',
        'KEYWORDS PLUS': 'ID', 'ID': 'ID', 'ABSTRACT': 'AB', 'AB': 'AB', 'CITED REFERENCES': 'CR', 'CR': 'CR',
        'PUBLICATION YEAR': 'PY', 'PY': 'PY', 'TIMES CITED, ALL DATABASES': 'TC', 'TC': 'TC', 'Z9': 'TC'
    }

    df = df_raw.copy()
    rename_dict = {col: standard_col for col, standard_col in column_mapping.items() if col in df.columns}
    df.rename(columns=rename_dict, inplace=True)

    with st.spinner("데이터를 분석하고 있습니다... / Analyzing data..."):
        
        df['Classification'] = df.apply(classify_article, axis=1)
        
        stop_words = set(stopwords.words('english'))
        custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article'}
        stop_words.update(custom_stop_words)
        lemmatizer = WordNetLemmatizer()
        include_mask = df['Classification'] == 'Include (관련연구)'

        if 'DE' in df.columns:
            df['DE_cleaned'] = df['DE'].copy()
            df.loc[include_mask, 'DE_cleaned'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))
        if 'ID' in df.columns:
            df['ID_cleaned'] = df['ID'].copy()
            df.loc[include_mask, 'ID_cleaned'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))

        st.success("✅ 분석 및 변환 완료! / Process Complete!")

        # --- 결과 요약 및 시각화 ---
        st.subheader("분석 결과 요약 / Analysis Summary")
        
        st.write("##### 논문 분류 결과")
        classification_counts = df['Classification'].value_counts().reset_index()
        classification_counts.columns = ['Classification', 'Count']
        st.dataframe(classification_counts)

        chart = alt.Chart(classification_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Classification", type="nominal", title="분류"),
            tooltip=['Classification', 'Count']
        ).properties(
            title='논문 분류 분포'
        )
        st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        st.write("##### '관련연구(Include)' 주요 키워드 분석")
        
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

        # --- 최종 출력 파일 생성 ---
        st.markdown("---")
        st.subheader("데이터 다운로드 / Download Data")
        
        df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        
        if 'DE_cleaned' in df_final.columns:
            df_final['DE'] = df_final['DE_cleaned']
        if 'ID_cleaned' in df_final.columns:
            df_final['ID'] = df_final['ID_cleaned']

        cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned']
        df_final_output = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns])
        
        st.metric("최종 분석 대상 논문 수 (Include + Review)", len(df_final_output))
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
