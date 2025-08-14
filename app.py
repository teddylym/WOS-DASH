import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import altair as alt
import io

# --- 1. 페이지 설정 및 기본 스타일 ---
st.set_page_config(
    page_title="WOS Prep | Professional Dashboard",
    layout="wide",  # 넓은 레이아웃으로 변경
    initial_sidebar_state="collapsed"
)

# --- 사용자 정의 CSS ---
st.markdown("""
<style>
    /* 기본 폰트 및 색상 설정 */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #F0F2F5;
    }
    /* 기본 색상 변수 */
    :root {
        --primary-color: #0096FF;
        --text-color: #333;
        --light-text-color: #6c757d;
        --bg-color: #FFFFFF;
        --border-color: #EAEAEA;
    }
    /* Streamlit 기본 요소 숨기기 */
    .stDeployButton { display: none; }
    /* 메인 컨테이너 스타일 */
    .main .block-container {
        padding: 2rem;
        max-width: 1400px;
    }
    /* 카드 스타일 */
    .metric-card {
        background-color: var(--bg-color);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        transition: all 0.3s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 16px rgba(0,0,0,0.08);
    }
    .metric-card h3 {
        color: var(--light-text-color);
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .metric-card p {
        color: var(--text-color);
        font-size: 2.25rem;
        font-weight: 700;
        margin: 0;
    }
    /* 차트 컨테이너 스타일 */
    .chart-container {
        background-color: var(--bg-color);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
    }
    /* 헤더 스타일 */
    h1, h2, h3, h4, h5, h6, .st-emotion-cache-10trblm, .st-emotion-cache-1kyxreq {
        color: var(--text-color) !important;
    }
    .st-emotion-cache-1kyxreq {
        font-weight: 600;
        font-size: 1.5rem;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    /* 버튼 스타일 */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    /* 파일 업로더 스타일 */
    .stFileUploader {
        background-color: var(--bg-color);
        border: 2px dashed var(--primary-color);
        border-radius: 10px;
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- NLTK 리소스 다운로드 (캐시 유지) ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 2. 백엔드 기능 함수 (수정된 버전) ---
def build_normalization_map():
    """성능 최적화를 위한 역방향 정규화 사전 생성"""
    base_map = {
        # AI/ML 관련 (세분화 유지)
        "machine learning": ["machine-learning", "machine_learning", "ml", "machinelearning"],
        "artificial intelligence": ["ai", "artificial-intelligence", "artificial_intelligence", "artificialintelligence"],
        "deep learning": ["deep-learning", "deep_learning", "deep neural networks", "deep neural network", "dnn", "deeplearning"],
        "neural networks": ["neural-networks", "neural_networks", "neuralnetworks", "neural network", "nn"],
        "natural language processing": ["nlp", "natural-language-processing", "natural_language_processing"],
        "computer vision": ["computer-vision", "computer_vision", "computervision", "cv"],
        "reinforcement learning": ["reinforcement-learning", "reinforcement_learning", "rl"],
        
        # 스트리밍/미디어 관련  
        "live streaming": ["live-streaming", "live_streaming", "livestreaming", "real time streaming"],
        "video streaming": ["video-streaming", "video_streaming", "videostreaming"],
        "social media": ["social-media", "social_media", "socialmedia"],
        "user experience": ["user-experience", "user_experience", "ux", "userexperience"],
        "user behavior": ["user-behavior", "user_behavior", "userbehavior"],
        "content creation": ["content-creation", "content_creation", "contentcreation"],
        "digital marketing": ["digital-marketing", "digital_marketing", "digitalmarketing"],
        "e commerce": ["ecommerce", "e-commerce", "e_commerce", "electronic commerce"],
        
        # 연구방법론 관련
        "data mining": ["data-mining", "data_mining", "datamining"],
        "big data": ["big-data", "big_data", "bigdata"],
        "data analysis": ["data-analysis", "data_analysis", "dataanalysis"],
        "sentiment analysis": ["sentiment-analysis", "sentiment_analysis", "sentimentanalysis"],
        "statistical analysis": ["statistical-analysis", "statistical_analysis", "statisticalanalysis"],
        "structural equation modeling": ["sem", "pls-sem", "pls sem", "structural equation model"],
        
        # 기술 관련
        "cloud computing": ["cloud-computing", "cloud_computing", "cloudcomputing"],
        "internet of things": ["iot", "internet-of-things", "internet_of_things"],
        "mobile applications": ["mobile-applications", "mobile_applications", "mobile apps", "mobile app"],
        "web development": ["web-development", "web_development", "webdevelopment"],
        "software engineering": ["software-engineering", "software_engineering", "softwareengineering"]
    }
    
    # 역방향 매핑 생성 (variation -> standard_form)
    reverse_map = {}
    for standard_form, variations in base_map.items():
        for variation in variations:
            reverse_map[variation.lower()] = standard_form
        # 표준 형태도 자기 자신으로 매핑
        reverse_map[standard_form.lower()] = standard_form
    
    return reverse_map

NORMALIZATION_MAP = build_normalization_map()

def normalize_keyword_phrase(phrase):
    """구문 단위 키워드 정규화"""
    phrase_lower = phrase.lower().strip()
    return NORMALIZATION_MAP.get(phrase_lower, phrase_lower)

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

def classify_article(row):
    inclusion_keywords = ['user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'behavior', 'experience', 'engagement', 'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 'society', 'commerce', 'marketing', 'business', 'brand', 'purchase', 'monetization', 'education', 'learning', 'influencer']
    exclusion_keywords = ['protocol', 'network coding', 'wimax', 'ieee 802.16', 'mac layer', 'packet dropping', 'bandwidth', 'fec', 'arq', 'goodput', 'sensor data', 'geoscience', 'environmental data', 'wlan', 'ofdm', 'error correction', 'tcp', 'udp', 'network traffic']
    title = str(row.get('TI', '')).lower()
    source_title = str(row.get('SO', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, source_title, author_keywords, keywords_plus, abstract])
    if any(keyword in full_text for keyword in exclusion_keywords): return 'Exclude (제외연구)'
    if any(keyword in full_text for keyword in inclusion_keywords): return 'Include (관련연구)'
    return 'Review (검토필요)'

def clean_keyword_string(keywords_str, stop_words, lemmatizer):
    """개선된 키워드 정규화 및 정제 처리"""
    if pd.isna(keywords_str) or not isinstance(keywords_str, str): 
        return ""
    
    all_keywords = keywords_str.split(';')
    cleaned_keywords = set()
    
    for keyword in all_keywords:
        if not keyword.strip():
            continue
            
        # 1단계: 기본 정제 (하이픈과 언더스코어 공백으로 변환)
        keyword_clean = keyword.strip().lower()
        keyword_clean = re.sub(r'[^a-z\s\-_]', '', keyword_clean)
        
        # 2단계: 구문 단위 정규화 먼저 시도 (하이픈 포함 상태로)
        normalized_phrase = normalize_keyword_phrase(keyword_clean)
        
        # 3단계: 정규화되지 않은 경우에만 단어별 처리
        if normalized_phrase == keyword_clean.lower():
            # 하이픈을 공백으로 변환하여 단어별 처리
            keyword_clean = keyword_clean.replace('-', ' ').replace('_', ' ')
            words = keyword_clean.split()
            
            # 불용어 제거 및 표제어 추출
            filtered_words = []
            for word in words:
                if word and len(word) > 2 and word not in stop_words:
                    lemmatized_word = lemmatizer.lemmatize(word)
                    filtered_words.append(lemmatized_word)
            
            if filtered_words:
                reconstructed_phrase = " ".join(filtered_words)
                # 재구성된 구문에 대해 다시 정규화 시도
                final_keyword = normalize_keyword_phrase(reconstructed_phrase)
                if final_keyword and len(final_keyword) > 2:
                    cleaned_keywords.add(final_keyword)
        else:
            # 이미 정규화된 경우 바로 추가
            if normalized_phrase and len(normalized_phrase) > 2:
                cleaned_keywords.add(normalized_phrase)
    
    return '; '.join(sorted(list(cleaned_keywords)))

def convert_df_to_scimat_format(df_to_convert):
    """완전한 SciMAT 형식 변환 함수"""
    # 원본 WoS 파일과 완전히 동일한 필드 순서 및 헤더
    wos_field_order = [
        'PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB', 'C1', 'C3', 'RP',
        'EM', 'RI', 'OI', 'FU', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA',
        'SN', 'EI', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'BP', 'EP', 'DI', 'EA', 'PG',
        'WC', 'WE', 'SC', 'GA', 'UT', 'PM', 'OA', 'DA'
    ]
    
    # 원본과 완전히 동일한 헤더
    file_content = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'C3', 'CR']
    
    for _, row in df_to_convert.iterrows():
        # 첫 번째 레코드가 아닌 경우에만 빈 줄 추가 (원본과 동일)
        if len(file_content) > 2:
            file_content.append("")
            
        sorted_tags = [tag for tag in wos_field_order if tag in row.index and pd.notna(row[tag])]
        
        for tag in sorted_tags:
            value = row[tag]
            if pd.isna(value):
                continue
            if not isinstance(value, str): 
                value = str(value)
            if not value.strip(): 
                continue

            if tag in multi_line_fields:
                items = [item.strip() for item in value.split(';') if item.strip()]
                if items:
                    file_content.append(f"{tag} {items[0]}")
                    for item in items[1:]:
                        file_content.append(f"   {item}")
            else:
                file_content.append(f"{tag} {value}")

        file_content.append("ER")
    
    # 원본과 동일: UTF-8 (BOM 없음)으로 인코딩
    return "\n".join(file_content).encode('utf-8')

# --- 3. UI 렌더링 ---
st.title("WOS Prep Dashboard")
st.markdown("<p style='margin-top:-1rem; color: var(--light-text-color)'>Web of Science 데이터 자동 전처리 및 시각화 도구</p>", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
with st.container():
    st.markdown("### 📁 데이터 업로드")
    uploaded_file = st.file_uploader(
        "Web of Science에서 다운로드한 Tab-delimited 또는 Plain Text 형식의 파일을 업로드하세요.",
        type=['csv', 'txt'],
        label_visibility="collapsed"
    )

if uploaded_file is None:
    st.info("데이터 파일을 업로드하면 분석이 시작됩니다.")
    st.stop()

# --- 데이터 처리 ---
df = load_data(uploaded_file)
if df is None:
    st.error("❌ 파일을 읽을 수 없습니다. 지원되는 파일 형식인지 확인해주세요.")
    st.stop()

# 컬럼명 매핑
column_mapping = {
    'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
    'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
    'Times Cited, All Databases': 'TC', 'Cited Reference Count': 'NR', 'Times Cited, WoS Core': 'Z9'
}
df.rename(columns=column_mapping, inplace=True)

# 데이터 분석 함수 실행
with st.spinner("🔄 데이터 분석 중..."):
    df['Classification'] = df.apply(classify_article, axis=1)
    stop_words = set(stopwords.words('english'))
    custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article', 'using', 'based', 'approach', 'method', 'system', 'model'}
    stop_words.update(custom_stop_words)
    lemmatizer = WordNetLemmatizer()
    include_mask = df['Classification'] == 'Include (관련연구)'
    
    if 'DE' in df.columns:
        df['DE_cleaned'] = df['DE'].copy()
        df.loc[include_mask, 'DE_cleaned'] = df.loc[include_mask, 'DE'].apply(
            lambda x: clean_keyword_string(x, stop_words, lemmatizer)
        )
    if 'ID' in df.columns:
        df['ID_cleaned'] = df['ID'].copy()
        df.loc[include_mask, 'ID_cleaned'] = df.loc[include_mask, 'ID'].apply(
            lambda x: clean_keyword_string(x, stop_words, lemmatizer)
        )

# --- 상단 통계 카드 ---
st.markdown("### 📊 Stats Overview")
total_papers = len(df)
final_papers = len(df[df['Classification'] != 'Exclude (제외연구)'])
included_papers = df['Classification'].value_counts().get('Include (관련연구)', 0)
reviewed_papers = df['Classification'].value_counts().get('Review (검토필요)', 0)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><h3>총 논문 수</h3><p>{total_papers:,}</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h3>최종 분석 대상</h3><p>{final_papers:,}</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h3>관련 연구</h3><p>{included_papers:,}</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h3>검토 필요</h3><p>{reviewed_papers:,}</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 중앙 분석 섹션 ---
col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("<h5 style='text-align:center;'>논문 분류 분포</h5>", unsafe_allow_html=True)
        classification_counts = df['Classification'].value_counts().reset_index()
        classification_counts.columns = ['분류', '논문 수']
        
        # 도넛그래프에 중앙 텍스트 추가
        base_chart = alt.Chart(classification_counts).mark_arc(
            innerRadius=70, 
            outerRadius=110,
            stroke='white',
            strokeWidth=2
        ).encode(
            theta=alt.Theta(field="논문 수", type="quantitative"),
            color=alt.Color(field="분류", type="nominal", scale=alt.Scale(
                domain=['Include (관련연구)', 'Review (검토필요)', 'Exclude (제외연구)'],
                range=['#0096FF', '#7F7F7F', '#D3D3D3']
            ), legend=alt.Legend(title="분류", orient="bottom")),
            tooltip=['분류', '논문 수']
        ).properties(height=300)
        
        # 중앙 텍스트 추가
        center_text = alt.Chart(pd.DataFrame({'text': [f'Total\n{total_papers:,}\nPapers']})).mark_text(
            align='center',
            baseline='middle',
            fontSize=12,
            fontWeight='bold',
            color='#333'
        ).encode(
            x=alt.value(0),
            y=alt.value(0),
            text='text:N'
        )
        
        combined_chart = base_chart + center_text
        st.altair_chart(combined_chart, use_container_width=True)

with col2:
    with st.container(border=True):
        st.markdown("<h5 style='text-align:center;'>연도별 연구 동향</h5>", unsafe_allow_html=True)
        if 'PY' in df.columns:
            df_trend = df.copy()
            df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
            yearly_counts = df_trend.dropna(subset=['PY'])['PY'].astype(int).value_counts().sort_index().reset_index()
            yearly_counts.columns = ['Year', 'Count']
            
            line_chart = alt.Chart(yearly_counts).mark_line(point=True, color='#0096FF').encode(
                x=alt.X('Year:O', title='발행 연도'),
                y=alt.Y('Count:Q', title='논문 수'),
                tooltip=['Year', 'Count']
            ).properties(height=300)
            st.altair_chart(line_chart, use_container_width=True)
        else:
            st.warning("발행 연도(PY) 데이터가 없습니다.")

st.markdown("<br>", unsafe_allow_html=True)

# --- 주요 인용 및 키워드 분석 ---
with st.container(border=True):
    st.markdown("<h5 style='text-align:center;'>주요 인용 및 키워드 분석</h5>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["주요 인용 논문", "주요 키워드"])
    
    with tab1:
        if 'TC' in df.columns:  # NR 대신 TC 사용
            df_cited = df.copy()
            df_cited['TC'] = pd.to_numeric(df_cited['TC'], errors='coerce').fillna(0)
            df_cited = df_cited.sort_values(by='TC', ascending=False).head(5)
            
            # 저자명과 제목 처리
            df_cited['Author_Short'] = df_cited['AU'].fillna('Unknown').str.split(';').str[0]
            df_cited['Title_Short'] = df_cited['TI'].fillna('Untitled').str[:40] + '...'
            df_cited['Label'] = df_cited['Author_Short'] + " - " + df_cited['Title_Short']
            
            cited_chart = alt.Chart(df_cited).mark_bar(color='#0096FF').encode(
                x=alt.X('TC:Q', title='인용 횟수'),
                y=alt.Y('Label:N', title='논문', sort='-x'),
                tooltip=['TI', 'AU', 'TC']
            ).properties(height=300)
            st.altair_chart(cited_chart, use_container_width=True)
        else:
            st.warning("인용 횟수(TC) 데이터가 없습니다.")

    with tab2:
        all_keywords = []
        if 'DE_cleaned' in df.columns:
            for text in df.loc[include_mask, 'DE_cleaned'].dropna():
                if text and isinstance(text, str):
                    all_keywords.extend([kw.strip() for kw in text.split(';') if kw.strip()])
        if 'ID_cleaned' in df.columns:
            for text in df.loc[include_mask, 'ID_cleaned'].dropna():
                if text and isinstance(text, str):
                    all_keywords.extend([kw.strip() for kw in text.split(';') if kw.strip()])
        
        if all_keywords:
            keyword_counts = Counter(all_keywords)
            top_keywords = keyword_counts.most_common(20)
            top_keywords_df = pd.DataFrame(top_keywords, columns=['키워드', '빈도'])
            top_3_keywords = top_keywords_df['키워드'].head(3).tolist()
            
            # 수정된 Altair 차트 (올바른 정렬 문법 사용)
            line = alt.Chart(top_keywords_df).mark_rule(size=2, color='#0096FF').encode(
                x='빈도:Q',
                y=alt.Y('키워드:N', sort='-x')  # 수정된 부분
            )
            
            lollipop_chart = alt.Chart(top_keywords_df).mark_point(filled=True, size=100).encode(
                x=alt.X('빈도:Q', title='빈도'),
                y=alt.Y('키워드:N', sort='-x', title=None),  # 수정된 부분
                color=alt.condition(
                    alt.FieldOneOfPredicate(field='키워드', oneOf=top_3_keywords),
                    alt.value('#FF6B6B'), alt.value('#0096FF')
                ),
                tooltip=['키워드', '빈도']
            )
            
            st.altair_chart((line + lollipop_chart).properties(height=500), use_container_width=True)
        else:
            st.warning("관련연구에서 키워드를 찾을 수 없습니다.")

# --- 데이터 미리보기 및 다운로드 ---
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📋 처리된 데이터 미리보기 및 다운로드"):
    df_final = df[df['Classification'] != 'Exclude (제외연구)'].copy()
    
    # 정제된 키워드로 교체
    for col in ['DE', 'ID']:
        if f'{col}_cleaned' in df_final.columns:
            df_final[col] = df_final[f'{col}_cleaned']
    
    cols_to_drop = [c for c in ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original'] if c in df_final.columns]
    df_final_output = df_final.drop(columns=cols_to_drop)
    
    st.dataframe(df_final_output.head(10))
    
    csv = df_final_output.to_csv(index=False).encode('utf-8')
    scimat_text = convert_df_to_scimat_format(df_final_output)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 CSV 파일 다운로드", 
            data=csv,
            file_name="wos_preprocessed_data.csv", 
            mime="text/csv", 
            use_container_width=True
        )
    with col2:
        st.download_button(
            label="📥 SciMAT 호환 파일 다운로드", 
            data=scimat_text,
            file_name="wos_for_scimat.txt", 
            mime="text/plain", 
            use_container_width=True
        )
