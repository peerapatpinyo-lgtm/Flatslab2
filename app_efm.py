# app_efm.py
import streamlit as st
import pandas as pd
import calc_efm # <--- เรียกใช้ไฟล์ Logic

def render_efm_tab(calc_obj):
    st.header("2️⃣ Equivalent Frame Method (EFM)")
    st.markdown("---")
    
    # เรียกฟังก์ชันคำนวณ
    res = calc_efm.calculate_efm(calc_obj)
    
    # 1. Kc
    st.subheader("Step 1: Column Stiffness ($K_c$)")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"- $I_c$ = {res['Ic']:.6f} m⁴")
        st.write(f"- $E_c$ = {res['Ec_kPa']/1e6:.2f} GPa")
    with c2:
        st.metric("ΣKc", f"{res['Kc_total']/1000:.1f}E3", "kN.m")
        
    st.markdown("---")
    
    # 2. Kt
    st.subheader("Step 2: Torsional Stiffness ($K_t$)")
    st.latex(r"K_t = \sum \frac{9E_{cs}C}{\ell_2(1 - \frac{c_2}{\ell_2})^3}")
    st.write(f"Torsion Constant C = {res['C_val']:.6f}")
    st.metric("Kt (Total)", f"{res['Kt_total']/1000:.1f}E3", "kN.m")
    
    st.markdown("---")
    
    # 3. Kec
    st.subheader("Step 3: Equivalent Stiffness ($K_{ec}$)")
    st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("1. ΣKc", f"{res['Kc_total']/1000:.1f}E3")
    col2.metric("2. Kt", f"{res['Kt_total']/1000:.1f}E3")
    col3.metric("🎯 Kec", f"{res['Kec']/1000:.1f}E3", "kN.m")
    
    # 4. DF Table
    st.subheader("Step 4: Distribution Factors")
    st.info("Moment Distribution Factors at the Joint:")
    df_data = {
        "Member": ["Slab (Ks)", "Equiv. Column (Kec)"],
        "Stiffness": [f"{res['Ks']/1000:.1f}E3", f"{res['Kec']/1000:.1f}E3"],
        "DF %": [f"{res['df_slab']*100:.1f}%", f"{res['df_col']*100:.1f}%"]
    }
    st.table(pd.DataFrame(df_data))
