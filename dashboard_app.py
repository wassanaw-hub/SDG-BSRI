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
        
        # ล้างช่องว่างในชื่อคอลัมน์ทั้งหมดป้องกันบั๊กพิมพ์เว้นวรรค
        df.columns = [str(c).strip() for c in df.columns]
        
        rename_dict = {}
        for col in df.columns:
            col_lower = col.lower()
            # 1. ค้นหาคอลัมน์ปี (บังคับหา Year2 ก่อน)
            if 'year2' in col_lower:
                rename_dict[col] = 'Year'
            elif ('ปี' in col_lower or 'year' in col_lower) and ('Year' not in rename_dict.values()):
                rename_dict[col] = 'Year'
                
            # 2. ค้นหาคอลัมน์ SDG
            elif 'sdg' in col_lower or 'เป้าหมาย' in col_lower:
                rename_dict[col] = 'SDG'
                
            # 3. ค้นหาคอลัมน์ชื่อบทความ
            elif 'บทความ' in col_lower or 'title' in col_lower or 'ชื่อ' in col_lower:
                rename_dict[col] = 'Title'
                
        df = df.rename(columns=rename_dict)
        
        # ถ้ายังหาไม่เจอจริงๆ ให้กวาดตามลำดับตำแหน่งคอลัมน์ (Fallback)
        if 'Year' not in df.columns and len(df.columns) > 0:
            # สมมติว่าถ้าเจอคอลัมน์ไหนมีคำว่า Year ให้ใช้คอลัมน์นั้นเลย
            for c in df.columns:
                if 'year' in str(c).lower() or 'ปี' in str(c):
                    df = df.rename(columns={c: 'Year'})
                    break
        
        # ตรวจสอบขั้นสุดท้ายถ้าไม่มีคอลัมน์สร้างให้ใหม่ป้องกันระบบพัง
        if 'Year' not in df.columns: df['Year'] = 2026
        if 'SDG' not in df.columns: df['SDG'] = "ไม่ระบุ"
        if 'Title' not in df.columns: df['Title'] = "บทความวิจัย"
        
        # แปลงชนิดข้อมูลให้เสถียรที่สุด
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)
        df['SDG'] = df['SDG'].fillna("ไม่ระบุ").astype(str).str.strip()
        df['Title'] = df['Title'].fillna("ไม่ระบุชื่อบทความ").astype(str).str.strip()
        
        return df
    except Exception as e:
        # โหมดสำรองเผื่อลิงก์ชีตหลักมีปัญหา
        mock_data = {
            'Year': [2023, 2024, 2025, 2026],
            'SDG': ['SDG 3', 'SDG 4', 'SDG 13', 'SDG 5'],
            'Title': ['บทความจำลองระบบ 1', 'บทความจำลองระบบ 2', 'บทความจำลองระบบ 3', 'บทความจำลองระบบ 4']
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

years_list = sorted([int(y) for y in df_raw['Year'].unique() if y > 0])
if not years_list:
    years_list = [2023, 2024, 2025, 2026]
selected_years = st.sidebar.multiselect("เลือกปี ค.ศ.", options=years_list, default=years_list)

sdg_list = sorted([str(s) for s in df_exploded['SDG_Split'].unique() if str(s).strip() != ''])
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
total_articles = df_filtered_raw.shape[0]

with col1:
    st.metric(label="📄 จำนวนบทความทั้งหมด (ตามตัวกรอง)", value=f"{total_articles} บทความ")

with col2:
    matching_sdg_count = df_filtered_raw[
        df_filtered_raw['SDG'].notna() & 
        (df_filtered_raw['SDG'] != '') & 
        (~df_filtered_raw['SDG'].str.lower().str.contains('ไม่ระบุ', na=True)) &
        (~df_filtered_raw['SDG'].str.lower().str.contains('nan', na=True))
    ].shape[0]
    
    pct = (matching_sdg_count / total_articles * 100) if total_articles > 0 else 0
    st.metric(label="🎯 บทความที่สอดคล้องกับ SDG", value=f"{matching_sdg_count} / {total_articles}", delta=f"คิดเป็น {pct:.1f}%")

with col3:
    year_range = f"{min(selected_years)} - {max(selected_years)}" if selected_years else "-"
    st.metric(label="📅 ช่วงปีที่เผยแพร่ข้อมูล", value=year_range)

st.write("---")

# การแสดงผลกราฟ
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**📈 จำนวนบทความวิจัยแยกตามปี ค.ศ.**")
    if not df_filtered_raw.empty:
        df_year_count = df_filtered_raw.groupby('Year').size().reset_index(name='จำนวนบทความ')
        fig_year = px.line(df_year_count, x='Year', y='จำนวนบทความ', markers=True, text='จำนวนบทความ', color_discrete_sequence=['#1E3A8A'])
        fig_year.update_traces(textposition="top center")
        st.plotly_chart(fig_year, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถิติรายปี")

with chart_col2:
    st.markdown("**📊 สัดส่วนและจำนวนบทความจำแนกตามเป้าหมาย SDG**")
    if not df_filtered_exploded.empty:
        df_sdg_count = df_filtered_exploded.groupby('SDG_Split').size().reset_index(name='จำนวนบทความ').sort_values(by='จำนวนบทความ', ascending=True)
        fig_sdg = px.bar(df_sdg_count, x='จำนวนบทความ', y='SDG_Split', orientation='h', text='จำนวนบทความ', color='จำนวนบทความ', color_continuous_scale='Blues')
        fig_sdg.update_traces(textposition="outside")
        st.plotly_chart(fig_sdg, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลสถิติ SDG")

# ==========================================
# 2. ส่วนรายละเอียดเชิงลึกและข้อมูลดิบ
# ==========================================
st.write("---")
st.subheader("🔬 สำหรับทีมปฏิบัติการ: รายละเอียดเชิงลึกและข้อมูลดิบ")

st.markdown("**📋 ตารางข้อมูลบทความวิจัยทั้งหมด (กรองแล้ว)**")
st.dataframe(df_filtered_raw, use_container_width=True)

csv = df_filtered_raw.to_csv(index=False).encode('utf-8-sig')
st.download_button(label="📥 ดาวน์โหลดข้อมูลชุดนี้เป็น CSV", data=csv, file_name='bsri_articles_sdg_filtered.csv', mime='text/csv')
