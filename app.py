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
    page_title="WOS Prep - Professional Data Preprocessing", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
            
        # 1단계: 기본 정제 (하이픈과 언더스코어 공백으로 변환)
        keyword_clean = keyword.strip().lower()
        keyword_clean = re.sub(r'[^a-z\s\-_]', '', keyword_clean)
        
        # 2단계: 구문 단위 정규화 먼저 시도 (하이픈 포함 상태로)
        normalized_phrase = normalize_keyword_phrase(keyword_clean)
        
        # 3단계: 정규화되지 않은 경우에만 단어별 처리
        if normalized_phrase == keyword_clean.lower():
            # 하이픈을 공백으로 변환하여 단어별 처리
            keyword_clean = keyword_clean.replace('-', ' ').replace('_', ' ')
            words = keyword_clean.split()
            
            # 불용어 제거 및 표제어 추출
            filtered_words = []
            for word in words:
                if word and len(word) > 2 and word not in stop_words:
                    lemmatized_word = lemmatizer.lemmatize(word)
                    filtered_words.append(lemmatized_word)
            
            if filtered_words:
                reconstructed_phrase = " ".join(filtered_words)
                # 재구성된 구문에 대해 다시 정규화 시도
                final_keyword = normalize_keyword_phrase(reconstructed_phrase)
                if final_keyword and len(final_keyword) > 2:
                    cleaned_keywords.add(final_keyword)
        else:
            # 이미 정규화된 경우 바로 추가
            if normalized_phrase and len(normalized_phrase) > 2:
                cleaned_keywords.add(normalized_phrase)
    
    return '; '.join(sorted(list(cleaned_keywords)))

# --- SCIMAT 형식 변환 함수 (완전 WoS 표준 준수) ---
def convert_df_to_scimat_format(df_to_convert):
    # 원본 WoS 파일과 완전히 동일한 필드 순서 및 헤더
    wos_field_order = [
        'PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB', 'C1', 'C3', 'RP',
        'EM', 'RI', 'OI', 'FU', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA',
        'SN', 'EI', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'BP', 'EP', 'DI', 'EA', 'PG',
        'WC', 'WE', 'SC', 'GA', 'UT', 'PM', 'OA', 'DA'
    ]
    
    # 원본과 완전히 동일한 헤더
    file_content = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'C3', 'CR']
    
    for _, row in df_to_convert.iterrows():
        # 첫 번째 레코드가 아닌 경우에만 빈 줄 추가 (원본과 동일)
        if len(file_content) > 2:
            file_content.append("")
            
        sorted_tags = [tag for tag in wos_field_order if tag in row.index and pd.notna(row[tag])]
        
        for tag in sorted_tags:
            value = row[tag]
            if pd.isna(value):
                continue
            if not isinstance(value, str): 
                value = str(value)
            if not value.strip(): 
                continue

            if tag in multi_line_fields:
                items = [item.strip() for item in value.split(';') if item.strip()]
                if items:
                    file_content.append(f"{tag} {items[0]}")
                    for item in items[1:]:
                        file_content.append(f"   {item}")
            else:
                file_content.append(f"{tag} {value}")

        file_content.append("ER")
    
    # 원본과 동일: UTF-8 (BOM 없음)으로 인코딩
    return "\n".join(file_content).encode('utf-8')

# --- Streamlit UI - 베인앤컴퍼니 스타일 ---

# 베인 스타일 CSS
st.markdown("""
<style>
    /* 베인 컬러 팔레트 */
    :root {
        --bain-red: #e31837;
        --bain-dark-gray: #333333;
        --bain-light-gray: #f8f9fa;
        --bain-medium-gray: #6c757d;
        --bain-white: #ffffff;
    }
    
    /* 헤더 스타일 */
    .bain-header {
        background: linear-gradient(135deg, #e31837 0%, #333333 100%);
        padding: 60px 0;
        text-align: center;
        color: white;
        margin-bottom: 50px;
    }
    
    /* 메인 타이틀 */
    .bain-title {
        font-family: 'Arial', sans-serif;
        font-size: 4rem;
        font-weight: 300;
        letter-spacing: -2px;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* 서브타이틀 */
    .bain-subtitle {
        font-size: 1.5rem;
        font-weight: 300;
        margin: 20px 0 0 0;
        opacity: 0.9;
    }
    
    /* 카드 스타일 */
    .bain-card {
        background: white;
        border: none;
        border-radius: 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 40px;
        margin: 20px 0;
        border-left: 4px solid var(--bain-red);
    }
    
    /* 섹션 헤더 */
    .bain-section-header {
        font-family: 'Arial', sans-serif;
        font-size: 2.2rem;
        font-weight: 300;
        color: var(--bain-dark-gray);
        margin: 50px 0 30px 0;
        border-bottom: 2px solid var(--bain-red);
        padding-bottom: 15px;
    }
    
    /* 메트릭 카드 */
    .bain-metric {
        background: white;
        padding: 30px;
        text-align: center;
        border-radius: 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-top: 3px solid var(--bain-red);
    }
    
    /* 메트릭 숫자 */
    .bain-metric-number {
        font-size: 3rem;
        font-weight: 300;
        color: var(--bain-red);
        margin: 0;
    }
    
    /* 메트릭 라벨 */
    .bain-metric-label {
        font-size: 1rem;
        color: var(--bain-medium-gray);
        margin: 10px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* 인사이트 박스 */
    .bain-insight {
        background: var(--bain-light-gray);
        border-left: 5px solid var(--bain-red);
        padding: 30px;
        margin: 30px 0;
        font-style: italic;
    }
    
    /* 다운로드 섹션 */
    .bain-download-section {
        background: var(--bain-light-gray);
        padding: 50px;
        margin: 40px 0;
    }
    
    /* 단계별 가이드 */
    .bain-step {
        background: white;
        padding: 25px;
        margin: 15px 0;
        border-left: 4px solid var(--bain-red);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .bain-step-number {
        background: var(--bain-red);
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 15px;
    }
</style>
""", unsafe_allow_html=True)

# 헤더 섹션
st.markdown("""
<div class="bain-header">
    <h1 class="bain-title">WOS Prep</h1>
    <p class="bain-subtitle">Professional Data Preprocessing for Science Mapping Excellence</p>
</div>
""", unsafe_allow_html=True)

# 전략적 개요 섹션
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="bain-card">
        <h2 style="color: #e31837; font-weight: 300; margin-top: 0;">Strategic Overview</h2>
        <p style="font-size: 1.1rem; line-height: 1.6; color: #333;">
            Transform raw Web of Science data into analysis-ready datasets through our proprietary 
            three-tier preprocessing methodology. Our platform delivers enterprise-grade data quality 
            while maintaining full compatibility with SciMAT's advanced analytics capabilities.
        </p>
        <p style="font-size: 1rem; color: #6c757d; margin-bottom: 0;">
            Designed for research professionals who demand precision and efficiency in their 
            bibliometric analysis workflows.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="bain-card">
        <h3 style="color: #e31837; font-weight: 300; margin-top: 0;">Key Capabilities</h3>
        <ul style="list-style: none; padding: 0;">
            <li style="padding: 8px 0; border-bottom: 1px solid #eee;">
                ✓ Intelligent Research Classification
            </li>
            <li style="padding: 8px 0; border-bottom: 1px solid #eee;">
                ✓ Advanced Keyword Normalization
            </li>
            <li style="padding: 8px 0; border-bottom: 1px solid #eee;">
                ✓ SciMAT Integration Optimization
            </li>
            <li style="padding: 8px 0;">
                ✓ Enterprise-Grade Output Formats
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 파일 업로드 섹션
st.markdown('<h2 class="bain-section-header">Data Input</h2>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload Web of Science Export File",
    type=['csv', 'txt'],
    help="Accepts Tab-delimited (.txt) or CSV formats from Web of Science"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("**Data Import Error:** Unable to process the uploaded file. Please ensure you've uploaded a valid Tab-delimited or Plain Text format file from Web of Science.")
        st.stop()
    
    # 원본 컬럼명 보존
    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC', 'Times Cited, WoS Core': 'Z9'
    }
    
    # 컬럼명이 이미 WoS 태그 형식인 경우는 변환하지 않음
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)

    # 처리 진행
    with st.spinner("Processing data with advanced algorithms..."):
        
        # 1단계: 분류 (원본 키워드 기준)
        df['Classification'] = df.apply(classify_article, axis=1)
        
        # 원본 키워드 백업 (비교용)
        if 'DE' in df.columns:
            df['DE_Original'] = df['DE'].copy()
        if 'ID' in df.columns:
            df['ID_Original'] = df['ID'].copy()
            
        # 2단계: Include 논문만 키워드 정규화
        stop_words = set(stopwords.words('english'))
        custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article', 'using', 'based', 'approach', 'method', 'system', 'model'}
        stop_words.update(custom_stop_words)
        lemmatizer = WordNetLemmatizer()
        
        include_mask = df['Classification'] == 'Include (관련연구)'
        
        if 'DE' in df.columns:
            df['DE_cleaned'] = df['DE'].copy()
            df.loc[include_mask, 'DE_cleaned'] = df.loc[include_mask, 'DE'].apply(
                lambda x: clean_keyword_string(x, stop_words, lemmatizer)
            )
        if 'ID' in df.columns:
            df['ID_cleaned'] = df['ID'].copy()
            df.loc[include_mask, 'ID_cleaned'] = df.loc[include_mask, 'ID'].apply(
                lambda x: clean_keyword_string(x, stop_words, lemmatizer)
            )
    
    # 성공 메시지
    st.success("Data processing completed successfully")
    
    # 결과 분석 섹션
    st.markdown('<h2 class="bain-section-header">Analysis Results</h2>', unsafe_allow_html=True)
    
    # 분류 결과 메트릭
    classification_counts = df['Classification'].value_counts().reset_index()
    classification_counts.columns = ['Classification', 'Count']
    
    include_count = classification_counts[classification_counts['Classification'] == 'Include (관련연구)']['Count'].iloc[0] if len(classification_counts[classification_counts['Classification'] == 'Include (관련연구)']) > 0 else 0
    review_count = classification_counts[classification_counts['Classification'] == 'Review (검토필요)']['Count'].iloc[0] if len(classification_counts[classification_counts['Classification'] == 'Review (검토필요)']) > 0 else 0
    exclude_count = classification_counts[classification_counts['Classification'] == 'Exclude (제외연구)']['Count'].iloc[0] if len(classification_counts[classification_counts['Classification'] == 'Exclude (제외연구)']) > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="bain-metric">
            <div class="bain-metric-number">{len(df):,}</div>
            <div class="bain-metric-label">Total Papers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="bain-metric">
            <div class="bain-metric-number">{include_count:,}</div>
            <div class="bain-metric-label">Relevant ({include_count/len(df)*100:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="bain-metric">
            <div class="bain-metric-number">{review_count:,}</div>
            <div class="bain-metric-label">Review Required ({review_count/len(df)*100:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="bain-metric">
            <div class="bain-metric-number">{exclude_count:,}</div>
            <div class="bain-metric-label">Excluded ({exclude_count/len(df)*100:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)

    # 인사이트 박스
    st.markdown(f"""
    <div class="bain-insight">
        <strong>Key Insight:</strong> {include_count + review_count:,} papers ({(include_count + review_count)/len(df)*100:.1f}%) 
        have been identified as analysis-ready, representing high-quality research aligned with your objectives.
    </div>
    """, unsafe_allow_html=True)

    # 키워드 분석 결과
    if include_count > 0:
        st.markdown('<h2 class="bain-section-header">Keyword Intelligence</h2>', unsafe_allow_html=True)
        
        all_keywords = []
        if 'DE_cleaned' in df.columns: 
            all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'DE_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        if 'ID_cleaned' in df.columns: 
            all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'ID_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        
        if all_keywords:
            keyword_counts = Counter(all_keywords)
            top_keywords = keyword_counts.most_common(15)
            df_keywords = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])
            
            # 차트 생성
            chart = alt.Chart(df_keywords).mark_bar(color='#e31837').encode(
                y=alt.Y('Keyword:N', title='', sort='-x'),
                x=alt.X('Frequency:Q', title='Frequency'),
                tooltip=['Keyword', 'Frequency']
            ).properties(
                title=alt.TitleParams(
                    text='Top 15 Normalized Keywords',
                    fontSize=18,
                    color='#333333'
                ),
                height=400
            )
            st.altair_chart(chart, use_container_width=True)

    # 다운로드 섹션
    st.markdown('<h2 class="bain-section-header">Export Options</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="bain-download-section">
        <h3 style="color: #333; font-weight: 300; margin-top: 0;">Three-Tier Export Strategy</h3>
        <p style="color: #6c757d; margin-bottom: 30px;">
            Choose the optimal format based on your analytical workflow and integration requirements.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # 원본 데이터
    with col1:
        df_scimat = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        
        if 'DE_Original' in df_scimat.columns:
            df_scimat['DE'] = df_scimat['DE_Original']
        if 'ID_Original' in df_scimat.columns:
            df_scimat['ID'] = df_scimat['ID_Original']
        
        cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
        df_scimat_output = df_scimat.drop(columns=[col for col in cols_to_drop if col in df_scimat.columns])
        
        st.markdown("""
        <div class="bain-card">
            <h4 style="color: #e31837; margin-top: 0;">Tier 1: Original Format</h4>
            <p style="color: #6c757d; font-size: 0.9rem; margin-bottom: 20px;">
                Preserves complete data integrity for comprehensive SciMAT preprocessing workflows.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.metric("Papers", f"{len(df_scimat_output):,}", delta="100% fidelity")
        
        text_data_scimat = convert_df_to_scimat_format(df_scimat_output)
        st.download_button(
            label="Download Original Format",
            data=text_data_scimat,
            file_name="wos_prep_original.txt",
            mime="text/plain",
            key="original_download",
            use_container_width=True
        )
    
    # 최소 처리
    with col2:
        df_minimal = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        
        if 'DE' in df_minimal.columns:
            df_minimal['DE'] = df_minimal['DE'].apply(
                lambda x: '; '.join([kw.strip().lower() for kw in str(x).split(';') if kw.strip()]) if pd.notna(x) else x
            )
    # 최소 처리
    with col2:
        df_minimal = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        
        if 'DE' in df_minimal.columns:
            df_minimal['DE'] = df_minimal['DE'].apply(
                lambda x: '; '.join([kw.strip().lower() for kw in str(x).split(';') if kw.strip()]) if pd.notna(x) else x
            )
        if 'ID' in df_minimal.columns:
            df_minimal['ID'] = df_minimal['ID'].apply(
                lambda x: '; '.join([kw.strip().lower() for kw in str(x).split(';') if kw.strip()]) if pd.notna(x) else x
            )
        
        cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
        df_minimal_output = df_minimal.drop(columns=[col for col in cols_to_drop if col in df_minimal.columns])
        
        st.markdown("""
        <div class="bain-card">
            <h4 style="color: #e31837; margin-top: 0;">Tier 2: Optimized Format</h4>
            <p style="color: #6c757d; font-size: 0.9rem; margin-bottom: 20px;">
                Case-normalized for enhanced Levenshtein distance performance in SciMAT grouping algorithms.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.metric("Papers", f"{len(df_minimal_output):,}", delta="Optimized")
        
        text_data_minimal = convert_df_to_scimat_format(df_minimal_output)
        st.download_button(
            label="Download Optimized Format",
            data=text_data_minimal,
            file_name="wos_prep_optimized.txt",
            mime="text/plain",
            key="minimal_download",
            use_container_width=True
        )
    
    # 완전 정규화
    with col3:
        df_analysis = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        
        if 'DE_cleaned' in df_analysis.columns: 
            df_analysis.loc[df_analysis['Classification'] == 'Include (관련연구)', 'DE'] = df_analysis.loc[df_analysis['Classification'] == 'Include (관련연구)', 'DE_cleaned']
        if 'ID_cleaned' in df_analysis.columns: 
            df_analysis.loc[df_analysis['Classification'] == 'Include (관련연구)', 'ID'] = df_analysis.loc[df_analysis['Classification'] == 'Include (관련연구)', 'ID_cleaned']
        
        cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
        df_analysis_output = df_analysis.drop(columns=[col for col in cols_to_drop if col in df_analysis.columns])
        
        st.markdown("""
        <div class="bain-card">
            <h4 style="color: #e31837; margin-top: 0;">Tier 3: Normalized Format</h4>
            <p style="color: #6c757d; font-size: 0.9rem; margin-bottom: 20px;">
                Fully standardized keywords for high-precision analysis and publication-ready insights.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.metric("Papers", f"{len(df_analysis_output):,}", delta="Normalized")
        
        text_data_analysis = convert_df_to_scimat_format(df_analysis_output)
        st.download_button(
            label="Download Normalized Format",
            data=text_data_analysis,
            file_name="wos_prep_normalized.txt",
            mime="text/plain",
            key="analysis_download",
            use_container_width=True
        )

    # 실행 가이드
    st.markdown('<h2 class="bain-section-header">Implementation Roadmap</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="bain-step">
        <span class="bain-step-number">1</span>
        <strong>Data Preparation</strong><br>
        Import Original or Optimized format into SciMAT. Leverage built-in preprocessing modules for maximum analytical depth.
    </div>
    
    <div class="bain-step">
        <span class="bain-step-number">2</span>
        <strong>Science Mapping Execution</strong><br>
        Configure temporal analysis periods, similarity measures, and clustering algorithms within SciMAT's analytical framework.
    </div>
    
    <div class="bain-step">
        <span class="bain-step-number">3</span>
        <strong>Strategic Insights</strong><br>
        Utilize Normalized format for final keyword analysis, strategic diagrams, and publication-ready research outputs.
    </div>
    """, unsafe_allow_html=True)

    # 전문가 권고사항
    with st.expander("🔍 Expert Recommendations"):
        st.markdown("""
        ### SciMAT Integration Best Practices
        
        **Optimal Grouping Strategy:**
        - Configure Levenshtein distance to 2-3 for semantic clustering
        - Prioritize manual grouping for domain-specific terminology
        - Implement Stop Groups for generic research terms
        
        **Performance Optimization:**
        - Use Tier 2 (Optimized) format for automated grouping workflows
        - Reserve Tier 1 (Original) for comprehensive manual preprocessing
        - Deploy Tier 3 (Normalized) for final analytical outputs
        
        **Quality Assurance:**
        - Validate keyword standardization against domain expertise
        - Cross-reference clustering results with literature reviews
        - Implement iterative refinement based on strategic objectives
        """)

    # 데이터 미리보기
    st.markdown('<h2 class="bain-section-header">Data Preview</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="bain-card">
        <h4 style="color: #e31837; margin-top: 0;">Sample Output (Optimized Format)</h4>
        <p style="color: #6c757d; margin-bottom: 20px;">
            Representative sample of processed data optimized for SciMAT integration.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.dataframe(df_minimal_output.head(8), use_container_width=True)

    # 처리 통계
    if include_mask.any():
        st.markdown(f"""
        <div class="bain-insight">
            <strong>Processing Summary:</strong> Applied advanced normalization algorithms to {include_count:,} relevant studies, 
            standardizing {len(all_keywords) if 'all_keywords' in locals() else 'N/A'} unique keywords for enhanced analytical precision.
        </div>
        """, unsafe_allow_html=True)

# 푸터
st.markdown("""
<div style="text-align: center; padding: 60px 0 40px 0; margin-top: 60px; border-top: 1px solid #eee; background: #f8f9fa;">
    <h3 style="color: #e31837; font-weight: 300; margin: 0 0 15px 0;">WOS Prep</h3>
    <p style="color: #6c757d; margin: 0; font-size: 1rem;">
        Professional Data Preprocessing for Science Mapping Excellence
    </p>
    <p style="color: #6c757d; margin: 5px 0 0 0; font-size: 0.9rem;">
        Engineered for research professionals • Optimized for SciMAT integration
    </p>
</div>
""", unsafe_allow_html=True)
