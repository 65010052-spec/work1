import streamlit as st
import pandas as pd
import numpy as np

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="ระบบสรุปยอดงานพนักงานประจำวัน",
    page_icon="📊",
    layout="wide"
)

# ปรับแต่งสไตล์หน้าเว็บ
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 20px; }
    .admin-box { background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; }
    .result-card { background-color: #EFF6FF; padding: 15px; border-radius: 8px; border: 1px solid #BFDBFE; margin-bottom: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ระบบ Login แถบข้าง ---
st.sidebar.markdown("## 🔒 ระบบเข้าสู่ระบบ")
user_role = st.sidebar.selectbox(
    "กรุณาเลือกชื่อของคุณเพื่อเข้าใช้งาน:",
    ["พนักงานทั่วไป (ดูข้อมูล)", "Admin 1", "Admin 2"]
)

if user_role in ["Admin 1", "Admin 2"]:
    st.sidebar.success(f"⚡ สถานะ: {user_role} (สิทธิ์ผู้ดูแลระบบ)")
else:
    st.sidebar.info("👤 สถานะ: พนักงานทั่วไป")

st.sidebar.markdown("---")

# --- 3. หน้าตาหลัก ---
st.markdown('<div class="main-title">📊 ระบบบันทึกและสรุปยอดงานพนักงานประจำวัน</div>', unsafe_allow_html=True)

if 'database' not in st.session_state:
    st.session_state['database'] = None

# --- 4. ส่วนของ Admin อัปโหลดไฟล์ ---
if user_role in ["Admin 1", "Admin 2"]:
    st.markdown('<div class="admin-box">', unsafe_allow_html=True)
    st.subheader("📥 พื้นที่สำหรับ Admin: อัปโหลดไฟล์ Excel ยอดงาน")
    
    uploaded_file = st.file_uploader("โยนไฟล์ Excel (.xlsx) หรือ CSV ตรงนี้", type=["xlsx", "csv"], key="uploader")
    
    if uploaded_file is not None:
        try:
            # อ่านไฟล์แบบไม่ดึงหัวตาราง เพื่อมาจัดการเองเนื่องจากโครงสร้างไฟล์ซับซ้อน
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file, header=None)
            else:
                raw_df = pd.read_excel(uploaded_file, header=None)
                
            # ค้นหาแถวที่เป็นหัวตารางจริง (ที่มีคำว่า DATE หรือ Date หรือ date)
            header_row_idx = None
            for idx, row in raw_df.iterrows():
                row_str = row.astype(str).str.strip().str.upper().values
                if 'DATE' in row_str and 'STATION' in row_str:
                    header_row_idx = idx
                    break
            
            if header_row_idx is None:
                st.error("❌ ไม่พบโครงสร้างตารางที่มีคำว่า DATE และ STATION ในไฟล์นี้ กรุณาตรวจสอบไฟล์อีกครั้ง")
            else:
                # ตั้งหัวตารางใหม่จากแถวที่เจอ
                headers = raw_df.iloc[header_row_idx].astype(str).str.strip().str.upper().values
                
                # เอาข้อมูลตั้งแต่แถวถัดจากหัวตารางลงมา
                data_df = raw_df.iloc[header_row_idx+1:].copy()
                data_df.columns = headers
                
                # ล้างคอลัมน์ที่ชื่อซ้ำ หรือตัดขยะออก เอาเฉพาะคอลัมน์หลักที่เราใช้
                # ค้นหาชื่อคอลัมน์ที่ตรงเป๊ะ
                final_cols = []
                needed = ['DATE', 'STATION', 'EMP ID']
                
                # ป้องกันกรณีมีคอลัมน์ชื่อซ้ำกันในระบบ
                df_cleaned = pd.DataFrame()
                for col_name in needed:
                    if col_name in data_df.columns:
                        # ถ้ามีคอลัมน์ชื่อซ้ำ เอาอันแรกสุด
                        col_data = data_df[col_name]
                        if isinstance(col_data, pd.DataFrame):
                            df_cleaned[col_name] = col_data.iloc[:, 0]
                        else:
                            df_cleaned[col_name] = col_data
                
                # เคลียร์เศษขยะ: ลบบรรทัดที่เป็นคำว่า 'DATE' ซ้ำซ้อน และลบบรรทัดที่เป็นค่าว่าง
                df_cleaned = df_cleaned.dropna(subset=['DATE', 'STATION', 'EMP ID'])
                df_cleaned = df_cleaned[df_cleaned['DATE'].astype(str).str.strip().str.upper() != 'DATE']
                df_cleaned = df_cleaned[df_cleaned['EMP ID'].astype(str).str.strip() != '']
                
                if len(df_cleaned) == 0:
                    st.error("❌ ดึงข้อมูลไม่ได้เนื่องจากไม่มีแถวข้อมูลที่สมบูรณ์ (ต้องมีทั้ง Date, Station, และ EMP ID ในแถวเดียวกัน)")
                else:
                    st.session_state['database'] = df_cleaned
                    st.success(f"🎉 อัปโหลดสำเร็จ! กรองขยะออกให้แล้ว เหลือข้อมูลงานจริง {len(df_cleaned)} รายการ")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5. ส่วนแสดงผลข้อมูล ---
if st.session_state['database'] is not None:
    df = st.session_state['database']
    
    # แปลงข้อมูลเป็นตัวหนังสือเพื่อป้องกันการเพี้ยนตอนค้นหา
    df['DATE'] = df['DATE'].astype(str).str.strip()
    df['EMP ID'] = df['EMP ID'].astype(str).str.strip()
    df['STATION'] = df['STATION'].astype(str).str.strip()
    
    st.subheader("🔍 เลือกเงื่อนไขเพื่อค้นหายอดงาน")
    col1, col2 = st.columns(2)
    
    with col1:
        all_dates = sorted(df['DATE'].unique())
        selected_date = st.selectbox("📅 1. เลือกวันที่ (DATE):", all_dates)
        
    with col2:
        # กรองรหัสพนักงานที่มีงานในวันนั้นๆ
        filtered_by_date = df[df['DATE'] == selected_date]
        all_emp_ids = sorted(filtered_by_date['EMP ID'].unique())
        selected_emp_id = st.selectbox("👤 2. เลือกรหัสพนักงาน (EMP ID):", all_emp_ids)
        
    # ดึงยอดงานของคนนั้นในวันนั้น
    final_result = filtered_by_date[filtered_by_date['EMP ID'] == selected_emp_id]
    
    st.markdown("---")
    st.markdown(f"### 📋 สรุปยอดงานของรหัสพนักงาน: **{selected_emp_id}** ประจำวันที่ **{selected_date}**")
    
    if not final_result.empty:
        # สรุปนับจำนวนตัวแยกตามแต่ละ Station
        summary_counts = final_result['STATION'].value_counts().reset_index()
        summary_counts.columns = ['STATION', 'จำนวน (ตัว)']
        
        # แสดงผลเป็นกล่องการ์ดสวยๆ
        m_col1, m_col2, m_col3 = st.columns(3)
        for idx, row in summary_counts.iterrows():
            current_col = [m_col1, m_col2, m_col3][idx % 3]
            with current_col:
                st.markdown(f"""
                <div class="result-card">
                    <p style="margin:0; color:#555; font-size:14px;">Station / รุ่นสินค้า</p>
                    <h3 style="margin:5px 0; color:#1E3A8A;">{row['STATION']}</h3>
                    <p style="margin:0; font-size:24px; font-weight:bold; color:#10B981;">{row['จำนวน (ตัว)']} ตัว</p>
                </div>
                """, unsafe_allow_html=True)
        
        # แสดงตารางให้ตรวจสอบ
        with st.expander("🔍 ดูรายการแถวข้อมูลทั้งหมดที่ระบบนับยอด"):
            st.dataframe(final_result[['DATE', 'STATION', 'EMP ID']].reset_index(drop=True), use_container_width=True)
            
    else:
        st.warning("⚠️ ไม่พบข้อมูลงานของพนักงานคนนี้ในวันที่ระบุ")

else:
    st.info("📢 ยินดีต้อนรับ! กรุณาให้ Admin 1 หรือ Admin 2 เปลี่ยนสิทธิ์ที่แถบเมนูด้านซ้ายเพื่ออัปโหลดไฟล์ก่อนครับ")
