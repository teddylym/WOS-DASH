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
        font-weight: 600 !important;
        color: #191f28 !important;
        font-family: 'Pretendard', sans-serif !important;
        font-size: 15px !important;
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
                    if df is not None and not df.empty:
                        encoding_used = encoding
                        break
                except Exception:
                    continue
            
            if df is not None and not df.empty:
                all_dataframes.append(df)
                file_status.append({
                    'filename': uploaded_file.name, 'status': 'SUCCESS', 'papers': len(df),
                    'encoding': encoding_used, 'message': f'✅ {len(df)}편 논문 로딩 성공'
                })
            else:
                file_status.append({
                    'filename': uploaded_file.name, 'status': 'ERROR', 'papers': 0,
                    'encoding': 'N/A', 'message': '❌ WOS Plain Text 형식이 아님'
                })
        except Exception as e:
            file_status.append({
                'filename': uploaded_file.name, 'status': 'ERROR', 'papers': 0,
                'encoding': 'N/A', 'message': f'❌ 파일 처리 오류: {str(e)[:50]}'
            })
    
    if all_dataframes:
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        # UT (Unique Article Identifier) 기준 중복 제거
        if 'UT' in merged_df.columns and merged_df['UT'].notna().any():
            before_dedup = len(merged_df)
            # UT가 비어있지 않은 행만 남기고, 중복 제거
            merged_df.dropna(subset=['UT'], inplace=True)
            merged_df.drop_duplicates(subset=['UT'], keep='first', inplace=True)
            duplicates_removed = before_dedup - len(merged_df)
        else: # UT가 없는 경우 제목+저자 기준으로 중복 제거 (더 엄격하게)
            before_dedup = len(merged_df)
            subset_cols = ['TI', 'AU']
            if 'AU' not in merged_df.columns:
                subset_cols = ['TI']
            merged_df.dropna(subset=subset_cols, inplace=True)
            merged_df.drop_duplicates(subset=subset_cols, keep='first', inplace=True)
            duplicates_removed = before_dedup - len(merged_df)
            
        return merged_df, file_status, duplicates_removed
    else:
        return None, file_status, 0

def parse_wos_format(content):
    records = []
    current_record = {}
    current_field = None
    
    for line in content.split('\n'):
        line = line.rstrip()
        if not line: continue
        if line == 'ER':
            if current_record: records.append(current_record)
            current_record, current_field = {}, None
            continue
        if line.startswith(('FN ', 'VR ')): continue
        
        if not line.startswith('   ') and len(line) > 2 and line[2] == ' ':
            current_field = line[:2]
            current_record[current_field] = line[3:].strip()
        elif line.startswith('   ') and current_field in current_record:
            current_record[current_field] += ' ' + line[3:].strip()
    
    if current_record: records.append(current_record)
    return pd.DataFrame(records)

# --- 최종 연구 계획서 기반 분류 함수 ---
def classify_article(row):
    """
    '초안 오퍼스0918.pdf' 연구 계획서의 IC/EC 기준을 반영한 최종 분류 함수.
    이 함수는 논문이 '참여자 상호작용' 또는 '플랫폼 생태계' 연구의 핵심 범주에 속하는지 판별.
    """
    # IC2-A: 사회-기술적 동학 (참여자 상호작용)
    socio_technical_keywords = [
        'user behavior', 'psychology', 'motivation', 'engagement', 'addiction', 'well-being',
        'parasocial', 'social presence', 'trust', 'interactive', 'interaction', 'participation',
        'community', 'identity', 'online culture', 'social capital', 'digital labor', 'fandom',
        'viewer', 'audience', 'streamer', 'creator', 'influencer', 'virtual influencer'
    ]
    
    # IC2-B: 플랫폼 생태계 동학
    platform_ecosystem_keywords = [
        'platform', 'ecosystem', 'business model', 'monetization', 'governance', 'policy',
        'creator economy', 'live commerce', 'live shopping', 'purchase intention', 'e-commerce',
        'marketing', 'advertising', 'revenue', 'donation', 'virtual gift', 'subscription',
        'algorithm', 'recommendation', 'multi-channel network', 'mcn', 'blockchain', 'nft'
    ]
    
    # EC1: 방법론적 부적합성
    methodological_exclusion_indicators = ['extended version', 'preliminary version', 'conference version']

    def extract_text(value):
        return str(value).lower().strip() if pd.notna(value) else ""
    
    title = extract_text(row.get('TI', ''))
    author_keywords = extract_text(row.get('DE', ''))
    keywords_plus = extract_text(row.get('ID', ''))
    abstract = extract_text(row.get('AB', ''))
    document_type = extract_text(row.get('DT', ''))
    
    topic_centrality_text = ' '.join([title, author_keywords, keywords_plus])
    full_text = ' '.join([topic_centrality_text, abstract])
    
    # 단계 1: EC1 - 방법론적 부적합성
    if not any(doc_type in document_type for doc_type in ['article', 'review']):
        return 'EC1 - Methodological Inappropriateness'
    if any(indicator in full_text for indicator in methodological_exclusion_indicators):
        return 'EC1 - Methodological Inappropriateness (Duplicate)'

    # 단계 2: EC2 - 낮은 주제 중심성
    core_topic_keywords = [
        'live stream', 'livestream', 'live-stream', 'live video', 'real-time stream',
        'live commerce', 'live shopping', 'game streaming', 'esports streaming'
    ]
    if not any(kw in topic_centrality_text for kw in core_topic_keywords):
        return 'EC2 - Low Topic Centrality'

    # 단계 3: EC3 - 핵심 현상 분석 부재
    has_socio_technical = any(kw in full_text for kw in socio_technical_keywords)
    has_platform_ecosystem = any(kw in full_text for kw in platform_ecosystem_keywords)
    
    if not (has_socio_technical or has_platform_ecosystem):
        return 'EC3 - Lacks Core Phenomenon Analysis'
            
    # 모든 배제 기준 통과 시, IC2 기준에 따라 세부적으로 포함 분류
    if has_socio_technical and has_platform_ecosystem:
        return 'Include - Participant Interaction & Ecosystem Dynamics'
    elif has_socio_technical:
        return 'Include - Participant Interaction'
    elif has_platform_ecosystem:
        return 'Include - Ecosystem Dynamics'
    
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
        <div class="feature-title">학술적 정제</div>
        <div class="feature-desc">최종 연구계획서 기반 자동 논문 분류</div>
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
            st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다. 파일 형식을 확인해주세요.")
            for status in file_status:
                st.markdown(f"<div class='file-status'><strong>{status['filename']}</strong><br>{status['message']}</div>", unsafe_allow_html=True)
            st.stop()
        
        merged_df['Classification'] = merged_df.apply(classify_article, axis=1)

    total_papers_before_filter = len(merged_df)
    
    df_excluded = merged_df[merged_df['Classification'].str.startswith('EC', na=False)]
    df_for_analysis = merged_df[~merged_df['Classification'].str.startswith('EC', na=False)].copy()
    
    st.success(f"✅ 병합 및 학술적 정제 완료! 최종 {len(df_for_analysis):,}편의 논문을 처리했습니다.")
    
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다.")

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 학술적 정제 결과</div>
        <div class="section-subtitle">최종 연구 계획서의 포함/배제 기준 적용 결과</div>
    </div>
    """, unsafe_allow_html=True)

    total_excluded = len(df_excluded)
    df_final_output = df_for_analysis.drop(columns=['Classification'], errors='ignore')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📋</div><div class="metric-value">{len(df_final_output):,}</div><div class="metric-label">최종 분석 대상<br><small style="color: #8b95a1;">(정제 후)</small></div></div>""", unsafe_allow_html=True)
    with col2:
        include_papers = len(df_for_analysis[df_for_analysis['Classification'].str.contains('Include', na=False)])
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">✅</div><div class="metric-value">{include_papers:,}</div><div class="metric-label">핵심 포함 연구</div></div>""", unsafe_allow_html=True)
    with col3:
        processing_rate = (len(df_final_output) / total_papers_before_filter * 100) if total_papers_before_filter > 0 else 0
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📊</div><div class="metric-value">{processing_rate:.1f}%</div><div class="metric-label">최종 포함 비율</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">⛔</div><div class="metric-value">{total_excluded:,}</div><div class="metric-label">학술적 배제</div></div>""", unsafe_allow_html=True)
        if st.button("배제 논문 상세보기", key="exclude_details_button", use_container_width=True):
            st.session_state['show_exclude_details'] = not st.session_state.get('show_exclude_details', False)

    if st.session_state.get('show_exclude_details', False) and total_excluded > 0:
        st.markdown("---")
        st.markdown(f"#### ⛔ 배제된 논문 상세 ({total_excluded:,}편)")
        
        excluded_excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excluded_excel_buffer, engine='openpyxl') as writer:
            df_excluded[['TI', 'PY', 'SO', 'Classification']].to_excel(writer, sheet_name='Excluded_Papers', index=False)
        
        st.download_button(
            label="📥 배제 논문 전체 목록 엑셀 다운로드", data=excluded_excel_buffer.getvalue(),
            file_name=f"excluded_papers_{total_excluded}편.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True
        )
        
        exclusion_categories = {
            'EC1': '방법론적 부적합성', 'EC2': '낮은 주제 중심성', 'EC3': '핵심 현상 분석 부재',
        }
        for ec_code, description in exclusion_categories.items():
            ec_papers = df_excluded[df_excluded['Classification'].str.contains(ec_code, na=False)]
            if not ec_papers.empty:
                with st.expander(f"{ec_code}: {description} ({len(ec_papers)}편)"):
                    st.dataframe(ec_papers[['TI', 'PY', 'SO']].rename(columns={'TI':'제목', 'PY':'연도', 'SO':'저널'}), hide_index=True)

    # --- 논문 분류 현황 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📊 포함된 논문 분류 현황</div>
        <div class="section-subtitle">최종 분석 대상 논문의 세부 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        classification_counts = df_for_analysis['Classification'].value_counts().reset_index()
        classification_counts.columns = ['분류', '논문 수']
        st.dataframe(classification_counts, use_container_width=True, hide_index=True)

    # --- 최종 파일 다운로드 섹션 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📥 최종 파일 다운로드</div>
        <div class="section-subtitle">학술적 정제가 완료된 SCIMAT 분석용 파일</div>
    </div>
    """, unsafe_allow_html=True)
    
    text_data = convert_to_scimat_wos_format(df_final_output)
    
    st.download_button(
        label="📥 SCIMAT용 WOS 파일 다운로드", data=text_data,
        file_name=f"scimat_ready_wos_{len(df_final_output)}papers.txt", mime="text/plain",
        type="primary", use_container_width=True
    )
