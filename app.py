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

# --- 커스텀 CSS 스타일 ---
st.markdown("""
<style>
    .main-container { background: #f8f9fa; min-height: 100vh; }
    .metric-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e9ecef; margin-bottom: 16px; transition: all 0.3s ease; }
    .metric-card:hover { box-shadow: 0 4px 20px rgba(0,56,117,0.15); border-color: #003875; }
    .metric-value { font-size: 2.8rem; font-weight: 700; color: #003875; margin: 0; line-height: 1; }
    .metric-label { font-size: 1rem; color: #6c757d; margin: 8px 0 0 0; font-weight: 500; }
    .metric-icon { background: linear-gradient(135deg, #003875, #0056b3); color: white; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin-bottom: 16px; }
    .chart-container { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e9ecef; margin: 16px 0; }
    .chart-title { font-size: 1.2rem; font-weight: 600; color: #212529; margin-bottom: 16px; border-bottom: 2px solid #003875; padding-bottom: 8px; }
    .section-header { background: linear-gradient(135deg, #003875, #0056b3); color: white; padding: 20px 24px; border-radius: 12px; margin: 24px 0 16px 0; box-shadow: 0 4px 16px rgba(0,56,117,0.2); }
    .section-title { font-size: 1.5rem; font-weight: 600; margin: 0; }
    .section-subtitle { font-size: 1rem; opacity: 0.9; margin: 4px 0 0 0; }
    .info-panel { background: #e8f0fe; border: 1px solid #003875; border-radius: 8px; padding: 16px; margin: 16px 0; }
    .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 24px 0; }
    .feature-card { background: white; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e9ecef; transition: all 0.3s ease; }
    .feature-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,56,117,0.15); border-color: #003875; }
    .feature-icon { font-size: 3rem; margin-bottom: 16px; background: linear-gradient(135deg, #003875, #0056b3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .feature-title { font-size: 1.2rem; font-weight: 600; color: #212529; margin-bottom: 8px; }
    .feature-desc { font-size: 0.95rem; color: #6c757d; line-height: 1.5; }
    .upload-zone { background: white; border: 2px dashed #003875; border-radius: 12px; padding: 40px; text-align: center; margin: 20px 0; transition: all 0.3s ease; }
    .upload-zone:hover { background: #f8f9fa; border-color: #0056b3; }
    .progress-indicator { background: linear-gradient(90deg, #003875, #0056b3); height: 4px; border-radius: 2px; margin: 16px 0; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
</style>
""", unsafe_allow_html=True)

# --- NLTK 리소스 다운로드 ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 개념 정규화 사전 ---
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
        "user behavior": ["consumer behavior"]
    }
    reverse_map = {}
    for standard_form, variations in base_map.items():
        for variation in variations:
            reverse_map[variation.strip().lower()] = standard_form
        reverse_map[standard_form.strip().lower()] = standard_form
    return reverse_map
NORMALIZATION_MAP = build_normalization_map()

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data(uploaded_file):
    file_name = uploaded_file.name.lower()
    try:
        if file_name.endswith(('.xls', '.xlsx')):
            return pd.read_excel(uploaded_file, engine=None)
        file_bytes = uploaded_file.getvalue()
        encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1', 'cp949']
        for encoding in encodings_to_try:
            try:
                file_content = file_bytes.decode(encoding)
                df = pd.read_csv(io.StringIO(file_content), sep='\t', lineterminator='\n')
                if df.shape[1] > 1: return df
            except Exception: continue
        for encoding in encodings_to_try:
            try:
                file_content = file_bytes.decode(encoding)
                df = pd.read_csv(io.StringIO(file_content))
                if df.shape[1] > 1: return df
            except Exception: continue
        return None
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        return None

# --- [핵심 수정] 최종 분류 알고리즘 ---
def classify_article(row):
    """오류를 수정한, 맥락 기반의 최종 분류 알고리즘"""
    title = str(row.get('TI', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, author_keywords, keywords_plus, abstract])

    # 1. 키워드 그룹 정의
    strong_inclusion_phrases = [
        'live streaming commerce', 'social commerce', 'livestreaming commerce',
        'purchase intention', 'customer engagement', 'consumer behavior', 'user behavior',
        'influencer marketing', 'brand engagement', 'online shopping', 'e-commerce',
        'viewer engagement', 'user experience', 'social motivations', 'parasocial interaction',
        'virtual gift', 'fan engagement', 'community building', 'travel live streaming'
    ]
    pure_tech_keywords = [
        'protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer',
        'packet dropping', 'bandwidth', 'forward error correction', 'fec', 'arq', 
        'goodput', 'wlan', 'ofdm', 'error correction', 'tcp', 'udp', 'network traffic',
        'p2p', 'peer-to-peer', 'qoe', 'quality of experience', 'bitrate', 'codec', 'encoding',
        'overlay network', 'routing algorithm'
    ]
    social_context_keywords = [
        'user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'experience', 
        'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 
        'society', 'marketing', 'business', 'brand', 'monetization', 'education', 'learning'
    ]
    medical_keywords = ['surgical education', 'medical education', 'surgery', 'clinical learning']

    # 2. 분류 로직 실행
    # 2.1 확실한 포함 규칙: 이 구문이 하나라도 있으면 무조건 '관련연구'
    if any(phrase in full_text for phrase in strong_inclusion_phrases):
        return 'Include (관련연구)'

    # 2.2 확실한 제외 규칙: 의료/수술 교육이 주목적이면 '제외'
    if sum(1 for keyword in medical_keywords if keyword in full_text) >= 2:
        return 'Exclude (제외연구)'

    # 2.3 확실한 제외 규칙: 순수 기술 키워드가 3개 이상 '그리고' 사회/상업적 키워드가 1개 이하일 때만 '제외'
    pure_tech_count = sum(1 for keyword in pure_tech_keywords if f' {keyword} ' in f' {full_text} ')
    social_count = sum(1 for keyword in social_context_keywords if keyword in full_text)
    if pure_tech_count >= 3 and social_count <= 1:
        return 'Exclude (제외연구)'

    # 2.4 제목 규칙: 제목에 'live stream' 또는 'live broadcast'가 포함되면 '관련연구'
    if 'live stream' in title or 'live broadcast' in title:
        return 'Include (관련연구)'

    # 2.5 일반 포함 규칙: 사회/상업적 키워드가 3개 이상이면 '관련연구'
    if social_count >= 3:
        return 'Include (관련연구)'

    # 2.6 그 외 모든 애매한 경우는 '검토필요'
    return 'Review (검토필요)'

# --- 키워드 전처리 함수 ---
def clean_keyword_string(keywords_str, stop_words, lemmatizer, normalization_map):
    if pd.isna(keywords_str) or not isinstance(keywords_str, str): return ""
    all_keywords = keywords_str.split(';')
    cleaned_keywords = set()
    for keyword in all_keywords:
        keyword_clean = keyword.strip().lower()
        if not keyword_clean: continue
        normalized_phrase = normalization_map.get(keyword_clean, keyword_clean)
        normalized_phrase = normalized_phrase.replace('-', ' ').replace('_', ' ')
        normalized_phrase = re.sub(r'[^a-z\s]', '', normalized_phrase)
        words = normalized_phrase.split()
        filtered_words = [lemmatizer.lemmatize(w) for w in words if w and len(w) > 2 and w not in stop_words]
        if filtered_words:
            final_keyword = " ".join(filtered_words)
            cleaned_keywords.add(final_keyword)
    return '; '.join(sorted(list(cleaned_keywords)))

# --- SCIMAT 형식 변환 함수 ---
def convert_df_to_scimat_format(df_to_convert):
    wos_field_order = ['PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB', 'C1', 'C3', 'RP', 'EM', 'RI', 'OI', 'FU', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA', 'SN', 'EI', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'BP', 'EP', 'DI', 'EA', 'PG', 'WC', 'WE', 'SC', 'GA', 'UT', 'PM', 'OA', 'DA']
    file_content = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'C3', 'CR']
    for _, row in df_to_convert.iterrows():
        if len(file_content) > 2: file_content.append("")
        sorted_tags = [tag for tag in wos_field_order if tag in row.index and pd.notna(row[tag])]
        for tag in sorted_tags:
            value = row[tag]
            if pd.isna(value) or not str(value).strip(): continue
            if not isinstance(value, str): value = str(value)
            if tag in multi_line_fields:
                items = [item.strip() for item in value.split(';') if item.strip()]
                if items:
                    file_content.append(f"{tag} {items[0]}")
                    for item in items[1:]: file_content.append(f"  {item}")
            else:
                file_content.append(f"{tag} {value}")
        file_content.append("ER")
    return "\n".join(file_content).encode('utf-8')

# --- 메인 헤더 및 UI ---
st.markdown("""
<div style="position: relative; text-align: center; padding: 2rem 0 3rem 0; background: linear-gradient(135deg, #003875, #0056b3); color: white; border-radius: 16px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,56,117,0.3);">
    <div style="position: absolute; top: 1rem; left: 2rem; color: white;">
        <div style="font-size: 14px; font-weight: 600; margin-bottom: 2px;">HANYANG UNIVERSITY</div>
        <div style="font-size: 12px; opacity: 0.9;">Technology Management Research</div>
    </div>
    <div style="position: absolute; top: 1rem; right: 2rem; text-align: right; color: rgba(255,255,255,0.9); font-size: 0.85rem;">
        <p style="margin: 0;"><strong>Developed by:</strong> 임태경 (Teddy Lym)</p>
    </div>
    <h1 style="font-size: 3.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.02em;">WOS Prep</h1>
    <p style="font-size: 1.3rem; margin: 0; font-weight: 400; opacity: 0.95;">Professional Tool for Web of Science Data Pre-processing</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Web of Science Raw Data 파일을 업로드하세요 (TXT, CSV, XLS, XLSX)",
    type=['txt', 'csv', 'xls', 'xlsx'],
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("⚠️ 파일을 읽을 수 없습니다.")
        st.stop()

    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC'
    }
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    with st.spinner("🔄 데이터를 분석하고 있습니다..."):
        df['Classification'] = df.apply(classify_article, axis=1)
        
        stop_words = set(stopwords.words('english'))
        custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article'}
        stop_words.update(custom_stop_words)
        lemmatizer = WordNetLemmatizer()
        include_mask = df['Classification'] == 'Include (관련연구)'

        if 'DE' in df.columns:
            df['DE_cleaned'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer, NORMALIZATION_MAP))
        if 'ID' in df.columns:
            df['ID_cleaned'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer, NORMALIZATION_MAP))

    st.success("✅ 분석 완료!")

    # --- 분석 결과 요약 ---
    st.markdown("""<div class="section-header"><div class="section-title">📈 Stats Overview</div></div>""", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    classification_counts = df['Classification'].value_counts()
    total_papers = len(df)
    include_papers = classification_counts.get('Include (관련연구)', 0)
    review_papers = classification_counts.get('Review (검토필요)', 0)
    
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-icon">📋</div><div class="metric-value">{total_papers:,}</div><div class="metric-label">Total Papers</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-icon">✅</div><div class="metric-value">{include_papers:,}</div><div class="metric-label">Relevant Studies</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-icon">🔍</div><div class="metric-value">{review_papers:,}</div><div class="metric-label">Needs Review</div></div>', unsafe_allow_html=True)
    
    keyword_count = 0
    if 'DE_cleaned' in df.columns or 'ID_cleaned' in df.columns:
        all_keywords = []
        if 'DE_cleaned' in df.columns:
            df['DE_cleaned'].dropna().apply(lambda x: all_keywords.extend([kw.strip() for kw in x.split(';') if kw.strip()]))
        if 'ID_cleaned' in df.columns:
            df['ID_cleaned'].dropna().apply(lambda x: all_keywords.extend([kw.strip() for kw in x.split(';') if kw.strip()]))
        keyword_count = len(set(all_keywords))
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-icon">🔤</div><div class="metric-value">{keyword_count:,}</div><div class="metric-label">Unique Keywords</div></div>', unsafe_allow_html=True)

    # --- 최종 파일 생성 및 다운로드 ---
    st.markdown("""<div class="section-header"><div class="section-title">💾 Export to SciMAT</div></div>""", unsafe_allow_html=True)
    
    df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
    if 'DE' in df_final.columns:
        df_final['DE'] = df_final['DE_cleaned']
    if 'ID' in df_final.columns:
        df_final['ID'] = df_final['ID_cleaned']
    
    cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned']
    df_final_output = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns], errors='ignore')
    
    text_data = convert_df_to_scimat_format(df_final_output)
    st.download_button(
        label="📥 SciMAT 호환 포맷 파일 다운로드 (.txt)",
        data=text_data,
        file_name="wos_prep_for_scimat.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True
    )
