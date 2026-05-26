import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าเว็บให้เป็นแนวกว้างและใส่ไอคอน
st.set_page_config(
    page_title="ระบบสรุปยอดงานพนักงานประจำวัน",
    page_icon="📊",
    layout="wide"
)

# ปรับแต่งสไตล์ปุ่มและฟอนต์เพิ่มเติมด้วย CSS แบบง่าย
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E3A8A; margin-bottom: 20px; }
    .admin-box { background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; }
    .result-card { background-color: #EFF6FF; padding: 15px; border-radius: 8px; border: 1px solid #BFDBFE; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ระบบ Login แบบเลือกชื่อในแถบข้าง (Sidebar) ---
st.sidebar.markdown("## 🔒 ระบบเข้าสู่ระบบ")
user_role = st.sidebar.selectbox(
    "กรุณาเลือกชื่อของคุณเพื่อเข้าใช้งาน:",
    ["พนักงานทั่วไป (ดูข้อมูล)", "Admin 1", "Admin 2"]
)

# แสดงสถานะผู้ใช้งานปัจจุบัน
if user_role in ["Admin 1", "Admin 2"]:
    st.sidebar.success(f"⚡ สถานะ: {user_role} (สิทธิ์ผู้ดูแลระบบ)")
else:
    st.sidebar.info("👤 สถานะ: พนักงานทั่วไป (สิทธิ์ดูข้อมูล)")

st.sidebar.markdown("---")
st.sidebar.caption("💡 ระบบนี้พัฒนาด้วย Python & Streamlit")

# --- 3. หน้าตาหลักของเว็บไซต์ ---
st.markdown('<div class="main-title">📊 ระบบบันทึกและสรุปยอดงานพนักงานประจำวัน</div>', unsafe_allow_html=True)

# ใช้ Session State เพื่อแชร์ข้อมูลร่วมกันระหว่างการกดบนหน้าเว็บ
if 'database' not in st.session_state:
    st.session_state['database'] = None

# --- 4. ส่วนของ Admin: อัปโหลดและจัดการไฟล์ข้อมูล ---
if user_role in ["Admin 1", "Admin 2"]:
    st.markdown('<div class="admin-box">', unsafe_allow_html=True)
    st.subheader("📥 พื้นที่สำหรับ Admin: อัปโหลดไฟล์ยอดงานประจำวัน")
    st.write("คุณสามารถลากไฟล์ Excel (.xlsx) หรือ CSV มาวางในช่องด้านล่างนี้ได้เลย")
    
    uploaded_file = st.file_uploader("เลือกไฟล์ข้อมูล...", type=["xlsx", "csv"], key="uploader")
    
    if uploaded_file is not None:
        try:
            # ตรวจสอบประเภทไฟล์และโหลดเข้าสู่ DataFrame
            if uploaded_file.name.endswith('.csv'):
                df_input = pd.read_csv(uploaded_file)
            else:
                df_input = pd.read_excel(uploaded_file)
                
            # แปลงชื่อคอลลัมน์ให้เป็นตัวพิมพ์เล็ก/ใหญ่ หรือตัดช่องว่างเพื่อลดความผิดพลาด
            df_input.columns = df_input.columns.str.strip()
            
            # ตรวจสอบคอลัมน์พื้นฐานที่จำเป็น
            required_cols = ['วันที่', 'รหัสพนักงาน', 'รุ่นสินค้า', 'จำนวน']
            missing_cols = [col for col in required_cols if col not in df_input.columns]
            
            if missing_cols:
                st.error(f"❌ ไฟล์ไม่ถูกต้อง! ตารางของคุณต้องมีหัวคอลัมน์ชื่อ: {', '.join(required_cols)}")
            else:
                st.session_state['database'] = df_input
                st.success(f"🎉 Admin โหลดข้อมูลสำเร็จแล้ว! พบข้อมูลทั้งหมด {len(df_input)} แถว")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# --- 5. ส่วนของการค้นหาและแสดงผล (พนักงานทุกคนใช้ร่วมกันได้) ---
if st.session_state['database'] is not None:
    df = st.session_state['database']
    
    st.subheader("🔍 ค้นหายอดงานประจำวัน")
    
    # ตัวเลือก Filter 3 ช่องเรียงกัน: วันที่ -> รหัสพนักงาน
    col1, col2 = st.columns(2)
    
    with col1:
        # ตรวจสอบและดึงรายชื่อวันที่ทั้งหมดในไฟล์
        df['วันที่'] = df['วันที่'].astype(str).str.strip()
        all_dates = sorted(df['วันที่'].unique())
        selected_date = st.selectbox("📅 1. เลือกวันที่:", all_dates)
        
    with col2:
        # ดึงรายชื่อพนักงานที่มีงานในวันนั้นๆ
        filtered_by_date = df[df['วันที่'] == selected_date]
        all_emp_ids = sorted(filtered_by_date['รหัสพนักงาน'].astype(str).unique())
        selected_emp_id = st.selectbox("👤 2. เลือกรหัสพนักงาน:", all_emp_ids)
        
    # ทำการกรองข้อมูลขั้นสุดท้าย
    final_result = filtered_by_date[filtered_by_date['รหัสพนักงาน'].astype(str) == selected_emp_id]
    
    # แสดงผลลัพธ์
    st.markdown("---")
    st.markdown(f"### 📋 สรุปยอดงานของรหัสพนักงาน: **{selected_emp_id}** ประจำวันที่ **{selected_date}**")
    
    if not final_result.empty:
        # แสดงผลลัพธ์การปรับรุ่นสินค้าเป็นกล่องๆ (Metrics)
        m_col1, m_col2, m_col3 = st.columns(3)
        
        for idx, row in final_result.reset_index().iterrows():
            # สลับแสดงผลในคอลัมน์ย่อยๆ เพื่อความสวยงาม
            current_col = [m_col1, m_col2, m_col3][idx % 3]
            with current_col:
                st.markdown(f"""
                <div class="result-card">
                    <p style="margin:0; color:#555; font-size:14px;">รุ่นสินค้า</p>
                    <h3 style="margin:0; color:#1E3A8A;">{row['รุ่นสินค้า']}</h3>
                    <p style="margin:5px 0 0 0; font-size:20px; font-weight:bold; color:#10B981;">ปรับได้ {row['จำนวน']} ตัว</p>
                </div>
                """, unsafe_allow_html=True)
        
        # มีตารางข้อมูลดิบให้ขยายดูได้เผื่อตรวจสอบ
        with st.expander("🔍 ดูตารางข้อมูลเต็มของพนักงานคนนี้"):
            st.dataframe(final_result, use_container_width=True)
            
    else:
        st.warning("⚠️ ไม่พบข้อมูลงานของพนักงานคนนี้ในวันที่ระบุ")

else:
    # กรณีเปิดเว็บมาครั้งแรกแล้วยังไม่ได้กดโยนไฟล์ข้อมูล
    st.info("📢 ยินดีต้อนรับสู่ระบบสรุปยอดงาน! ขณะนี้ระบบยังไม่มีฐานข้อมูลในเซสชั่นปัจจุบัน กรุณาให้ Admin 1 หรือ Admin 2 ทำการเข้าสู่ระบบที่แถบด้านซ้ายเพื่ออัปโหลดไฟล์ข้อมูลก่อนครับ")