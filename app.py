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

# --- 키워드 정규화 사전 (확장된 라이브 스트리밍 버전) ---
def build_normalization_map():
    """라이브 스트리밍 연구 특화 정규화 사전"""
    base_map = {
        # === 라이브 스트리밍 핵심 용어 ===
        "live streaming": ["live-streaming", "live_streaming", "livestreaming", "live stream", "live streams", "real time streaming"],
        "live commerce": ["live-commerce", "live_commerce", "livestream commerce", "streaming commerce", "live shopping", "live selling"],
        "live broadcasting": ["live-broadcasting", "live_broadcasting", "live broadcast", "live broadcasts"],
        "video streaming": ["video-streaming", "video_streaming", "videostreaming", "video stream"],
        "streaming platform": ["streaming-platform", "streaming_platform", "stream platform", "streaming platforms"],
        "streaming service": ["streaming-service", "streaming_service", "stream service", "streaming services"],
        
        # === 사용자 행동 관련 ===
        "user behavior": ["user-behavior", "user_behavior", "userbehavior", "user behaviour"],
        "viewer behavior": ["viewer-behavior", "viewer_behavior", "viewer behaviour"],
        "consumer behavior": ["consumer-behavior", "consumer_behavior", "consumer behaviour"],
        "streaming behavior": ["streaming-behavior", "streaming_behavior"],
        "user experience": ["user-experience", "user_experience", "ux", "userexperience"],
        "user engagement": ["user-engagement", "user_engagement", "userengagement"],
        
        # === AI/ML 관련 ===
        "machine learning": ["machine-learning", "machine_learning", "ml", "machinelearning"],
        "artificial intelligence": ["ai", "artificial-intelligence", "artificial_intelligence", "artificialintelligence"],
        "deep learning": ["deep-learning", "deep_learning", "deep neural networks", "deep neural network", "dnn", "deeplearning"],
        "neural networks": ["neural-networks", "neural_networks", "neuralnetworks", "neural network", "nn"],
        "natural language processing": ["nlp", "natural-language-processing", "natural_language_processing"],
        "computer vision": ["computer-vision", "computer_vision", "computervision", "cv"],
        "reinforcement learning": ["reinforcement-learning", "reinforcement_learning", "rl"],

        # === 소셜 미디어/플랫폼 ===
        "social media": ["social-media", "social_media", "socialmedia"],
        "social platform": ["social-platform", "social_platform", "socialplatform"],
        "digital platform": ["digital-platform", "digital_platform", "digitalplatform"],
        "content creation": ["content-creation", "content_creation", "contentcreation"],
        "digital marketing": ["digital-marketing", "digital_marketing", "digitalmarketing"],
        "e commerce": ["ecommerce", "e-commerce", "e_commerce", "electronic commerce"],

        # === 연구방법론 관련 ===
        "data mining": ["data-mining", "data_mining", "datamining"],
        "big data": ["big-data", "big_data", "bigdata"],
        "data analysis": ["data-analysis", "data_analysis", "dataanalysis"],
        "sentiment analysis": ["sentiment-analysis", "sentiment_analysis", "sentimentanalysis"],
        "statistical analysis": ["statistical-analysis", "statistical_analysis", "statisticalanalysis"],
        "structural equation modeling": ["sem", "pls-sem", "pls sem", "structural equation model"],

        # === 기술 관련 ===
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

# --- 데이터 로드 함수 (기존과 동일) ---
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

# --- 개선된 논문 분류 함수 ---
def classify_article(row):
    """
    라이브 스트리밍 연구를 위한 개선된 분류 알고리즘
    - 포괄적 연구 범위 적용
    - 기술적 기반 연구 포함
    - 명확한 제외 기준만 적용
    """
    
    # === 1단계: 핵심 포함 키워드 (확장) ===
    core_inclusion_keywords = [
        # 직접적 라이브 스트리밍
        'live streaming', 'livestreaming', 'live stream', 'live broadcast', 'live video',
        'real time streaming', 'real-time streaming', 'streaming platform', 'streaming service',
        
        # 라이브 커머스 및 상업적 활용
        'live commerce', 'live shopping', 'live selling', 'livestream commerce',
        'social commerce', 'live marketing', 'streaming monetization',
        
        # 사용자 및 사회적 측면
        'streamer', 'viewer', 'audience engagement', 'streaming audience', 'live audience',
        'streaming behavior', 'viewer behavior', 'streaming experience', 'live interaction',
        'streaming community', 'online community', 'digital community',
        
        # 플랫폼 관련
        'twitch', 'youtube live', 'facebook live', 'instagram live', 'tiktok live',
        'streaming media', 'video streaming', 'audio streaming', 'multimedia streaming',
        
        # 교육 및 엔터테인먼트
        'live learning', 'streaming education', 'online education', 'e-learning',
        'gaming stream', 'esports', 'live gaming', 'streaming content',
        
        # 비즈니스 및 마케팅
        'influencer marketing', 'content creator', 'digital marketing', 'brand engagement',
        'consumer behavior', 'purchase intention', 'social influence'
    ]
    
    # === 2단계: 기술적 포함 키워드 ===
    technical_inclusion_keywords = [
        'real time video', 'real-time video', 'video compression', 'video encoding',
        'adaptive streaming', 'video quality', 'streaming quality', 'latency',
        'video delivery', 'content delivery', 'cdn', 'edge computing',
        'multimedia communication', 'video communication', 'webrtc',
        'peer to peer streaming', 'p2p streaming', 'distributed streaming',
        'mobile streaming', 'mobile video', 'wireless streaming',
        'mobile broadcast', 'smartphone streaming'
    ]
    
    # === 3단계: 명확한 제외 키워드 (최소화) ===
    clear_exclusion_keywords = [
        # 순수 네트워크 프로토콜
        'routing protocol', 'network topology', 'packet routing', 'mac protocol', 
        'ieee 802.11', 'wimax protocol', 'lte protocol',
        
        # 하드웨어 설계
        'vlsi design', 'circuit design', 'antenna design', 'rf circuit',
        'hardware implementation', 'fpga implementation', 'asic design',
        
        # 물리계층 신호처리
        'signal processing algorithm', 'modulation scheme', 'channel estimation',
        'beamforming', 'mimo antenna', 'ofdm modulation',
        
        # 비관련 도메인
        'satellite communication', 'underwater communication', 'space communication',
        'biomedical signal', 'medical imaging', 'radar system'
    ]
    
    # === 4단계: 텍스트 추출 ===
    title = str(row.get('TI', '')).lower()
    source_title = str(row.get('SO', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    
    # === 5단계: 분류 로직 ===
    
    # 1차: 명확한 제외 대상
    if any(keyword in full_text for keyword in clear_exclusion_keywords):
        return 'Exclude (기술적 비관련)'
    
    # 2차: 핵심 라이브 스트리밍 연구
    if any(keyword in full_text for keyword in core_inclusion_keywords):
        return 'Include (핵심연구)'
    
    # 3차: 기술적 기반 연구
    if any(keyword in full_text for keyword in technical_inclusion_keywords):
        # 추가 검증: 라이브 스트리밍 연관성
        live_indicators = ['live', 'real time', 'real-time', 'streaming', 'broadcast', 'interactive']
        if any(indicator in full_text for indicator in live_indicators):
            return 'Include (기술기반)'
        else:
            return 'Review (기술검토)'
    
    # 4차: 일반적 관련성
    general_keywords = [
        'social media', 'social network', 'online platform', 'digital platform',
        'user experience', 'user behavior', 'consumer behavior', 'online behavior',
        'digital marketing', 'online marketing', 'content creation', 'content sharing',
        'video content', 'multimedia content', 'interactive media'
    ]
    
    if any(keyword in full_text for keyword in general_keywords):
        return 'Review (일반관련)'
    
    # 5차: 기타
    return 'Review (검토필요)'

def clean_keyword_string(keywords_str, stop_words, lemmatizer):
    """SciMAT 최적화된 키워드 정제 처리"""
    if pd.isna(keywords_str) or not isinstance(keywords_str, str):
        return ""

    # SciMAT 호환 특수문자 처리
    keywords_str = re.sub(r'[^\w\s\-;]', '', keywords_str)  # 기본 특수문자 제거
    keywords_str = re.sub(r'\s+', ' ', keywords_str)        # 다중 공백 정리
    
    all_keywords = keywords_str.split(';')
    cleaned_keywords = set()

    for keyword in all_keywords:
        if not keyword.strip():
            continue

        # 1단계: 기본 정제
        keyword_clean = keyword.strip().lower()
        keyword_clean = re.sub(r'[^a-z\s\-_]', '', keyword_clean)
        keyword_clean = re.sub(r'\s+', ' ', keyword_clean).strip()
        
        # 길이 제한 (SciMAT 권장)
        if len(keyword_clean) < 3 or len(keyword_clean) > 50:
            continue

        # 2단계: 구문 단위 정규화
        normalized_phrase = normalize_keyword_phrase(keyword_clean)

        # 3단계: 단어별 처리 (구문 정규화가 안된 경우)
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

# --- SCIMAT 형식 변환 함수 (기존과 동일) ---
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
    <h1 style="font-size: 3.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
        WOS Prep
    </h1>
    <p style="font-size: 1.3rem; margin: 0; font-weight: 400; opacity: 0.95;">
        Professional Tool for Web of Science Data Pre-processing (Live Streaming Research Optimized)
    </p>
    <div style="width: 100px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 주요 기능 소개 ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">라이브 스트리밍 특화 분류</div>
        <div class="feature-desc">29년 진화 연구를 위한 포괄적 논문 선별</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🏷️</div>
        <div class="feature-title">SciMAT 최적화</div>
        <div class="feature-desc">안정적인 분석을 위한 키워드 전처리</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">계량서지학 지원</div>
        <div class="feature-desc">지식 구조 진화 분석 완벽 지원</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 키워드 정규화 기준 설명 ---
with st.expander("ℹ️ 라이브 스트리밍 특화 정규화 기준", expanded=False):
    st.markdown("""
    <div class="info-panel">
        <h4 style="color: #003875; margin-bottom: 16px;">적용되는 정규화 규칙:</h4>
        <ul style="line-height: 1.8; color: #495057;">
            <li><strong>라이브 스트리밍:</strong> live streaming ← live-streaming, livestreaming, real time streaming</li>
            <li><strong>라이브 커머스:</strong> live commerce ← live-commerce, livestream commerce, live shopping</li>
            <li><strong>스트리밍 플랫폼:</strong> streaming platform ← streaming-platform, stream platform</li>
            <li><strong>사용자 행동:</strong> user behavior ← user-behavior, userbehavior, user behaviour</li>
            <li><strong>AI/ML 용어:</strong> machine learning ← machine-learning, ML, machinelearning</li>
            <li><strong>연구방법론:</strong> structural equation modeling ← SEM, PLS-SEM</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- 개선된 분류 기준 설명 ---
with st.expander("🎯 개선된 분류 기준 (라이브 스트리밍 연구 특화)", expanded=False):
    st.markdown("""
    <div class="info-panel">
        <h4 style="color: #003875; margin-bottom: 16px;">포괄적 연구 범위:</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
            <div>
                <h5 style="color: #28a745; margin-bottom: 8px;">✅ Include (핵심연구)</h5>
                <p style="font-size: 0.9rem; color: #495057;">라이브 스트리밍, 라이브 커머스, 사용자 행동, 스트리밍 플랫폼 등</p>
            </div>
            <div>
                <h5 style="color: #17a2b8; margin-bottom: 8px;">🔧 Include (기술기반)</h5>
                <p style="font-size: 0.9rem; color: #495057;">실시간 비디오, 적응형 스트리밍, CDN, WebRTC 등</p>
            </div>
            <div>
                <h5 style="color: #ffc107; margin-bottom: 8px;">📝 Review (일반관련)</h5>
                <p style="font-size: 0.9rem; color: #495057;">소셜 미디어, 디지털 마케팅, 온라인 플랫폼 등</p>
            </div>
            <div>
                <h5 style="color: #dc3545; margin-bottom: 8px;">❌ Exclude (기술적 비관련)</h5>
                <p style="font-size: 0.9rem; color: #495057;">순수 하드웨어, 네트워크 프로토콜, 신호처리 등</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 나머지 코드는 기존과 동일하게 유지...
# (파일 업로드, 분석 로직, 차트 생성, 다운로드 등)
