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
    .main-container {
        background: #f8f9fa;
        min-height: 100vh;
    }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 20px rgba(0,56,117,0.15);
        border-color: #003875;
    }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: 700;
        color: #003875;
        margin: 0;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
        margin: 8px 0 0 0;
        font-weight: 500;
    }
    
    .metric-icon {
        background: linear-gradient(135deg, #003875, #0056b3);
        color: white;
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 16px;
    }
    
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin: 16px 0;
    }
    
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 16px;
        border-bottom: 2px solid #003875;
        padding-bottom: 8px;
    }
    
    .section-header {
        background: linear-gradient(135deg, #003875, #0056b3);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin: 24px 0 16px 0;
        box-shadow: 0 4px 16px rgba(0,56,117,0.2);
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
    }
    
    .section-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin: 4px 0 0 0;
    }
    
    .info-panel {
        background: #e8f0fe;
        border: 1px solid #003875;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin: 24px 0;
    }
    
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,56,117,0.15);
        border-color: #003875;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 16px;
        background: linear-gradient(135deg, #003875, #0056b3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 8px;
    }
    
    .feature-desc {
        font-size: 0.95rem;
        color: #6c757d;
        line-height: 1.5;
    }
    
    .upload-zone {
        background: white;
        border: 2px dashed #003875;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        margin: 20px 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        background: #f8f9fa;
        border-color: #0056b3;
    }
    
    .progress-indicator {
        background: linear-gradient(90deg, #003875, #0056b3);
        height: 4px;
        border-radius: 2px;
        margin: 16px 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .download-button {
        background: linear-gradient(135deg, #003875, #0056b3) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .download-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(0,56,117,0.3) !important;
    }
    
    .stMetric {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
    }
    
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    
    .comparison-panel {
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
    }
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
        # AI/ML 관련
        "machine learning": ["machine-learning", "ml"], "artificial intelligence": ["ai"],
        "deep learning": ["deep-learning", "deep neural networks", "dnn"], "neural networks": ["neural network", "nn"],
        "natural language processing": ["nlp"], "computer vision": ["cv"], "reinforcement learning": ["rl"],
        # 스트리밍/미디어 관련
        "live streaming": ["live-streaming", "livestreaming", "real time streaming", "live broadcast"],
        "video streaming": ["video-streaming"], "social media": ["social-media"],
        "user experience": ["user-experience", "ux"], "user behavior": ["user-behavior", "consumer behavior"],
        "content creation": ["content-creation"], "digital marketing": ["digital-marketing"],
        "e commerce": ["ecommerce", "e-commerce", "electronic commerce", "live commerce", "live shopping", "social commerce"],
        # 연구방법론 관련
        "data mining": ["data-mining"], "big data": ["big-data"], "data analysis": ["data-analysis"],
        "sentiment analysis": ["sentiment-analysis"], "statistical analysis": ["statistical-analysis"],
        "structural equation modeling": ["sem", "pls-sem"],
        # 기술 관련
        "cloud computing": ["cloud-computing"], "internet of things": ["iot"],
        "mobile applications": ["mobile app", "mobile apps"],
    }
    # 빠른 조회를 위한 역방향 맵 생성
    reverse_map = {}
    for standard_form, variations in base_map.items():
        for variation in variations:
            reverse_map[variation.strip().lower()] = standard_form
        reverse_map[standard_form.strip().lower()] = standard_form
    return reverse_map

NORMALIZATION_MAP = build_normalization_map()

# --- 데이터 로드 함수 (기존과 동일) ---
def load_data(uploaded_file):
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

# --- [핵심 수정] 개선된 논문 분류 함수 (보수적 알고리즘) ---
def classify_article(row):
    # 1. 강력한 포함 키워드 (이 키워드가 있으면 우선적으로 '관련연구'로 분류)
    strong_inclusion_keywords = [
        'live streaming', 'livestreaming', 'live-streaming', 'live commerce',
        'consumer behavior', 'user behavior', 'user engagement', 'purchase intention',
        'social commerce', 'influencer', 'viewer engagement', 'e-commerce'
    ]
    
    # 2. 일반 포함 키워드
    inclusion_keywords = [
        'user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'experience',
        'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural',
        'society', 'marketing', 'business', 'brand', 'monetization', 'education', 'learning'
    ]
    
    # 3. 명확하고 구체적인 제외 키워드
    exclusion_keywords = [
        'protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer',
        'packet dropping', 'bandwidth', 'forward error correction', 'fec', 'arq', 'goodput',
        'sensor data', 'geoscience', 'environmental data', 'wlan',
        'ofdm', 'error correction', 'tcp', 'udp', 'network traffic'
    ]

    title = str(row.get('TI', '')).lower()
    source_title = str(row.get('SO', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    words = set(re.findall(r'\b\w+\b', full_text))

    # --- 새로운 분류 로직 ---
    if any(keyword in full_text for keyword in strong_inclusion_keywords):
        return 'Include (관련연구)'
    if any(f' {keyword} ' in f' {full_text} ' for keyword in exclusion_keywords):
        return 'Exclude (제외연구)'
    if any(keyword in words for keyword in inclusion_keywords):
        return 'Include (관련연구)'
    return 'Review (검토필요)'

# --- 개선된 키워드 전처리 함수 ---
def clean_keyword_string(keywords_str, stop_words, lemmatizer, normalization_map):
    if pd.isna(keywords_str) or not isinstance(keywords_str, str):
        return ""
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

# --- SCIMAT 형식 변환 함수 (기존과 동일) ---
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

# --- 메인 헤더 (기존과 동일) ---
st.markdown("""
<div style="position: relative; text-align: center; padding: 2rem 0 3rem 0; background: linear-gradient(135deg, #003875, #0056b3); color: white; border-radius: 16px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,56,117,0.3);">
    <div style="position: absolute; top: 1rem; left: 2rem; color: white;">
        <div style="font-size: 14px; font-weight: 600; margin-bottom: 2px;">HANYANG UNIVERSITY</div>
        <div style="font-size: 12px; opacity: 0.9;">Technology Management Research</div>
        <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">mot.hanyang.ac.kr</div>
    </div>
    <div style="position: absolute; top: 1rem; right: 2rem; text-align: right; color: rgba(255,255,255,0.9); font-size: 0.85rem;">
        <p style="margin: 0;"><strong>Developed by:</strong> 임태경 (Teddy Lym)</p>
    </div>
    <h1 style="font-size: 3.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.02em;">WOS Prep</h1>
    <p style="font-size: 1.3rem; margin: 0; font-weight: 400; opacity: 0.95;">Professional Tool for Web of Science Data Pre-processing</p>
    <div style="width: 100px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
uploaded_file = st.file_uploader(
    "Tab-delimited 또는 Plain Text 형식의 WOS 데이터 파일을 업로드하세요.",
    type=['csv', 'txt'],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("⚠️ 파일을 읽을 수 없습니다. Web of Science에서 다운로드한 'Tab-delimited' 또는 'Plain Text' 형식의 파일이 맞는지 확인해주세요.")
        st.stop()

    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC', 'Cited Reference Count': 'NR', 'Times Cited, WoS Core': 'Z9'
    }
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)

    with st.spinner("🔄 데이터를 분석하고 있습니다..."):
        df['Classification'] = df.apply(classify_article, axis=1)
        
        if 'DE' in df.columns: df['DE_Original'] = df['DE'].copy()
        if 'ID' in df.columns: df['ID_Original'] = df['ID'].copy()

        stop_words = set(stopwords.words('english'))
        custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article', 'using', 'based', 'approach', 'method', 'system', 'model'}
        stop_words.update(custom_stop_words)
        lemmatizer = WordNetLemmatizer()
        include_mask = df['Classification'] == 'Include (관련연구)'

        if 'DE' in df.columns:
            df['DE_cleaned'] = df['DE'].copy()
            df.loc[include_mask, 'DE_cleaned'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer, NORMALIZATION_MAP))
        if 'ID' in df.columns:
            df['ID_cleaned'] = df['ID'].copy()
            df.loc[include_mask, 'ID_cleaned'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer, NORMALIZATION_MAP))

    st.success("✅ 분석 완료!")

    # --- 분석 결과 요약 ---
    # ... (이전과 동일한 UI 코드) ...

    # --- 최종 파일 생성 및 다운로드 ---
    # ... (이전과 동일한 UI 코드) ...
