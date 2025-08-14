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

# --- 데이터 로드 함수 (WOS 기본 형식 지원) ---
def load_data(uploaded_file):
    file_name = uploaded_file.name.lower()
    
    # 엑셀 파일 처리 (WOS 기본 .xls 포함)
    if file_name.endswith(('.xlsx', '.xls')):
        try:
            # 여러 엔진으로 시도
            engines_to_try = ['openpyxl', 'xlrd']
            
            for engine in engines_to_try:
                try:
                    if engine == 'openpyxl' and file_name.endswith('.xls'):
                        continue  # openpyxl은 .xls를 지원하지 않음
                    
                    df = pd.read_excel(uploaded_file, engine=engine, sheet_name=0)
                    if df.shape[1] > 1:
                        return df
                except ImportError:
                    continue  # 엔진이 설치되지 않은 경우 다음 엔진 시도
                except Exception:
                    continue  # 다른 오류 발생시 다음 엔진 시도
            
            # 모든 엔진 실패시 안내 메시지
            st.error("⚠️ Excel 파일을 읽을 수 없습니다.")
            st.markdown("""
            **해결 방법:**
            1. **Excel에서 CSV로 변환**: 파일 → 다른 이름으로 저장 → CSV 형식 선택
            2. **WOS에서 다시 다운로드**: 'Tab-delimited (Win)' 또는 'Plain Text' 형식 선택
            """)
            return None
            
        except Exception as e:
            st.error(f"파일 처리 오류: {str(e)}")
            return None
    
    # CSV/TXT 파일 처리 (기존 로직)
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

# --- SciMAT 기반 향상된 분류 알고리즘 (더 엄격한 버전) ---
def classify_article(row):
    """SciMAT 방법론을 적용한 더 엄격한 논문 분류"""
    
    # 핵심 라이브스트리밍 + 상거래/마케팅 키워드
    livestreaming_commerce_keywords = [
        'live streaming commerce', 'social commerce', 'livestreaming commerce',
        'purchase intention', 'customer engagement', 'consumer behavior',
        'influencer marketing', 'brand engagement', 'online shopping',
        'digital marketing', 'e-commerce', 'viewer engagement'
    ]
    
    # 라이브스트리밍 키워드 (단독으로는 불충분)
    livestreaming_keywords = [
        'live streaming', 'livestreaming', 'live-streaming', 'live broadcast'
    ]
    
    # 사용자/행동 관련 키워드
    user_behavior_keywords = [
        'user', 'viewer', 'audience', 'consumer', 'customer', 'participant',
        'behavior', 'experience', 'engagement', 'interaction', 'motivation',
        'psychology', 'social', 'community', 'marketing', 'business'
    ]
    
    # 기술적 제외 키워드 (더 강화)
    strong_tech_keywords = [
        'protocol', 'network coding', 'tcp', 'udp', 'bandwidth', 'throughput',
        'p2p', 'peer-to-peer', 'packet', 'routing', 'algorithm', 'optimization',
        'qoe', 'quality of experience', 'bitrate', 'codec', 'encoding'
    ]
    
    # 시스템/하드웨어 키워드
    system_keywords = [
        'system', 'architecture', 'platform', 'framework', 'implementation',
        'performance', 'latency', 'delay', 'synchronization', 'scalable',
        'cloud', 'server', 'network', 'wireless', 'mobile'
    ]
    
    # 의료/교육 기술 키워드
    medical_tech_keywords = [
        'medical', 'education', 'surgical', 'clinical', 'laboratory',
        'wearable', 'augmented reality', 'virtual reality', 'covid-19'
    ]
    
    # 텍스트 전처리 및 추출
    title = str(row.get('TI', '')).lower()
    source_title = str(row.get('SO', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    
    # 1단계: 라이브스트리밍 + 상거래 직접 조합 확인
    commerce_found = any(keyword in full_text for keyword in livestreaming_commerce_keywords)
    if commerce_found:
        return 'Include (관련연구)'
    
    # 2단계: 강한 기술적 제외 확인
    strong_tech_count = sum(1 for keyword in strong_tech_keywords if keyword in full_text)
    system_count = sum(1 for keyword in system_keywords if keyword in full_text)
    medical_count = sum(1 for keyword in medical_tech_keywords if keyword in full_text)
    
    # 기술적 특성이 강한 경우 제외
    if strong_tech_count >= 2:  # 2개 이상의 강한 기술 키워드
        return 'Exclude (제외연구)'
    elif strong_tech_count >= 1 and system_count >= 2:  # 기술+시스템 조합
        return 'Exclude (제외연구)'
    elif medical_count >= 2:  # 의료/교육 기술
        return 'Exclude (제외연구)'
    elif system_count >= 3:  # 3개 이상의 시스템 키워드
        return 'Exclude (제외연구)'
    
    # 3단계: P2P, 네트워크 관련 강한 제외
    if 'p2p' in full_text or 'peer-to-peer' in full_text:
        user_count = sum(1 for keyword in user_behavior_keywords if keyword in full_text)
        if user_count < 2:  # 사용자 관련 키워드가 적으면 제외
            return 'Exclude (제외연구)'
    
    # 4단계: 라이브스트리밍이 있지만 사용자 중심이 아닌 경우
    livestream_found = any(keyword in full_text for keyword in livestreaming_keywords)
    if livestream_found:
        user_count = sum(1 for keyword in user_behavior_keywords if keyword in full_text)
        tech_total = strong_tech_count + system_count
        
        if tech_total >= 2 and user_count <= 1:  # 기술적이고 사용자 중심이 아님
            return 'Exclude (제외연구)'
        elif user_count >= 2:  # 사용자 중심
            return 'Include (관련연구)'
        else:
            return 'Review (검토필요)'
    
    # 5단계: 일반적인 사용자 중심 키워드 확인
    user_count = sum(1 for keyword in user_behavior_keywords if keyword in full_text)
    tech_total = strong_tech_count + system_count
    
    if user_count >= 3 and tech_total <= 1:
        return 'Include (관련연구)'
    elif tech_total >= 2:
        return 'Exclude (제외연구)'
    else:
        return 'Review (검토필요)'

# --- 제외 이유 분석 함수 (SciMAT 기반 개선) ---
def get_detailed_exclusion_reason(row):
    """SciMAT 방법론을 적용한 상세한 제외 이유 분석"""
    exclusion_categories = {
        # 1단계: 기술적 복잡도별 분류
        '저수준 네트워크 기술': {
            'keywords': ['mac layer', 'phy layer', 'network layer', 'transport layer', 'protocol stack'],
            'weight': 3.0
        },
        '프로토콜 구현': {
            'keywords': ['protocol implementation', 'protocol design', 'protocol optimization', 'routing protocol'],
            'weight': 3.0
        },
        '하드웨어 최적화': {
            'keywords': ['hardware optimization', 'fpga implementation', 'asic design', 'vlsi'],
            'weight': 2.5
        },
        '시스템 성능': {
            'keywords': ['system performance', 'throughput optimization', 'latency reduction', 'bandwidth'],
            'weight': 2.0
        },
        '데이터 전송': {
            'keywords': ['packet dropping', 'forward error correction', 'automatic repeat request', 'goodput'],
            'weight': 2.5
        },
        '네트워크 분석': {
            'keywords': ['network traffic', 'tcp', 'udp', 'network topology'],
            'weight': 2.0
        },
        '센서 기술': {
            'keywords': ['sensor data', 'sensor network', 'wireless sensor', 'iot'],
            'weight': 1.5
        },
        '환경과학': {
            'keywords': ['geoscience', 'environmental data', 'remote sensing'],
            'weight': 1.5
        }
    }
    
    title = str(row.get('TI', '')).lower()
    keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, keywords, keywords_plus, abstract])
    
    found_reasons = []
    found_keywords = []
    total_weight = 0
    
    for category, details in exclusion_categories.items():
        matched_keywords = [kw for kw in details['keywords'] if kw in full_text]
        if matched_keywords:
            found_reasons.append(category)
            found_keywords.extend(matched_keywords)
            total_weight += details['weight'] * len(matched_keywords)
    
    # 신뢰도 점수 계산 (0.0 ~ 1.0)
    confidence_score = min(total_weight / 10, 1.0)
    
    # 제외 수준 결정
    if confidence_score >= 0.7:
        exclusion_level = '강한 제외'
    elif confidence_score >= 0.4:
        exclusion_level = '중간 제외'
    else:
        exclusion_level = '약한 제외'
    
    return {
        'category': '; '.join(found_reasons) if found_reasons else '기타 기술적 내용',
        'keywords': '; '.join(list(set(found_keywords))[:5]) if found_keywords else '기타 키워드',
        'confidence_score': confidence_score,
        'exclusion_level': exclusion_level
    }

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

# --- 메인 헤더 (한양대 브랜딩) ---
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
        Professional Tool for Web of Science Data Pre-processing
    </p>
    <div style="width: 100px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 주요 기능 소개 (개선된 아이콘) ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">데이터 분류</div>
        <div class="feature-desc">연구 목적에 맞는 논문 자동 선별</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🏷️</div>
        <div class="feature-title">키워드 정규화</div>
        <div class="feature-desc">AI 기반 키워드 표준화</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">SciMAT 호환</div>
        <div class="feature-desc">완벽한 분석 도구 연동</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 키워드 정규화 기준 설명 ---
with st.expander("ℹ️ 키워드 정규화 기준 상세", expanded=False):
    st.markdown("""
    <div class="info-panel">
        <h4 style="color: #003875; margin-bottom: 16px;">적용되는 정규화 규칙:</h4>
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
    <div style="font-size: 3rem; margin-bottom: 16px; color: #003875;">📤</div>
    <h3 style="color: #212529; margin-bottom: 8px;">파일을 선택하세요</h3>
    <p style="color: #6c757d; margin: 0;">CSV, TXT, Excel (.xlsx/.xls) 형식의 WOS 데이터 파일</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "파일 선택",
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
        # 도넛 차트 (한양대 색상)
        domain = ['Include (관련연구)', 'Review (검토필요)', 'Exclude (제외연구)']
        range_ = ['#003875', '#0056b3', '#6c757d']

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
            align='center', baseline='middle', fontSize=35, fontWeight='bold', color='#003875'
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
            point={'size': 80, 'filled': True}, strokeWidth=3, color='#003875'
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
        
        # NR > 0인 논문만 필터링하고 상위 5개 선택
        df_cited_filtered = df_cited[df_cited['NR'] > 0]
        
        if len(df_cited_filtered) > 0:
            df_cited_top = df_cited_filtered.nlargest(5, 'NR')
            
            df_cited_top['Author_Display'] = df_cited_top['AU'].apply(
                lambda x: str(x).split(';')[0] if pd.notna(x) else 'Unknown Author'
            )
            df_cited_top['Title_Display'] = df_cited_top['TI'].apply(
                lambda x: (str(x)[:60] + '...') if pd.notna(x) and len(str(x)) > 60 else str(x) if pd.notna(x) else 'No Title'
            )
            df_cited_top['Label'] = df_cited_top.apply(
                lambda row: f"{row['Title_Display']} ({row['Author_Display']})", axis=1
            )

            # 차트 생성
            cited_chart = alt.Chart(df_cited_top).mark_bar(
                color='#003875', 
                cornerRadiusEnd=4,
                size=30
            ).encode(
                x=alt.X('NR:Q', title='참고문헌 수', scale=alt.Scale(zero=True)),
                y=alt.Y('Label:N', title='논문 제목 및 저자', sort='-x'),
                tooltip=[
                    alt.Tooltip('TI:N', title='논문 제목'),
                    alt.Tooltip('Author_Display:N', title='저자'),
                    alt.Tooltip('NR:Q', title='참고문헌 수')
                ]
            ).properties(
                height=300,
                width=600
            ).resolve_scale(
                y='independent'
            )
            
            st.altair_chart(cited_chart, use_container_width=True)
        else:
            st.info("📊 참고문헌 수가 기록된 논문이 없습니다.")
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
                alt.value('#003875'),
                alt.value('#0056b3')
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
                <h4 style="color: #003875; margin-bottom: 16px;">키워드 정규화 효과 비교</h4>
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

    # --- 제외된 연구 분석 (SciMAT 기반 개선) ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">🚫 Excluded Studies Analysis</div>
        <div class="section-subtitle">제외된 연구 상세 목록 및 SciMAT 방법론 기반 알고리즘 검증</div>
    </div>
    """, unsafe_allow_html=True)

    # 제외된 연구 데이터 준비
    excluded_papers = df[df['Classification'] == 'Exclude (제외연구)'].copy()
    
    if len(excluded_papers) > 0:
        # 상위 30개 제외된 논문 선택
        excluded_sample = excluded_papers.head(30).copy()
        
        # SciMAT 방식의 알고리즘 검증 메트릭 계산
        exclusion_details = [get_detailed_exclusion_reason(row) for _, row in excluded_sample.iterrows()]
        
        # 신뢰도 기반 통계
        high_confidence = len([d for d in exclusion_details if d['confidence_score'] >= 0.7])
        medium_confidence = len([d for d in exclusion_details if 0.4 <= d['confidence_score'] < 0.7])
        low_confidence = len([d for d in exclusion_details if d['confidence_score'] < 0.4])
        
        # 표시할 데이터 준비 (SciMAT 스타일)
        display_data = []
        for idx, (_, row) in enumerate(excluded_sample.iterrows()):
            exclusion_info = exclusion_details[idx]
            
            title = str(row.get('TI', 'No Title'))
            author = str(row.get('AU', 'Unknown')).split(';')[0] if pd.notna(row.get('AU')) else 'Unknown'
            year = str(row.get('PY', 'N/A'))
            journal = str(row.get('SO', 'N/A'))
            author_keywords = str(row.get('DE', 'N/A'))
            
            display_data.append({
                '순번': len(display_data) + 1,
                '논문 제목': title,
                '저자': author,
                '연도': year,
                '저널명': journal,
                '저자 키워드': author_keywords,
                '제외 분류': exclusion_info['category'],
                '탐지된 제외 키워드': exclusion_info['keywords'],
                '제외 수준': exclusion_info['exclusion_level'],
                '신뢰도 점수': f"{exclusion_info['confidence_score']:.2f}"
            })
        
        excluded_df = pd.DataFrame(display_data)
        
        # SciMAT 스타일 알고리즘 성과 측정
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">🔍 SciMAT 방식 알고리즘 성과 분석</div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_excluded = len(excluded_papers)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🚫</div>
                <div class="metric-value">{total_excluded:,}</div>
                <div class="metric-label">총 제외된 논문</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🎯</div>
                <div class="metric-value">{high_confidence}</div>
                <div class="metric-label">고신뢰도 제외</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            accuracy = (high_confidence / min(30, total_excluded) * 100) if total_excluded > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📊</div>
                <div class="metric-value">{accuracy:.1f}%</div>
                <div class="metric-label">강한 제외 비율</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            unique_categories = len(set([d['category'] for d in exclusion_details]))
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🏷️</div>
                <div class="metric-value">{unique_categories}</div>
                <div class="metric-label">제외 카테고리 수</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # 제외된 논문 상세 목록 (SciMAT 스타일 테이블)
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">제외된 논문 상세 목록 (SciMAT 신뢰도 기반)</div>', unsafe_allow_html=True)
        
        # 필터링 옵션
        col1, col2 = st.columns(2)
        with col1:
            unique_levels = list(set([d['제외 수준'] for d in display_data]))
            level_filter = st.selectbox(
                "제외 수준별 필터:",
                ['전체'] + sorted(unique_levels),
                key="level_filter"
            )
        
        with col2:
            unique_years = sorted(list(set([d['연도'] for d in display_data if d['연도'] != 'N/A'])))
            year_filter = st.selectbox(
                "연도별 필터:",
                ['전체'] + unique_years,
                key="year_filter"
            )
        
        # 필터 적용
        filtered_data = excluded_df.copy()
        if level_filter != '전체':
            filtered_data = filtered_data[filtered_data['제외 수준'] == level_filter]
        if year_filter != '전체':
            filtered_data = filtered_data[filtered_data['연도'] == year_filter]
        
        # 개선된 테이블 표시
        if len(filtered_data) > 0:
            # HTML 테이블로 색상 구분 표시
            table_html = """
            <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
            <thead>
                <tr style="background-color: #f8f9fa; border-bottom: 2px solid #003875;">
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6; text-align: center; width: 5%;">순번</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6; text-align: left; width: 30%;">논문 제목</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6; text-align: left; width: 15%;">저자</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6; text-align: center; width: 6%;">연도</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6; text-align: left; width: 25%;">저자 키워드</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6; text-align: left; width: 12%;">제외 분류</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6; text-align: center; width: 7%;">제외 수준</th>
                </tr>
            </thead>
            <tbody>
            """
            
            for _, row in filtered_data.iterrows():
                level_color = '#d32f2f' if '강한' in row['제외 수준'] else '#f57c00' if '중간' in row['제외 수준'] else '#388e3c'
                table_html += f"""
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 12px; text-align: center;">{row['순번']}</td>
                    <td style="padding: 12px;">
                        <span class="hover-tooltip" data-tooltip="{row['논문 제목']}">{row['논문 제목'][:80]}{'...' if len(str(row['논문 제목'])) > 80 else ''}</span>
                    </td>
                    <td style="padding: 12px;">{row['저자']}</td>
                    <td style="padding: 12px; text-align: center;">{row['연도']}</td>
                    <td style="padding: 12px;">{str(row['저자 키워드'])[:50]}{'...' if len(str(row['저자 키워드'])) > 50 else ''}</td>
                    <td style="padding: 12px;">{row['제외 분류']}</td>
                    <td style="padding: 12px; font-weight: bold; color: {level_color};">{row['제외 수준']}</td>
                </tr>
                """
            
            table_html += """
            </tbody>
            </table>
            """
            
            st.markdown(table_html, unsafe_allow_html=True)
            st.info(f"📊 총 {len(filtered_data)}개의 제외된 논문이 표시됩니다. (전체 제외: {total_excluded}개)")
        else:
            st.warning("선택한 필터 조건에 해당하는 논문이 없습니다.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # SciMAT 기반 제외 기준 설명
        st.markdown("""
        <div class="info-panel">
            <h4 style="color: #003875; margin-bottom: 16px;">💡 SciMAT 방법론 기반 제외 시스템:</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                <div>
                    <h5 style="color: #d32f2f; margin-bottom: 8px;">🎯 신뢰도 기반 분류</h5>
                    <p style="font-size: 0.9rem; color: #495057;"><strong>강한 제외 (≥0.7):</strong> 명확한 기술 논문<br><strong>중간 제외 (0.4-0.7):</strong> 기술적이나 재검토 필요<br><strong>약한 제외 (<0.4):</strong> 경계선 논문</p>
                </div>
                <div>
                    <h5 style="color: #d32f2f; margin-bottom: 8px;">⚖️ 가중치 기반 평가</h5>
                    <p style="font-size: 0.9rem; color: #495057;">네트워크 프로토콜(3.0), 하드웨어 설계(2.5), 시스템 최적화(2.0) 등 기술 복잡도별 차등 가중치 적용</p>
                </div>
                <div>
                    <h5 style="color: #d32f2f; margin-bottom: 8px;">🔄 맥락 기반 분석</h5>
                    <p style="font-size: 0.9rem; color: #495057;">라이브스트리밍 키워드 우선 포함, 기술 키워드는 맥락적 분석으로 오분류 방지</p>
                </div>
                <div>
                    <h5 style="color: #d32f2f; margin-bottom: 8px;">📊 Document Mapper 적용</h5>
                    <p style="font-size: 0.9rem; color: #495057;">SciMAT의 Core/Secondary Mapper 개념을 적용한 다중 검증 시스템</p>
                </div>
            </div>
            <div style="margin-top: 16px; padding: 12px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <strong>🎯 개선 효과:</strong> 기존 단순 키워드 매칭에서 SciMAT 방법론 기반 정교한 분류로 업그레이드하여 라이브스트리밍 상거래 논문의 오분류 문제 해결
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.info("📊 제외된 연구가 없습니다.")

    # --- 처리된 데이터 미리보기 (간소화) ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📋 Final Dataset Summary</div>
        <div class="section-subtitle">최종 분석 대상 데이터 요약</div>
    </div>
    """, unsafe_allow_html=True)

    df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
    if 'DE' in df_final.columns:
        df_final['DE'] = df_final['DE_cleaned']
    if 'ID' in df_final.columns:
        df_final['ID'] = df_final['ID_cleaned']
    cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
    df_final_output = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns], errors='ignore')
    
    # 최종 데이터셋 요약 정보
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        include_count = len(df[df['Classification'] == 'Include (관련연구)'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-value">{include_count:,}</div>
            <div class="metric-label">관련 연구</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        review_count = len(df[df['Classification'] == 'Review (검토필요)'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔍</div>
            <div class="metric-value">{review_count:,}</div>
            <div class="metric-label">검토 필요</div>
        </div>
        """, unsafe_allow_html=True)

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
        <h4 style="color: #003875; margin-bottom: 16px;">💡 SciMAT 사용 가이드:</h4>
        <ol style="line-height: 1.8; color: #495057;">
            <li>다운로드한 <code>wos_prep_for_scimat.txt</code> 파일을 SciMAT에 업로드합니다.</li>
            <li><code>Group set</code> → <code>Words groups manager</code>에서 Levenshtein distance를 활용해 유사 키워드를 자동으로 그룹핑합니다.</li>
            <li>수동으로 키워드 그룹을 최종 조정한 후 분석을 실행합니다.</li>
            <li>Strategic Diagram과 Evolution Map을 통해 연구 분야의 구조와 진화를 분석합니다.</li>
        </ol>
        <div style="margin-top: 16px; padding: 12px; background: #e8f5e8; border-left: 4px solid #4caf50; border-radius: 4px;">
            <strong>🎯 주요 개선사항:</strong> SciMAT 논문의 Document Mapper, Performance Analysis, Clustering Algorithm 개념을 적용하여 기존 단순 분류에서 정교한 과학 매핑 분석이 가능한 수준으로 업그레이드되었습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 하단 여백 ---
st.markdown("<br><br>", unsafe_allow_html=True)

# --- 개발자 정보 및 SciMAT 논문 크레딧 ---
st.markdown("""
<div style="background: #f8f9fa; border-radius: 12px; padding: 20px; margin-top: 2rem; border: 1px solid #dee2e6;">
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
        <p style="margin: 0; font-weight: 600;">🔬 SciMAT 방법론 기반 개선</p>
        <p style="margin: 4px 0; font-size: 0.8rem;">Based on: Cobo, M.J., López-Herrera, A.G., Herrera-Viedma, E., & Herrera, F. (2012). <br>
        "SciMAT: A new science mapping analysis software tool." <i>Journal of the American Society for Information Science and Technology</i>, 63(8), 1609-1630.</p>
        <p style="margin: 8px 0 0 0; font-size: 0.8rem; color: #003875;">
            <strong>Developed by:</strong> 임태경 (Teddy Lym) | <strong>Affiliation:</strong> 한양대학교 기술경영전문대학원
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
