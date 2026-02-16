# app_ddm.py
import streamlit as st
import pandas as pd

def render_ddm_tab(calc_obj):
    st.header("1️⃣ Direct Design Method (DDM)")
    st.info("💡 วิธี DDM ใช้สัมประสิทธิ์ (Coefficients) ในการแบ่งโมเมนต์จาก Static Moment ($M_0$) โดยสมมติพฤติกรรมโครงสร้างตามมาตรฐาน")

    # 1. Retrieve Data
    geom = calc_obj['geom']
    loads = calc_obj['loads']
    L1 = geom['L1']
    L2 = geom['L2']
    Ln = L1 - (calc_obj['col_size']['c1']/100) # Clear Span
    w_u = loads['w_total'] # kg/m2
    
    # 2. Calculate Total Static Moment (M0)
    # M0 = (wu * L2 * Ln^2) / 8
    # Convert units: w_u (kg/m2) -> M0 (kg-m) -> then to kN-m for display
    M0_val = (w_u * L2 * (Ln**2)) / 8
    M0_knm = M0_val * 9.81 / 1000 # Convert kg-m to kN-m

    st.markdown("### 🅰️ Total Static Moment ($M_0$)")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Total $M_0$", f"{M0_knm:.2f} kN.m")
    with c2:
        st.markdown(r"$$M_0 = \frac{w_u \ell_2 \ell_n^2}{8}$$")
        st.caption(f"Calculated based on Clear Span ($L_n$) = {Ln:.2f} m")

    st.divider()

    # 3. Coefficient Distribution (ACI 318)
    st.markdown("### 🅱️ Moment Distribution (Longitudinal)")
    
    # Define Coefficients based on Location (Simplified for Demo)
    # In real app, logic depends on End Span vs Interior Span
    case_type = "Interior Span" # Default assumption for now
    
    if case_type == "Interior Span":
        # ACI Coeffs for Interior Span
        coefs = {"Neg": 0.65, "Pos": 0.35}
    
    st.write(f"**Case:** {case_type} (Flat Slab w/o Beams)")
    
    col_neg, col_pos = st.columns(2)
    
    # Negative Moment
    m_neg = M0_knm * coefs['Neg']
    with col_neg:
        st.error(f"**Negative Moment ($M_{{neg}}$)**")
        st.metric("Coeff", f"{coefs['Neg']*100:.0f}%", "Top Steel")
        st.metric("Value", f"{m_neg:.2f} kN.m")
        st.progress(coefs['Neg'])

    # Positive Moment
    m_pos = M0_knm * coefs['Pos']
    with col_pos:
        st.success(f"**Positive Moment ($M_{{pos}}$)**")
        st.metric("Coeff", f"{coefs['Pos']*100:.0f}%", "Bottom Steel")
        st.metric("Value", f"{m_pos:.2f} kN.m")
        st.progress(coefs['Pos'])

    # 4. Transverse Distribution (Column Strip vs Middle Strip)
    st.markdown("### ©️ Transverse Distribution (Column/Middle Strip)")
    
    # Simplified Logic for Interior Neg Moment (75% Col Strip, 25% Mid Strip)
    st.markdown("**Distribution of Negative Moment:**")
    cs_neg = m_neg * 0.75
    ms_neg = m_neg * 0.25
    
    dist_data = {
        "Strip Type": ["Column Strip (75%)", "Middle Strip (25%)"],
        "Design Moment (kN.m)": [f"{cs_neg:.2f}", f"{ms_neg:.2f}"],
        "Action": ["Reinforce @ Column Head", "Reinforce @ Mid Panel"]
    }
    st.table(pd.DataFrame(dist_data))
