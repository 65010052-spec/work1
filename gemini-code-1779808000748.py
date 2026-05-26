import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="ระบบสรุปยอดงานพนักงานประจำวัน",
    page_icon="📊",
    layout="wide"
)

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
    st.sidebar.success(f"⚡ Status: {user_role} (สิทธิ์ผู้ดูแลระบบ)")
else:
    st.sidebar.info("👤 Status: พนักงานทั่วไป")

st.sidebar.markdown("---")

# --- 3. หน้าตาหลัก ---
st.markdown('<div class="main-title">📊 ระบบบันทึกและสรุปยอดงานพนักงานประจำวัน</div>', unsafe_allow_html=True)

if 'database' not in st.session_state:
    st.session_state['database'] = None

# --- 4. ส่วนของ Admin อัปโหลดไฟล์ ---
if user_role in ["Admin 1", "Admin 2"]:
    st.markdown('<div class="admin-box">', unsafe_allow_html=True)
    st.subheader("📥 พื้นที่สำหรับ Admin: อัปโหลดไฟล์ยอดงานประจำวัน")
    
    uploaded_file = st.file_uploader("โยนไฟล์ Excel (.xlsx) หรือ CSV ตรงนี้", type=["xlsx", "csv"], key="uploader")
    
    if uploaded_file is not None:
        try:
            # 1. โหลดไฟล์เข้ามาโดยบังคับให้อ่านทุกช่องเป็น "ตัวหนังสือ (str)" ตั้งแต่แรกเพื่อกันเอ๋อ
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file, header=None, dtype=str)
            else:
                df_raw = pd.read_excel(uploaded_file, header=None, engine='openpyxl', dtype=str)
            
            cleaned_rows = []
            
            # 2. วนลูปสแกนทีละแถวแบบปลอดภัย
            for idx, row in df_raw.iterrows():
                # แปลงค่าและตัดช่องว่าง แปลงเป็นตัวพิมพ์ใหญ่เพื่อความชัวร์ในการเช็คขยะ
                date_val = str(row.iloc[0]).strip()
                station_val = str(row.iloc[1]).strip()
                emp_val = str(row.iloc[-1]).strip()
                
                # เช็คคำว่า DATE หรือหัวตารางซ้ำๆ
                if 'DATE' in date_val.upper() or 'STATION' in station_val.upper():
                    continue
                
                # กรองเศษแถวว่าง แถวแถม หรือแถวที่เป็น nan
                if date_val != 'nan' and date_val != '' and station_val != 'nan' and station_val != '' and emp_val != 'nan' and emp_val != '':
                    
                    # หั่นวันที่เอาเฉพาะส่วนหลัก (กรณีมีเวลาพ่วงมาด้วยจากระบบ Excel)
                    if " " in date_val:
                        date_val = date_val.split(" ")[0]
                        
                    cleaned_rows.append({
                        'DATE': date_val,
                        'STATION': station_val,
                        'EMP_ID': emp_val
                    })
            
            # 3. สรุปตารางผลลัพธ์
            if len(cleaned_rows) == 0:
                st.error("❌ ดึงข้อมูลไม่สำเร็จ กรุณาเช็คว่าโครงสร้างไฟล์มีการขยับคอลัมน์หรือไม่")
            else:
                st.session_state['database'] = pd.DataFrame(cleaned_rows)
                st.success(f"🎉 รอบนี้ผ่านฉลุยครับพี่! ดึงข้อมูลงานจริงได้ทั้งหมด {len(cleaned_rows)} รายการ")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5. ส่วนแสดงผลข้อมูล ---
if st.session_state['database'] is not None:
    df = st.session_state['database']
    
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
