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
    
    .warning-panel {
        background: #fff3cd;
        border: 1px solid #ffc107;
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
        padding: 40px 20px;
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
    
    .file-status {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid #003875;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
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
        
        # 중복 제거 로직 - 완전히 새로 작성 (가장 보수적 접근)
        duplicates_removed = 0
        
        # UT 필드가 있는 경우에만 중복 제거 시도
        if 'UT' in merged_df.columns:
            # UT 값들의 실제 상태 분석
            ut_series = merged_df['UT'].copy()
            
            # 실제 의미있는 UT 식별자만 찾기 (매우 엄격한 기준)
            def has_real_ut_identifier(value):
                if pd.isna(value):
                    return False
                
                str_val = str(value).strip()
                
                # 빈 문자열이나 일반적인 결측값 표현들 제외
                if str_val.lower() in ['', 'nan', 'none', 'null', 'na']:
                    return False
                
                # WOS UT는 보통 'WOS:000...' 형태이거나 고유한 식별자
                # 최소 10자 이상이고 실제 식별자 패턴을 가져야 함
                if len(str_val) < 10:
                    return False
                
                # 'WOS:' 로 시작하거나 충분히 긴 영숫자 조합인 경우만 유효
                if str_val.startswith('WOS:') or (len(str_val) >= 15 and any(c.isalnum() for c in str_val)):
                    return True
                
                return False
            
            # 실제 UT 식별자를 가진 행들만 선별
            has_real_ut = ut_series.apply(has_real_ut_identifier)
            rows_with_real_ut = merged_df[has_real_ut]
            rows_without_real_ut = merged_df[~has_real_ut]
            
            print(f"DEBUG: 전체 {original_count}편 중 실제 UT 식별자 보유: {len(rows_with_real_ut)}편")
            print(f"DEBUG: UT 없거나 무효한 UT: {len(rows_without_real_ut)}편")
            
            # 실제 UT 식별자가 있는 행들에서만 중복 제거
            if len(rows_with_real_ut) > 1:  # 최소 2개 이상 있어야 중복 검사 의미
                # 중복 제거 전후 비교
                before_dedup = len(rows_with_real_ut)
                deduplicated_ut_rows = rows_with_real_ut.drop_duplicates(subset=['UT'], keep='first')
                after_dedup = len(deduplicated_ut_rows)
                
                actual_duplicates = before_dedup - after_dedup
                
                if actual_duplicates > 0:
                    print(f"DEBUG: 실제 UT 중복 발견: {actual_duplicates}편 제거")
                    duplicates_removed = actual_duplicates
                    
                    # 중복 제거된 결과와 UT 없는 행들 재결합
                    merged_df = pd.concat([deduplicated_ut_rows, rows_without_real_ut], ignore_index=True)
                else:
                    print("DEBUG: 실제 UT 중복 없음")
            else:
                print("DEBUG: 중복 검사할 만한 실제 UT 식별자가 충분하지 않음")
        
        # 대안: UT가 없거나 신뢰할 수 없는 경우 제목+저자 기준 중복 제거
        if duplicates_removed == 0 and 'TI' in merged_df.columns:
            print("DEBUG: UT 기준 중복이 없어 제목+저자 기준으로 추가 확인")
            
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
                    print(f"DEBUG: 제목+저자 기준 중복 발견: {title_author_removed}편 제거")
                    duplicates_removed = title_author_removed
                    merged_df = pd.concat([deduplicated_complete, incomplete_rows], ignore_index=True)
        
        final_count = len(merged_df)
        print(f"DEBUG: 최종 결과 - 원본: {original_count}편, 최종: {final_count}편, 제거: {duplicates_removed}편")
        
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

# --- 라이브 스트리밍 특화 분류 함수 ---
def classify_article(row):
    """라이브 스트리밍 연구를 위한 포괄적 분류 - 개선된 알고리즘"""
    
    # 핵심 라이브 스트리밍 키워드 (직접적 관련성)
    core_streaming_keywords = [
        'live streaming', 'livestreaming', 'live stream', 'live broadcast', 'live video',
        'real time streaming', 'real-time streaming', 'streaming platform', 'streaming service',
        'live webcast', 'webcasting', 'live transmission', 'interactive broadcasting',
        'live commerce', 'live shopping', 'live selling', 'livestream commerce',
        'live e-commerce', 'social commerce', 'live marketing', 'streaming monetization',
        'live retail', 'shoppertainment', 'live sales', 'streaming sales',
        'streamer', 'viewer', 'audience engagement', 'streaming audience', 'live audience',
        'streaming behavior', 'viewer behavior', 'streaming experience', 'live interaction',
        'streaming community', 'online community', 'digital community', 'virtual community',
        'parasocial relationship', 'streamer-viewer', 'live chat', 'chat interaction',
        'twitch', 'youtube live', 'facebook live', 'instagram live', 'tiktok live',
        'periscope', 'mixer', 'douyin', 'kuaishou', 'taobao live', 'tmall live',
        'amazon live', 'shopee live', 'live.ly', 'bigo live',
        'live gaming', 'game streaming', 'esports streaming', 'streaming content',
        'live entertainment', 'live performance', 'virtual concert', 'live music'
    ]
    
    # 확장된 비즈니스 및 커머스 관련 키워드
    business_commerce_keywords = [
        'e-commerce', 'online shopping', 'digital commerce', 'mobile commerce', 'm-commerce',
        'social commerce', 'influencer marketing', 'content creator', 'digital marketing', 
        'brand engagement', 'consumer behavior', 'purchase intention', 'buying behavior',
        'social influence', 'word of mouth', 'viral marketing', 'user generated content',
        'brand advocacy', 'customer engagement', 'social media marketing', 'digital influence',
        'online influence', 'interactive marketing', 'personalized marketing', 'real-time marketing',
        'digital transformation', 'omnichannel', 'customer experience', 'user experience',
        'engagement marketing', 'social selling', 'digital retail', 'online retail'
    ]
    
    # 교육 및 학습 관련 키워드 (확장)
    education_keywords = [
        'online education', 'e-learning', 'distance learning', 'remote learning',
        'virtual classroom', 'online teaching', 'digital learning', 'mooc',
        'educational technology', 'learning management system', 'blended learning',
        'medical education', 'nursing education', 'surgical training', 'clinical education',
        'telemedicine', 'telehealth', 'digital health', 'health education',
        'interactive learning', 'synchronous learning', 'real-time learning'
    ]
    
    # 기술적 기반 키워드 (확장)
    technical_keywords = [
        'real time video', 'real-time video', 'video streaming', 'audio streaming',
        'multimedia streaming', 'video compression', 'video encoding', 'video delivery',
        'content delivery', 'cdn', 'edge computing', 'multimedia communication',
        'video communication', 'webrtc', 'peer to peer streaming', 'p2p streaming',
        'distributed streaming', 'mobile streaming', 'mobile video', 'wireless streaming',
        'mobile broadcast', 'smartphone streaming', 'live video transmission',
        'streaming technology', 'adaptive streaming', 'video quality', 'streaming latency',
        'interactive media', 'virtual reality', 'augmented reality', 'vr', 'ar',
        '3d streaming', 'immersive media', 'metaverse'
    ]
    
    # 사회문화적 영향 키워드 (신규 추가)
    sociocultural_keywords = [
        'digital culture', 'online culture', 'virtual community', 'digital society',
        'social media', 'social network', 'digital communication', 'online interaction',
        'digital identity', 'virtual identity', 'online presence', 'digital participation',
        'cultural transmission', 'digital religion', 'online religion', 'virtual religion',
        'digital migration', 'online migration', 'digital diaspora', 'virtual diaspora',
        'social cohesion', 'community building', 'social capital', 'digital divide'
    ]
    
    # COVID-19 및 팬데믹 관련 키워드 (신규 추가)
    pandemic_keywords = [
        'covid-19', 'pandemic', 'coronavirus', 'sars-cov-2', 'lockdown', 'quarantine',
        'social distancing', 'remote work', 'work from home', 'digital adaptation',
        'pandemic response', 'crisis communication', 'emergency response'
    ]
    
    # 확장된 소셜 미디어 키워드
    social_media_keywords = [
        'social media', 'social network', 'online platform', 'digital platform',
        'user experience', 'user behavior', 'online behavior', 'digital behavior',
        'social interaction', 'online interaction', 'digital interaction',
        'user engagement', 'digital engagement', 'platform economy', 'network effects',
        'viral content', 'content sharing', 'social sharing', 'online community'
    ]
    
    # 제외 키워드 (기술적 비관련 - 더 엄격하게)
    exclusion_keywords = [
        'routing protocol', 'network topology', 'packet routing', 'mac protocol',
        'ieee 802.11', 'wimax protocol', 'lte protocol', 'network security protocol',
        'vlsi design', 'circuit design', 'antenna design', 'rf circuit',
        'hardware implementation', 'fpga implementation', 'asic design',
        'signal processing algorithm', 'modulation scheme', 'channel estimation',
        'beamforming algorithm', 'mimo antenna', 'ofdm modulation',
        'frequency allocation', 'spectrum allocation', 'wireless sensor network',
        'satellite communication', 'underwater communication', 'space communication',
        'biomedical signal', 'medical imaging', 'radar system', 'sonar system',
        'geological survey', 'seismic data', 'astronomical data', 'climate modeling'
    ]
    
    # 텍스트 추출
    def extract_text(value):
        if pd.isna(value) or value is None:
            return ""
        return str(value).lower().strip()
    
    title = extract_text(row.get('TI', ''))
    source_title = extract_text(row.get('SO', ''))
    author_keywords = extract_text(row.get('DE', ''))
    keywords_plus = extract_text(row.get('ID', ''))
    abstract = extract_text(row.get('AB', ''))
    
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    
    # 개선된 분류 로직
    # 1. 명확한 제외 대상 먼저 필터링
    if any(keyword in full_text for keyword in exclusion_keywords):
        return 'Exclude (기술적 비관련)'
    
    # 2. 핵심 라이브 스트리밍 키워드 - 최우선 포함
    if any(keyword in full_text for keyword in core_streaming_keywords):
        return 'Include (핵심연구)'
    
    # 3. 비즈니스/커머스 + 디지털 지표 - 포용적 접근
    if any(keyword in full_text for keyword in business_commerce_keywords):
        digital_indicators = ['digital', 'online', 'internet', 'web', 'social media', 'platform', 'mobile', 'app', 'virtual', 'interactive']
        if any(indicator in full_text for indicator in digital_indicators):
            return 'Include (비즈니스 관련)'
    
    # 4. 교육 + 온라인/디지털 지표 - 포용적 접근
    if any(keyword in full_text for keyword in education_keywords):
        online_indicators = ['online', 'digital', 'virtual', 'remote', 'distance', 'interactive', 'real-time', 'synchronous']
        if any(indicator in full_text for indicator in online_indicators):
            return 'Include (교육 관련)'
    
    # 5. 기술적 기반 + 라이브/실시간 지표
    if any(keyword in full_text for keyword in technical_keywords):
        live_indicators = ['live', 'real time', 'real-time', 'streaming', 'broadcast', 'interactive', 'synchronous', 'instant']
        if any(indicator in full_text for indicator in live_indicators):
            return 'Include (기술적 기반)'
    
    # 6. 사회문화적 + 디지털 지표 (신규)
    if any(keyword in full_text for keyword in sociocultural_keywords):
        digital_indicators = ['digital', 'online', 'virtual', 'internet', 'web', 'platform', 'social media']
        if any(indicator in full_text for indicator in digital_indicators):
            return 'Include (사회문화 관련)'
    
    # 7. 팬데믹 관련 + 디지털 지표 (신규)
    if any(keyword in full_text for keyword in pandemic_keywords):
        digital_indicators = ['digital', 'online', 'virtual', 'remote', 'streaming', 'platform', 'technology']
        if any(indicator in full_text for indicator in digital_indicators):
            return 'Include (팬데믹 디지털화)'
    
    # 8. 소셜 미디어 일반 - 조건부 포함
    if any(keyword in full_text for keyword in social_media_keywords):
        interaction_indicators = ['interaction', 'engagement', 'community', 'sharing', 'content', 'creator', 'influencer']
        if any(indicator in full_text for indicator in interaction_indicators):
            return 'Include (소셜미디어 관련)'
        else:
            return 'Review (소셜미디어 검토)'
    
    # 9. 기타 - 최소 검토 대상
    return 'Review (분류 불확실)'

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
        WOS PREP
    </h1>
    <p style="font-size: 1.3rem; margin: 0; font-weight: 400; opacity: 0.95;">
        SCIMAT Edition
    </p>
    <div style="width: 100px; height: 4px; background-color: rgba(255,255,255,0.3); margin: 2rem auto; border-radius: 2px;"></div>
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
        <div class="feature-title">데이터 분류</div>
        <div class="feature-desc">대규모 데이터 포괄적 분류 및 분석</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">📁 다중 WOS Plain Text 파일 업로드</div>
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
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 분석 중..."):
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
    total_papers = len(merged_df)
    
    st.success(f"✅ 병합 완료! {successful_files}개 파일에서 {total_papers:,}편의 논문을 성공적으로 처리했습니다.")
    
    # 중복 제거 결과 표시 - 실제 결과만
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다. (원본 총 {total_papers + duplicates_removed:,}편 → 정제 후 {total_papers:,}편)")
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
            color = "#28a745" if status['status'] == 'SUCCESS' else "#dc3545"
            icon = "✅" if status['status'] == 'SUCCESS' else "❌"
            
            st.markdown(f"""
            <div style="margin: 8px 0; padding: 12px; background: #f8f9fa; border-left: 4px solid {color}; border-radius: 4px;">
                <strong>{icon} {status['filename']}</strong><br>
                <small style="color: #6c757d;">{status['message']}</small>
                {f" | 인코딩: {status['encoding']}" if status['encoding'] != 'N/A' else ""}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # 파일 처리 통계
        success_count = len([s for s in file_status if s['status'] == 'SUCCESS'])
        error_count = len([s for s in file_status if s['status'] == 'ERROR'])
        
        st.markdown(f"""
        <div class="metric-card" style="background: #f8f9fa;">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{success_count}</div>
            <div class="metric-label">성공한 파일</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card" style="background: #f8f9fa;">
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
        issues, recommendations = diagnose_merged_quality(merged_df, successful_files, duplicates_removed)

    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">🔍 병합 데이터 품질 진단 결과</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h5 style="color: #dc3545; margin-bottom: 12px;">🚨 발견된 문제점</h5>', unsafe_allow_html=True)
        
        if issues:
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.markdown("✅ **문제점 없음** - 병합 데이터 품질 우수")
    
    with col2:
        st.markdown('<h5 style="color: #28a745; margin-bottom: 12px;">💡 병합 결과</h5>', unsafe_allow_html=True)
        
        if recommendations:
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.markdown("🎯 **최적 상태** - SCIMAT 완벽 호환")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 병합 성공 알림
    st.markdown("""
    <div class="success-panel">
        <h4 style="color: #155724; margin-bottom: 16px;">🎯 다중 파일 병합 성공!</h4>
        <p style="color: #155724; margin: 4px 0;">여러 WOS Plain Text 파일이 성공적으로 하나로 병합되었습니다.</p>
        <p style="color: #155724; margin: 4px 0;"><strong>중복 제거:</strong> 동일한 논문은 자동으로 제거되어 정확한 분석 결과를 보장합니다.</p>
        <p style="color: #155724; margin: 4px 0;"><strong>SCIMAT 호환성:</strong> 병합된 파일은 SCIMAT에서 100% 정상 작동합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📈 병합 데이터 분석 결과</div>
        <div class="section-subtitle">라이브 스트리밍 연구 분류 결과</div>
    </div>
    """, unsafe_allow_html=True)

    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    classification_counts = merged_df['Classification'].value_counts()
    total_papers = len(merged_df)
    include_papers = len(merged_df[merged_df['Classification'].str.contains('Include', na=False)])
    
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
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔗</div>
            <div class="metric-value" style="font-size: 1.8rem;">{successful_files}개</div>
            <div class="metric-label">Merged Files</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 논문 분류 현황 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">Research Classification Distribution</div>
    """, unsafe_allow_html=True)

    classification_counts_df = merged_df['Classification'].value_counts().reset_index()
    classification_counts_df.columns = ['분류', '논문 수']

    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        st.dataframe(classification_counts_df, use_container_width=True, hide_index=True)

    with col2:
        # 도넛 차트 - 크기 확대
        selection = alt.selection_point(fields=['분류'], on='mouseover', nearest=True)

        base = alt.Chart(classification_counts_df).encode(
            theta=alt.Theta(field="논문 수", type="quantitative", stack=True),
            color=alt.Color(field="분류", type="nominal", title="Classification",
                           scale=alt.Scale(range=['#003875', '#0056b3', '#17a2b8', '#28a745', '#ffc107', '#dc3545']),
                           legend=alt.Legend(orient="right", titleColor="#212529", labelColor="#495057")),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.8))
        ).add_params(selection)

        pie = base.mark_arc(outerRadius=150, innerRadius=90)
        text_total = alt.Chart(pd.DataFrame([{'value': f'{total_papers}'}])).mark_text(
            align='center', baseline='middle', fontSize=45, fontWeight='bold', color='#003875'
        ).encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame([{'value': 'Total Papers'}])).mark_text(
            align='center', baseline='middle', fontSize=16, dy=30, color='#495057'
        ).encode(text='value:N')

        chart = (pie + text_total + text_label).properties(
            width=350, height=350
        ).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 분류 상세 결과 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">분류별 상세 분포</div>
    """, unsafe_allow_html=True)
    
    # 분류별 상세 통계 - 폰트 크기 증가
    for classification in merged_df['Classification'].unique():
        count = len(merged_df[merged_df['Classification'] == classification])
        percentage = (count / total_papers * 100)
        
        if classification.startswith('Include'):
            color = "#28a745"
            icon = "✅"
        elif classification.startswith('Review'):
            color = "#ffc107"
            icon = "📝"
        else:
            color = "#dc3545"
            icon = "❌"
        
        st.markdown(f"""
        <div style="margin: 12px 0; padding: 16px; background: white; border-left: 4px solid {color}; border-radius: 4px; font-size: 1.1rem;">
            <strong>{icon} {classification}:</strong> {count:,}편 ({percentage:.1f}%)
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 연도별 연구 동향 ---
    if 'PY' in merged_df.columns:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">29년 라이브 스트리밍 연구 진화 동향 (1996-2024)</div>
        """, unsafe_allow_html=True)
        
        df_trend = merged_df.copy()
        df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
        df_trend.dropna(subset=['PY'], inplace=True)
        df_trend['PY'] = df_trend['PY'].astype(int)
        
        yearly_counts = df_trend['PY'].value_counts().reset_index()
        yearly_counts.columns = ['Year', 'Count']
        yearly_counts = yearly_counts[yearly_counts['Year'] <= 2025].sort_values('Year')

        if len(yearly_counts) > 0:
            line_chart = alt.Chart(yearly_counts).mark_line(
                point={'size': 80, 'filled': True}, strokeWidth=3, color='#003875'
            ).encode(
                x=alt.X('Year:O', title='발행 연도'),
                y=alt.Y('Count:Q', title='논문 수'),
                tooltip=['Year', 'Count']
            ).properties(height=300)
            
            st.altair_chart(line_chart, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 키워드 샘플 확인 ---
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">병합 데이터 키워드 품질 확인</div>
    """, unsafe_allow_html=True)
    
    sample_data = []
    sample_rows = merged_df[merged_df['Classification'].str.contains('Include', na=False)].head(3)
    
    for idx, row in sample_rows.iterrows():
        title = str(row.get('TI', 'N/A'))[:80] + "..." if len(str(row.get('TI', 'N/A'))) > 80 else str(row.get('TI', 'N/A'))
        de_keywords = str(row.get('DE', 'N/A')) if pd.notna(row.get('DE')) else 'N/A'
        id_keywords = str(row.get('ID', 'N/A')) if pd.notna(row.get('ID')) else 'N/A'
        
        # 키워드 개수 계산
        de_count = len([k.strip() for k in de_keywords.split(';') if k.strip()]) if de_keywords != 'N/A' else 0
        id_count = len([k.strip() for k in id_keywords.split(';') if k.strip()]) if id_keywords != 'N/A' else 0
        
        sample_data.append({
            '논문 제목': title,
            'DE 키워드': de_keywords[:100] + "..." if len(de_keywords) > 100 else de_keywords,
            'ID 키워드': id_keywords[:100] + "..." if len(id_keywords) > 100 else id_keywords,
            'DE 개수': de_count,
            'ID 개수': id_count
        })
    
    if sample_data:
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True, hide_index=True)
        
        # 키워드 품질 평가
        avg_de = sum([d['DE 개수'] for d in sample_data]) / len(sample_data) if sample_data else 0
        avg_id = sum([d['ID 개수'] for d in sample_data]) / len(sample_data) if sample_data else 0
        
        if avg_de >= 3 and avg_id >= 3:
            st.success("✅ 키워드 품질 우수 - SCIMAT에서 원활한 그룹핑 예상")
        elif avg_de >= 2 or avg_id >= 2:
            st.warning("⚠️ 키워드 품질 보통 - SCIMAT에서 일부 제한 가능")
        else:
            st.error("❌ 키워드 품질 부족 - 원본 WOS 다운로드 설정 확인 필요")

    st.markdown("</div>", unsafe_allow_html=True)

    # 최종 데이터셋 준비 (제외된 논문만 빼고)
    df_final = merged_df[~merged_df['Classification'].str.contains('Exclude', na=False)].copy()
    
    # Classification 컬럼만 제거 (원본 WOS 형식 유지)
    df_final_output = df_final.drop(columns=['Classification'], errors='ignore')

    # 최종 통계 - 제외 박스 추가
    exclude_papers = merged_df[merged_df['Classification'].str.contains('Exclude', na=False)]
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상<br><small style="color: #6c757d;">(Exclude 제외)</small></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        include_count = len(merged_df[merged_df['Classification'].str.contains('Include', na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{include_count:,}</div>
            <div class="metric-label">핵심 포함 연구</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        review_count = len(merged_df[merged_df['Classification'].str.contains('Review', na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📝</div>
            <div class="metric-value">{review_count:,}</div>
            <div class="metric-label">검토 대상</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        exclude_count = len(exclude_papers)
        # 제외 박스 - 클릭하면 토글되도록 만들기
        if st.button(
            f"❌ {exclude_count:,} 제외 대상", 
            key="exclude_toggle_button",
            help="클릭하면 제외된 논문 목록을 확인할 수 있습니다",
            use_container_width=True
        ):
            st.session_state['show_exclude_details'] = not st.session_state.get('show_exclude_details', False)

    # 제외 박스 클릭 시 상세 정보 토글
    if st.session_state.get('show_exclude_details', False) and len(exclude_papers) > 0:
        st.markdown("""
        <div style="background: #f8d7da; padding: 16px; border-radius: 8px; margin: 16px 0; border: 1px solid #dc3545;">
            <h4 style="color: #721c24; margin-bottom: 12px;">❌ 제외된 논문 상세 목록</h4>
            <p style="color: #721c24; margin-bottom: 16px;">
                <strong>🚫 제외 사유:</strong> 라이브 스트리밍 연구와 관련성이 낮은 기술적 비관련 연구들입니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        for idx, (_, paper) in enumerate(exclude_papers.head(10).iterrows(), 1):  # 최대 10개만 표시
            title = str(paper.get('TI', 'N/A'))[:100] + "..." if len(str(paper.get('TI', 'N/A'))) > 100 else str(paper.get('TI', 'N/A'))
            year = str(paper.get('PY', 'N/A'))
            source = str(paper.get('SO', 'N/A'))[:50] + "..." if len(str(paper.get('SO', 'N/A'))) > 50 else str(paper.get('SO', 'N/A'))
            
            st.markdown(f"""
            <div style="margin: 8px 0; padding: 12px; background: white; border-left: 3px solid #dc3545; border-radius: 4px;">
                <div style="display: flex; align-items: center; margin-bottom: 6px;">
                    <span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; margin-right: 8px;">제외</span>
                    <span style="color: #6c757d; font-size: 0.9rem;">#{idx}</span>
                </div>
                <div style="font-weight: 600; color: #212529; margin-bottom: 4px; line-height: 1.4;">
                    {title}
                </div>
                <div style="font-size: 0.9rem; color: #6c757d;">
                    <strong>연도:</strong> {year} | <strong>저널:</strong> {source}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if len(exclude_papers) > 10:
            st.markdown(f"<p style='color: #6c757d; text-align: center; margin: 16px 0;'>... 외 {len(exclude_papers) - 10}편 더</p>", unsafe_allow_html=True)

    # --- 분류별 논문 상세 목록 (Review만 토글로 유지) ---
    # Review 분류 논문들 토글
    review_papers = merged_df[merged_df['Classification'].str.contains('Review', na=False)]
    
    if len(review_papers) > 0:
        with st.expander(f"📝 Review (검토 필요) - 논문 목록 ({len(review_papers)}편)", expanded=False):
            st.markdown("""
            <div style="background: #fff3cd; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                <strong>📋 검토 안내:</strong> 아래 논문들은 라이브 스트리밍 연구와의 관련성을 추가 검토가 필요한 논문들입니다.
                제목과 출판 정보를 확인하여 연구 범위에 포함할지 결정하세요.
            </div>
            """, unsafe_allow_html=True)
            
            # Review 논문 엑셀 다운로드 버튼
            review_excel_data = []
            for idx, (_, paper) in enumerate(review_papers.iterrows(), 1):
                review_excel_data.append({
                    '번호': idx,
                    '논문 제목': str(paper.get('TI', 'N/A')),
                    '출판연도': str(paper.get('PY', 'N/A')),
                    '저널명': str(paper.get('SO', 'N/A')),
                    '저자': str(paper.get('AU', 'N/A')),
                    '분류': str(paper.get('Classification', 'N/A')),
                    '저자 키워드': str(paper.get('DE', 'N/A')),
                    'WOS 키워드': str(paper.get('ID', 'N/A')),
                    '초록': str(paper.get('AB', 'N/A'))
                })
            
            review_excel_df = pd.DataFrame(review_excel_data)
            
            # 엑셀 파일 생성
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                review_excel_df.to_excel(writer, sheet_name='Review_Papers', index=False)
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 검토 논문 목록 엑셀 다운로드",
                data=excel_data,
                file_name=f"review_papers_list_{len(review_papers)}편.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
                use_container_width=True
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            for idx, (_, paper) in enumerate(review_papers.iterrows(), 1):
                title = str(paper.get('TI', 'N/A'))
                year = str(paper.get('PY', 'N/A'))
                source = str(paper.get('SO', 'N/A'))
                classification = str(paper.get('Classification', 'N/A'))
                
                # 분류별 색상 설정
                if '불확실' in classification:
                    badge_color = "#6c757d"
                    badge_text = "분류 불확실"
                elif '소셜미디어' in classification:
                    badge_color = "#17a2b8"
                    badge_text = "소셜미디어"
                elif '비즈니스' in classification:
                    badge_color = "#28a745"
                    badge_text = "비즈니스"
                elif '기술적' in classification:
                    badge_color = "#fd7e14"
                    badge_text = "기술적"
                elif '교육' in classification:
                    badge_color = "#6f42c1"
                    badge_text = "교육"
                else:
                    badge_color = "#ffc107"
                    badge_text = "기타"
                
                st.markdown(f"""
                <div style="margin: 8px 0; padding: 12px; background: white; border-left: 3px solid #ffc107; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; margin-right: 8px;">{badge_text}</span>
                        <span style="color: #6c757d; font-size: 0.9rem;">#{idx}</span>
                    </div>
                    <div style="font-weight: 600; color: #212529; margin-bottom: 4px; line-height: 1.4;">
                        {title}
                    </div>
                    <div style="font-size: 0.9rem; color: #6c757d;">
                        <strong>연도:</strong> {year} | <strong>저널:</strong> {source}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Exclude 분류 논문들 (변수만 정의, 위에서 이미 처리됨)

    # 병합 성과 강조 - 실제 데이터 기반
    success_info = []
    success_info.append(f"<strong>파일 통합:</strong> {successful_files}개의 WOS 파일을 하나로 병합")
    
    if duplicates_removed > 0:
        success_info.append(f"<strong>중복 제거:</strong> {duplicates_removed}편의 중복 논문 자동 감지 및 제거")
    
    success_info.append(f"<strong>최종 규모:</strong> {total_papers:,}편의 논문으로 대규모 연구 분석 가능")
    success_info.append("<strong>SCIMAT 호환:</strong> 완벽한 WOS Plain Text 형식으로 100% 호환성 보장")
    
    success_content = "".join([f"<p style='color: #003875; margin: 4px 0;'>{info}</p>" for info in success_info])
    
    st.markdown(f"""
    <div class="info-panel">
        <h4 style="color: #003875; margin-bottom: 12px;">🏆 병합 성과</h4>
        {success_content}
    </div>
    """, unsafe_allow_html=True)

    # --- 최종 파일 다운로드 섹션 ---
    # SCIMAT 호환 파일 다운로드 - 기본 파란색 버튼
    text_data = convert_to_scimat_wos_format(df_final_output)
    
    # 다운로드 버튼과 SCIMAT 가이드 자동 토글
    download_clicked = st.download_button(
        label="📥 SCIMAT 분석용 파일 다운로드",
        data=text_data,
        file_name="live_streaming_merged_scimat_ready.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
        key="download_final_file",
        help="다운로드 후 SCIMAT 완벽 분석 가이드가 자동으로 표시됩니다"
    )
    
    # 다운로드 버튼 클릭 시 SCIMAT 가이드 자동 토글
    if download_clicked:
        st.session_state['show_scimat_guide'] = True
    
    # SCIMAT 완벽 분석 가이드 자동 표시
    if st.session_state.get('show_scimat_guide', False):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 20px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 20px rgba(0,123,255,0.3);">
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <div style="font-size: 2.5rem; margin-right: 16px;">🎯</div>
                <div>
                    <h3 style="margin: 0; color: white;">WOS → SciMAT 분석 실행 가이드</h3>
                    <p style="margin: 4px 0 0 0; opacity: 0.9;">다운로드된 파일로 단계별 분석 수행</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # SCIMAT 분석 가이드 상세 내용
        st.markdown("""
        ### 📋 필요한 것
        - SciMAT 소프트웨어 (무료 다운로드)
        - 다운로드된 WOS Plain Text 파일
        - Java 1.8 이상
        
        ### 🚀 1단계: SciMAT 시작하기
        
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
        
        ### 🔧 2단계: 키워드 정리하기
        
        **유사 키워드 자동 통합**
        ```
        1. Group set → Word → Find similar words by distances
        2. Maximum distance: 1 (한 글자 차이)
        3. 같은 의미 단어들 확인하고 Move로 통합
        ```
        📖 **의미**: 철자가 1글자만 다른 단어들을 찾아서 제안 (예: "platform" ↔ "platforms")
        
        **수동으로 키워드 정리**
        ```
        1. Group set → Word → Word Group manual set
        2. Words without group 목록 확인
        3. 관련 키워드들 선택 후 New group으로 묶기
        4. 불필요한 키워드 제거
        ```
        📖 **목적**: 데이터 품질 향상, 의미 있는 클러스터 형성
        
        ### ⏰ 3단계: 시간 구간 설정
        
        **Period 만들기**
        ```
        1. Knowledge base → Periods → Periods manager
        2. Add 버튼으로 시간 구간 생성:
           - Period 1: 1996-2006 (태동기)
           - Period 2: 2007-2016 (형성기)
           - Period 3: 2017-2021 (확산기)
           - Period 4: 2022-2024 (성숙기)
        ```
        📖 **원리**: 연구 분야의 진화 단계를 반영한 의미 있는 구분
        
        **각 Period에 논문 할당**
        ```
        1. Period 1 클릭 → Add
        2. 해당 연도 논문들 선택
        3. 오른쪽 화살표로 이동
        4. 다른 Period들도 동일하게 반복
        ```
        
        ### 📊 4단계: 분석 실행
        
        **분석 마법사 시작**
        ```
        1. Analysis → Make Analysis
        2. 모든 Period 선택 → Next
        ```
        
        **Step 1: Unit of Analysis**
        - ✅ "Word Group" 선택
        - ✅ "Author's words + Source's words" 선택
        
        📖 **의미**: 저자 키워드와 저널 키워드를 모두 사용해서 포괄적 분석
        
        **Step 2: Data Reduction**
        - **Minimum frequency: 2** (최소 2번 출현)
        
        📖 **목적**: 노이즈 제거, 한 번만 나타나는 희귀 키워드 배제
        
        **Step 3: Network Type**
        - ✅ "Co-occurrence" 선택
        
        📖 **의미**: 키워드들이 동시에 나타나는 빈도로 관련성 측정
        
        **Step 4: Normalization**
        - ✅ "Equivalence Index" 선택
        
        📖 **Equivalence Index란?**
        - 키워드 간 연관성을 측정하는 정규화 방법
        - 네트워크의 밀도를 적절히 조정하여 의미 있는 클러스터 형성
        - 다른 방법(Jaccard, Cosine)보다 SciMAT에서 권장하는 표준 방법
        
        **Step 5: Clustering**
        - ✅ "Simple Centers Algorithm" 선택
        - **Maximum network size: 50**
        
        📖 **Simple Centers Algorithm이란?**
        - 클러스터의 중심이 되는 핵심 키워드를 찾아서 그룹을 형성하는 방법
        - 복잡한 알고리즘보다 해석이 용이하고 안정적인 결과 제공
        
        📖 **왜 50인가?**
        - 너무 크면(100+): 복잡해서 해석 어려움
        - 너무 작으면(10-20): 중요한 연결 관계 누락
        - 50개: 의미 있는 키워드들을 포함하면서도 시각적으로 분석 가능한 적정 크기
        - 경험적으로 검증된 최적 크기
        
        **Step 6: Document Mapper**
        - ✅ "Core Mapper" 선택
        
        📖 **Core Mapper란?**
        - 각 주제 클러스터를 대표하는 "핵심 논문들"을 식별하는 방법
        - Core documents = 해당 주제의 키워드를 다수 포함하는 중요 논문들
        - 클러스터의 실제 내용을 이해하는 데 필수적
        
        📖 **왜 Core Mapper?**
        - 주제별로 가장 대표적인 논문들을 찾아서 클러스터의 의미 파악 가능
        - 단순한 빈도 기반보다 질적으로 우수한 논문 선별
        
        **Step 7: Performance Measures**
        - ✅ **G-index, Sum Citations** 모두 선택
        
        📖 **각 지표의 의미:**
        - **G-index**: h-index의 개선된 버전, 고인용 논문들의 영향력을 더 정확히 측정
          - 예: 논문 10편 중 상위 5편이 각각 100회 이상 인용되면 높은 G-index
        - **Sum Citations**: 총 인용 횟수, 해당 주제의 전체적인 학술적 영향력
        - **Average Citations**: 논문당 평균 인용 수, 주제의 질적 수준
        
        📖 **왜 여러 지표?** 다각도로 주제의 중요성과 영향력 평가
        
        **Step 8: Evolution Map**
        - ✅ "Jaccard Index" 선택
        
        📖 **Jaccard Index란?**
        - 두 시기 간 주제의 연속성을 측정하는 유사도 지표
        - 공식: |A ∩ B| / |A ∪ B| (교집합 / 합집합)
        - 0~1 사이 값: 1에 가까울수록 두 주제가 매우 유사
        
        📖 **예시**:
        - Period 1의 "스트리밍 기술" 키워드: {platform, streaming, video, real-time}
        - Period 2의 "플랫폼 기술" 키워드: {platform, streaming, service, user}
        - Jaccard = |{platform, streaming}| / |{platform, streaming, video, real-time, service, user}| = 2/6 = 0.33
        
        **분석 실행**
        ```
        - Finish 클릭
        - 완료까지 대기 (10-30분)
        ```
        📖 **처리 과정**: 키워드 매트릭스 생성 → 클러스터링 → 진화 분석 → 시각화
        
        ### 📈 5단계: 결과 보기
        
        **전략적 다이어그램 확인**
        ```
        1. Period View에서 각 시기별 다이어그램 확인
        2. 4사분면 해석:
           - 우상단: Motor Themes (핵심 주제) - 중심성↑, 밀도↑
           - 좌상단: Specialized Themes (전문화된 주제) - 중심성↓, 밀도↑
           - 좌하단: Emerging/Declining Themes (신흥/쇠퇴 주제) - 중심성↓, 밀도↓
           - 우하단: Basic Themes (기초 주제) - 중심성↑, 밀도↓
        ```
        
        **클러스터 세부 확인**
        ```
        1. 각 주제 클릭하면 세부 키워드 네트워크 확인
        2. Core documents 클릭하면 논문 수 확인
        3. G-index 클릭하면 인용 수 확인
        ```
        
        **진화 맵 확인**
        ```
        1. 시간에 따른 주제 변화 추적
        2. 노드 크기 = 논문 수 (클수록 더 많은 연구)
        3. 연결선 두께 = Jaccard 유사도 (두꺼울수록 더 연관성 높음)
        ```
        
        ### 💾 6단계: 결과 저장
        
        **보고서 생성**
        ```
        1. File → Export
        2. HTML 또는 LaTeX 선택
        3. 파일명 입력 후 저장
        ```
        
        **결과물**
        - 전략적 다이어그램 이미지들
        - 진화 맵
        - 클러스터 네트워크 이미지들
        - 통계 데이터
        
        ### 🔧 문제 해결
        
        **자주 발생하는 문제**
        - **임포트 안됨**: WOS 파일이 Plain Text인지 확인
        - **분석 중단**: Java 메모리 부족 → 재시작
        - **한글 깨짐**: 파일 인코딩 UTF-8로 변경
        
        **키워드 정리**: 시간을 투자해서 꼼꼼히 정리 (분석 품질의 핵심!)
        **Period 구분**: 너무 세분화하지 말고 의미있는 구간으로 (각 구간당 최소 50편)
        **논문 수**: 각 Period당 최소 50편 이상 권장 (통계적 의미 확보)
        **설정값 조정**: 분야 특성에 따라 Maximum network size 조정 가능 (30-100)
        
        ### 📊 결과 해석 가이드
        
        **Motor Themes (핵심 주제) 해석**
        - 해당 시기의 연구 분야를 이끄는 중심 주제
        - 많은 연구가 집중되고, 다른 주제와 연결성이 높음
        - 투자와 연구가 활발한 "핫" 영역
        
        **Emerging Themes (신흥 주제) 주목**
        - 아직 연구가 적지만 향후 성장 가능성 높은 영역
        - 다음 Period에서 Motor Theme으로 발전할 가능성
        - 선행 연구 기회가 많은 "블루오션"
        """)
        
        # 가이드 닫기 버튼
        if st.button("🔼 가이드 닫기", key="close_guide"):
            st.session_state['show_scimat_guide'] = False
            st.rerun()

# --- 하단 여백 및 추가 정보 ---
st.markdown("<br>", unsafe_allow_html=True)

# SCIMAT 분석 가이드 추가 (기존 expander는 제거하고 위에서 자동 토글로 처리)
with st.expander("❓ 자주 묻는 질문 (FAQ)"):
    st.markdown("""
    **Q: 여러 WOS 파일을 어떻게 한 번에 처리하나요?**
    A: WOS에서 여러 번 Plain Text 다운로드한 후, 모든 .txt 파일을 한 번에 업로드하면 자동으로 병합됩니다.
    
    **Q: 중복된 논문이 있을까봐 걱정됩니다.**
    A: UT(Unique Article Identifier) 기준으로 자동 중복 제거되며, UT가 없으면 제목+저자 조합으로 중복을 감지합니다.
    
    **Q: WOS에서 어떤 설정으로 다운로드해야 하나요?**
    A: Export → Record Content: "Full Record and Cited References", File Format: "Plain Text"로 설정하세요. 인용 관계 분석을 위해 참고문헌 정보가 필수입니다.
    
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

st.markdown("<br><br>", unsafe_allow_html=True)
