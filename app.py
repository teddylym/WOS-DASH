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
        
        # 중복 제거 로직
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

# --- 수정된 라이브 스트리밍 특화 분류 함수 (Nature급 기준) ---
def classify_article(row):
    """Nature급 저널 기준에 맞춘 균형잡힌 라이브 스트리밍 연구 분류"""
    
    # --- 키워드 셋 정의 (더 포괄적이고 균형잡힌 접근) ---
    
    # IC1: 핵심 플랫폼 및 개념 (확장된 범위)
    core_streaming_keywords = [
        'live stream', 'livestream', 'live-stream', 'live video', 'live broadcast',
        'streaming platform', 'streaming service', 'streaming media',
        'live commerce', 'live shopping', 'social commerce', 'shoppertainment',
        'streamer', 'broadcaster', 'content creator', 'influencer',
        'viewer', 'audience', 'streaming community',
        'twitch', 'youtube', 'facebook live', 'instagram live', 'tiktok', 
        'douyin', 'kuaishou', 'taobao live', 'amazon live',
        'game streaming', 'esports', 'gaming broadcast',
        'educational streaming', 'webinar', 'virtual event',
        'live content', 'real-time content', 'synchronous media'
    ]
    
    # IC2: 연구 차원 키워드 (6개 차원으로 분류)
    research_dimensions = {
        'Technical': [
            'latency', 'bandwidth', 'quality', 'qos', 'qoe', 'buffering',
            'cdn', 'p2p', 'webrtc', 'streaming protocol', 'video quality',
            'adaptive bitrate', 'transcoding', 'edge computing', '5g'
        ],
        'Platform': [
            'platform', 'ecosystem', 'business model', 'monetization',
            'revenue', 'creator economy', 'platform governance', 'algorithm',
            'recommendation', 'content moderation', 'platform policy'
        ],
        'User': [
            'user behavior', 'user experience', 'engagement', 'interaction',
            'participation', 'motivation', 'satisfaction', 'loyalty',
            'parasocial', 'social presence', 'community', 'fandom'
        ],
        'Commercial': [
            'commerce', 'e-commerce', 'marketing', 'advertising', 'brand',
            'purchase', 'sales', 'conversion', 'roi', 'influencer marketing',
            'product placement', 'sponsorship', 'donation', 'virtual gift'
        ],
        'Social': [
            'social', 'cultural', 'identity', 'social capital', 'social impact',
            'digital culture', 'online community', 'social interaction',
            'social media', 'social network', 'viral', 'trend'
        ],
        'Educational': [
            'education', 'learning', 'teaching', 'mooc', 'online education',
            'distance learning', 'virtual classroom', 'student engagement',
            'pedagogical', 'instructional', 'training', 'skill development'
        ]
    }
    
    # EC: 배제 기준 (최소화 및 명확화)
    
    # EC1: 순수 기술 인프라 (사회적 맥락 완전 부재)
    pure_infrastructure = [
        'network topology', 'routing algorithm', 'packet loss',
        'tcp congestion', 'udp optimization', 'multicast routing',
        'satellite communication', 'optical fiber', 'base station',
        'antenna design', 'signal processing', 'modulation scheme'
    ]
    
    # EC2: 의료/생물학적 신호 처리 (완전히 다른 도메인)
    medical_signals = [
        'ecg streaming', 'eeg monitoring', 'medical imaging',
        'biosignal', 'telemedicine device', 'remote surgery',
        'patient monitoring', 'health sensor'
    ]
    
    # EC3: 비학술적 콘텐츠
    non_academic = [
        'conference abstract only', 'editorial', 'news item',
        'book review', 'obituary', 'erratum', 'retraction'
    ]
    
    # --- 텍스트 필드 추출 및 결합 ---
    def extract_text(value):
        return str(value).lower().strip() if pd.notna(value) else ""
    
    title = extract_text(row.get('TI', ''))
    abstract = extract_text(row.get('AB', ''))
    author_keywords = extract_text(row.get('DE', ''))
    keywords_plus = extract_text(row.get('ID', ''))
    document_type = extract_text(row.get('DT', ''))
    
    # 제목과 키워드를 우선적으로 검토 (초록은 보조적)
    primary_text = ' '.join([title, author_keywords, keywords_plus])
    full_text = ' '.join([title, abstract, author_keywords, keywords_plus])
    
    # --- 분류 로직 (균형잡힌 접근) ---
    
    # Stage 1: 문서 유형 확인
    if document_type and any(exc in document_type for exc in ['editorial', 'correction', 'retraction']):
        return 'EC3 - Non-academic content'
    
    # Stage 2: 핵심 라이브 스트리밍 관련성 확인 (제목/키워드 우선)
    core_relevance_score = sum(1 for kw in core_streaming_keywords if kw in primary_text)
    
    # 제목이나 키워드에 명확한 언급이 있으면 포함
    if core_relevance_score >= 1:
        # 연구 차원 확인
        dimension_scores = {}
        for dim, keywords in research_dimensions.items():
            score = sum(1 for kw in keywords if kw in full_text)
            if score > 0:
                dimension_scores[dim] = score
        
        if dimension_scores:
            # 가장 강한 연구 차원 식별
            primary_dimension = max(dimension_scores, key=dimension_scores.get)
            
            # 순수 인프라나 의료 신호가 주요 주제가 아닌지 확인
            infra_score = sum(1 for kw in pure_infrastructure if kw in full_text)
            medical_score = sum(1 for kw in medical_signals if kw in full_text)
            
            # 인프라/의료가 부차적인 경우에만 배제
            if infra_score > core_relevance_score * 2:
                return 'EC1 - Pure infrastructure focus'
            elif medical_score > core_relevance_score:
                return 'EC2 - Medical domain'
            else:
                return f'Include - {primary_dimension}'
        else:
            # 연구 차원이 명확하지 않지만 라이브 스트리밍은 언급됨
            return 'Review - Dimension unclear'
    
    # Stage 3: 초록에서만 언급되는 경우 (더 신중한 평가)
    abstract_relevance = sum(1 for kw in core_streaming_keywords if kw in abstract)
    
    if abstract_relevance >= 2:  # 초록에 여러 번 언급
        # 연구 차원 재확인
        for dim, keywords in research_dimensions.items():
            if any(kw in full_text for kw in keywords):
                return f'Include - {dim}'
        return 'Review - Peripheral mention'
    elif abstract_relevance == 1:  # 초록에 한 번만 언급
        return 'Review - Minimal relevance'
    
    # Stage 4: 완전히 무관한 연구
    return 'Exclude - No relevance'

# --- 데이터 품질 진단 함수 ---
def diagnose_merged_quality(df, file_count, duplicates_removed):
    """병합된 WOS 데이터의 품질 진단"""
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
    
    # 병합 관련 정보
    recommendations.append(f"✅ {file_count}개 파일 성공적으로 병합됨")
    
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
<div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #3182f6, #1c64f2); color: white; border-radius: 8px; margin-bottom: 1.5rem;">
    <h1 style="font-size: 3rem; font-weight: 700; margin-bottom: 0.3rem;">WOS PREP</h1>
    <p style="font-size: 1.1rem; margin: 0; font-weight: 500;">SCIMAT Edition - Nature급 학술 기준 적용</p>
</div>
""", unsafe_allow_html=True)

# --- 핵심 기능 소개 ---
st.markdown("""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; margin: 20px 0;">
    <div style="background: white; border-radius: 8px; padding: 20px; text-align: center; border: 1px solid #e5e8eb;">
        <div style="font-size: 32px; margin-bottom: 12px;">🔗</div>
        <div style="font-weight: 600; margin-bottom: 8px;">다중 파일 자동 병합</div>
        <div style="font-size: 13px; color: #8b95a1;">여러 WOS 파일을 한 번에 병합 처리</div>
    </div>
    <div style="background: white; border-radius: 8px; padding: 20px; text-align: center; border: 1px solid #e5e8eb;">
        <div style="font-size: 32px; margin-bottom: 12px;">🎯</div>
        <div style="font-weight: 600; margin-bottom: 8px;">균형잡힌 학술 필터링</div>
        <div style="font-size: 13px; color: #8b95a1;">Nature급 저널 기준 적용</div>
    </div>
    <div style="background: white; border-radius: 8px; padding: 20px; text-align: center; border: 1px solid #e5e8eb;">
        <div style="font-size: 32px; margin-bottom: 12px;">📊</div>
        <div style="font-weight: 600; margin-bottom: 8px;">SCIMAT 완벽 호환</div>
        <div style="font-size: 13px; color: #8b95a1;">100% 호환 WOS 형식 출력</div>
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
    
    with st.spinner(f"🔄 {len
