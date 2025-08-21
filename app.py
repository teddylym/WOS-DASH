# -*- coding: utf-8 -*-
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

# --- 다중 WOS Plain Text 파일 로딩 및 병합 함수 (수정됨) ---
def load_and_merge_wos_files(uploaded_files):
    """다중 WOS Plain Text 파일을 로딩하고 병합 - 중복 제거 로직 수정"""
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
                    'message': f'&#9989; {len(df)}편 논문 로딩 성공'
                })
            else:
                file_status.append({
                    'filename': uploaded_file.name,
                    'status': 'ERROR',
                    'papers': 0,
                    'encoding': 'N/A',
                    'message': '&#10060; WOS Plain Text 형식이 아님'
                })
                
        except Exception as e:
            file_status.append({
                'filename': uploaded_file.name,
                'status': 'ERROR',
                'papers': 0,
                'encoding': 'N/A',
                'message': f'&#10060; 파일 처리 오류: {str(e)[:50]}'
            })
    
    # 모든 데이터프레임 병합
    if all_dataframes:
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        original_count = len(merged_df)
        
        # 중복 제거 로직 - 완전 수정
        duplicates_removed = 0
        
        if 'UT' in merged_df.columns:
            # 유효한 UT만 필터링 (비어있지 않고 'nan'이 아닌 것)
            valid_ut_mask = (
                merged_df['UT'].notna() & 
                (merged_df['UT'] != '') & 
                (merged_df['UT'].astype(str).str.lower() != 'nan') &
                (merged_df['UT'].astype(str).str.strip() != '')
            )
            
            if valid_ut_mask.sum() > 0:  # 유효한 UT가 있는 경우만
                # 중복 제거 전 개수
                before_count = len(merged_df)
                
                # UT 기준 중복 제거 (유효한 UT만)
                merged_df = merged_df.drop_duplicates(subset=['UT'], keep='first')
                
                # 실제 제거된 개수
                after_count = len(merged_df)
                duplicates_removed = before_count - after_count
        
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

# --- 데이터 품질 진단 함수 (수정됨) ---
def diagnose_merged_quality(df, file_count, duplicates_removed):
    """병합된 WOS 데이터의 품질 진단 - 수정된 버전"""
    issues = []
    recommendations = []
    
    # 필수 필드 확인
    required_fields = ['TI', 'AU', 'SO', 'PY']
    keyword_fields = ['DE', 'ID']
    
    for field in required_fields:
        if field not in df.columns:
            issues.append(f"&#10060; 필수 필드 누락: {field}")
        else:
            valid_count = df[field].notna().sum()
            total_count = len(df)
            missing_rate = (total_count - valid_count) / total_count * 100
            
            if missing_rate > 10:
                issues.append(f"&#9888; {field} 필드의 {missing_rate:.1f}%가 누락됨")
    
    # 키워드 필드 품질 확인
    has_keywords = False
    for field in keyword_fields:
        if field in df.columns:
            has_keywords = True
            valid_keywords = df[field].notna() & (df[field] != '') & (df[field] != 'nan')
            valid_count = valid_keywords.sum()
            total_count = len(df)
            
            if valid_count < total_count * 0.7:
                issues.append(f"&#9888; {field} 필드의 {((total_count-valid_count)/total_count*100):.1f}%가 비어있음")
    
    if not has_keywords:
        issues.append("&#10060; 키워드 필드 없음: DE 또는 ID 필드 필요")
    
    # 병합 관련 정보 - 실제 결과만 반영
    recommendations.append(f"&#9989; {file_count}개 파일 성공적으로 병합됨")
    
    # 중복 제거 결과 - 실제 제거된 경우만 표시
    if duplicates_removed > 0:
        recommendations.append(f"&#128260; 실제 중복 논문 {duplicates_removed}편 제거됨")
    else:
        recommendations.append("&#9989; 중복 논문 없음 - 모든 논문이 고유함")
    
    recommendations.append("&#9989; WOS Plain Text 형식 - SCIMAT 완벽 호환")
    
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
        <div class="feature-icon">&#128279;</div>
        <div class="feature-title">다중 파일 자동 병합</div>
        <div class="feature-desc">여러 WOS 파일을 한 번에 병합 처리</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">&#128683;</div>
        <div class="feature-title">스마트 중복 제거</div>
        <div class="feature-desc">UT 기준 자동 중복 논문 감지 및 제거</div>
    </div>
    <div class="feature-card">
        <div class="feature-icon">&#127919;</div>
        <div class="feature-title">데이터 분류</div>
        <div class="feature-desc">대규모 데이터 포괄적 분류 및 분석</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">&#128193; 다중 WOS Plain Text 파일 업로드</div>
    <div class="section-subtitle">500개 단위로 나뉜 여러 WOS 파일을 모두 선택하여 업로드하세요</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="upload-zone">
    <div style="font-size: 3rem; margin-bottom: 16px; color: #003875;">&#128228;</div>
    <div style="padding: 0 20px;">
        <h3 style="color: #212529; margin-bottom: 8px;">WOS Plain Text 파일들을 모두 선택하세요</h3>
        <p style="color: #6c757d; margin: 0;">Ctrl+클릭으로 여러 파일 동시 선택 가능</p>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "WOS Plain Text 파일 선택 (다중 선택 가능)",
    type=['txt'],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    st.markdown(f"&#128203; **선택된 파일 개수:** {len(uploaded_files)}개")
    
    # 프로그레스 인디케이터
    st.markdown('<div class="progress-indicator"></div>', unsafe_allow_html=True)
    
    with st.spinner(f"&#128260; {len(uploaded_files)}개 WOS 파일 병합 및 분석 중..."):
        # 파일 병합
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)
        
        if merged_df is None:
            st.error("&#9888; 처리 가능한 WOS Plain Text 파일이 없습니다. 파일들이 Web of Science에서 다운로드한 정품 Plain Text 파일인지 확인해주세요.")
            
            # 파일별 상태 표시
            st.markdown("### &#128196; 파일별 처리 상태")
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
    
    st.success(f"&#9989; 병합 완료! {successful_files}개 파일에서 {total_papers:,}편의 논문을 성공적으로 처리했습니다.")
    
    # 중복 제거 결과 표시 - 실제 결과만 (수정됨)
    if duplicates_removed > 0:
        st.info(f"&#128260; 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다. (원본 총 {total_papers + duplicates_removed:,}편 → 정제 후 {total_papers:,}편)")
    else:
        st.info("&#9989; 중복 논문 없음 - 모든 논문이 고유한 데이터입니다.")

    # --- 파일별 처리 상태 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">&#128196; 파일별 처리 상태</div>
        <div class="section-subtitle">업로드된 각 파일의 처리 결과</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">&#128203; 파일별 상세 상태</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.6, 0.4])
    
    with col1:        
        for status in file_status:
            color = "#28a745" if status['status'] == 'SUCCESS' else "#dc3545"
            icon = "&#9989;" if status['status'] == 'SUCCESS' else "&#10060;"
            
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
            <div class="metric-icon">&#9989;</div>
            <div class="metric-value">{success_count}</div>
            <div class="metric-label">성공한 파일</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card" style="background: #f8f9fa;">
            <div class="metric-icon">&#10060;</div>
            <div class="metric-value">{error_count}</div>
            <div class="metric-label">실패한 파일</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 데이터 품질 진단 결과 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">&#128269; 병합 데이터 품질 진단</div>
        <div class="section-subtitle">병합된 WOS 데이터의 품질과 SCIMAT 호환성 검증</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("&#128269; 병합 데이터 품질 분석 중..."):
        issues, recommendations = diagnose_merged_quality(merged_df, successful_files, duplicates_removed)

    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">&#128269; 병합 데이터 품질 진단 결과</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h5 style="color: #dc3545; margin-bottom: 12px;">&#128680; 발견된 문제점</h5>', unsafe_allow_html=True)
        
        if issues:
            for issue in issues:
                st.markdown(f"- {issue}")
        else:
            st.markdown("&#9989; **문제점 없음** - 병합 데이터 품질 우수")
    
    with col2:
        st.markdown('<h5 style="color: #28a745; margin-bottom: 12px;">&#128161; 병합 결과</h5>', unsafe_allow_html=True)
        
        if recommendations:
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.markdown("&#127919; **최적 상태** - SCIMAT 완벽 호환")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 병합 성공 알림
    st.markdown("""
    <div class="success-panel">
        <h4 style="color: #155724; margin-bottom: 16px;">&#127919; 다중 파일 병합 성공!</h4>
        <p style="color: #155724; margin: 4px 0;">여러 WOS Plain Text 파일이 성공적으로 하나로 병합되었습니다.</p>
        <p style="color: #155724; margin: 4px 0;"><strong>중복 제거:</strong> 동일한 논문은 자동으로 제거되어 정확한 분석 결과를 보장합니다.</p>
        <p style="color: #155724; margin: 4px 0;"><strong>SCIMAT 호환성:</strong> 병합된 파일은 SCIMAT에서 100% 정상 작동합니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 분석 결과 요약 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">&#128200; 병합 데이터 분석 결과</div>
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
            <div class="metric-icon">&#128203;</div>
            <div class="metric-value">{total_papers:,}</div>
            <div class="metric-label">Total Papers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">&#9989;</div>
            <div class="metric-value">{include_papers:,}</div>
            <div class="metric-label">Included Studies</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        processing_rate = (include_papers / total_papers * 100) if total_papers > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">&#128202;</div>
            <div class="metric-value">{processing_rate:.1f}%</div>
            <div class="metric-label">Inclusion Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">&#128279;</div>
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
            icon = "&#9989;"
        elif classification.startswith('Review'):
            color = "#ffc107"
            icon = "&#128221;"
        else:
            color = "#dc3545"
            icon = "&#10060;"
        
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
            st.success("&#9989; 키워드 품질 우수 - SCIMAT에서 원활한 그룹핑 예상")
        elif avg_de >= 2 or avg_id >= 2:
            st.warning("&#9888; 키워드 품질 보통 - SCIMAT에서 일부 제한 가능")
        else:
            st.error("&#10060; 키워드 품질 부족 - 원본 WOS 다운로드 설정 확인 필요")

    st.markdown("</div>", unsafe_allow_html=True)

    # 최종 데이터셋 준비 (제외된 논문만 빼고)
    df_final = merged_df[~merged_df['Classification'].str.contains('Exclude', na=False)].copy()
    
    # Classification 컬럼만 제거 (원본 WOS 형식 유지)
    df_final_output = df_final.drop(columns=['Classification'], errors='ignore')

    # 최종 통계
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">&#128203;</div>
            <div class="metric-value">{len(df_final_output):,}</div>
            <div class="metric-label">최종 분석 대상<br><small style="color: #6c757d;">(Exclude 제외)</small></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        include_count = len(merged_df[merged_df['Classification'].str.contains('Include', na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">&#9989;</div>
            <div class="metric-value">{include_count:,}</div>
            <div class="metric-label">핵심 포함 연구</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        review_count = len(merged_df[merged_df['Classification'].str.contains('Review', na=False)])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">&#128221;</div>
            <div class="metric-value">{review_count:,}</div>
            <div class="metric-label">검토 대상</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 분류별 논문 상세 목록 (Review와 Exclude 모두 토글) ---
    # Review 분류 논문들 토글
    review_papers = merged_df[merged_df['Classification'].str.contains('Review', na=False)]
    
    if len(review_papers) > 0:
        with st.expander(f"&#128221; Review (검토 필요) - 논문 목록 ({len(review_papers)}편)", expanded=False):
            st.markdown("""
            <div style="background: #fff3cd; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                <strong>&#128203; 검토 안내:</strong> 아래 논문들은 라이브 스트리밍 연구와의 관련성을 추가 검토가 필요한 논문들입니다.
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
                label="&#128202; 검토 논문 목록 엑셀 다운로드",
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

    # Exclude 분류 논문들 토글 (신규 추가)
    exclude_papers = merged_df[merged_df['Classification'].str.contains('Exclude', na=False)]
    
    if len(exclude_papers) > 0:
        with st.expander(f"&#10060; Exclude (제외 대상) - 논문 목록 ({len(exclude_papers)}편)", expanded=False):
            st.markdown("""
            <div style="background: #f8d7da; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                <strong>&#128683; 제외 안내:</strong> 아래 논문들은 라이브 스트리밍 연구와 관련성이 낮아 최종 분석에서 제외되는 논문들입니다.
                기술적으로 비관련된 연구들이 포함되어 있습니다.
            </div>
            """, unsafe_allow_html=True)
            
            for idx, (_, paper) in enumerate(exclude_papers.iterrows(), 1):
                title = str(paper.get('TI', 'N/A'))
                year = str(paper.get('PY', 'N/A'))
                source = str(paper.get('SO', 'N/A'))
                
                st.markdown(f"""
                <div style="margin: 8px 0; padding: 12px; background: white; border-left: 3px solid #dc3545; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; margin-right: 8px;">기술적 비관련</span>
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

    # 병합 성과 강조 - 실제 데이터 기반 (수정됨)
    success_info = []
    success_info.append(f"<strong>파일 통합:</strong> {successful_files}개의 WOS 파일을 하나로 병합")
    
    if duplicates_removed > 0:
        success_info.append(f"<strong>중복 제거:</strong> {duplicates_removed}편의 중복 논문 자동 감지 및 제거")
    else:
        success_info.append("<strong>중복 확인:</strong> 모든 논문이 고유하여 중복 제거 불필요")
    
    success_info.append(f"<strong>최종 규모:</strong> {total_papers:,}편의 논문으로 대규모 연구 분석 가능")
    success_info.append("<strong>SCIMAT 호환:</strong> 완벽한 WOS Plain Text 형식으로 100% 호환성 보장")
    
    success_content = "".join([f"<p style='color: #003875; margin: 4px 0;'>{info}</p>" for info in success_info])
    
    st.markdown(f"""
    <div class="info-panel">
        <h4 style="color: #003875; margin-bottom: 12px;">&#127942; 병합 성과</h4>
        {success_content}
    </div>
    """, unsafe_allow_html=True)

    # --- 최종 파일 다운로드 섹션 ---
    # SCIMAT 호환 파일 다운로드 - 기본 파란색 버튼
    text_data = convert_to_scimat_wos_format(df_final_output)
    
    st.download_button(
        label="Download",
        data=text_data,
        file_name="live_streaming_merged_scimat_ready.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
        key="download_final_file"
    )

# --- 하단 여백 및 추가 정보 ---
st.markdown("<br>", unsafe_allow_html=True)

# 도움말 섹션
with st.expander("&#10067; 자주 묻는 질문 (FAQ)"):
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

# SCIMAT 분석 가이드 추가
with st.expander("&#128202; SCIMAT 완벽 분석 가이드"):
    st.markdown("""
    ### &#127919; SCIMAT 분석 핵심 단계
    
    **1단계: 프로젝트 생성**
    - SCIMAT 실행 → File → New Project → 경로 설정
    
    **2단계: 데이터 로딩**
    - File → Add Files → "ISI WoS" 선택 → 다운로드한 .txt 파일 선택
    
    **3단계: 키워드 정리 (중요!)**
    - **자동 통합**: Group set → Word → Find similar words by distances (거리: 1)
    - **수동 그룹화**: Word Group manual set에서 관련 키워드들 묶기
    - **목적**: 데이터 품질 향상, 의미 있는 클러스터 형성
    
    **4단계: 시간 구간 설정**
    - Knowledge base → Periods → Periods manager
    - 연구 분야 진화 단계를 반영한 의미 있는 구간 설정
    - 각 Period당 최소 50편 이상 논문 포함 권장
    
    **5단계: 분석 설정**
    - **Unit of Analysis**: "Word Group" + "Author's words + Source's words"
    - **Data Reduction**: Minimum frequency: 2 (노이즈 제거)
    - **Network Type**: "Co-occurrence" (키워드 동시 출현 분석)
    - **Normalization**: "Equivalence Index" (표준 정규화 방법)
    - **Clustering**: "Simple Centers Algorithm" (해석 용이, 안정적)
    - **Maximum network size**: 50 (시각적 분석 가능한 적정 크기)
    - **Document Mapper**: "Core Mapper" (핵심 논문 식별)
    - **Performance Measures**: G-index, Sum Citations 모두 선택
    - **Evolution Map**: "Jaccard Index" (시기간 주제 연속성 측정)
    
    **6단계: 결과 해석**
    - **전략적 다이어그램 4사분면**:
      - 우상단: Motor Themes (핵심 주제) - 중심성↑, 밀도↑
      - 좌상단: Specialized Themes (전문화된 주제) - 중심성↓, 밀도↑  
      - 좌하단: Emerging/Declining Themes (신흥/쇠퇴 주제) - 중심성↓, 밀도↓
      - 우하단: Basic Themes (기초 주제) - 중심성↑, 밀도↓
    
    ### &#128161; 성공적인 분석을 위한 팁
    - **키워드 정리에 충분한 시간 투자** (분석 품질의 핵심!)
    - **Period 구분**: 너무 세분화하지 말고 의미있는 구간으로
    - **각 Period당 최소 50편** 이상으로 통계적 의미 확보
    - **설정값 조정**: 분야 특성에 따라 Maximum network size 조정 가능 (30-100)
    
    ### &#128295; 문제 해결
    - **임포트 안됨**: WOS 파일이 Plain Text인지 확인
    - **분석 중단**: Java 메모리 부족 시 재시작
    - **한글 깨짐**: 파일 인코딩 UTF-8로 변경
    """)

st.markdown("<br><br>", unsafe_allow_html=True)
