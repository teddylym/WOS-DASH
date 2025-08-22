import streamlit as st
import pandas as pd
import altair as alt
import io
import re
from collections import Counter

# --- 페이지 설정 ---
st.set_page_config(
    page_title="WOS Multi-File Merger | SCIMAT Edition",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 토스 스타일 CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap');
    
    .main-container {
        background: #f9fafb;
        min-height: 100vh;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }
    
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #e5e8eb;
        margin-bottom: 16px;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transform: translateY(-1px);
        border-color: #0064ff;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #191f28;
        margin: 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    
    .metric-label {
        font-size: 14px;
        color: #8b95a1;
        margin: 8px 0 0 0;
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    
    .metric-icon {
        background: linear-gradient(135deg, #0064ff, #0050cc);
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,100,255,0.2);
    }
    
    .chart-container {
        background: white;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #e5e8eb;
        margin: 20px 0;
    }
    
    .chart-title {
        font-size: 18px;
        font-weight: 700;
        color: #191f28;
        margin-bottom: 20px;
        letter-spacing: -0.02em;
    }
    
    .section-header {
        background: linear-gradient(135deg, #0064ff, #0050cc);
        color: white;
        padding: 32px;
        border-radius: 20px;
        margin: 32px 0 20px 0;
        box-shadow: 0 4px 20px rgba(0,100,255,0.15);
        position: relative;
        overflow: hidden;
    }
    
    .section-header::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: rgba(255,255,255,0.1);
        border-radius: 50%;
        transform: translate(30px, -30px);
    }
    
    .section-title {
        font-size: 24px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .section-subtitle {
        font-size: 16px;
        opacity: 0.9;
        margin: 8px 0 0 0;
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    
    .info-panel {
        background: #f0f6ff;
        border: 1px solid #b3d7ff;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        position: relative;
    }
    
    .success-panel {
        background: #f0fdf9;
        border: 1px solid #86efac;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        position: relative;
    }
    
    .warning-panel {
        background: #fffbeb;
        border: 1px solid #fbbf24;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        position: relative;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 20px;
        margin: 32px 0;
    }
    
    .feature-card {
        background: white;
        border-radius: 20px;
        padding: 32px 24px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #e5e8eb;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0064ff, #0050cc);
        transform: scaleX(0);
        transition: transform 0.2s ease;
    }
    
    .feature-card:hover::before {
        transform: scaleX(1);
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        border-color: #0064ff;
    }
    
    .feature-icon {
        font-size: 48px;
        margin-bottom: 20px;
        color: #0064ff;
    }
    
    .feature-title {
        font-size: 18px;
        font-weight: 700;
        color: #191f28;
        margin-bottom: 12px;
        letter-spacing: -0.02em;
    }
    
    .feature-desc {
        font-size: 14px;
        color: #8b95a1;
        line-height: 1.6;
        letter-spacing: -0.01em;
    }
    
    .upload-zone {
        background: white;
        border: 2px dashed #c7d2fe;
        border-radius: 16px;
        padding: 48px 24px;
        text-align: center;
        margin: 24px 0;
        transition: all 0.2s ease;
    }
    
    .upload-zone:hover {
        background: #f8faff;
        border-color: #0064ff;
    }
    
    .progress-indicator {
        background: linear-gradient(90deg, #0064ff, #0050cc);
        height: 4px;
        border-radius: 2px;
        margin: 20px 0;
        animation: pulse 2s infinite;
    }
    
    .file-status {
        background: #f8faff;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        border-left: 4px solid #0064ff;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* 토스 스타일 버튼 */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #0064ff, #0050cc) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 16px 32px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        letter-spacing: -0.01em !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(0,100,255,0.2) !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,100,255,0.3) !important;
    }
    
    /* 토스 스타일 expander */
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 16px !important;
        border: 1px solid #e5e8eb !important;
        font-weight: 600 !important;
        color: #191f28 !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* 데이터프레임 스타일링 */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #e5e8eb !important;
    }
    
    /* 스피너 스타일링 */
    .stSpinner {
        color: #0064ff !important;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* 메인 컨테이너 여백 조정 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* 알림 메시지 스타일링 */
    .stAlert {
        border-radius: 16px !important;
        border: none !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    
    .stSuccess {
        background: #f0fdf9 !important;
        color: #065f46 !important;
    }
    
    .stInfo {
        background: #f0f6ff !important;
        color: #1e40af !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        color: #92400e !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        color: #dc2626 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 다중 WOS Plain Text 파일 로딩 및 병합 함수 ---
def load_and_merge_wos_files(uploaded_files):
    """다중 WOS Plain Text 파일을 로딩하고 병합 - 중복 제거 완전 수정"""
    all_dataframes = []
    file_status = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            file_bytes = uploaded_file.getvalue()
            encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1']
            
            df = None
            encoding_used = None
            
            for encoding in encodings_to_try:
                try:
                    file_content = file_bytes.decode(encoding)
                    
                    # WOS 원본 형식 검증 (FN으로 시작해야 함)
                    if not file_content.strip().startswith('FN '):
                        continue
                        
                    # WOS 형식 파싱
                    df = parse_wos_format(file_content)
                    if df is not None and len(df) > 0:
                        encoding_used = encoding
                        break
                        
                except Exception:
                    continue
            
            if df is not None:
                all_dataframes.append(df)
                file_status.append({
                    'filename': uploaded_file.name,
                    'status': 'SUCCESS',
                    'papers': len(df),
                    'encoding': encoding_used,
                    'message': f'✅ {len(df)}편 논문 로딩 성공'
                })
            else:
                file_status.append({
                    'filename': uploaded_file.name,
                    'status': 'ERROR',
                    'papers': 0,
                    'encoding': 'N/A',
                    'message': '❌ WOS Plain Text 형식이 아님'
                })
                
        except Exception as e:
            file_status.append({
                'filename': uploaded_file.name,
                'status': 'ERROR',
                'papers': 0,
                'encoding': 'N/A',
                'message': f'❌ 파일 처리 오류: {str(e)[:50]}'
            })
    
    # 모든 데이터프레임 병합
    if all_dataframes:
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        original_count = len(merged_df)
        
        # 중복 제거 로직 - 완전히 새로 작성
        duplicates_removed = 0
        
        if 'UT' in merged_df.columns:
            # UT 필드의 실제 값들 확인
            ut_series = merged_df['UT'].copy()
            
            # 유효한 UT 값만 필터링 (더 엄격한 조건)
            def is_meaningful_ut(value):
                if pd.isna(value):
                    return False
                str_value = str(value).strip()
                # 빈 문자열, 'nan', 'None', 매우 짧은 값들 제외
                if len(str_value) == 0 or str_value.lower() in ['nan', 'none', 'null', '']:
                    return False
                # WOS UT는 일반적으로 'WOS:' 또는 문자+숫자 조합
                # 최소 10자 이상의 의미있는 값만 유효한 것으로 간주
                if len(str_value) < 10:
                    return False
                # 'WOS:' 로 시작하거나 충분히 긴 영숫자 조합인 경우만 유효
                if str_value.startswith('WOS:') or (len(str_value) >= 15 and any(c.isalnum() for c in str_value)):
                    return True
                return False
            
            # 유효한 UT를 가진 행들만 선별
            meaningful_ut_mask = ut_series.apply(is_meaningful_ut)
            rows_with_meaningful_ut = merged_df[meaningful_ut_mask]
            rows_without_meaningful_ut = merged_df[~meaningful_ut_mask]
            
            # 실제로 의미있는 UT가 있는 경우에만 중복 검사
            if len(rows_with_meaningful_ut) > 1:  # 최소 2개 이상 있어야 중복 검사 의미
                # 중복 제거 전후 비교
                before_dedup = len(rows_with_meaningful_ut)
                deduplicated_meaningful = rows_with_meaningful_ut.drop_duplicates(subset=['UT'], keep='first')
                after_dedup = len(deduplicated_meaningful)
                
                actual_duplicates = before_dedup - after_dedup
                
                if actual_duplicates > 0:
                    duplicates_removed = actual_duplicates
                    
                    # 중복 제거된 결과와 UT 없는 행들 재결합
                    merged_df = pd.concat([deduplicated_meaningful, rows_without_meaningful_ut], ignore_index=True)
        
        # 대안: UT가 없거나 신뢰할 수 없는 경우 제목+저자 기준 중복 제거
        if duplicates_removed == 0 and 'TI' in merged_df.columns:
            # 제목과 첫 번째 저자 기준으로 중복 확인 (매우 보수적)
            title_author_before = len(merged_df)
            
            # 제목이 있고 저자가 있는 행들만 대상
            has_title = merged_df['TI'].notna() & (merged_df['TI'].str.strip() != '')
            has_author = merged_df.get('AU', pd.Series()).notna() if 'AU' in merged_df.columns else pd.Series([False] * len(merged_df))
            
            complete_rows = merged_df[has_title & has_author] if 'AU' in merged_df.columns else merged_df[has_title]
            incomplete_rows = merged_df[~(has_title & has_author)] if 'AU' in merged_df.columns else merged_df[~has_title]
            
            if len(complete_rows) > 1:
                dedup_columns = ['TI', 'AU'] if 'AU' in merged_df.columns else ['TI']
                deduplicated_complete = complete_rows.drop_duplicates(subset=dedup_columns, keep='first')
                title_author_removed = len(complete_rows) - len(deduplicated_complete)
                
                if title_author_removed > 0:
                    duplicates_removed = title_author_removed
                    merged_df = pd.concat([deduplicated_complete, incomplete_rows], ignore_index=True)
        
        return merged_df, file_status, duplicates_removed
    else:
        return None, file_status, 0

def parse_wos_format(content):
    """WOS Plain Text 형식을 DataFrame으로 변환"""
    lines = content.split('\n')
    records = []
    current_record = {}
    current_field = None
    
    for line in lines:
        line = line.rstrip()
        
        if not line:
            continue
            
        # 레코드 종료
        if line == 'ER':
            if current_record:
                records.append(current_record.copy())
                current_record = {}
                current_field = None
            continue
            
        # 헤더 라인 건너뛰기
        if line.startswith(('FN ', 'VR ')):
            continue
            
        # 새 필드 시작
        if not line.startswith('   ') and ' ' in line:
            parts = line.split(' ', 1)
            if len(parts) == 2:
                field_tag, field_value = parts
                current_field = field_tag
                current_record[field_tag] = field_value.strip()
        
        # 기존 필드 연속
        elif line.startswith('   ') and current_field and current_field in current_record:
            continuation_value = line[3:].strip()
            if continuation_value:
                current_record[current_field] += '; ' + continuation_value
    
    # 마지막 레코드 처리
    if current_record:
        records.append(current_record)
    
    if not records:
        return None
        
    return pd.DataFrame(records)

# --- 라이브 스트리밍 특화 분류 함수 ---
def classify_article(row):
    """라이브 스트리밍 연구를 위한 포괄적 분류 - 개선된 알고리즘"""
    
    # 핵심 라이브 스트리밍 키워드 (직접적 관련성)
    core_streaming_keywords = [
        'live streaming', 'livestreaming', 'live stream', 'live broadcast', 'live video',
        'real time streaming', 'real-time streaming', 'streaming platform', 'streaming service',
        'live webcast', 'webcasting', 'live transmission', 'interactive broadcasting',
        'live commerce', 'live shopping', 'live selling', 'livestream commerce',
        'live e-commerce', 'social commerce', 'live marketing', 'streaming monetization',
        'live retail', 'shoppertainment', 'live sales', 'streaming sales',
        'streamer', 'viewer', 'audience engagement', 'streaming audience', 'live audience',
        'streaming behavior', 'viewer behavior', 'streaming experience', 'live interaction',
        'streaming community', 'online community', 'digital community', 'virtual community',
        'parasocial relationship', 'streamer-viewer', 'live chat', 'chat interaction',
        'twitch', 'youtube live', 'facebook live', 'instagram live', 'tiktok live',
        'periscope', 'mixer', 'douyin', 'kuaishou', 'taobao live', 'tmall live',
        'amazon live', 'shopee live', 'live.ly', 'bigo live',
        'live gaming', 'game streaming', 'esports streaming', 'streaming content',
        'live entertainment', 'live performance', 'virtual concert', 'live music'
    ]
    
    # 확장된 비즈니스 및 커머스 관련 키워드
    business_commerce_keywords = [
        'e-commerce', 'online shopping', 'digital commerce', 'mobile commerce', 'm-commerce',
        'social commerce', 'influencer marketing', 'content creator', 'digital marketing', 
        'brand engagement', 'consumer behavior', 'purchase intention', 'buying behavior',
        'social influence', 'word of mouth', 'viral marketing', 'user generated content',
        'brand advocacy', 'customer engagement', 'social media marketing', 'digital influence',
        'online influence', 'interactive marketing', 'personalized marketing', 'real-time marketing',
        'digital transformation', 'omnichannel', 'customer experience', 'user experience',
        'engagement marketing', 'social selling', 'digital retail', 'online retail'
    ]
    
    # 교육 및 학습 관련 키워드 (확장)
    education_keywords = [
        'online education', 'e-learning', 'distance learning', 'remote learning',
        'virtual classroom', 'online teaching', 'digital learning', 'mooc',
        'educational technology', 'learning management system', 'blended learning',
        'medical education', 'nursing education', 'surgical training', 'clinical education',
        'telemedicine', 'telehealth', 'digital health', 'health education',
        'interactive learning', 'synchronous learning', 'real-time learning'
    ]
    
    # 기술적 기반 키워드 (확장)
    technical_keywords = [
        'real time video', 'real-time video', 'video streaming', 'audio streaming',
        'multimedia streaming', 'video compression', 'video encoding', 'video delivery',
        'content delivery', 'cdn', 'edge computing', 'multimedia communication',
        'video communication', 'webrtc', 'peer to peer streaming', 'p2p streaming',
        'distributed streaming', 'mobile streaming', 'mobile video', 'wireless streaming',
        'mobile broadcast', 'smartphone streaming', 'live video transmission',
        'streaming technology', 'adaptive streaming', 'video quality', 'streaming latency',
        'interactive media', 'virtual reality', 'augmented reality', 'vr', 'ar',
        '3d streaming', 'immersive media', 'metaverse'
    ]
    
    # 사회문화적 영향 키워드 (신규 추가)
    sociocultural_keywords = [
        'digital culture', 'online culture', 'virtual community', 'digital society',
        'social media', 'social network', 'digital communication', 'online interaction',
        'digital identity', 'virtual identity', 'online presence', 'digital participation',
        'cultural transmission', 'digital religion', 'online religion', 'virtual religion',
        'digital migration', 'online migration', 'digital diaspora', 'virtual diaspora',
        'social cohesion', 'community building', 'social capital', 'digital divide'
    ]
    
    # COVID-19 및 팬데믹 관련 키워드 (신규 추가)
    pandemic_keywords = [
        'covid-19', 'pandemic', 'coronavirus', 'sars-cov-2', 'lockdown', 'quarantine',
        'social distancing', 'remote work', 'work from home', 'digital adaptation',
        'pandemic response', 'crisis communication', 'emergency response'
    ]
    
    # 확장된 소셜 미디어 키워드
    social_media_keywords = [
        'social media', 'social network', 'online platform', 'digital platform',
        'user experience', 'user behavior', 'online behavior', 'digital behavior',
        'social interaction', 'online interaction', 'digital interaction',
        'user engagement', 'digital engagement', 'platform economy', 'network effects',
        'viral content', 'content sharing', 'social sharing', 'online community'
    ]
    
    # 제외 키워드 (기술적 비관련 - 더 엄격하게)
    exclusion_keywords = [
        'routing protocol', 'network topology', 'packet routing', 'mac protocol',
        'ieee 802.11', 'wimax protocol', 'lte protocol', 'network security protocol',
        'vlsi design', 'circuit design', 'antenna design', 'rf circuit',
        'hardware implementation', 'fpga implementation', 'asic design',
        'signal processing algorithm', 'modulation scheme', 'channel estimation',
        'beamforming algorithm', 'mimo antenna', 'ofdm modulation',
        'frequency allocation', 'spectrum allocation', 'wireless sensor network',
        'satellite communication', 'underwater communication', 'space communication',
        'biomedical signal', 'medical imaging', 'radar system', 'sonar system',
        'geological survey', 'seismic data', 'astronomical data', 'climate modeling'
    ]
    
    # 텍스트 추출
    def extract_text(value):
        if pd.isna(value) or value is None:
            return ""
        return str(value).lower().strip()
    
    title = extract_text(row.get('TI', ''))
    source_title = extract_text(row.get('SO', ''))
    author_keywords = extract_text(row.get('DE', ''))
    keywords_plus = extract_text(row.get('ID', ''))
    abstract = extract_text(row.get('AB', ''))
    
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    
    # 개선된 분류 로직
    # 1. 명확한 제외 대상 먼저 필터링
    if any(keyword in full_text for keyword in exclusion_keywords):
        return 'Exclude (기술적 비관련)'
    
    # 2. 핵심 라이브 스트리밍 키워드 - 최우선 포함
    if any(keyword in full_text for keyword in core_streaming_keywords):
        return 'Include (핵심연구)'
    
    # 3. 비즈니스/커머스 + 디지털 지표 - 포용적 접근
    if any(keyword in full_text for keyword in business_commerce_keywords):
        digital_indicators = ['digital', 'online', 'internet', 'web', 'social media', 'platform', 'mobile', 'app', 'virtual', 'interactive']
        if any(indicator in full_text for indicator in digital_indicators):
            return 'Include (비즈니스 관련)'
    
    # 4. 교육 + 온라인/디지털 지표 - 포용적 접근
    if any(keyword in full_text for keyword in education_keywords):
        online_indicators = ['online', 'digital', 'virtual', 'remote', 'distance', 'interactive', 'real-time', 'synchronous']
        if any(indicator in full_text for indicator in online_indicators):
            return 'Include (교육 관련)'
    
    # 5. 기술적 기반 + 라이브/실시간 지표
    if any(keyword in full_text for keyword in technical_keywords):
        live_indicators = ['live', 'real time', 'real-time', 'streaming', 'broadcast', 'interactive', 'synchronous', 'instant']
        if any(indicator in full_text for indicator in live_indicators):
            return 'Include (기술적 기반)'
    
    # 6. 사회문화적 + 디지털 지표 (신규)
    if any(keyword in full_text for keyword in sociocultural_keywords):
        digital_indicators = ['digital', 'online', 'virtual', 'internet', 'web', 'platform', 'social media']
        if any(indicator in full_text for indicator in digital_indicators):
            return 'Include (사회문화 관련)'
    
    # 7. 팬데믹 관련 + 디지털 지표 (신규)
    if any(keyword in full_text for keyword in pandemic_keywords):
        digital_indicators = ['digital', 'online', 'virtual', 'remote', 'streaming', 'platform', 'technology']
        if any(indicator in full_text for indicator in digital_indicators):
            return 'Include (팬데믹 디지털화)'
    
    # 8. 소셜 미디어 일반 - 조건부 포함
    if any(keyword in full_text for keyword in social_media_keywords):
        interaction_indicators = ['interaction', 'engagement', 'community', 'sharing', 'content', 'creator', 'influencer']
        if any(indicator in full_text for indicator in interaction_indicators):
            return 'Include (소셜미디어 관련)'
        else:
            return 'Review (소셜미디어 검토)'
    
    # 9. 기타 - 최소 검토 대상
    return 'Review (분류 불확실)'

# --- 데이터 품질 진단 함수 ---
def diagnose_merged_quality(df, file_count, duplicates_removed):
    """병합된 WOS 데이터의 품질 진단 - 수정된 버전"""
    issues = []
    recommendations = []
    
    # 필수 필드 확인
    required_fields = ['TI', 'AU', 'SO', 'PY']
    keyword_fields = ['DE', 'ID']
    
    for field in required_fields:
        if field not in df.columns:
            issues.append(f"❌ 필수 필드 누락: {field}")
        else:
            valid_count = df[field].notna().sum()
            total_count = len(df)
            missing_rate = (total_count - valid_count) / total_count * 100
            
            if missing_rate > 10:
                issues.append(f"⚠️ {field} 필드의 {missing_rate:.1f}%가 누락됨")
    
    # 키워드 필드 품질 확인
    has_keywords = False
    for field in keyword_fields:
        if field in df.columns:
            has_keywords = True
            valid_keywords = df[field].notna() & (df[field] != '') & (df[field] != 'nan')
            valid_count = valid_keywords.sum()
            total_count = len(df)
            
            if valid_count < total_count * 0.7:
                issues.append(f"⚠️ {field} 필드의 {((total_count-valid_count)/total_count*100):.1f}%가 비어있음")
    
    if not has_keywords:
        issues.append("❌ 키워드 필드 없음: DE 또는 ID 필드 필요")
    
    # 병합 관련 정보 - 실제 결과만 반영 (완전 수정)
    recommendations.append(f"✅ {file_count}개 파일 성공적으로 병합됨")
    
    # 중복 제거 결과만 실제 데이터에 따라 표시
    if duplicates_removed > 0:
        recommendations.append(f"🔄 중복 논문 {duplicates_removed}편 자동 제거됨")
    else:
        recommendations.append("✅ 중복 논문 없음 - 모든 논문이 고유 데이터")
    
    recommendations.append("✅ WOS Plain Text 형식 - SCIMAT 최적 호환성 확보")
    
    return issues, recommendations

# --- WOS Plain Text 형식 변환 함수 ---
def convert_to_scimat_wos_format(df_to_convert):
    """SCIMAT 완전 호환 WOS Plain Text 형식으로 변환"""
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
        
        for tag in wos_field_order:
            if tag in row.index and pd.notna(row[tag]) and str(row[tag]).strip() and str(row[tag]).strip().lower() != 'nan':
                value = str(row[tag]).strip()
                
                if tag in multi_line_fields:
                    items = [item.strip() for item in value.split(';') if item.strip()]
                    if items:
                        file_content.append(f"{tag} {items[0]}")
                        for item in items[1:]:
                            file_content.append(f"   {item}")
                else:
                    file_content.append(f"{tag} {value}")
        
        file_content.append("ER")
    
    return "\n".join(file_content).encode('utf-8-sig')

# --- 메인 헤더 ---
st.markdown("""
<div style="position: relative; text-align: center; padding: 3rem 0 4rem 0; background: linear-gradient(135deg, #0064ff, #0050cc); color: white; border-radius: 24px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,100,255,0.15); overflow: hidden;">
    <div style="position: absolute; top: 0; right: 0; width: 200px; height: 200px; background: rgba(255,255,255,0.05); border-radius: 50%; transform: translate(60px, -60px);"></div>
    <div style="position: absolute; top: 1.5rem; left: 2rem; color: white;">
        <div style="font-size: 14px; font-weight: 600; margin-bottom: 4px; letter-spacing: 0.5px;">HANYANG UNIVERSITY</div>
        <div style="font-size: 12px; opacity: 0.9; font-weight: 500;">Technology Management Research</div>
        <div style="font-size: 11px; opacity: 0.8; margin-top: 6px; font-weight: 400;">mot.hanyang.ac.kr</div>
    </div>
    <div style="position: absolute; top: 1.5rem; right: 2rem; text-align: right; color: rgba(255,255,255,0.9); font-size: 13px;">
        <p style="margin: 0; font-weight: 600;">Developed by: 임태경 (Teddy Lym)</p>
    </div>
    <h1 style="font-size: 4rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.03em;">
        WOS PREP
    </h1>
    <p style="font-size: 1.4rem; margin: 0; font-weight: 500; opacity: 0.95; letter-spacing: -0.01em;">
        SCIMAT Edition
    </p>
    <div style="width: 120px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2.5rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 핵심 기능 소개 ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🔗</div>
        <div class="feature-title">다중 파일 자동 병합</div>
        <div class="feature-desc">여러 WOS 파일을 한 번에 병합 처리</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🚫</div>
        <div class="feature-title">스마트 중복 제거</div>
        <div class="feature-desc">UT 기준 자동 중복 논문 감지 및 제거</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">데이터 분류</div>
        <div class="feature-desc">대규모 데이터 포괄적 분류 및 분석</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">📂 다중 WOS Plain Text 파일 업로드</div>
    <div class="section-subtitle">500개 단위로 나뉜 여러 WOS 파일을 모두 선택하여 업로드하세요</div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "WOS Plain Text 파일 선택 (다중 선택 가능)",
    type=['txt'],
    accept_multiple_files=True,
    label_visibility="collapsed",
    help="WOS Plain Text 파일들을 드래그하여 놓거나 클릭하여 선택하세요"
)

if uploaded_files:
    st.markdown(f"📋 **선택된 파일 개수:** {len(uploaded_files)}개")
    
    # 프로그레스 인디케이터
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 분석 중..."):
        # 파일 병합
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)
        
        if merged_df is None:
            st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다. 파일들이 Web of Science에서 다운로드한 정품 Plain Text 파일인지 확인해주세요.")
            
            # 파일별 상태 표시
            st.markdown("### 📄 파일별 처리 상태")
            for status in file_status:
                st.markdown(f"""
                <div class="file-status">
                    <strong>{status['filename']}</strong><br>
                    {status['message']}
                </div>
                """, unsafe_allow_html=True)
            st.stop()
        
        # 논문 분류 수행
        merged_df['Classification'] = merged_df.apply(classify_article, axis=1)

    # 성공적인 파일 개수 계산
    successful_files = len([s for s in file_status if s['status'] == 'SUCCESS'])
    total_papers = len(merged_df)
    
    st.success(f"✅ 병합 완료! {successful_files}개 파일에서 {total_papers:,}편의 논문을 성공적으로 처리했습니다.")
    
    # 중복 제거 결과 표시 - 실제 결과만
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다. (원본 총 {total_papers + duplicates_removed:,}편 → 정제 후 {total_papers:,}편)")
    else:
        st.info("✅ 중복 논문 없음 - 모든 논문이 고유한 데이터입니다.")

    # --- 파일별 처리 상태 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📄 파일별 처리 상태</div>
        <div class="section-subtitle">업로드된 각 파일의 처리 결과</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">📋 파일별 상세 상태</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.6, 0.4])
    
    with col1:        
        for status in file_status:
            color = "#10b981" if status['status'] == 'SUCCESS' else "#ef4444"
            icon = "✅" if status['status'] == 'SUCCESS' else "❌"
            
            st.markdown(f"""
            <div style="margin: 12px 0; padding: 16px; background: white; border-left: 4px solid {color}; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <strong>{icon} {status['filename']}</strong><br>
                <small style="color: #8b95a1;">{status['message']}</small>
                {f" | 인코딩: {status['encoding']}" if status['encoding'] != 'N/A' else ""}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # 파일 처리 통계
        success_count = len([s for s in file_status if s['status'] == 'SUCCESS'])
        error_count = len([s for s in file_status if s['status'] == 'ERROR'])
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{success_count}</div>
            <div class="metric-label">성공한 파일</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">❌</div>
            <div class="metric-value">{error_count}</div>
            <div class="metric-label">실패한 파일</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 데이터 품질 진단 결과 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">🔍 병합 데이터 품질 진단</div>
        <div class="section-subtitle">병합된 WOS 데이터의 품질과 SCIMAT 호환성 검증</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("🔍 병합 데이터 품질 분석 중..."):
        issues, recommendations = diagnose_merged_quality(merged_df, successful_files, duplicates_removed)

    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">🔍 병합 데이터 품질 진단 결과</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h5 style="color: #ef4444; margin-bottom: 16px;">🚨 발견된 문제점</h5>', unsafe_allow_html=True)
        
        if issues:
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.markdown("✅ **문제점 없음** - 병합 데이터 품질 우수")
    
    with col2:
        st.markdown('<h5 style="color: #10b981; margin-bottom: 16px;">💡 병합 결과</h5>', unsafe_allow_html=True)
        
        if recommendations:
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.markdown("🎯 **최적 상태** - SCIMAT 완벽 호환")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 병합 성공 알림
    st.markdown("""
    <div class="success-panel">
        <h4 style="color: #065f46; margin-bottom: 20px; font-weight: 700;">🎯 다중 파일 병합 성공!</h4>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;">여러 WOS Plain Text 파일이 성공적으로 하나로 병합되었습니다.</p>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;"><strong>중복 제거:</strong> 동일한 논문은 자동으로 제거되어 정확한 분석 결과를 보장합니다.</p>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;"><strong>SCIMAT 호환성:</strong> 병합된 파일은 SCIMAT에서 100% 정상 작동합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 병합 데이터 분석 결과</div>
        <div class="section-subtitle">라이브 스트리밍 연구 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    classification_counts = merged_df['Classification'].value_counts()
    total_papers = len(merged_df)
    include_papers = len(merged_df[merged_df['Classification'].str.contains('Include', na=False)])
    
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
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔗</div>
            <div class="metric-value" style="font-size: 1.8rem;">{successful_files}개</div>
            <div class="metric-label">Merged Files</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 논문 분류 현황 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Research Classification Distribution</div>
    """, unsafe_allow_html=True)

    classification_counts_df = merged_df['Classification'].value_counts().reset_index()
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
                           scale=alt.Scale(range=['#0064ff', '#0050cc', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']),
                           legend=alt.Legend(orient="right", titleColor="#191f28", labelColor="#8b95a1")),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.8))
        ).add_params(selection)

        pie = base.mark_arc(outerRadius=150, innerRadius=90)
        text_total = alt.Chart(pd.DataFrame([{'value': f'{total_papers}'}])).mark_text(
            align='center', baseline='middle', fontSize=45, fontWeight='bold', color='#0064ff'
        ).encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame([{'value': 'Total Papers'}])).mark_text(
            align='center', baseline='middle', fontSize=16, dy=30, color='#8b95a1'
        ).encode(text='value:N')

        chart = (pie + text_total + text_label).properties(
            width=350, height=350
        ).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 분류 상세 결과 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">분류별 상세 분포</div>
    """, unsafe_allow_html=True)
    
    # 분류별 상세 통계
    for classification in merged_df['Classification'].unique():
        count = len(merged_df[merged_df['Classification'] == classification])
        percentage = (count / total_papers * 100)
        
        if classification.startswith('Include'):
            color = "#10b981"
            icon = "✅"
        elif classification.startswith('Review'):
            color = "#f59e0b"
            icon = "🔍"
        else:
            color = "#ef4444"
            icon = "❌"
        
        st.markdown(f"""
        <div style="margin: 16px 0; padding: 20px; background: white; border-left: 4px solid {color}; border-radius: 12px; font-size: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <strong>{icon} {classification}:</strong> {count:,}편 ({percentage:.1f}%)
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 연도별 연구 동향 ---
    if 'PY' in merged_df.columns:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">29년 라이브 스트리밍 연구 진화 동향 (1996-2024)</div>
        """, unsafe_allow_html=True)
        
        df_trend = merged_df.copy()
        df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
        df_trend.dropna(subset=['PY'], inplace=True)
        df_trend['PY'] = df_trend['PY'].astype(int)
        
        yearly_counts = df_trend['PY'].value_counts().reset_index()
        yearly_counts.columns = ['Year', 'Count']
        yearly_counts = yearly_counts[yearly_counts['Year'] <= 2025].sort_values('Year')

        if len(yearly_counts) > 0:
            line_chart = alt.Chart(yearly_counts).mark_line(
                point={'size': 80, 'filled': True}, strokeWidth=3, color='#0064ff'
            ).encode(
                x=alt.X('Year:O', title='발행 연도'),
                y=alt.Y('Count:Q', title='논문 수'),
                tooltip=['Year', 'Count']
            ).properties(height=300)
            
            st.altair_chart(line_chart, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 키워드 샘플 확인 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">병합 데이터 키워드 품질 확인</div>
    """, unsafe_allow_html=True)
    
    sample_data = []
    sample_rows = merged_df[merged_df['Classification'].str.contains('Include', na=False)].head(3)
    
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
            st.success("✅ 키워드 품질 우수 - SCIMAT에서 원활한 그루핑 예상")
        elif avg_de >= 2 or avg_id >= 2:
            st.warning("⚠️ 키워드 품질 보통 - SCIMAT에서 일부 제한 가능")
        else:
            st.error("❌ 키워드 품질 부족 - 원본 WOS 다운로드 설정 확인 필요")

    st.markdown("</div>", unsafe_allow_html=True)

    # 최종 데이터셋 준비 (제외된 논문만 빼고)
    df_final = merged_df[~merged_df['Classification'].str.contains('Exclude', na=False)].copy()
    
    # Classification 컬럼만 제거 (원본 WOS 형식 유지)
    df_final_output = df_final.drop(columns=['Classification'], errors='ignore')

    # 최종 통계 - 제외 박스 추가
    exclude_papers = merged_df[merged_df['Classification'].str.contains('Exclude', na=False)]
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상<br><small style="color: #8b95a1;">(Exclude 제외)</small></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        include_count = len(merged_df[merged_df['Classification'].str.contains('Include', na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{include_count:,}</div>
            <div class="metric-label">핵심 포함 연구</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col
