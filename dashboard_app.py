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
        
        # ค้นหาและจับคู่ชื่อคอลัมน์อัตโนมัติ (เพิ่มรองรับ Year2)
        rename_dict = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if 'year2' in col_lower:
                rename_dict[col] = 'Year'
            elif 'ปี' in col_lower or 'year' in col_lower:
                if 'Year' not in rename_dict.values(): # ถ้ายังไม่มีการจับคู่ Year2 ให้ใช้คอลัมน์ปีทั่วไป
                    rename_dict[col] = 'Year'
            elif 'sdg' in col_lower or 'เป้าหมาย' in col_lower:
                rename_dict[col] = 'SDG'
            elif 'บทความ' in col_lower or 'title' in col_lower or 'ชื่อ' in col_lower:
                rename_dict[col] = 'Title'
                
        df = df.rename(columns=rename_dict)
        
        # จัดการกรณีระบบหาคอลัมน์หลักไม่เจอ
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
