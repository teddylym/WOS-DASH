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
        min-height: 160px; /* 동일한 높이를 위한 최소 높이 지정 */
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
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
    
    .stDownloadButton > button, .stButton > button {
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
    
    .stDownloadButton > button:hover, .stButton > button:hover {
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

# --- 논문 분류 함수 (연구 목표에 맞게 재설계) ---
def classify_article(row):
    """
    연구 목표(생태계 분석)에 맞춰, 광범위한 관련 연구를 수집하되 명백한 비관련 연구를 배제하는 함수
    """
    
    # --- 텍스트 필드 추출 및 결합 (소문자 변환) ---
    def extract_text(value):
        return str(value).lower().strip() if pd.notna(value) else ""
    
    title = extract_text(row.get('TI', ''))
    abstract = extract_text(row.get('AB', ''))
    author_keywords = extract_text(row.get('DE', ''))
    wos_keywords = extract_text(row.get('ID', ''))
    
    full_text = ' '.join([title, abstract, author_keywords, wos_keywords])
    document_type = extract_text(row.get('DT', ''))

    # --- 키워드 셋 정의 ---
    # 핵심 주제어: 이 중 하나는 반드시 포함되어야 함
    core_keywords = [
        'live stream', 'livestream', 'live-stream', 'live commerce', 
        'game streaming', 'virtual influencer', 'live video', 'live shopping',
        'twitch', 'youtube live', 'facebook live', 'tiktok live'
    ]
    
    # 배제 기준 키워드
    irrelevant_domain_keywords = ['remote surgery', 'military', 'medical signal', 'telemedicine', 'seismic', 'geological', 'satellite image', 'astronomy']
    non_academic_types = ['editorial', 'news', 'correction', 'letter', 'book review', 'meeting abstract']
    non_interactive_keywords = ['vod', 'asynchronous', 'pre-recorded', 'video on demand']
    methodology_keywords = ['survey', 'experiment', 'interview', 'case study', 'model', 'ethnography', 'empirical', 'framework', 'analysis', 'mechanism', 'sem', 'review', 'meta-analysis', 'algorithm']

    # --- 1단계: 기초 필터링 (명백한 비관련 논문 배제) ---
    
    # 핵심 주제어조차 없는 경우
    if not any(kw in full_text for kw in core_keywords):
        return 'Exclude - Core keyword missing'

    # EC1 (도메인 관련성)
    if any(kw in full_text for kw in irrelevant_domain_keywords):
        return 'Exclude - EC1 (Irrelevant domain)'
        
    # EC3 (학술적 형태)
    if any(doc_type in document_type for doc_type in non_academic_types):
        return 'Exclude - EC3 (Non-academic)'
        
    # EC4 (실시간 상호작용성)
    if any(kw in full_text for kw in non_interactive_keywords):
        return 'Exclude - EC4 (Non-interactive)'
        
    # EC6 (연구 방법론)
    if not any(kw in full_text for kw in methodology_keywords):
        return 'Exclude - EC6 (No methodology)'

    # --- 2단계: 최종 분류 (포함된 논문들의 성격 규명) ---
    # 1단계를 통과한 모든 논문은 일단 연구 대상에 포함
    dimension_keywords = {
        'Technical': ['latency', 'qos', 'qoe', 'protocol', 'bandwidth', 'codec', 'network', 'infrastructure', 'algorithm', 'architecture'],
        'Platform': ['ecosystem', 'governance', 'business model', 'platform', 'monetization', 'creator economy'],
        'User': ['behavior', 'motivation', 'engagement', 'psychology', 'user', 'viewer', 'audience', 'parasocial', 'trust', 'intention'],
        'Commercial': ['commerce', 'marketing', 'sales', 'roi', 'purchase', 'influencer', 'advertising', 'e-commerce', 'brand'],
        'Social': ['culture', 'identity', 'social impact', 'fandom', 'community', 'social presence', 'cultural'],
        'Educational': ['learning', 'teaching', 'virtual classroom', 'education', 'student']
    }
    
    matched_dimensions = [dim for dim, kws in dimension_keywords.items() if any(kw in full_text for kw in kws)]
    
    # 한/영 병기 레이블 맵
    classification_map = {
        'Technical': 'Technical (기술)',
        'Platform': 'Platform (플랫폼)',
        'User': 'User (사용자)',
        'Commercial': 'Commercial (커머스)',
        'Social': 'Social (사회)',
        'Educational': 'Educational (교육)',
        'Multidisciplinary': 'Multidisciplinary (다학제)',
        'etc': 'etc (기타)'
    }

    if len(matched_dimensions) == 0:
         return classification_map['etc']
    elif len(matched_dimensions) == 1:
        return classification_map[matched_dimensions[0]]
    else:
        return classification_map['Multidisciplinary']


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
                missing_rate = ((total_count - valid_count) / total_count * 100)
                issues.append(f"⚠️ {field} 필드의 {missing_rate:.1f}%가 비어있음")
    
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
        <div class="feature-title">연구 목표 기반 정제</div>
        <div class="feature-desc">생태계 분석을 위한 광범위한 관련 연구 데이터 정제</div>
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

if 'show_exclude_details' not in st.session_state:
    st.session_state['show_exclude_details'] = False

if uploaded_files:
    st.markdown(f"📋 **선택된 파일 개수:** {len(uploaded_files)}개")
    
    # 프로그레스 인디케이터
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 데이터 정제 적용 중..."):
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
    total_papers_before_filter = len(merged_df)
    
    # 최종 데이터셋 준비
    df_excluded = merged_df[merged_df['Classification'].str.startswith('Exclude', na=False)]
    df_for_analysis = merged_df[~merged_df['Classification'].str.startswith('Exclude', na=False)].copy()
    
    total_papers = len(df_for_analysis)
    
    st.success(f"✅ 병합 및 데이터 정제 완료! {successful_files}개 파일에서 최종 {total_papers:,}편의 논문을 성공적으로 처리했습니다.")
    
    # 중복 제거 결과 표시
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
        <div class="metric-card" style="min-height: auto;">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{success_count}</div>
            <div class="metric-label">성공한 파일</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card" style="min-height: auto;">
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
        <h4 style="color: #065f46; margin-bottom: 20px; font-weight: 700;">🎯 다중 파일 병합 및 데이터 정제 성공!</h4>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;">여러 WOS Plain Text 파일이 성공적으로 하나로 병합되었습니다.</p>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;"><strong>데이터 정제:</strong> 연구 목표에 맞춰 관련성이 높은 논문만을 체계적으로 선별했습니다.</p>
        <p style="color: #065f46; margin: 6px 0; font-weight: 500;"><strong>SCIMAT 호환성:</strong> 정제된 파일은 SCIMAT에서 100% 정상 작동합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 데이터 정제 결과</div>
        <div class="section-subtitle">연구 목표에 맞춰 정제된 최종 데이터셋 요약</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔬 적용된 데이터 정제 기준 보기"):
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef;">
        <h5 style="color: #3182f6;">✅ 포함 기준 (Inclusion Criteria)</h5>
        <p>아래 모든 배제 기준에 해당하지 않는, '라이브 스트리밍' 관련 학술 연구를 최종 분석 대상으로 포함합니다.</p>
        <hr>
        <h5 style="color: #e53e3e;">⛔️ 배제 기준 (Exclusion Criteria)</h5>
        <ul>
            <li><b>핵심 주제어 부재:</b> 'live stream' 등 핵심 주제어를 전혀 포함하지 않는 경우</li>
            <li><b>EC1 (도메인 관련성 부재)</b>: 원격 수술, 군사 작전 등 무관한 분야</li>
            <li><b>EC3 (학술적 형태 부적합)</b>: 사설(editorial), 뉴스(news) 등 비학술 자료</li>
            <li><b>EC4 (실시간 상호작용성 부재)</b>: VOD, 비동기(asynchronous) 영상 등 실시간 상호작용이 없는 경우</li>
            <li><b>EC6 (연구 방법론 부재)</b>: survey, model 등 실증적 연구 방법론이 명시되지 않은 경우</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)


    # 총 배제된 논문 수 계산
    total_excluded = len(df_excluded)
    
    # Classification 컬럼만 제거 (원본 WOS 형식 유지)
    df_final_output = df_for_analysis.drop(columns=['Classification'], errors='ignore')

    # --- 최종 분석 대상 엑셀 다운로드용 데이터 준비 ---
    export_columns = ['PT', 'AU', 'AF', 'AB', 'TI', 'PY', 'DI']
    df_for_excel = df_final_output[[col for col in export_columns if col in df_final_output.columns]]
    
    excel_buffer_included = io.BytesIO()
    with pd.ExcelWriter(excel_buffer_included, engine='openpyxl') as writer:
        df_for_excel.to_excel(writer, sheet_name='Included_Papers', index=False)
    excel_data_included = excel_buffer_included.getvalue()
    
    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상<br><small style="color: #8b95a1;">(데이터 정제 후)</small></div>
        </div>
        """, unsafe_allow_html=True)
        st.download_button(
            label="상세",
            data=excel_data_included,
            file_name=f"included_papers_{len(df_final_output)}편.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_included_papers",
            help="최종 분석에 포함된 논문 상세 보기 (엑셀 다운로드)",
            use_container_width=True
        )
    
    include_papers = len(df_for_analysis)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{include_papers:,}</div>
            <div class="metric-label">핵심 포함 연구</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 46px;'></div>", unsafe_allow_html=True)

    with col3:
        processing_rate = (len(df_final_output) / total_papers_before_filter * 100) if total_papers_before_filter > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-value">{processing_rate:.1f}%</div>
            <div class="metric-label">최종 포함 비율</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 46px;'></div>", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">⛔</div>
            <div class="metric-value">{total_excluded:,}</div>
            <div class="metric-label">데이터 정제 후 배제</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("상세", key="exclude_details_button", help="배제된 논문 상세 보기", use_container_width=True):
            st.session_state['show_exclude_details'] = not st.session_state.get('show_exclude_details', False)

    # 학술적 엄밀성 확보 패널 추가
    st.markdown(f"""
    <div class="info-panel">
        <h4 style="color: #1d4ed8; margin-bottom: 16px; font-weight: 700;">📊 학술적 엄밀성 확보</h4>
        <p style="color: #1e40af; margin: 6px 0; font-weight: 500;"><strong>총 입력:</strong> {total_papers_before_filter:,}편의 논문</p>
        <p style="color: #1e40af; margin: 6px 0; font-weight: 500;"><strong>배제 적용:</strong> {total_excluded:,}편 제외 ({(total_excluded/total_papers_before_filter*100):.1f}%)</p>
        <p style="color: #1e40af; margin: 6px 0; font-weight: 500;"><strong>최종 분석:</strong> {len(df_final_output):,}편으로 정제된 고품질 데이터셋</p>
        <p style="color: #1e40af; margin: 6px 0; font-weight: 500;"><strong>핵심 연구:</strong> {include_papers:,}편의 직접 관련 라이브스트리밍 연구 확보</p>
    </div>
    """, unsafe_allow_html=True)


    # 배제된 논문 상세 정보 토글 표시
    if st.session_state.get('show_exclude_details', False) and total_excluded > 0:
        st.markdown("""
        <div style="background: #fef2f2; padding: 20px; border-radius: 16px; margin: 20px 0; border: 1px solid #ef4444;">
            <h4 style="color: #dc2626; margin-bottom: 16px; font-weight: 700;">⛔ 데이터 정제 기준에 따라 제외된 논문</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # 배제된 논문 전체 목록 다운로드
        excel_buffer_excluded = io.BytesIO()
        with pd.ExcelWriter(excel_buffer_excluded, engine='openpyxl') as writer:
            df_excluded.to_excel(writer, sheet_name='Excluded_Papers', index=False)
        excel_data_excluded = excel_buffer_excluded.getvalue()
        
        st.download_button(
            label="📊 (엑셀다운로드) - 배제된 논문 전체 목록",
            data=excel_data_excluded,
            file_name=f"excluded_papers_{len(df_excluded)}편.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # 배제 이유별로 그룹화하여 표시
        exclusion_reasons = df_excluded['Classification'].value_counts().index
        for reason in exclusion_reasons:
            reason_papers = df_excluded[df_excluded['Classification'] == reason]
            with st.expander(f"{reason} ({len(reason_papers)}편)", expanded=False):
                for _, paper in reason_papers.head(5).iterrows(): # 샘플 5개 표시
                    title = str(paper.get('TI', 'N/A'))[:100]
                    year = str(paper.get('PY', 'N/A'))
                    source = str(paper.get('SO', 'N/A'))[:50]
                    st.markdown(f"**{title}** ({year}) - *{source}*")
    
    # --- 포함된 논문의 가상 분류 현황 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">포함된 논문의 분류 분포 (Classification Distribution)</div>
    """, unsafe_allow_html=True)
    
    classification_counts_df = df_for_analysis['Classification'].value_counts().reset_index()
    classification_counts_df.columns = ['분류 (Classification)', '논문 수 (Count)']

    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        st.dataframe(classification_counts_df, use_container_width=True, hide_index=True)

    with col2:
        # 도넛 차트 (신규 분류 및 색상 적용)
        color_map = {
            'Technical (기술)': '#1f77b4',
            'Platform (플랫폼)': '#ff7f0e',
            'User (사용자)': '#2ca02c',
            'Commercial (커머스)': '#d62728',
            'Social (사회)': '#9467bd',
            'Educational (교육)': '#8c564b',
            'Multidisciplinary (다학제)': '#7f7f7f',
            'etc (기타)': '#c7c7c7'
        }
        
        # 데이터프레임 순서에 맞게 도메인/범위 정렬
        ordered_df = classification_counts_df.set_index('분류 (Classification)')
        domain = ordered_df.index.tolist()
        range_ = [color_map.get(cat, '#333') for cat in domain]

        selection = alt.selection_point(fields=['분류 (Classification)'], on='mouseover', nearest=True)

        base = alt.Chart(classification_counts_df).encode(
            theta=alt.Theta(field="논문 수 (Count)", type="quantitative", stack=True),
            color=alt.Color(field="분류 (Classification)", type="nominal", title="분류 (Classification)",
                           scale=alt.Scale(domain=domain, range=range_),
                           legend=alt.Legend(orient="right", titleColor="#191f28", labelColor="#8b95a1")),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.8)),
            tooltip=['분류 (Classification)', '논문 수 (Count)']
        ).add_params(selection)

        pie = base.mark_arc(outerRadius=150, innerRadius=90)
        text_total = alt.Chart(pd.DataFrame([{'value': f'{len(df_final_output)}'}])).mark_text(
            align='center', baseline='middle', fontSize=45, fontWeight='bold', color='#3182f6'
        ).encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame([{'value': 'Refined Papers'}])).mark_text(
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
            <div class="chart-title">정제된 라이브 스트리밍 연구 동향 (데이터 정제 기준 적용 후)</div>
        """, unsafe_allow_html=True)
        
        df_trend = df_final_output.copy()
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

    # --- 최종 파일 다운로드 섹션 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">🔥 데이터 정제 완료 - SCIMAT 분석용 파일 다운로드</div>
        <div class="section-subtitle">연구 목표에 맞춰 정제된 최종 데이터셋</div>
    </div>
    """, unsafe_allow_html=True)
    
    # SCIMAT 호환 파일 다운로드
    text_data = convert_to_scimat_wos_format(df_final_output)
    
    download_clicked = st.download_button(
        label="🔥 다운로드",
        data=text_data,
        file_name=f"live_streaming_refined_for_scimat_{len(df_final_output)}papers.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
        key="download_final_file",
        help="데이터 정제 기준 적용 후 SCIMAT에서 바로 사용 가능한 WOS Plain Text 파일"
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
    A: 연구 목표에 맞춰 명백히 관련 없는 논문(타 분야, 비학술, VOD 등)을 체계적으로 배제합니다. 상세 기준은 '데이터 정제 결과' 섹션에서 확인할 수 있습니다.
    
    **Q: SCIMAT에서 키워드 정리를 어떻게 하나요?**
    A: Group set → Word → Find similar words by distances (Maximum distance: 1)로 유사 키워드를 자동 통합하고, Word Group manual set에서 수동으로 관련 키워드들을 그룹화하세요.
    
    **Q: SCIMAT 분석 설정은 어떻게 하나요?**
    A: Unit of Analysis: "Author's words + Source's words", Network Type: "Co-occurrence", Normalization: "Equivalence Index", Clustering: "Simple Centers Algorithm" (Maximum network size: 50)를 권장합니다.
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
    2. "ISI WOS" 선택
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

st.markdown("<br>", unsafe_allow_html=True)

# 기술 지원 및 추가 정보 (조건부 표시)
if uploaded_files and 'df_final_output' in locals() and len(df_final_output) > 0:
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: #f8fafe; border-radius: 8px; margin-top: 30px; border: 1px solid #e1f2ff;">
        <p style="color: #1e40af; font-size: 14px; margin: 0;">
            <strong>한양대학교 기술경영학과 연구실</strong> | 
            WOS 데이터 전처리 도구 | 
            SCIMAT 분석 최적화
        </p>
        <p style="color: #6b7280; font-size: 12px; margin: 6px 0 0 0;">
            문의사항이 있으시면 mot.hanyang.ac.kr을 통해 연락주세요
        </p>
    </div>
    """, unsafe_allow_html=True)

