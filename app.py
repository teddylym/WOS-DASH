import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
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

# --- 데이터 로드 함수 (수정: 안정적인 버전으로 복원) ---
@st.cache_data
def load_data(uploaded_file):
    encodings_to_try = ['utf-8', 'latin1', 'cp949', 'utf-8-sig']
    df = None
    # 1. 탭으로 구분된 파일(가장 일반적인 WoS 형식) 먼저 시도
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df_try = pd.read_csv(uploaded_file, sep='\t', encoding=encoding)
            if df_try.shape[1] > 1:
                return df_try
        except Exception:
            continue
    # 2. 콤마로 구분된 CSV 파일 시도
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df_try = pd.read_csv(uploaded_file, encoding=encoding)
            if df_try.shape[1] > 1:
                return df_try
        except Exception:
            continue
    return None

# --- 핵심 기능 함수 ---
def classify_article(row):
    # 'TI', 'SO' 등 표준화된 태그 사용
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
    if not isinstance(keywords_str, str): return ""
    all_keywords = keywords_str.lower().split(';')
    cleaned_keywords = set()
    for keyword in all_keywords:
        keyword = keyword.strip().replace('-', ' ')
        keyword = re.sub(r'[^a-z\s]', '', keyword)
        final_words = [lemmatizer.lemmatize(w) for w in keyword.split() if w not in stop_words and len(w) > 2]
        if final_words: cleaned_keywords.add(" ".join(final_words))
    return '; '.join(sorted(list(cleaned_keywords)))

# --- SCIMAT 형식으로 변환하는 함수 ---
@st.cache_data
def convert_df_to_scimat_format(df_to_convert):
    wos_field_order = [
        'FN', 'VR', 'PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB', 'C1', 'RP',
        'EM', 'FU', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA', 'SN',
        'EI', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'BP', 'EP', 'DI', 'PG', 'WC', 'SC',
        'GA', 'UT', 'PM', 'DA'
    ]
    file_content = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'CR']
    for _, row in df_to_convert.iterrows():
        sorted_tags = [tag for tag in wos_field_order if tag in row.index and pd.notna(row[tag])]
        for tag in sorted_tags:
            value = row[tag]
            if not value: continue
            if not isinstance(value, str): value = str(value)
            if tag in multi_line_fields:
                items = [item.strip() for item in value.split(';')]
                if items:
                    file_content.append(f"{tag} {items[0]}")
                    for item in items[1:]: file_content.append(f"   {item}")
            else:
                file_content.append(f"{tag} {value}")
        file_content.append("ER\n")
    if file_content[-1] == "ER\n": file_content[-1] = "ER"
    return "\n".join(file_content).encode('utf-8-sig')

# --- Streamlit UI 및 실행 로직 ---
st.title("WOS 데이터 분석 및 정제 도구")
st.caption("WOS Data Classifier & Preprocessor")
uploaded_file = st.file_uploader("WoS Raw Data 파일(CSV/TXT)을 업로드하세요", type=['csv', 'txt'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("파일을 읽을 수 없습니다. Web of Science에서 다운로드한 'Tab-delimited' 또는 'Plain Text' 형식의 파일이 맞는지 확인해주세요.")
        st.stop()
    
    # 원본 파일의 컬럼명을 대문자 표준 태그로 일괄 변환
    df.columns = [col.upper() for col in df.columns]
    column_mapping = {
        'AUTHORS': 'AU', 'ARTICLE TITLE': 'TI', 'SOURCE TITLE': 'SO', 'AUTHOR KEYWORDS': 'DE',
        'KEYWORDS PLUS': 'ID', 'ABSTRACT': 'AB', 'CITED REFERENCES': 'CR', 'PUBLICATION YEAR': 'PY',
        'TIMES CITED, ALL DATABASES': 'TC', 'Z9': 'TC'
    }
    # df.columns에 있는 이름만 골라 rename
    df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)


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

        st.subheader("분석 결과 요약 / Analysis Summary")
        st.write("##### 논문 분류 결과")
        classification_counts = df['Classification'].value_counts().reset_index()
        classification_counts.columns = ['Classification', 'Count']
        st.dataframe(classification_counts)
        chart = alt.Chart(classification_counts).mark_arc(innerRadius=50).encode(theta=alt.Theta(field="Count", type="quantitative"), color=alt.Color(field="Classification", type="nominal", title="분류"), tooltip=['Classification', 'Count']).properties(title='논문 분류 분포')
        st.altair_chart(chart, use_container_width=True)
        st.markdown("---")
        st.write("##### '관련연구(Include)' 주요 키워드 분석")
        all_keywords = []
        if 'DE_cleaned' in df.columns: all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'DE_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        if 'ID_cleaned' in df.columns: all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'ID_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        if all_keywords:
            keyword_counts = Counter(all_keywords)
            top_n = 20; top_keywords = keyword_counts.most_common(top_n); df_keywords = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])
            keyword_chart = alt.Chart(df_keywords).mark_bar().encode(x=alt.X('Frequency:Q', title='빈도'), y=alt.Y('Keyword:N', title='키워드', sort='-x'), tooltip=['Keyword', 'Frequency']).properties(title=f'상위 {top_n} 키워드 빈도')
            st.altair_chart(keyword_chart, use_container_width=True)
        else: st.warning("'관련연구'로 분류된 논문에서 유효한 키워드를 찾을 수 없습니다.")

        st.markdown("---")
        st.subheader("데이터 다운로드 / Download Data")
        df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        if 'DE_cleaned' in df_final.columns: df_final['DE'] = df_final['DE_cleaned']
        if 'ID_cleaned' in df_final.columns: df_final['ID'] = df_final['ID_cleaned']
        cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned']
        df_final_output = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns])
        st.metric("최종 분석 대상 논문 수 (Include + Review)", len(df_final_output))
        st.dataframe(df_final_output.head(10))
        text_data = convert_df_to_scimat_format(df_final_output)
        st.download_button(label="📥 최종 파일 다운로드 (.txt for SciMAT)", data=text_data, file_name="wos_processed_for_scimat.txt", mime="text/plain")
