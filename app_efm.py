import streamlit as st
import pandas as pd
import calc_efm

def render_efm_tab(calc_obj):
    st.header("2️⃣ Equivalent Frame Method (Stiffness Analysis)")
    st.markdown("วิเคราะห์ค่าความแข็งแรงเสมือนของโครงสร้างตามมาตรฐาน ACI 318")
    st.markdown("---")
    
    try:
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"Error: {e}")
        return
        
    def fmt_sci(val):
        return f"{val:.2e}"
    
    def fmt_num(val):
        return f"{val:,.2f}"

    # 1. Member Stiffness
    st.subheader("Step 1: Member Stiffness ($K$)")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Slab Stiffness ($K_s$)**")
        st.latex(r"K_s = \frac{4EI_s}{\ell_1}")
        st.metric("Ks", fmt_sci(res['Ks']), "N·m")
        st.caption(f"Inertia ($I_s$): {fmt_sci(res['Is'])} $m^4$")
        
    with c2:
        st.markdown("**Column Stiffness ($\Sigma K_c$)**")
        st.latex(r"K_c = \frac{4EI_c}{\ell_c}")
        st.metric("ΣKc", fmt_sci(res['Sum_Kc']), "N·m")
        st.caption(f"Inertia ($I_c$): {fmt_sci(res['Ic'])} $m^4$")
        
    with c3:
        st.markdown("**Torsional Stiffness ($K_t$)**")
        st.latex(r"K_t = \sum \frac{9E_{cs}C}{\ell_2(1-c_2/\ell_2)^3}")
        st.metric("Kt", fmt_sci(res['Kt']), "N·m")
        st.caption(f"Constant ($C$): {fmt_sci(res['C'])}")
        
    st.markdown("---")
    
    # 2. Equivalent Column
    st.subheader("Step 2: Equivalent Column Stiffness ($K_{ec}$)")
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.info("💡 **Concept:** เสาและส่วนรับแรงบิด (Torsional Member) ถูกมองว่าต่อกันแบบอนุกรม (Series) ความยืดหยุ่นรวมจึงลดลง")
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
    with col_r:
        st.metric("🎯 Kec", fmt_sci(res['Kec']), "N·m")
        if res['Sum_Kc'] > 0:
            red = (1 - res['Kec']/res['Sum_Kc']) * 100
            st.write(f"Stiffness ลดลง: :red[{red:.1f}%]")

    st.markdown("---")
    
    # 3. Distribution Factors
    st.subheader("Step 3: Moment Distribution Factors (DF)")
    
    # แสดงตารางเปรียบเทียบ
    df_res = pd.DataFrame([
        {"Member": "Slab (พื้น)", "Stiffness (K)": fmt_sci(res['Ks']), "DF": f"{res['df_slab']*100:.2f}%"},
        {"Member": "Equivalent Column (เสา)", "Stiffness (Kec)": fmt_sci(res['Kec']), "DF": f"{res['df_col']*100:.2f}%"}
    ])
    
    st.table(df_res)

    # 4. Detailed Breakdown (Expander)
    with st.expander("🔍 ดูรายละเอียดการคำนวณ (Calculation Breakdown)"):
        st.write("### ข้อมูลวัสดุและหน้าตัด")
        st.write(f"- **Modulus of Elasticity ($E_c$):** {fmt_num(res['Ec_kPa'] / 1e6)} GPa")
        
        st.write("### ขั้นตอนการกระจายโมเมนต์")
        st.latex(r"DF_{slab} = \frac{K_s}{K_s + K_{ec}}")
        st.latex(fr"DF_{{slab}} = \frac{{{fmt_sci(res['Ks'])}}}{{{fmt_sci(res['Ks'])} + {fmt_sci(res['Kec'])}}} = {res['df_slab']:.4f}")
        
        st.success(f"สรุป: เมื่อเกิด Moment ที่ Joint พื้นจะรับไป {res['df_slab']*100:.1f}% และเสารับไป {res['df_col']*100:.1f}%")

    st.toast("คำนวณ Stiffness สำเร็จ!", icon='✅')
