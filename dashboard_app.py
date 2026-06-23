import streamlit as st
import pandas as pd
import plotly.express as px

# ตั้งค่าหน้าจอแบบ Wide และปิดเมนูพื้นฐานบางส่วนเพื่อความสวยงาม
st.set_page_config(
    page_title="BSRI SDG Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 จัดการสไตล์ดีไซน์ด้วย CSS (Font K2D + แบนเนอร์เขียวเข้ม + การ์ดมน)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=K2D:wght@300;400;500;600;700&display=swap');
    
    /* บังคับใช้ฟอนต์ K2D ทั้งเว็บแอป */
    html, body, [data-testid="stSidebar"], .stApp, p, h1, h2, h3, h4, h5, h6, span, div, button, select, input {
        font-family: 'K2D', sans-serif !important;
    }
    
    /* แบนเนอร์หัวเว็บสีเขียวเข้มตามแบบ */
    .banner-container {
        background-color: #0F5132;
        padding: 20px 30px;
        border-radius: 12px;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .banner-title {
        font-size: 28px;
        font-weight: 700;
        margin: 0;
    }
    .banner-subtitle {
        font-size: 15px;
        opacity: 0.85;
        margin: 5px 0 0 0;
    }
    
    /* ปรับแต่งสไตล์ของส่วน Metric Card ให้มีมิติ */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #111827 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        color: #4B5563 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #F8FAFC;
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* ตกแต่งกล่อง Sidebar กรองข้อมูล */
    [data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 🏢 แสดงผลแบนเนอร์ด้านบนสุด (Header Banner)
st.markdown("""
    <div class="banner-container">
        <div>
            <h1 class="banner-title">🌿 SDG Dashboard</h1>
            <p class="banner-subtitle">ภาพรวมบทความตามเป้าหมายการพัฒนาที่ยั่งยืน (SDGs) | สถาบันวิจัยพฤติกรรมศาสตร์ มศว</p>
        </div>
        <div style="text-align: right; font-size: 13px; opacity: 0.8;">
            ข้อมูลอัปเดตล่าสุด<br><b>30 มิ.ย. 2026</b>
        </div>
    </div>
""", unsafe_allow_html=True)

# ฟังก์ชันดึงข้อมูลจาก Google Sheets
@st.cache_data
def load_data():
    sheet_id = "13L0ou9OMP0-Y1U-z6KiOeafXb0qnKnNhGSUzWWDuRJo"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    df = pd.read_csv(url)
    
    # Clean คอลัมน์
    df.columns = [str(c).replace('\n', '').replace(' ', '').strip() for c in df.columns]
    
    rename_dict = {}
    for col in df.columns:
        if col == 'Year': rename_dict[col] = 'Year'
        elif 'ArticleTitle(Thai)' in col: rename_dict[col] = 'Title'
        elif 'Author' in col: rename_dict[col] = 'Author'
            
    df = df.rename(columns=rename_dict)
    
    if 'Year' not in df.columns: df['Year'] = 2026
    if 'Title' not in df.columns: df['Title'] = "ไม่ระบุชื่อบทความ"
    if 'Author' not in df.columns: df['Author'] = "ไม่ระบุชื่อผู้แต่ง"
    
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)
    df['Title'] = df['Title'].fillna("ไม่ระบุชื่อบทความ").astype(str)
    df['Author'] = df['Author'].fillna("ไม่ระบุชื่อผู้แต่ง").astype(str)
    
    # แตกโครงสร้าง SDG1 - SDG17
    sdg_cols = [c for c in df.columns if 'SDG' in c]
    exploded_records = []
    for _, row in df.iterrows():
        has_sdg = False
        for col in sdg_cols:
            val = str(row[col]).strip()
            if val != '' and val != 'nan' and val.lower() != 'none' and val != '0' and val != '0.0':
                sdg_num = col.replace('SDG', 'SDG ')
                exploded_records.append({
                    'Year': row['Year'], 'Title': row['Title'], 'Author': row['Author'], 'SDG_Target': sdg_num
                })
                has_sdg = True
        if not has_sdg:
            exploded_records.append({
                'Year': row['Year'], 'Title': row['Title'], 'Author': row['Author'], 'SDG_Target': 'ไม่ระบุ SDG'
            })
            
    return df, pd.DataFrame(exploded_records)

df_raw, df_exploded = load_data()

# ==========================================
# ส่วนของ SIDEBAR FILTERS
# ==========================================
st.sidebar.header("🔍 ตัวกรองข้อมูล")

years_list = sorted([int(y) for y in df_raw['Year'].unique() if y > 0])
selected_years = st.sidebar.multiselect("ปี ค.ศ.", options=years_list, default=years_list)

sdg_list = sorted([str(s) for s in df_exploded['SDG_Target'].unique() if str(s).strip() != ''])
selected_sdgs = st.sidebar.multiselect("เป้าหมาย SDG", options=sdg_list, default=sdg_list)

# กรองข้อมูลตามที่เลือกบน Sidebar
df_filtered_raw = df_raw[df_raw['Year'].isin(selected_years)]
df_filtered_exploded = df_exploded[
    (df_exploded['Year'].isin(selected_years)) & 
    (df_exploded['SDG_Target'].isin(selected_sdgs))
]

# ==========================================
# 📊 SECTION 1: เมทริกซ์การ์ด 4 ใบด้านบน
# ==========================================
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

total_articles = df_filtered_raw.shape[0]
total_sdgs = df_filtered_exploded[df_filtered_exploded['SDG_Target'] != 'ไม่ระบุ SDG']['SDG_Target'].nunique()
total_authors = df_filtered_raw['Author'].nunique()
year_range_str = f"{min(selected_years)}-{max(selected_years)}" if selected_years else "N/A"

with m_col1:
    st.metric(label="📄 จำนวนบทความทั้งหมด", value=f"{total_articles} บทความ")
with m_col2:
    st.metric(label="🎯 SDGs ที่เกี่ยวข้อง", value=f"{total_sdgs} เป้าหมาย")
with m_col3:
    st.metric(label="👥 ผู้แต่งทั้งหมด", value=f"{total_authors} คน")
with m_col4:
    st.metric(label="📅 ปีที่ครอบคลุมข้อมูล", value=year_range_str)

st.write("##")

# ==========================================
# 📈 SECTION 2: กราฟแถวบน (จำนวนบทความราย SDG และรายปี)
# ==========================================
chart_row1_col1, chart_row1_col2 = st.columns([1.6, 1.0])

with chart_row1_col1:
    st.markdown("### 📊 จำนวนบทความตาม SDG (1–17)")
    df_sdg_plot = df_filtered_exploded[df_filtered_exploded['SDG_Target'] != 'ไม่ระบุ SDG']
    if not df_sdg_plot.empty:
        df_sdg_count = df_sdg_plot.groupby('SDG_Target').size().reset_index(name='จำนวนบทความ')
        
        # จัดเรียงลำดับตามตัวเลข SDG เพื่อให้แสดงเรียงจาก 1 ไป 17
        df_sdg_count['sort_idx'] = df_sdg_count['SDG_Target'].str.extract('(\d+)').astype(int)
        df_sdg_count = df_sdg_count.sort_values('sort_idx')
        
        fig_sdg = px.bar(
            df_sdg_count, x='SDG_Target', y='จำนวนบทความ', 
            text='จำนวนบทความ', color='SDG_Target',
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_sdg.update_traces(textposition="outside")
        fig_sdg.update_layout(
            font=dict(family="K2D", size=13),
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="", yaxis_title="จำนวนบทความ (บทความ)"
        )
        st.plotly_chart(fig_sdg, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถิติเป้าหมาย")

with chart_row1_col2:
    st.markdown("### 📅 จำนวนบทความตามปี")
    if not df_filtered_raw.empty:
        df_year_count = df_filtered_raw.groupby('Year').size().reset_index(name='จำนวนบทความ')
        df_year_count['Year'] = df_year_count['Year'].astype(str)
        
        fig_year = px.bar(
            df_year_count, x='Year', y='จำนวนบทความ', 
            text='จำนวนบทความ', color_discrete_sequence=['#2563EB']
        )
        fig_year.update_traces(textposition="outside")
        fig_year.update_layout(
            font=dict(family="K2D", size=13),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="ปี", yaxis_title="จำนวนบทความ (บทความ)"
        )
        st.plotly_chart(fig_year, use_container_width=True)

# ==========================================
# 📊 SECTION 3: กราฟแถวล่าง (Top 10 SDGs & Top 10 ผู้แต่ง)
# ==========================================
chart_row2_col1, chart_row2_col2 = st.columns(2)

with chart_row2_col1:
    st.markdown("### 🏆 Top 10 SDGs ที่พบมากที่สุด")
    if not df_sdg_plot.empty:
        df_top_sdg = df_sdg_plot.groupby('SDG_Target').size().reset_index(name='จำนวนบทความ').sort_values(by='จำนวนบทความ', ascending=True).tail(10)
        fig_top_sdg = px.bar(
            df_top_sdg, x='จำนวนบทความ', y='SDG_Target', 
            orientation='h', text='จำนวนบทความ',
            color='จำนวนบทความ', color_continuous_scale='Greens'
        )
        fig_top_sdg.update_traces(textposition="outside")
        fig_top_sdg.update_layout(
            font=dict(family="K2D", size=12), 
            coloraxis_showscale=False, 
            xaxis_title="จำนวนบทความ (บทความ)", 
            yaxis_title="",
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_top_sdg, use_container_width=True)

with chart_row2_col2:
    st.markdown("### 👥 Top 10 ผู้แต่งที่มีบทความมากที่สุด")
    if not df_filtered_raw.empty:
        df_top_author = df_filtered_raw.groupby('Author').size().reset_index(name='จำนวนบทความ').sort_values(by='จำนวนบทความ', ascending=True).tail(10)
        fig_top_author = px.bar(
            df_top_author, x='จำนวนบทความ', y='Author', 
            orientation='h', text='จำนวนบทความ',
            color_discrete_sequence=['#84CC16']
        )
        fig_top_author.update_traces(textposition="outside")
        fig_top_author.update_layout(
            font=dict(family="K2D", size=12), 
            xaxis_title="จำนวนบทความ (บทความ)", 
            yaxis_title="",
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_top_author, use_container_width=True)

# ==========================================
# 🔬 SECTION 4: ตารางข้อมูลดิบด้านล่างสุด
# ==========================================
st.write("---")
st.subheader("🔬 รายละเอียดบทความวิจัยทั้งหมด")
display_cols = [c for c in ['Year', 'Title', 'Author'] if c in df_filtered_raw.columns]
st.dataframe(df_filtered_raw[display_cols], use_container_width=True)
