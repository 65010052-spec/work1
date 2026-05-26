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

# 🧠 สร้างระบบจำข้อมูลถาวร (Session State) 
if 'database' not in st.session_state:
    st.session_state['database'] = None

# --- 4. ส่วนของ Admin จัดการไฟล์ ---
if user_role in ["Admin 1", "Admin 2"]:
    st.markdown('<div class="admin-box">', unsafe_allow_html=True)
    st.subheader("📥 พื้นที่สำหรับ Admin: จัดการไฟล์ยอดงานประจำวัน")
    
    col_upload, col_clear = st.columns([4, 1])
    
    with col_upload:
        # ช่องอัปโหลดไฟล์ CSV
        uploaded_file = st.file_uploader("โยนไฟล์ CSV (.csv) ตรงนี้ ระบบจะกรองและจำข้อมูลไว้ตลอดไป", type=["csv"], key="uploader")
    
    with col_clear:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # 🔴 ปุ่มสั่งล้างความจำ (เมื่อกดปุ่มนี้เท่านั้นระบบถึงจะลืมข้อมูล)
        if st.button("🗑️ เคลียร์ข้อมูลทั้งหมด", type="primary", use_container_width=True):
            st.session_state['database'] = None
            st.success("ล้างฐานข้อมูลเก่าเรียบร้อยแล้ว!")
            st.rerun()
            
    # ตรรกะการประมวลผลและจำไฟล์
    if uploaded_file is not None:
        try:
            # อ่านไฟล์ CSV โดยบังคับให้เป็น String เพื่อความปลอดภัย
            df_raw = pd.read_csv(uploaded_file, header=None, dtype=str)
            cleaned_rows = []
            
            for idx, row in df_raw.iterrows():
                date_val = str(row.iloc[0]).strip()
                station_val = str(row.iloc[1]).strip()
                emp_val = str(row.iloc[-1]).strip() # คอลัมน์ขวาสุด (EMP ID)
                
                if 'DATE' in date_val.upper() or 'STATION' in station_val.upper():
                    continue
                
                if date_val != 'nan' and date_val != '' and station_val != 'nan' and station_val != '' and emp_val != 'nan' and emp_val != '':
                    if " " in date_val:
                        date_val = date_val.split(" ")[0]
                        
                    cleaned_rows.append({
                        'DATE': date_val,
                        'STATION': station_val,
                        'EMP_ID': emp_val
                    })
            
            if len(cleaned_rows) == 0:
                st.error("❌ ไม่พบข้อมูลงานจริงในไฟล์ CSV กรุณาตรวจสอบคอลัมน์ใหม่อีกครั้ง")
            else:
                # 💾 อัปโหลดไฟล์ใหม่สำเร็จ -> บันทึกทับความจำเดิมทันที
                st.session_state['database'] = pd.DataFrame(cleaned_rows)
                st.success(f"🚀 อัปโหลดไฟล์ใหม่สำเร็จ! ระบบบันทึกความจำชุดใหม่ {len(cleaned_rows)} รายการ")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ CSV: {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5. ส่วนแสดงผลข้อมูล (พนักงานค้นหาและดูยอด) ---
# ระบบจะดึงข้อมูลจากความจำเก่า (ที่เคยอัปโหลดไว้) ออกมาแสดงผลเสมอ ไม่ว่าใครจะกดอะไรบนหน้าจอ
if st.session_state['database'] is not None:
    df = st.session_state['database']
    
    st.markdown("### 🟢 สถานะระบบ: มีฐานข้อมูลพร้อมใช้งานในระบบ (ดึงข้อมูลล่าสุดมาใช้งาน)")
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
    # แสดงข้อความนี้เฉพาะตอนที่ระบบ "ไม่มีความจำเหลืออยู่เลย" (เช่น เปิดแอปครั้งแรก หรือ พึ่งกดปุ่มเคลียร์ข้อมูล)
    st.info("📢 ระบบยังไม่มีฐานข้อมูลในความจำชั่วคราว กรุณาให้ Admin เข้าสู่ระบบเพื่ออัปโหลดไฟล์ CSV ก่อนครับ")
