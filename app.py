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
    page_title="WOS Prep - Professional Data Preprocessing", 
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

# --- Streamlit UI 및 실행 로직 ---
# 헤더 섹션 - 전문적 디자인
st.markdown("""
<div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            border-radius: 10px; margin-bottom: 2rem; color: white;">
    <h1 style="font-size: 3rem; font-weight: 300; margin: 0; letter-spacing: -1px;">
        📊 WOS Prep
    </h1>
    <p style="font-size: 1.2rem; margin: 0.5rem 0 0 0; opacity: 0.9; font-weight: 300;">
        Professional Data Preprocessing for Science Mapping Analysis
    </p>
</div>
""", unsafe_allow_html=True)

# 기능 개요 섹션
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; height: 120px;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
        <h4 style="margin: 0; font-weight: 500;">Smart Classification</h4>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">AI-powered research filtering</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; height: 120px;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔬</div>
        <h4 style="margin: 0; font-weight: 500;">SciMAT Integration</h4>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">Seamless compatibility</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; height: 120px;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
        <h4 style="margin: 0; font-weight: 500;">Keyword Normalization</h4>
        <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">Advanced standardization</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 정규화 예시 표시 - 전문적 스타일
with st.expander("⚙️ Advanced Keyword Normalization Rules"):
    st.markdown("""
    **Machine Learning & AI Standardization:**
    - `machine learning` ← machine-learning, ML, machinelearning
    - `artificial intelligence` ← AI, artificial-intelligence
    - `deep learning` ← deep-learning, deep neural networks, DNN
    
    **Streaming & Media Normalization:**
    - `live streaming` ← live-streaming, livestreaming
    - `user experience` ← user-experience, UX
    
    **Research Methodology Standardization:**
    - `structural equation modeling` ← SEM, PLS-SEM
    - `e commerce` ← ecommerce, e-commerce, electronic commerce
    """)

# 파일 업로드 섹션 - 전문적 디자인
st.markdown("""
<div style="border: 2px dashed #ccc; border-radius: 10px; padding: 2rem; text-align: center; margin: 2rem 0;">
    <div style="font-size: 3rem; margin-bottom: 1rem;">📁</div>
    <h3 style="margin: 0; color: #333;">Upload Your WOS Data</h3>
    <p style="color: #666; margin: 0.5rem 0;">Support for CSV and TXT formats from Web of Science</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose your Web of Science file", 
    type=['csv', 'txt'],
    help="Please upload Tab-delimited or Plain Text format files downloaded from Web of Science"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("파일을 읽을 수 없습니다. Web of Science에서 다운로드한 'Tab-delimited' 또는 'Plain Text' 형식의 파일이 맞는지 확인해주세요.")
        st.stop()
    
    # 원본 컬럼명 보존 (대소문자 변환하지 않음)
    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC', 'Times Cited, WoS Core': 'Z9'
    }
    
    # 컬럼명이 이미 WoS 태그 형식인 경우는 변환하지 않음
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)

    with st.spinner("🔍 Processing your data with advanced algorithms..."):
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
        
        st.success("✅ Processing completed successfully!")
        
        # 결과 요약 - 전문적 메트릭 디스플레이
        st.markdown("### 📈 Analysis Results")
        
        # 메트릭 카드 스타일
        classification_counts = df['Classification'].value_counts().reset_index()
        classification_counts.columns = ['Classification', 'Count']
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        include_count = classification_counts[classification_counts['Classification'] == 'Include (관련연구)']['Count'].iloc[0] if len(classification_counts[classification_counts['Classification'] == 'Include (관련연구)']) > 0 else 0
        review_count = classification_counts[classification_counts['Classification'] == 'Review (검토필요)']['Count'].iloc[0] if len(classification_counts[classification_counts['Classification'] == 'Review (검토필요)']) > 0 else 0
        exclude_count = classification_counts[classification_counts['Classification'] == 'Exclude (제외연구)']['Count'].iloc[0] if len(classification_counts[classification_counts['Classification'] == 'Exclude (제외연구)']) > 0 else 0
        
        with metric_col1:
            st.metric("Relevant Studies", include_count, delta=f"{include_count/(len(df))*100:.1f}%")
        with metric_col2:
            st.metric("Review Required", review_count, delta=f"{review_count/(len(df))*100:.1f}%")
        with metric_col3:
            st.metric("Excluded", exclude_count, delta=f"{exclude_count/(len(df))*100:.1f}%")
        
        # 차트 표시
        chart = alt.Chart(classification_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Count", type="quantitative"), 
            color=alt.Color(field="Classification", type="nominal", title="Classification"),
            tooltip=['Classification', 'Count']
        ).properties(title='Research Classification Distribution', width=400, height=300)
        st.altair_chart(chart, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🔍 Keyword Analysis for Relevant Studies")
        all_keywords = []
        if 'DE_cleaned' in df.columns: 
            all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'DE_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        if 'ID_cleaned' in df.columns: 
            all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'ID_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
        
        if all_keywords:
            keyword_counts = Counter(all_keywords)
            top_n = 20
            top_keywords = keyword_counts.most_common(top_n)
            df_keywords = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])
            
            keyword_chart = alt.Chart(df_keywords).mark_bar(color='#667eea').encode(
                x=alt.X('Frequency:Q', title='Frequency'), 
                y=alt.Y('Keyword:N', title='Keywords', sort='-x'),
                tooltip=['Keyword', 'Frequency']
            ).properties(title=f'Top {top_n} Normalized Keywords', width=600, height=400)
            st.altair_chart(keyword_chart, use_container_width=True)
            
            # 정규화 전후 비교 샘플 표시
            if st.checkbox("🔬 View Normalization Examples"):
                st.markdown("**Keyword Normalization Comparison (Top 3 Relevant Studies)**")
                sample_data = []
                sample_rows = df.loc[include_mask].head(3)
                
                for idx, row in sample_rows.iterrows():
                    if 'DE_Original' in df.columns and pd.notna(row.get('DE_Original')):
                        sample_data.append({
                            'Paper ID': idx,
                            'Field': 'Author Keywords (DE)',
                            'Before': str(row['DE_Original'])[:80] + "..." if len(str(row['DE_Original'])) > 80 else str(row['DE_Original']),
                            'After': str(row['DE_cleaned'])[:80] + "..." if len(str(row['DE_cleaned'])) > 80 else str(row['DE_cleaned'])
                        })
                    if 'ID_Original' in df.columns and pd.notna(row.get('ID_Original')):
                        sample_data.append({
                            'Paper ID': idx,
                            'Field': 'Keywords Plus (ID)',
                            'Before': str(row['ID_Original'])[:80] + "..." if len(str(row['ID_Original'])) > 80 else str(row['ID_Original']),
                            'After': str(row['ID_cleaned'])[:80] + "..." if len(str(row['ID_cleaned'])) > 80 else str(row['ID_cleaned'])
                        })
                
                if sample_data:
                    comparison_df = pd.DataFrame(sample_data)
                    st.dataframe(comparison_df, use_container_width=True)
                else:
                    st.info("No comparison data available.")
        else:
            st.warning("⚠️ No valid keywords found in relevant studies.")

        st.markdown("---")
        st.markdown("### 📥 Download Processed Data")
        
        # 다운로드 옵션을 카드 스타일로 개선
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <h4 style="margin: 0 0 0.5rem 0; color: #333;">Choose Your Export Format</h4>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Select the appropriate format based on your analysis workflow</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 세 가지 다운로드 옵션 제공
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🔧 Complete Original**")
            df_scimat = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
            
            # 원본 키워드 완전 복원 (SciMAT 호환성 최우선)
            if 'DE_Original' in df_scimat.columns:
                df_scimat['DE'] = df_scimat['DE_Original']
            if 'ID_Original' in df_scimat.columns:
                df_scimat['ID'] = df_scimat['ID_Original']
            
            # 임시 컬럼들만 제거
            cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
            df_scimat_output = df_scimat.drop(columns=[col for col in cols_to_drop if col in df_scimat.columns])
            
            st.metric("Papers", len(df_scimat_output), delta="Original format")
            
            text_data_scimat = convert_df_to_scimat_format(df_scimat_output)
            st.download_button(
                label="📥 Download Original", 
                data=text_data_scimat, 
                file_name="wos_prep_original.txt", 
                mime="text/plain",
                key="scimat_download",
                use_container_width=True
            )
            st.caption("🎯 For SciMAT manual preprocessing")
        
        with col2:
            st.markdown("**⚡ Minimal Processing**")
            df_minimal = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
            
            # 최소 정제: SciMAT 그룹핑 최적화
            if 'DE' in df_minimal.columns:
                df_minimal['DE'] = df_minimal['DE'].apply(
                    lambda x: '; '.join([kw.strip().lower() for kw in str(x).split(';') if kw.strip()]) if pd.notna(x) else x
                )
            if 'ID' in df_minimal.columns:
                df_minimal['ID'] = df_minimal['ID'].apply(
                    lambda x: '; '.join([kw.strip().lower() for kw in str(x).split(';') if kw.strip()]) if pd.notna(x) else x
                )
            
            # 임시 컬럼들 제거
            cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
            df_minimal_output = df_minimal.drop(columns=[col for col in cols_to_drop if col in df_minimal.columns])
            
            st.metric("Papers", len(df_minimal_output), delta="Case normalized")
            
            text_data_minimal = convert_df_to_scimat_format(df_minimal_output)
            st.download_button(
                label="📥 Download Minimal", 
                data=text_data_minimal, 
                file_name="wos_prep_minimal.txt", 
                mime="text/plain",
                key="minimal_download",
                use_container_width=True
            )
            st.caption("✨ Optimized for Levenshtein distance")
        
        with col3:
            st.markdown("**📊 Full Normalization**")
            df_analysis = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
            
            # 정규화된 키워드로 교체 (Include 논문만)
            if 'DE_cleaned' in df_analysis.columns: 
                df_analysis.loc[df_analysis['Classification'] == 'Include (관련연구)', 'DE'] = df_analysis.loc[df_analysis['Classification'] == 'Include (관련연구)', 'DE_cleaned']
            if 'ID_cleaned' in df_analysis.columns: 
                df_analysis.loc[df_analysis['Classification'] == 'Include (관련연구)', 'ID'] = df_analysis.loc[df_analysis['Classification'] == 'Include (관련연구)', 'ID_cleaned']
            
            # 임시 컬럼들 제거
            cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
            df_analysis_output = df_analysis.drop(columns=[col for col in cols_to_drop if col in df_analysis.columns])
            
            st.metric("Papers", len(df_analysis_output), delta="Fully normalized")
            
            text_data_analysis = convert_df_to_scimat_format(df_analysis_output)
            st.download_button(
                label="📥 Download Normalized", 
                data=text_data_analysis, 
                file_name="wos_prep_normalized.txt", 
                mime="text/plain",
                key="analysis_download",
                use_container_width=True
            )
            st.caption("📈 For final analysis & papers")
        
        # 사용 안내 및 SciMAT 워크플로우 가이드
        st.info("""
        **📋 SciMAT 최적화 워크플로우:**
        
        **1단계**: **원본 키워드** 또는 **최소 정제** 파일을 SciMAT에 업로드
        - SciMAT의 강력한 내장 전처리 모듈 활용
        - Levenshtein distance로 자동 그룹핑 수행
        - 수동 그룹 조정 및 Stop group 설정
        
        **2단계**: SciMAT에서 Science Mapping 분석 실행
        - 기간별 분석 설정
        - 클러스터링 및 시각화
        
        **3단계**: **완전 정규화** 파일로 추가 키워드 분석
        - 표준화된 키워드로 정밀 분석
        - 최종 보고서 및 논문 작성
        
        **💡 핵심**: SciMAT 자체의 전처리 기능을 활용하여 최적의 결과 달성
        """)
        
        # 키워드 정규화 통계
        if include_mask.any():
            include_count = include_mask.sum()
            st.success(f"✅ 키워드 정규화 적용: {include_count}개 'Include' 논문")
        
        # SciMAT 전문가 팁
        with st.expander("💡 SciMAT 전문가 팁 - 효과적인 그룹핑 전략"):
            st.write("""
            **📌 SciMAT에서 효과적인 키워드 그룹핑:**
            
            **1. Levenshtein Distance 활용**
            - `Group set` → `Words groups manager` → `Add` 버튼 옆 도구 활용
            - Maximum distance 2-3으로 설정하여 유사 키워드 자동 탐지
            - "live streaming", "live-streaming", "livestreaming" 등 자동 그룹화
            
            **2. 수동 그룹핑 우선순위**
            - 의미적으로 동일한 키워드들 우선 그룹화
            - 복수형/단수형: "consumer" ↔ "consumers"
            - 약어/풀네임: "AI" ↔ "artificial intelligence"
            
            **3. Stop Group 설정**
            - 너무 일반적인 키워드는 Stop group으로 설정
            - "research", "analysis", "study" 등 제외
            
            **4. 그룹명 설정 규칙**
            - 가장 표준적이고 명확한 용어를 그룹명으로 선택
            - 소문자 통일 및 하이픈 대신 공백 사용 권장
            """)
        
        st.write("**미리보기 (최소 정제 - SciMAT 최적화 버전)**")
        st.dataframe(df_minimal_output.head(10))
