import streamlit as st
import pandas as pd
import calc_efm

def render_efm_tab(calc_obj):
    st.header("2️⃣ Equivalent Frame Method (Stiffness Analysis)")
    st.markdown("---")
    
    try:
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"❌ Error in Calculation: {e}")
        return

    # --- ฟังก์ชันช่วยจัดฟอร์แมต ---
    def fmt_sci(val): return f"{val:.3e}"
    def fmt_num(val): return f"{val:,.2f}"

    # --- ส่วนที่ 1: สรุปผลลัพธ์หลัก (Summary Dashboard) ---
    st.subheader("📊 Stiffness Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Slab ($K_s$)", fmt_sci(res['Ks']))
    c2.metric("Column ($\Sigma K_c$)", fmt_sci(res['Sum_Kc']))
    c3.metric("Torsion ($K_t$)", fmt_sci(res['Kt']))
    c4.metric("Equiv. Col ($K_{ec}$)", fmt_sci(res['Kec']), delta=f"-{(1-res['Kec']/res['Sum_Kc'])*100:.1f}%")

    # --- ส่วนที่ 2: ตารางการกระจายโมเมนต์ (Distribution) ---
    st.markdown("### 📋 Moment Distribution Factors")
    df_data = pd.DataFrame({
        "Member": ["Slab Strip (พื้น)", "Equivalent Column (เสาเสมือน)"],
        "Stiffness (K)": [fmt_sci(res['Ks']), fmt_sci(res['Kec'])],
        "DF (Ratio)": [f"{res['df_slab']:.4f}", f"{res['df_col']:.4f}"],
        "Percentage": [f"{res['df_slab']*100:.1f}%", f"{res['df_col']*100:.1f}%"]
    })
    st.table(df_data)

    # --- ส่วนที่ 3: แสดงการคำนวณอย่างละเอียด (Calculation Proof) ---
    with st.expander("🔍 ดูขั้นตอนการคำนวณอย่างละเอียด (Manual Check)"):
        
        # ก. ข้อมูลวัสดุ
        st.write("**A. Material & Geometry Properties**")
        st.write(f"- $E_c$ (Concrete): {fmt_num(res['Ec_kPa'])} $kN/m^2$")
        st.write(f"- $I_s$ (Slab): {fmt_sci(res['Is'])} $m^4$")
        st.write(f"- $I_c$ (Column): {fmt_sci(res['Ic'])} $m^4$")
        
        st.divider()
        
        # ข. การคำนวณ Stiffness
        st.write("**B. Stiffness Calculations**")
        st.latex(fr"K_s = \frac{{4 \times {fmt_sci(res['Ec_kPa'])} \times {fmt_sci(res['Is'])}}}{{L_1}} = {fmt_sci(res['Ks'])} \text{{ N-m}}")
        
        st.write("Torsion Constant ($C$):")
        st.latex(fr"C = \sum (1 - 0.63 \frac{{x}}{{y}}) \frac{{x^3 y}}{{3}} = {fmt_sci(res['C'])}")
        
        st.divider()
        
        # ค. การรวม Stiffness เป็น Kec
        st.write("**C. Equivalent Column Derivation**")
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
        st.latex(fr"\frac{{1}}{{K_{{ec}}}} = \frac{{1}}{{{fmt_sci(res['Sum_Kc'])}}} + \frac{{1}}{{{fmt_sci(res['Kt'])}}}")
        st.success(f"Result: $K_{{ec}} = {fmt_sci(res['Kec'])}$")

    st.info("💡 **Tip:** ค่า DF จะถูกส่งต่อไปยังขั้นตอน 'Moment Distribution' เพื่อหาโมเมนต์ลบและโมเมนต์บวกในแต่ละช่วง")
