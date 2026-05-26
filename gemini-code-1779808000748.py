import streamlit as st
import pandas as pd

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
    st.subheader("📥 พื้นที่สำหรับ Admin: อัปโหลดไฟล์ยอดงานประจำวัน")
    st.write("📢 โย่นไฟล์ได้ทั้ง Excel (.xlsx) และ CSV ระบบจะเคลียร์ขยะให้อัตโนมัติ")
    
    uploaded_file = st.file_uploader("โยนไฟล์ Excel (.xlsx) หรือ CSV ตรงนี้", type=["xlsx", "csv"], key="uploader")
    
    if uploaded_file is not None:
        try:
            # ใช้คำสั่งอ่านข้อมูลแบบดิบที่สุด โดยบังคับใช้ engine='openpyxl' สำหรับ excel เพื่อแก้ปัญหาค้าง
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file, header=None)
            else:
                raw_df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
            
            cleaned_rows = []
            
            # วนลูปอ่านข้อมูลทีละบรรทัด ค้นหาข้อมูลงานจริง
            for idx, row in raw_df.iterrows():
                row_values = row.astype(str).str.strip().values
                
                # หากเจอแถวที่เป็นหัวข้อตารางซ้ำซ้อน ให้ข้ามไป
                if 'DATE' in [str(x).upper() for x in row_values] and 'STATION' in [str(x).upper() for x in row_values]:
                    continue
                
                date_val = str(row_values[0]).strip()     # คอลัมน์แรกสุด (วันที่)
                station_val = str(row_values[1]).strip()  # คอลัมน์ที่สอง (ชื่อรุ่น / Station)
                emp_val = str(row_values[-1]).strip()     # คอลัมน์ขวาสุด (รหัสพนักงาน)
                
                # คัดกรอง: แถวนั้นต้องเป็นวันที่จริง (มีเครื่องหมาย /) และมีรหัสพนักงานจริง ไม่ใช่บรรทัดว่าง
                if '/' in date_val and date_val != 'nan' and station_val != 'nan' and emp_val != 'nan' and emp_val != '':
                    cleaned_rows.append({
                        'DATE': date_val,
                        'STATION': station_val,
                        'EMP_ID': emp_val
                    })
            
            if len(cleaned_rows) == 0:
                st.error("❌ ไม่สามารถดึงข้อมูลจากไฟล์นี้ได้ กรุณาตรวจสอบว่าในตารางมีข้อมูลวันที่และรหัสพนักงานครบถ้วนหรือไม่")
            else:
                df_clean = pd.DataFrame(cleaned_rows)
                st.session_state['database'] = df_clean
                st.success(f"🎉 สำเร็จแล้วครับพี่! ระบบสแกนไฟล์ดึงข้อมูลงานจริงออกมาได้ {len(df_clean)} รายการ")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการเปิดหรืออ่านไฟล์: {e} (แนะนำให้ลองเซฟไฟล์เป็น .csv หรืออัปโหลดใหม่อีกครั้ง)")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5. ส่วนแสดงผลข้อมูล ---
if st.session_state['database'] is not None:
    df = st.session_state['database']
    
    df['DATE'] = df['DATE'].astype(str).str.strip()
    df['EMP_ID'] = df['EMP_ID'].astype(str).str.strip()
    df['STATION'] = df['STATION'].astype(str).str.strip()
    
    st.subheader("🔍 เลือกเงื่อนไขเพื่อค้นหายอดงาน")
    col1, col2 = st.columns(2)
    
    with col1:
        all_dates = sorted(df['DATE'].unique())
        selected_date = st.selectbox("📅 1. เลือกวันที่ (DATE):", all_dates)
        
    with col2:
        filtered_by_date = df[df['DATE'] == selected_date]
        all_emp_ids = sorted(filtered_by_date['EMP_ID'].unique())
        selected_emp_id = st.selectbox("👤 2. เลือกรหัสพนักงาน (EMP ID):", all_emp_ids)
        
    final_result = filtered_by_date[filtered_by_date['EMP_ID'] == selected_emp_id]
    
    st.markdown("---")
    st.markdown(f"### 📋 สรุปยอดงานของรหัสพนักงาน: **{selected_emp_id}** ประจำวันที่ **{selected_date}**")
    
    if not final_result.empty:
        summary_counts = final_result['STATION'].value_counts().reset_index()
        summary_counts.columns = ['STATION', 'จำนวน (ตัว)']
        
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
        
        with st.expander("🔍 ดูรายละเอียดตารางงานทั้งหมดที่ระบบนับยอด"):
            st.dataframe(final_result.reset_index(drop=True), use_container_width=True)
            
    else:
        st.warning("⚠️ ไม่พบข้อมูลงานของพนักงานคนนี้ในวันที่ระบุ")

else:
    st.info("📢 ยินดีต้อนรับ! กรุณาให้ Admin 1 หรือ Admin 2 เปลี่ยนสิทธิ์ที่แถบเมนูด้านซ้ายเพื่ออัปโหลดไฟล์ก่อนครับ")
