import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import io

# --- 페이지 설정 (원본 유지) ---
st.set_page_config(page_title="WOS 전처리", layout="wide", initial_sidebar_state="expanded")

# --- 커스텀 CSS (색상만 수정) ---
st.markdown("""
<style>
/* 기존 CSS 구조를 그대로 유지하며 색상만 변경합니다. */
.st-br {
    background: #003C71; /* 한양대 공식 색상으로 변경 */
}
/* 나머지 기존 스타일은 그대로 적용됩니다. */
.css-1v3fvcr {
    font-family: "Source Sans Pro", sans-serif;
    font-weight: 400;
    line-height: 1.6;
    text-size-adjust: 100%;
    -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
    -webkit-font-smoothing: auto;
    color: rgb(49, 51, 63);
    background-color: rgb(255, 255, 255);
    width: 100%;
    height: 100%;
    overflow: hidden;
}
.css-1r6slb0 {
    width: 100%;
    padding: 6rem 1rem 10rem;
    max-width: 46rem;
}
.st-b8 {
    background-color: #f0f2f6;
}
.css-1d391kg {
    padding: 2rem 1rem 1rem;
}
.css-18e3th9 {
    padding-top: 2rem;
}
.st-emotion-cache-16txtl3 {
   padding: 2rem 2rem 2rem;
}
</style>
""", unsafe_allow_html=True)

# --- NLTK 리소스 다운로드 (원본 유지) ---
@st.cache_resource
def download_nltk_resources():
    try:
        nltk.data.find('corpora/stopwords')
    except:
        nltk.download('stopwords')
    try:
        nltk.data.find('corpora/wordnet')
    except:
        nltk.download('wordnet')
download_nltk_resources()

# --- 핵심 처리 함수들 (원본 유지) ---
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_keywords(keywords):
    if not isinstance(keywords, str):
        return []
    keywords = re.split(r';\s*', keywords)
    processed = []
    for keyword in keywords:
        kw_lower = keyword.lower().strip()
        if kw_lower and kw_lower not in stop_words:
            lemma = lemmatizer.lemmatize(kw_lower)
            processed.append(lemma)
    return processed

def convert_df_to_scimat_format(df):
    output = []
    for index, row in df.iterrows():
        entry = f"PT J\n"
        entry += f"AU {row.get('Authors', '')}\n"
        entry += f"TI {row.get('Article Title', '')}\n"
        entry += f"SO {row.get('Source Title', '')}\n"
        entry += f"DE {row.get('Author Keywords', '')}\n"
        entry += f"ID {row.get('Keywords Plus', '')}\n"
        entry += f"AB {row.get('Abstract', '')}\n"
        entry += f"C1 {row.get('Addresses', '')}\n"
        entry += f"PY {row.get('Publication Year', '')}\n"
        entry += f"TC {row.get('WoS Core Collection Times Cited Count', '')}\n"
        entry += f"ER\n"
        output.append(entry)
    return "\n".join(output)

# --- UI 구성 (원본 구조에 로고와 제목만 수정) ---

# 사이드바에 로고 추가
LOGO_PATH = "HYU_logotype_blue_eng.png"
try:
    st.sidebar.image(LOGO_PATH, use_column_width=True)
except FileNotFoundError:
    st.sidebar.warning(f"`{LOGO_PATH}` 파일을 찾을 수 없습니다. 스크립트와 동일한 폴더에 있는지 확인해주세요.")

# 원본과 동일한 사이드바 헤더
st.sidebar.header("WOS 데이터 전처리")

# 원본과 동일한 메인 화면 제목
st.title("WOS 전처리 및 키워드 정규화")

# 파일 업로드 (원본 유지)
uploaded_file = st.sidebar.file_uploader("WoS 원문(.txt) 파일 업로드", type=['txt'])

if uploaded_file is not None:
    content = uploaded_file.getvalue().decode('utf-8-sig')
    articles_raw = content.strip().split('\nER\n')
    records = []
    for article in articles_raw:
        if "PT J" not in article: continue
        lines = article.strip().split('\n')
        record = {}
        field = None
        for line in lines:
            if len(line) > 2 and line[2] == ' ':
                field = line[:2]
                record[field] = line[3:]
            elif field:
                record[field] += ' ' + line.strip()
        records.append(record)
    df = pd.DataFrame(records)
    df.rename(columns={'AU': 'Authors', 'TI': 'Article Title', 'SO': 'Source Title', 'DE': 'Author Keywords', 'ID': 'Keywords Plus', 'AB': 'Abstract', 'C1': 'Addresses', 'PY': 'Publication Year', 'TC': 'WoS Core Collection Times Cited Count'}, inplace=True)
    st.session_state.df = df
    st.sidebar.success("파일이 성공적으로 업로드되었습니다.")

# 이후 모든 로직은 원본 코드와 100% 동일합니다.
if 'df' in st.session_state:
    st.header("데이터 미리보기")
    st.dataframe(st.session_state.df)

    st.header("키워드 전처리 및 정규화")
    df_processed = st.session_state.df.copy()
    df_processed['DE_processed'] = df_processed['Author Keywords'].apply(preprocess_keywords)
    df_processed['ID_processed'] = df_processed['Keywords Plus'].apply(preprocess_keywords)
    all_keywords = df_processed['DE_processed'].sum() + df_processed['ID_processed'].sum()
    keyword_counts = Counter(all_keywords)
    df_keywords = pd.DataFrame(keyword_counts.items(), columns=['Keyword', 'Frequency']).sort_values(by='Frequency', ascending=False)
    st.subheader("키워드 빈도 분석")
    st.dataframe(df_keywords)

    st.subheader("키워드 정규화 규칙 입력")
    normalization_rules_str = st.text_area("정규화 규칙을 입력하세요 (예: technologies: technology, networks: network)", height=150)
    
    if st.button("정규화 적용"):
        normalization_map = {}
        if normalization_rules_str:
            rules = normalization_rules_str.split(',')
            for rule in rules:
                try:
                    target, representative = rule.split(':')
                    normalization_map[target.strip()] = representative.strip()
                except ValueError:
                    st.warning(f"잘못된 형식의 규칙 '{rule}'은(는) 무시됩니다.")
        
        def normalize_keywords(keywords_list):
            return [normalization_map.get(kw, kw) for kw in keywords_list]
        
        df_processed['DE_normalized'] = df_processed['DE_processed'].apply(normalize_keywords)
        df_processed['ID_normalized'] = df_processed['ID_processed'].apply(normalize_keywords)
        
        def join_keywords(keywords_list):
            return '; '.join(keywords_list)
            
        st.session_state.df['Author Keywords'] = df_processed['DE_normalized'].apply(join_keywords)
        st.session_state.df['Keywords Plus'] = df_processed['ID_normalized'].apply(join_keywords)
        st.success("키워드 정규화가 완료되었습니다.")
        st.header("정규화된 데이터")
        st.dataframe(st.session_state.df)

    st.header("SciMAT 형식으로 변환 및 다운로드")
    if st.button("SciMAT 형식으로 변환"):
        scimat_output = convert_df_to_scimat_format(st.session_state.df)
        st.session_state.scimat_output = scimat_output
        st.text_area("SciMAT 형식 데이터", scimat_output, height=300)

    if 'scimat_output' in st.session_state:
        st.download_button(
            label="변환된 파일 다운로드",
            data=st.session_state.scimat_output,
            file_name="wos_for_scimat.txt",
            mime="text/plain"
        )
