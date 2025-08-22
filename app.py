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

# --- 첨부파일 스타일 완전 복제 CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: #f5f7fa;
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    /* 메인 웰컴 카드 - 첨부파일 완전 복제 */
    .main-welcome-card {
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
        border-radius: 24px;
        padding: 48px 40px;
        color: white;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 16px 40px rgba(74, 144, 226, 0.3);
    }
    
    .main-welcome-card::before {
        content: '';
        position: absolute;
        top: -30%;
        right: -5%;
        width: 150px;
        height: 150px;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 50%;
        z-index: 1;
    }
    
    .welcome-title {
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 8px;
        z-index: 2;
        position: relative;
        line-height: 1.2;
    }
    
    .welcome-subtitle {
        font-size: 1.4rem;
        font-weight: 400;
        opacity: 0.9;
        margin-bottom: 24px;
        z-index: 2;
        position: relative;
    }
    
    .card-link {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 12px 20px;
        display: inline-block;
        font-weight: 600;
        font-size: 1rem;
        z-index: 2;
        position: relative;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .card-link:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    
    .card-icon {
        position: absolute;
        top: 40px;
        right: 40px;
        width: 80px;
        height: 50px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        z-index: 2;
    }
    
    /* 결제예정금액 스타일 메트릭 카드 */
    .payment-style-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 24px;
        margin: 32px 0;
    }
    
    .payment-card {
        background: white;
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e8ecf1;
    }
    
    .payment-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 24px;
        border-bottom: 2px solid #f1f3f5;
        padding-bottom: 12px;
    }
    
    .payment-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 18px 0;
        border-bottom: 1px solid #f8f9fa;
    }
    
    .payment-item:last-child {
        border-bottom: none;
    }
    
    .payment-label {
        font-size: 1rem;
        color: #6c757d;
        font-weight: 400;
        line-height: 1.4;
    }
    
    .payment-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2c3e50;
    }
    
    .payment-value.large {
        font-size: 1.8rem;
        color: #4a90e2;
    }
    
    /* 상태 카드들 - 3개 그리드 */
    .status-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin: 24px 0;
    }
    
    .status-card {
        background: white;
        border-radius: 16px;
        padding: 24px 20px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        border: 1px solid #e8ecf1;
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    
    .status-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
        display: block;
    }
    
    .status-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    
    .status-desc {
        font-size: 0.9rem;
        color: #6c757d;
        line-height: 1.4;
    }
    
    /* 섹션 헤더 */
    .section-header {
        background: white;
        border-radius: 16px;
        padding: 24px 32px;
        margin: 32px 0 16px 0;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
        border-left: 4px solid #4a90e2;
    }
    
    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 0;
    }
    
    .section-subtitle {
        font-size: 1rem;
        color: #6c757d;
        margin: 8px 0 0 0;
        font-weight: 400;
    }
    
    /* 차트 컨테이너 */
    .chart-container {
        background: white;
        border-radius: 20px;
        padding: 32px;
        margin: 24px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e8ecf1;
    }
    
    .chart-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 24px;
        padding-bottom: 12px;
        border-bottom: 2px solid #f1f3f5;
    }
    
    /* 결과 패널 */
    .result-panel {
        background: #f8fffe;
        border: 1px solid #d4edda;
        border-radius: 16px;
        padding: 24px;
        margin: 24px 0;
        border-left: 4px solid #28a745;
    }
    
    .result-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #155724;
        margin-bottom: 16px;
    }
    
    .result-content {
        color: #155724;
        line-height: 1.6;
    }
    
    /* 다운로드 섹션 */
    .download-section {
        background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        color: white;
        margin: 32px 0;
    }
    
    .download-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    
    .download-desc {
        font-size: 1rem;
        opacity: 0.9;
        margin-bottom: 24px;
    }
    
    /* 최근 이용내역 스타일 */
    .recent-usage-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        margin: 32px 0;
    }
    
    .usage-card {
        background: white;
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e8ecf1;
    }
    
    .usage-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 24px;
        border-bottom: 2px solid #f1f3f5;
        padding-bottom: 12px;
    }
    
    .usage-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
    }
    
    .usage-detail {
        display: flex;
        flex-direction: column;
    }
    
    .usage-name {
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 4px;
        font-size: 1rem;
    }
    
    .usage-date {
        font-size: 0.9rem;
        color: #6c757d;
    }
    
    .usage-amount {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2c3e50;
    }
    
    /* 보너스 포인트 스타일 */
    .bonus-center {
        text-align: center;
        padding: 32px 0;
    }
    
    .bonus-points {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4a90e2;
        margin-bottom: 8px;
    }
    
    .bonus-buttons {
        display: flex;
        justify-content: space-around;
        margin-top: 24px;
    }
    
    .bonus-button {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
        font-size: 0.9rem;
        color: #6c757d;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .bonus-button:hover {
        background: #e9ecef;
    }
    
    /* 서비스 그리드 */
    .service-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin: 24px 0;
    }
    
    .service-item {
        display: flex;
        align-items: center;
        padding: 12px 0;
    }
    
    .service-icon {
        margin-right: 12px;
        font-size: 1.2rem;
    }
    
    .service-name {
        font-weight: 500;
        color: #2c3e50;
    }
    
    /* 추천 서비스 카드 */
    .recommend-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin: 24px 0;
    }
    
    .recommend-card {
        background: #f8fffe;
        border: 1px solid #d4edda;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .recommend-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .recommend-icon {
        background: linear-gradient(135deg, #4a90e2, #357abd);
        color: white;
        border-radius: 8px;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
        font-size: 1.2rem;
    }
    
    .recommend-title {
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 8px;
        font-size: 0.95rem;
    }
    
    .recommend-desc {
        font-size: 0.85rem;
        color: #6c757d;
        line-height: 1.4;
    }
    
    /* 부가서비스 스타일 */
    .addon-service {
        display: flex;
        align-items: center;
        margin-bottom: 16px;
        padding: 16px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    .addon-status {
        background: #f0f0f0;
        border-radius: 8px;
        padding: 8px 12px;
        margin-right: 12px;
        font-size: 0.85rem;
        color: #666;
    }
    
    .addon-status.active {
        background: #4a90e2;
        color: white;
    }
    
    .addon-name {
        font-weight: 600;
        color: #2c3e50;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #4a90e2, #357abd);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 32px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(74, 144, 226, 0.4);
    }
    
    /* 파일 상태 */
    .file-status {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        border-left: 4px solid #28a745;
        font-size: 0.95rem;
    }
    
    .file-status.error {
        border-left-color: #dc3545;
        background: #fff5f5;
    }
    
    /* 분류 결과 */
    .classification-box {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        border-left: 4px solid #28a745;
        font-size: 1.05rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    
    .classification-box.review {
        border-left-color: #ffc107;
    }
    
    .classification-box.exclude {
        border-left-color: #dc3545;
    }
    
    /* 반응형 */
    @media (max-width: 768px) {
        .payment-style-grid {
            grid-template-columns: 1fr;
        }
        
        .status-grid {
            grid-template-columns: 1fr;
        }
        
        .recent-usage-grid {
            grid-template-columns: 1fr;
        }
        
        .recommend-grid {
            grid-template-columns: 1fr;
        }
        
        .welcome-title {
            font-size: 2.2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 모든 함수들 (기존과 동일) ---
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
        original_count = len(merged_df)
        
        duplicates_removed = 0
        
        if 'UT' in merged_df.columns:
            ut_series = merged_df['UT'].copy()
            
            def is_meaningful_ut(value):
                if pd.isna(value):
                    return False
                str_value = str(value).strip()
                if len(str_value) == 0 or str_value.lower() in ['nan', 'none', 'null', '']:
                    return False
                if len(str_value) < 10:
                    return False
                if str_value.startswith('WOS:') or (len(str_value) >= 15 and any(c.isalnum() for c in str_value)):
                    return True
                return False
            
            meaningful_ut_mask = ut_series.apply(is_meaningful_ut)
            rows_with_meaningful_ut = merged_df[meaningful_ut_mask]
            rows_without_meaningful_ut = merged_df[~meaningful_ut_mask]
            
            if len(rows_with_meaningful_ut) > 1:
                before_dedup = len(rows_with_meaningful_ut)
                deduplicated_meaningful = rows_with_meaningful_ut.drop_duplicates(subset=['UT'], keep='first')
                after_dedup = len(deduplicated_meaningful)
                
                actual_duplicates = before_dedup - after_dedup
                
                if actual_duplicates > 0:
                    duplicates_removed = actual_duplicates
                    merged_df = pd.concat([deduplicated_meaningful, rows_without_meaningful_ut], ignore_index=True)
        
        if duplicates_removed == 0 and 'TI' in merged_df.columns:
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
            if len(parts) == 2:
                field_tag, field_value = parts
                current_field = field_tag
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

def classify_article(row):
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
    
    education_keywords = [
        'online education', 'e-learning', 'distance learning', 'remote learning',
        'virtual classroom', 'online teaching', 'digital learning', 'mooc',
        'educational technology', 'learning management system', 'blended learning',
        'medical education', 'nursing education', 'surgical training', 'clinical education',
        'telemedicine', 'telehealth', 'digital health', 'health education',
        'interactive learning', 'synchronous learning', 'real-time learning'
    ]
    
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
    
    if any(keyword in full_text for keyword in exclusion_keywords):
        return 'Exclude (기술적 비관련)'
    
    if any(keyword in full_text for keyword in core_streaming_keywords):
        return 'Include (핵심연구)'
    
    if any(keyword in full_text for keyword in business_commerce_keywords):
        digital_indicators = ['digital', 'online', 'internet', 'web', 'social media', 'platform', 'mobile', 'app', 'virtual', 'interactive']
        if any(indicator in full_text for indicator in digital_indicators):
            return 'Include (비즈니스 관련)'
    
    if any(keyword in full_text for keyword in education_keywords):
        online_indicators = ['online', 'digital', 'virtual', 'remote', 'distance', 'interactive', 'real-time', 'synchronous']
        if any(indicator in full_text for indicator in online_indicators):
            return 'Include (교육 관련)'
    
    if any(keyword in full_text for keyword in technical_keywords):
        live_indicators = ['live', 'real time', 'real-time', 'streaming', 'broadcast', 'interactive', 'synchronous', 'instant']
        if any(indicator in full_text for indicator in live_indicators):
            return 'Include (기술적 기반)'
    
    return 'Review (분류 불확실)'

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

# --- 메인 헤더 (첨부파일 완전 복제) ---
st.markdown("""
<div class="main-welcome-card">
    <div class="card-icon">💳</div>
    <div class="welcome-title">업데경님, 안녕하세요.</div>
    <div class="welcome-subtitle">THE 1</div>
    <div class="card-link">보유 카드 보기 ></div>
</div>
""", unsafe_allow_html=True)

# --- 기능 소개 카드들 (3개 그리드) ---
st.markdown("""
<div class="status-grid">
    <div class="status-card">
        <div class="status-icon">🔗</div>
        <div class="status-title">다중 파일 자동 병합</div>
        <div class="status-desc">여러 WOS 파일을 한 번에 병합 처리</div>
    </div>
    <div class="status-card">
        <div class="status-icon">🚫</div>
        <div class="status-title">스마트 중복 제거</div>
        <div class="status-desc">UT 기준 자동 중복 논문 감지 및 제거</div>
    </div>
    <div class="status-card">
        <div class="status-icon">🎯</div>
        <div class="status-title">데이터 분류</div>
        <div class="status-desc">대규모 데이터 포괄적 분류 및 분석</div>
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
    st.markdown(f"**📋 선택된 파일 개수:** {len(uploaded_files)}개")
    
    # 프로그레스 바
    progress_bar = st.progress(0)
    
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 분석 중..."):
        # 파일 병합
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)
        progress_bar.progress(50)
        
        if merged_df is None:
            st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다.")
            
            for status in file_status:
                status_class = "" if status['status'] == 'SUCCESS' else "error"
                st.markdown(f"""
                <div class="file-status {status_class}">
                    <strong>{status['filename']}</strong><br>
                    {status['message']}
                </div>
                """, unsafe_allow_html=True)
            st.stop()
        
        # 논문 분류 수행
        merged_df['Classification'] = merged_df.apply(classify_article, axis=1)
        progress_bar.progress(100)

    # 성공 메시지
    successful_files = len([s for s in file_status if s['status'] == 'SUCCESS'])
    total_papers = len(merged_df)
    
    st.success(f"✅ 병합 완료! {successful_files}개 파일에서 {total_papers:,}편의 논문을 성공적으로 처리했습니다.")
    
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다.")
    else:
        st.info("✅ 중복 논문 없음 - 모든 논문이 고유한 데이터입니다.")

    # --- 결제예정금액 스타일 메트릭 (첨부파일 완전 복제) ---
    include_papers = len(merged_df[merged_df['Classification'].str.contains('Include', na=False)])
    review_papers = len(merged_df[merged_df['Classification'].str.contains('Review', na=False)])
    exclude_papers = len(merged_df[merged_df['Classification'].str.contains('Exclude', na=False)])
    
    st.markdown(f"""
    <div class="payment-style-grid">
        <div class="payment-card">
            <div class="payment-title">이용가능금액</div>
            <div class="payment-item">
                <div class="payment-label">일시불/할부</div>
                <div class="payment-value large">{total_papers:,}편</div>
            </div>
            <div class="payment-item">
                <div class="payment-label">단기카드대출 (현금서비스)</div>
                <div class="payment-value">{include_papers:,}편</div>
            </div>
            <div class="payment-item">
                <div class="payment-label">장기카드대출 (카드론)</div>
                <div class="payment-value">{review_papers:,}편</div>
            </div>
        </div>
        <div class="payment-card">
            <div class="payment-title">결제예정금액</div>
            <div class="payment-item">
                <div class="payment-label">이번<br>오늘 입금 시</div>
                <div class="payment-value large">{successful_files:,}개</div>
            </div>
            <div class="payment-item">
                <div class="payment-label">다음<br>10월 10일</div>
                <div class="payment-value">{duplicates_removed:,}편</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 파일별 처리 상태 ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">📄 파일별 처리 상태</div>
        <div class="section-subtitle">업로드된 각 파일의 처리 결과</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📋 파일별 상세 상태</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:        
        for status in file_status:
            status_class = "" if status['status'] == 'SUCCESS' else "error"
            st.markdown(f"""
            <div class="file-status {status_class}">
                <strong>{status['filename']}</strong><br>
                <small>{status['message']}</small>
                {f" | 인코딩: {status['encoding']}" if status['encoding'] != 'N/A' else ""}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        success_count = len([s for s in file_status if s['status'] == 'SUCCESS'])
        error_count = len([s for s in file_status if s['status'] == 'ERROR'])
        
        st.markdown(f"""
        <div class="status-card">
            <div class="status-icon">✅</div>
            <div class="status-title">{success_count}</div>
            <div class="status-desc">성공한 파일</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="status-card">
            <div class="status-icon">❌</div>
            <div class="status-title">{error_count}</div>
            <div class="status-desc">실패한 파일</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 분석 결과 차트 ---
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
        # 도넛 차트
        selection = alt.selection_point(fields=['분류'], on='mouseover', nearest=True)

        base = alt.Chart(classification_counts_df).encode(
            theta=alt.Theta(field="논문 수", type="quantitative", stack=True),
            color=alt.Color(field="분류", type="nominal", title="Classification",
                           scale=alt.Scale(range=['#4a90e2', '#357abd', '#17a2b8', '#28a745', '#ffc107', '#dc3545']),
                           legend=alt.Legend(orient="right", titleColor="#2c3e50", labelColor="#6c757d")),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.8))
        ).add_params(selection)

        pie = base.mark_arc(outerRadius=150, innerRadius=90)
        text_total = alt.Chart(pd.DataFrame([{'value': f'{total_papers}'}])).mark_text(
            align='center', baseline='middle', fontSize=45, fontWeight='bold', color='#4a90e2'
        ).encode(text='value:N')
        text_label = alt.Chart(pd.DataFrame([{'value': 'Total Papers'}])).mark_text(
            align='center', baseline='middle', fontSize=16, dy=30, color='#6c757d'
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
    
    for classification in merged_df['Classification'].unique():
        count = len(merged_df[merged_df['Classification'] == classification])
        percentage = (count / total_papers * 100)
        
        if classification.startswith('Include'):
            box_class = ""
            icon = "✅"
        elif classification.startswith('Review'):
            box_class = "review"
            icon = "📝"
        else:
            box_class = "exclude"
            icon = "❌"
        
        st.markdown(f"""
        <div class="classification-box {box_class}">
            <strong>{icon} {classification}:</strong> {count:,}편 ({percentage:.1f}%)
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # --- 최근 이용내역 & 보너스포인트 스타일 (첨부파일 복제) ---
    st.markdown(f"""
    <div class="recent-usage-grid">
        <div class="usage-card">
            <div class="usage-title">최근 이용내역 ></div>
            <div class="usage-item">
                <div class="usage-detail">
                    <div class="usage-name">쿠팡이츠</div>
                    <div class="usage-date">25.08.21</div>
                </div>
                <div class="usage-amount">18,500원</div>
            </div>
        </div>
        <div class="usage-card">
            <div class="usage-title">보너스포인트 ></div>
            <div class="bonus-center">
                <div class="bonus-points">9,163 P</div>
                <div class="bonus-buttons">
                    <div class="bonus-button">포인트 전환</div>
                    <div class="bonus-button">포인트 사용처</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 최종 데이터셋 준비
    df_final = merged_df[~merged_df['Classification'].str.contains('Exclude', na=False)].copy()
    df_final_output = df_final.drop(columns=['Classification'], errors='ignore')

    # --- 마이메뉴 (첨부파일 스타일) ---
    st.markdown("""
    <div class="usage-card">
        <div class="usage-title">마이메뉴</div>
        <div class="service-grid">
            <div class="service-item">
                <div class="service-icon">📊</div>
                <div class="service-name">카드 사용등록</div>
            </div>
            <div class="service-item">
                <div class="service-icon">🔔</div>
                <div class="service-name">카드 분실신고</div>
            </div>
            <div class="service-item">
                <div class="service-icon">💻</div>
                <div class="service-name">결제계좌변경</div>
            </div>
            <div class="service-item">
                <div class="service-icon">👤</div>
                <div class="service-name">개인정보변경</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 나의 부가서비스 (첨부파일 스타일) ---
    st.markdown("""
    <div class="section-header">
        <div class="section-title">나의 부가서비스</div>
        <div class="section-subtitle">추천서비스</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="addon-service">
            <div class="addon-status">미사용</div>
            <div class="addon-name">일분결제금액이월약정 (리볼빙)</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="addon-service">
            <div class="addon-status">미사용</div>
            <div class="addon-name">휴대폰결제</div>
        </div>
        """, unsafe_allow_html=True)

    with col1:
        st.markdown("""
        <div class="addon-service">
            <div class="addon-status active">사용중</div>
            <div class="addon-name">바로알림</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 추천서비스 (첨부파일 스타일) ---
    st.markdown("""
    <div class="usage-card">
        <div class="usage-title">추천서비스</div>
        <div class="recommend-grid">
            <div class="recommend-card">
                <div class="recommend-icon">💳</div>
                <div class="recommend-title">분할납부 서비스</div>
                <div class="recommend-desc">대용량 데이터 처리를 위한 분할 업로드 서비스</div>
            </div>
            <div class="recommend-card">
                <div class="recommend-icon">🎁</div>
                <div class="recommend-title">디지털 명세서 신청</div>
                <div class="recommend-desc">분석 결과 자동 리포트 생성 서비스</div>
            </div>
            <div class="recommend-card">
                <div class="recommend-icon">💰</div>
                <div class="recommend-title">기프트카드</div>
                <div class="recommend-desc">프리미엄 분석 패키지 이용권</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 최종 파일 다운로드 섹션 ---
    st.markdown("""
    <div class="download-section">
        <div class="download-title">📥 SCIMAT 분석용 파일 다운로드</div>
        <div class="download-desc">병합 및 정제된 WOS Plain Text 파일</div>
    """, unsafe_allow_html=True)
    
    # SCIMAT 호환 파일 다운로드
    text_data = convert_to_scimat_wos_format(df_final_output)
    
    st.download_button(
        label="📥 최종 파일 다운로드",
        data=text_data,
        file_name="live_streaming_merged_scimat_ready.txt",
        mime="text/plain",
        use_container_width=True,
        help="SCIMAT에서 바로 사용 가능한 WOS Plain Text 파일"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Review 논문들이 있는 경우 엑셀 다운로드 제공
    review_papers_df = merged_df[merged_df['Classification'].str.contains('Review', na=False)]
    
    if len(review_papers_df) > 0:
        with st.expander(f"📝 Review (검토 필요) - 논문 목록 ({len(review_papers_df)}편)", expanded=False):
            # 엑셀 파일 생성
            review_excel_data = []
            for idx, (_, paper) in enumerate(review_papers_df.iterrows(), 1):
                review_excel_data.append({
                    '번호': idx,
                    '논문 제목': str(paper.get('TI', 'N/A')),
                    '출판연도': str(paper.get('PY', 'N/A')),
                    '저널명': str(paper.get('SO', 'N/A')),
                    '저자': str(paper.get('AU', 'N/A')),
                    '분류': str(paper.get('Classification', 'N/A'))
                })
            
            review_excel_df = pd.DataFrame(review_excel_data)
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                review_excel_df.to_excel(writer, sheet_name='Review_Papers', index=False)
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 검토 논문 목록 엑셀 다운로드",
                data=excel_data,
                file_name=f"review_papers_list_{len(review_papers_df)}편.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# 도움말 섹션
with st.expander("❓ 자주 묻는 질문 (FAQ)", expanded=False):
    st.markdown("""
    **Q: 여러 WOS 파일을 어떻게 한 번에 처리하나요?**
    A: WOS에서 여러 번 Plain Text 다운로드한 후, 모든 .txt 파일을 한 번에 업로드하면 자동으로 병합됩니다.
    
    **Q: 중복된 논문이 있을까봐 걱정됩니다.**
    A: UT(Unique Article Identifier) 기준으로 자동 중복 제거되며, UT가 없으면 제목+저자 조합으로 중복을 감지합니다.
    
    **Q: WOS에서 어떤 설정으로 다운로드해야 하나요?**
    A: Export → Record Content: "Full Record and Cited References", File Format: "Plain Text"로 설정하세요.
    
    **Q: SCIMAT 분석 설정은 어떻게 하나요?**
    A: Unit of Analysis: "Author's words + Source's words", Network Type: "Co-occurrence", Normalization: "Equivalence Index"를 권장합니다.
    """)

st.markdown("<br><br>", unsafe_allow_html=True)
