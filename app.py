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
    page_title="WOS Prep | SciMAT Compatible Edition",
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
    
    .warning-panel {
        background: #fff3cd;
        border: 1px solid #ffc107;
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

# --- 라이브 스트리밍 특화 분류 함수 (기존과 동일) ---
def classify_article(row):
    """라이브 스트리밍 연구를 위한 포괄적 분류"""
    
    # 핵심 포함 키워드
    core_inclusion_keywords = [
        'live streaming', 'livestreaming', 'live stream', 'live broadcast', 'live video',
        'real time streaming', 'real-time streaming', 'streaming platform', 'streaming service',
        'live commerce', 'live shopping', 'live selling', 'livestream commerce',
        'social commerce', 'live marketing', 'streaming monetization',
        'streamer', 'viewer', 'audience engagement', 'streaming audience', 'live audience',
        'streaming behavior', 'viewer behavior', 'streaming experience', 'live interaction',
        'streaming community', 'online community', 'digital community',
        'twitch', 'youtube live', 'facebook live', 'instagram live', 'tiktok live',
        'streaming media', 'video streaming', 'audio streaming', 'multimedia streaming',
        'live learning', 'streaming education', 'online education', 'e-learning',
        'gaming stream', 'esports', 'live gaming', 'streaming content',
        'influencer marketing', 'content creator', 'digital marketing', 'brand engagement',
        'consumer behavior', 'purchase intention', 'social influence'
    ]
    
    # 기술적 포함 키워드
    technical_inclusion_keywords = [
        'real time video', 'real-time video', 'video compression', 'video encoding',
        'adaptive streaming', 'video quality', 'streaming quality', 'latency',
        'video delivery', 'content delivery', 'cdn', 'edge computing',
        'multimedia communication', 'video communication', 'webrtc',
        'peer to peer streaming', 'p2p streaming', 'distributed streaming',
        'mobile streaming', 'mobile video', 'wireless streaming',
        'mobile broadcast', 'smartphone streaming'
    ]
    
    # 명확한 제외 키워드 (최소화)
    clear_exclusion_keywords = [
        'routing protocol', 'network topology', 'packet routing', 'mac protocol', 
        'ieee 802.11', 'wimax protocol', 'lte protocol',
        'vlsi design', 'circuit design', 'antenna design', 'rf circuit',
        'hardware implementation', 'fpga implementation', 'asic design',
        'signal processing algorithm', 'modulation scheme', 'channel estimation',
        'beamforming', 'mimo antenna', 'ofdm modulation',
        'satellite communication', 'underwater communication', 'space communication',
        'biomedical signal', 'medical imaging', 'radar system'
    ]
    
    # 텍스트 추출
    title = str(row.get('TI', '')).lower()
    source_title = str(row.get('SO', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    
    # 분류 로직
    if any(keyword in full_text for keyword in clear_exclusion_keywords):
        return 'Exclude (기술적 비관련)'
    
    if any(keyword in full_text for keyword in core_inclusion_keywords):
        return 'Include (핵심연구)'
    
    if any(keyword in full_text for keyword in technical_inclusion_keywords):
        live_indicators = ['live', 'real time', 'real-time', 'streaming', 'broadcast', 'interactive']
        if any(indicator in full_text for indicator in live_indicators):
            return 'Include (기술기반)'
        else:
            return 'Review (기술검토)'
    
    general_keywords = [
        'social media', 'social network', 'online platform', 'digital platform',
        'user experience', 'user behavior', 'consumer behavior', 'online behavior',
        'digital marketing', 'online marketing', 'content creation', 'content sharing',
        'video content', 'multimedia content', 'interactive media'
    ]
    
    if any(keyword in full_text for keyword in general_keywords):
        return 'Review (일반관련)'
    
    return 'Review (검토필요)'

# --- SciMAT 호환성 최우선 키워드 처리 ---
def scimat_compatible_keyword_processing(keywords_str):
    """
    SciMAT 호환성을 위한 최소한의 키워드 처리
    - 다양성 보존 (정규화 최소화)
    - 기본 정리만 수행
    - Word Group 기능이 작동할 수 있도록 원시성 유지
    """
    if pd.isna(keywords_str) or not isinstance(keywords_str, str) or not keywords_str.strip():
        return ""
    
    # 1. 기본 분리
    if ';' in keywords_str:
        keywords_list = keywords_str.split(';')
    elif ',' in keywords_str:
        keywords_list = keywords_str.split(',')
    else:
        keywords_list = [keywords_str]
    
    # 2. 최소한의 정리만 수행
    cleaned_keywords = []
    for keyword in keywords_list:
        keyword = keyword.strip()
        
        # 빈 키워드 제거
        if not keyword:
            continue
        
        # 길이 제한만 적용 (SciMAT 기본 요구사항)
        if len(keyword) < 2 or len(keyword) > 100:
            continue
        
        # 극심한 특수문자만 제거 (SciMAT 파싱 오류 방지용)
        keyword = re.sub(r'[^\w\s\-\.&\(\)]', '', keyword)  # 기본 문자만 유지
        keyword = re.sub(r'\s+', ' ', keyword).strip()  # 다중 공백 정리
        
        if keyword:
            # 원본 형태 최대한 보존 (대소문자, 띄어쓰기 등)
            cleaned_keywords.append(keyword)
    
    # 3. 중복 제거 (대소문자 구분하여 다양성 보존)
    # 완전히 동일한 것만 제거
    seen = set()
    final_keywords = []
    for kw in cleaned_keywords:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            final_keywords.append(kw)
    
    # 4. SciMAT 표준 구분자로 연결
    return '; '.join(final_keywords)

# --- SCIMAT 형식 변환 함수 ---
def convert_df_to_scimat_format(df_to_convert):
    """SciMAT 호환 WOS 형식으로 변환"""
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
                        file_content.append(f"   {item}")
            else:
                file_content.append(f"{tag} {value}")

        file_content.append("ER")
    return "\n".join(file_content).encode('utf-8')

# --- SciMAT 호환성 진단 함수 ---
def diagnose_scimat_readiness(df):
    """SciMAT 준비도 진단"""
    issues = []
    recommendations = []
    
    # 1. 필수 필드 확인
    if 'DE' not in df.columns and 'ID' not in df.columns:
        issues.append("❌ 키워드 필드 없음: DE 또는 ID 필드 필요")
    
    # 2. 키워드 필드 분석
    for field in ['DE', 'ID']:
        if field in df.columns:
            valid_keywords = df[field].dropna()
            valid_keywords = valid_keywords[valid_keywords != '']
            
            if len(valid_keywords) == 0:
                issues.append(f"❌ {field} 필드에 유효한 키워드 없음")
                continue
            
            # 키워드 다양성 확인
            all_keywords = []
            for keywords_str in valid_keywords:
                keywords_list = str(keywords_str).split(';')
                all_keywords.extend([kw.strip().lower() for kw in keywords_list if kw.strip()])
            
            unique_keywords = len(set(all_keywords))
            total_keywords = len(all_keywords)
            diversity_ratio = unique_keywords / total_keywords if total_keywords > 0 else 0
            
            if diversity_ratio < 0.3:
                issues.append(f"⚠️ {field} 키워드 다양성 부족 ({diversity_ratio:.1%})")
                recommendations.append(f"💡 {field} 키워드 정규화 강도를 낮춰 다양성 확보")
            
            # 평균 키워드 수 확인
            keyword_counts = []
            for keywords_str in valid_keywords.head(100):  # 샘플 100개
                count = len([kw.strip() for kw in str(keywords_str).split(';') if kw.strip()])
                keyword_counts.append(count)
            
            avg_keywords = sum(keyword_counts) / len(keyword_counts) if keyword_counts else 0
            
            if avg_keywords < 2:
                issues.append(f"⚠️ {field} 평균 키워드 수 부족 ({avg_keywords:.1f}개)")
                recommendations.append(f"💡 {field} 키워드 삭제 기준 완화 필요")
    
    return issues, recommendations

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
    <h1 style="font-size: 3.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
        WOS Prep
    </h1>
    <p style="font-size: 1.3rem; margin: 0; font-weight: 400; opacity: 0.95;">
        SciMAT Compatible Edition for Live Streaming Research
    </p>
    <div style="width: 100px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 주요 기능 소개 ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">SciMAT 호환성 최우선</div>
        <div class="feature-desc">Word Group 기능이 정상 작동하도록 설계</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">라이브 스트리밍 특화</div>
        <div class="feature-desc">29년 연구 진화 분석을 위한 포괄적 분류</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">최소 전처리</div>
        <div class="feature-desc">키워드 다양성 보존으로 그룹핑 효과 극대화</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SciMAT 호환성 안내 ---
st.markdown("""
<div class="warning-panel">
    <h4 style="color: #856404; margin-bottom: 16px;">🎯 SciMAT 호환성 전략</h4>
    <ul style="line-height: 1.8; color: #856404;">
        <li><strong>키워드 다양성 보존:</strong> 정규화보다는 원본 형태 유지 우선</li>
        <li><strong>최소 전처리:</strong> SciMAT 파싱 오류만 방지하는 수준</li>
        <li><strong>Word Group 최적화:</strong> 유사 키워드가 존재해야 그룹핑 가능</li>
        <li><strong>세미콜론 구분자:</strong> SciMAT 표준 구분자 엄격 준수</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">📁 데이터 업로드</div>
    <div class="section-subtitle">Web of Science Raw Data 파일을 업로드하여 SciMAT 호환 분석을 시작하세요.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="upload-zone">
    <div style="font-size: 3rem; margin-bottom: 16px; color: #003875;">📤</div>
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
    
    with st.spinner("🔄 SciMAT 호환성을 고려하여 데이터를 처리하고 있습니다..."):
        # 1단계: 논문 분류
        df['Classification'] = df.apply(classify_article, axis=1)

        # 2단계: 원본 백업
        if 'DE' in df.columns: df['DE_Original'] = df['DE'].copy()
        if 'ID' in df.columns: df['ID_Original'] = df['ID'].copy()

        # 3단계: SciMAT 호환 키워드 처리 (포함된 논문만)
        include_mask = df['Classification'].str.contains('Include', na=False)

        if 'DE' in df.columns:
            df['DE_processed'] = df['DE'].copy()
            df.loc[include_mask, 'DE_processed'] = df.loc[include_mask, 'DE'].apply(scimat_compatible_keyword_processing)
        
        if 'ID' in df.columns:
            df['ID_processed'] = df['ID'].copy()
            df.loc[include_mask, 'ID_processed'] = df.loc[include_mask, 'ID'].apply(scimat_compatible_keyword_processing)

    st.success("✅ SciMAT 호환 처리 완료!")

    # --- SciMAT 준비도 진단 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">🔍 SciMAT 준비도 진단</div>
        <div class="section-subtitle">SciMAT Word Group 기능 작동 가능성 검증</div>
    </div>
    """, unsafe_allow_html=True)

    # 진단 실행
    df_for_diagnosis = df.copy()
    if 'DE_processed' in df_for_diagnosis.columns:
        df_for_diagnosis['DE'] = df_for_diagnosis['DE_processed']
    if 'ID_processed' in df_for_diagnosis.columns:
        df_for_diagnosis['ID'] = df_for_diagnosis['ID_processed']

    issues, recommendations = diagnose_scimat_readiness(df_for_diagnosis)

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">⚠️ 발견된 문제점</div>', unsafe_allow_html=True)
        
        if issues:
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.markdown("✅ **문제점 없음** - SciMAT에서 정상 작동 예상")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">💡 개선 권장사항</div>', unsafe_allow_html=True)
        
        if recommendations:
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.markdown("🎯 **추가 개선 불필요** - 현재 상태가 최적")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 분석 결과 요약</div>
        <div class="section-subtitle">처리 결과 및 SciMAT 준비 현황</div>
    </div>
    """, unsafe_allow_html=True)

    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    classification_counts = df['Classification'].value_counts()
    total_papers = len(df)
    include_papers = len(df[df['Classification'].str.contains('Include', na=False)])
    
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
            <div class="metric-label">Included Studies</div>
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
        # 키워드 다양성 계산
        diversity_score = 0
        if 'DE_processed' in df.columns:
            all_keywords = []
            for text in df.loc[include_mask, 'DE_processed'].dropna():
                keywords = [kw.strip().lower() for kw in text.split(';') if kw.strip()]
                all_keywords.extend(keywords)
            
            if all_keywords:
                unique_count = len(set(all_keywords))
                total_count = len(all_keywords)
                diversity_score = (unique_count / total_count * 100) if total_count > 0 else 0
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-value">{diversity_score:.1f}%</div>
            <div class="metric-label">Keyword Diversity</div>
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
        # 도넛 차트
        selection = alt.selection_point(fields=['분류'], on='mouseover', nearest=True)

        base = alt.Chart(classification_counts_df).encode(
            theta=alt.Theta(field="논문 수", type="quantitative", stack=True),
            color=alt.Color(field="분류", type="nominal", title="Classification",
                           scale=alt.Scale(range=['#003875', '#0056b3', '#17a2b8', '#ffc107', '#dc3545']),
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

    # --- 키워드 처리 전후 비교 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Keyword Processing Comparison (SciMAT Compatibility Focus)</div>
    """, unsafe_allow_html=True)
    
    if st.checkbox("🔍 키워드 처리 전후 비교 보기 (샘플)", key="comparison_check"):
        sample_data = []
        sample_rows = df.loc[include_mask].head(5)
        
        for idx, row in sample_rows.iterrows():
            if 'DE_Original' in df.columns and pd.notna(row.get('DE_Original')):
                original = str(row['DE_Original'])[:100] + "..." if len(str(row['DE_Original'])) > 100 else str(row['DE_Original'])
                processed = str(row.get('DE_processed', ''))[:100] + "..." if len(str(row.get('DE_processed', ''))) > 100 else str(row.get('DE_processed', ''))
                
                # 키워드 수 계산
                original_count = len([k.strip() for k in str(row['DE_Original']).split(';') if k.strip()]) if pd.notna(row['DE_Original']) else 0
                processed_count = len([k.strip() for k in str(row.get('DE_processed', '')).split(';') if k.strip()]) if row.get('DE_processed') else 0
                
                sample_data.append({
                    '논문 ID': f"#{idx}",
                    '필드': 'DE (Author Keywords)',
                    '원본 키워드': original,
                    '처리 후 키워드': processed,
                    '원본 수': original_count,
                    '처리 후 수': processed_count,
                    '보존율': f"{(processed_count/original_count*100):.1f}%" if original_count > 0 else "0%"
                })
        
        if sample_data:
            comparison_df = pd.DataFrame(sample_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            
            # 보존율 통계
            preservation_rates = [float(d['보존율'].replace('%', '')) for d in sample_data if d['보존율'] != '0%']
            if preservation_rates:
                avg_preservation = sum(preservation_rates) / len(preservation_rates)
                
                if avg_preservation >= 90:
                    st.success(f"✅ 우수한 키워드 보존율: 평균 {avg_preservation:.1f}% (SciMAT Word Group 정상 작동 예상)")
                elif avg_preservation >= 70:
                    st.warning(f"⚠️ 양호한 키워드 보존율: 평균 {avg_preservation:.1f}% (SciMAT에서 일부 그룹핑 제한 가능)")
                else:
                    st.error(f"❌ 낮은 키워드 보존율: 평균 {avg_preservation:.1f}% (Word Group 기능 제한적)")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 연도별 연구 동향 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Research Trend Analysis (1996-2024)</div>
    """, unsafe_allow_html=True)
    
    df_trend = df.copy()
    if 'PY' in df_trend.columns:
        df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
        df_trend.dropna(subset=['PY'], inplace=True)
        df_trend['PY'] = df_trend['PY'].astype(int)
        
        yearly_counts = df_trend['PY'].value_counts().reset_index()
        yearly_counts.columns = ['Year', 'Count']
        yearly_counts = yearly_counts[yearly_counts['Year'] <= 2025].sort_values('Year')

        selection_trend = alt.selection_point(fields=['Year'], on='mouseover', nearest=True, empty='none')
        
        line_chart = alt.Chart(yearly_counts).mark_line(
            point={'size': 80, 'filled': True}, strokeWidth=3, color='#003875'
        ).encode(
            x=alt.X('Year:O', title='발행 연도'),
            y=alt.Y('Count:Q', title='논문 수'),
            tooltip=['Year', 'Count'],
            opacity=alt.condition(selection_trend, alt.value(1), alt.value(0.8))
        ).add_params(selection_trend)
        
        trend_chart = line_chart.properties(height=350)
        st.altair_chart(trend_chart, use_container_width=True)
        
        # 변곡점 분석
        if len(yearly_counts) >= 10:
            st.markdown("""
            <div class="info-panel">
                <h4 style="color: #003875; margin-bottom: 12px;">📈 29년 연구 진화 패턴</h4>
                <p style="margin: 4px 0; color: #495057;">• <strong>1996-2006 (태동기):</strong> 기술적 기반 연구 중심</p>
                <p style="margin: 4px 0; color: #495057;">• <strong>2007-2016 (형성기):</strong> 플랫폼 등장과 사용자 연구 시작</p>
                <p style="margin: 4px 0; color: #495057;">• <strong>2017-2021 (확산기):</strong> 소셜 미디어와 상업적 활용 급증</p>
                <p style="margin: 4px 0; color: #495057;">• <strong>2022-2024 (성숙기):</strong> 라이브 커머스와 메타버스 융합</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 발행 연도(PY) 데이터가 없어 연구 동향을 분석할 수 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 최종 데이터셋 준비 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">💾 SciMAT 호환 파일 다운로드</div>
        <div class="section-subtitle">Word Group 기능 최적화된 최종 데이터셋</div>
    </div>
    """, unsafe_allow_html=True)

    # 최종 데이터셋 준비
    df_final = df[~df['Classification'].str.contains('Exclude', na=False)].copy()
    
    # 처리된 키워드 적용
    if 'DE_processed' in df_final.columns:
        df_final['DE'] = df_final['DE_processed']
    if 'ID_processed' in df_final.columns:
        df_final['ID'] = df_final['ID_processed']
    
    # 불필요한 컬럼 제거
    cols_to_drop = ['Classification', 'DE_processed', 'ID_processed', 'DE_Original', 'ID_Original']
    df_final_output = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns], errors='ignore')

    # 최종 통계
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        include_count = len(df[df['Classification'].str.contains('Include', na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{include_count:,}</div>
            <div class="metric-label">핵심 + 기술기반</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        review_count = len(df[df['Classification'].str.contains('Review', na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📝</div>
            <div class="metric-value">{review_count:,}</div>
            <div class="metric-label">검토 대상</div>
        </div>
        """, unsafe_allow_html=True)

    # SciMAT 호환 파일 다운로드
    text_data = convert_df_to_scimat_format(df_final_output)
    
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        st.download_button(
            label="🔥 SciMAT 호환 파일 다운로드 (.txt)",
            data=text_data,
            file_name="live_streaming_scimat_compatible.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        # 테스트 파일 다운로드 (50개 샘플)
        df_test = df_final_output.head(50)
        test_data = convert_df_to_scimat_format(df_test)
        
        st.download_button(
            label="🧪 테스트 파일 (50개)",
            data=test_data,
            file_name="test_scimat_50papers.txt",
            mime="text/plain",
            use_container_width=True
        )

    # SciMAT 사용 가이드
    st.markdown("""
    <div class="info-panel">
        <h4 style="color: #003875; margin-bottom: 16px;">🎯 SciMAT 사용 가이드 (호환성 우선)</h4>
        <ol style="line-height: 1.8; color: #495057;">
            <li><strong>테스트 우선:</strong> 먼저 <code>test_scimat_50papers.txt</code> 파일로 SciMAT에서 정상 작동 확인</li>
            <li><strong>Word Group 확인:</strong> <code>Group set → Words groups manager</code>에서 키워드 목록이 나타나는지 검증</li>
            <li><strong>자동 그룹핑:</strong> Levenshtein distance로 유사 키워드 자동 그룹화 시도</li>
            <li><strong>수동 조정:</strong> 라이브 스트리밍 특화 키워드 그룹 수동 생성</li>
            <li><strong>전체 분석:</strong> 테스트 성공 시 전체 파일로 29년 진화 분석 실행</li>
        </ol>
        
        <div style="margin-top: 16px; padding: 12px; background: #d1ecf1; border-left: 4px solid #17a2b8; border-radius: 4px;">
            <strong>💡 핵심 포인트:</strong> 이 파일은 키워드 다양성을 최대한 보존하여 SciMAT Word Group 기능이 정상 작동하도록 설계되었습니다.
        </div>
        
        <div style="margin-top: 12px; padding: 12px; background: #d4edda; border-left: 4px solid #28a745; border-radius: 4px;">
            <strong>🎯 예상 결과:</strong> 라이브 스트리밍 연구 분야 최초의 종합적 지식 구조 진화 분석 (1996-2024)
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 하단 여백 ---
st.markdown("<br><br>", unsafe_allow_html=True)
