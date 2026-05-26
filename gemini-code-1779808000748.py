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
                
            # ล้างช่องว่างที่หัวคอลัมน์ออกเพื่อกันเอ๋อ
            df_input.columns = df_input.columns.str.strip()
            
            # ตรวจสอบว่ามีคอลัมน์ตามไฟล์จริงไหม (Date, Station, OP_ID)
            required_cols = ['Date', 'Station', 'OP_ID']
            missing_cols = [col for col in required_cols if col not in df_input.columns]
            
            if missing_cols:
                st.error(f"❌ โครงสร้างไฟล์ไม่ถูกต้อง! ตารางต้องมีคอลัมน์ชื่อ: {', '.join(required_cols)} (ตัวพิมพ์เล็ก-ใหญ่ต้องตรง)")
            else:
                st.session_state['database'] = df_input
                st.success(f"🎉 อัปโหลดสำเร็จ! พบข้อมูลทั้งหมด {len(df_input)} รายการ")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5. ส่วนแสดงผลข้อมูล ---
if st.session_state['database'] is not None:
    df = st.session_state['database']
    
    # จัดการแปลงคอลัมน์ให้เป็น Text เพื่อป้องกันปัญหาการค้นหา
    df['Date'] = df['Date'].astype(str).str.strip()
    df['OP_ID'] = df['OP_ID'].astype(str).str.strip()
    df['Station'] = df['Station'].astype(str).str.strip()
    
    st.subheader("🔍 เลือกเงื่อนไขเพื่อค้นหายอดงาน")
    col1, col2 = st.columns(2)
    
    with col1:
        all_dates = sorted(df['Date'].unique())
        selected_date = st.selectbox("📅 1. เลือกวันที่ (Date):", all_dates)
        
    with col2:
        # กรองเอาเฉพาะพนักงานที่มีงานในวันนั้นๆ มาให้เลือก
        filtered_by_date = df[df['Date'] == selected_date]
        all_emp_ids = sorted(filtered_by_date['OP_ID'].unique())
        selected_emp_id = st.selectbox("👤 2. เลือกรหัสพนักงาน (OP_ID):", all_emp_ids)
        
    # กรองข้อมูลจริง
    final_result = filtered_by_date[filtered_by_date['OP_ID'] == selected_emp_id]
    
    st.markdown("---")
    st.markdown(f"### 📋 สรุปยอดงานของรหัสพนักงาน: **{selected_emp_id}** ประจำวันที่ **{selected_date}**")
    
    if not final_result.empty:
        # คำนวณนับจำนวนว่าพนักงานคนนี้ทำแต่ละ Station ไปกี่ตัว
        summary_counts = final_result['Station'].value_counts().reset_index()
        summary_counts.columns = ['Station', 'จำนวน (ตัว)']
        
        # แสดงผลลัพธ์เป็นกล่องการ์ดสวยๆ
        m_col1, m_col2, m_col3 = st.columns(3)
        for idx, row in summary_counts.iterrows():
            current_col = [m_col1, m_col2, m_col3][idx % 3]
            with current_col:
                st.markdown(f"""
                <div class="result-card">
                    <p style="margin:0; color:#555; font-size:14px;">Station / รุ่นสินค้า</p>
                    <h3 style="margin:5px 0; color:#1E3A8A;">{row['Station']}</h3>
                    <p style="margin:0; font-size:24px; font-weight:bold; color:#10B981;">{row['จำนวน (ตัว)']} ตัว</p>
                </div>
                """, unsafe_allow_html=True)
        
        # แสดงตารางดีเทลด้านล่าง เผื่อไว้เช็คเวลาทำงาน
        with st.expander("🔍 ดูรายการงานดิบทั้งหมดของพนักงานคนนี้"):
            st.dataframe(final_result[['Date', 'Station', 'OP_ID']], use_container_width=True)
            
    else:
        st.warning("⚠️ ไม่พบข้อมูลงานของพนักงานคนนี้ในวันที่ระบุ")

else:
    st.info("📢 ยินดีต้อนรับ! กรุณาให้ Admin 1 หรือ Admin 2 เลือกสิทธิ์ที่แถบเมนูด้านซ้ายเพื่ออัปโหลดไฟล์ก่อนระบบถึงจะแสดงผลให้ค้นหาครับ")
