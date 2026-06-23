import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าจอ Dashboard
st.set_page_config(
    page_title="BSRI Research Articles & SDGs Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ดึงฟอนต์ K2D จาก Google Fonts และบังคับใช้ด้วย CSS ที่ถูกต้อง
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=K2D:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stSidebar"], .stApp, p, h1, h2, h3, h4, h5, h6, span, div, button, select, input {
        font-family: 'K2D', sans-serif !important;
    }
    .main-title { 
        font-size: 28px; 
        font-weight: bold; 
        color: #1E3A8A; 
        margin-bottom: 5px; 
    }
    .sub-title { 
        font-size: 16px; 
        color: #4B5563; 
        margin-bottom: 25px; 
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊ระบบรายงานสถิติตัวชี้วัดเป้าหมายการพัฒนาที่ยั่งยืน (SDGs)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">สถาบันวิจัยพฤทีวกรรมศาสตร์ มหาวิทยาลัยศรีนครินทรวิโรฒ</div>', unsafe_allow_html=True)

# ฟังก์ชันดึงข้อมูลจาก Google Sheets
@st.cache_data
def load_data():
    sheet_id = "13L0ou9OMP0-Y1U-z6KiOeafXb0qnKnNhGSUzWWDuRJo"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    df = pd.read_csv(url)
    
    # ล้างชื่อคอลัมน์ ลบเว้นวรรค และลบตัวขึ้นบรรทัดใหม่ (\n) ออกให้หมด
    df.columns = [str(c).replace('\n', '').replace(' ', '').strip() for c in df.columns]
    
    # จับคู่คอลัมน์หลัก
    rename_dict = {}
    for col in df.columns:
        if col == 'Year':
            rename_dict[col] = 'Year'
        elif 'ArticleTitle(Thai)' in col:
            rename_dict[col] = 'Title'
        elif 'Author' in col:
            rename_dict[col] = 'Author'
            
    df = df.rename(columns=rename_dict)
    
    if 'Year' not in df.columns: df['Year'] = 2026
    if 'Title' not in df.columns: df['Title'] = "ไม่ระบุชื่อบทความ"
    if 'Author' not in df.columns: df['Author'] = "ไม่ระบุชื่อผู้แต่ง"
    
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)
    df['Title'] = df['Title'].fillna("ไม่ระบุชื่อบทความ").astype(str)
    df['Author'] = df['Author'].fillna("ไม่ระบุชื่อผู้แต่ง").astype(str)
    
    # รวบรวมข้อมูลจากคอลัมน์ SDG1 - SDG17
    sdg_cols = [c for c in df.columns if 'SDG' in c]
    
    exploded_records = []
    for _, row in df.iterrows():
        has_sdg = False
        for col in sdg_cols:
            val = str(row[col]).strip()
            if val != '' and val != 'nan' and val.lower() != 'none' and val != '0' and val != '0.0':
                sdg_name = col.replace('SDG', 'SDG ')
                exploded_records.append({
                    'Year': row['Year'],
                    'Title': row['Title'],
                    'Author': row['Author'],
                    'SDG_Target': sdg_name
                })
                has_sdg = True
        if not has_sdg:
            exploded_records.append({
                'Year': row['Year'],
                'Title': row['Title'],
                'Author': row['Author'],
                'SDG_Target': 'ไม่ระบุ SDG'
            })
            
    df_exploded = pd.DataFrame(exploded_records)
    return df, df_exploded

df_raw, df_exploded = load_data()

# ==========================================
# ส่วนของ FILTERS (แถบด้านข้าง Sidebar)
# ==========================================
st.sidebar.header("🔍 ตัวกรองข้อมูล (Filters)")

years_list = sorted([int(y) for y in df_raw['Year'].unique() if y > 0])
if not years_list: years_list = [2026]
selected_years = st.sidebar.multiselect("เลือกปี ค.ศ.", options=years_list, default=years_list)

sdg_list = sorted([str(s) for s in df_exploded['SDG_Target'].unique() if str(s).strip() != ''])
selected_sdgs = st.sidebar.multiselect("เลือกเป้าหมาย SDG", options=sdg_list, default=sdg_list)

# กรองข้อมูลตามเงื่อนไข
df_filtered_raw = df_raw[df_raw['Year'].isin(selected_years)]
df_filtered_exploded = df_exploded[
    (df_exploded['Year'].isin(selected_years)) & 
    (df_exploded['SDG_Target'].isin(selected_sdgs))
]

# ==========================================
# 1. ส่วนสรุปภาพรวมสำหรับผู้บริหาร (Executive Summary)
# ==========================================
st.subheader("🏢 สำหรับผู้บริหาร: ภาพรวมการดำเนินงาน")

col1, col2, col3 = st.columns(3)
total_articles = df_filtered_raw.shape[0]

with col1:
    st.metric(label="📄 จำนวนบทความทั้งหมด (ตามปีที่เลือก)", value=f"{total_articles} บทความ")

with col2:
    articles_with_sdg = df_filtered_exploded[df_filtered_exploded['SDG_Target'] != 'ไม่ระบุ SDG']['Title'].nunique()
    pct = (articles_with_sdg / total_articles * 100) if total_articles > 0 else 0
    st.metric(label="🎯 บทความที่สนับสนุนเป้าหมาย SDG", value=f"{articles_with_sdg} เรื่อง", delta=f"คิดเป็น {pct:.1f}%")

with col3:
    year_range = f"{min(selected_years)} - {max(selected_years)}" if selected_years else "-"
    st.metric(label="📅 ช่วงปีงบประมาณ/เผยแพร่", value=year_range)

st.write("---")

# ส่วนแสดงกราฟ
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**📈 จำนวนบทความวิจัยแยกตามปี ค.ศ.**")
    if not df_filtered_raw.empty:
        df_year_count = df_filtered_raw.groupby('Year').size().reset_index(name='จำนวนบทความ')
        fig_year = px.line(df_year_count, x='Year', y='จำนวนบทความ', markers=True, text='จำนวนบทความ', color_discrete_sequence=['#1E3A8A'])
        fig_year.update_traces(textposition="top center")
        fig_year.update_layout(font=dict(family="K2D", size=14))
        st.plotly_chart(fig_year, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถิติรายปี")

with chart_col2:
    st.markdown("**📊 จำนวนบทความจำแนกตามเป้าหมาย SDG**")
    df_sdg_plot = df_filtered_exploded[df_filtered_exploded['SDG_Target'] != 'ไม่ระบุ SDG']
    if not df_sdg_plot.empty:
        df_sdg_count = df_sdg_plot.groupby('SDG_Target').size().reset_index(name='จำนวนบทความ').sort_values(by='จำนวนบทความ', ascending=True)
        fig_sdg = px.bar(df_sdg_count, x='จำนวนบทความ', y='SDG_Target', orientation='h', text='จำนวนบทความ', color='จำนวนบทความ', color_continuous_scale='Blues')
        fig_sdg.update_traces(textposition="outside")
        fig_sdg.update_layout(font=dict(family="K2D", size=14))
        st.plotly_chart(fig_sdg, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลที่ตรงกับเป้าหมาย SDG")

# ==========================================
# 2. ส่วนตารางข้อมูลดิบ
# ==========================================
st.write("---")
st.subheader("🔬 รายละเอียดบทความวิจัยทั้งหมดจาก Google Sheets")

display_cols = [c for c in ['Year', 'Title', 'Author'] if c in df_filtered_raw.columns]
st.dataframe(df_filtered_raw[display_cols], use_container_width=True)

csv = df_filtered_raw[display_cols].to_csv(index=False).encode('utf-8-sig')
st.download_button(label="📥 ดาวน์โหลดข้อมูลชุดนี้เป็น CSV", data=csv, file_name='bsri_sdg_report.csv', mime='text/csv')
