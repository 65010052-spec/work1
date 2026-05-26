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
            # อ่านข้อมูลดิบทั้งหมดเข้ามาแบบไม่มีหัวตารางเพื่อป้องกันระบบเอ๋อ
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file, header=None)
            else:
                raw_df = pd.read_excel(uploaded_file, header=None)
            
            # ลิสต์สำหรับเก็บข้อมูลที่ทำความสะอาดแล้ว
            cleaned_rows = []
            
            # วนลูปเช็คทีละแถว ค้นหาข้อมูลจริง
            for idx, row in raw_df.iterrows():
                # แปลงข้อมูลในแถวเป็นลิสต์ของตัวหนังสือ
                row_values = row.astype(str).str.strip().values
                
                # ถ้าเป็นแถวที่มีคำว่า DATE, STATION ถือว่าเป็นหัวข้อขยะซ้ำซ้อน ให้ข้ามไป
                if 'DATE' in [str(x).upper() for x in row_values] and 'STATION' in [str(x).upper() for x in row_values]:
                    continue
                
                # เช็คว่าแถวนั้นมี วันที่ (คอลัมน์ 0) และมีสถานี (คอลัมน์ 1) หรือไม่
                date_val = str(row_values[0]).strip()
                station_val = str(row_values[1]).strip()
                # รหัสพนักงานมักจะอยู่คอลัมน์สุดท้ายที่มีข้อมูล (จากไฟล์จริงคือคอลัมน์ที่ 14 หรือขวาสุด)
                # เราจะดึงค่าจากช่องขวาสุด (index -1) หรือรองสุดท้ายที่พบข้อมูลจริงมาเช็ค
                emp_val = str(row_values[-1]).strip()
                
                # คัดกรองเอาเฉพาะแถวที่มี วันที่จริง ๆ (เช่น มีเครื่องหมาย / ) และมีรหัสพนักงาน
                if '/' in date_val and date_val != 'nan' and station_val != 'nan' and emp_val != 'nan' and emp_val != '':
                    cleaned_rows.append({
                        'DATE': date_val,
                        'STATION': station_val,
                        'EMP_ID': emp_val
                    })
            
            # แปลงผลลัพธ์เป็นตารางที่ใช้งานได้จริง
            if len(cleaned_rows) == 0:
                st.error("❌ ระบบพยายามกวาดข้อมูลแล้ว แต่ไม่พบแถวข้อมูลที่สมบูรณ์ตามโครงสร้าง กรุณาเช็คไฟล์อีกครั้งครับ")
            else:
                df_clean = pd.DataFrame(cleaned_rows)
                st.session_state['database'] = df_clean
                st.success(f"🎉 รอบนี้ผ่านแล้วครับพี่! ระบบสแกนและดึงข้อมูลงานจริงออกมาได้ทั้งหมด {len(df_clean)} รายการ")
                
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
        # กรองรหัสพนักงานที่มีงานในวันนั้นๆ
        filtered_by_date = df[df['DATE'] == selected_date]
        all_emp_ids = sorted(filtered_by_date['EMP_ID'].unique())
        selected_emp_id = st.selectbox("👤 2. เลือกรหัสพนักงาน (EMP ID):", all_emp_ids)
        
    # ดึงยอดงานของคนนั้นในวันนั้น
    final_result = filtered_by_date[filtered_by_date['EMP_ID'] == selected_emp_id]
    
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
            st.dataframe(final_result.reset_index(drop=True), use_container_width=True)
            
    else:
        st.warning("⚠️ ไม่พบข้อมูลงานของพนักงานคนนี้ในวันที่ระบุ")

else:
    st.info("📢 ยินดีต้อนรับ! กรุณาให้ Admin 1 หรือ Admin 2 เปลี่ยนสิทธิ์ที่แถบเมนูด้านซ้ายเพื่ออัปโหลดไฟล์ก่อนครับ")
