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

# สไตล์ CSS เพิ่มความสวยงาม
st.markdown("""
    <style>
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
    .metric-box {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# หัวข้อหลักของ Dashboard
st.markdown('<div class="main-title">📊ระบบรายงานสถิติตัวชี้วัดเป้าหมายการพัฒนาที่ยั่งยืน (SDGs)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">สถาบันวิจัยพฤติกรรมศาสตร์ มหาวิทยาลัยศรีนครินทรวิโรฒ</div>', unsafe_allow_html=True)

# ฟังก์ชันดึงข้อมูลจาก Google Sheets
@st.cache_data
def load_data():
    sheet_id = "13L0ou9OMP0-Y1U-z6KiOeafXb0qnKnNhGSUzWWDuRJo"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        df = pd.read_csv(url)
        
        # ค้นหาและจับคู่ชื่อคอลัมน์อัตโนมัติ
        rename_dict = {}
        for col in df.columns:
            if 'ปี' in col or 'year' in col.lower():
                rename_dict[col] = 'Year'
            elif 'sdg' in col.lower() or 'เป้าหมาย' in col:
                rename_dict[col] = 'SDG'
            elif 'บทความ' in col or 'title' in col.lower() or 'ชื่อ' in col:
                rename_dict[col] = 'Title'
                
        df = df.rename(columns=rename_dict)
        
        # จัดการกรณีไม่มีคอลัมน์หลัก
        if 'Year' not in df.columns: df['Year'] = 2026
        if 'SDG' not in df.columns: df['SDG'] = "ไม่ระบุ"
        if 'Title' not in df.columns: df['Title'] = "บทความวิจัย"
        
        # ทำความสะอาดข้อมูล ป้องกัน Error เรื่องประเภทข้อมูล
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)
        df['SDG'] = df['SDG'].fillna("ไม่ระบุ").astype(str).str.strip()
        
        return df
    except Exception as e:
        # หากดึงข้อมูลไม่ได้ ให้ใช้ Mock Data แสดงโครงสร้างก่อน
        mock_data = {
            'Year': [2023, 2023, 2024, 2024, 2025, 2025, 2026],
            'SDG': ['SDG 3', 'SDG 4', 'SDG 3', 'SDG 13', 'SDG 4', 'SDG 17', 'SDG 5'],
            'Title': [f'บทความวิจัยเรื่องที่ {i}' for i in range(1, 8)]
        }
        return pd.DataFrame(mock_data)

df_raw = load_data()

# แตกแถวกรณีมีหลาย SDG คั่นด้วยจุลภาค
df_exploded = df_raw.copy()
df_exploded['SDG_Split'] = df_exploded['SDG'].str.split(',')
df_exploded = df_exploded.explode('SDG_Split')
df_exploded['SDG_Split'] = df_exploded['SDG_Split'].fillna("ไม่ระบุ").astype(str).str.strip()

# ==========================================
# ส่วนของ FILTERS (แถบด้านข้าง Sidebar)
# ==========================================
st.sidebar.header("🔍 ตัวกรองข้อมูล (Filters)")

years_list = sorted(df_raw['Year'].unique())
if 0 in years_list: years_list.remove(0)
selected_years = st.sidebar.multiselect("เลือกปี ค.ศ.", options=years_list, default=years_list)

sdg_list = sorted(df_exploded['SDG_Split'].unique())
selected_sdgs = st.sidebar.multiselect("เลือกเป้าหมาย SDG", options=sdg_list, default=sdg_list)

# กรองข้อมูลตามเงื่อนไขที่เลือก
df_filtered_raw = df_raw[df_raw['Year'].isin(selected_years)]
df_filtered_exploded = df_exploded[
    (df_exploded['Year'].isin(selected_years)) & 
    (df_exploded['SDG_Split'].isin(selected_sdgs))
]

# ==========================================
# 1. ส่วนสรุปภาพรวมสำหรับผู้บริหาร (Executive Summary)
# ==========================================
st.subheader("🏢 สำหรับผู้บริหาร: ภาพรวมการดำเนินงาน")

col1, col2, col3 = st.columns(3)

with col1:
    total_articles = df_filtered_raw.shape[0]
    st.metric(label="📄 จำนวนบทความทั้งหมด (ตามตัวกรอง)", value=f"{total_articles} บทความ")

with col2:
    # นับบทความที่สอดคล้อง (ไม่เป็นค่าว่าง หรือ 'ไม่ระบุ')
    matching_sdg_count = df_filtered_raw[
        df_filtered_raw['SDG'].notna() & 
        (df_filtered_raw['SDG'] != '') & 
        (~df_filtered_raw['SDG'].str.lower().str.contains('ไม่ระบุ', na=True)) &
        (~df_filtered_raw['SDG'].str.lower().str.contains('nan', na=True))
    ].shape[0]
    
    st.metric(
        label="🎯 บทความที่สอดคล้องกับ SDG", 
        value=f"{matching_sdg_count} / {total_articles}",
        delta=f"คิดเป็น {(matching_sdg_count/total_articles*100):.1f}%" if total_articles > 0 else "0%"
    )

with col3:
    if len(selected_years) > 0:
        year_range = f"{min(selected_years)} - {max(selected_years)}"
    else:
        year_range = "-"
    st.metric(label="📅 ช่วงปีที่เผยแพร่ข้อมูล", value=year_range)

st.write("---")

# ส่วนแสดงกราฟสรุป
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**📈 5) จำนวนบทความวิจัยแยกตามปี ค.ศ.**")
    df_year_count = df_filtered_raw.groupby('Year').size().reset_index(name='จำนวนบทความ')
    fig_year = px.line(
        df_year_count, x='Year', y='จำนวนบทความ', 
        markers=True, text='จำนวนบทความ',
        color_discrete_sequence=['#1E3A8A']
    )
    fig_year.update_traces(textposition="top center")
    fig_year.update_layout(xaxis_title="ปี ค.ศ.", yaxis_title="จำนวนบทความ (เรื่อง)")
    st.plotly_chart(fig_year, use_container_width=True)

with chart_col2:
    st.markdown("**📊 4) สัดส่วนและจำนวนบทความจำแนกตามเป้าหมาย SDG (1-17)**")
    df_sdg_count = df_filtered_exploded.groupby('SDG_Split').size().reset_index(name='จำนวนบทความ')
    df_sdg_count = df_sdg_count.sort_values(by='จำนวนบทความ', ascending=True)
    
    fig_sdg = px.bar(
        df_sdg_count, x='จำนวนบทความ', y='SDG_Split', 
        orientation='h', text='จำนวนบทความ',
        color='จำนวนบทความ', color_continuous_scale='Blues'
    )
    fig_sdg.update_traces(textposition="outside")
    fig_sdg.update_layout(yaxis_title="เป้าหมาย SDG", xaxis_title="จำนวนบทความ (เรื่อง)", showlegend=False)
    st.plotly_chart(fig_sdg, use_container_width=True)

# ==========================================
# 2. ส่วนรายละเอียดเชิงลึกสำหรับทีมปฏิบัติการ (Operational Insights)
# ==========================================
st.write("---")
st.subheader("🔬 สำหรับทีมปฏิบัติการ: รายละเอียดเชิงลึกและข้อมูลดิบ")

st.markdown("**📊 6) จำนวนบทความที่สอดคล้องในแต่ละ SDG แยกตามปี ค.ศ. (เปรียบเทียบแนวโน้ม)**")
if not df_filtered_exploded.empty:
    df_cross = df_filtered_exploded.groupby(['Year', 'SDG_Split']).size().reset_index(name='จำนวนบทความ')
    fig_cross = px.bar(
        df_cross, x='SDG_Split', y='จำนวนบทความ', color='Year',
        barmode='group', text='จำนวนบทความ',
        labels={'SDG_Split': 'เป้าหมาย SDG', 'Year': 'ปี ค.ศ.'},
        color_continuous_scale='Viridis'
    )
    fig_cross.update_traces(textposition='outside')
    st.plotly_chart(fig_cross, use_container_width=True)
else:
    st.info("ไม่มีข้อมูลสอดคล้องตามตัวกรองที่เลือก")

st.markdown("**📋 ตารางข้อมูลบทความวิจัยทั้งหมด (กรองแล้ว)**")
st.dataframe(df_filtered_raw, use_container_width=True)

csv = df_filtered_raw.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="📥 ดาวน์โหลดข้อมูลชุดนี้เป็น CSV",
    data=csv,
    file_name='bsri_articles_sdg_filtered.csv',
    mime='text/csv',
)

st.caption("ระบบดึงข้อมูลอัปเดตแบบ Real-time จาก Google Sheets ของสถาบันวิจัยพฤติกรรมศาสตร์")
