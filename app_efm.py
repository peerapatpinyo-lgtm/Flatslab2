import streamlit as st
import pandas as pd
import calc_efm

def render_efm_tab(calc_obj):
    """
    เรนเดอร์หน้า UI สำหรับขั้นตอน Equivalent Frame Method (Stiffness Analysis)
    """
    st.header("2️⃣ Equivalent Frame Method (Stiffness Analysis)")
    st.markdown("""
    ขั้นตอนนี้เป็นการคำนวณหาค่าความแข็งแรง (Stiffness) ขององค์อาคารต่างๆ 
    เพื่อใช้ในการกระจายโมเมนต์ดัดในโครงสร้างเสมือน (Equivalent Frame)
    """)
    st.markdown("---")
    
    try:
        # เรียกใช้ฟังก์ชันคำนวณจากไฟล์ calc_efm.py
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการคำนวณ: {e}")
        return
        
    # Helper function สำหรับการแสดงผลตัวเลขแบบ Scientific Notation (เช่น 1.23e+07)
    def fmt_sci(val):
        return f"{val:.2e}"
    
    # --- ส่วนที่ 1: Member Stiffness ---
    st.subheader("Step 1: Member Stiffness ($K$)")
    st.write("คำนวณค่า Stiffness ของพื้น, เสา และส่วนที่รับแรงบิด")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.info("**Slab Stiffness ($K_s$)**")
        st.latex(r"K_s = \frac{4EI_s}{\ell_1}")
        st.metric("Ks", fmt_sci(res['Ks']), "N·m")
        
    with c2:
        st.info("**Column Stiffness ($\Sigma K_c$)**")
        st.latex(r"K_c = \frac{4EI_c}{\ell_c}")
        st.metric("ΣKc", fmt_sci(res['Sum_Kc']), "N·m")
        
    with c3:
        st.info("**Torsional Stiffness ($K_t$)**")
        st.latex(r"K_t = \sum \frac{9E_{cs}C}{\ell_2(1-c_2/\ell_2)^3}")
        st.metric("Kt", fmt_sci(res['Kt']), "N·m")
        
    st.markdown("---")
    
    # --- ส่วนที่ 2: Equivalent Column ---
    st.subheader("Step 2: Equivalent Column Stiffness ($K_{ec}$)")
    st.warning("ความยืดหยุ่นของจุดต่อ (Torsional member) จะลดความแข็งแรงประสิทธิผลของเสาลง")
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
        st.write("""
        *พิจารณาค่า Stiffness ของเสารวมกับค่า Stiffness ของคานขวางที่รับแรงบิด (Torsional Member)*
        """)
    with col_r:
        st.metric("🎯 Kec (Result)", fmt_sci(res['Kec']), "N·m")
        
    # คำนวณ % การลดลงของ Stiffness เพื่อเป็นข้อมูลประกอบ
    if res['Sum_Kc'] > 0:
        reduction = (1 - res['Kec']/res['Sum_Kc']) * 100
        st.caption(f"💡 หมายเหตุ: ความยืดหยุ่นจากแรงบิดทำให้ Stiffness ของเสาลดลง **{reduction:.1f}%**")
        
    st.markdown("---")
    
    # --- ส่วนที่ 3: Distribution Factors ---
    st.subheader("Step 3: Moment Distribution Factors (DF)")
    st.write("การกระจายโมเมนต์ที่ไม่สมดุลที่จุดต่อ จะแบ่งตามสัดส่วน Stiffness ดังนี้:")
    
    # สร้าง DataFrame สำหรับแสดงตาราง DF
    df_data = [
        {
            "Member": "Slab (พื้น)", 
            "Stiffness (K)": fmt_sci(res['Ks']), 
            "Distribution Factor (DF)": f"{res['df_slab']*100:.2f}%"
        },
        {
            "Member": "Equivalent Column (เสาเสมือน)", 
            "Stiffness (Kec)": fmt_sci(res['Kec']), 
            "Distribution Factor (DF)": f"{res['df_col']*100:.2f}%"
        }
    ]
    
    df_res = pd.DataFrame(df_data)
    
    # แสดงตารางแบบเต็มความกว้าง
    st.table(df_res)
    
    st.success("✅ คำนวณ Stiffness Matrix เรียบร้อยแล้ว (ขั้นตอนถัดไป: Moment Distribution)")

# ส่วนนี้สำหรับทดสอบรันเฉพาะไฟล์นี้ (ถ้าต้องการ)
if __name__ == "__main__":
    st.set_page_config(page_title="EFM Analysis", layout="wide")
    st.warning("กรุณารันผ่านไฟล์ main app เพื่อส่งค่า calc_obj")
