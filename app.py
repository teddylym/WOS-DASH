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

# --- 토스 스타일 CSS (생략 - 기존 코드와 동일) ---
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
        min-height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
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


# --- 데이터 로딩 및 파싱 함수 (수정 없음) ---
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

# --- 신규: 지능형 분류 함수 ---
def classify_for_review(row):
    """
    귀하의 수동 분류 로직을 학습하여 논문을 'Include', 'Exclude (X)', 'Consider (C)'로 자동 분류합니다.
    """
    
    def extract_text(value):
        return str(value).lower().strip() if pd.notna(value) else ""

    title = extract_text(row.get('TI', ''))
    abstract = extract_text(row.get('AB', ''))
    full_text = title + ' ' + abstract

    # --- 키워드 셋 정의 (XC모음.csv 분석 기반) ---

    # 1. '미해당(X)' 분류 키워드
    # EC1: 특정 응용 분야
    exclude_domains_X = [
        'surgery', 'surgical', 'medical', 'parasitology', 'anesthesiology', 'cardiac',
        'clinical', 'otolaryngology', 'thrombectomy', 'aneurysm', 'microsurgery',
        'teaching', 'education', 'learning', 'classroom', 'student',
        'legal', 'judicial', 'law', 'court', 'justice',
        'journalism', 'politics', 'political', 'authoritarianism', 'government',
        'suicide', 'trauma', 'abuse', 'trafficking', 'violence', 'terror',
        'firearm', 'buddhist', 'deities', 'ghosts', 'geological', 'seismic', 'satellite image'
    ]
    # EC2/EC5: 순수 기술 공학
    exclude_tech_X = [
        'p2p', 'peer-to-peer', 'network', 'protocol', 'qoe', 'qos', 'latency',
        'mpeg', 'dash', 'webrtc', 'algorithm', 'caching', 'bitrate', 'codec',
        'architecture', 'system performance', 'framework', 'traffic model',
        'packet scheduling', 'resource allocation', 'server system', 'optimization'
    ]
    # EC-Other: 명백한 범위 이탈
    exclude_other_X = ['on-demand', 'ott', 'pre-recorded', 'asynchronous', 'vod']

    # 2. '재검토(C)' 분류 키워드
    # 인접 플랫폼 유형
    consider_adjacent_C = ['music streaming']
    # 기술의 전략적 함의
    consider_tech_strategy_C = ['ai', 'artificial intelligence', 'blockchain', 'gamification']
    # 사회문화 현상 분석
    consider_socio_cultural_C = ['fan', 'fandom', 'community', 'bts']
    
    # 3. 생태계 관련 키워드 (X와 C를 구분하는 기준)
    ecosystem_keywords = [
        'platform', 'ecosystem', 'strategy', 'governance', 'business model', 'user',
        'consumer', 'audience', 'creator', 'streamer', 'viewer', 'community',
        'monetization', 'revenue', 'commerce', 'marketing', 'adoption', 'loyalty',
        'engagement', 'interaction', 'behavior', 'perception', 'intention', 'trust',
        'policy', 'regulation', 'ethics', 'supply chain', 'value'
    ]

    # --- 분류 로직 실행 ---

    # 1단계: 명백한 '미해당(X)' 사례 필터링
    if any(keyword in full_text for keyword in exclude_domains_X):
        return 'X', 'EC1: 특정 응용 분야'
    if any(keyword in full_text for keyword in exclude_other_X):
        return 'X', 'EC-Other: 명백한 범위 이탈'
    
    # 2단계: '재검토(C)' 사례 필터링
    if any(keyword in full_text for keyword in consider_adjacent_C):
        return 'C', '인접 플랫폼 유형'
    if any(keyword in full_text for keyword in consider_socio_cultural_C):
        return 'C', '사회문화 현상 분석'

    # 3단계: 기술 논문(X/C) 구분
    is_tech_topic = any(keyword in full_text for keyword in exclude_tech_X + consider_tech_strategy_C)
    is_ecosystem_topic = any(keyword in full_text for keyword in ecosystem_keywords)

    if is_tech_topic:
        if is_ecosystem_topic:
            return 'C', '기술의 전략적 함의' # 기술 + 생태계 논의 = 재검토
        else:
            return 'X', 'EC2/EC5: 순수 기술 공학' # 순수 기술 논의 = 미해당

    # 4단계: 위 조건에 모두 해당하지 않으면 '포함'
    return 'Include', '연구 범위 부합'


# --- 엑셀 변환 함수 ---
def to_excel(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# --- 메인 UI ---
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
        SCIMAT Edition (Advanced Filtering)
    </p>
    <div style="width: 80px; height: 3px; background-color: rgba(255,255,255,0.3); margin: 1.5rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)


st.markdown("""
<div class="section-header">
    <div class="section-title">📂 다중 WOS Plain Text 파일 업로드</div>
    <div class="section-subtitle">분석할 WOS Plain Text 파일들을 모두 선택하여 업로드하세요</div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "WOS Plain Text 파일 선택 (다중 선택 가능)",
    type=['txt'],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    st.markdown(f"📋 **선택된 파일 개수:** {len(uploaded_files)}개")
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 1차 스크리닝 적용 중..."):
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)
        
        if merged_df is None:
            st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다.")
            st.stop()

        # 지능형 분류 적용
        classification_results = merged_df.apply(classify_for_review, axis=1)
        merged_df[['Classification', 'Reason']] = pd.DataFrame(classification_results.tolist(), index=merged_df.index)

    st.success(f"✅ 병합 및 1차 스크리닝 완료! 총 {len(merged_df):,}편의 논문이 분류되었습니다.")
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다.")

    # --- 신규: 1차 스크리닝 결과 섹션 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">🔬 연구 대상 1차 스크리닝 결과</div>
        <div class="section-subtitle">귀하의 분류 기준에 따라 자동 생성된 '미해당(X)' 및 '재검토(C)' 목록</div>
    </div>
    """, unsafe_allow_html=True)

    df_included = merged_df[merged_df['Classification'] == 'Include']
    df_excluded = merged_df[merged_df['Classification'] == 'X']
    df_to_consider = merged_df[merged_df['Classification'] == 'C']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div>
                <div class="metric-icon" style="background: #10b981;">✅</div>
                <div class="metric-value">{len(df_included):,}</div>
                <div class="metric-label">연구 대상 후보 (Included)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div>
                <div class="metric-icon" style="background: #ef4444;">❌</div>
                <div class="metric-value">{len(df_excluded):,}</div>
                <div class="metric-label">연구 미해당 (Exclude - X)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div>
                <div class="metric-icon" style="background: #f59e0b;">⚠️</div>
                <div class="metric-value">{len(df_to_consider):,}</div>
                <div class="metric-label">재검토 필요 (Consider - C)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")

    # 미해당(X) 목록
    st.markdown('<h4 style="color: #dc2626;">❌ 연구 미해당 (Exclude - X) 목록</h4>', unsafe_allow_html=True)
    if not df_excluded.empty:
        st.download_button(
            label="엑셀 다운로드 (X 목록)",
            data=to_excel(df_excluded[['TI', 'AU', 'PY', 'Reason']]),
            file_name=f"excluded_papers_{len(df_excluded)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.dataframe(df_excluded[['TI', 'AU', 'PY', 'Reason']].rename(columns={
            'TI': '제목', 'AU': '저자', 'PY': '발행연도', 'Reason': '분류 사유'
        }), use_container_width=True, height=300)
    else:
        st.info("미해당으로 분류된 논문이 없습니다.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 재검토(C) 목록
    st.markdown('<h4 style="color: #d97706;">⚠️ 재검토 필요 (Consider - C) 목록</h4>', unsafe_allow_html=True)
    if not df_to_consider.empty:
        st.download_button(
            label="엑셀 다운로드 (C 목록)",
            data=to_excel(df_to_consider[['TI', 'AU', 'PY', 'Reason']]),
            file_name=f"consider_papers_{len(df_to_consider)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.dataframe(df_to_consider[['TI', 'AU', 'PY', 'Reason']].rename(columns={
            'TI': '제목', 'AU': '저자', 'PY': '발행연도', 'Reason': '분류 사유'
        }), use_container_width=True, height=300)
    else:
        st.info("재검토 필요로 분류된 논문이 없습니다.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)


    # --- 최종 분석 파일 생성 섹션 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">🔥 최종 분석용 파일 생성</div>
        <div class="section-subtitle">'연구 대상 후보(Included)' 논문만으로 SCIMAT 분석용 파일을 생성합니다.</div>
    </div>
    """, unsafe_allow_html=True)

    if not df_included.empty:
        df_final_output = df_included.drop(columns=['Classification', 'Reason'], errors='ignore')
        
        # SCIMAT 호환 파일 다운로드
        text_data = convert_to_scimat_wos_format(df_final_output)
        
        st.download_button(
            label=f"🔥 SCIMAT 분석용 파일 다운로드 ({len(df_final_output)}편)",
            data=text_data,
            file_name=f"included_for_scimat_{len(df_final_output)}_papers.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True,
            key="download_final_file",
            help="1차 스크리닝을 통과한 논문만으로 SCIMAT 분석용 파일을 생성합니다."
        )
    else:
        st.warning("분석용 파일을 생성할 '연구 대상 후보' 논문이 없습니다.")

