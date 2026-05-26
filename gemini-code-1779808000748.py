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
    st.subheader("📥 พื้นที่สำหรับ Admin: อัปโหลดไฟล์ Excel ยอดงาน")
    
    uploaded_file = st.file_uploader("โยนไฟล์ Excel (.xlsx) หรือ CSV ตรงนี้", type=["xlsx", "csv"], key="uploader")
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_input = pd.read_csv(uploaded_file)
            else:
                df_input = pd.read_excel(uploaded_file)
                
            # ล้างช่องว่างที่หัวคอลัมน์ และแปลงเป็นตัวพิมพ์ใหญ่ทั้งหมดเพื่อความชัวร์
            df_input.columns = df_input.columns.str.strip().str.upper()
            
            # ตรวจสอบคอลัมน์หลักตามรูปจริงของพี่: DATE, STATION, EMP ID
            required_cols = ['DATE', 'STATION', 'EMP ID']
            missing_cols = [col for col in required_cols if col not in df_input.columns]
            
            if missing_cols:
                st.error(f"❌ โครงสร้างไฟล์ไม่ถูกต้อง! ตารางต้องมีคอลัมน์ชื่อ: DATE, STATION, EMP ID")
            else:
                # ลบแถวที่ไม่มีข้อมูลสำคัญออก (ลบแถวที่เป็นค่าว่างในช่อง DATE หรือ EMP ID)
                df_clean = df_input.dropna(subset=['DATE', 'EMP ID']).copy()
                
                st.session_state['database'] = df_clean
                st.success(f"🎉 อัปโหลดสำเร็จ! พบข้อมูลที่ใช้งานได้จริงทั้งหมด {len(df_clean)} รายการ")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5. ส่วนแสดงผลข้อมูล ---
if st.session_state['database'] is not None:
    df = st.session_state['database']
    
    # แปลงคอลัมน์ให้เป็นตัวหนังสือ (String) และตัดช่องว่างออก
    df['DATE'] = df['DATE'].astype(str).str.strip()
    df['EMP ID'] = df['EMP ID'].astype(str).str.strip()
    df['STATION'] = df['STATION'].astype(str).str.strip()
    
    st.subheader("🔍 เลือกเงื่อนไขเพื่อค้นหายอดงาน")
    col1, col2 = st.columns(2)
    
    with col1:
        all_dates = sorted(df['DATE'].unique())
        selected_date = st.selectbox("📅 1. เลือกวันที่ (DATE):", all_dates)
        
    with col2:
        # กรองเอาเฉพาะพนักงานที่มีงานในวันนั้นๆ
        filtered_by_date = df[df['DATE'] == selected_date]
        all_emp_ids = sorted(filtered_by_date['EMP ID'].unique())
        selected_emp_id = st.selectbox("👤 2. เลือกรหัสพนักงาน (EMP ID):", all_emp_ids)
        
    # กรองข้อมูลตามที่เลือก
    final_result = filtered_by_date[filtered_by_date['EMP ID'] == selected_emp_id]
    
    st.markdown("---")
    st.markdown(f"### 📋 สรุปยอดงานของรหัสพนักงาน: **{selected_emp_id}** ประจำวันที่ **{selected_date}**")
    
    if not final_result.empty:
        # นับจำนวนตัวแยกตาม Station / รุ่นสินค้า
        summary_counts = final_result['STATION'].value_counts().reset_index()
        summary_counts.columns = ['STATION', 'จำนวน (ตัว)']
        
        # แสดงผลเป็นกล่องการ์ดสวยงาม
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
        
        # แสดงตารางข้อมูลดิบ
        with st.expander("🔍 ดูรายละเอียดตารางงานทั้งหมด"):
            st.dataframe(final_result[['DATE', 'STATION', 'EMP ID']], use_container_width=True)
            
    else:
        st.warning("⚠️ ไม่พบข้อมูลงานของพนักงานคนนี้ในวันที่ระบุ")

else:
    st.info("📢 ยินดีต้อนรับ! กรุณาให้ Admin 1 หรือ Admin 2 เลือกสิทธิ์ที่แถบเมนูด้านซ้ายเพื่ออัปโหลดไฟล์ก่อนระบบถึงจะแสดงผลให้ค้นหาครับ")
