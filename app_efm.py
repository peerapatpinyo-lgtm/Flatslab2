# app_efm.py
import streamlit as st
import pandas as pd
import calc_efm

def render_efm_tab(calc_obj):
    st.header("2️⃣ Equivalent Frame Method (Stiffness Analysis)")
    st.markdown("---")
    
    try:
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"Error: {e}")
        return
        
    # Helper to format Scientific
    def fmt_sci(val):
        return f"{val:.2e}"
    
    # 1. Member Stiffness
    st.subheader("Step 1: Member Stiffness ($K$)")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Slab Stiffness ($K_s$)**")
        st.latex(r"K_s = \frac{4EI_s}{\ell_1}")
        st.metric("Ks", fmt_sci(res['Ks']), "N.m")
        
    with c2:
        st.markdown("**Column Stiffness ($\Sigma K_c$)**")
        st.latex(r"K_c = \frac{4EI_c}{\ell_c}")
        st.metric("ΣKc", fmt_sci(res['Sum_Kc']), "N.m")
        
    with c3:
        st.markdown("**Torsional Stiffness ($K_t$)**")
        st.latex(r"K_t = \sum \frac{9E_{cs}C}{\ell_2(1-c_2/\ell_2)^3}")
        st.metric("Kt", fmt_sci(res['Kt']), "N.m")
        
    st.markdown("---")
    
    # 2. Equivalent Column
    st.subheader("Step 2: Equivalent Column Stiffness ($K_{ec}$)")
    st.info("The flexibility of the connection reduces the effective column stiffness.")
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
    with col_r:
        st.metric("🎯 Kec", fmt_sci(res['Kec']), "N.m")
        
    # Check Reduction
    if res['Sum_Kc'] > 0:
        reduction = (1 - res['Kec']/res['Sum_Kc']) * 100
        st.caption(f"Note: Torsional flexibility reduced column stiffness by **{reduction:.1f}%**")
        
    st.markdown("---")
    
    # 3. Distribution Factors
    st.subheader("Step 3: Moment Distribution Factors (DF)")
    st.write("At the joint, unbalanced moment is distributed based on Stiffness:")
    
    df_res = pd.DataFrame([
        {"Member": "Slab", "Stiffness (K)": fmt_sci(res['Ks']), "DF": f"{res['df_slab']*100:.2f}%"},
        {"Member": "Equivalent Column", "Stiffness (Kec)": fmt_sci(res['Kec']), "DF": f"{res['df_col']*100:.2f}%"}
    ])
    
    st.table(df_res)
    
    st.success("✅ EFM Stiffness Matrix Ready. (Moment Distribution process is next step)")
