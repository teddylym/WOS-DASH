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
st.set_page_config(page_title="WOS Prep", page_icon="⚙️", layout="centered")

# --- NLTK 리소스 다운로드 ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 데이터 로드 및 처리 함수들 (이전과 동일) ---
def load_data(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1', 'cp949']
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(io.StringIO(file_bytes.decode(encoding)), sep='\t', lineterminator='\n')
            if df.shape[1] > 1: return df
        except Exception: continue
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(io.StringIO(file_bytes.decode(encoding)))
            if df.shape[1] > 1: return df
        except Exception: continue
    return None

def normalize_keyword(keyword):
    normalization_dict = {'ml': 'machine learning', 'ai': 'artificial intelligence', 'live streaming': 'streaming',
                          'livestreaming': 'streaming', 'live stream': 'streaming', 'user behavior': 'consumer behavior',
                          'user engagement': 'consumer engagement', 'pls-sem': 'sem', 'structural equation modeling': 'sem'}
    return normalization_dict.get(keyword, keyword)

def clean_keyword_string(keywords_str, stop_words, lemmatizer):
    if pd.isna(keywords_str): return ""
    cleaned_keywords = set()
    for keyword in str(keywords_str).lower().split(';'):
        keyword = keyword.strip().replace('-', ' '); keyword = re.sub(r'[^a-z\s]', '', keyword)
        words = [lemmatizer.lemmatize(w) for w in keyword.split() if w not in stop_words and len(w) > 2]
        if not words: continue
        normalized_keyword = normalize_keyword(" ".join(words)); cleaned_keywords.add(normalized_keyword)
    return '; '.join(sorted(list(cleaned_keywords)))

def classify_article(row):
    inclusion_keywords = ['user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'behavior', 'experience', 'engagement', 'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 'society', 'commerce', 'marketing', 'business', 'brand', 'purchase', 'monetization', 'education', 'learning', 'influencer']
    exclusion_keywords = ['protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer', 'packet dropping', 'bandwidth', 'fec', 'arq', 'goodput', 'sensor data', 'geoscience', 'environmental data', 'wlan', 'ofdm', 'error correction', 'tcp', 'udp', 'network traffic']
    text_to_check = ' '.join(str(row.get(c, '')).lower() for c in ['TI', 'SO', 'DE', 'ID', 'AB'])
    if any(keyword in text_to_check for keyword in exclusion_keywords): return 'Exclude (제외연구)'
    if any(keyword in text_to_check for keyword in inclusion_keywords): return 'Include (관련연구)'
    return 'Review (검토필요)'

def convert_df_to_scimat_format(df_to_convert):
    wos_field_order = [
        'FN', 'VR', 'PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB', 'C1', 'C3', 'RP', 'EM', 'RI',
        'OI', 'FU', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA', 'SN', 'EI', 'J9', 'JI',
        'PD', 'PY', 'VL', 'IS', 'BP', 'EP', 'AR', 'DI', 'PG', 'WC', 'SC', 'GA', 'UT', 'PM', 'OA', 'EA', 'DA'
    ]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'C3', 'CR']
    all_records_text = []
    for _, row in df_to_convert.iterrows():
        record_lines = []
        for tag in wos_field_order:
            if tag in row.index and pd.notna(row[tag]) and str(row[tag]).strip() != '':
                value = str(row[tag])
                if tag in multi_line_fields:
                    items = [item.strip() for item in value.split(';') if item.strip()]
                    if items:
                        record_lines.append(f"{tag} {items[0]}")
                        record_lines.extend([f"   {item}" for item in items[1:]])
                else:
                    record_lines.append(f"{tag} {value}")
        if record_lines:
            record_lines.append("ER")
            all_records_text.append("\n".join(record_lines))
    header = "FN Clarivate Analytics Web of Science\nVR 1.0"
    final_content = header + "\n" + "\n".join(all_records_text)
    return final_content.encode('utf-8')

# --- Streamlit UI 및 실행 로직 ---

# --- 헤더 섹션 ---
st.title("⚙️ WOS Prep")
st.subheader("Web of Science 데이터 전처리 및 분석 도구")
st.caption("Streamlining the preparation of your bibliometric data for analysis.")
st.markdown("---")

# --- 파일 업로드 전 초기 화면 ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False

# 파일 업로더
uploaded_file = st.file_uploader(
    "WOS에서 'Tab-delimited' 형식으로 다운로드한 TXT 또는 CSV 파일을 여기에 업로드하세요.",
    type=['csv', 'txt']
)

# 파일이 업로드 되면 즉시 분석 시작
if uploaded_file is not None and not st.session_state.analysis_done:
    st.session_state.analysis_done = True # 중복 실행 방지
    # 분석 로직을 이 블록 안으로 이동
    with st.spinner("파일을 처리하고 있습니다. 잠시만 기다려주세요..."):
        df = load_data(uploaded_file)
        if df is None:
            st.error("파일을 읽을 수 없습니다. Web of Science에서 다운로드한 'Tab-delimited' 또는 'Plain Text' 형식의 파일이 맞는지 확인해주세요.")
            st.stop()

        df.columns = [col.upper().strip() for col in df.columns]
        column_mapping = {'AUTHORS': 'AU', 'ARTICLE TITLE': 'TI', 'SOURCE TITLE': 'SO', 'AUTHOR KEYWORDS': 'DE', 'KEYWORDS PLUS': 'ID', 'ABSTRACT': 'AB', 'CITED REFERENCES': 'CR', 'PUBLICATION YEAR': 'PY', 'TIMES CITED, ALL DATABASES': 'TC'}
        df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)
        
        # 원본 데이터 및 처리된 데이터 저장
        st.session_state.original_df = df.copy()
        
        if 'DE' in df.columns: df['DE_Original'] = df['DE']
        if 'ID' in df.columns: df['ID_Original'] = df['ID']

        df['Classification'] = df.apply(classify_article, axis=1)

        df_processed = df.copy()
        stop_words, lemmatizer = set(stopwords.words('english')), WordNetLemmatizer()
        custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article'}
        stop_words.update(custom_stop_words)
        include_mask = df_processed['Classification'] == 'Include (관련연구)'
        if 'DE' in df_processed.columns: df_processed.loc[include_mask, 'DE'] = df_processed.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))
        if 'ID' in df_processed.columns: df_processed.loc[include_mask, 'ID'] = df_processed.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))
        
        st.session_state.processed_df = df_processed

# --- 파일 업로드 전/후 공통 표시 영역 ---
if not st.session_state.analysis_done:
    st.markdown(
        """
        **WOS Prep에 오신 것을 환영합니다.**

        이 도구는 Web of Science(WOS)에서 다운로드한 서지 데이터를 **분석 가능한 형태로 신속하게 정제하고 분류**하기 위해 설계되었습니다.
        복잡한 데이터 준비 과정을 자동화하여 연구 생산성을 높이고, **SciMAT과 같은 전문 분석 도구와의 완벽한 호환성**을 제공합니다.
        """
    )

# --- 분석 완료 후 결과 표시 ---
if st.session_state.analysis_done:
    st.success("✅ 분석 및 변환 완료!")
    st.markdown("#### 단계 2: 분석 결과 확인 및 다운로드")

    df = st.session_state.original_df
    df_processed = st.session_state.processed_df
    include_mask = df_processed['Classification'] == 'Include (관련연구)'

    st.subheader("분석 결과 요약")
    
    # 수정: 논문 분류 결과와 그래프를 수직으로 배치
    st.write("##### 논문 분류 결과")
    classification_counts = df['Classification'].value_counts().reset_index().rename(columns={'index': 'Classification', 'Classification': 'Count'})
    st.dataframe(classification_counts, use_container_width=True)

    # 수정: Altair 차트 중앙에 전체 논문 수 추가
    total_papers = len(df)
    base = alt.Chart(classification_counts).encode(
        theta=alt.Theta(field="Count", type="quantitative", stack=True),
        color=alt.Color(field="Classification", type="nominal", title="분류"),
        tooltip=['Classification', 'Count']
    )
    pie = base.mark_arc(outerRadius=120, innerRadius=70)
    text = alt.Chart(pd.DataFrame({'total': [total_papers]})).mark_text(
        align='center', baseline='middle', fontSize=24, fontWeight='bold', color="#4A4A4A"
    ).encode(text='total:N').properties(title=alt.TitleParams(text="논문 분류 분포", anchor='middle'))
    st.altair_chart(pie + text, use_container_width=True)
    
    st.markdown("---")

    st.write("##### '관련연구(Include)' 주요 키워드 (전처리 후)")
    all_keywords = []
    if 'DE' in df_processed.columns: all_keywords.extend([kw.strip() for text in df_processed.loc[include_mask, 'DE'].dropna() for kw in text.split(';') if kw.strip()])
    if 'ID' in df_processed.columns: all_keywords.extend([kw.strip() for text in df_processed.loc[include_mask, 'ID'].dropna() for kw in text.split(';') if kw.strip()])
    if all_keywords:
        df_keywords = pd.DataFrame(Counter(all_keywords).most_common(20), columns=['Keyword', 'Frequency'])
        keyword_chart = alt.Chart(df_keywords).mark_bar().encode(x=alt.X('Frequency:Q', title='빈도'), y=alt.Y('Keyword:N', title='키워드', sort='-x')).properties(title='상위 20 키워드 빈도')
        st.altair_chart(keyword_chart, use_container_width=True)
    
    st.markdown("---")

    # 수정: st.expander 제거하고 항상 보이도록 변경
    st.write("##### 🔬 정규화 전/후 키워드 비교 (상위 5개 관련 연구)")
    compare_cols = []
    if 'DE_Original' in df_processed.columns: compare_cols.extend(['DE_Original', 'DE'])
    if 'ID_Original' in df_processed.columns: compare_cols.extend(['ID_Original', 'ID'])
    if compare_cols:
        st.dataframe(df_processed.loc[include_mask, compare_cols].head(5), use_container_width=True)
    else:
        st.info("비교할 키워드 필드가 없습니다.")

    # 수정: 다운로드 버튼을 최하단으로 이동 및 수직 배치
    st.markdown("---")
    st.subheader("데이터 다운로드")
    
    st.write("**1. SciMAT 분석용 파일 (권장)**")
    st.caption("Scimat의 모든 기능을 사용하려면 원본 데이터를 다운로드하세요.")
    df_for_scimat = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
    scimat_output_df = df_for_scimat.drop(columns=[col for col in ['DE_Original', 'ID_Original', 'Classification'] if col in df_for_scimat.columns])
    text_data_scimat = convert_df_to_scimat_format(scimat_output_df)
    st.download_button(label="📥 **원본 파일** 다운로드 (.txt for SciMAT)", data=text_data_scimat, file_name="wos_original_for_scimat.txt", mime="text/plain", key="scimat_download", use_container_width=True)

    st.write("") # 간격 추가

    st.write("**2. 전처리 완료 파일**")
    st.caption("키워드 정제/정규화가 완료된 데이터입니다. 외부 시각화에 사용할 수 있습니다.")
    df_for_viz = df_processed[df_processed['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
    viz_output_df = df_for_viz.drop(columns=[col for col in ['DE_Original', 'ID_Original', 'Classification'] if col in df_for_viz.columns])
    text_data_viz = convert_df_to_scimat_format(viz_output_df)
    st.download_button(label="📥 **전처리된 파일** 다운로드 (.txt)", data=text_data_viz, file_name="wos_preprocessed.txt", mime="text/plain", key="preprocessed_download", use_container_width=True)

# --- 수정: 앱 하단에 개발자 정보 및 버전 표기 ---
st.markdown("---")
st.caption("Developed by 임태경, 한양대학교 기술경영전문대학원 | Version 1.0.0")
