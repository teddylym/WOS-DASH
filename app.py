import streamlit as st
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import re
from collections import Counter
import base64
from pathlib import Path

# --- 페이지 설정 ---
st.set_page_config(
    page_title="WOS Prep for SciMAT | Hanyang University Edition",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 이미지 파일을 Base64로 인코딩하는 함수 ---
# 이 함수는 로고 파일을 코드에 직접 삽입하여 GitHub 배포 시 파일 경로 문제를 방지합니다.
def get_image_as_base64(path):
    # 이미지 파일이 존재하는지 확인
    if not Path(path).exists():
        return None
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# --- 로고 및 CSS 설정 (한양대 UI 적용) ---
HANYANG_BLUE = "#003C71"  # 한양대학교 공식 블루 색상
LOGO_PATH = "HYU_logotype_blue_eng.png" # 코드와 동일한 위치에 있어야 할 로고 파일

encoded_logo = get_image_as_base64(LOGO_PATH)

# 로고가 파일 경로에 존재할 경우에만 HTML 생성
if encoded_logo:
    logo_html = f'<img src="data:image/png;base64,{encoded_logo}" style="height: 50px; margin-right: 20px;">'
else:
    logo_html = "" # 로고 파일이 없으면 비워둠

# 커스텀 CSS
st.markdown(f"""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {{
        background: #f8f9fa;
        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    }}

    /* 헤더 스타일 */
    .app-header {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        background-color: white;
        padding: 1.5rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }}

    .app-header h1 {{
        font-size: 2rem;
        font-weight: 700;
        color: {HANYANG_BLUE};
        margin: 0;
        line-height: 1.2;
    }}

    /* 메트릭 카드 스타일 */
    .metric-card {{
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin-bottom: 16px;
        transition: all 0.3s ease;
        text-align: center;
    }}

    .metric-card:hover {{
        box-shadow: 0 6px 20px rgba(0, 60, 113, 0.15);
        border-color: {HANYANG_BLUE};
        transform: translateY(-3px);
    }}

    .metric-value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {HANYANG_BLUE};
    }}

    .metric-label {{
        font-size: 1rem;
        color: #6c757d;
        font-weight: 500;
    }}

    /* 버튼 스타일 */
    .stButton > button {{
        font-weight: 600;
        border-radius: 8px;
        border: 2px solid {HANYANG_BLUE};
        background-color: {HANYANG_BLUE};
        color: white;
        width: 100%;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        background-color: white;
        color: {HANYANG_BLUE};
    }}
    .stDownloadButton > button {{
        font-weight: 600;
        border-radius: 8px;
        border: 2px solid {HANYANG_BLUE};
        background-color: {HANYANG_BLUE};
        color: white;
        width: 100%;
        transition: all 0.3s ease;
    }}
    .stDownloadButton > button:hover {{
        background-color: white;
        color: {HANYANG_BLUE};
    }}


    /* 구분선 스타일 */
    hr {{
        border-top: 1px solid #dee2e6;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }}
</style>
""", unsafe_allow_html=True)


# --- NLTK 리소스 다운로드 (최초 1회) ---
@st.cache_resource
def download_nltk_resources():
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet')
download_nltk_resources()


# --- 핵심 처리 함수들 ---
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_keywords(keywords):
    if not isinstance(keywords, str):
        return []
    # 세미콜론 기준으로 분리
    keywords = re.split(r';\s*', keywords)
    processed = []
    for keyword in keywords:
        kw_lower = keyword.lower().strip()
        # 불용어 처리 및 표제어 추출
        if kw_lower and kw_lower not in stop_words:
            lemma = lemmatizer.lemmatize(kw_lower)
            processed.append(lemma)
    return processed

def convert_df_to_scimat_format(df):
    output = []
    for _, row in df.iterrows():
        # 필수 필드만 선택하여 SciMAT 형식에 맞게 변환
        required_fields = {
            'AU': row.get('Authors', ''),
            'TI': row.get('Article Title', ''),
            'SO': row.get('Source Title', ''),
            'DE': row.get('Author Keywords', ''),
            'ID': row.get('Keywords Plus', ''),
            'AB': row.get('Abstract', ''),
            'C1': row.get('Addresses', ''),
            'PY': row.get('Publication Year', ''),
            'TC': row.get('WoS Core Collection Times Cited Count', '')
        }

        entry = ""
        for key, value in required_fields.items():
            # 값이 존재하고 비어있지 않을 경우에만 추가
            if pd.notna(value) and str(value).strip() != '':
                entry += f"{key} {str(value)}\n"

        output.append(entry + "ER\n")

    # 파일 시작 부분에 필수 헤더 추가
    header = "FN Thomson Reuters Web of Science\nVR 1.0\n"
    return header + "\n".join(output)

# --- 앱 UI 구성 ---

# 헤더
st.markdown(f"""
<div class="app-header">
    {logo_html}
    <h1>WOS Prep for SciMAT</h1>
</div>
""", unsafe_allow_html=True)

if not encoded_logo:
    st.warning(f"로고 파일을 찾을 수 없습니다. `{LOGO_PATH}` 파일이 코드와 동일한 위치에 있는지 확인해주세요.")

st.markdown("Web of Science 데이터를 SciMAT 분석에 최적화된 형태로 정제하고 변환합니다. 아래 절차에 따라 파일을 업로드하고 키워드를 정규화하세요.")

# 1. 파일 업로드
st.markdown("---")
st.header("1단계: WOS 데이터 파일 업로드")
st.info("Web of Science에서 다운로드한 **'Plain Text'** 형식의 파일을 업로드해주세요.", icon="📂")

uploaded_file = st.file_uploader(
    "파일을 이곳에 드래그하거나 클릭하여 업로드하세요.",
    type=['txt'],
    label_visibility="collapsed"
)

# 세션 상태 초기화
if 'df' not in st.session_state:
    st.session_state.df = None
    st.session_state.df_final = None
    st.session_state.normalization_applied = False
    st.session_state.normalized_count = 0


if uploaded_file is not None:
    try:
        # 파일 파싱
        content = uploaded_file.getvalue().decode('utf-8-sig')
        articles_raw = content.strip().split('\nER\n')
        
        records = []
        for article in articles_raw:
            if not article.strip().startswith('FN'): continue # 파일 헤더 건너뛰기
            
            record = {}
            # PT, AU, TI 등 2글자 코드로 시작하는 라인만 필드로 인식
            lines = article.strip().split('\n')
            field = None
            value_lines = []
            
            for i, line in enumerate(lines):
                # 파일의 시작(FN, VR)은 건너뛴다.
                if i < 2 and (line.startswith("FN") or line.startswith("VR")):
                    continue
                
                # 새로운 필드가 시작되면 이전 필드 저장
                if len(line) > 2 and line[2] == ' ' and line[:2].isalpha() and line[:2].isupper():
                    if field and value_lines:
                        record[field] = ' '.join(value_lines)
                    field = line[:2]
                    value_lines = [line[3:].strip()]
                # 필드가 계속되면 내용 추가
                elif field:
                    value_lines.append(line.strip())
            
            # 마지막 필드 저장
            if field and value_lines:
                record[field] = ' '.join(value_lines)
                
            if 'TI' in record: # 제목이 있는 레코드만 추가
                records.append(record)
        
        df = pd.DataFrame(records)
        # 컬럼 이름 변경 (WOS 표준 필드 -> 이해하기 쉬운 이름)
        df.rename(columns={
            'AU': 'Authors', 'TI': 'Article Title', 'SO': 'Source Title',
            'DE': 'Author Keywords', 'ID': 'Keywords Plus', 'AB': 'Abstract',
            'C1': 'Addresses', 'PY': 'Publication Year', 'TC': 'WoS Core Collection Times Cited Count'
        }, inplace=True)
        
        st.session_state.df = df
        st.session_state.df_final = df.copy() # 초기 최종본은 원본과 동일
        st.success(f"**{len(df)}개**의 논문 데이터를 성공적으로 불러왔습니다.")

    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        st.warning("파일이 Web of Science의 'Plain Text' 형식이 맞는지 확인해주세요.")
        st.stop()


if st.session_state.df is not None:
    df = st.session_state.df

    # 2. 키워드 정규화
    st.markdown("---")
    st.header("2단계: 키워드 정규화 (선택 사항)")
    st.markdown("분석 정확도를 높이기 위해 동의어, 단/복수형 등을 대표 키워드로 통일합니다. **'Author Keywords'**와 **'Keywords Plus'**에 모두 적용됩니다.")
    
    # 키워드 처리 및 빈도 분석 (df_processed는 UI 표시용 임시 데이터프레임)
    df_processed = df.copy()
    df_processed['DE_processed'] = df_processed['Author Keywords'].apply(preprocess_keywords)
    df_processed['ID_processed'] = df_processed['Keywords Plus'].apply(preprocess_keywords)
    
    all_keywords = df_processed['DE_processed'].sum() + df_processed['ID_processed'].sum()
    keyword_counts = Counter(all_keywords)
    df_keywords = pd.DataFrame(keyword_counts.items(), columns=['Keyword', 'Frequency']).sort_values(by='Frequency', ascending=False).reset_index(drop=True)

    with st.expander("키워드 빈도 분석 및 정규화 규칙 설정 보기", expanded=False):
        st.write(f"총 **{len(df_keywords)}개**의 고유 키워드가 발견되었습니다. (표제어 추출 및 불용어 제거 후)")
        st.dataframe(df_keywords, height=300, use_container_width=True)
        
        st.markdown("<h6>정규화 규칙 입력</h6>", unsafe_allow_html=True)
        st.markdown("`변경될 키워드: 대표 키워드` 형식으로 입력하세요. 여러 규칙은 **쉼표(,)**로 구분합니다.")
        
        normalization_rules_str = st.text_area(
            "정규화 규칙:", 
            key="normalization_rules",
            height=120,
            placeholder="예: big data analytics: big data, ai: artificial intelligence, technologies: technology"
        )

    # 3. 처리 및 다운로드
    st.markdown("---")
    st.header("3단계: 최종 결과 생성 및 다운로드")
    
    if st.button("✨ 정규화 적용 및 결과 생성", use_container_width=True):
        df_final = df.copy() # 항상 원본에서 시작
        
        if normalization_rules_str.strip():
            rules_list = [rule.strip() for rule in normalization_rules_str.split(',') if ':' in rule]
            normalization_map = {}
            for rule in rules_list:
                try:
                    target, representative = rule.split(':')
                    normalization_map[target.strip().lower()] = representative.strip()
                except ValueError:
                    st.warning(f"잘못된 형식의 규칙 '{rule}'은(는) 무시됩니다. '키워드: 대표키워드' 형식을 지켜주세요.")
            
            def apply_normalization(keywords_str):
                if not isinstance(keywords_str, str): return keywords_str, False
                
                keywords = re.split(r';\s*', keywords_str)
                normalized_keywords = []
                was_normalized = False
                
                for kw in keywords:
                    # 규칙 적용을 위해 소문자+표제어 변환
                    kw_processed = lemmatizer.lemmatize(kw.lower().strip())
                    
                    if kw_processed in normalization_map:
                        normalized_keywords.append(normalization_map[kw_processed])
                        was_normalized = True
                    else:
                        normalized_keywords.append(kw.strip()) # 원본 키워드 유지
                
                # 중복 제거 후 다시 문자열로 결합
                final_keywords = '; '.join(sorted(list(set(normalized_keywords))))
                return final_keywords, was_normalized

            # 'Author Keywords'와 'Keywords Plus'에 정규화 적용
            res_de = df_final['Author Keywords'].apply(apply_normalization)
            res_id = df_final['Keywords Plus'].apply(apply_normalization)
            
            df_final['Author Keywords'], normalized_de = zip(*res_de)
            df_final['Keywords Plus'], normalized_id = zip(*res_id)
            
            # 하나라도 정규화가 적용된 행을 찾기 위한 마스크
            normalization_mask = pd.Series(normalized_de) | pd.Series(normalized_id)
            st.session_state.normalized_count = normalization_mask.sum()
            st.success(f"**{st.session_state.normalized_count}개** 논문의 키워드에 정규화 규칙을 적용했습니다.")
        else:
            st.session_state.normalized_count = 0
            st.info("입력된 정규화 규칙이 없어 원본 데이터로 최종 파일을 생성합니다.")
        
        st.session_state.df_final = df_final
        st.session_state.normalization_applied = True


    if st.session_state.normalization_applied:
        df_to_show = st.session_state.df_final
        
        st.markdown("<h4>최종 데이터 미리보기</h4>", unsafe_allow_html=True)
        st.dataframe(df_to_show.head(), use_container_width=True)

        st.markdown("<h4>요약 통계</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(df_to_show):,}</div>
                <div class="metric-label">최종 분석 대상 논문</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.normalized_count:,}</div>
                <div class="metric-label">키워드 정규화 적용 논문</div>
            </div>
            """, unsafe_allow_html=True)

        # 다운로드 버튼
        text_data = convert_df_to_scimat_format(df_to_show)
        st.download_button(
            label="📥 SciMAT 호환 포맷 파일 다운로드 (.txt)",
            data=text_data,
            file_name="wos_for_scimat_hanyang.txt",
            mime="text/plain"
        )
