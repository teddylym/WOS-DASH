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
st.set_page_config(page_title="WOS Prep | Professional Edition", layout="wide", initial_sidebar_state="collapsed")

# --- 커스텀 CSS 스타일 (기존 유지, 간략히) ---
st.markdown("""
<style>
    .metric-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); border: 1px solid #e9ecef; margin-bottom: 16px; transition: all 0.3s ease; }
    .metric-card:hover { box-shadow: 0 4px 20px rgba(0,56,117,0.15); border-color: #003875; }
    .metric-value { font-size: 2.8rem; font-weight: 700; color: #003875; margin: 0; line-height: 1; }
    .metric-label { font-size: 1rem; color: #6c757d; margin: 8px 0 0 0; font-weight: 500; }
    .metric-icon { background: linear-gradient(135deg, #003875, #0056b3); color: white; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin-bottom: 16px; }
    .section-header { background: linear-gradient(135deg, #003875, #0056b3); color: white; padding: 20px 24px; border-radius: 12px; margin: 24px 0 16px 0; box-shadow: 0 4px 16px rgba(0,56,117,0.2); }
    .section-title { font-size: 1.5rem; font-weight: 600; margin: 0; }
    .section-subtitle { font-size: 1rem; opacity: 0.9; margin: 4px 0 0 0; }
    .upload-zone { background: white; border: 2px dashed #003875; border-radius: 12px; padding: 40px; text-align: center; margin: 20px 0; transition: all 0.3s ease; }
    .upload-zone:hover { background: #f8f9fa; border-color: #0056b3; }
</style>
""", unsafe_allow_html=True)

# --- NLTK 리소스 ---
@st.cache_resource
def download_nltk_resources():
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
download_nltk_resources()

# --- 키워드 정규화 사전 ---
@st.cache_data
def build_normalization_map():
    base_map = {
        "live commerce": ["live shopping", "social commerce", "livestream shopping", "live video commerce", "e-commerce live streaming"],
        "live streaming": ["live-streaming", "livestreaming", "real time streaming", "live broadcast"],
        "user engagement": ["consumer engagement", "viewer engagement", "audience engagement", "customer engagement"],
        "purchase intention": ["purchase intentions", "buying intention", "purchase behavior"],
        "user experience": ["consumer experience", "viewer experience", "ux"],
        "social presence": ["perceived social presence"],
        "influencer marketing": ["influencer", "digital celebrities", "wanghong"],
        "platform technology": ["streaming technology", "platform architecture", "streaming media"],
        "peer-to-peer": ["p2p", "peer to peer"],
        "artificial intelligence": ["ai"],
        "user behavior": ["consumer behavior"],
        "vulnerability analysis": ["service quality", "platform adoption"]
    }
    reverse_map = {}
    for standard_form, variations in base_map.items():
        for variation in variations:
            reverse_map[variation.strip().lower()] = standard_form
        reverse_map[standard_form.strip().lower()] = standard_form
    return reverse_map

NORMALIZATION_MAP = build_normalization_map()

# --- 데이터 로드 ---
def load_data(uploaded_file):
    file_name = uploaded_file.name.lower()
    try:
        if file_name.endswith(('.xls', '.xlsx')):
            return pd.read_excel(uploaded_file)
        file_bytes = uploaded_file.getvalue()
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'cp949']
        for enc in encodings:
            try:
                content = file_bytes.decode(enc)
                df = pd.read_csv(io.StringIO(content), sep='\t', lineterminator='\n')
                if df.shape[1] > 1: return df
            except: pass
        for enc in encodings:
            try:
                content = file_bytes.decode(enc)
                df = pd.read_csv(io.StringIO(content))
                if df.shape[1] > 1: return df
            except: pass
        return None
    except Exception as e:
        st.error(f"파일 오류: {e}")
        return None

# --- [보수적 수정] 분류 함수 ---
def classify_article(row):
    strong_inclusion_keywords = [
        'live streaming commerce', 'social commerce', 'livestreaming commerce', 'purchase intention', 
        'customer engagement', 'consumer behavior', 'influencer marketing', 'brand engagement', 
        'online shopping', 'digital marketing', 'e-commerce', 'viewer engagement', 'user experience',
        'social motivations', 'parasocial interaction', 'virtual gift', 'fan engagement',
        'vulnerability analysis', 'service quality', 'platform adoption'
    ]
    
    inclusion_keywords = [
        'user', 'viewer', 'audience', 'streamer', 'consumer', 'participant', 'experience', 
        'interaction', 'motivation', 'psychology', 'social', 'community', 'cultural', 
        'society', 'marketing', 'business', 'brand', 'monetization', 'education', 'learning'
    ]
    
    exclusion_keywords = [  # 엄격: 복합 키워드만
        'protocol optimization', 'network coding scheme', 'wimax technology', 'ieee 802.16 standard',
        'mac layer protocol', 'packet dropping algorithm', 'bandwidth optimization', 
        'forward error correction scheme', 'sensor data processing', 'geoscience application'
    ]
    
    medical_keywords = ['surgical education', 'medical education', 'surgery', 'clinical learning']
    
    title = str(row.get('TI', '')).lower()
    author_keywords = str(row.get('DE', '')).lower()
    keywords_plus = str(row.get('ID', '')).lower()
    abstract = str(row.get('AB', '')).lower()
    full_text = ' '.join([title, author_keywords, keywords_plus, abstract])
    
    # 1. 강력 포함
    if any(kw in full_text for kw in strong_inclusion_keywords):
        return 'Include (관련연구)'
    
    # 2. 명확 제외 (복합 키워드)
    if any(kw in full_text for kw in exclusion_keywords):
        return 'Exclude (제외연구)'
    
    # 3. 의료 재검토
    if any(kw in full_text for kw in medical_keywords):
        return 'Review (검토필요)'
    
    # 4. 일반 포함 (2개 이상)
    if sum(1 for kw in inclusion_keywords if kw in full_text) >= 2:
        return 'Include (관련연구)'
    
    # 나머지 수동 확인
    return 'Review (검토필요)'

# --- 키워드 정규화 ---
def clean_keyword_string(keywords_str, stop_words, lemmatizer, normalization_map):
    if pd.isna(keywords_str) or not isinstance(keywords_str, str): return ""
    all_keywords = keywords_str.split(';')
    cleaned_keywords = set()
    for keyword in all_keywords:
        keyword_clean = keyword.strip().lower()
        if not keyword_clean: continue
        normalized = normalization_map.get(keyword_clean, keyword_clean)
        normalized = normalized.replace('-', ' ').replace('_', ' ')
        normalized = re.sub(r'[^a-z\s]', '', normalized)
        words = normalized.split()
        filtered = [lemmatizer.lemmatize(w) for w in words if len(w) > 2 and w not in stop_words]
        if filtered:
            cleaned_keywords.add(" ".join(filtered))
    return '; '.join(sorted(cleaned_keywords))

# --- SCIMAT 형식 변환 ---
def convert_df_to_scimat_format(df_to_convert):
    wos_field_order = ['PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB', 'C1', 'C3', 'RP', 'EM', 'RI', 'OI', 'FU', 'FX', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA', 'SN', 'EI', 'J9', 'JI', 'PD', 'PY', 'VL', 'IS', 'BP', 'EP', 'DI', 'EA', 'PG', 'WC', 'WE', 'SC', 'GA', 'UT', 'PM', 'OA', 'DA']
    file_content = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'C3', 'CR']
    for _, row in df_to_convert.iterrows():
        if len(file_content) > 2: file_content.append("")
        sorted_tags = [tag for tag in wos_field_order if tag in row.index and pd.notna(row[tag])]
        for tag in sorted_tags:
            value = row[tag]
            if pd.isna(value) or not str(value).strip(): continue
            value = str(value)
            if tag in multi_line_fields:
                items = [item.strip() for item in value.split(';') if item.strip()]
                if items:
                    file_content.append(f"{tag} {items[0]}")
                    for item in items[1:]: file_content.append(f"  {item}")
            else:
                file_content.append(f"{tag} {value}")
        file_content.append("ER")
    return "\n".join(file_content).encode('utf-8')

# --- 업로드 및 처리 ---
uploaded_file = st.file_uploader("WOS 파일 업로드", type=['csv', 'txt', 'xlsx', 'xls'])
if uploaded_file:
    df = load_data(uploaded_file)
    if df is None: st.stop()
    
    # 컬럼 매핑
    column_mapping = {'Authors': 'AU', 'Article Title': 'TI', 'Source Title': 'SO', 'Author Keywords': 'DE', 'Keywords Plus': 'ID', 'Abstract': 'AB', 'Cited References': 'CR', 'Publication Year': 'PY', 'Times Cited, All Databases': 'TC', 'Cited Reference Count': 'NR', 'Times Cited, WoS Core': 'Z9'}
    df.rename(columns=column_mapping, inplace=True)
    
    with st.spinner("분석 중..."):
        df['Classification'] = df.apply(classify_article, axis=1)
        stop_words = set(stopwords.words('english'))
        custom_stop = {'study', 'research', 'analysis', 'results', 'paper', 'article', 'using', 'based', 'approach', 'method', 'system', 'model'}
        stop_words.update(custom_stop)
        lemmatizer = WordNetLemmatizer()
        include_mask = df['Classification'] == 'Include (관련연구)'
        if 'DE' in df.columns:
            df['DE_cleaned'] = df.apply(lambda r: clean_keyword_string(r['DE'], stop_words, lemmatizer, NORMALIZATION_MAP) if r['Classification'] == 'Include (관련연구)' else r['DE'], axis=1)
        if 'ID' in df.columns:
            df['ID_cleaned'] = df.apply(lambda r: clean_keyword_string(r['ID'], stop_words, lemmatizer, NORMALIZATION_MAP) if r['Classification'] == 'Include (관련연구)' else r['ID'], axis=1)
    
    st.success("완료!")

    # 요약 메트릭 (기존 유지, 간략히)
    classification_counts = df['Classification'].value_counts()
    total = len(df)
    include = classification_counts.get('Include (관련연구)', 0)
    review = classification_counts.get('Review (검토필요)', 0)
    exclude = classification_counts.get('Exclude (제외연구)', 0)
    st.write(f"총 {total}편 | 포함 {include}편 | 검토필요 {review}편 | 제외 {exclude}편")

    # Review UI
    st.subheader("검토필요 논문")
    review_df = df[df['Classification'] == 'Review (검토필요)']
    if not review_df.empty:
        st.dataframe(review_df[['TI', 'AU', 'PY', 'DE']].head(30))
        for idx in review_df.index:
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"포함: {df.loc[idx, 'TI'][:30]}", key=f"inc_{idx}"):
                    df.loc[idx, 'Classification'] = 'Include (관련연구)'
            with col2:
                if st.button(f"제외: {df.loc[idx, 'TI'][:30]}", key=f"exc_{idx}"):
                    df.loc[idx, 'Classification'] = 'Exclude (제외연구)')
    else:
        st.info("검토필요 없음.")

    # 최종 출력
    df_final = df[df['Classification'] == 'Include (관련연구)'].copy()
    if 'DE' in df_final: df_final['DE'] = df_final['DE_cleaned']
    if 'ID' in df_final: df_final['ID'] = df_final['ID_cleaned']
    text_data = convert_df_to_scimat_format(df_final)
    st.download_button("SciMAT 파일 다운로드", text_data, "wos_prep.txt")
