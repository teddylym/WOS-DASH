import streamlit as st
import pandas as pd
import altair as alt
import io
from collections import Counter

# --- 페이지 설정 ---
st.set_page_config(
    page_title="WOS Prep | Raw Data Edition",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 커스텀 CSS 스타일 ---
st.markdown("""
<style>
    .main-container {
        background: #f8f9fa;
        min-height: 100vh;
    }
    
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 20px rgba(0,56,117,0.15);
        border-color: #003875;
    }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: 700;
        color: #003875;
        margin: 0;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
        margin: 8px 0 0 0;
        font-weight: 500;
    }
    
    .metric-icon {
        background: linear-gradient(135deg, #003875, #0056b3);
        color: white;
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 16px;
    }
    
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin: 16px 0;
    }
    
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 16px;
        border-bottom: 2px solid #003875;
        padding-bottom: 8px;
    }
    
    .section-header {
        background: linear-gradient(135deg, #003875, #0056b3);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin: 24px 0 16px 0;
        box-shadow: 0 4px 16px rgba(0,56,117,0.2);
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
    }
    
    .section-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin: 4px 0 0 0;
    }
    
    .info-panel {
        background: #e8f0fe;
        border: 1px solid #003875;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .success-panel {
        background: #d4edda;
        border: 1px solid #28a745;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 20px;
        margin: 24px 0;
    }
    
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0,56,117,0.15);
        border-color: #003875;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 16px;
        background: linear-gradient(135deg, #003875, #0056b3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .feature-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 8px;
    }
    
    .feature-desc {
        font-size: 0.95rem;
        color: #6c757d;
        line-height: 1.5;
    }
    
    .upload-zone {
        background: white;
        border: 2px dashed #003875;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        margin: 20px 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        background: #f8f9fa;
        border-color: #0056b3;
    }
    
    .progress-indicator {
        background: linear-gradient(90deg, #003875, #0056b3);
        height: 4px;
        border-radius: 2px;
        margin: 16px 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
""", unsafe_allow_html=True)

# --- 데이터 로드 함수 ---
def load_data(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    encodings_to_try = ['utf-8-sig', 'utf-8', 'latin1', 'cp949']

    for encoding in encodings_to_try:
        try:
            file_content = file_bytes.decode(encoding)
            # 탭 구분자 우선 시도
            df = pd.read_csv(io.StringIO(file_content), sep='\t', lineterminator='\n')
            if df.shape[1] > 1: return df
        except Exception:
            continue

    for encoding in encodings_to_try:
        try:
            file_content = file_bytes.decode(encoding)
            # 콤마 구분자 시도
            df = pd.read_csv(io.StringIO(file_content))
            if df.shape[1] > 1: return df
        except Exception:
            continue

    return None

# --- 라이브 스트리밍 특화 분류 함수 ---
def classify_article(row):
    """라이브 스트리밍 연구를 위한 포괄적 분류"""
    
    # 핵심 포함 키워드
    core_inclusion_keywords = [
        'live streaming', 'livestreaming', 'live stream', 'live broadcast', 'live video',
        'real time streaming', 'real-time streaming', 'streaming platform', 'streaming service',
        'live commerce', 'live shopping', 'live selling', 'livestream commerce',
        'social commerce', 'live marketing', 'streaming monetization',
        'streamer', 'viewer', 'audience engagement', 'streaming audience', 'live audience',
        'streaming behavior', 'viewer behavior', 'streaming experience', 'live interaction',
        'streaming community', 'online community', 'digital community',
        'twitch', 'youtube live', 'facebook live', 'instagram live', 'tiktok live',
        'streaming media', 'video streaming', 'audio streaming', 'multimedia streaming',
        'live learning', 'streaming education', 'online education', 'e-learning',
        'gaming stream', 'esports', 'live gaming', 'streaming content',
        'influencer marketing', 'content creator', 'digital marketing', 'brand engagement',
        'consumer behavior', 'purchase intention', 'social influence'
    ]
    
    # 기술적 포함 키워드
    technical_inclusion_keywords = [
        'real time video', 'real-time video', 'video compression', 'video encoding',
        'adaptive streaming', 'video quality', 'streaming quality', 'latency',
        'video delivery', 'content delivery', 'cdn', 'edge computing',
        'multimedia communication', 'video communication', 'webrtc',
        'peer to peer streaming', 'p2p streaming', 'distributed streaming',
        'mobile streaming', 'mobile video', 'wireless streaming',
        'mobile broadcast', 'smartphone streaming'
    ]
    
    # 명확한 제외 키워드 (최소화)
    clear_exclusion_keywords = [
        'routing protocol', 'network topology', 'packet routing', 'mac protocol', 
        'ieee 802.11', 'wimax protocol', 'lte protocol',
        'vlsi design', 'circuit design', 'antenna design', 'rf circuit',
        'hardware implementation', 'fpga implementation', 'asic design',
        'signal processing algorithm', 'modulation scheme', 'channel estimation',
        'beamforming', 'mimo antenna', 'ofdm modulation',
        'satellite communication', 'underwater communication', 'space communication',
        'biomedical signal', 'medical imaging', 'radar system'
    ]
    
    # 텍스트 추출
    title = str(row.get('TI', '')).lower()
    source_title = str(row.get('SO', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    
    # 분류 로직
    if any(keyword in full_text for keyword in clear_exclusion_keywords):
        return 'Exclude (기술적 비관련)'
    
    if any(keyword in full_text for keyword in core_inclusion_keywords):
        return 'Include (핵심연구)'
    
    if any(keyword in full_text for keyword in technical_inclusion_keywords):
        live_indicators = ['live', 'real time', 'real-time', 'streaming', 'broadcast', 'interactive']
        if any(indicator in full_text for indicator in live_indicators):
            return 'Include (기술기반)'
        else:
            return 'Review (기술검토)'
    
    general_keywords = [
        'social media', 'social network', 'online platform', 'digital platform',
        'user experience', 'user behavior', 'consumer behavior', 'online behavior',
        'digital marketing', 'online marketing', 'content creation', 'content sharing',
        'video content', 'multimedia content', 'interactive media'
    ]
    
    if any(keyword in full_text for keyword in general_keywords):
        return 'Review (일반관련)'
    
    return 'Review (검토필요)'

# --- 원본 보존 WOS 변환 함수 ---
def convert_df_to_scimat_format(df_to_convert):
    """원본 데이터 그대로 WOS 형식으로 변환 (전처리 없음)"""
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
        
        # WOS 필드 순서대로 출력
        for tag in wos_field_order:
            if tag in row.index and pd.notna(row[tag]) and str(row[tag]).strip():
                value = str(row[tag]).strip()
                
                if tag in multi_line_fields:
                    # 세미콜론으로 분리된 항목들을 멀티라인으로 처리
                    items = [item.strip() for item in value.split(';') if item.strip()]
                    if items:
                        # 첫 번째 항목: 태그와 함께
                        file_content.append(f"{tag} {items[0]}")
                        # 나머지 항목들: 정확히 3칸 공백 인덴테이션
                        for item in items[1:]:
                            file_content.append(f"   {item}")
                else:
                    # 단일 라인 필드
                    file_content.append(f"{tag} {value}")
        
        file_content.append("ER")
    
    return "\n".join(file_content).encode('utf-8')

# --- 메인 헤더 ---
st.markdown("""
<div style="position: relative; text-align: center; padding: 2rem 0 3rem 0; background: linear-gradient(135deg, #003875, #0056b3); color: white; border-radius: 16px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,56,117,0.3);">
    <div style="position: absolute; top: 1rem; left: 2rem; color: white;">
        <div style="font-size: 14px; font-weight: 600; margin-bottom: 2px;">HANYANG UNIVERSITY</div>
        <div style="font-size: 12px; opacity: 0.9;">Technology Management Research</div>
        <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">mot.hanyang.ac.kr</div>
    </div>
    <div style="position: absolute; top: 1rem; right: 2rem; text-align: right; color: rgba(255,255,255,0.9); font-size: 0.85rem;">
        <p style="margin: 0;"><strong>Developed by:</strong> 임태경 (Teddy Lym)</p>
    </div>
    <h1 style="font-size: 3.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.02em;">
        WOS Prep
    </h1>
    <p style="font-size: 1.3rem; margin: 0; font-weight: 400; opacity: 0.95;">
        Raw Data Edition - No Preprocessing for Maximum SciMAT Compatibility
    </p>
    <div style="width: 100px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2rem auto; border-radius: 2px;"></div>
</div>
""", unsafe_allow_html=True)

# --- 주요 기능 소개 ---
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <div class="feature-icon">🔒</div>
        <div class="feature-title">원본 데이터 보존</div>
        <div class="feature-desc">키워드 전처리 없이 원본 그대로 유지</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">SciMAT 완전 호환</div>
        <div class="feature-desc">Word Group 기능 100% 작동 보장</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">라이브 스트리밍 분류</div>
        <div class="feature-desc">연구 범위 분류만 수행</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 핵심 철학 ---
st.markdown("""
<div class="success-panel">
    <h4 style="color: #155724; margin-bottom: 16px;">🎯 핵심 철학: 원본 데이터 그대로</h4>
    <ul style="line-height: 1.8; color: #155724;">
        <li><strong>키워드 전처리 금지:</strong> DE, ID 필드의 모든 키워드를 원본 그대로 보존</li>
        <li><strong>다양성 최대 보장:</strong> "machine learning", "machine-learning", "ML" 등 모든 표기법 유지</li>
        <li><strong>SciMAT Word Group:</strong> 유사 키워드가 충분히 존재하여 자동 그룹핑 가능</li>
        <li><strong>연구자 주도:</strong> SciMAT에서 수동으로 키워드 정리 및 그룹핑</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">📁 원본 데이터 업로드</div>
    <div class="section-subtitle">전처리 없이 원본 그대로 SciMAT에서 활용할 수 있도록 변환합니다.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="upload-zone">
    <div style="font-size: 3rem; margin-bottom: 16px; color: #003875;">📤</div>
    <h3 style="color: #212529; margin-bottom: 8px;">WOS 원본 파일을 선택하세요</h3>
    <p style="color: #6c757d; margin: 0;">Tab-delimited 또는 Plain Text 형식의 Web of Science 파일</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "파일 선택",
    type=['csv', 'txt'],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("⚠️ 파일을 읽을 수 없습니다. Web of Science에서 다운로드한 'Tab-delimited' 또는 'Plain Text' 형식의 파일이 맞는지 확인해주세요.")
        st.stop()

    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC', 'Cited Reference Count': 'NR', 'Times Cited, WoS Core': 'Z9'
    }
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)

    # 프로그레스 인디케이터
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner("🔄 라이브 스트리밍 연구 분류 중... (키워드는 원본 그대로 보존)"):
        # 논문 분류만 수행 (키워드 전처리 없음)
        df['Classification'] = df.apply(classify_article, axis=1)

    st.success("✅ 분류 완료! 키워드는 원본 그대로 보존되었습니다.")

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 분석 결과 요약</div>
        <div class="section-subtitle">원본 데이터 기반 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    classification_counts = df['Classification'].value_counts()
    total_papers = len(df)
    include_papers = len(df[df['Classification'].str.contains('Include', na=False)])
    
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
        # 원본 키워드 다양성 계산
        keyword_diversity = 0
        if 'DE' in df.columns:
            all_keywords = []
            for text in df['DE'].dropna():
                if text and str(text).strip():
                    keywords = [kw.strip() for kw in str(text).split(';') if kw.strip()]
                    all_keywords.extend(keywords)
            
            if all_keywords:
                unique_count = len(set([kw.lower() for kw in all_keywords]))
                total_count = len(all_keywords)
                keyword_diversity = (unique_count / total_count * 100) if total_count > 0 else 0
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🌈</div>
            <div class="metric-value">{keyword_diversity:.1f}%</div>
            <div class="metric-label">원본 키워드 다양성</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 논문 분류 현황 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Research Classification Distribution</div>
    """, unsafe_allow_html=True)

    classification_counts_df = df['Classification'].value_counts().reset_index()
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
                           scale=alt.Scale(range=['#003875', '#0056b3', '#17a2b8', '#ffc107', '#dc3545']),
                           legend=alt.Legend(orient="right", titleColor="#212529", labelColor="#495057")),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.8))
        ).add_params(selection)

        pie = base.mark_arc(outerRadius=120, innerRadius=70)
        text_total = alt.Chart(pd.DataFrame([{'value': f'{total_papers}'}])).mark_text(
            align='center', baseline='middle', fontSize=35, fontWeight='bold', color='#003875'
        ).encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame([{'value': 'Total Papers'}])).mark_text(
            align='center', baseline='middle', fontSize=14, dy=-25, color='#495057'
        ).encode(text='value:N')

        chart = (pie + text_total + text_label).properties(
            title=alt.TitleParams(text='논문 분류 분포', anchor='middle', fontSize=16, fontWeight=500, color="#212529"),
            width=300, height=300
        ).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 원본 키워드 샘플 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">원본 키워드 샘플 (전처리 없음)</div>
    """, unsafe_allow_html=True)
    
    if st.checkbox("🔍 원본 키워드 샘플 보기", key="sample_check"):
        sample_data = []
        sample_rows = df[df['Classification'].str.contains('Include', na=False)].head(5)
        
        for idx, row in sample_rows.iterrows():
            de_keywords = str(row.get('DE', 'N/A')) if pd.notna(row.get('DE')) else 'N/A'
            id_keywords = str(row.get('ID', 'N/A')) if pd.notna(row.get('ID')) else 'N/A'
            
            sample_data.append({
                '논문 ID': f"#{idx}",
                '제목': str(row.get('TI', 'N/A'))[:60] + "...",
                'DE (Author Keywords)': de_keywords[:100] + "..." if len(de_keywords) > 100 else de_keywords,
                'ID (Keywords Plus)': id_keywords[:100] + "..." if len(id_keywords) > 100 else id_keywords
            })
        
        if sample_data:
            sample_df = pd.DataFrame(sample_data)
            st.dataframe(sample_df, use_container_width=True, hide_index=True)
            
            st.success("✅ 모든 키워드가 원본 그대로 보존되어 SciMAT에서 최대한의 다양성을 제공합니다!")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 최종 데이터셋 준비 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">💾 SciMAT 호환 파일 다운로드</div>
        <div class="section-subtitle">원본 키워드 그대로 보존된 최고 호환성 파일</div>
    </div>
    """, unsafe_allow_html=True)

    # 최종 데이터셋 준비 (제외된 논문만 빼고)
    df_final = df[~df['Classification'].str.contains('Exclude', na=False)].copy()
    
    # Classification 컬럼만 제거 (키워드는 원본 그대로)
    df_final_output = df_final.drop(columns=['Classification'], errors='ignore')

    # 최종 통계
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        include_count = len(df[df['Classification'].str.contains('Include', na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{include_count:,}</div>
            <div class="metric-label">핵심 +
