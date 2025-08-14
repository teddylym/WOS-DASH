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
</style>
""", unsafe_allow_html=True)

# --- NLTK 리소스 다운로드 (캐시 유지) ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 개념 정규화 사전 (Thesaurus) ---
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

# --- [핵심 수정] 매우 보수적인 최종 분류 알고리즘 ---
def classify_article(row):
    """'확실한 것'만 분류하고, 나머지는 연구자 검토로 넘기는 보수적 알고리즘"""
    
    # 1. 텍스트 필드 추출 및 통합
    title = str(row.get('TI', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, author_keywords, keywords_plus, abstract])

    # 2. 키워드 그룹 정의
    # 2.1 확실한 포함 키워드 (사회/상업적 맥락이 명확한 구문)
    certain_inclusion_phrases = [
        'live streaming commerce', 'social commerce', 'livestreaming commerce',
        'purchase intention', 'customer engagement', 'consumer behavior',
        'influencer marketing', 'brand engagement', 'online shopping',
        'digital marketing', 'e-commerce', 'viewer engagement', 'user experience',
        'social motivations', 'parasocial interaction', 'virtual gift', 'fan engagement'
    ]

    # 2.2 확실한 제외 키워드 (순수 공학 분야)
    certain_exclusion_keywords = [
        'protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer',
        'packet dropping', 'bandwidth', 'forward error correction', 'fec', 'arq', 
        'goodput', 'wlan', 'ofdm', 'error correction', 'tcp', 'udp', 'network traffic',
        'p2p', 'peer-to-peer', 'qoe', 'quality of experience', 'bitrate', 'codec', 'encoding'
    ]
    
    # 2.3 사회/상업적 맥락을 나타내는 키워드
    social_context_keywords = [
        'user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'experience', 
        'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 
        'society', 'marketing', 'business', 'brand', 'monetization', 'education', 'learning'
    ]

    # 3. 분류 로직 실행
    # 3.1 확실한 포함 규칙: 이 구문이 하나라도 있으면 무조건 '관련연구'
    if any(phrase in full_text for phrase in certain_inclusion_phrases):
        return 'Include (관련연구)'

    # 3.2 확실한 제외 규칙: 순수 기술 키워드가 2개 이상 '그리고' 사회/상업적 키워드가 1개 이하일 때만 '제외'
    tech_count = sum(1 for keyword in certain_exclusion_keywords if f' {keyword} ' in f' {full_text} ')
    social_count = sum(1 for keyword in social_context_keywords if keyword in full_text)
    
    if tech_count >= 2 and social_count <= 1:
        return 'Exclude (제외연구)'

    # 3.3 그 외 모든 애매한 경우는 '검토필요'
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

# --- 메인 헤더 ---
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

# --- 주요 기능 소개 ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🔍</div> <div class="feature-title">데이터 분류</div>
        <div class="feature-desc">연구 목적에 맞는 논문 자동 선별</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🏷️</div> <div class="feature-title">키워드 정규화</div>
        <div class="feature-desc">AI 기반 키워드 표준화</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔗</div> <div class="feature-title">SciMAT 호환</div>
        <div class="feature-desc">완벽한 분석 도구 연동</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
uploaded_file = st.file_uploader(
    "Tab-delimited, Plain Text, 또는 Excel 형식의 WOS 데이터 파일을 여기에 드래그하거나 선택하세요.",
    type=['csv', 'txt', 'xlsx', 'xls'],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("⚠️ 파일을 읽을 수 없습니다.")
        st.markdown("""
        **지원되는 파일 형식:**
        - **CSV 파일** (.csv) - 콤마로 구분된 형식
        - **TXT 파일** (.txt) - 탭으로 구분된 WOS 형식
        - **Excel 파일** (.xlsx/.xls) - WOS 기본 다운로드 형식 포함

        **Web of Science 다운로드 권장 형식:**
        - 'Tab-delimited (Win)' 또는 'Plain Text' 형식을 선택하세요.
        """)
        st.stop()

    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC', 'Cited Reference Count': 'NR', 'Times Cited, WoS Core': 'Z9'
    }
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)

    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
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
            df['DE_cleaned'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer, NORMALIZATION_MAP))
        if 'ID' in df.columns:
            df['ID_cleaned'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer, NORMALIZATION_MAP))

    st.success("✅ 분석 완료!")

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 Stats Overview</div>
        <div class="section-subtitle">분석 결과 주요 지표</div>
    </div>
    """, unsafe_allow_html=True)
    
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
    if 'DE_cleaned' in df.columns:
        all_keywords = []
        for text in df.loc[include_mask, 'DE_cleaned'].dropna():
            all_keywords.extend([kw.strip() for kw in text.split(';') if kw.strip()])
        keyword_count = len(set(all_keywords))
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-icon">🔤</div><div class="metric-value">{keyword_count:,}</div><div class="metric-label">Unique Keywords</div></div>', unsafe_allow_html=True)

    # --- 최종 파일 생성 및 다운로드 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">💾 Export to SciMAT</div>
        <div class="section-subtitle">SciMAT 호환 파일 다운로드 및 최종 결과</div>
    </div>
    """, unsafe_allow_html=True)
    
    df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
    if 'DE' in df_final.columns:
        df_final.loc[df_final['Classification'] == 'Include (관련연구)', 'DE'] = df_final.loc[df_final['Classification'] == 'Include (관련연구)', 'DE_cleaned']
    if 'ID' in df_final.columns:
        df_final.loc[df_final['Classification'] == 'Include (관련연구)', 'ID'] = df_final.loc[df_final['Classification'] == 'Include (관련연구)', 'ID_cleaned']
    
    cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
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
