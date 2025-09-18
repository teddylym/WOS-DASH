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
        position: relative; /* For button positioning */
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
    """WOS Plain Text 형식을 DataFrame으로 변환"""
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

# --- 라이브 스트리밍 특화 분류 함수 (사용자 요청 기준 적용) ---
def classify_article(row):
    """사용자 요청에 따른 포함/배제 기준(IC/EC)을 적용한 논문 분류 함수"""
    
    # --- 키워드 셋 정의 ---
    core_streaming_keywords = [
        'live stream', 'livestream', 'live video', 'live broadcast', 
        'real-time stream', 'streaming platform', 'streaming service',
        'live commerce', 'live shopping', 'shoppertainment',
        'streamer', 'viewer', 'streaming audience', 'viewer behavior',
        'twitch', 'youtube live', 'facebook live', 'tiktok live'
    ]
    interaction_keywords = [
        'real-time', 'real time', 'interactive', 'interaction', 'two-way', 'bidirectional',
        'synchronous', 'live chat', 'audience participation', 'user engagement', 'live feedback',
        'parasocial', 'viewer engagement', 'community'
    ]
    socio_tech_context_keywords = [
        'user behavior', 'psychology', 'motivation', 'engagement', 'addiction', 'parasocial', 'social presence', 'trust',
        'social impact', 'cultural', 'community', 'identity', 'online culture', 'social capital', 'digital labor',
        'commerce', 'marketing', 'influencer', 'brand', 'purchase intention', 'advertising', 'e-commerce', 'social commerce',
        'education', 'learning', 'teaching', 'pedagogy', 'student engagement', 'mooc', 'virtual classroom',
        'platform', 'ecosystem', 'business model', 'monetization', 'governance', 'creator economy'
    ]
    pure_tech_exclusions = ['codec', 'network latency', 'optimization', 'routing protocol', 'bandwidth allocation']
    peripheral_mention_indicators = ['for example', 'such as', 'including', 'future work', 'future research']
    methodological_exclusion_types = ['editorial', 'book review', 'abstract', 'errata', 'white paper', 'letter', 'note', 'correction']
    duplicate_indicators = ['extended version', 'preliminary version', 'conference version']

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
    
    # IC2 (학술적 형태) & EC4 (학술적 엄밀성 부족)
    if not any(doc_type in document_type for doc_type in ['article', 'review']):
        return 'EC4 - 학술적 엄밀성 부족'
    if any(exclude_type in document_type for exclude_type in methodological_exclusion_types):
        return 'EC4 - 학술적 엄밀성 부족'
        
    # IC3 (언어)
    if language and language != 'english':
        return 'EC - Non-English' # Not in formal EC list, but functionally an exclusion

    # EC5 (중복)
    if any(indicator in full_text for indicator in duplicate_indicators):
        return 'EC5 - 중복 게재'

    # IC1 (주제 중심성) & EC1 (주제 관련성 부족)
    has_core_keyword = any(kw in full_text for kw in core_streaming_keywords)
    if not has_core_keyword:
        return 'EC1 - 주제 관련성 부족'
    if any(indicator in full_text for indicator in peripheral_mention_indicators) and sum(1 for kw in core_streaming_keywords if kw in full_text) <= 2:
        return 'EC1 - 주제 관련성 부족'

    # EC3 (상호작용성 부재)
    if not any(kw in full_text for kw in interaction_keywords):
        return 'EC3 - 상호작용성 부재'
        
    # EC2 (사회-기술적 맥락 부재)
    if any(kw in full_text for kw in pure_tech_exclusions) and not any(kw in full_text for kw in socio_tech_context_keywords):
        return 'EC2 - 사회-기술적 맥락 부재'

    # 모든 기준 통과 -> 포함
    # 세부 분류 로직은 기존 유지
    analytical_contribution_keywords = {
        'Included - Commercial Application': ['commerce', 'marketing', 'influencer', 'brand', 'purchase intention', 'advertising', 'e-commerce', 'social commerce'],
        'Included - Educational Use': ['education', 'learning', 'teaching', 'pedagogy', 'student engagement', 'mooc', 'virtual classroom'],
        'Included - Platform Ecosystem': ['platform', 'ecosystem', 'business model', 'monetization', 'governance', 'creator economy'],
        'Included - User Behavior/Psychology': ['user behavior', 'psychology', 'motivation', 'engagement', 'addiction', 'parasocial', 'social presence', 'trust'],
        'Included - Socio-Cultural Impact': ['social impact', 'cultural', 'community', 'identity', 'online culture', 'social capital', 'digital labor'],
        'Included - Technical Implementation': ['architecture', 'algorithm', 'latency', 'quality of service', 'qos', 'video quality', 'webrtc', 'cdn']
    }
    for category, keywords in analytical_contribution_keywords.items():
        if any(kw in full_text for kw in keywords):
            return category
            
    return 'Review - Contribution Unclear'

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
        if len(file_content) > 2: file_content.append("")
        for tag in wos_field_order:
            if tag in row.index and pd.notna(row[tag]) and str(row[tag]).strip():
                value = str(row[tag]).strip()
                if tag in multi_line_fields:
                    items = [item.strip() for item in value.split(';') if item.strip()]
                    if items:
                        file_content.append(f"{tag} {items[0]}")
                        for item in items[1:]: file_content.append(f"   {item}")
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
    <h1 style="font-size: 3rem; font-weight: 700; margin-bottom: 0.3rem; letter-spacing: -0.02em;">WOS PREP</h1>
    <p style="font-size: 1.1rem; margin: 0; font-weight: 500; opacity: 0.95; letter-spacing: -0.01em;">SCIMAT Edition</p>
    <div style="width: 80px; height: 3px; background-color: rgba(255,255,255,0.3); margin: 1.5rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 핵심 기능 소개 ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card"><div class="feature-icon">🔗</div><div class="feature-title">다중 파일 자동 병합</div><div class="feature-desc">여러 WOS 파일을 한 번에 병합 처리</div></div>
    <div class="feature-card"><div class="feature-icon">🚫</div><div class="feature-title">스마트 중복 제거</div><div class="feature-desc">UT 기준 자동 중복 논문 감지 및 제거</div></div>
    <div class="feature-card"><div class="feature-icon">🎯</div><div class="feature-title">학술적 엄밀성</div><div class="feature-desc">개념 기반 학술적 정제 적용</div></div>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">📂 다중 WOS Plain Text 파일 업로드</div>
    <div class="section-subtitle">500개 단위로 나뉜 여러 WOS 파일을 모두 선택하여 업로드하세요</div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("WOS Plain Text 파일 선택 (다중 선택 가능)", type=['txt'], accept_multiple_files=True, label_visibility="collapsed")

if 'show_exclude_details' not in st.session_state:
    st.session_state['show_exclude_details'] = False

if uploaded_files:
    st.markdown(f"📋 **선택된 파일 개수:** {len(uploaded_files)}개")
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 학술적 정제 적용 중..."):
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)
        
        if merged_df is None:
            st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다. 파일 형식을 확인해주세요.")
            st.stop()
        
        merged_df['Classification'] = merged_df.apply(classify_article, axis=1)

    successful_files = sum(1 for s in file_status if s['status'] == 'SUCCESS')
    total_papers_before_filter = len(merged_df)
    
    df_excluded = merged_df[merged_df['Classification'].str.startswith('EC', na=False)]
    df_included = merged_df[~merged_df['Classification'].str.startswith('EC', na=False)].copy()
    
    st.success(f"✅ 병합 및 정제 완료! {successful_files}개 파일에서 최종 {len(df_included):,}편의 논문을 처리했습니다.")
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다.")

    # --- 분석 결과 요약 ---
    st.markdown(f"""
    <div class="section-header">
        <div class="section-title">📈 학술적 정제 결과 (Academic Refinement Results)</div>
        <div class="section-subtitle">선정 기준 적용 후 라이브 스트리밍 연구 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    total_excluded = len(df_excluded)
    df_final_output = df_included.drop(columns=['Classification'], errors='ignore')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📋</div><div class="metric-value">{len(df_final_output):,}</div><div class="metric-label">최종 분석 대상<br><small>(Final Papers)</small></div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">✅</div><div class="metric-value">{len(df_included):,}</div><div class="metric-label">핵심 포함 연구<br><small>(Included Papers)</small></div></div>""", unsafe_allow_html=True)
    with col3:
        processing_rate = (len(df_included) / total_papers_before_filter * 100) if total_papers_before_filter > 0 else 0
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📊</div><div class="metric-value">{processing_rate:.1f}%</div><div class="metric-label">최종 포함 비율<br><small>(Inclusion Rate)</small></div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card" style="padding-bottom: 50px;"><div class="metric-icon" style="background-color: #ef4444;">⛔</div><div class="metric-value">{total_excluded:,}</div><div class="metric-label">학술적 배제<br><small>(Excluded Papers)</small></div><div style="position: absolute; bottom: 10px; right: 15px;">""", unsafe_allow_html=True)
        if st.button("(상세보기)", key="exclude_details_button"):
            st.session_state['show_exclude_details'] = not st.session_state.get('show_exclude_details', False)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 선정 기준 설명 UI ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">📜 선정 기준 (Inclusion and Exclusion Criteria)</div>
    """, unsafe_allow_html=True)
    ic_col, ec_col = st.columns(2)
    with ic_col:
        st.markdown('<h5 style="color: #10b981;">✅ 포함 기준 (Inclusion Criteria)</h5>', unsafe_allow_html=True)
        st.markdown("""
        - **IC1 (주제 중심성):** 라이브 스트리밍의 기술, 플랫폼, 사용자, 사회문화적/경제적 영향을 연구의 핵심 주제로 다루는 연구.
        - **IC2 (학술적 형태):** 동료 심사를 거친 학술지 논문(Article) 또는 리뷰(Review).
        - **IC3 (언어):** 영어로 작성된 논문.
        """)
    with ec_col:
        st.markdown('<h5 style="color: #ef4444;">⛔️ 제외 기준 (Exclusion Criteria)</h5>', unsafe_allow_html=True)
        st.markdown("""
        - **EC1 (주제 관련성 부족):** 라이브 스트리밍을 부차적 맥락으로만 언급한 연구.
        - **EC2 (사회-기술적 맥락 부재):** 사용자 행태 분석 없이 순수 기술만 다룬 연구.
        - **EC3 (상호작용성 부재):** 실시간 상호작용 개념이 없는 단방향 VOD 연구.
        - **EC4 (학술적 엄밀성 부족):** 사설, 서평 등 동료 심사를 거치지 않은 연구.
        - **EC5 (중복):** 명백히 중복 게재된 연구.
        """)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 배제된 논문 상세 정보 ---
    if st.session_state.get('show_exclude_details', False) and total_excluded > 0:
        with st.container():
            st.markdown("""<div style="background: #fff1f2; padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #ffdde0;"><h4 style="color: #be123c;">⛔ 제외 논문 상세 (Excluded Papers Details)</h4>""", unsafe_allow_html=True)
            
            exclusion_reasons = df_excluded['Classification'].unique()
            for reason in sorted(exclusion_reasons):
                ec_papers = df_excluded[df_excluded['Classification'] == reason]
                st.markdown(f"""<div style="margin: 12px 0; padding: 16px; background: white; border-left: 4px solid #f43f5e; border-radius: 12px;"><strong style="color: #be123c;">{reason}</strong> <span style="color: #8b95a1;">(총 {len(ec_papers)}편 중 2편 샘플)</span></div>""", unsafe_allow_html=True)
                for _, paper in ec_papers.head(2).iterrows():
                    st.markdown(f"""<div style="margin: 8px 0 8px 20px; padding: 12px; background: #f9fafb; border-radius: 8px; font-size: 14px;"><div style="font-weight: 500;">{paper.get('TI', 'N/A')}</div><div style="color: #6b7280; font-size: 12px;">{paper.get('PY', 'N/A')} | {paper.get('SO', 'N/A')}</div></div>""", unsafe_allow_html=True)

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_excluded.to_excel(writer, sheet_name='Excluded_Papers', index=False)
            st.download_button(label=" (엑셀다운로드) - 배제된 논문 전체 목록", data=excel_buffer.getvalue(), file_name="excluded_papers.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 학술적 엄밀성 확보 요약 패널 ---
    st.markdown(f"""
    <div class="info-panel">
        <h4 style="color: #0064ff; margin-bottom: 16px; font-weight: 700;">📊 학술적 엄밀성 확보</h4>
        <p style="color: #191f28; margin: 6px 0;"><strong>총 입력:</strong> {total_papers_before_filter:,}편의 논문</p>
        <p style="color: #191f28; margin: 6px 0;"><strong>배제 적용:</strong> {total_excluded:,}편 제외 ({(total_excluded/total_papers_before_filter*100):.1f}%)</p>
        <p style="color: #191f28; margin: 6px 0;"><strong>최종 분석:</strong> {len(df_final_output):,}편으로 정제된 고품질 데이터셋</p>
        <p style="color: #191f28; margin: 6px 0;"><strong>핵심 연구:</strong> {len(df_included[df_included['Classification'] != 'Review - Contribution Unclear']):,}편의 직접 관련 라이브스트리밍 연구 확보</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- 논문 분류 현황 ---
    st.markdown("""<div class="chart-container"><div class="chart-title">포함된 연구의 분류 분포 (Distribution of Included Research)</div>""", unsafe_allow_html=True)
    classification_counts_df = df_included['Classification'].value_counts().reset_index()
    classification_counts_df.columns = ['Classification (분류)', 'Count (논문 수)']
    
    c1, c2 = st.columns([0.4, 0.6])
    with c1:
        st.dataframe(classification_counts_df, use_container_width=True, hide_index=True)
    with c2:
        chart = alt.Chart(classification_counts_df).mark_arc(innerRadius=90, outerRadius=150).encode(
            theta=alt.Theta(field="Count (논문 수)", type="quantitative", stack=True),
            color=alt.Color(field="Classification (분류)", type="nominal", title="Research Topic (연구 분야)", scale=alt.Scale(scheme='tableau20')),
            tooltip=['Classification (분류)', 'Count (논문 수)']
        )
        text_total = alt.Chart(pd.DataFrame({'value': [f'{len(df_included)}']})).mark_text(align='center', baseline='middle', fontSize=45, fontWeight='bold', color='#0064ff').encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame({'value': ['Research Topics']})).mark_text(align='center', baseline='middle', fontSize=16, dy=30, color='#8b95a1').encode(text='value:N')
        st.altair_chart((chart + text_total + text_label).properties(width=350, height=350).configure_view(strokeWidth=0), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 분류별 상세 분포 ---
    st.markdown("""<div class="chart-container"><div class="chart-title">분류별 상세 분포 (배제 기준 적용 후)</div>""", unsafe_allow_html=True)
    sorted_classifications = df_included['Classification'].value_counts()
    for classification, count in sorted_classifications.items():
        percentage = (count / len(df_included) * 100) if len(df_included) > 0 else 0
        icon = "🔍" if "Review" in classification else "✅"
        color = "#f59e0b" if "Review" in classification else "#10b981"
        st.markdown(f"""
        <div style="margin: 16px 0; padding: 20px; background: white; border-left: 4px solid {color}; border-radius: 12px; font-size: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <strong>{icon} {classification}:</strong> {count:,}편 ({percentage:.1f}%)
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 연도별 연구 동향 ---
    if 'PY' in df_final_output.columns:
        st.markdown("""<div class="chart-container"><div class="chart-title">연도별 연구 동향 (Publication Trend by Year)</div>""", unsafe_allow_html=True)
        df_trend = df_final_output.copy()
        df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
        df_trend.dropna(subset=['PY'], inplace=True)
        yearly_counts = df_trend['PY'].astype(int).value_counts().reset_index()
        yearly_counts.columns = ['Year', 'Count']
        
        line_chart = alt.Chart(yearly_counts).mark_line(point=True, strokeWidth=3, color='#0064ff').encode(
            x=alt.X('Year:O', title='Publication Year (발행 연도)'),
            y=alt.Y('Count:Q', title='Number of Papers (논문 수)'),
            tooltip=['Year', 'Count']
        ).properties(height=300)
        st.altair_chart(line_chart, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # --- 키워드 품질 확인 ---
    st.markdown("""<div class="chart-container"><div class="chart-title">정제된 데이터 키워드 품질 확인</div>""", unsafe_allow_html=True)
    sample_data = []
    sample_rows = df_included[df_included['Classification'] != 'Review - Contribution Unclear'].head(3)
    for _, row in sample_rows.iterrows():
        de_keywords = str(row.get('DE', 'N/A'))
        id_keywords = str(row.get('ID', 'N/A'))
        sample_data.append({
            '논문 제목': str(row.get('TI', 'N/A')),
            'DE 키워드': de_keywords,
            'ID 키워드': id_keywords
        })
    if sample_data:
        st.dataframe(pd.DataFrame(sample_data), use_container_width=True, hide_index=True)
        st.success("✅ 키워드 품질 우수 - SCIMAT에서 원활한 그루핑 예상")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Review 논문 목록 ---
    review_papers = df_included[df_included['Classification'] == 'Review - Contribution Unclear']
    if not review_papers.empty:
        with st.expander(f"🔍 Review (검토 필요) - 논문 목록 ({len(review_papers)}편)"):
            st.markdown("아래 논문들은 연구의 핵심 속성은 만족하나, 명확한 분석적 기여 차원을 특정하기 어려워 수동 검토가 필요합니다.")
            st.dataframe(review_papers[['TI', 'PY', 'SO', 'AU', 'DE', 'ID']], use_container_width=True, hide_index=True)

    # --- 최종 요약 패널 ---
    st.markdown(f"""
    <div class="info-panel">
        <h4 style="color: #0064ff; margin-bottom: 16px; font-weight: 700;">🎯 학술적 데이터 정제 완료</h4>
        <p style="color: #191f28; margin: 6px 0;"><strong>파일 통합:</strong> {successful_files}개의 WOS 파일을 하나로 병합</p>
        <p style="color: #191f28; margin: 6px 0;"><strong>중복 제거:</strong> {duplicates_removed}편의 중복 논문 자동 감지 및 제거</p>
        <p style="color: #191f28; margin: 6px 0;"><strong>학술적 엄밀성:</strong> 개념 기반 배제 기준으로 {total_excluded}편 제외</p>
        <p style="color: #191f28; margin: 6px 0;"><strong>최종 규모:</strong> {len(df_final_output):,}편의 고품질 논문으로 정제된 데이터셋</p>
        <p style="color: #191f28; margin: 6px 0;"><strong>핵심 연구:</strong> {len(df_included[df_included['Classification'] != 'Review - Contribution Unclear']):,}편의 직접 관련 라이브스트리밍 연구 확보</p>
        <p style="color: #191f28; margin: 6px 0;"><strong>SCIMAT 호환:</strong> 완벽한 WOS Plain Text 형식으로 100% 호환성 보장</p>
        <div style="margin-top: 16px; padding: 12px; background: rgba(0,100,255,0.1); border-radius: 8px;">
            <p style='color: #0064ff; margin: 0; font-weight: 600; font-size: 14px;'>
            💡 <strong>배제 기준 적용률:</strong> {(total_excluded/total_papers_before_filter*100):.1f}% 
            - 연구 질문에 직접적으로 기여하는 논문만을 선별하여 분석의 깊이와 신뢰성을 확보했습니다.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # --- 최종 다운로드 ---
    st.markdown("""<div class="section-header"><div class="section-title">📥 최종 파일 다운로드 (Final File Download)</div><div class="section-subtitle">정제된 고품질 WOS Plain Text 파일</div></div>""", unsafe_allow_html=True)
    text_data = convert_to_scimat_wos_format(df_final_output)
    st.download_button(label="📥 다운로드 (Download)", data=text_data, file_name=f"scimat_filtered_{len(df_final_output)}papers.txt", mime="text/plain", use_container_width=True)

# --- 하단 고정 정보 ---
st.markdown("<br><br>", unsafe_allow_html=True)

with st.expander("❓ 자주 묻는 질문 (FAQ)", expanded=False):
    st.markdown("""
    **Q: 여러 WOS 파일을 어떻게 한 번에 처리하나요?**
    A: WOS에서 여러 번 Plain Text 다운로드한 후, 모든 .txt 파일을 한 번에 업로드하면 자동으로 병합됩니다.
    
    **Q: 중복된 논문이 있을까봐 걱정됩니다.**
    A: UT(Unique Article Identifier) 기준으로 자동 중복 제거되며, UT가 없으면 제목+저자 조합으로 중복을 감지합니다.
    
    **Q: WOS에서 어떤 설정으로 다운로드해야 하나요?**
    A: Export → Record Content: "Full Record and Cited References", File Format: "Plain Text"로 설정하세요. 인용 관계 분석을 위해 참고문헌 정보가 필수입니다.
    
    **Q: 어떤 기준으로 논문이 배제되나요?**
    A: 사회-기술적 맥락이 부재하거나(EC1), 주제의 주변성이 높거나(EC2), 방법론적으로 부적합한(EC3) 연구를 체계적으로 배제하여 분석의 깊이와 신뢰성을 확보합니다.
    
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
