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
    .main-title { font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .sub-title { font-size: 16px; color: #4B5563; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊ระบบรายงานสถิติตัวชี้วัดเป้าหมายการพัฒนาที่ยั่งยืน (SDGs)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">สถาบันวิจัยพฤติกรรมศาสตร์ มหาวิทยาลัยศรีนครินทรวิโรฒ</div>', unsafe_allow_html=True)

# ฟังก์ชันดึงข้อมูลจาก Google Sheets (เวอร์ชันตรวจสอบความจริง)
@st.cache_data
def load_data():
    sheet_id = "13L0ou9OMP0-Y1U-z6KiOeafXb0qnKnNhGSUzWWDuRJo"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    # ดึงข้อมูลดิบมาตรงๆ ไม่ใช้ try-except เพื่อดูเออร์เรอร์ที่แท้จริง
    df = pd.read_csv(url)
    df.columns = [str(c).strip() for c in df.columns]
    
    # แสดงชื่อคอลัมน์ทั้งหมดที่ระบบอ่านได้จาก Google Sheet จริงขึ้นบนหน้าจอชั่วคราว
    st.info(f"📋 ชื่อคอลัมน์ที่ระบบอ่านได้จริงจาก Google Sheets: {list(df.columns)}")
    
    rename_dict = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'year2' in col_lower:
            rename_dict[col] = 'Year'
        elif 'sdg' in col_lower or 'เป้าหมาย' in col_lower:
            rename_dict[col] = 'SDG'
        elif 'บทความ' in col_lower or 'title' in col_lower or 'ชื่อ' in col_lower:
            rename_dict[col] = 'Title'
            
    df = df.rename(columns=rename_dict)
    
    # แปลงชนิดข้อมูล
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(0).astype(int)
    df['SDG'] = df['SDG'].fillna("ไม่ระบุ").astype(str).str.strip()
    df['Title'] = df['Title'].fillna("ไม่ระบุชื่อบทความ").astype(str).str.strip()
    
    return df

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
if not years_list: years_list = [2026]
selected_years = st.sidebar.multiselect("เลือกปี ค.ศ.", options=years_list, default=years_list)

sdg_list = sorted([str(s) for s in df_exploded['SDG_Split'].unique() if str(s).strip() != ''])
selected_sdgs = st.sidebar.multiselect("เลือกเป้าหมาย SDG", options=sdg_list, default=sdg_list)

df_filtered_raw = df_raw[df_raw['Year'].isin(selected_years)]
df_filtered_exploded = df_exploded[(df_exploded['Year'].isin(selected_years)) & (df_exploded['SDG_Split'].isin(selected_sdgs))]

# ==========================================
# แสดงผลตารางและกราฟ
# ==========================================
st.subheader("🏢 ภาพรวมข้อมูลจริงจาก Google Sheets")
total_articles = df_filtered_raw.shape[0]
st.metric(label="📄 จำนวนบทความทั้งหมด", value=f"{total_articles} บทความ")

st.markdown("**📋 ตารางข้อมูลจริงจาก Google Sheets**")
st.dataframe(df_filtered_raw, use_container_width=True)
