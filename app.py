import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import altair as alt
import io

# --- 페이지 설정 ---
st.set_page_config(
    page_title="WOS Prep", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- NLTK 리소스 다운로드 (캐시 유지) ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 키워드 정규화 사전 (역방향 매핑으로 최적화) ---
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

# --- 핵심 기능 함수 ---
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

# --- SCIMAT 형식 변환 함수 (완전 WoS 표준 준수) ---
def convert_df_to_scimat_format(df_to_convert):
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

# --- 헤더 (Streamlit 호환 레이아웃) ---
st.markdown("""
<div style="text-align: center; padding: 1.5rem 0 2rem 0;">
    <h1 style="color: #202124; font-size: 2.2rem; font-weight: 500; margin-bottom: 2rem; letter-spacing: -0.01em;">
        WOS Prep
    </h1>
</div>
""", unsafe_allow_html=True)

# 정사각형 그리드 (Streamlit columns 사용)
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div style="width: 100%; height: 200px; padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center; border: 1px solid #e8eaed; display: flex; flex-direction: column; justify-content: center; margin-bottom: 1rem;">
        <div style="color: #1a73e8; font-size: 2rem; margin-bottom: 0.8rem;">📊</div>
        <div style="color: #3c4043; font-size: 1rem; font-weight: 500; margin-bottom: 0.3rem;">Data Classification</div>
        <div style="color: #5f6368; font-size: 0.8rem;">Targeted paper selection</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="width: 100%; height: 200px; padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center; border: 1px solid #e8eaed; display: flex; flex-direction: column; justify-content: center;">
        <div style="color: #ea4335; font-size: 2rem; margin-bottom: 0.8rem;">🎯</div>
        <div style="color: #3c4043; font-size: 1rem; font-weight: 500; margin-bottom: 0.3rem;">SciMAT Compatibility</div>
        <div style="color: #5f6368; font-size: 0.8rem;">Perfect analysis integration</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="width: 100%; height: 200px; padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center; border: 1px solid #e8eaed; display: flex; flex-direction: column; justify-content: center; margin-bottom: 1rem;">
        <div style="color: #34a853; font-size: 2rem; margin-bottom: 0.8rem;">⚙️</div>
        <div style="color: #3c4043; font-size: 1rem; font-weight: 500; margin-bottom: 0.3rem;">Keyword Normalization</div>
        <div style="color: #5f6368; font-size: 0.8rem;">AI-based standardization</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="width: 100%; height: 200px; padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center; border: 1px solid #e8eaed; display: flex; flex-direction: column; justify-content: center;">
        <div style="color: #9aa0a6; font-size: 1.5rem; margin-bottom: 0.8rem;">👨‍💻</div>
        <div style="color: #3c4043; font-size: 0.9rem; font-weight: 500; margin-bottom: 0.3rem;">T.K. Lim</div>
        <div style="color: #5f6368; font-size: 0.75rem; margin-bottom: 0.2rem;">Hanyang Univ.</div>
        <div style="color: #5f6368; font-size: 0.75rem;">Version 1.0.0</div>
    </div>
    """, unsafe_allow_html=True)

# PREP 설명
st.markdown("""
<div style="text-align: center; margin: 2rem 0;">
    <p style="color: #3c4043; font-size: 0.95rem; font-weight: 600; margin: 0;">
        <strong>PREP:</strong> Professional REsearch data Preprocessing for optimal SciMAT workflow
    </p>
</div>
""", unsafe_allow_html=True)

# 키워드 정규화 기준 (항상 표시)
st.markdown("""
<div style="background: #fff; border: 1px solid #e8eaed; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem;">
    <h4 style="color: #3c4043; margin-bottom: 1rem; font-weight: 500; display: flex; align-items: center;">
        <span style="margin-right: 0.5rem;">⚙️</span>키워드 정규화 규칙
    </h4>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.9rem;">
        <div>
            <div style="color: #1a73e8; font-weight: 500; margin-bottom: 0.5rem;">AI/ML & Technology</div>
            <div style="color: #5f6368; line-height: 1.5;">
                • machine learning ← ML, machine-learning<br>
                • artificial intelligence ← AI<br>
                • deep learning ← deep-learning, DNN<br>
                • live streaming ← livestreaming
            </div>
        </div>
        <div>
            <div style="color: #34a853; font-weight: 500; margin-bottom: 0.5rem;">Research Methods</div>
            <div style="color: #5f6368; line-height: 1.5;">
                • user experience ← UX, user-experience<br>
                • structural equation modeling ← SEM<br>
                • e commerce ← ecommerce, e-commerce<br>
                • data mining ← data-mining
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 파일 업로드 (전문 도구 스타일)
uploaded_file = st.file_uploader(
    "Web of Science Raw Data 파일 업로드",
    type=['csv', 'txt'],
    help="Tab-delimited 또는 Plain Text 형식 지원 (최대 200MB)",
    label_visibility="visible"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("❌ 파일을 읽을 수 없습니다. Web of Science에서 다운로드한 'Tab-delimited' 또는 'Plain Text' 형식의 파일이 맞는지 확인해주세요.")
        st.stop()
    
    # 원본 컬럼명 보존
    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC', 'Times Cited, WoS Core': 'Z9'
    }
    
    # 컬럼명이 이미 WoS 태그 형식인 경우는 변환하지 않음
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)

    with st.spinner("🔄 데이터를 분석하고 있습니다..."):
        # 1단계: 분류 (원본 키워드 기준)
        df['Classification'] = df.apply(classify_article, axis=1)
        
        # 원본 키워드 백업 (비교용)
        if 'DE' in df.columns:
            df['DE_Original'] = df['DE'].copy()
        if 'ID' in df.columns:
            df['ID_Original'] = df['ID'].copy()
            
        # 2단계: Include 논문만 키워드 정규화
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
        
        st.success("✅ 분석 완료!")
        
        # 분석 결과 (박스 제거, 간결화)
        st.markdown("### 📈 분석 결과")
        
        # 논문 분류 결과 (동일 크기)
        classification_counts = df['Classification'].value_counts().reset_index()
        classification_counts.columns = ['분류', '논문 수']
        total_papers = len(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**논문 분류 현황**")
            st.dataframe(classification_counts, hide_index=True, use_container_width=True)
        
        with col2:
            # 단순한 도넛 차트로 수정 (오류 해결)
            chart = alt.Chart(classification_counts).mark_arc(innerRadius=50, outerRadius=90).encode(
                theta=alt.Theta(field="논문 수", type="quantitative"), 
                color=alt.Color(field="분류", type="nominal", title="분류"),
                tooltip=['분류', '논문 수']
            ).properties(width=200, height=200)
            st.altair_chart(chart, use_container_width=True)
            
            # 중앙 텍스트를 별도로 표시
            st.markdown(f"""
            <div style="text-align: center; margin-top: -120px; margin-bottom: 80px;">
                <div style="color: #3c4043; font-size: 1.2rem; font-weight: bold;">
                    총 {total_papers}편
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 키워드 분석
        st.markdown("**주요 키워드 (관련연구)**")
        all_keywords = []
        if 'DE_cleaned' in df.columns: 
            all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'DE_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        if 'ID_cleaned' in df.columns: 
            all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'ID_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        
        if all_keywords:
            keyword_counts = Counter(all_keywords)
            top_n = 12
            top_keywords = keyword_counts.most_common(top_n)
            df_keywords = pd.DataFrame(top_keywords, columns=['키워드', '빈도'])
            
            keyword_chart = alt.Chart(df_keywords).mark_bar(color='#1a73e8').encode(
                x=alt.X('빈도:Q'), 
                y=alt.Y('키워드:N', sort='-x'),
                tooltip=['키워드', '빈도']
            ).properties(height=300)
            st.altair_chart(keyword_chart, use_container_width=True)
            
            # 정규화 전후 비교 (항상 표시)
            st.markdown("**정규화 전후 비교**")
            sample_rows = df.loc[include_mask].head(2)
            for idx, row in sample_rows.iterrows():
                if 'DE_Original' in df.columns and pd.notna(row.get('DE_Original')):
                    st.markdown(f"**논문 {idx}**")
                    st.text(f"정규화 전: {str(row['DE_Original'])[:80]}...")
                    st.text(f"정규화 후: {str(row['DE_cleaned'])[:80]}...")
                    st.markdown("---")
        else:
            st.warning("관련연구로 분류된 논문에서 키워드를 찾을 수 없습니다.")

        # 메트릭 정보
        col1, col2 = st.columns(2)
        with col1:
            st.metric("분석 대상 논문", len(df_final_output))
        with col2:
            if include_mask.any():
                st.metric("정규화 적용", f"{include_mask.sum()}개")
        
        # 미리보기
        st.markdown("**처리된 데이터 미리보기**")
        st.dataframe(df_final_output.head(5), use_container_width=True)
        
        # SciMAT 사용 팁
        with st.expander("💡 SciMAT 사용 팁"):
            st.markdown("""
            1. 다운로드한 파일을 SciMAT에 업로드
            2. `Group set` → `Words groups manager`에서 Levenshtein distance 사용
            3. 키워드 그룹 수동 조정 후 분석 실행
            """)
        
        # 다운로드 버튼 (최하단)
        st.markdown("---")
        text_data = convert_df_to_scimat_format(df_final_output)
        st.download_button(
            label="📥 SciMAT 호환 파일 다운로드",
            data=text_data,
            file_name="wos_prep_for_scimat.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
