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
        background: #f2f4f6;
        min-height: 100vh;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }
    
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: none;
        border: 1px solid #e5e8eb;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transform: translateY(-1px);
        border-color: #3182f6;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #191f28;
        margin: 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    
    .metric-label {
        font-size: 13px;
        color: #8b95a1;
        margin: 6px 0 0 0;
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    
    .metric-icon {
        background: #3182f6;
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        margin-bottom: 12px;
    }
    
    .chart-container {
        background: white;
        border-radius: 8px;
        padding: 24px;
        box-shadow: none;
        border: 1px solid #e5e8eb;
        margin: 16px 0;
    }
    
    .chart-title {
        font-size: 16px;
        font-weight: 600;
        color: #191f28;
        margin-bottom: 16px;
        letter-spacing: -0.01em;
    }
    
    .section-header {
        background: white;
        color: #191f28;
        padding: 16px 20px;
        border-radius: 8px;
        margin: 20px 0 12px 0;
        box-shadow: none;
        border: 1px solid #e5e8eb;
        position: relative;
        overflow: hidden;
    }
    
    .section-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: #3182f6;
    }
    
    .section-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.01em;
        color: #191f28;
    }
    
    .section-subtitle {
        font-size: 13px;
        color: #8b95a1;
        margin: 4px 0 0 0;
        font-weight: 400;
        letter-spacing: 0;
    }
    
    .info-panel {
        background: #f8fafe;
        border: 1px solid #e1f2ff;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        position: relative;
    }
    
    .success-panel {
        background: #f0fdf4;
        border: 1px solid #dcfce7;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        position: relative;
    }
    
    .warning-panel {
        background: #fffbeb;
        border: 1px solid #fed7aa;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        position: relative;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 12px;
        margin: 20px 0;
    }
    
    .feature-card {
        background: white;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: none;
        border: 1px solid #e5e8eb;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #3182f6;
    }
    
    .feature-icon {
        font-size: 32px;
        margin-bottom: 12px;
        color: #3182f6;
    }
    
    .feature-title {
        font-size: 15px;
        font-weight: 600;
        color: #191f28;
        margin-bottom: 8px;
        letter-spacing: -0.01em;
    }
    
    .feature-desc {
        font-size: 13px;
        color: #8b95a1;
        line-height: 1.5;
        letter-spacing: 0;
    }
    
    .upload-zone {
        background: white;
        border: 1px dashed #d1d5db;
        border-radius: 8px;
        padding: 24px;
        text-align: center;
        margin: 16px 0;
        transition: all 0.2s ease;
    }
    
    .upload-zone:hover {
        background: #f8fafe;
        border-color: #3182f6;
    }
    
    .progress-indicator {
        background: #3182f6;
        height: 3px;
        border-radius: 2px;
        margin: 12px 0;
        animation: pulse 2s infinite;
    }
    
    .file-status {
        background: #f8fafe;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        border-left: 3px solid #3182f6;
        font-family: 'Pretendard', sans-serif;
    }
    
    .stDownloadButton > button {
        background: #3182f6 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: -0.01em !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        font-family: 'Pretendard', sans-serif !important;
    }
    
    .stDownloadButton > button:hover {
        background: #1c64f2 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
    }
    
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 8px !important;
        border: 1px solid #e5e8eb !important;
        font-weight: 500 !important;
        color: #191f28 !important;
        font-family: 'Pretendard', sans-serif !important;
        font-size: 14px !important;
    }
    
    .stDataFrame {
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #e5e8eb !important;
    }
    
    .stSpinner {
        color: #3182f6 !important;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
    }
    
    .stAlert {
        border-radius: 8px !important;
        border: none !important;
        font-family: 'Pretendard', sans-serif !important;
        font-size: 14px !important;
    }
    
    .stSuccess {
        background: #f0fdf4 !important;
        color: #15803d !important;
    }
    
    .stInfo {
        background: #f8fafe !important;
        color: #1d4ed8 !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        color: #d97706 !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        color: #dc2626 !important;
    }
    
    .main-text {
        font-size: 14px;
        color: #191f28;
        line-height: 1.5;
    }
    
    .sub-text {
        font-size: 13px;
        color: #8b95a1;
        line-height: 1.4;
    }
    
    .small-text {
        font-size: 12px;
        color: #8b95a1;
        line-height: 1.3;
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

# --- 라이브 스트리밍 특화 분류 함수 (최종 로직) ---
def classify_article(row):
    """강화된 포함 기준(IC)과 재설계된 로직을 적용한 최종 분류 함수"""
    
    # --- 키워드 셋 정의 ---
    # IC1: 연구의 핵심 주제
    core_streaming_keywords = [
        'live stream', 'livestream', 'live video', 'live broadcast', 
        'real-time stream', 'streaming platform', 'streaming service',
        'live commerce', 'live shopping', 'shoppertainment',
        'streamer', 'viewer', 'streaming audience',
        'twitch', 'youtube live', 'facebook live', 'tiktok live', 'douyin', 'kuaishou', 'taobao live',
        'game streaming', 'esports streaming'
    ]
    
    # IC2: 연구의 핵심 현상 (A. 사회-기술적 동학)
    socio_technical_keywords = [
        # 상호작용
        'interactive', 'interaction', 'interactivity', 'real-time', 'synchronous',
        'social presence', 'telepresence', 'immediacy', 'responsiveness',
        # 사용자 행동/심리
        'user behavior', 'viewer behavior', 'psychology', 'psychological', 'motivation', 'motivate', 
        'engagement', 'engaging', 'addiction', 'addictive', 'loyalty', 'trust', 
        'satisfaction', 'intention', 'intentions', 'emotion', 'affective', 'attitude',
        # 사회적 관계
        'parasocial', 'social relationship', 'social support', 'social influence',
        # 커뮤니티 및 문화
        'community', 'communities', 'virtual community', 'online community', 
        'cultural', 'culture', 'identity', 'identities', 'social capital', 'online culture'
    ]

    # IC2: 연구의 핵심 현상 (B. 플랫폼 생태계 동학)
    platform_ecosystem_keywords = [
        # 비즈니스 모델 및 전략
        'platform', 'platforms', 'ecosystem', 'ecosystems', 'business model', 'business models',
        'monetization', 'revenue', 'governance', 'govern', 'creator economy', 'creators',
        'multi-sided', 'hiring', 'strategy', 'strategic', 'competitive',
        # 상업적 응용
        'commerce', 'marketing', 'influencer', 'brand', 'brands', 'purchase', 'purchasing', 
        'advertising', 'advertise', 'e-commerce', 'social commerce', 'sales', 'sale'
    ]
    
    # 그 외 포함 가능한 기술 연구
    technical_keywords = [
        'architecture', 'architectures', 'algorithm', 'algorithms', 'latency', 'quality of service', 
        'qos', 'video quality', 'webrtc', 'cdn'
    ]

    # EC2: 주변부 연구
    peripheral_mention_indicators = [
        'for example', 'such as', 'including', 'future work', 'future research', 'future study',
        'potential application', 'recommendation for future'
    ]
    
    # EC3: 방법론적 부적합성
    methodological_exclusion_types = [
        'editorial material', 'letter', 'proceedings paper', 'book chapter', 'correction', 
        'retracted publication', 'meeting abstract', 'note', 'short survey'
    ]
    duplicate_indicators = [
        'extended version', 'preliminary version', 'conference version', 'short version'
    ]

    # --- 텍스트 필드 추출 및 결합 ---
    def extract_text(value):
        return str(value).lower().strip() if pd.notna(value) else ""
    
    title = extract_text(row.get('TI', ''))
    abstract = extract_text(row.get('AB', ''))
    author_keywords = extract_text(row.get('DE', ''))
    keywords_plus = extract_text(row.get('ID', ''))
    document_type = extract_text(row.get('DT', ''))
    
    full_text = ' '.join([title, abstract, author_keywords, keywords_plus])
    
    # --- 최종 분류 로직 ---
    
    # Stage 1: 방법론적 부적합성 배제 (EC3)
    if not any(doc in document_type for doc in ['article', 'review']):
        return 'EC3 - 방법론적 부적합성'
    if any(indicator in full_text for indicator in duplicate_indicators):
        return 'EC3 - 방법론적 부적합성'

    # Stage 2: 주제 적합성(IC1) 및 주변성(EC2) 검증
    has_core_streaming = any(kw in full_text for kw in core_streaming_keywords)
    if not has_core_streaming:
        return 'EC2 - 높은 주제 주변성'
    if any(indicator in full_text for indicator in peripheral_mention_indicators):
        if sum(1 for kw in core_streaming_keywords if kw in full_text) <= 2:
            return 'EC2 - 높은 주제 주변성'

    # Stage 3: 핵심 현상(IC2) 분석 여부 검증
    if any(kw in full_text for kw in socio_technical_keywords):
        return 'Include - Socio-Technical Dynamics (사회-기술적 동학)'
    
    if any(kw in full_text for kw in platform_ecosystem_keywords):
        return 'Include - Platform Ecosystem Dynamics (플랫폼 생태계 동학)'
        
    if any(kw in full_text for kw in technical_keywords):
        # 순수 기술(e.g., control theory)과 구분하기 위해, 사회/경제적 맥락 단어가 하나라도 있는지 확인
        context_words = ['user', 'viewer', 'audience', 'business', 'market', 'service', 'platform', 'streamer']
        if any(cw in full_text for cw in context_words):
             return 'Include - Technical Implementation (기술적 구현)'

    # Stage 4: 핵심 현상 분석이 없는 경우 최종 배제 (EC4)
    return 'EC4 - 핵심 현상 분석 부재'


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

# --- 이하 UI 코드는 변경 없음 ---

# --- 메인 헤더 ---
st.markdown("""
<div style="position: relative; text-align: center; padding: 2.5rem 0 3rem 0; background: linear-gradient(135deg, #3182f6, #1c64f2); color: white; border-radius: 8px; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(49,130,246,0.15); overflow: hidden;">
    <div style="position: absolute; top: 1rem; left: 1.5rem; color: white;">
        <div style="font-size: 12px; font-weight: 600; margin-bottom: 3px; letter-spacing: 0.3px;">HANYANG UNIVERSITY</div>
        <div style="font-size: 11px; opacity: 0.9; font-weight: 500;">Technology Management Research</div>
        <div style="font-size: 10px; opacity: 0.8; margin-top: 4px; font-weight: 400;">mot.hanyang.ac.kr</div>
    </div>
    <div style="position: absolute; top: 1rem; right: 1.5rem; text-align: right; color: rgba(255,255,255,0.9); font-size: 11px;">
        <p style="margin: 0; font-weight: 500;">Developed by: 임태경 (Teddy Lym)</p>
    </div>
    <h1 style="font-size: 3rem; font-weight: 700; margin-bottom: 0.3rem; letter-spacing: -0.02em;">
        WOS PREP
    </h1>
    <p style="font-size: 1.1rem; margin: 0; font-weight: 500; opacity: 0.95; letter-spacing: -0.01em;">
        SCIMAT Edition
    </p>
    <div style="width: 80px; height: 3px; background-color: rgba(255,255,255,0.3); margin: 1.5rem auto; border-radius: 2px;"></div>
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
        <div class="feature-title">학술적 엄밀성</div>
        <div class="feature-desc">개념 기반 학술적 정제 적용</div>
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
    
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 학술적 정제 적용 중..."):
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)
        
        if merged_df is None:
            st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다. 파일들이 Web of Science에서 다운로드한 정품 Plain Text 파일인지 확인해주세요.")
            st.stop()
        
        merged_df['Classification'] = merged_df.apply(classify_article, axis=1)

    successful_files = len([s for s in file_status if s['status'] == 'SUCCESS'])
    total_papers_before_filter = len(merged_df)
    
    df_excluded_strict = merged_df[merged_df['Classification'].str.startswith('EC', na=False)]
    df_for_analysis = merged_df[~merged_df['Classification'].str.startswith('EC', na=False)].copy()
    
    total_papers = len(df_for_analysis)
    
    st.success(f"✅ 병합 및 학술적 정제 완료! {successful_files}개 파일에서 최종 {total_papers:,}편의 논문을 성공적으로 처리했습니다.")
    
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다. (원본 총 {total_papers_before_filter + duplicates_removed:,}편 → 정제 후 {total_papers_before_filter:,}편)")
    else:
        st.info("✅ 중복 논문 없음 - 모든 논문이 고유한 데이터입니다.")

    st.markdown("""
    <div class="section-header">
        <div class="section-title">📄 파일별 처리 상태</div>
        <div class="section-subtitle">업로드된 각 파일의 처리 결과</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            for status in file_status:
                color = "#10b981" if status['status'] == 'SUCCESS' else "#ef4444"
                icon = "✅" if status['status'] == 'SUCCESS' else "❌"
                st.markdown(f"""<div style="margin-bottom: 8px; padding: 12px; background: #f9fafb; border-left: 3px solid {color}; border-radius: 6px;">
                    <strong>{icon} {status['filename']}</strong><br>
                    <small style="color: #8b95a1;">{status['message']}</small>
                </div>""", unsafe_allow_html=True)
        with col2:
            success_count = len([s for s in file_status if s['status'] == 'SUCCESS'])
            error_count = len(file_status) - success_count
            st.markdown(f"""<div class="metric-card" style="margin-bottom:8px;"><div class="metric-icon">✅</div><div class="metric-value">{success_count}</div><div class="metric-label">성공 파일</div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="metric-card"><div class="metric-icon" style="background-color:#ef4444;">❌</div><div class="metric-value">{error_count}</div><div class="metric-label">실패 파일</div></div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 학술적 정제 결과</div>
        <div class="section-subtitle">재설계된 포함 기준(IC) 적용 후 연구 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    total_excluded = len(df_excluded_strict)
    df_final_output = df_for_analysis.drop(columns=['Classification'], errors='ignore')
    
    columns = st.columns(4)
    with columns[0]:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📋</div><div class="metric-value">{len(df_final_output):,}</div><div class="metric-label">최종 분석 대상</div></div>""", unsafe_allow_html=True)
    
    include_papers = len(df_for_analysis[df_for_analysis['Classification'].str.contains('Include', na=False)])
    with columns[1]:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">✅</div><div class="metric-value">{include_papers:,}</div><div class="metric-label">핵심 포함 연구</div></div>""", unsafe_allow_html=True)
    
    with columns[2]:
        processing_rate = (len(df_final_output) / total_papers_before_filter * 100) if total_papers_before_filter > 0 else 0
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📊</div><div class="metric-value">{processing_rate:.1f}%</div><div class="metric-label">최종 포함 비율</div></div>""", unsafe_allow_html=True)
    
    with columns[3]:
        st.markdown(f"""<div class="metric-card" style="margin-bottom: 8px; text-align: center;"><div class="metric-icon" style="margin-left: auto; margin-right: auto; background-color:#ef4444;">⛔</div><div class="metric-value">{total_excluded:,}</div><div class="metric-label">학술적 배제</div></div>""", unsafe_allow_html=True)
        if st.button("상세보기 및 다운로드", key="exclude_details_button", use_container_width=True):
            st.session_state['show_exclude_details'] = not st.session_state.get('show_exclude_details', False)

    if st.session_state.get('show_exclude_details', False) and total_excluded > 0:
        st.markdown("""<div style="background: #fef2f2; padding: 20px; border-radius: 16px; margin: 20px 0; border: 1px solid #ef4444;"><h4 style="color: #dc2626; margin-bottom: 16px; font-weight: 700;">⛔ 학술적 배제 기준에 따른 제외 논문</h4></div>""", unsafe_allow_html=True)

        excluded_excel_data = [{'번호': idx + 1, '논문 제목': str(paper.get('TI', 'N/A')), '출판연도': str(paper.get('PY', 'N/A')), '저널명': str(paper.get('SO', 'N/A')), '저자': str(paper.get('AU', 'N/A')), '배제 사유': str(paper.get('Classification', 'N/A'))} for idx, paper in df_excluded_strict.iterrows()]
        excluded_excel_df = pd.DataFrame(excluded_excel_data)
        excel_buffer_excluded = io.BytesIO()
        with pd.ExcelWriter(excel_buffer_excluded, engine='openpyxl') as writer:
            excluded_excel_df.to_excel(writer, sheet_name='Excluded_Papers', index=False)
        st.download_button(label=f"📊 제외된 논문 목록 엑셀 다운로드 ({len(df_excluded_strict)}편)", data=excel_buffer_excluded.getvalue(), file_name=f"excluded_papers_{len(df_excluded_strict)}papers.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="secondary", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        exclusion_categories = {'EC2': '높은 주제 주변성', 'EC3': '방법론적 부적합성', 'EC4': '핵심 현상 분석 부재'}
        for ec_code, description in exclusion_categories.items():
            ec_papers = df_excluded_strict[df_excluded_strict['Classification'] == ec_code]
            if not ec_papers.empty:
                st.markdown(f"""<div style="margin: 12px 0; padding: 16px; background: white; border-left: 4px solid #ef4444; border-radius: 12px;"><strong style="color: #dc2626;">{ec_code}: {description}</strong> <span style="color: #8b95a1;">({len(ec_papers)}편)</span></div>""", unsafe_allow_html=True)
                for _, paper in ec_papers.head(5).iterrows():
                    title = str(paper.get('TI', 'N/A'))[:80] + "..." if len(str(paper.get('TI', 'N/A'))) > 80 else str(paper.get('TI', 'N/A'))
                    year = str(paper.get('PY', 'N/A'))
                    source = str(paper.get('SO', 'N/A'))[:40] + "..." if len(str(paper.get('SO', 'N/A'))) > 40 else str(paper.get('SO', 'N/A'))
                    st.markdown(f"""<div style="margin: 8px 0 8px 20px; padding: 12px; background: #f9fafb; border-radius: 8px; font-size: 14px;"><div style="font-weight: 500; color: #374151; margin-bottom: 4px;">{title}</div><div style="color: #6b7280; font-size: 12px;">{year} | {source}</div></div>""", unsafe_allow_html=True)
                if len(ec_papers) > 5:
                    st.markdown(f"<p style='color: #8b95a1; text-align: right; margin: 8px 20px 16px 20px; font-size: 12px;'>... 외 {len(ec_papers) - 5}편 더</p>", unsafe_allow_html=True)

    st.markdown("""<div class="chart-container"><div class="chart-title">학술적 정제 후 연구 분류 분포</div>""", unsafe_allow_html=True)
    classification_counts_df = df_for_analysis['Classification'].value_counts().reset_index()
    classification_counts_df.columns = ['분류', '논문 수']
    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        st.dataframe(classification_counts_df, use_container_width=True, hide_index=True)
    with col2:
        selection = alt.selection_point(fields=['분류'], on='mouseover', nearest=True)
        base = alt.Chart(classification_counts_df).encode(theta=alt.Theta(field="논문 수", type="quantitative", stack=True), color=alt.Color(field="분류", type="nominal", title="Classification", scale=alt.Scale(scheme='tableau20'), legend=alt.Legend(orient="right")), opacity=alt.condition(selection, alt.value(1), alt.value(0.8))).add_params(selection)
        pie = base.mark_arc(outerRadius=150, innerRadius=90)
        text_total = alt.Chart(pd.DataFrame([{'value': f'{len(df_final_output)}'}])).mark_text(align='center', baseline='middle', fontSize=45, fontWeight='bold', color='#0064ff').encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame([{'value': 'Refined Papers'}])).mark_text(align='center', baseline='middle', fontSize=16, dy=30, color='#8b95a1').encode(text='value:N')
        chart = (pie + text_total + text_label).properties(width=350, height=350).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="section-header">
        <div class="section-title">📥 학술적 정제 완료 - SCIMAT 분석용 파일 다운로드</div>
        <div class="section-subtitle">최종 포함 기준이 적용된 고품질 WOS Plain Text 파일</div>
    </div>
    """, unsafe_allow_html=True)
    text_data = convert_to_scimat_wos_format(df_final_output)
    st.download_button(label="📥 최종 데이터셋 다운로드", data=text_data, file_name=f"live_streaming_final_dataset_{len(df_final_output)}papers.txt", mime="text/plain", type="primary", use_container_width=True)
