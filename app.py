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

# --- 라이브 스트리밍 특화 분류 함수 (사용자 요청 기준 적용) ---
def classify_article(row):
    """사용자 요청에 따른 포함/배제 기준(IC/EC)을 적용한 논문 분류 함수"""
    
    # --- 키워드 셋 정의 ---
    # IC1: 주제 중심성 (라이브 스트리밍 핵심)
    core_streaming_keywords = [
        'live stream', 'livestream', 'live video', 'live broadcast', 'live e-commerce',
        'real-time stream', 'streaming platform', 'streaming service', 'live shopping',
        'live commerce', 'shoppertainment', 'streamer', 'viewer', 'broadcaster',
        'twitch', 'youtube live', 'facebook live', 'tiktok live', 'douyin', 'kuaishou', 'taobao live'
    ]
    
    # EC3: 상호작용성 부재
    interaction_keywords = [
        'interactive', 'interaction', 'real-time', 'real time', 'two-way', 'bidirectional',
        'synchronous', 'live chat', 'audience participation', 'user engagement', 'parasocial',
        'viewer engagement', 'community', 'social presence'
    ]

    # EC2: 사회-기술적 맥락 부재 (순수 기술)
    pure_tech_exclusions = [
        'routing protocol', 'network topology', 'mac protocol', 'tcp/ip', 'udp', 'rtmp', 'hls', 'dash',
        'video codec', 'audio codec', 'h.264', 'h.265', 'hevc', 'mpeg', 'video compression',
        'cdn architecture', 'server load balancing', 'edge server', 'bandwidth allocation', 'qos',
        'vlsi', 'fpga', 'asic', 'signal processing', 'modulation', 'mimo', 'ofdm', 'latency optimization'
    ]
    # 사회-기술적 맥락을 나타내는 키워드 (EC2를 피하기 위함)
    socio_tech_context_keywords = [
        'user behavior', 'psychology', 'motivation', 'engagement', 'addiction', 'parasocial', 
        'social presence', 'trust', 'social impact', 'cultural', 'community', 'identity', 
        'online culture', 'social capital', 'digital labor', 'commerce', 'marketing', 'influencer', 
        'brand', 'purchase intention', 'advertising', 'e-commerce', 'social commerce', 'creator economy'
    ]

    # EC1: 주제 관련성 부족 (부차적 맥락)
    peripheral_mention_indicators = [
        'for example', 'such as', 'including', 'future work', 'future research', 'future direction'
    ]

    # EC4: 학술적 엄밀성 부족
    methodological_exclusion_types = [
        'editorial material', 'letter', 'book review', 'meeting abstract', 
        'proceedings paper', 'correction', 'errata', 'note', 'short survey', 'white paper'
    ]
    
    # EC5: 중복 게재
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
    language = extract_text(row.get('LA', ''))
    
    full_text = ' '.join([title, abstract, author_keywords, keywords_plus])
    
    # --- 분류 로직 (계층적 필터링) ---
    
    # [EC4/IC2] 학술적 형태 및 엄밀성 검증
    if any(doc_type in document_type for doc_type in methodological_exclusion_types):
        return 'EC4 - 학술적 엄밀성 부족'
    if not any(doc in document_type for doc in ['article', 'review']):
        return 'EC4 - 학술적 엄밀성 부족'

    # [IC3] 언어 검증
    if language and language != 'english':
        return 'EC - Non-English'

    # [EC5] 중복 게재 검증
    if any(indicator in full_text for indicator in duplicate_indicators):
        return 'EC5 - 중복 게재'

    # [IC1/EC1] 주제 중심성 및 관련성 부족 검증
    has_core_keyword = any(kw in full_text for kw in core_streaming_keywords)
    if not has_core_keyword:
        return 'EC1 - 주제 관련성 부족'
    
    is_peripheral = any(indicator in full_text for indicator in peripheral_mention_indicators)
    core_keyword_count = sum(1 for kw in core_streaming_keywords if kw in full_text)
    if is_peripheral and core_keyword_count <= 2:
        return 'EC1 - 주제 관련성 부족'

    # [EC3] 상호작용성 부재 검증
    has_interaction = any(kw in full_text for kw in interaction_keywords)
    if not has_interaction:
        return 'EC3 - 상호작용성 부재'

    # [EC2] 사회-기술적 맥락 부재 검증
    is_pure_tech = any(kw in full_text for kw in pure_tech_exclusions)
    has_socio_context = any(kw in full_text for kw in socio_tech_context_keywords)
    if is_pure_tech and not has_socio_context:
        return 'EC2 - 사회-기술적 맥락 부재'

    # 모든 제외 기준을 통과한 경우, 포함
    return 'Include'


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
    
    # 프로그레스 인디케이터
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 학술적 정제 적용 중..."):
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
        
        # 논문 분류 수행 - 강화된 기준 적용
        merged_df['Classification'] = merged_df.apply(classify_article, axis=1)

    # 성공적인 파일 개수 계산
    successful_files = len([s for s in file_status if s['status'] == 'SUCCESS'])
    total_papers_before_filter = len(merged_df)
    
    # 최종 데이터셋 준비
    df_excluded_strict = merged_df[~merged_df['Classification'].str.startswith('Include', na=False)]
    df_for_analysis = merged_df[merged_df['Classification'].str.startswith('Include', na=False)].copy()
    
    total_papers = len(df_for_analysis)
    
    st.success(f"✅ 병합 및 학술적 정제 완료! {successful_files}개 파일에서 최종 {total_papers:,}편의 논문을 성공적으로 처리했습니다.")
    
    # 중복 제거 결과 표시 - 실제 결과만
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다. (원본 총 {total_papers_before_filter + duplicates_removed:,}편 → 정제 후 {total_papers_before_filter:,}편)")
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
        issues, recommendations = diagnose_merged_quality(df_for_analysis, successful_files, duplicates_removed)

    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">🔍 병합 데이터 품질 진단 결과</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h5 style="color: #ef4444; margin-bottom: 16px;">🚨 발견된 문제점 (Identified Issues)</h5>', unsafe_allow_html=True)
        
        if issues:
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.markdown("✅ **문제점 없음** - 병합 데이터 품질 우수")
    
    with col2:
        st.markdown('<h5 style="color: #10b981; margin-bottom: 16px;">💡 병합 결과 (Merge Results)</h5>', unsafe_allow_html=True)
        
        if recommendations:
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.markdown("🎯 **최적 상태** - SCIMAT 완벽 호환")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 병합 성공 알림
    st.markdown("""
    <div class="success-panel">
        <h4 style="color: #065f46; margin-bottom: 20px; font-weight: 700;">🎯 다중 파일 병합 및 학술적 정제 성공!</h4>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;">여러 WOS Plain Text 파일이 성공적으로 하나로 병합되었습니다.</p>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;"><strong>학술적 엄밀성:</strong> 강화된 포함/배제 기준을 체계적으로 적용하여 연구의 신뢰성을 확보했습니다.</p>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;"><strong>SCIMAT 호환성:</strong> 병합된 파일은 SCIMAT에서 100% 정상 작동합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 학술적 정제 결과</div>
        <div class="section-subtitle">학술적 정제 기준 적용 후 라이브 스트리밍 연구 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    # 총 배제된 논문 수 계산
    total_excluded = len(df_excluded_strict)
    
    # Classification 컬럼만 제거 (원본 WOS 형식 유지)
    df_final_output = df_for_analysis.drop(columns=['Classification'], errors='ignore')
    
    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상 (Final)<br><small style="color: #8b95a1;">(정제 기준 적용후)</small></div>
        </div>
        """, unsafe_allow_html=True)
    
    include_papers = len(df_for_analysis)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{include_papers:,}</div>
            <div class="metric-label">핵심 포함 연구 (Included)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        processing_rate = (len(df_final_output) / total_papers_before_filter * 100) if total_papers_before_filter > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{processing_rate:.1f}%</div>
            <div class="metric-label">최종 포함 비율 (Inclusion Rate)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # 배제된 논문들을 위한 토글 버튼이 있는 박스
        col4_inner1, col4_inner2 = st.columns([3, 1])
        
        with col4_inner1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">⛔</div>
                <div class="metric-value">{total_excluded:,}</div>
                <div class="metric-label">학술적 배제 (Excluded)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4_inner2:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            if st.button(
                "📋", 
                key="exclude_details_button",
                help="배제된 논문 상세 보기 (View Excluded Papers)"
            ):
                st.session_state['show_exclude_details'] = not st.session_state.get('show_exclude_details', False)

    # 배제된 논문 상세 정보 토글 표시
    if st.session_state.get('show_exclude_details', False) and total_excluded > 0:
        st.markdown("""
        <div style="background: #fef2f2; padding: 20px; border-radius: 16px; margin: 20px 0; border: 1px solid #ef4444;">
            <h4 style="color: #dc2626; margin-bottom: 16px; font-weight: 700;">⛔ 학술적 배제 기준에 따른 제외 논문 (Excluded Papers by Criteria)</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # --- 제외 논문 다운로드 버튼 추가 ---
        excluded_excel_data = []
        for idx, (_, paper) in enumerate(df_excluded_strict.iterrows(), 1):
            excluded_excel_data.append({
                'No (번호)': idx,
                'Title (논문 제목)': str(paper.get('TI', 'N/A')),
                'Year (출판연도)': str(paper.get('PY', 'N/A')),
                'Journal (저널명)': str(paper.get('SO', 'N/A')),
                'Authors (저자)': str(paper.get('AU', 'N/A')),
                'Exclusion Reason (제외 사유)': str(paper.get('Classification', 'N/A')),
                'Author Keywords (저자 키워드)': str(paper.get('DE', 'N/A')),
                'WOS Keywords (WOS 키워드)': str(paper.get('ID', 'N/A')),
                'Abstract (초록)': str(paper.get('AB', 'N/A')),
                'Document Type (문서유형)': str(paper.get('DT', 'N/A'))
            })
        
        excluded_excel_df = pd.DataFrame(excluded_excel_data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            excluded_excel_df.to_excel(writer, sheet_name='Excluded_Papers', index=False)
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📊 제외된 논문 전체 목록 엑셀 다운로드 (Download Excluded Papers as Excel)",
            data=excel_data,
            file_name=f"excluded_papers_list_{len(df_excluded_strict)}papers.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # 배제 기준별 분류 및 표시
        exclusion_categories = {
            'EC1': '주제 관련성 부족',
            'EC2': '사회-기술적 맥락 부재',
            'EC3': '상호작용성 부재',
            'EC4': '학술적 엄밀성 부족',
            'EC5': '중복 게재',
        }
        
        # EC 기준별 배제 현황
        for ec_code, description in exclusion_categories.items():
            ec_papers = df_excluded_strict[df_excluded_strict['Classification'].str.startswith(ec_code, na=False)]
            if len(ec_papers) > 0:
                st.markdown(f"""
                <div style="margin: 12px 0; padding: 16px; background: white; border-left: 4px solid #ef4444; border-radius: 12px;">
                    <strong style="color: #dc2626;">{ec_code}: {description}</strong> 
                    <span style="color: #8b95a1;">({len(ec_papers)}편)</span>
                </div>
                """, unsafe_allow_html=True)
                
                # 상위 5편만 샘플로 표시
                for idx, (_, paper) in enumerate(ec_papers.head(5).iterrows(), 1):
                    title = str(paper.get('TI', 'N/A'))[:80] + "..." if len(str(paper.get('TI', 'N/A'))) > 80 else str(paper.get('TI', 'N/A'))
                    year = str(paper.get('PY', 'N/A'))
                    source = str(paper.get('SO', 'N/A'))[:40] + "..." if len(str(paper.get('SO', 'N/A'))) > 40 else str(paper.get('SO', 'N/A'))
                    
                    st.markdown(f"""
                    <div style="margin: 8px 0 8px 20px; padding: 12px; background: #f9fafb; border-radius: 8px; font-size: 14px;">
                        <div style="font-weight: 500; color: #374151; margin-bottom: 4px;">{title}</div>
                        <div style="color: #6b7280; font-size: 12px;">{year} | {source}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if len(ec_papers) > 5:
                    st.markdown(f"<p style='color: #8b95a1; text-align: right; margin: 8px 20px 16px 20px; font-size: 12px;'>... 외 {len(ec_papers) - 5}편 더</p>", unsafe_allow_html=True)

    # 배제 기준 적용 결과 요약
    st.markdown(f"""
    <div class="info-panel">
        <h4 style="color: #0064ff; margin-bottom: 16px; font-weight: 700;">📊 학술적 엄밀성 확보</h4>
        <p style="color: #0064ff; margin: 6px 0; font-weight: 500;"><strong>총 입력 (Total Input):</strong> {total_papers_before_filter:,}편의 논문</p>
        <p style="color: #0064ff; margin: 6px 0; font-weight: 500;"><strong>배제 적용 (Excluded):</strong> {total_excluded:,}편 제외 ({(total_excluded/total_papers_before_filter*100):.1f}%)</p>
        <p style="color: #0064ff; margin: 6px 0; font-weight: 500;"><strong>최종 분석 (Final Dataset):</strong> {len(df_final_output):,}편으로 정제된 고품질 데이터셋</p>
        <p style="color: #0064ff; margin: 6px 0; font-weight: 500;"><strong>핵심 연구 (Core Research):</strong> {include_papers:,}편의 직접 관련 라이브스트리밍 연구 확보</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 논문 분류 현황 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">학술적 정제 후 연구 분류 분포 (Distribution of Research after Filtering)</div>
    """, unsafe_allow_html=True)

    classification_counts_df = df_for_analysis['Classification'].value_counts().reset_index()
    classification_counts_df.columns = ['Classification (분류)', 'Count (논문 수)']

    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        st.dataframe(classification_counts_df, use_container_width=True, hide_index=True)

    with col2:
        # 도넛 차트
        selection = alt.selection_point(fields=['Classification (분류)'], on='mouseover', nearest=True)

        base = alt.Chart(classification_counts_df).encode(
            theta=alt.Theta(field="Count (논문 수)", type="quantitative", stack=True),
            color=alt.Color(field="Classification (분류)", type="nominal", title="Classification (분류)",
                           scale=alt.Scale(scheme='tableau20'),
                           legend=alt.Legend(orient="right", titleColor="#191f28", labelColor="#8b95a1")),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.8))
        ).add_params(selection)

        pie = base.mark_arc(outerRadius=150, innerRadius=90)
        text_total = alt.Chart(pd.DataFrame([{'value': f'{len(df_final_output)}'}])).mark_text(
            align='center', baseline='middle', fontSize=45, fontWeight='bold', color='#0064ff'
        ).encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame([{'value': 'Included Papers'}])).mark_text(
            align='center', baseline='middle', fontSize=16, dy=30, color='#8b95a1'
        ).encode(text='value:N')

        chart = (pie + text_total + text_label).properties(
            width=350, height=350
        ).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 연도별 연구 동향 ---
    if 'PY' in df_final_output.columns:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">정제된 라이브 스트리밍 연구 동향 (Publication Trend of Refined Papers)</div>
        """, unsafe_allow_html=True)
        
        df_trend = df_final_output.copy()
        df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
        df_trend.dropna(subset=['PY'], inplace=True)
        df_trend['PY'] = df_trend['PY'].astype(int)
        
        yearly_counts = df_trend['PY'].value_counts().reset_index()
        yearly_counts.columns = ['Year (발행 연도)', 'Count (논문 수)']
        yearly_counts = yearly_counts[yearly_counts['Year (발행 연도)'] <= 2025].sort_values('Year (발행 연도)')

        if len(yearly_counts) > 0:
            line_chart = alt.Chart(yearly_counts).mark_line(
                point={'size': 80, 'filled': True}, strokeWidth=3, color='#0064ff'
            ).encode(
                x=alt.X('Year (발행 연도):O', title='Publication Year (발행 연도)'),
                y=alt.Y('Count (논문 수):Q', title='Number of Papers (논문 수)'),
                tooltip=['Year (발행 연도)', 'Count (논문 수)']
            ).properties(height=300)
            
            st.altair_chart(line_chart, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 키워드 샘플 확인 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">정제된 데이터 키워드 품질 확인 (Keyword Quality Check)</div>
    """, unsafe_allow_html=True)
    
    sample_data = []
    sample_rows = df_for_analysis.head(3)
    
    for idx, row in sample_rows.iterrows():
        title = str(row.get('TI', 'N/A'))[:80] + "..." if len(str(row.get('TI', 'N/A'))) > 80 else str(row.get('TI', 'N/A'))
        de_keywords = str(row.get('DE', 'N/A')) if pd.notna(row.get('DE')) else 'N/A'
        id_keywords = str(row.get('ID', 'N/A')) if pd.notna(row.get('ID')) else 'N/A'
        
        # 키워드 개수 계산
        de_count = len([k.strip() for k in de_keywords.split(';') if k.strip()]) if de_keywords != 'N/A' else 0
        id_count = len([k.strip() for k in id_keywords.split(';') if k.strip()]) if id_keywords != 'N/A' else 0
        
        sample_data.append({
            'Title (논문 제목)': title,
            'DE Keywords': de_keywords[:100] + "..." if len(de_keywords) > 100 else de_keywords,
            'ID Keywords': id_keywords[:100] + "..." if len(id_keywords) > 100 else id_keywords,
            'DE Count': de_count,
            'ID Count': id_count
        })
    
    if sample_data:
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True, hide_index=True)
        
        # 키워드 품질 평가
        avg_de = sum([d['DE Count'] for d in sample_data]) / len(sample_data) if sample_data else 0
        avg_id = sum([d['ID Count'] for d in sample_data]) / len(sample_data) if sample_data else 0
        
        if avg_de >= 3 and avg_id >= 3:
            st.success("✅ 키워드 품질 우수 - SCIMAT에서 원활한 그루핑 예상")
        elif avg_de >= 2 or avg_id >= 2:
            st.warning("⚠️ 키워드 품질 보통 - SCIMAT에서 일부 제한 가능")
        else:
            st.error("❌ 키워드 품질 부족 - 원본 WOS 다운로드 설정 확인 필요")

    st.markdown("</div>", unsafe_allow_html=True)

    # (기존 Review 논문 상세 목록 섹션은 새로운 분류 기준에 따라 불필요하여 제거)

    # 병합 성과 강조 - 학술적 엄밀성 반영
    success_info = []
    success_info.append(f"<strong>파일 통합:</strong> {successful_files}개의 WOS 파일을 하나로 병합")
    
    if duplicates_removed > 0:
        success_info.append(f"<strong>중복 제거:</strong> {duplicates_removed}편의 중복 논문 자동 감지 및 제거")
    
    success_info.append(f"<strong>학술적 엄밀성:</strong> 개념 기반 배제 기준으로 {total_excluded}편 제외")
    success_info.append(f"<strong>최종 규모:</strong> {len(df_final_output):,}편의 고품질 논문으로 정제된 데이터셋")
    success_info.append(f"<strong>핵심 연구:</strong> {include_papers}편의 직접 관련 라이브스트리밍 연구 확보")
    success_info.append("<strong>SCIMAT 호환:</strong> 완벽한 WOS Plain Text 형식으로 100% 호환성 보장")
    
    success_content = "".join([f"<p style='color: #0064ff; margin: 6px 0; font-weight: 500;'>{info}</p>" for info in success_info])
    
    st.markdown(f"""
    <div class="info-panel">
        <h4 style="color: #0064ff; margin-bottom: 16px; font-weight: 700;">🎯 학술적 데이터 정제 완료</h4>
        {success_content}
        <div style="margin-top: 16px; padding: 12px; background: rgba(0,100,255,0.1); border-radius: 8px;">
            <p style='color: #0064ff; margin: 0; font-weight: 600; font-size: 14px;'>
            💡 <strong>배제 기준 적용률:</strong> {(total_excluded/total_papers_before_filter*100):.1f}% 
            - 연구 질문에 직접적으로 기여하는 논문만을 선별하여 분석의 깊이와 신뢰성을 확보했습니다.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 최종 파일 다운로드 섹션 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📥 학술적 정제 완료 - SCIMAT 분석용 파일 다운로드</div>
        <div class="section-subtitle">강화된 포함/배제 기준 적용 후 정제된 고품질 WOS Plain Text 파일</div>
    </div>
    """, unsafe_allow_html=True)
    
    # SCIMAT 호환 파일 다운로드
    text_data = convert_to_scimat_wos_format(df_final_output)
    
    download_clicked = st.download_button(
        label="📥 다운로드 (Download)",
        data=text_data,
        file_name=f"live_streaming_academic_filtered_scimat_{len(df_final_output)}papers.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
        key="download_final_file",
        help="학술적 정제 기준 적용 후 SCIMAT에서 바로 사용 가능한 WOS Plain Text 파일"
    )

# --- 하단 여백 및 추가 정보 ---
st.markdown("<br>", unsafe_allow_html=True)

# 도움말 섹션 - 항상 표시
with st.expander("❓ 자주 묻는 질문 (FAQ)", expanded=False):
    st.markdown("""
    **Q: 여러 WOS 파일을 어떻게 한 번에 처리하나요?**
    A: WOS에서 여러 번 Plain Text 다운로드한 후, 모든 .txt 파일을 한 번에 업로드하면 자동으로 병합됩니다.
    
    **Q: 중복된 논문이 있을까봐 걱정됩니다.**
    A: UT(Unique Article Identifier) 기준으로 자동 중복 제거되며, UT가 없으면 제목+저자 조합으로 중복을 감지합니다.
    
    **Q: WOS에서 어떤 설정으로 다운로드해야 하나요?**
    A: Export → Record Content: "Full Record and Cited References", File Format: "Plain Text"로 설정하세요. 인용 관계 분석을 위해 참고문헌 정보가 필수입니다.
    
    **Q: 어떤 기준으로 논문이 배제되나요?**
    A: 아래의 체계적인 기준에 따라 연구의 깊이와 신뢰성을 확보합니다.
    - **EC1 (주제 관련성 부족):** 라이브 스트리밍을 부차적 맥락으로만 언급한 연구
    - **EC2 (사회-기술적 맥락 부재):** 사용자나 사회적 함의 없이 순수 기술만 다룬 연구
    - **EC3 (상호작용성 부재):** 실시간 상호작용 개념이 없는 단방향 VOD 연구
    - **EC4 (학술적 엄밀성 부족):** 동료 심사를 거치지 않은 사설, 서평 등
    - **EC5 (중복):** 명백히 중복 게재된 연구
    
    **Q: SCIMAT에서 키워드 정리를 어떻게 하나요?**
    A: Group set → Word → Find similar words by distances (Maximum distance: 1)로 유사 키워드를 자동 통합하고, Word Group manual set에서 수동으로 관련 키워드들을 그룹화하세요.
    
    **Q: SCIMAT 분석 설정은 어떻게 하나요?**
    A: Unit of Analysis: "Author's words + Source's words", Network Type: "Co-occurrence", Normalization: "Equivalence Index", Clustering: "Simple Centers Algorithm" (Maximum network size: 50)를 권장합니다.
    
    **Q: 병합된 파일이 SCIMAT에서 제대로 로딩되지 않습니다.**
    A: 원본 WOS 파일들이 'FN Clarivate Analytics Web of Science'로 시작하는 정품 Plain Text 파일인지 확인하세요.
    
    **Q: SCIMAT에서 Period는 어떻게 설정하나요?**
    A: 연구 분야의 진화 단계를 반영하여 의미 있게 구분하되, 각 Period당 최소 50편 이상의 논문을 포함하도록 설정하세요.
    
    **Q: 몇 개의 파일까지 동시에 업로드할 수 있나요?**
    A: 기술적으로는 제한이 없지만, 안정성을 위해 10개 이하의 파일을 권장합니다. 매우 큰 데이터셋의 경우 나누어서 처리하세요.
    """)

# SciMAT 분석 가이드 - 항상 표시
with st.expander("📊 WOS → SciMAT 분석 실행 가이드", expanded=False):
    st.markdown("""
    ### 필요한 것
    - SciMAT 소프트웨어 (무료 다운로드)
    - 다운로드된 WOS Plain Text 파일
    - Java 1.8 이상
    
    ### 1단계: SciMAT 시작하기
    
    **새 프로젝트 생성**
    ```
    1. SciMAT 실행 (SciMAT.jar 더블클릭)
    2. File → New Project
    3. Path: 저장할 폴더 선택
    4. File name: 프로젝트 이름 입력
    5. Accept
    ```
    
    **데이터 불러오기**
    ```
    1. File → Add Files
    2. "ISI WoS" 선택
    3. 다운로드한 txt 파일 선택
    4. 로딩 완료까지 대기
    ```
    
    ### 2단계: 키워드 정리하기
    
    **유사 키워드 자동 통합**
    ```
    1. Group set → Word → Find similar words by distances
    2. Maximum distance: 1 (한 글자 차이)
    3. 같은 의미 단어들 확인하고 Move로 통합
    ```
    의미: 철자가 1글자만 다른 단어들을 찾아서 제안 (예: "platform" ↔ "platforms")
    
    **수동으로 키워드 정리**
    ```
    1. Group set → Word → Word Group manual set
    2. Words without group 목록 확인
    3. 관련 키워드들 선택 후 New group으로 묶기
    4. 불필요한 키워드 제거
    ```
    목적: 데이터 품질 향상, 의미 있는 클러스터 형성
    
    ### 3단계: 시간 구간 설정
    
    **Period 만들기**
    ```
    1. Knowledge base → Periods → Periods manager
    2. Add 버튼으로 시간 구간 생성:
       - Period 1: 1996-2006 (태동기)
       - Period 2: 2007-2016 (형성기)
       - Period 3: 2017-2021 (확산기)
       - Period 4: 2022-2024 (성숙기)
    ```
    원리: 연구 분야의 진화 단계를 반영한 의미 있는 구분
    
    **각 Period에 논문 할당**
    ```
    1. Period 1 클릭 → Add
    2. 해당 연도 논문들 선택
    3. 오른쪽 화살표로 이동
    4. 다른 Period들도 동일하게 반복
    ```
    
    ### 4단계: 분석 실행
    
    **분석 마법사 시작**
    ```
    1. Analysis → Make Analysis
    2. 모든 Period 선택 → Next
    ```
    
    **Step 1-8: 분석 설정**
    - Unit of Analysis: "Author's words + Source's words"
    - Data Reduction: Minimum frequency 2
    - Network Type: "Co-occurrence"
    - Normalization: "Equivalence Index"
    - Clustering: "Simple Centers Algorithm" (Max network size: 50)
    - Document Mapper: "Core Mapper"
    - Performance Measures: G-index, Sum Citations
    - Evolution Map: "Jaccard Index"
    
    **분석 실행**
    ```
    - Finish 클릭
    - 완료까지 대기 (10-30분)
    ```
    
    ### 5단계: 결과 해석
    
    **전략적 다이어그램 4사분면**
    - 우상단: Motor Themes (핵심 주제)
    - 좌상단: Specialized Themes (전문화된 주제)
    - 좌하단: Emerging/Declining Themes (신흥/쇠퇴 주제)
    - 우하단: Basic Themes (기초 주제)
    
    **진화 맵 분석**
    - 노드 크기 = 논문 수
    - 연결선 두께 = Jaccard 유사도
    - 시간에 따른 주제 변화 추적
    
    ### 문제 해결
    - 키워드 정리를 꼼꼼히 (분석품질의 핵심)
    - Period별 최소 50편 이상 권장
    - Java 메모리 부족시 재시작
    - 인코딩 문제시 UTF-8로 변경
    """)

st.markdown("<br><br>", unsafe_allow_html=True)
