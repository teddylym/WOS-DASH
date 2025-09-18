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
    """다중 WOS Plain Text 파일을 로딩하고 병합합니다."""
    all_dataframes = []
    file_status = []
    
    for uploaded_file in uploaded_files:
        try:
            file_bytes = uploaded_file.getvalue()
            encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1']
            df = None
            encoding_used = None
            
            for encoding in encodings_to_try:
                try:
                    file_content = file_bytes.decode(encoding)
                    if file_content.strip().startswith('FN '):
                        df = parse_wos_format(file_content)
                        if df is not None and not df.empty:
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
                    'filename': uploaded_file.name, 'status': 'ERROR', 'papers': 0, 'encoding': 'N/A',
                    'message': '❌ WOS Plain Text 형식이 아니거나 내용이 없습니다.'
                })
        except Exception as e:
            file_status.append({
                'filename': uploaded_file.name, 'status': 'ERROR', 'papers': 0, 'encoding': 'N/A',
                'message': f'❌ 파일 처리 오류: {e}'
            })
    
    if all_dataframes:
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        original_count = len(merged_df)
        
        duplicates_removed = 0
        if 'UT' in merged_df.columns:
            ut_not_na = merged_df[merged_df['UT'].notna()]
            ut_is_na = merged_df[merged_df['UT'].isna()]
            
            ut_not_na_dedup = ut_not_na.drop_duplicates(subset=['UT'], keep='first')
            
            merged_df = pd.concat([ut_not_na_dedup, ut_is_na], ignore_index=True)
            duplicates_removed = original_count - len(merged_df)
            
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
            
        if line == 'ER':
            if current_record:
                records.append(current_record.copy())
                current_record = {}
                current_field = None
            continue
            
        if line.startswith(('FN ', 'VR ')):
            continue
            
        if not line.startswith('   ') and ' ' in line:
            parts = line.split(' ', 1)
            if len(parts) == 2 and len(parts[0]) == 2 and parts[0].isalpha():
                field_tag, field_value = parts
                current_field = field_tag
                if field_tag in current_record:
                     current_record[field_tag] += '; ' + field_value.strip()
                else:
                    current_record[field_tag] = field_value.strip()
        
        elif line.startswith('   ') and current_field and current_field in current_record:
            continuation_value = line[3:].strip()
            if continuation_value:
                current_record[current_field] += '; ' + continuation_value
    
    if current_record:
        records.append(current_record)
    
    if not records:
        return None
        
    return pd.DataFrame(records)

# --- 라이브 스트리밍 특화 분류 함수 (새로운 IC/EC 기준 적용) ---
def classify_article(row):
    """새로운 IC/EC 기준에 따라 논문을 분류합니다."""
    title = str(row.get('TI', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    doc_type = str(row.get('DT', '')).lower()
    
    full_text = ' '.join([title, abstract, author_keywords, keywords_plus])

    # EC4: 학술적 엄밀성 부족 (가장 먼저 필터링)
    non_academic_types = ['editorial material', 'letter', 'meeting abstract', 'correction', 'book review', 'note']
    if any(doc_type_kw in doc_type for doc_type_kw in non_academic_types):
         return 'EC4: 학술적 엄밀성 부족 (Lack of Academic Rigor)'

    # IC2 (학술적 형태) - article, review가 아닌 경우 EC4로 처리
    if 'article' not in doc_type and 'review' not in doc_type:
        return 'EC4: 학술적 엄밀성 부족 (Lack of Academic Rigor)'

    # EC1: 주제 관련성 부족 (부차적 언급)
    core_keywords = ['live stream', 'livestream', 'live commerce', 'game streaming', 'virtual influencer', 'streamer', 'twitch', 'youtube live']
    if not any(kw in full_text for kw in core_keywords):
        return 'EC1: 주제 관련성 부족 (Topic Irrelevance)'

    # EC2: 사회-기술적 맥락 부재 (순수 기술)
    pure_tech_keywords = ['protocol', 'codec', 'latency optimization', 'bandwidth allocation', 'network topology', 'signal processing', 'video compression', 'qos']
    socio_tech_keywords = ['user', 'behavior', 'social', 'economic', 'community', 'motivation', 'engagement', 'psychology', 'culture']
    if any(kw in full_text for kw in pure_tech_keywords) and not any(kw in full_text for kw in socio_tech_keywords):
        return 'EC2: 사회-기술적 맥락 부재 (Lack of Socio-Technical Context)'

    # EC3: 상호작용성 부재 (단방향 방송)
    oneway_keywords = ['vod', 'video on demand', 'traditional broadcast', 'non-interactive']
    interactive_keywords = ['interactive', 'chat', 'real-time', 'community', 'engagement', 'synchronous', 'parasocial']
    if any(kw in full_text for kw in oneway_keywords) and not any(kw in full_text for kw in interactive_keywords):
        return 'EC3: 상호작용성 부재 (Lack of Interactivity)'
    
    return '포함 (Included)'

# --- 데이터 품질 진단 함수 ---
def diagnose_merged_quality(df, file_count, duplicates_removed):
    """병합된 WOS 데이터의 품질 진단"""
    issues = []
    recommendations = []
    
    required_fields = ['TI', 'AU', 'SO', 'PY']
    keyword_fields = ['DE', 'ID']
    
    for field in required_fields:
        if field not in df.columns or (not df.empty and df[field].isnull().sum() > len(df) * 0.1):
            missing_rate = df[field].isnull().sum() / len(df) * 100 if field in df.columns and not df.empty else 100
            issues.append(f"⚠️ {field} 필드의 {missing_rate:.1f}%가 누락됨")
    
    has_keywords = any(field in df.columns for field in keyword_fields)
    if not has_keywords:
        issues.append("❌ 키워드 필드 없음 (DE 또는 ID)")
    
    recommendations.append(f"✅ {file_count}개 파일 성공적으로 병합됨")
    if duplicates_removed > 0:
        recommendations.append(f"🔄 중복 논문 {duplicates_removed}편 자동 제거됨")
    
    return issues, recommendations

# --- WOS Plain Text 형식 변환 함수 (SciMAT 호환) ---
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

def to_excel(df):
    """DataFrame을 Excel 파일 바이트로 변환합니다."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

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

if 'show_exclude_details' not in st.session_state:
    st.session_state.show_exclude_details = False

if uploaded_files:
    st.markdown(f"📋 **선택된 파일 개수:** {len(uploaded_files)}개")
    
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 학술적 정제 적용 중..."):
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)
        
        if merged_df is None:
            st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다. 파일 형식을 확인해주세요.")
            st.stop()
        
        # 논문 분류 수행
        merged_df['Classification'] = merged_df.apply(classify_article, axis=1)

    successful_files = len([s for s in file_status if s['status'] == 'SUCCESS'])
    total_papers_before_filter = len(merged_df)
    
    df_included = merged_df[merged_df['Classification'] == '포함 (Included)'].copy()
    df_excluded = merged_df[merged_df['Classification'] != '포함 (Included)'].copy()
    
    st.success(f"✅ 병합 및 학술적 정제 완료! 최종 {len(df_included):,}편의 논문을 분석 대상으로 선정했습니다.")
    
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다.")

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 학술적 정제 결과</div>
        <div class="section-subtitle">학술적 정제 기준 적용 후 라이브 스트리밍 연구 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total_papers_before_filter:,}</div><div class="metric-label">총 고유 논문</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10b981;">{len(df_included):,}</div><div class="metric-label">포함 대상 논문</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#ef4444;">{len(df_excluded):,}</div><div class="metric-label">제외 대상 논문</div></div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ 포함/제외(IC/EC) 기준 상세 설명", expanded=True):
        st.markdown("""
        #### 포함 기준 (Inclusion Criteria)
        - **IC1 (주제 중심성):** 라이브 스트리밍의 기술, 플랫폼, 사용자, 사회문화적/경제적 영향을 연구의 핵심 주제(primary subject)로 다루는 연구.
        - **IC2 (학술적 형태):** 동료 심사(peer-review)를 거친 학술지 논문(Article) 또는 리뷰(Review).
        #### 제외 기준 (Exclusion Criteria)
        - **EC1 (주제 관련성 부족):** 라이브 스트리밍을 단순히 데이터 수집 도구, 기술적 예시, 또는 부차적 맥락으로만 언급한 연구.
        - **EC2 (사회-기술적 맥락 부재):** 사회적, 경제적, 사용자 행태적 함의에 대한 분석 없이, 순수하게 기술 프로토콜의 공학적 측면만 다룬 연구.
        - **EC3 (상호작용성 부재):** 라이브 스트리밍의 핵심 특징인 실시간 상호작용 개념이 결여된 단방향 방송(VOD)에 관한 연구.
        - **EC4 (학술적 엄밀성 부족):** 동료 심사를 거치지 않은 사설, 서평, 콘퍼런스 초록 등.
        """)

    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">분류 결과 분포 (Classification Distribution)</div>
    """, unsafe_allow_html=True)
    classification_counts = merged_df['Classification'].value_counts().reset_index()
    classification_counts.columns = ['Classification', 'Count']
    
    chart = alt.Chart(classification_counts).mark_bar().encode(
        x=alt.X('Count:Q', title='논문 수 (Number of Papers)'),
        y=alt.Y('Classification:N', title='분류 (Classification)', sort='-x'),
        color=alt.condition(
            alt.datum.Classification == '포함 (Included)',
            alt.value('#10b981'),
            alt.value('#ef4444')
        ),
        tooltip=['Classification', 'Count']
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 제외 논문 상세 다운로드 ---
    if not df_excluded.empty:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">❌ 제외 대상 논문 상세 (Excluded Papers Details)</div>
        """, unsafe_allow_html=True)
        st.warning(f"총 {len(df_excluded):,}편의 논문이 기준에 따라 제외되었습니다. 상세 내용은 아래 엑셀 파일로 검토할 수 있습니다.")

        excel_data = to_excel(df_excluded[['TI', 'AU', 'PY', 'SO', 'Classification']].rename(columns={
            'TI': '제목 (Title)', 'AU': '저자 (Authors)', 'PY': '연도 (Year)', 
            'SO': '저널 (Journal)', 'Classification': '제외사유 (Exclusion Reason)'
        }))
        st.download_button(
           label=f"📄 제외 논문 전체 목록 엑셀 다운로드 ({len(df_excluded):,}편)",
           data=excel_data,
           file_name=f"Excluded_{len(df_excluded)}_papers.xlsx",
           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
           use_container_width=True,
           type="secondary",
           key="download_excel_button"
        )
        st.markdown("</div>", unsafe_allow_html=True)


    # --- 최종 파일 다운로드 섹션 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📥 최종 파일 다운로드</div>
        <div class="section-subtitle">SCIMAT 분석용으로 정제된 최종 WOS Plain Text 파일</div>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_included.empty:
        df_included_for_download = df_included.drop(columns=['Classification'])
        text_data = convert_to_scimat_wos_format(df_included_for_download)
        st.download_button(
            label=f"📥 SCIMAT용 TXT 다운로드 ({len(df_included):,}편)",
            data=text_data,
            file_name=f"SCIMAT_Included_{len(df_included)}_papers.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_final_file"
        )

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # --- 원본 UI 요소들 (FAQ 및 가이드) ---
    with st.expander("❓ 자주 묻는 질문 (FAQ)", expanded=False):
        st.markdown("""
        **Q: 여러 WOS 파일을 어떻게 한 번에 처리하나요?**
        A: WOS에서 여러 번 Plain Text 다운로드한 후, 모든 .txt 파일을 한 번에 업로드하면 자동으로 병합됩니다.
        
        **Q: 중복된 논문이 있을까봐 걱정됩니다.**
        A: UT(Unique Article Identifier) 기준으로 자동 중복 제거됩니다.
        
        **Q: WOS에서 어떤 설정으로 다운로드해야 하나요?**
        A: Export → Record Content: "Full Record and Cited References", File Format: "Plain Text"로 설정하세요.
        
        **Q: 어떤 기준으로 논문이 배제되나요?**
        A: IC/EC 기준에 따라 주제 관련성, 사회-기술적 맥락, 상호작용성, 학술적 형태 등을 종합적으로 판단하여 정제합니다.
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

