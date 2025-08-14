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
    page_title="WOS Prep | Professional Edition",
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

        # 1단계: 기본 정제
        keyword_clean = keyword.strip().lower()
        keyword_clean = re.sub(r'[^a-z\s\-_]', '', keyword_clean)

        # 2단계: 구문 단위 정규화
        normalized_phrase = normalize_keyword_phrase(keyword_clean)

        # 3단계: 단어별 처리
        if normalized_phrase == keyword_clean.lower():
            keyword_clean = keyword_clean.replace('-', ' ').replace('_', ' ')
            words = keyword_clean.split()

            filtered_words = []
            for word in words:
                if word and len(word) > 2 and word not in stop_words:
                    lemmatized_word = lemmatizer.lemmatize(word)
                    filtered_words.append(lemmatized_word)

            if filtered_words:
                reconstructed_phrase = " ".join(filtered_words)
                final_keyword = normalize_keyword_phrase(reconstructed_phrase)
                if final_keyword and len(final_keyword) > 2:
                    cleaned_keywords.add(final_keyword)
        else:
            if normalized_phrase and len(normalized_phrase) > 2:
                cleaned_keywords.add(normalized_phrase)

    return '; '.join(sorted(list(cleaned_keywords)))

# --- SCIMAT 형식 변환 함수 ---
def convert_df_to_scimat_format(df_to_convert):
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
        sorted_tags = [tag for tag in wos_field_order if tag in row.index and pd.notna(row[tag])]

        for tag in sorted_tags:
            value = row[tag]
            if pd.isna(value) or not str(value).strip():
                continue
            if not isinstance(value, str):
                value = str(value)

            if tag in multi_line_fields:
                items = [item.strip() for item in value.split(';') if item.strip()]
                if items:
                    file_content.append(f"{tag} {items[0]}")
                    for item in items[1:]:
                        file_content.append(f"  {item}")
            else:
                file_content.append(f"{tag} {value}")

        file_content.append("ER")
    return "\n".join(file_content).encode('utf-8')

# --- 헤더 및 버전 정보 ---
st.markdown("""
<div style="text-align: center; padding-top: 1rem;">
    <h1 style="color: #212529; font-size: 2.8rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: -0.05em;">
        WOS Prep
    </h1>
    <p style="color: #495057; font-size: 1.2rem; margin: 0; font-weight: 400;">
        A Professional Tool for Web of Science Data Pre-processing
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.85rem; padding: 1rem 0 2rem 0;">
    <p style="margin-bottom: 0.25rem;">
        <strong>Developed by:</strong> 임태경 (Teddy Lym), Hanyang University (Graduate School of Technology & Innovation Management)
    </p>
    <p style="margin: 0; font-size: 0.8rem;">
        <strong>Version:</strong> 1.5.0 | A Tool for Academic Research
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="width: 80px; height: 4px; background-color: #0d6efd; margin: 0 auto 3rem auto; border-radius: 2px;"></div>', unsafe_allow_html=True)


# --- 주요 기능 소개 ---
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; background: #f8f9fa; border-radius: 12px; border: 1px solid #e8eaed; height: 100%;">
        <div style="color: #1a73e8; font-size: 2.5rem; margin-bottom: 0.8rem;">📊</div>
        <h4 style="color: #3c4043; margin-bottom: 0.5rem; font-weight: 500;">데이터 분류</h4>
        <p style="color: #5f6368; font-size: 0.9rem; margin: 0;">핵심 논문 자동 분류</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; background: #f8f9fa; border-radius: 12px; border: 1px solid #e8eaed; height: 100%;">
        <div style="color: #34a853; font-size: 2.5rem; margin-bottom: 0.8rem;">⚙️</div>
        <h4 style="color: #3c4043; margin-bottom: 0.5rem; font-weight: 500;">키워드 정규화</h4>
        <p style="color: #5f6368; font-size: 0.9rem; margin: 0;">AI 기반 키워드 표준화</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; background: #f8f9fa; border-radius: 12px; border: 1px solid #e8eaed; height: 100%;">
        <div style="color: #ea4335; font-size: 2.5rem; margin-bottom: 0.8rem;">🎯</div>
        <h4 style="color: #3c4043; margin-bottom: 0.5rem; font-weight: 500;">SciMAT 호환</h4>
        <p style="color: #5f6368; font-size: 0.9rem; margin: 0;">완벽한 분석 도구 연동</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 키워드 정규화 기준 설명 ---
with st.expander("ⓘ 키워드 정규화 기준 상세"):
    st.markdown("""
    **적용되는 정규화 규칙:**
    - **AI/ML 관련**: machine learning ← machine-learning, ML, machinelearning
    - **인공지능**: artificial intelligence ← AI, artificial-intelligence
    - **딥러닝**: deep learning ← deep-learning, deep neural networks, DNN
    - **스트리밍**: live streaming ← live-streaming, livestreaming
    - **사용자 경험**: user experience ← user-experience, UX
    - **연구방법론**: structural equation modeling ← SEM, PLS-SEM
    - **전자상거래**: e commerce ← ecommerce, e-commerce, electronic commerce
    """)

# --- 파일 업로드 ---
st.divider()
st.subheader("📁 데이터 업로드")
st.markdown("<p style='color: #495057; font-size: 1rem; margin-top: -10px;'>Web of Science Raw Data 파일을 업로드하여 분석을 시작하세요.</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Tab-delimited 또는 Plain Text 형식의 파일을 선택하세요.",
    type=['csv', 'txt'],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is None:
        st.error("❌ 파일을 읽을 수 없습니다. Web of Science에서 다운로드한 'Tab-delimited' 또는 'Plain Text' 형식의 파일이 맞는지 확인해주세요.")
        st.stop()

    column_mapping = {
        'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE',
        'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY',
        'Times Cited, All Databases': 'TC', 'Times Cited, WoS Core': 'Z9'
    }
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)

    with st.spinner("🔄 데이터를 분석하고 있습니다... 잠시만 기다려주세요."):
        # 1단계: 분류
        df['Classification'] = df.apply(classify_article, axis=1)

        # 원본 키워드 백업
        if 'DE' in df.columns: df['DE_Original'] = df['DE'].copy()
        if 'ID' in df.columns: df['ID_Original'] = df['ID'].copy()

        # 2단계: 키워드 정규화
        stop_words = set(stopwords.words('english'))
        custom_stop_words = {'study', 'research', 'analysis', 'results', 'paper', 'article', 'using', 'based', 'approach', 'method', 'system', 'model'}
        stop_words.update(custom_stop_words)
        lemmatizer = WordNetLemmatizer()
        include_mask = df['Classification'] == 'Include (관련연구)'

        if 'DE' in df.columns:
            df['DE_cleaned'] = df['DE'].copy()
            df.loc[include_mask, 'DE_cleaned'] = df.loc[include_mask, 'DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))
        if 'ID' in df.columns:
            df['ID_cleaned'] = df['ID'].copy()
            df.loc[include_mask, 'ID_cleaned'] = df.loc[include_mask, 'ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))

        st.success("✅ 분석 완료!")

        # --- 분석 결과 요약 ---
        st.divider()
        st.subheader("📈 분석 결과 요약")

        # 전처리 결과 계산
        unique_before, unique_after = 0, 0
        if include_mask.any():
            de_original = df.loc[include_mask, 'DE_Original'].dropna().str.split(';').explode().str.strip().str.lower()
            id_original = df.loc[include_mask, 'ID_Original'].dropna().str.split(';').explode().str.strip().str.lower()
            unique_before = pd.concat([de_original, id_original]).nunique()

            de_cleaned = df.loc[include_mask, 'DE_cleaned'].dropna().str.split(';').explode().str.strip().str.lower()
            id_cleaned = df.loc[include_mask, 'ID_cleaned'].dropna().str.split(';').explode().str.strip().str.lower()
            unique_after = pd.concat([de_cleaned, id_cleaned]).nunique()
        
        # 처리 효율 요약
        st.markdown("###### **처리 효율 요약**")
        col1, col2, col3 = st.columns(3)
        df_final = df[df['Classification'].isin(['Include (관련연구)', 'Review (검토필요)'])].copy()
        col1.metric("최종 분석 논문", f"{len(df_final)} 건")
        col2.metric("정규화 적용 논문", f"{include_mask.sum()} 건")
        col3.metric("키워드 정규화", f"{unique_before} → {unique_after}", f"-{unique_before - unique_after} 개", help="유사/동의어 키워드를 표준화하여 고유 키워드 개수를 줄였습니다.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("###### **논문 분류 및 키워드 현황**")

        col1, col2 = st.columns([0.4, 0.6])
        with col1:
            # 도넛 차트
            classification_counts = df['Classification'].value_counts().reset_index()
            classification_counts.columns = ['분류', '논문 수']
            total_papers = classification_counts['논문 수'].sum()
            domain = ['Include (관련연구)', 'Review (검토필요)', 'Exclude (제외연구)']
            range_ = ['#d62728', '#1f77b4', '#7f7f7f']  # Red, Blue, Grey

            base = alt.Chart(classification_counts).encode(
                theta=alt.Theta(field="논문 수", type="quantitative", stack=True),
                color=alt.Color(field="분류", type="nominal", title="분류",
                               scale=alt.Scale(domain=domain, range=range_),
                               legend=alt.Legend(orient="bottom", titleColor="#212529", labelColor="#495057"))
            )
            pie = base.mark_arc(outerRadius=120, innerRadius=70)
            text_total = alt.Chart(pd.DataFrame([{'value': f'{total_papers}'}])).mark_text(
                align='center', baseline='middle', fontSize=35, fontWeight='bold', color='#212529'
            ).encode(text='value:N')
            text_label = alt.Chart(pd.DataFrame([{'value': 'Total Papers'}])).mark_text(
                align='center', baseline='middle', fontSize=14, dy=-25, color='#495057'
            ).encode(text='value:N')

            chart = (pie + text_total + text_label).properties(
                title=alt.TitleParams(text='논문 분류 분포', anchor='middle', fontSize=16, fontWeight=500, color="#212529"),
            ).configure_view(strokeWidth=0)
            st.altair_chart(chart, use_container_width=True)

        with col2:
            # 주요 키워드 분석 (롤리팝 차트)
            all_keywords = []
            if 'DE_cleaned' in df.columns:
                all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'DE_cleaned'].dropna() for kw in text.split(';') if kw.strip()])
            if 'ID_cleaned' in df.columns:
                all_keywords.extend([kw.strip() for text in df.loc[include_mask, 'ID_cleaned'].dropna() for kw in text.split(';') if kw.strip()])

            if all_keywords:
                keyword_counts = Counter(all_keywords)
                top_n = 20
                top_keywords_df = pd.DataFrame(keyword_counts.most_common(top_n), columns=['키워드', '빈도'])
                top_3_keywords = top_keywords_df['키워드'].head(3).tolist()
                
                y_encoding = alt.Y('키워드:N', title=None, sort=alt.SortField(field='빈도', order='descending'))
                x_encoding = alt.X('빈도:Q', title='빈도', scale=alt.Scale(zero=True))
                
                line = alt.Chart(top_keywords_df).mark_rule(size=2).encode(y=y_encoding, x=x_encoding)
                point = alt.Chart(top_keywords_df).mark_point(filled=True, size=100).encode(
                    y=y_encoding, x=x_encoding, tooltip=['키워드', '빈도'],
                    color=alt.condition(alt.FieldOneOfPredicate(field='키워드', oneOf=top_3_keywords), alt.value('#d62728'), alt.value('#4c78a8'))
                )
                lollipop_chart = (line + point).properties(
                    title=alt.TitleParams(text=f'상위 {top_n} 키워드', anchor='middle', fontSize=16, fontWeight=500, color="#212529"),
                    height=450
                ).configure_axis(grid=False).configure_view(strokeWidth=0)
                st.altair_chart(lollipop_chart, use_container_width=True)
            else:
                st.warning("⚠️ 관련연구로 분류된 논문에서 유효한 키워드를 찾을 수 없습니다.")

        st.divider()
        
        # --- 연도별 연구 동향 그래프 ---
        st.markdown("###### **연도별 연구 동향**")
        
        # 연도별 데이터 처리
        df_trend = df.copy()
        df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
        df_trend.dropna(subset=['PY'], inplace=True)
        df_trend['PY'] = df_trend['PY'].astype(int)
        
        yearly_counts = df_trend['PY'].value_counts().reset_index()
        yearly_counts.columns = ['Year', 'Count']
        yearly_counts = yearly_counts[yearly_counts['Year'] <= 2025].sort_values('Year')

        # 2025년 예상치 계산
        projection_layer = alt.Chart(pd.DataFrame([])).mark_line()
        show_projection_caption = False
        if 2025 in yearly_counts['Year'].values and 2024 in yearly_counts['Year'].values:
            count_2025_actual = yearly_counts.loc[yearly_counts['Year'] == 2025, 'Count'].iloc[0]
            count_2024_actual = yearly_counts.loc[yearly_counts['Year'] == 2024, 'Count'].iloc[0]
            count_2025_projected = count_2025_actual * 2
            
            projection_df = pd.DataFrame([
                {'Year': 2024, 'Count': count_2024_actual},
                {'Year': 2025, 'Count': count_2025_projected}
            ])
            
            projection_layer = alt.Chart(projection_df).mark_line(
                strokeDash=[5, 5], color='red', point={'color': 'red', 'filled': False, 'size': 60}
            ).encode(x='Year:O', y='Count:Q')
            show_projection_caption = True
            
        # 기본 라인 차트
        line_chart = alt.Chart(yearly_counts).mark_line(point=True).encode(
            x=alt.X('Year:O', title='발행 연도'),
            y=alt.Y('Count:Q', title='논문 수'),
            tooltip=['Year', 'Count']
        ).properties(height=300)
        
        # 차트 결합 및 출력
        trend_chart = (line_chart + projection_layer).properties(title="연도별 논문 발행 수")
        st.altair_chart(trend_chart, use_container_width=True)
        if show_projection_caption:
            st.caption("📈 붉은 점선은 2025년 상반기 데이터 기준으로 연간 발행량을 추정한 예상치입니다.")

        # --- 파일 다운로드 및 미리보기 ---
        st.divider()
        st.subheader("📋 처리된 데이터 미리보기 및 다운로드")
        
        df_final_output = df_final.copy()
        if 'DE' in df_final_output.columns:
            df_final_output['DE'] = df_final_output['DE_cleaned']
        if 'ID' in df_final_output.columns:
            df_final_output['ID'] = df_final_output['ID_cleaned']
        cols_to_drop = ['Classification', 'DE_cleaned', 'ID_cleaned', 'DE_Original', 'ID_Original']
        df_final_output = df_final_output.drop(columns=[col for col in cols_to_drop if col in df_final_output.columns], errors='ignore')
        
        st.dataframe(df_final_output.head(10), use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        text_data = convert_df_to_scimat_format(df_final_output)
        st.download_button(
            label="📥 SciMAT 호환 포맷 파일 다운로드 (.txt)",
            data=text_data,
            file_name="wos_prep_for_scimat.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        if st.checkbox("SciMAT 사용 가이드 보기"):
            st.info("""
            **💡 SciMAT 사용 가이드:**
            1. 다운로드한 `wos_prep_for_scimat.txt` 파일을 SciMAT에 업로드합니다.
            2. `Group set` → `Words groups manager`에서 Levenshtein distance를 활용해 유사 키워드를 자동으로 그룹핑합니다.
            3. 수동으로 키워드 그룹을 최종 조정한 후 분석을 실행합니다.
            """)
