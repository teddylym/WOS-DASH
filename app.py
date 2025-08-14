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

# --- 커스텀 CSS 스타일 (ResearchGate 스타일) ---
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
        box-shadow: 0 4px 20px rgba(0,150,255,0.15);
        border-color: #0096FF;
    }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: 700;
        color: #0096FF;
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
        background: linear-gradient(135deg, #0096FF, #00d4ff);
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
        border-bottom: 2px solid #0096FF;
        padding-bottom: 8px;
    }
    
    .section-header {
        background: linear-gradient(135deg, #0096FF, #00d4ff);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin: 24px 0 16px 0;
        box-shadow: 0 4px 16px rgba(0,150,255,0.2);
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
        background: #e3f2fd;
        border: 1px solid #0096FF;
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
        box-shadow: 0 8px 24px rgba(0,150,255,0.15);
        border-color: #0096FF;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 16px;
        background: linear-gradient(135deg, #0096FF, #00d4ff);
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
        border: 2px dashed #0096FF;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        margin: 20px 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        background: #f8f9fa;
        border-color: #0066cc;
    }
    
    .progress-indicator {
        background: linear-gradient(90deg, #0096FF, #00d4ff);
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
        background: linear-gradient(135deg, #0096FF, #00d4ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .download-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(0,150,255,0.3) !important;
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

# --- 키워드 정규화 사전 (역방향 매핑으로 최적화) ---
def build_normalization_map():
    """성능 최적화를 위한 역방향 정규화 사전 생성"""
    base_map = {
        # AI/ML 관련 (세분화 유지)
        "machine learning": ["machine-learning", "machine_learning", "ml", "machinelearning"],
        "artificial intelligence": ["ai", "artificial-intelligence", "artificial_intelligence", "artificialintelligence"],
        "deep learning": ["deep-learning", "deep_learning", "deep neural networks", "deep neural network", "dnn", "deeplearning"],
        "neural networks": ["neural-networks", "neural_networks", "neuralnetworks", "neural network", "nn"],
        "natural language processing": ["nlp", "natural-language-processing", "natural_language_processing"],
        "computer vision": ["computer-vision", "computer_vision", "computervision", "cv"],
        "reinforcement learning": ["reinforcement-learning", "reinforcement_learning", "rl"],

        # 스트리밍/미디어 관련
        "live streaming": ["live-streaming", "live_streaming", "livestreaming", "real time streaming"],
        "video streaming": ["video-streaming", "video_streaming", "videostreaming"],
        "social media": ["social-media", "social_media", "socialmedia"],
        "user experience": ["user-experience", "user_experience", "ux", "userexperience"],
        "user behavior": ["user-behavior", "user_behavior", "userbehavior"],
        "content creation": ["content-creation", "content_creation", "contentcreation"],
        "digital marketing": ["digital-marketing", "digital_marketing", "digitalmarketing"],
        "e commerce": ["ecommerce", "e-commerce", "e_commerce", "electronic commerce"],

        # 연구방법론 관련
        "data mining": ["data-mining", "data_mining", "datamining"],
        "big data": ["big-data", "big_data", "bigdata"],
        "data analysis": ["data-analysis", "data_analysis", "dataanalysis"],
        "sentiment analysis": ["sentiment-analysis", "sentiment_analysis", "sentimentanalysis"],
        "statistical analysis": ["statistical-analysis", "statistical_analysis", "statisticalanalysis"],
        "structural equation modeling": ["sem", "pls-sem", "pls sem", "structural equation model"],

        # 기술 관련
        "cloud computing": ["cloud-computing", "cloud_computing", "cloudcomputing"],
        "internet of things": ["iot", "internet-of-things", "internet_of_things"],
        "mobile applications": ["mobile-applications", "mobile_applications", "mobile apps", "mobile app"],
        "web development": ["web-development", "web_development", "webdevelopment"],
        "software engineering": ["software-engineering", "software_engineering", "softwareengineering"]
    }

    # 역방향 매핑 생성 (variation -> standard_form)
    reverse_map = {}
    for standard_form, variations in base_map.items():
        for variation in variations:
            reverse_map[variation.lower()] = standard_form
        # 표준 형태도 자기 자신으로 매핑
        reverse_map[standard_form.lower()] = standard_form

    return reverse_map

NORMALIZATION_MAP = build_normalization_map()

def normalize_keyword_phrase(phrase):
    """구문 단위 키워드 정규화"""
    phrase_lower = phrase.lower().strip()
    return NORMALIZATION_MAP.get(phrase_lower, phrase_lower)

# --- 데이터 로드 함수 ---
def load_data(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1', 'cp949']

    for encoding in encodings_to_try:
        try:
            file_content = file_bytes.decode(encoding)
            # 탭 구분자 우선 시도
            df = pd.read_csv(io.StringIO(file_content), sep='\t', lineterminator='\n')
            if df.shape[1] > 1: return df
        except Exception:
            continue

    for encoding in encodings_to_try:
        try:
            file_content = file_bytes.decode(encoding)
            # 콤마 구분자 시도
            df = pd.read_csv(io.StringIO(file_content))
            if df.shape[1] > 1: return df
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
    """개선된 키워드 정규화 및 정제 처리"""
    if pd.isna(keywords_str) or not isinstance(keywords_str, str):
        return ""

    all_keywords = keywords_str.split(';')
    cleaned_keywords = set()

    for keyword in all_keywords:
        if not keyword.strip():
            continue

        # 1단계: 기본 정제
        keyword_clean = keyword.strip().lower()
        keyword_clean = re.sub(r'[^a-z\s\-_]', '', keyword_clean)

        # 2단계: 구문 단위 정규화
        normalized_phrase = normalize_keyword_phrase(keyword_clean)

        # 3단계: 단어별 처리
        if normalized_phrase == keyword_clean.lower():
            keyword_clean = keyword_clean.replace('-', ' ').replace('_', ' ')
            words = keyword_clean.split()

            filtered_words = []
            for word in words:
                if word and len(word) > 2 and word not in stop_words:
                    lemmatized_word = lemmatizer.lemmatize(word)
                    filtered_words.append(lemmatized_word)

            if filtered_words:
                reconstructed_phrase = " ".join(filtered_words)
                final_keyword = normalize_keyword_phrase(reconstructed_phrase)
                if final_keyword and len(final_keyword) > 2:
                    cleaned_keywords.add(final_keyword)
        else:
            if normalized_phrase and len(normalized_phrase) > 2:
                cleaned_keywords.add(normalized_phrase)

    return '; '.join(sorted(list(cleaned_keywords)))

# --- SCIMAT 형식 변환 함수 ---
def convert_df_to_scimat_format(df_to_convert):
    wos_field_order = [
        'PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB', 'C1', 'C3', 'RP',
        'EM', 'RI', 'OI', 'FU', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA',
        'SN', 'EI', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'BP', 'EP', 'DI', 'EA', 'PG',
        'WC', 'WE', 'SC', 'GA', 'UT', 'PM', 'OA', 'DA'
    ]
    file_content = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'C3', 'CR']

    for _, row in df_to_convert.iterrows():
        if len(file_content) > 2:
            file_content.append("")
        sorted_tags = [tag for tag in wos_field_order if tag in row.index and pd.notna(row[tag])]

        for tag in sorted_tags:
            value = row[tag]
            if pd.isna(value) or not str(value).strip():
                continue
            if not isinstance(value, str):
                value = str(value)

            if tag in multi_line_fields:
                items = [item.strip() for item in value.split(';') if item.strip()]
                if items:
                    file_content.append(f"{tag} {items[0]}")
                    for item in items[1:]:
                        file_content.append(f"  {item}")
            else:
                file_content.append(f"{tag} {value}")

        file_content.append("ER")
    return "\n".join(file_content).encode('utf-8')

# --- 메인 헤더 ---
st.markdown("""
<div style="position: relative; text-align: center; padding: 2rem 0 3rem 0; background: linear-gradient(135deg, #0096FF, #00d4ff); color: white; border-radius: 16px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,150,255,0.3);">
    <div style="position: absolute; top: 1rem; right: 2rem; text-align: right; color: rgba(255,255,255,0.9); font-size: 0.85rem;">
        <p style="margin: 0;"><strong>Developed by:</strong> 임태경 (Teddy Lym)</p>
        <p style="margin: 0;">Hanyang University</p>
    </div>
    <h1 style="font-size: 3.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
        WOS Prep
    </h1>
    <p style="font-size: 1.3rem; margin: 0; font-weight: 400; opacity: 0.95;">
        Professional Tool for Web of Science Data Pre-processing
    </p>
    <div style="width: 100px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 주요 기능 소개 (개선된 디자인) ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">데이터 분류</div>
        <div class="feature-desc">연구 목적에 맞는 논문 자동 선별</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">⚙️</div>
        <div class="feature-title">키워드 정규화</div>
        <div class="feature-desc">AI 기반 키워드 표준화</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">SciMAT 호환</div>
        <div class="feature-desc">완벽한 분석 도구 연동</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 키워드 정규화 기준 설명 ---
with st.expander("ℹ️ 키워드 정규화 기준 상세", expanded=False):
    st.markdown("""
    <div class="info-panel">
        <h4 style="color: #0096FF; margin-bottom: 16px;">적용되는 정규화 규칙:</h4>
        <ul style="line-height: 1.8; color: #495057;">
            <li><strong>AI/ML 관련:</strong> machine learning ← machine-learning, ML, machinelearning</li>
            <li><strong>인공지능:</strong> artificial intelligence ← AI, artificial-intelligence</li>
            <li><strong>딥러닝:</strong> deep learning ← deep-learning, deep neural networks, DNN</li>
            <li><strong>스트리밍:</strong> live streaming ← live-streaming, livestreaming</li>
            <li><strong>사용자 경험:</strong> user experience ← user-experience, UX</li>
            <li><strong>연구방법론:</strong> structural equation modeling ← SEM, PLS-SEM</li>
            <li><strong>전자상거래:</strong> e commerce ← ecommerce, e-commerce, electronic commerce</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">📁 데이터 업로드</div>
    <div class="section-subtitle">Web of Science Raw Data 파일을 업로드하여 분석을 시작하세요.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="upload-zone">
    <div style="font-size: 3rem; margin-bottom: 16px; color: #0096FF;">📤</div>
    <h3 style="color: #212529; margin-bottom: 8px;">파일을 선택하세요</h3>
    <p style="color: #6c757d; margin: 0;">Tab-delimited 또는 Plain Text 형식의 WOS 데이터 파일</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "파일 선택",
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

    # 프로그레스 인디케이터
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner("🔄 데이터를 분석하고 있습니다... 잠시만 기다려주세요."):
        # 1단계: 분류
        df['Classification'] = df.apply(classify_article, axis=1)

        # 원본 키워드 백업
        if 'DE' in df.columns: df['DE_Original'] = df['DE'].copy()
        if 'ID' in df.columns: df['ID_Original'] = df['ID'].copy()

        # 2단계: 키워드 정규화
        stop_words = set(stopwords.words('english'))
        custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article', 'using', 'based', 'approach', 'method', 'system', 'model'}
        stop_words.update(custom_stop_words)
        lemmatizer = WordNetLemmatizer()
        include_mask = df['Classification'] == 'Include (관련연구)'

        if 'DE' in df.columns:
            df['DE_cleaned'] = df['DE'].copy()
            df.loc[include_mask, 'DE_cleaned'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))
        if 'ID' in df.columns:
            df['ID_cleaned'] = df['ID'].copy()
            df.loc[include_mask, 'ID_cleaned'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))

    st.success("✅ 분석 완료!")

    # --- 분석 결과 요약 (Stats Overview 스타일) ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 Stats Overview</div>
        <div class="section-subtitle">분석 결과 주요 지표</div>
    </div>
    """, unsafe_allow_html=True)

    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    classification_counts = df['Classification'].value_counts()
    total_papers = len(df)
    include_papers = classification_counts.get('Include (관련연구)', 0)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{total_papers:,}</div>
            <div class="metric-label">Total Papers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{include_papers:,}</div>
            <div class="metric-label">Relevant Studies</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        processing_rate = (include_papers / total_papers * 100) if total_papers > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{processing_rate:.1f}%</div>
            <div class="metric-label">Inclusion Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # 키워드 수 계산
        keyword_count = 0
        if 'DE_cleaned' in df.columns:
            all_keywords = []
            for text in df.loc[include_mask, 'DE_cleaned'].dropna():
                all_keywords.extend([kw.strip() for kw in text.split(';') if kw.strip()])
            keyword_count = len(set(all_keywords))
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔤</div>
            <div class="metric-value">{keyword_count:,}</div>
            <div class="metric-label">Unique Keywords</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 논문 분류 현황 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Research Classification Distribution</div>
    """, unsafe_allow_html=True)

    classification_counts_df = df['Classification'].value_counts().reset_index()
    classification_counts_df.columns = ['분류', '논문 수']

    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        st.dataframe(classification_counts_df, use_container_width=True, hide_index=True)

    with col2:
        # 도넛 차트 (개선된 색상)
        domain = ['Include (관련연구)', 'Review (검토필요)', 'Exclude (제외연구)']
        range_ = ['#0096FF', '#00d4ff', '#6c757d']

        selection = alt.selection_point(fields=['분류'], on='mouseover', nearest=True)

        base = alt.Chart(classification_counts_df).encode(
            theta=alt.Theta(field="논문 수", type="quantitative", stack=True),
            color=alt.Color(field="분류", type="nominal", title="Classification",
                           scale=alt.Scale(domain=domain, range=range_),
                           legend=alt.Legend(orient="right", titleColor="#212529", labelColor="#495057")),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.8))
        ).add_params(selection)

        pie = base.mark_arc(outerRadius=120, innerRadius=70)
        text_total = alt.Chart(pd.DataFrame([{'value': f'{total_papers}'}])).mark_text(
            align='center', baseline='middle', fontSize=35, fontWeight='bold', color='#0096FF'
        ).encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame([{'value': 'Total Papers'}])).mark_text(
            align='center', baseline='middle', fontSize=14, dy=-25, color='#495057'
        ).encode(text='value:N')

        chart = (pie + text_total + text_label).properties(
            title=alt.TitleParams(text='논문 분류 분포', anchor='middle', fontSize=16, fontWeight=500, color="#212529"),
            width=300, height=300
        ).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 연도별 연구 동향 그래프 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Research Trend Analysis</div>
    """, unsafe_allow_html=True)
    
    df_trend = df.copy()
    if 'PY' in df_trend.columns:
        df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
        df_trend.dropna(subset=['PY'], inplace=True)
        df_trend['PY'] = df_trend['PY'].astype(int)
        
        yearly_counts = df_trend['PY'].value_counts().reset_index()
        yearly_counts.columns = ['Year', 'Count']
        yearly_counts = yearly_counts[yearly_counts['Year'] <= 2025].sort_values('Year')

        projection_layer = alt.Chart(pd.DataFrame([])).mark_line()
        show_projection_caption = False
        if 2025 in yearly_counts['Year'].values and 2024 in yearly_counts['Year'].values:
            count_2025_actual = yearly_counts.loc[yearly_counts['Year'] == 2025, 'Count'].iloc[0]
            count_2024_actual = yearly_counts.loc[yearly_counts['Year'] == 2024, 'Count'].iloc[0]
            count_2025_projected = count_2025_actual * 2
            
            projection_df = pd.DataFrame([
                {'Year': 2024, 'Count': count_2024_actual, 'Type': 'Projected'},
                {'Year': 2025, 'Count': count_2025_projected, 'Type': 'Projected'}
            ])
            
            projection_layer = alt.Chart(projection_df).mark_line(
                strokeDash=[5, 5], color='#ff6b6b', point={'color': '#ff6b6b', 'filled': False, 'size': 60}
            ).encode(x='Year:O', y='Count:Q')
            show_projection_caption = True
        
        selection_trend = alt.selection_point(fields=['Year'], on='mouseover', nearest=True, empty='none')
        
        line_chart = alt.Chart(yearly_counts).mark_line(
            point={'size': 80, 'filled': True}, strokeWidth=3, color='#0096FF'
        ).encode(
            x=alt.X('Year:O', title='발행 연도'),
            y=alt.Y('Count:Q', title='논문 수'),
            tooltip=['Year', 'Count'],
            opacity=alt.condition(selection_trend, alt.value(1), alt.value(0.8))
        ).add_params(selection_trend)
        
        trend_chart = (line_chart + projection_layer).properties(height=350)
        st.altair_chart(trend_chart, use_container_width=True)
        if show_projection_caption:
            st.caption("📈 빨간 점선은 2025년 상반기 데이터 기준으로 연간 발행량을 추정한 예상치입니다.")
    else:
        st.warning("⚠️ 발행 연도(PY) 데이터가 없어 연구 동향을 분석할 수 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 주요 인용 논문 분석 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Top Cited Papers (by Reference Count)</div>
    """, unsafe_allow_html=True)
    
    if 'NR' in df.columns:
        df_cited = df.copy()
        df_cited['NR'] = pd.to_numeric(df_cited['NR'], errors='coerce').fillna(0)
        df_cited = df_cited.sort_values(by='NR', ascending=False).head(5)
        
        df_cited['Author_Display'] = df_cited['AU'].apply(lambda x: str(x).split(';')[0] if pd.notna(x) else 'N/A')
        df_cited['Title_Display'] = df_cited['TI'].apply(lambda x: str(x)[:50] + '...' if len(str(x)) > 50 else str(x))
        df_cited['Label'] = df_cited['Title_Display'] + ' (' + df_cited['Author_Display'] + ')'

        selection_cited = alt.selection_point(fields=['Label'], on='mouseover', nearest=True, empty='none')

        cited_chart = alt.Chart(df_cited).mark_bar(color='#0096FF', cornerRadiusEnd=4).encode(
            x=alt.X('NR:Q', title='참고문헌 수'),
            y=alt.Y('Label:N', title='논문 제목 및 저자', sort='-x'),
            tooltip=['TI', 'AU', 'NR'],
            opacity=alt.condition(selection_cited, alt.value(1), alt.value(0.8))
        ).add_params(selection_cited).properties(height=300)
        st.altair_chart(cited_chart, use_container_width=True)
    else:
        st.warning("⚠️ 참고문헌 수(NR) 데이터가 없어 주요 인용 논문을 분석할 수 없습니다.")
        
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 주요 키워드 분석 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Top Keywords Analysis (Relevant Studies Only)</div>
    """, unsafe_allow_html=True)
    
    all_keywords = []
    if 'DE_cleaned' in df.columns:
        all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'DE_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
    if 'ID_cleaned' in df.columns:
        all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'ID_cleaned'].dropna() for kw in text.split(';') if kw.strip()])

    if all_keywords:
        keyword_counts = Counter(all_keywords)
        top_n = 20
        top_keywords_df = pd.DataFrame(keyword_counts.most_common(top_n), columns=['키워드', '빈도'])
        top_3_keywords = top_keywords_df['키워드'].head(3).tolist()
        
        selection_keyword = alt.selection_point(fields=['키워드'], on='mouseover', nearest=True, empty='none')

        y_encoding = alt.Y('키워드:N', title=None, sort=alt.SortField(field='빈도', order='descending'))
        x_encoding = alt.X('빈도:Q', title='빈도', scale=alt.Scale(zero=True))
        
        base_chart = alt.Chart(top_keywords_df).encode(
            y=y_encoding,
            x=x_encoding,
            opacity=alt.condition(selection_keyword, alt.value(1), alt.value(0.8)),
            tooltip=['키워드', '빈도']
        ).add_params(selection_keyword)

        line = base_chart.mark_rule(size=3, color='#dee2e6')
        
        point = base_chart.mark_point(filled=True, size=120).encode(
            color=alt.condition(
                alt.FieldOneOfPredicate(field='키워드', oneOf=top_3_keywords),
                alt.value('#0096FF'),
                alt.value('#00d4ff')
            )
        )
        
        final_chart = (line + point).properties(height=500).configure_axis(
            grid=False
        ).configure_view(strokeWidth=0)

        st.altair_chart(final_chart, use_container_width=True)

        # 정규화 전후 비교 (개선된 디자인)
        if st.checkbox("🔍 정규화 전후 비교 보기 (샘플)", key="comparison_check"):
            st.markdown("""
            <div class="comparison-panel">
                <h4 style="color: #0096FF; margin-bottom: 16px;">키워드 정규화 효과 비교</h4>
            """, unsafe_allow_html=True)
            
            sample_data = []
            sample_rows = df.loc[include_mask].head(3)
            for idx, row in sample_rows.iterrows():
                if 'DE_Original' in df.columns and pd.notna(row.get('DE_Original')):
                    sample_data.append({
                        '논문 ID': idx, '필드': 'Author Keywords (DE)',
                        '정규화 전': str(row['DE_Original']), '정규화 후': str(row['DE_cleaned'])
                    })
            if sample_data:
                st.dataframe(pd.DataFrame(sample_data), use_container_width=True, hide_index=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ 관련연구로 분류된 논문에서 유효한 키워드를 찾을 수 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 처리된 데이터 미리보기 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📋 Processed Data Preview</div>
        <div class="section-subtitle">처리된 데이터 상위 10개 미리보기</div>
    </div>
    """, unsafe_allow_html=True)

    df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
    if 'DE' in df_final.columns:
        df_final['DE'] = df_final['DE_cleaned']
    if 'ID' in df_final.columns:
        df_final['ID'] = df_final['ID_cleaned']
    cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
    df_final_output = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns], errors='ignore')
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.dataframe(df_final_output.head(10), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SciMAT 호환 파일 다운로드 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">💾 Export to SciMAT</div>
        <div class="section-subtitle">SciMAT 호환 파일 다운로드 및 최종 결과</div>
    </div>
    """, unsafe_allow_html=True)

    # 최종 메트릭 (개선된 디자인)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상 논문 수</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if include_mask.any():
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🎯</div>
                <div class="metric-value">{include_mask.sum():,}</div>
                <div class="metric-label">키워드 정규화 적용 논문</div>
            </div>
            """, unsafe_allow_html=True)

    # 다운로드 버튼 (개선된 스타일)
    text_data = convert_df_to_scimat_format(df_final_output)
    st.download_button(
        label="📥 SciMAT 호환 포맷 파일 다운로드 (.txt)",
        data=text_data,
        file_name="wos_prep_for_scimat.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True
    )
    
    # 사용 가이드 (개선된 디자인)
    st.markdown("""
    <div class="info-panel">
        <h4 style="color: #0096FF; margin-bottom: 16px;">💡 SciMAT 사용 가이드:</h4>
        <ol style="line-height: 1.8; color: #495057;">
            <li>다운로드한 <code>wos_prep_for_scimat.txt</code> 파일을 SciMAT에 업로드합니다.</li>
            <li><code>Group set</code> → <code>Words groups manager</code>에서 Levenshtein distance를 활용해 유사 키워드를 자동으로 그룹핑합니다.</li>
            <li>수동으로 키워드 그룹을 최종 조정한 후 분석을 실행합니다.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# --- 하단 여백 ---
st.markdown("<br><br>", unsafe_allow_html=True)
