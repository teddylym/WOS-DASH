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

# --- 2. 백엔드 기능 함수 (변경 없음) ---
def build_normalization_map():
    base_map = {
        "machine learning": ["machine-learning", "ml", "machinelearning"], "artificial intelligence": ["ai"],
        "deep learning": ["deep-learning", "dnn"], "neural networks": ["neural network", "nn"],
        "natural language processing": ["nlp"], "computer vision": ["cv"], "reinforcement learning": ["rl"],
        "live streaming": ["live-streaming", "livestreaming"], "video streaming": ["video-streaming"],
        "social media": ["social-media"], "user experience": ["ux"], "user behavior": ["user-behavior"],
        "content creation": ["content-creation"], "digital marketing": ["digital-marketing"],
        "e commerce": ["ecommerce", "e-commerce"], "data mining": ["data-mining"], "big data": ["big-data"],
        "data analysis": ["data-analysis"], "sentiment analysis": ["sentiment-analysis"],
        "statistical analysis": ["statistical-analysis"], "structural equation modeling": ["sem", "pls-sem"],
        "cloud computing": ["cloud-computing"], "internet of things": ["iot"],
        "mobile applications": ["mobile apps", "mobile app"], "web development": ["web-development"],
        "software engineering": ["software-engineering"]
    }
    reverse_map = {}
    for standard, variations in base_map.items():
        reverse_map[standard] = standard
        for v in variations:
            reverse_map[v.replace(" ", "").replace("-", "")] = standard
            reverse_map[v] = standard
    return reverse_map
NORMALIZATION_MAP = build_normalization_map()

def normalize_keyword_phrase(phrase):
    return NORMALIZATION_MAP.get(phrase.lower().replace(" ", "").replace("-", ""), phrase.lower().strip())

def load_data(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    for encoding in ['utf-8-sig', 'utf-8', 'latin1', 'cp949']:
        try:
            df = pd.read_csv(io.StringIO(file_bytes.decode(encoding)), sep='\t', lineterminator='\n')
            if df.shape[1] > 1: return df
        except Exception: continue
    for encoding in ['utf-8-sig', 'utf-8', 'latin1', 'cp949']:
        try:
            df = pd.read_csv(io.StringIO(file_bytes.decode(encoding)))
            if df.shape[1] > 1: return df
        except Exception: continue
    return None

def classify_article(row):
    text = ' '.join(str(row.get(c, '')).lower() for c in ['TI', 'SO', 'DE', 'ID', 'AB'])
    if any(k in text for k in ['protocol', 'network coding', 'wimax', 'mac layer', 'bandwidth', 'tcp', 'udp']): return 'Exclude (제외연구)'
    if any(k in text for k in ['user', 'viewer', 'behavior', 'experience', 'engagement', 'motivation', 'social', 'commerce']): return 'Include (관련연구)'
    return 'Review (검토필요)'

def clean_keyword_string(keywords_str, stop_words, lemmatizer):
    if pd.isna(keywords_str): return ""
    cleaned = set()
    for kw in keywords_str.split(';'):
        norm_kw = normalize_keyword_phrase(kw)
        words = re.sub(r'[^a-z\s]', '', norm_kw).split()
        lemmatized = [lemmatizer.lemmatize(w) for w in words if w not in stop_words and len(w) > 2]
        if lemmatized:
            cleaned.add(" ".join(lemmatized))
    return '; '.join(sorted(list(cleaned)))

def convert_df_to_scimat_format(df):
    # ... (기존 함수와 동일, 생략)
    return "FN Clarivate Analytics Web of Science\nVR 1.0\n\n" + "\n\n".join(
        "\n".join(f"{tag} {val}" for tag, val in row.items() if pd.notna(val)) + "\nER"
        for _, row in df.iterrows()
    )


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
    lemmatizer = WordNetLemmatizer()
    include_mask = df['Classification'] == 'Include (관련연구)'
    if 'DE' in df.columns:
        df['DE_cleaned'] = df['DE'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))
    if 'ID' in df.columns:
        df['ID_cleaned'] = df['ID'].apply(lambda x: clean_keyword_string(x, stop_words, lemmatizer))

# --- 상단 통계 카드 ---
st.markdown("### 📊 Stats Overview")
total_papers = len(df)
final_papers = len(df[df['Classification'] != 'Exclude (제외연구)'])
included_papers = df['Classification'].value_counts().get('Include (관련연구)', 0)
reviewed_papers = df['Classification'].value_counts().get('Review (검토필요)', 0)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><h3>총 논문 수</h3><p>{total_papers}</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h3>최종 분석 대상</h3><p>{final_papers}</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h3>관련 연구</h3><p>{included_papers}</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h3>검토 필요</h3><p>{reviewed_papers}</p></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 중앙 분석 섹션 ---
col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("<h5 style='text-align:center;'>논문 분류 분포</h5>", unsafe_allow_html=True)
        classification_counts = df['Classification'].value_counts().reset_index()
        classification_counts.columns = ['분류', '논문 수']
        
        donut_chart = alt.Chart(classification_counts).mark_arc(innerRadius=70, outerRadius=110).encode(
            theta=alt.Theta(field="논문 수", type="quantitative"),
            color=alt.Color(field="분류", type="nominal", scale=alt.Scale(
                domain=['Include (관련연구)', 'Review (검토필요)', 'Exclude (제외연구)'],
                range=['#0096FF', '#7F7F7F', '#D3D3D3']
            ), legend=alt.Legend(title="분류", orient="bottom")),
            tooltip=['분류', '논문 수']
        ).properties(height=300)
        st.altair_chart(donut_chart, use_container_width=True)

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
        if 'NR' in df.columns:
            df_cited = df.copy()
            df_cited['NR'] = pd.to_numeric(df_cited['NR'], errors='coerce').fillna(0)
            df_cited = df_cited.sort_values(by='NR', ascending=False).head(5)
            df_cited['Label'] = df_cited['AU'].str.split(';').str[0] + " - " + df_cited['TI'].str[:40] + '...'
            
            cited_chart = alt.Chart(df_cited).mark_bar(color='#0096FF').encode(
                x=alt.X('NR:Q', title='참고문헌 수'),
                y=alt.Y('Label:N', title='논문', sort='-x'),
                tooltip=['TI', 'AU', 'NR']
            ).properties(height=300)
            st.altair_chart(cited_chart, use_container_width=True)
        else:
            st.warning("참고문헌 수(NR) 데이터가 없습니다.")

    with tab2:
        all_keywords = []
        if 'DE_cleaned' in df.columns:
            all_keywords.extend(df.loc[include_mask, 'DE_cleaned'].dropna().str.split(';').explode())
        if 'ID_cleaned' in df.columns:
            all_keywords.extend(df.loc[include_mask, 'ID_cleaned'].dropna().str.split(';').explode())
        
        if all_keywords:
            top_keywords_df = pd.DataFrame(Counter(all_keywords).most_common(20), columns=['키워드', '빈도'])
            top_3_keywords = top_keywords_df['키워드'].head(3).tolist()
            
            y_sort = alt.SortField(field='빈도', order='descending')

            line = alt.Chart(top_keywords_df).mark_rule(size=2, color='#0096FF').encode(
                x='빈도:Q',
                y=alt.Y('키워드:N', sort=y_sort)
            )
            
            lollipop_chart = alt.Chart(top_keywords_df).mark_point(filled=True, size=100).encode(
                x=alt.X('빈도:Q', title='빈도'),
                y=alt.Y('키워드:N', sort=y_sort, title=None),
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
            label="📥 CSV 파일 다운로드", data=csv,
            file_name="wos_preprocessed_data.csv", mime="text/csv", use_container_width=True
        )
    with col2:
        st.download_button(
            label="📥 SciMAT 호환 파일 다운로드", data=scimat_text,
            file_name="wos_for_scimat.txt", mime="text/plain", use_container_width=True
        )

# --- 하단 여백 ---
st.markdown("<br><br>", unsafe_allow_html=True)
