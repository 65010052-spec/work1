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
            # ดึงข้อมูลดิบเข้ามาโดยไม่อ่านหัวตาราง
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file, header=None)
            else:
                df_raw = pd.read_excel(uploaded_file, header=None, engine='openpyxl')
            
            # บังคับเลือกเฉพาะ 3 คอลัมน์สำคัญ (คอลัมน์ index 0=วันที่, 1=Station, -1=ขวาสุดรหัสพนักงาน)
            df_select = pd.DataFrame({
                'DATE': df_raw[0],
                'STATION': df_raw[1],
                'EMP_ID': df_raw.iloc[:, -1] # เอาคอลัมน์ขวาสุดเสมอ
            })
            
            # แปลงค่าทุกช่องให้เป็นตัวหนังสือและตัดช่องว่างออก
            df_select = df_select.astype(str).apply(lambda x: x.str.strip())
            
            # ลบแถวขยะที่เป็นหัวตารางซ้ำๆ ออกไป
            df_clean = df_select[
                (~df_select['DATE'].str.upper().str.contains('DATE', na=False)) & 
                (df_select['DATE'] != 'nan') & (df_select['DATE'] != '') &
                (df_select['EMP_ID'] != 'nan') & (df_select['EMP_ID'] != '')
            ].copy()
            
            # จัดการรูปแบบวันที่ให้สวยงาม (ตัดเวลาออกถ้ามีพ่วงมา)
            df_clean['DATE'] = df_clean['DATE'].apply(lambda x: x.split(" ")[0] if " " in x else x)
            
            if df_clean.empty:
                st.error("❌ ไม่สามารถดึงข้อมูลได้ กรุณาตรวจสอบสิทธิ์ผู้ใช้หรือหน้าตาตารางข้างในไฟล์อีกครั้ง")
            else:
                st.session_state['database'] = df_clean.reset_index(drop=True)
                st.success(f"🎉 สำเร็จแล้วครับพี่! ระบบดึงข้อมูลงานจริงออกมาได้ทั้งหมด {len(df_clean)} รายการ")
                
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
