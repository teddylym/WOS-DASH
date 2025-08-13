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

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data(uploaded_file):
    encodings_to_try = ['utf-8', 'latin1', 'cp949', 'utf-8-sig']
    df = None
    # WoS Plain text file은 'PT'로 시작하는 레코드들로 구성됨
    # 이를 먼저 체크하여 빠르게 파일을 읽음
    try:
        uploaded_file.seek(0)
        content = uploaded_file.read().decode('utf-8-sig')
        if content.strip().startswith('FN') or content.strip().startswith('PT'):
            # 파일 내용을 레코드 단위로 분할
            records_str = content.strip().split('\nER\n')
            all_records = []
            for record_str in records_str:
                if not record_str.strip(): continue
                record_data = {}
                current_tag = ''
                for line in record_str.split('\n'):
                    if len(line) > 2 and line[2] == ' ':
                        current_tag = line[:2]
                        # 다중 값 필드 (예: AU, CR) 처리를 위해 리스트로 저장
                        if current_tag not in record_data:
                            record_data[current_tag] = []
                        record_data[current_tag].append(line[3:])
                    elif line.startswith('   '): # 들여쓰기 된 라인
                        if current_tag in record_data:
                            record_data[current_tag].append(line[3:])
                # 리스트를 세미콜론으로 합쳐서 DataFrame에 저장
                for tag, values in record_data.items():
                    record_data[tag] = '; '.join(values)
                all_records.append(record_data)
            df = pd.DataFrame(all_records)
            # 파일 끝에 ER이 없는 경우를 처리
            if 'ER' in df.columns:
                 df = df.drop(columns=['ER'])
            return df
    except Exception as e:
        st.warning(f"WoS 형식을 읽는 중 오류 발생: {e}. 일반 CSV/TSV 읽기를 시도합니다.")

    # 일반 CSV/TSV 파일 읽기 시도
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df_try = pd.read_csv(uploaded_file, sep='\t', encoding=encoding)
            if df_try.shape[1] > 1: return df_try
        except Exception: continue
    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)
            df_try = pd.read_csv(uploaded_file, encoding=encoding)
            if df_try.shape[1] > 1: return df_try
        except Exception: continue
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
    if not isinstance(keywords_str, str): return ""
    all_keywords = keywords_str.lower().split(';')
    cleaned_keywords = set()
    for keyword in all_keywords:
        keyword = keyword.strip().replace('-', ' ')
        keyword = re.sub(r'[^a-z\s]', '', keyword)
        final_words = [lemmatizer.lemmatize(w) for w in keyword.split() if w not in stop_words and len(w) > 2]
        if final_words: cleaned_keywords.add(" ".join(final_words))
    return '; '.join(sorted(list(cleaned_keywords)))

# --- **수정**: SCIMAT 형식으로 변환하는 새 함수 ---
@st.cache_data
def convert_df_to_scimat_format(df_to_convert):
    # SciMAT이 인식하는 필드 순서 (일반적인 순서)
    wos_field_order = [
        'FN', 'VR', 'PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB',
        'C1', 'RP', 'EM', 'FU', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU',
        'PI', 'PA', 'SN', 'EI', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'BP', 'EP',
        'DI', 'PG', 'WC', 'SC', 'GA', 'UT', 'PM', 'DA'
    ]
    
    file_content = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'CR'] # 여러 줄로 나눠야 할 필드

    for _, row in df_to_convert.iterrows():
        # 정의된 순서대로 필드를 정렬하되, 데이터에 없는 필드는 건너뜀
        sorted_tags = [tag for tag in wos_field_order if tag in row.index and pd.notna(row[tag])]
        
        for tag in sorted_tags:
            value = row[tag]
            if not value: continue

            # 문자열이 아닌 경우 문자열로 변환
            if not isinstance(value, str):
                value = str(value)
            
            # 여러 줄 필드 처리
            if tag in multi_line_fields:
                items = [item.strip() for item in value.split(';')]
                if items:
                    file_content.append(f"{tag} {items[0]}")
                    for item in items[1:]:
                        file_content.append(f"   {item}")
            # 한 줄 필드 처리
            else:
                file_content.append(f"{tag} {value}")

        file_content.append("ER\n") # 레코드 끝

    # 마지막 레코드의 불필요한 공백 제거
    if file_content[-1] == "ER\n":
        file_content[-1] = "ER"
        
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

        # --- 최종 출력 파일 생성 ---
        st.markdown("---")
        st.subheader("데이터 다운로드 / Download Data")
        df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        if 'DE_cleaned' in df_final.columns: df_final['DE'] = df_final['DE_cleaned']
        if 'ID_cleaned' in df_final.columns: df_final['ID'] = df_final['ID_cleaned']
        cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned']; df_final_output = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns])
        st.metric("최종 분석 대상 논문 수 (Include + Review)", len(df_final_output))
        st.dataframe(df_final_output.head(10))

        # **수정**: 새로 만든 SCIMAT 변환 함수를 사용하여 데이터 생성
        text_data = convert_df_to_scimat_format(df_final_output)
        
        st.download_button(label="📥 최종 파일 다운로드 (.txt for SciMAT)", data=text_data, file_name="wos_processed_for_scimat.txt", mime="text/plain")
