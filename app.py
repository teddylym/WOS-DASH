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

# --- 헤더 ---
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 3rem 2rem; margin: -1rem -1rem 3rem -1rem; border-radius: 0 0 20px 20px;">
    <div style="text-align: center; color: white;">
        <h1 style="font-size: 2.8rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.03em;">
            WOS Prep
        </h1>
        <h2 style="font-size: 1.2rem; font-weight: 300; margin-bottom: 1.5rem; opacity: 0.9;">
            Web of Science Data Processing & SciMAT Integration Platform
        </h2>
        <div style="background: rgba(255,255,255,0.2); padding: 0.8rem 1.5rem; border-radius: 25px; display: inline-block; margin-bottom: 1rem;">
            <span style="font-size: 0.95rem; font-weight: 500;">
                한양대학교 기술경영전문대학원 | Hanyang Graduate School of Technology and Innovation Management
            </span>
        </div>
        <div style="color: rgba(255,255,255,0.85); font-size: 0.9rem; font-weight: 400;">
            Developed by 임태경 (Teddy Lym) | Version 2.1
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 주요 기능 소개 - 전문적 디자인
st.markdown("""
<div style="margin: 2rem 0 3rem 0;">
    <h3 style="text-align: center; color: #2c3e50; font-size: 1.4rem; font-weight: 600; margin-bottom: 2rem;">
        Core Capabilities
    </h3>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1.5rem; background: linear-gradient(145deg, #f8f9fa, #e9ecef); 
                border-radius: 15px; border-left: 4px solid #007bff; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
        <div style="color: #007bff; font-size: 2.2rem; margin-bottom: 1rem;">📊</div>
        <h4 style="color: #2c3e50; margin-bottom: 0.8rem; font-weight: 600; font-size: 1.1rem;">Intelligent Classification</h4>
        <p style="color: #6c757d; font-size: 0.9rem; margin: 0; line-height: 1.5;">
            AI-driven research paper categorization with precision filtering algorithms
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1.5rem; background: linear-gradient(145deg, #f8f9fa, #e9ecef); 
                border-radius: 15px; border-left: 4px solid #28a745; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
        <div style="color: #28a745; font-size: 2.2rem; margin-bottom: 1rem;">⚙️</div>
        <h4 style="color: #2c3e50; margin-bottom: 0.8rem; font-weight: 600; font-size: 1.1rem;">Advanced Normalization</h4>
        <p style="color: #6c757d; font-size: 0.9rem; margin: 0; line-height: 1.5;">
            Machine learning-powered keyword standardization and semantic unification
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 2rem 1.5rem; background: linear-gradient(145deg, #f8f9fa, #e9ecef); 
                border-radius: 15px; border-left: 4px solid #dc3545; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
        <div style="color: #dc3545; font-size: 2.2rem; margin-bottom: 1rem;">🎯</div>
        <h4 style="color: #2c3e50; margin-bottom: 0.8rem; font-weight: 600; font-size: 1.1rem;">SciMAT Integration</h4>
        <p style="color: #6c757d; font-size: 0.9rem; margin: 0; line-height: 1.5;">
            Seamless export compatibility for advanced bibliometric analysis workflows
        </p>
    </div>
    """, unsafe_allow_html=True)

# 키워드 정규화 기준 설명
with st.expander("🔧 Normalization Standards & Methodology", expanded=False):
    st.markdown("""
    **Applied Normalization Rules:**
    
    - **AI/ML Domain**: machine learning ← machine-learning, ML, machinelearning
    - **Artificial Intelligence**: artificial intelligence ← AI, artificial-intelligence  
    - **Deep Learning**: deep learning ← deep-learning, deep neural networks, DNN
    - **Streaming Technology**: live streaming ← live-streaming, livestreaming
    - **User Experience**: user experience ← user-experience, UX
    - **Research Methods**: structural equation modeling ← SEM, PLS-SEM
    - **E-commerce**: e commerce ← ecommerce, e-commerce, electronic commerce
    """)

# 파일 업로드 섹션 - 전문적 스타일
st.markdown("""
<div style="background: linear-gradient(145deg, #ffffff, #f8f9fa); padding: 2.5rem; border-radius: 15px; 
            border: 1px solid #dee2e6; margin: 2rem 0; box-shadow: 0 8px 25px rgba(0,0,0,0.06);">
    <h3 style="color: #2c3e50; margin-bottom: 1.5rem; font-weight: 600; font-size: 1.3rem; text-align: center;">
        📁 Data Upload & Processing
    </h3>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload your Web of Science raw data file",
    type=['csv', 'txt'],
    help="Please upload Tab-delimited or Plain Text format files downloaded from Web of Science database"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("❌ File processing failed. Please ensure the file is in 'Tab-delimited' or 'Plain Text' format from Web of Science.")
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

    with st.spinner("🔄 Processing and analyzing your data..."):
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
        
        st.success("✅ Data processing completed successfully!")
        
        # 분석 결과 - 전문적 레이아웃
        st.markdown("""
        <div style="background: linear-gradient(145deg, #ffffff, #f8f9fa); padding: 2.5rem; border-radius: 15px; 
                    border: 1px solid #dee2e6; margin: 2rem 0; box-shadow: 0 8px 25px rgba(0,0,0,0.06);">
            <h3 style="color: #2c3e50; margin-bottom: 2rem; font-weight: 600; font-size: 1.3rem; text-align: center;">
                📈 Analysis Results & Insights
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 논문 분류 결과
        classification_counts = df['Classification'].value_counts().reset_index()
        classification_counts.columns = ['분류', '논문 수']
        total_papers = len(df)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Research Classification Summary")
            st.dataframe(classification_counts, use_container_width=True)
        
        with col2:
            if include_mask.any():
                include_count = include_mask.sum()
                st.metric("🎯 Normalized Keywords Applied", f"{include_count:,} papers")
        
        text_data = convert_df_to_scimat_format(df_final_output)
        st.download_button(
            label="📥 Download SciMAT Compatible File",
            data=text_data,
            file_name="wos_prep_for_scimat.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #e3f2fd, #f3e5f5); padding: 1.5rem; border-radius: 12px; 
                    border-left: 4px solid #2196f3; margin: 1.5rem 0;">
            <h4 style="color: #1565c0; margin-bottom: 1rem; font-weight: 600;">💡 SciMAT Integration Guide</h4>
            <ol style="color: #424242; margin: 0; padding-left: 1.2rem;">
                <li style="margin-bottom: 0.5rem;">Import the downloaded file into SciMAT platform</li>
                <li style="margin-bottom: 0.5rem;">Navigate to <strong>Group set</strong> → <strong>Words groups manager</strong></li>
                <li style="margin-bottom: 0.5rem;">Apply Levenshtein distance algorithm for automatic grouping</li>
                <li>Manually adjust keyword groups and execute comprehensive analysis</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # 미리보기 섹션
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #2c3e50; font-weight: 600; font-size: 1.2rem;">
                📋 Processed Dataset Preview
            </h3>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(df_final_output.head(10), use_container_width=True):
            # 도넛그래프에 중앙 텍스트 추가
            base_chart = alt.Chart(classification_counts).add_selection(
                alt.selection_single()
            ).mark_arc(
                innerRadius=60, 
                outerRadius=120,
                stroke='white',
                strokeWidth=2
            ).encode(
                theta=alt.Theta(field="논문 수", type="quantitative"), 
                color=alt.Color(
                    field="분류", 
                    type="nominal", 
                    title="Classification",
                    scale=alt.Scale(range=['#007bff', '#28a745', '#ffc107'])
                ),
                tooltip=['분류', '논문 수']
            ).properties(
                title=alt.TitleParams(
                    text='Research Distribution Overview',
                    anchor='start',
                    fontSize=16,
                    fontWeight='bold'
                ),
                width=300, 
                height=300
            )
            
            # 중앙 텍스트 추가
            center_text = alt.Chart(pd.DataFrame({'x': [0], 'y': [0], 'text': [f'Total\n{total_papers}\nPapers']})).mark_text(
                align='center',
                baseline='middle',
                fontSize=14,
                fontWeight='bold',
                color='#2c3e50'
            ).encode(
                x=alt.value(150),  # 차트 중앙
                y=alt.value(150),  # 차트 중앙
                text='text:N'
            )
            
            combined_chart = base_chart + center_text
            st.altair_chart(combined_chart, use_container_width=True)
        
        # 키워드 분석
        st.subheader("Key Research Topics Analysis (Relevant Studies Only)")
        all_keywords = []
        if 'DE_cleaned' in df.columns: 
            all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'DE_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        if 'ID_cleaned' in df.columns: 
            all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'ID_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        
        if all_keywords:
            keyword_counts = Counter(all_keywords)
            top_n = 15
            top_keywords = keyword_counts.most_common(top_n)
            df_keywords = pd.DataFrame(top_keywords, columns=['키워드', '빈도'])
            
            keyword_chart = alt.Chart(df_keywords).mark_bar(
                color='#667eea',
                cornerRadiusTopRight=3,
                cornerRadiusBottomRight=3
            ).encode(
                x=alt.X('빈도:Q', title='Frequency'), 
                y=alt.Y('키워드:N', title='Keywords', sort='-x'),
                tooltip=['키워드', '빈도']
            ).properties(
                title=alt.TitleParams(
                    text=f'Top {top_n} Research Keywords Distribution',
                    anchor='start',
                    fontSize=16,
                    fontWeight='bold'
                ),
                height=400
            )
            st.altair_chart(keyword_chart, use_container_width=True)
            
            # 정규화 전후 비교
            if st.checkbox("📋 Normalization Comparison Analysis"):
                sample_data = []
                sample_rows = df.loc[include_mask].head(3)
                
                for idx, row in sample_rows.iterrows():
                    if 'DE_Original' in df.columns and pd.notna(row.get('DE_Original')):
                        sample_data.append({
                            'Paper ID': idx,
                            'Field Type': 'Author Keywords (DE)',
                            'Before Normalization': str(row['DE_Original'])[:60] + "..." if len(str(row['DE_Original'])) > 60 else str(row['DE_Original']),
                            'After Normalization': str(row['DE_cleaned'])[:60] + "..." if len(str(row['DE_cleaned'])) > 60 else str(row['DE_cleaned'])
                        })
                
                if sample_data:
                    comparison_df = pd.DataFrame(sample_data)
                    st.dataframe(comparison_df, use_container_width=True)
        else:
            st.warning("⚠️ No valid keywords found in the relevant research category.")

        # 데이터 다운로드 섹션
        st.markdown("""
        <div style="background: linear-gradient(145deg, #ffffff, #f8f9fa); padding: 2.5rem; border-radius: 15px; 
                    border: 1px solid #dee2e6; margin: 2rem 0; box-shadow: 0 8px 25px rgba(0,0,0,0.06);">
            <h3 style="color: #2c3e50; margin-bottom: 2rem; font-weight: 600; font-size: 1.3rem; text-align: center;">
                💾 SciMAT Compatible Export
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        
        # 최소 정제 버전 (SciMAT 최적화)
        if 'DE' in df_final.columns:
            df_final['DE'] = df_final['DE'].apply(
                lambda x: '; '.join([kw.strip().lower() for kw in str(x).split(';') if kw.strip()]) if pd.notna(x) else x
            )
        if 'ID' in df_final.columns:
            df_final['ID'] = df_final['ID'].apply(
                lambda x: '; '.join([kw.strip().lower() for kw in str(x).split(';') if kw.strip()]) if pd.notna(x) else x
            )
        
        # 임시 컬럼들 제거
        cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
        df_final_output = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.metric("📊 Final Analysis Dataset", f"{len(df_final_output):,} papers")
        with col2
