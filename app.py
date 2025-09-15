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
    all_dataframes = []
    file_status = []
    
    for uploaded_file in uploaded_files:
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
                file_status.append({'filename': uploaded_file.name, 'status': 'SUCCESS', 'papers': len(df), 'encoding': encoding_used, 'message': f'✅ {len(df)}편 논문 로딩 성공'})
            else:
                file_status.append({'filename': uploaded_file.name, 'status': 'ERROR', 'papers': 0, 'encoding': 'N/A', 'message': '❌ WOS Plain Text 형식이 아님'})
        except Exception as e:
            file_status.append({'filename': uploaded_file.name, 'status': 'ERROR', 'papers': 0, 'encoding': 'N/A', 'message': f'❌ 파일 처리 오류: {str(e)[:50]}'})
    
    if all_dataframes:
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        duplicates_removed = 0
        if 'UT' in merged_df.columns:
            def is_meaningful_ut(value):
                if pd.isna(value): return False
                str_value = str(value).strip()
                if not str_value or str_value.lower() in ['nan', 'none', 'null']: return False
                if str_value.startswith('WOS:') or len(str_value) >= 15: return True
                return False

            meaningful_ut_mask = merged_df['UT'].apply(is_meaningful_ut)
            rows_with_meaningful_ut = merged_df[meaningful_ut_mask]
            rows_without_meaningful_ut = merged_df[~meaningful_ut_mask]
            
            if len(rows_with_meaningful_ut) > 1:
                before_dedup = len(rows_with_meaningful_ut)
                deduplicated_meaningful = rows_with_meaningful_ut.drop_duplicates(subset=['UT'], keep='first')
                duplicates_removed = before_dedup - len(deduplicated_meaningful)
                merged_df = pd.concat([deduplicated_meaningful, rows_without_meaningful_ut], ignore_index=True)
        
        return merged_df, file_status, duplicates_removed
    else:
        return None, file_status, 0

def parse_wos_format(content):
    lines = content.split('\n')
    records, current_record, current_field = [], {}, None
    for line in lines:
        line = line.rstrip()
        if not line: continue
        if line == 'ER':
            if current_record: records.append(current_record.copy())
            current_record, current_field = {}, None
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

# --- 최종 분류 함수 (주제 중심성 필터 적용) ---
def classify_article(row):
    """'주제 중심성' 필터가 적용된 최종 분류 함수"""
    
    # --- 키워드 셋 정의 ---
    core_streaming_keywords = [
        'live stream', 'livestream', 'live video', 'live broadcast', 
        'real-time stream', 'streaming platform', 'streaming service',
        'live commerce', 'live shopping', 'shoppertainment',
        'streamer', 'viewer', 'streaming audience',
        'twitch', 'youtube live', 'facebook live', 'tiktok live', 'douyin', 'kuaishou', 'taobao live',
        'game streaming', 'esports streaming'
    ]
    
    socio_technical_keywords = [
        'interactive', 'interaction', 'interactivity', 'real-time', 'synchronous',
        'social presence', 'telepresence', 'immediacy', 'responsiveness', 'user behavior', 
        'viewer behavior', 'psychology', 'psychological', 'motivation', 'motivate', 
        'engagement', 'engaging', 'addiction', 'addictive', 'loyalty', 'trust', 
        'satisfaction', 'intention', 'intentions', 'emotion', 'affective', 'attitude',
        'parasocial', 'social relationship', 'social support', 'social influence',
        'community', 'communities', 'virtual community', 'online community', 
        'cultural', 'culture', 'identity', 'identities', 'social capital', 'online culture'
    ]

    platform_ecosystem_keywords = [
        'platform', 'platforms', 'ecosystem', 'ecosystems', 'business model', 'business models',
        'monetization', 'revenue', 'governance', 'govern', 'creator economy', 'creators',
        'multi-sided', 'hiring', 'strategy', 'strategic', 'competitive',
        'commerce', 'marketing', 'influencer', 'brand', 'brands', 'purchase', 'purchasing', 
        'advertising', 'advertise', 'e-commerce', 'social commerce', 'sales', 'sale'
    ]
    
    technical_keywords = [
        'architecture', 'architectures', 'algorithm', 'algorithms', 'latency', 'quality of service', 
        'qos', 'video quality', 'webrtc', 'cdn'
    ]

    methodological_exclusion_types = [
        'editorial material', 'letter', 'proceedings paper', 'book chapter', 'correction', 
        'retracted publication', 'meeting abstract', 'note', 'short survey'
    ]
    duplicate_indicators = [
        'extended version', 'preliminary version', 'conference version', 'short version'
    ]

    # --- 텍스트 필드 추출 ---
    def extract_text(value): return str(value).lower().strip() if pd.notna(value) else ""
    title = extract_text(row.get('TI', ''))
    author_keywords = extract_text(row.get('DE', ''))
    keywords_plus = extract_text(row.get('ID', ''))
    abstract = extract_text(row.get('AB', ''))
    document_type = extract_text(row.get('DT', ''))
    
    full_text = ' '.join([title, abstract, author_keywords, keywords_plus])
    central_text = ' '.join([title, author_keywords, keywords_plus])

    # --- 최종 분류 로직 ---
    # Stage 1: 방법론적 부적합성 (EC3)
    if 'article' not in document_type and 'review' not in document_type: return 'EC3 - 방법론적 부적합성'
    if any(ind in full_text for ind in duplicate_indicators): return 'EC3 - 방법론적 부적합성'

    # Stage 2: 주제 중심성 필터 (EC2)
    if not any(kw in central_text for kw in core_streaming_keywords):
        return 'EC2 - 낮은 주제 중심성'

    # Stage 3: 핵심 현상 분류 (IC)
    if any(kw in full_text for kw in socio_technical_keywords):
        return 'Include - Socio-Technical Dynamics (사회-기술적 동학)'
    
    if any(kw in full_text for kw in platform_ecosystem_keywords):
        return 'Include - Platform Ecosystem Dynamics (플랫폼 생태계 동학)'
        
    if any(kw in full_text for kw in technical_keywords):
        context_words = ['user', 'viewer', 'audience', 'business', 'market', 'service', 'platform', 'streamer']
        if any(cw in full_text for cw in context_words):
             return 'Include - Technical Implementation (기술적 구현)'

    # Stage 4: 핵심 현상 부재 (EC4)
    return 'EC4 - 핵심 현상 분석 부재'

# --- 데이터 품질 진단 함수 ---
def diagnose_merged_quality(df, file_count, duplicates_removed):
    issues, recommendations = [], []
    required_fields, keyword_fields = ['TI', 'AU', 'SO', 'PY'], ['DE', 'ID']
    for field in required_fields:
        if field not in df.columns or df[field].isna().sum() / len(df) > 0.1:
            issues.append(f"⚠️ {field} 필드 누락률 높음")
    if not any(field in df.columns for field in keyword_fields):
        issues.append("❌ 키워드 필드(DE, ID) 없음")
    recommendations.append(f"✅ {file_count}개 파일 병합됨")
    if duplicates_removed > 0: recommendations.append(f"🔄 중복 논문 {duplicates_removed}편 제거됨")
    return issues, recommendations

# --- WOS Plain Text 형식 변환 함수 ---
def convert_to_scimat_wos_format(df_to_convert):
    wos_field_order = ['PT','AU','AF','TI','SO','LA','DT','DE','ID','AB','C1','C3','RP','EM','RI','OI','FU','FX','CR','NR','TC','Z9','U1','U2','PU','PI','PA','SN','EI','J9','JI','PD','PY','VL','IS','BP','EP','DI','EA','PG','WC','WE','SC','GA','UT','PM','OA','DA']
    file_content = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'C3', 'CR']
    for _, row in df_to_convert.iterrows():
        file_content.append("")
        for tag in wos_field_order:
            if tag in row and pd.notna(row[tag]) and str(row[tag]).strip():
                value = str(row[tag]).strip()
                if tag in multi_line_fields:
                    items = [item.strip() for item in value.split(';') if item.strip()]
                    if items:
                        file_content.append(f"{tag} {items[0]}")
                        file_content.extend(f"   {item}" for item in items[1:])
                else:
                    file_content.append(f"{tag} {value}")
        file_content.append("ER")
    return "\n".join(file_content).encode('utf-8-sig')

# --- 이하 UI 코드는 원상 복구 및 유지 ---

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
        <div class="feature-desc">주제 중심성 필터로 핵심 논문 정밀 선별</div>
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
    
    st.success(f"✅ 최종 정제 완료! {successful_files}개 파일에서 실장님의 연구 목적에 부합하는 핵심 논문 {total_papers:,}편을 정밀 선별했습니다.")
    
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다.")

    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 학술적 정제 결과</div>
        <div class="section-subtitle">최종 포함 기준(IC) 적용 후 연구 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    total_excluded = len(df_excluded_strict)
    df_final_output = df_for_analysis.drop(columns=['Classification'], errors='ignore')
    
    columns = st.columns(4)
    with columns[0]:
        st.markdown(f"""<div class="metric-card"><div class="metric-icon">📋</div><div class="metric-value">{len(df_final_output):,}</div><div class="metric-label">최종 분석 대상</div></div>""", unsafe_allow_html=True)
    
    include_papers = len(df_for_analysis)
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

        excluded_excel_data = [{'번호': idx + 1, '논문 제목': str(paper.get('TI', 'N/A')), '출판연도': str(paper.get('PY', 'N/A')), '저널명': str(paper.get('SO', 'N/A')), '배제 사유': str(paper.get('Classification', 'N/A'))} for idx, paper in df_excluded_strict.iterrows()]
        excluded_excel_df = pd.DataFrame(excluded_excel_data)
        excel_buffer_excluded = io.BytesIO()
        with pd.ExcelWriter(excel_buffer_excluded, engine='openpyxl') as writer:
            excluded_excel_df.to_excel(writer, sheet_name='Excluded_Papers', index=False)
        st.download_button(label=f"📊 제외된 논문 목록 엑셀 다운로드 ({len(df_excluded_strict)}편)", data=excel_buffer_excluded.getvalue(), file_name=f"excluded_papers_{len(df_excluded_strict)}papers.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="secondary", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        exclusion_categories = {'EC2': '낮은 주제 중심성', 'EC3': '방법론적 부적합성', 'EC4': '핵심 현상 분석 부재'}
        for ec_code, description in exclusion_categories.items():
            ec_papers = df_excluded_strict[df_excluded_strict['Classification'] == ec_code]
            if not ec_papers.empty:
                st.markdown(f"""<div style="margin: 12px 0; padding: 16px; background: white; border-left: 4px solid #ef4444; border-radius: 12px;"><strong style="color: #dc2626;">{ec_code}: {description}</strong> <span style="color: #8b95a1;">({len(ec_papers)}편)</span></div>""", unsafe_allow_html=True)

    st.markdown("""<div class="chart-container"><div class="chart-title">최종 정제 후 연구 분류 분포</div>""", unsafe_allow_html=True)
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
        <div class="section-title">📥 최종 데이터셋 다운로드</div>
        <div class="section-subtitle">최종 포함 기준이 적용된 고품질 WOS Plain Text 파일</div>
    </div>
    """, unsafe_allow_html=True)
    text_data = convert_to_scimat_wos_format(df_final_output)
    st.download_button(label="📥 최종 데이터셋 다운로드", data=text_data, file_name=f"live_streaming_final_dataset_{len(df_final_output)}papers.txt", mime="text/plain", type="primary", use_container_width=True)
