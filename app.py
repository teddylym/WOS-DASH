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
                    
                    if not file_content.strip().startswith('FN '):
                        continue
                        
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
    
    if all_dataframes:
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        
        duplicates_removed = 0
        if 'UT' in merged_df.columns:
            def is_meaningful_ut(value):
                if pd.isna(value): return False
                str_value = str(value).strip()
                if len(str_value) < 10 or str_value.lower() in ['nan', 'none', 'null', '']: return False
                return True
            
            meaningful_ut_mask = merged_df['UT'].apply(is_meaningful_ut)
            rows_with_meaningful_ut = merged_df[meaningful_ut_mask]
            rows_without_meaningful_ut = merged_df[~meaningful_ut_mask]
            
            if not rows_with_meaningful_ut.empty:
                before_dedup = len(rows_with_meaningful_ut)
                deduplicated_meaningful = rows_with_meaningful_ut.drop_duplicates(subset=['UT'], keep='first')
                duplicates_removed = before_dedup - len(deduplicated_meaningful)
                merged_df = pd.concat([deduplicated_meaningful, rows_without_meaningful_ut], ignore_index=True)
        
        if duplicates_removed == 0 and 'TI' in merged_df.columns and 'AU' in merged_df.columns:
            subset_cols = ['TI', 'AU']
            valid_rows_mask = merged_df[subset_cols].notna().all(axis=1)
            valid_rows = merged_df[valid_rows_mask]
            invalid_rows = merged_df[~valid_rows_mask]
            
            if not valid_rows.empty:
                before_dedup = len(valid_rows)
                deduplicated_valid = valid_rows.drop_duplicates(subset=subset_cols, keep='first')
                duplicates_removed = before_dedup - len(deduplicated_valid)
                merged_df = pd.concat([deduplicated_valid, invalid_rows], ignore_index=True)
        
        return merged_df, file_status, duplicates_removed
    else:
        return None, file_status, 0

def parse_wos_format(content):
    lines = content.split('\n')
    records = []
    current_record = {}
    current_field = None
    
    for line in lines:
        line = line.rstrip()
        if not line: continue
        if line == 'ER':
            if current_record:
                records.append(current_record.copy())
            current_record = {}
            current_field = None
            continue
        if line.startswith(('FN ', 'VR ')): continue
            
        if not line.startswith('   ') and ' ' in line:
            parts = line.split(' ', 1)
            if len(parts) == 2:
                current_field, field_value = parts
                current_record[current_field] = field_value.strip()
        elif line.startswith('   ') and current_field in current_record:
            current_record[current_field] += '; ' + line[3:].strip()
    
    if current_record: records.append(current_record)
    return pd.DataFrame(records) if records else None

# --- [교체된 함수] 2단계 필터링 로직 ---
def classify_article(row):
    """2단계 필터링(Two-Step Filtering)을 적용한 논문 분류 함수"""
    
    def extract_text(value):
        return str(value).lower().strip() if pd.notna(value) else ""
    
    title = extract_text(row.get('TI', ''))
    abstract = extract_text(row.get('AB', ''))
    author_keywords = extract_text(row.get('DE', ''))
    wos_keywords = extract_text(row.get('ID', ''))
    
    full_text_for_keywords = ' '.join([title, abstract, author_keywords, wos_keywords])
    document_type = extract_text(row.get('DT', ''))

    core_keywords = [
        'live stream', 'livestream', 'live-streaming', 'twitch', 'live commerce', 'streamer', 
        'real-time interaction', 'youtube live', 'facebook live', 'tiktok live', 
        'periscope', 'bilibili live', 'afreecatv', 'chzzk', 'kick live'
    ]
    
    dimension_keywords = {
        'Technical': ['latency', 'qos', 'quality of service', 'qoe', 'quality of experience', 'protocol', 'bandwidth', 'codec', 'network', 'infrastructure'],
        'Platform': ['ecosystem', 'governance', 'algorithm', 'business model', 'platform'],
        'User': ['behavior', 'motivation', 'engagement', 'psychology', 'user', 'viewer', 'audience', 'parasocial', 'participation'],
        'Commercial': ['commerce', 'marketing', 'sales', 'roi', 'purchase', 'influencer', 'advertising', 'monetization'],
        'Social': ['culture', 'identity', 'social impact', 'fandom', 'community', 'cultural'],
        'Educational': ['learning', 'teaching', 'virtual classroom', 'education']
    }

    irrelevant_domain_keywords = [
        'remote surgery', 'medical signal', 'military', 'satellite image', 'astronomy',
        'seismic', 'geological', 'telemedicine', 'vehicular network', 'drone video'
    ]
    
    non_academic_types = ['editorial', 'news', 'correction', 'short commentary', 'conference abstract', 'letter', 'book review']
    
    non_interactive_keywords = ['vod', 'video on demand', 'asynchronous', 'pre-recorded', 'one-way video']

    methodology_keywords = [
        'survey', 'experiment', 'interview', 'case study', 'qualitative', 'quantitative', 
        'model', 'ethnography', 'empirical', 'framework', 'algorithm', 'protocol', 'analysis',
        'mechanism', 'effect', 'impact', 'influence', 'antecedent', 'consequence', 
        'structural equation model', 'sem', 'review', 'meta-analysis'
    ]

    # --- 1단계 필터링 (기초 선별) ---
    if any(doc_type in document_type for doc_type in non_academic_types):
        return 'Exclude - EC3 (학술적 형태 부적합)'
    if not any(doc_type in document_type for doc_type in ['article', 'review']):
        return 'Exclude - IC2 위배 (학술적 기여 부족)'
    if any(kw in full_text_for_keywords for kw in irrelevant_domain_keywords):
        return 'Exclude - EC1 (도메인 관련성 부재)'
    if any(kw in full_text_for_keywords for kw in non_interactive_keywords):
        return 'Exclude - EC4 (실시간 상호작용성 부재)'
    if not any(kw in full_text_for_keywords for kw in core_keywords):
        return 'Exclude - IC1 위배 (핵심 키워드 부재)'
    abstract_keyword_count = sum(abstract.count(kw) for kw in core_keywords)
    if abstract_keyword_count < 2:
        return 'Exclude - EC2 (부차적 언급)'

    # --- 2단계 필터링 (핵심 연구 속성 검증) ---
    matched_dimensions = []
    for dim, kws in dimension_keywords.items():
        if any(kw in full_text_for_keywords for kw in kws):
            matched_dimensions.append(dim)
    
    if len(matched_dimensions) < 2:
        return 'Exclude - EC5 (연구 차원 단일)'
    if not any(kw in full_text_for_keywords for kw in methodology_keywords):
        return 'Exclude - EC6 (연구 방법론 부재)'

    # --- 최종 분류 ---
    if len(matched_dimensions) == 1:
        return f'Include - {matched_dimensions[0]}'
    elif len(matched_dimensions) > 1:
        return 'Include - Multidisciplinary'
    else:
        return 'Review - Contribution Unclear'

# --- 데이터 품질 진단 함수 ---
def diagnose_merged_quality(df, file_count, duplicates_removed):
    issues = []
    recommendations = []
    
    required_fields = ['TI', 'AU', 'SO', 'PY']
    keyword_fields = ['DE', 'ID']
    
    for field in required_fields:
        if field not in df.columns or df[field].isnull().all():
            issues.append(f"❌ 필수 필드 누락: {field}")
        else:
            missing_rate = df[field].isnull().sum() / len(df) * 100
            if missing_rate > 10:
                issues.append(f"⚠️ {field} 필드의 {missing_rate:.1f}%가 누락됨")
    
    if not any(field in df.columns for field in keyword_fields):
        issues.append("❌ 키워드 필드 없음: DE 또는 ID 필드 필요")
    
    if not issues:
        recommendations.append("✅ 문제점 없음 - 병합 데이터 품질 우수")

    recommendations.append(f"✅ {file_count}개 파일 성공적으로 병합됨")
    if duplicates_removed > 0:
        recommendations.append(f"🔄 중복 논문 {duplicates_removed}편 자동 제거됨")
    
    recommendations.append("✅ WOS Plain Text 형식 - SCIMAT 최적 호환성 확보")
    
    return issues, recommendations


# --- WOS Plain Text 형식 변환 함수 ---
def convert_to_scimat_wos_format(df_to_convert):
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
        <div class="feature-desc">2단계 필터링으로 핵심 연구 선별</div>
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
    label_visibility="collapsed"
)

if 'show_exclude_details' not in st.session_state:
    st.session_state['show_exclude_details'] = False

if uploaded_files:
    st.markdown(f"📋 **선택된 파일 개수:** {len(uploaded_files)}개")
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 학술적 정제 적용 중..."):
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)
        
        if merged_df is None:
            st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다.")
            st.stop()
        
        merged_df['Classification'] = merged_df.apply(classify_article, axis=1)

    successful_files = sum(1 for s in file_status if s['status'] == 'SUCCESS')
    total_papers_before_filter = len(merged_df)
    
    df_excluded = merged_df[merged_df['Classification'].str.startswith('Exclude', na=False)]
    df_included = merged_df[~merged_df['Classification'].str.startswith('Exclude', na=False)].copy()
    df_review = df_included[df_included['Classification'].str.startswith('Review', na=False)]
    
    st.success(f"✅ 다중 파일 병합 및 학술적 정제 성공! {successful_files}개 파일에서 최종 {len(df_included):,}편의 논문을 처리했습니다.")

    # --- 파일별 처리 상태 ---
    with st.expander("파일별 처리 상태 보기"):
        for status in file_status:
            st.markdown(f"<div class='file-status'>{status['filename']}: {status['message']}</div>", unsafe_allow_html=True)

    # --- 데이터 품질 진단 결과 ---
    with st.expander("병합 데이터 품질 진단 및 결과"):
        issues, recommendations = diagnose_merged_quality(merged_df, successful_files, duplicates_removed)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('**발견된 문제점**')
            if issues:
                for issue in issues: st.warning(issue)
            else:
                st.success("문제점 없음 - 병합 데이터 품질 우수")
        with col2:
            st.markdown('**병합 결과**')
            for rec in recommendations: st.info(rec)

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 학술적 정제 결과</div>
    </div>
    """, unsafe_allow_html=True)

    total_excluded = len(df_excluded)
    df_final_output = df_included.drop(columns=['Classification'], errors='ignore')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📋</div><div class="metric-value">{len(df_final_output):,}</div><div class="metric-label">최종 분석 대상</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">✅</div><div class="metric-value">{len(df_included) - len(df_review):,}</div><div class="metric-label">핵심 포함 연구</div></div>""", unsafe_allow_html=True)
    with col3:
        processing_rate = (len(df_included) / total_papers_before_filter * 100) if total_papers_before_filter > 0 else 0
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📊</div><div class="metric-value">{processing_rate:.1f}%</div><div class="metric-label">최종 포함 비율</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon" style="background-color: #ef4444;">⛔</div><div class="metric-value">{total_excluded:,}</div><div class="metric-label">학술적 배제</div>""", unsafe_allow_html=True)
        if st.button("상세보기", key="exclude_details_button"):
            st.session_state['show_exclude_details'] = not st.session_state.get('show_exclude_details', False)

    # --- [추가된 기능] 선정 기준 설명 UI ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">📜 2단계 필터링 선정 기준 (Two-Step Filtering Criteria)</div>
    """, unsafe_allow_html=True)
    ic_col, ec_col = st.columns(2)
    with ic_col:
        st.markdown('<h5 style="color: #10b981;">✅ 포함 기준 (Inclusion Criteria)</h5>', unsafe_allow_html=True)
        st.markdown("""
        - **IC (핵심 연구):** 아래 **모든 배제 기준을 통과**하고, **최소 2개 이상의 연구 차원**에 걸쳐있으며, **명확한 연구 방법론**을 제시하는 깊이 있는 연구.
        """)
    with ec_col:
        st.markdown('<h5 style="color: #ef4444;">⛔️ 배제 기준 (Exclusion Criteria)</h5>', unsafe_allow_html=True)
        st.markdown("""
        **1단계: 기초 선별**
        - **EC1 (도메인 관련성 부재):** 원격 수술, 군사 등 무관 도메인 연구.
        - **EC2 (부차적 언급):** 초록 내 핵심 키워드 2회 미만 언급 연구.
        - **EC3 (학술적 형태 부적합):** 사설, 뉴스 등 비학술 자료.
        - **EC4 (실시간 상호작용성 부재):** VOD, 비동기 영상 등 연구.
        
        **2단계: 핵심 속성 검증**
        - **EC5 (연구 차원 단일):** 1개의 연구 차원에만 국한된 연구.
        - **EC6 (연구 방법론 부재):** 실증적 연구 방법론이 없는 연구.
        """)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 최종 다운로드 ---
    st.markdown("""<div class="section-header"><div class="section-title">📥 최종 파일 다운로드</div></div>""", unsafe_allow_html=True)
    text_data = convert_to_scimat_wos_format(df_final_output)
    st.download_button(label="📥 다운로드", data=text_data, file_name=f"scimat_filtered_{len(df_final_output)}papers.txt", mime="text/plain", use_container_width=True)

# --- 하단 정보 ---
with st.expander("❓ 자주 묻는 질문 (FAQ)", expanded=False):
    st.markdown(""" ... FAQ Content ... """)
with st.expander("📊 WOS → SciMAT 분석 실행 가이드", expanded=False):
    st.markdown(""" ... Guide Content ... """)

st.markdown("<br><br>", unsafe_allow_html=True)
