# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import altair as alt
import io

# --- 페이지 설정 ---
st.set_page_config(
    page_title="WOS Prep | SCIMAT Edition",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 커스텀 CSS 스타일 ---
st.markdown("""
<style>
    /* 여기에 기존 CSS 코드를 모두 붙여넣으세요 */
    .main-container {
        background: #f8f9fa;
        min-height: 100vh;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 20px rgba(0,56,117,0.15);
        border-color: #003875;
    }
    .metric-value {
        font-size: 2.8rem;
        font-weight: 700;
        color: #003875;
        margin: 0;
        line-height: 1;
    }
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
        margin: 8px 0 0 0;
        font-weight: 500;
    }
    .metric-icon {
        background: linear-gradient(135deg, #003875, #0056b3);
        color: white;
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 16px;
    }
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
        margin: 16px 0;
    }
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #212529;
        margin-bottom: 16px;
        border-bottom: 2px solid #003875;
        padding-bottom: 8px;
    }
    .section-header {
        background: linear-gradient(135deg, #003875, #0056b3);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin: 24px 0 16px 0;
        box-shadow: 0 4px 16px rgba(0,56,117,0.2);
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
    }
    .section-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin: 4px 0 0 0;
    }
    .upload-zone {
        background: white;
        border: 2px dashed #003875;
        border-radius: 12px;
        padding: 40px 20px;
        text-align: center;
        margin: 20px 0;
        transition: all 0.3s ease;
    }
    .upload-zone:hover {
        background: #f8f9fa;
        border-color: #0056b3;
    }
</style>
""", unsafe_allow_html=True)


# --- 데이터 처리 함수들 ---

def parse_wos_format(content):
    """WOS Plain Text 형식을 DataFrame으로 변환합니다."""
    records = []
    current_record = {}
    current_field = None
    # 'PT', 'AU' 등 WOS 태그는 두 글자로 고정되어 있음
    field_tag_pattern = re.compile(r"^([A-Z0-9]{2})\s(.*)$")

    lines = content.split('\n')
    for line in lines:
        line = line.rstrip()
        if not line:
            continue

        if line == 'ER':
            if current_record:
                records.append(current_record)
            current_record = {}
            current_field = None
            continue

        if line.startswith('   '): # 연속되는 필드 값 처리
            if current_field in current_record:
                # 여러 저자, 키워드 등을 세미콜론으로 구분하여 추가
                current_record[current_field] += '; ' + line.strip()
        else:
            match = field_tag_pattern.match(line)
            if match:
                current_field, value = match.groups()
                current_record[current_field] = value.strip()

    if current_record: # 마지막 레코드 추가
        records.append(current_record)

    if not records:
        return None
    return pd.DataFrame(records)


def load_and_merge_wos_files(uploaded_files):
    """다중 WOS 파일을 병합하고, 강화된 중복 제거 로직을 적용합니다."""
    all_dataframes = []
    file_status = []

    for uploaded_file in uploaded_files:
        try:
            file_bytes = uploaded_file.getvalue()
            detected_encoding = None
            decoded_content = None

            for encoding in ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1']:
                try:
                    decoded_content = file_bytes.decode(encoding)
                    # 파일 시작 부분이 WOS 형식인지 간단히 확인
                    if decoded_content.strip().startswith('FN '):
                        detected_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue

            if not decoded_content or not detected_encoding:
                file_status.append({
                    'filename': uploaded_file.name, 'status': 'ERROR', 'message': '❌ 지원되지 않는 파일 형식 또는 인코딩입니다.'
                })
                continue

            df = parse_wos_format(decoded_content)
            if df is not None and not df.empty:
                all_dataframes.append(df)
                file_status.append({
                    'filename': uploaded_file.name, 'status': 'SUCCESS', 'message': f'✅ {len(df)}편 논문 로딩 성공 (인코딩: {detected_encoding})'
                })
            else:
                 file_status.append({
                    'filename': uploaded_file.name, 'status': 'ERROR', 'message': '❌ WOS Plain Text 형식이 아니거나 내용이 없습니다.'
                })

        except Exception as e:
            file_status.append({
                'filename': uploaded_file.name, 'status': 'ERROR', 'message': f'❌ 파일 처리 중 오류 발생: {e}'
            })

    if not all_dataframes:
        return None, file_status, 0

    merged_df = pd.concat(all_dataframes, ignore_index=True)
    original_count = len(merged_df)

    # 1단계: UT (고유 식별자) 기준으로 중복 제거
    if 'UT' in merged_df.columns:
        # UT 값이 없는 경우를 대비해 NaN을 고유한 값으로 처리
        merged_df['UT'] = merged_df['UT'].fillna(pd.NA)
        merged_df.dropna(subset=['UT'], inplace=True)
        merged_df.drop_duplicates(subset=['UT'], keep='first', inplace=True)

    # 2단계: UT가 없는 경우를 대비해 제목(TI)과 저자(AU) 조합으로 중복 제거
    if 'TI' in merged_df.columns and 'AU' in merged_df.columns:
        # 저자 목록의 순서나 공백 차이를 무시하기 위해 정규화
        merged_df['AU_normalized'] = merged_df['AU'].str.lower().str.replace(r'[^a-z]', '', regex=True)
        merged_df.drop_duplicates(subset=['TI', 'AU_normalized'], keep='first', inplace=True)
        merged_df.drop(columns=['AU_normalized'], inplace=True)

    final_count = len(merged_df)
    duplicates_removed = original_count - final_count

    return merged_df, file_status, duplicates_removed

def classify_article(row):
    """라이브 스트리밍 연구를 위한 포괄적 분류 함수."""
    # 텍스트 추출 및 소문자 변환
    def extract_text(value):
        return str(value).lower() if pd.notna(value) else ""

    title = extract_text(row.get('TI'))
    keywords = extract_text(row.get('DE')) + " " + extract_text(row.get('ID'))
    abstract = extract_text(row.get('AB'))
    full_text = title + " " + keywords + " " + abstract

    # 분류 키워드 정의 (더 정교하게)
    core_streaming = ['live stream', 'livestream', 'live video', 'real-time stream', 'live commerce', 'streamer']
    related_digital = ['social media', 'e-commerce', 'influencer', 'digital marketing', 'online education', 'telemedicine']
    technical_exclude = ['routing protocol', 'network topology', 'vlsi design', 'antenna design', 'signal processing']

    # 분류 로직
    if any(keyword in full_text for keyword in technical_exclude):
        return 'Exclude (기술적 비관련)'
    if any(keyword in full_text for keyword in core_streaming):
        return 'Include (핵심연구)'
    if any(keyword in full_text for keyword in related_digital):
        # 'live', 'real-time' 등과 함께 나타나면 관련 연구로 간주
        if 'live' in full_text or 'real-time' in full_text or 'interactive' in full_text:
             return 'Include (관련연구)'
        else:
             return 'Review (관련성 검토)'
    return 'Review (분류 불확실)'

def convert_to_scimat_wos_format(df_to_convert):
    """DataFrame을 SCIMAT 호환 WOS Plain Text 형식으로 변환합니다."""
    # SCIMAT이 인식하는 표준 필드 순서
    wos_field_order = [
        'PT', 'AU', 'AF', 'TI', 'SO', 'LA', 'DT', 'DE', 'ID', 'AB', 'C1', 'RP',
        'EM', 'FU', 'FX', 'CR', 'NR', 'TC', 'PU', 'PI', 'PA', 'SN', 'J9', 'JI',
        'PD', 'PY', 'VL', 'IS', 'BP', 'EP', 'DI', 'PG', 'WC', 'SC', 'GA', 'UT'
    ]
    multi_line_fields = ['AU', 'AF', 'DE', 'ID', 'C1', 'CR']

    content_lines = ["FN Clarivate Analytics Web of Science", "VR 1.0"]
    for _, row in df_to_convert.iterrows():
        # 레코드 사이에 공백 라인 추가
        if len(content_lines) > 2:
            content_lines.append("")

        for tag in wos_field_order:
            if tag in row.index and pd.notna(row[tag]):
                value = str(row[tag]).strip()
                if not value: continue

                if tag in multi_line_fields:
                    # 세미콜론으로 구분된 항목들을 여러 줄로 나눔
                    items = [item.strip() for item in value.split(';') if item.strip()]
                    if items:
                        content_lines.append(f"{tag:<2} {items[0]}")
                        for item in items[1:]:
                            content_lines.append(f"   {item}")
                else:
                    content_lines.append(f"{tag:<2} {value}")
        content_lines.append("ER")

    # 파일 끝에 EF(End of File) 추가
    content_lines.append("EF")
    return "\n".join(content_lines).encode('utf-8-sig')


# --- UI 렌더링 시작 ---

st.markdown("""
<div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #003875, #0056b3); color: white; border-radius: 16px; margin-bottom: 2rem;">
    <h1 style="font-size: 3.5rem; font-weight: 700;">WOS PREP</h1>
    <p style="font-size: 1.3rem;">SCIMAT Edition</p>
</div>
""", unsafe_allow_html=True)

# --- 파일 업로드 섹션 ---
st.markdown("""
<div class="section-header">
    <div class="section-title">📁 다중 WOS Plain Text 파일 업로드</div>
    <div class="section-subtitle">500개 단위로 나뉜 여러 WOS 파일을 모두 선택하여 업로드하세요</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="upload-zone">
    <div style="font-size: 3rem; margin-bottom: 16px; color: #003875;">📤</div>
    <h3 style="color: #212529;">WOS Plain Text 파일들을 여기에 드래그하거나 클릭하세요</h3>
    <p style="color: #6c757d;">Ctrl 키를 누르고 여러 파일을 동시에 선택할 수 있습니다.</p>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "WOS Plain Text 파일 선택",
    type=['txt'],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    with st.spinner(f"🔄 {len(uploaded_files)}개 WOS 파일 병합 및 분석 중... 잠시만 기다려주세요."):
        merged_df, file_status, duplicates_removed = load_and_merge_wos_files(uploaded_files)

    if merged_df is None or merged_df.empty:
        st.error("⚠️ 처리 가능한 WOS Plain Text 파일이 없습니다. 파일 형식을 확인해주세요.")
        # 파일별 상세 상태 표시
        st.markdown("### 📄 파일별 처리 상태")
        for status in file_status:
            st.warning(f"**{status['filename']}**: {status['message']}")
        st.stop()

    # --- 데이터 처리 및 통계 계산 (한 번에 수행) ---
    merged_df['Classification'] = merged_df.apply(classify_article, axis=1)

    # 통계치 중앙 계산
    successful_files = len([s for s in file_status if s['status'] == 'SUCCESS'])
    total_papers = len(merged_df)
    classification_counts = merged_df['Classification'].value_counts()
    include_papers = classification_counts[classification_counts.index.str.contains('Include', na=False)].sum()
    review_papers_count = classification_counts[classification_counts.index.str.contains('Review', na=False)].sum()
    exclude_papers_count = classification_counts[classification_counts.index.str.contains('Exclude', na=False)].sum()

    st.success(f"✅ 병합 및 분석 완료! {successful_files}개 파일에서 {total_papers:,}편의 고유한 논문을 성공적으로 처리했습니다.")
    if duplicates_removed > 0:
        st.info(f"🔄 중복 논문 {duplicates_removed}편이 자동으로 제거되었습니다.")

    # --- 분석 결과 요약 대시보드 ---
    st.markdown("---")
    st.markdown("## 📈 병합 데이터 분석 결과")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 논문 수", f"{total_papers:,}편")
    with col2:
        st.metric("핵심 연구 (Include)", f"{include_papers:,}편")
    with col3:
        st.metric("검토 대상 (Review)", f"{review_papers_count:,}편")
    with col4:
        st.metric("제외 대상 (Exclude)", f"{exclude_papers_count:,}편")
    st.markdown("---")


    # --- 논문 분류 현황 (차트와 테이블) ---
    st.markdown("## 📊 논문 분류 현황")
    col1, col2 = st.columns([0.4, 0.6])

    with col1:
        st.dataframe(classification_counts.reset_index(), use_container_width=True, hide_index=True)

    with col2:
        chart_data = classification_counts.reset_index()
        chart_data.columns = ['Classification', 'Count']
        donut_chart = alt.Chart(chart_data).mark_arc(innerRadius=70).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Classification", type="nominal", title="분류"),
            tooltip=['Classification', 'Count']
        ).properties(
            width=500,
            height=350
        )
        st.altair_chart(donut_chart, use_container_width=True)


    # --- 연도별 연구 동향 ---
    if 'PY' in merged_df.columns:
        st.markdown("## 🗓️ 연도별 연구 동향")
        try:
            df_trend = merged_df.copy()
            df_trend['PY'] = pd.to_numeric(df_trend['PY'], errors='coerce')
            df_trend.dropna(subset=['PY'], inplace=True)
            df_trend['PY'] = df_trend['PY'].astype(int)

            yearly_counts = df_trend['PY'].value_counts().reset_index()
            yearly_counts.columns = ['Year', 'Count']
            yearly_counts = yearly_counts.sort_values('Year')

            line_chart = alt.Chart(yearly_counts).mark_line(point=True).encode(
                x=alt.X('Year:O', title='발행 연도'),
                y=alt.Y('Count:Q', title='논문 수'),
                tooltip=['Year', 'Count']
            ).properties(height=300)
            st.altair_chart(line_chart, use_container_width=True)
        except Exception as e:
            st.warning(f"연도별 연구 동향 차트를 생성하는 중 오류가 발생했습니다: {e}")


    # --- 분류별 논문 상세 목록 (Expander) ---
    st.markdown("---")
    st.markdown("## 📂 분류별 논문 상세 목록")

    # Review 논문 목록
    if review_papers_count > 0:
        with st.expander(f"📝 Review (검토 필요) - {review_papers_count}편"):
            review_df = merged_df[merged_df['Classification'].str.contains('Review', na=False)]
            st.dataframe(review_df[['TI', 'AU', 'PY', 'SO', 'Classification']].rename(columns={
                'TI':'제목', 'AU':'저자', 'PY':'연도', 'SO':'저널', 'Classification':'분류'
            }), hide_index=True)

    # Exclude 논문 목록
    if exclude_papers_count > 0:
        with st.expander(f"❌ Exclude (제외 대상) - {exclude_papers_count}편"):
            exclude_df = merged_df[merged_df['Classification'].str.contains('Exclude', na=False)]
            st.dataframe(exclude_df[['TI', 'AU', 'PY', 'SO']].rename(columns={
                'TI':'제목', 'AU':'저자', 'PY':'연도', 'SO':'저널'
            }), hide_index=True)


    # --- 최종 파일 다운로드 섹션 ---
    st.markdown("---")
    st.markdown("## 📥 최종 파일 다운로드")

    # 분석 대상 데이터 (Exclude 제외)
    df_final_output = merged_df[~merged_df['Classification'].str.contains('Exclude', na=False)].copy()
    # WOS 형식 유지를 위해 추가했던 Classification 컬럼 제거
    df_final_output.drop(columns=['Classification'], errors='ignore', inplace=True)

    st.info(f"**총 {len(df_final_output):,}편**의 논문(Include 및 Review)이 SCIMAT 분석용 파일에 포함됩니다.")

    # SCIMAT 호환 파일 다운로드 버튼
    text_data = convert_to_scimat_wos_format(df_final_output)
    st.download_button(
        label="🚀 SCIMAT 분석용 파일 다운로드 (.txt)",
        data=text_data,
        file_name="scimat_ready_merged_data.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
    )

    # 엑셀 파일 다운로드 버튼 (모든 정보 포함)
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        merged_df.to_excel(writer, sheet_name='Merged_Data', index=False)
    st.download_button(
        label="📊 전체 결과 엑셀로 다운로드 (.xlsx)",
        data=excel_buffer.getvalue(),
        file_name="wos_classification_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
