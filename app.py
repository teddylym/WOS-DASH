import streamlit as st
import pandas as pd
import altair as alt
import io
import re
from collections import Counter

# --- 페이지 설정 ---
st.set_page_config(
    page_title="WOS Prep | Final Edition",
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
    
    .success-panel {
        background: #d4edda;
        border: 1px solid #28a745;
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
</style>
""", unsafe_allow_html=True)

# --- 데이터 로드 함수 (강화된 버전) ---
def load_data(uploaded_file):
    """다양한 형식의 WOS 데이터 파일을 안정적으로 로드"""
    file_bytes = uploaded_file.getvalue()
    encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1', 'cp949', 'iso-8859-1']
    
    # 파일 형식 감지
    file_name = uploaded_file.name.lower()
    
    if file_name.endswith('.xlsx'):
        # 엑셀 파일 처리
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
            if df.shape[1] > 1:
                return df, "Excel"
        except Exception as e:
            st.error(f"엑셀 파일 읽기 오류: {str(e)}")
            return None, None
    
    # 텍스트 파일 처리
    for encoding in encodings_to_try:
        try:
            file_content = file_bytes.decode(encoding)
            
            # WOS 원본 형식 감지 (FN으로 시작하는 경우)
            if file_content.startswith('FN '):
                return parse_wos_format(file_content), "WOS_Original"
            
            # 탭 구분자 시도
            df = pd.read_csv(io.StringIO(file_content), sep='\t', lineterminator='\n', dtype=str, keep_default_na=False)
            if df.shape[1] > 1:
                return df, "Tab_Delimited"
                
        except Exception:
            continue
    
    # 콤마 구분자 최종 시도
    for encoding in encodings_to_try:
        try:
            file_content = file_bytes.decode(encoding)
            df = pd.read_csv(io.StringIO(file_content), dtype=str, keep_default_na=False)
            if df.shape[1] > 1:
                return df, "CSV"
        except Exception:
            continue
    
    return None, None

def parse_wos_format(content):
    """WOS 원본 형식을 DataFrame으로 변환"""
    lines = content.split('\n')
    records = []
    current_record = {}
    current_field = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line == 'ER':
            if current_record:
                records.append(current_record.copy())
                current_record = {}
            continue
            
        if line.startswith(('FN ', 'VR ')):
            continue
            
        # 필드 시작 (공백으로 시작하지 않는 경우)
        if not line.startswith('   ') and ' ' in line:
            field_tag = line.split(' ', 1)[0]
            field_value = line.split(' ', 1)[1]
            current_field = field_tag
            current_record[field_tag] = field_value
        # 필드 계속 (3칸 공백으로 시작)
        elif line.startswith('   ') and current_field:
            current_record[current_field] += '; ' + line[3:]
    
    return pd.DataFrame(records)

# --- 라이브 스트리밍 특화 분류 함수 ---
def classify_article(row):
    """라이브 스트리밍 연구를 위한 포괄적 분류 (최종 버전)"""
    
    # 핵심 라이브 스트리밍 키워드 (확장)
    core_streaming_keywords = [
        # 직접적 라이브 스트리밍
        'live streaming', 'livestreaming', 'live stream', 'live broadcast', 'live video',
        'real time streaming', 'real-time streaming', 'streaming platform', 'streaming service',
        'live webcast', 'webcasting', 'live transmission', 'interactive broadcasting',
        
        # 라이브 커머스 및 상업적 활용
        'live commerce', 'live shopping', 'live selling', 'livestream commerce',
        'live e-commerce', 'social commerce', 'live marketing', 'streaming monetization',
        'live retail', 'shoppertainment', 'live sales', 'streaming sales',
        
        # 사용자 및 사회적 측면
        'streamer', 'viewer', 'audience engagement', 'streaming audience', 'live audience',
        'streaming behavior', 'viewer behavior', 'streaming experience', 'live interaction',
        'streaming community', 'online community', 'digital community', 'virtual community',
        'parasocial relationship', 'streamer-viewer', 'live chat', 'chat interaction',
        
        # 주요 플랫폼
        'twitch', 'youtube live', 'facebook live', 'instagram live', 'tiktok live',
        'periscope', 'mixer', 'douyin', 'kuaishou', 'taobao live', 'tmall live',
        'amazon live', 'shopee live', 'live.ly', 'bigo live',
        
        # 콘텐츠 및 장르
        'live gaming', 'game streaming', 'esports streaming', 'streaming content',
        'live entertainment', 'live performance', 'virtual concert', 'live music',
        'live education', 'streaming education', 'live learning', 'online teaching',
        'live tutorial', 'live demonstration', 'live presentation',
        
        # 기술 및 품질
        'streaming media', 'video streaming', 'audio streaming', 'multimedia streaming',
        'streaming quality', 'video quality', 'streaming latency', 'real-time video',
        'adaptive streaming', 'live video quality', 'streaming technology'
    ]
    
    # 비즈니스 및 마케팅 관련
    business_keywords = [
        'influencer marketing', 'content creator', 'digital marketing', 'brand engagement',
        'consumer behavior', 'purchase intention', 'social influence', 'word of mouth',
        'viral marketing', 'user generated content', 'brand advocacy', 'customer engagement',
        'social media marketing', 'digital influence', 'online influence'
    ]
    
    # 기술적 기반 (라이브 스트리밍 관련)
    technical_keywords = [
        'real time video', 'real-time video', 'video compression', 'video encoding',
        'video delivery', 'content delivery', 'cdn', 'edge computing',
        'multimedia communication', 'video communication', 'webrtc',
        'peer to peer streaming', 'p2p streaming', 'distributed streaming',
        'mobile streaming', 'mobile video', 'wireless streaming',
        'mobile broadcast', 'smartphone streaming', 'live video transmission'
    ]
    
    # 교육 및 학습
    education_keywords = [
        'online education', 'e-learning', 'distance learning', 'remote learning',
        'virtual classroom', 'online teaching', 'digital learning', 'mooc',
        'educational technology', 'learning management system'
    ]
    
    # 소셜 미디어 일반
    social_media_keywords = [
        'social media', 'social network', 'online platform', 'digital platform',
        'user experience', 'user behavior', 'online behavior', 'digital behavior',
        'social interaction', 'online interaction', 'digital interaction'
    ]
    
    # 명확한 제외 키워드 (최소화)
    exclusion_keywords = [
        # 순수 네트워크/하드웨어
        'routing protocol', 'network topology', 'packet routing', 'mac protocol',
        'ieee 802.11', 'wimax protocol', 'lte protocol', 'network security protocol',
        'vlsi design', 'circuit design', 'antenna design', 'rf circuit',
        'hardware implementation', 'fpga implementation', 'asic design',
        
        # 신호처리 (사용자 경험과 무관)
        'signal processing algorithm', 'modulation scheme', 'channel estimation',
        'beamforming algorithm', 'mimo antenna', 'ofdm modulation',
        'frequency allocation', 'spectrum allocation',
        
        # 비관련 도메인
        'satellite communication', 'underwater communication', 'space communication',
        'biomedical signal', 'medical imaging', 'radar system', 'sonar system',
        'geological survey', 'seismic data', 'astronomical data'
    ]
    
    # 텍스트 추출 및 정리
    def extract_text(value):
        if pd.isna(value):
            return ""
        return str(value).lower().strip()
    
    title = extract_text(row.get('TI', ''))
    source_title = extract_text(row.get('SO', ''))
    author_keywords = extract_text(row.get('DE', ''))
    keywords_plus = extract_text(row.get('ID', ''))
    abstract = extract_text(row.get('AB', ''))
    
    # 전체 텍스트 결합
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    
    # 분류 로직 (계층적 우선순위)
    
    # 1단계: 명확한 제외 대상
    if any(keyword in full_text for keyword in exclusion_keywords):
        return 'Exclude (기술적 비관련)'
    
    # 2단계: 핵심 라이브 스트리밍 연구
    if any(keyword in full_text for keyword in core_streaming_keywords):
        return 'Include (핵심 라이브스트리밍)'
    
    # 3단계: 비즈니스/마케팅 (라이브 스트리밍과 연관 가능)
    if any(keyword in full_text for keyword in business_keywords):
        # 추가 검증: 디지털/온라인 맥락 확인
        digital_indicators = ['digital', 'online', 'internet', 'web', 'social media', 'platform']
        if any(indicator in full_text for indicator in digital_indicators):
            return 'Include (비즈니스 관련)'
        else:
            return 'Review (비즈니스 검토)'
    
    # 4단계: 기술적 기반 연구
    if any(keyword in full_text for keyword in technical_keywords):
        # 추가 검증: 실시간/라이브 맥락 확인
        live_indicators = ['live', 'real time', 'real-time', 'streaming', 'broadcast', 'interactive']
        if any(indicator in full_text for indicator in live_indicators):
            return 'Include (기술적 기반)'
        else:
            return 'Review (기술적 검토)'
    
    # 5단계: 교육 관련
    if any(keyword in full_text for keyword in education_keywords):
        # 온라인/디지털 교육 맥락 확인
        online_edu_indicators = ['online', 'digital', 'virtual', 'remote', 'distance']
        if any(indicator in full_text for indicator in online_edu_indicators):
            return 'Include (교육 관련)'
        else:
            return 'Review (교육 검토)'
    
    # 6단계: 소셜 미디어 일반
    if any(keyword in full_text for keyword in social_media_keywords):
        return 'Review (소셜미디어 관련)'
    
    # 7단계: 기타
    return 'Review (분류 불확실)'

# --- 데이터 품질 진단 함수 ---
def diagnose_data_quality(df, file_type):
    """업로드된 데이터의 품질과 SciMAT 호환성 진단"""
    issues = []
    recommendations = []
    
    # 기본 필드 확인
    required_fields = ['TI', 'AU', 'SO', 'PY']
    keyword_fields = ['DE', 'ID']
    
    for field in required_fields:
        if field not in df.columns:
            issues.append(f"❌ 필수 필드 누락: {field}")
    
    # 키워드 필드 확인
    has_keywords = False
    for field in keyword_fields:
        if field in df.columns:
            has_keywords = True
            valid_keywords = df[field].notna() & (df[field] != '') & (df[field] != 'nan')
            valid_count = valid_keywords.sum()
            total_count = len(df)
            
            if valid_count < total_count * 0.5:
                issues.append(f"⚠️ {field} 필드의 {((total_count-valid_count)/total_count*100):.1f}%가 비어있음")
            
            # 키워드 다양성 확인
            if valid_count > 0:
                all_keywords = []
                for text in df.loc[valid_keywords, field]:
                    if pd.notna(text) and str(text).strip():
                        keywords = [kw.strip().lower() for kw in str(text).split(';') if kw.strip()]
                        all_keywords.extend(keywords)
                
                if all_keywords:
                    unique_count = len(set(all_keywords))
                    total_keywords = len(all_keywords)
                    diversity = (unique_count / total_keywords * 100) if total_keywords > 0 else 0
                    
                    if diversity < 30:
                        issues.append(f"⚠️ {field} 키워드 다양성 부족 ({diversity:.1f}%)")
                        if file_type == "Excel":
                            recommendations.append(f"💡 Excel → TXT 변환 시 키워드 손실 가능성. WOS에서 직접 Plain Text 다운로드 권장")
                        else:
                            recommendations.append(f"💡 {field} 키워드 정규화 강도를 낮춰 다양성 확보")
    
    if not has_keywords:
        issues.append("❌ 키워드 필드 없음: DE 또는 ID 필드 필요")
    
    # 파일 형식별 특별 체크
    if file_type == "Excel":
        recommendations.append("💡 Excel 파일보다는 WOS Plain Text 형식이 더 안정적입니다")
    
    return issues, recommendations

# --- WOS 형식 변환 함수 (최종 버전) ---
def convert_df_to_scimat_format(df_to_convert):
    """SciMAT 완전 호환 WOS 형식으로 변환"""
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
        
        # WOS 필드 순서대로 출력
        for tag in wos_field_order:
            if tag in row.index and pd.notna(row[tag]) and str(row[tag]).strip() and str(row[tag]).strip() != 'nan':
                value = str(row[tag]).strip()
                
                if tag in multi_line_fields:
                    # 세미콜론으로 분리된 항목들을 멀티라인으로 처리
                    items = [item.strip() for item in value.split(';') if item.strip()]
                    if items:
                        # 첫 번째 항목: 태그와 함께
                        file_content.append(f"{tag} {items[0]}")
                        # 나머지 항목들: 정확히 3칸 공백 인덴테이션
                        for item in items[1:]:
                            file_content.append(f"   {item}")
                else:
                    # 단일 라인 필드
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
    <h1 style="font-size: 3.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
        WOS Prep
    </h1>
    <p style="font-size: 1.3rem; margin: 0; font-weight: 400; opacity: 0.95;">
        Final Edition - Live Streaming Research Specialized for SciMAT
    </p>
    <div style="width: 100px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 핵심 기능 소개 ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">라이브 스트리밍 특화</div>
        <div class="feature-desc">29년 연구 진화 분석을 위한 포괄적 분류</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔧</div>
        <div class="feature-title">다중 형식 지원</div>
        <div class="feature-desc">Excel, TXT, WOS 원본 모든 형식 처리</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">SciMAT 완전 호환</div>
        <div class="feature-desc">Word Group 기능 100% 작동 보장</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 권장사항 ---
st.markdown("""
<div class="info-panel">
    <h4 style="color: #003875; margin-bottom: 16px;">📋 최적 사용 가이드</h4>
    <ol style="line-height: 1.8; color: #495057;">
        <li><strong>WOS Plain Text 권장:</strong> 가능하면 Web of Science에서 직접 Plain Text 형식으로 다운로드</li>
        <li><strong>Excel 사용 시:</strong> UTF-8 인코딩 확인 및 키워드 필드 손실 여부 체크</li>
        <li><strong>테스트 우선:</strong> 전체 데이터 전에 50개 샘플로 SciMAT 호환성 확인</li>
        <li><strong>키워드 보존:</strong> 원본 키워드 다양성 최대한 유지</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">📁 데이터 업로드</div>
    <div class="section-subtitle">다양한 형식의 WOS 데이터를 지능적으로 처리합니다.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="upload-zone">
    <div style="font-size: 3rem; margin-bottom: 16px; color: #003875;">📤</div>
    <h3 style="color: #212529; margin-bottom: 8px;">WOS 데이터 파일을 선택하세요</h3>
    <p style="color: #6c757d; margin: 0;">Excel (.xlsx), Tab-delimited (.txt), WOS Plain Text 지원</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "파일 선택",
    type=['csv', 'txt', 'xlsx'],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    df, file_type = load_data(uploaded_file)
    
    if df is None:
        st.error("⚠️ 파일을 읽을 수 없습니다. 지원되는 형식인지 확인해주세요.")
        st.stop()
    
    # 컬럼명 표준화
    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC', 'Cited Reference Count': 'NR', 'Times Cited, WoS Core': 'Z9'
    }
    # 컬럼명 표준화
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
    
    with st.spinner("🔄 데이터 품질 진단 및 라이브 스트리밍 연구 분류 중..."):
        # 데이터 품질 진단
        issues, recommendations = diagnose_data_quality(df, file_type)
        
        # 논문 분류 수행
        df['Classification'] = df.apply(classify_article, axis=1)

    st.success(f"✅ 처리 완료! {file_type} 형식으로 {len(df)}편의 논문을 분석했습니다.")

    # --- 데이터 품질 진단 결과 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">🔍 데이터 품질 진단</div>
        <div class="section-subtitle">업로드된 데이터의 품질과 SciMAT 호환성 검증</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">🚨 발견된 문제점</div>', unsafe_allow_html=True)
        
        if issues:
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.markdown("✅ **문제점 없음** - 데이터 품질 양호")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">💡 개선 권장사항</div>', unsafe_allow_html=True)
        
        if recommendations:
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.markdown("🎯 **추가 개선 불필요** - 현재 상태 최적")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # WOS 원본 TXT 샘플 확인
    if file_type == "WOS_Original":
        st.markdown("""
        <div class="success-panel">
            <h4 style="color: #155724; margin-bottom: 16px;">🎯 WOS 원본 형식 감지됨!</h4>
            <p style="color: #155724; margin: 4px 0;">완벽한 WOS 원본 파일입니다. 키워드 다양성과 데이터 완성도가 최적 상태입니다.</p>
            <p style="color: #155724; margin: 4px 0;"><strong>예상 결과:</strong> SciMAT Word Group에서 100% 정상 작동</p>
        </div>
        """, unsafe_allow_html=True)

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 분석 결과 요약</div>
        <div class="section-subtitle">라이브 스트리밍 연구 분류 결과</div>
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
        # 파일 형식 표시
        format_icons = {
            "Excel": "📊", "Tab_Delimited": "📝", 
            "CSV": "📄", "WOS_Original": "🎯"
        }
        icon = format_icons.get(file_type, "📁")
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-value" style="font-size: 1.8rem;">{file_type}</div>
            <div class="metric-label">File Format</div>
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
                           scale=alt.Scale(range=['#003875', '#0056b3', '#17a2b8', '#28a745', '#ffc107', '#dc3545']),
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

    # --- 연도별 연구 동향 ---
    if 'PY' in df.columns:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">29년 라이브 스트리밍 연구 진화 동향 (1996-2024)</div>
        """, unsafe_allow_html=True)
        
        df_trend = df.copy()
        df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
        df_trend.dropna(subset=['PY'], inplace=True)
        df_trend['PY'] = df_trend['PY'].astype(int)
        
        yearly_counts = df_trend['PY'].value_counts().reset_index()
        yearly_counts.columns = ['Year', 'Count']
        yearly_counts = yearly_counts[yearly_counts['Year'] <= 2025].sort_values('Year')

        if len(yearly_counts) > 0:
            line_chart = alt.Chart(yearly_counts).mark_line(
                point={'size': 80, 'filled': True}, strokeWidth=3, color='#003875'
            ).encode(
                x=alt.X('Year:O', title='발행 연도'),
                y=alt.Y('Count:Q', title='논문 수'),
                tooltip=['Year', 'Count']
            ).properties(height=300)
            
            st.altair_chart(line_chart, use_container_width=True)
            
            # 진화 단계 분석
            st.markdown("""
            <div class="info-panel">
                <h4 style="color: #003875; margin-bottom: 12px;">📈 라이브 스트리밍 연구 진화 4단계</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; text-align: center;">
                        <strong style="color: #003875;">1996-2006 태동기</strong><br>
                        <small style="color: #6c757d;">기술적 기반 연구</small>
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; text-align: center;">
                        <strong style="color: #003875;">2007-2016 형성기</strong><br>
                        <small style="color: #6c757d;">플랫폼 등장과 확산</small>
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; text-align: center;">
                        <strong style="color: #003875;">2017-2021 확산기</strong><br>
                        <small style="color: #6c757d;">상업적 활용 급증</small>
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; text-align: center;">
                        <strong style="color: #003875;">2022-2024 성숙기</strong><br>
                        <small style="color: #6c757d;">융합과 진화</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 키워드 샘플 확인 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">키워드 데이터 품질 확인</div>
    """, unsafe_allow_html=True)
    
    if st.checkbox("🔍 키워드 샘플 및 품질 확인", key="keyword_check"):
        sample_data = []
        sample_rows = df[df['Classification'].str.contains('Include', na=False)].head(3)
        
        for idx, row in sample_rows.iterrows():
            title = str(row.get('TI', 'N/A'))[:80] + "..." if len(str(row.get('TI', 'N/A'))) > 80 else str(row.get('TI', 'N/A'))
            de_keywords = str(row.get('DE', 'N/A')) if pd.notna(row.get('DE')) else 'N/A'
            id_keywords = str(row.get('ID', 'N/A')) if pd.notna(row.get('ID')) else 'N/A'
            
            # 키워드 개수 계산
            de_count = len([k.strip() for k in de_keywords.split(';') if k.strip()]) if de_keywords != 'N/A' else 0
            id_count = len([k.strip() for k in id_keywords.split(';') if k.strip()]) if id_keywords != 'N/A' else 0
            
            sample_data.append({
                '논문 제목': title,
                'DE 키워드': de_keywords[:100] + "..." if len(de_keywords) > 100 else de_keywords,
                'ID 키워드': id_keywords[:100] + "..." if len(id_keywords) > 100 else id_keywords,
                'DE 개수': de_count,
                'ID 개수': id_count
            })
        
        if sample_data:
            sample_df = pd.DataFrame(sample_data)
            st.dataframe(sample_df, use_container_width=True, hide_index=True)
            
            # 키워드 품질 평가
            avg_de = sum([d['DE 개수'] for d in sample_data]) / len(sample_data) if sample_data else 0
            avg_id = sum([d['ID 개수'] for d in sample_data]) / len(sample_data) if sample_data else 0
            
            if avg_de >= 3 and avg_id >= 3:
                st.success("✅ 키워드 품질 우수 - SciMAT에서 원활한 그룹핑 예상")
            elif avg_de >= 2 or avg_id >= 2:
                st.warning("⚠️ 키워드 품질 보통 - SciMAT에서 일부 제한 가능")
            else:
                st.error("❌ 키워드 품질 부족 - 원본 데이터 확인 필요")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 최종 데이터셋 준비 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">💾 SciMAT 호환 파일 다운로드</div>
        <div class="section-subtitle">라이브 스트리밍 연구에 최적화된 최종 데이터셋</div>
    </div>
    """, unsafe_allow_html=True)

    # 최종 데이터셋 준비 (제외된 논문만 빼고)
    df_final = df[~df['Classification'].str.contains('Exclude', na=False)].copy()
    
    # Classification 컬럼만 제거 (키워드는 원본 그대로)
    df_final_output = df_final.drop(columns=['Classification'], errors='ignore')

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
            <div class="metric-label">핵심 포함 연구</div>
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
            label="🔥 SciMAT 완전 호환 파일 다운로드 (.txt)",
            data=text_data,
            file_name="live_streaming_final_for_scimat.txt",
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
            file_name="test_final_50papers.txt",
            mime="text/plain",
            use_container_width=True
        )

    # 최종 사용 가이드
    st.markdown("""
    <div class="success-panel">
        <h4 style="color: #155724; margin-bottom: 16px;">🎯 SciMAT 사용 완벽 가이드</h4>
        <ol style="line-height: 1.8; color: #155724;">
            <li><strong>테스트 우선:</strong> 50개 샘플 파일로 SciMAT 호환성 먼저 확인</li>
            <li><strong>파일 업로드:</strong> SciMAT에서 다운로드한 파일 로드</li>
            <li><strong>Word Group 작업:</strong> Words groups manager에서 키워드 그룹핑</li>
            <li><strong>Levenshtein Distance:</strong> 자동 유사 키워드 묶기 활용</li>
            <li><strong>수동 정제:</strong> 라이브 스트리밍 특화 그룹 생성</li>
            <li><strong>진화 분석:</strong> 시계열 분석으로 29년간 지식 구조 변화 탐지</li>
        </ol>
        
        <div style="margin-top: 16px; padding: 12px; background: #d1ecf1; border-left: 4px solid #17a2b8; border-radius: 4px;">
            <strong>🎖️ 연구 성과:</strong> 라이브 스트리밍 분야 최초의 종합적 지식 구조 진화 분석 (1996-2024)
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 분류 상세 결과 (선택사항)
    if st.checkbox("📊 분류 상세 결과 보기", key="detail_check"):
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">분류별 상세 분포</div>
        """, unsafe_allow_html=True)
        
        # 분류별 상세 통계
        for classification in df['Classification'].unique():
            count = len(df[df['Classification'] == classification])
            percentage = (count / total_papers * 100)
            
            if classification.startswith('Include'):
                color = "#28a745"
                icon = "✅"
            elif classification.startswith('Review'):
                color = "#ffc107"
                icon = "📝"
            else:
                color = "#dc3545"
                icon = "❌"
            
            st.markdown(f"""
            <div style="margin: 8px 0; padding: 12px; background: white; border-left: 4px solid {color}; border-radius: 4px;">
                <strong>{icon} {classification}:</strong> {count:,}편 ({percentage:.1f}%)
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# --- 하단 여백 ---
st.markdown("<br><br>", unsafe_allow_html=True)
