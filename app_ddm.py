import streamlit as st
import pandas as pd
import math
from calc_ddm import calculate_ddm

def render_ddm_tab(calc_obj):
    """
    ฟังก์ชันสำหรับแสดงผล Tab DDM
    รับค่า calc_obj มาจาก app.py (Main File)
    """
    st.header("📘 Direct Design Method (DDM)")
    st.markdown("---")

    # --- 1. Validation & Calculation ---
    if not calc_obj:
        st.error("❌ Data missing: Please check inputs in the main sidebar.")
        return

    # เรียกฟังก์ชันคำนวณจาก calc_ddm.py
    try:
        results = calculate_ddm(calc_obj)
    except Exception as e:
        st.error(f"Calculation Error: {str(e)}")
        st.warning("Please check input values (e.g., Span length, Loads).")
        return

    # --- 2. Check for Warnings ---
    if results.get('warnings'):
        for warn in results['warnings']:
            st.warning(f"⚠️ ACI LIMITATION: {warn}")
    
    # Extract Data for Display
    inp = results['inputs']
    m_tot = results['moments_total']
    pct = results['cs_percents']
    steel = results['steel_required']
    shear = results['shear_check']
    chk_h = results['check_h']
    
    # ดึงค่า C1, C2 เพื่อใช้แสดงผล (ถ้ามีใน calc_obj หรือใช้ค่า default)
    c1_display = calc_obj.get('col_size', {}).get('c1', 50)
    c2_display = calc_obj.get('col_size', {}).get('c2', 50)
    
    # ==========================================
    # REPORT SECTION
    # ==========================================
    
    # --- Part 1: Design Summary ---
    st.subheader("📝 1. Design Parameters & Validation")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clear Span (Ln)", f"{inp['Ln']:.2f} m")
    col2.metric("Factored Load (Wu)", f"{inp['w_u_kn']:.2f} kN/m²", "1.2D+1.6L")
    col3.metric("Min. Thickness", f"{chk_h['req']:.3f} m", 
              delta="PASS" if chk_h['status'] == 'OK' else "FAIL",
              delta_color="normal" if chk_h['status'] == 'OK' else "inverse")
    col4.metric("Effective Depth (d)", f"{inp['d']*100:.1f} cm")

    # แสดงวิธีทำ Load แบบย่อ
    # หมายเหตุ: เรา assume ค่า DL/LL จาก w_u ย้อนกลับไม่ได้ง่ายๆ ถ้าไม่ส่งมาแยก
    # จึงแสดงค่า Wu สุดท้ายเลย
    st.info(f"**Design Load:** $w_u = {inp['w_u_kn']:.2f} \\; kN/m^2$")
    
    st.markdown("---")
    
    # --- Part 2: Moment Analysis ---
    st.subheader("📐 2. Moment Analysis & Distribution")
    
    # Step 2.1 Static Moment
    st.markdown("**Step 2.1: Total Static Moment ($M_0$)**")
    st.latex(r"M_0 = \frac{w_u L_2 L_n^2}{8}")
    st.write(f"$$M_0 = \\frac{{{inp['w_u_kn']:.2f} \\cdot {inp['L2']:.2f} \\cdot {inp['Ln']:.2f}^2}}{{8}} = \\mathbf{{{results['M0_kNm']:.2f} \\; kN\\cdot m}}$$")
    
    # Step 2.2 Distribution Table
    st.markdown("**Step 2.2: Distribution to Strips**")
    
    # Create DataFrame
    data = {
        "Location": ["Exterior Negative", "Positive (+)", "Interior Negative"],
        "Total Coeff.": [results['long_coeffs']['neg_ext'], results['long_coeffs']['pos'], results['long_coeffs']['neg_int']],
        "Total Moment (kNm)": [m_tot['neg_ext'], m_tot['pos'], m_tot['neg_int']],
        "Col Strip %": [pct['neg_ext_cs']*100, pct['pos_cs']*100, pct['neg_int_cs']*100],
        "CS Moment (kNm)": [results['design_moments']['neg_ext_cs'], results['design_moments']['pos_cs'], results['design_moments']['neg_int_cs']],
        "MS Moment (kNm)": [results['design_moments']['neg_ext_ms'], results['design_moments']['pos_ms'], results['design_moments']['neg_int_ms']],
    }
    df_moments = pd.DataFrame(data)
    
    # Formatting columns
    st.dataframe(df_moments.style.format({
        "Total Coeff.": "{:.2f}",
        "Total Moment (kNm)": "{:.2f}",
        "Col Strip %": "{:.1f}%",
        "CS Moment (kNm)": "{:.2f}",
        "MS Moment (kNm)": "{:.2f}"
    }), use_container_width=True)
    
    st.markdown("---")

    # --- Part 3: Reinforcement ---
    st.subheader("⛓️ 3. Reinforcement Design (Required Area)")
    st.markdown(r"Calculating $A_s$ using $M_u = \phi A_s f_y (d - a/2)$ with $\phi=0.9$")
    
    rc1, rc2 = st.columns(2)
    
    with rc1:
        st.markdown("#### Column Strip (CS)")
        st.write(f"Width = {min(inp['L1'], inp['L2'])/2:.2f} m")
        st.write(f"- **Ext. Neg:** $M_u={results['design_moments']['neg_ext_cs']:.2f} \Rightarrow A_s = \\mathbf{{{steel['neg_ext_cs']:.2f}}}$ cm²")
        st.write(f"- **Positive:** $M_u={results['design_moments']['pos_cs']:.2f} \Rightarrow A_s = \\mathbf{{{steel['pos_cs']:.2f}}}$ cm²")
        st.write(f"- **Int. Neg:** $M_u={results['design_moments']['neg_int_cs']:.2f} \Rightarrow A_s = \\mathbf{{{steel['neg_int_cs']:.2f}}}$ cm²")
        
    with rc2:
        st.markdown("#### Middle Strip (MS)")
        st.write(f"Width = {inp['L2'] - min(inp['L1'], inp['L2'])/2:.2f} m")
        st.write(f"- **Ext. Neg:** $M_u={results['design_moments']['neg_ext_ms']:.2f} \Rightarrow A_s = \\mathbf{{{steel['neg_ext_ms']:.2f}}}$ cm²")
        st.write(f"- **Positive:** $M_u={results['design_moments']['pos_ms']:.2f} \Rightarrow A_s = \\mathbf{{{steel['pos_ms']:.2f}}}$ cm²")
        st.write(f"- **Int. Neg:** $M_u={results['design_moments']['neg_int_ms']:.2f} \Rightarrow A_s = \\mathbf{{{steel['neg_int_ms']:.2f}}}$ cm²")

    st.caption("*Note: As shown is the greater of calculated As or Minimum As (Temp & Shrinkage)*")
    
    st.markdown("---")

    # --- Part 4: Shear Check ---
    st.subheader("🛡️ 4. Shear Safety Checks")
    
    # Punching Shear
    punch = shear['punching']
    st.markdown("#### 4.1 Punching Shear (Two-Way Action) - Critical")
    
    psc1, psc2 = st.columns([2, 1])
    with psc1:
        st.latex(r"V_u \le \phi V_c")
        st.write(f"**Applied Shear ($V_u$):** {punch['Vu']:.2f} kN")
        st.write(f"**Capacity ($\phi V_c$):** {punch['phi_Vc']:.2f} kN")
        
        # Ratio Logic
        ratio = punch['ratio']
        if ratio > 1.0:
            st.error(f"**RATIO = {ratio:.2f} (> 1.0) ❌ FAIL**")
            st.write("👉 Suggestion: Increase slab thickness, concrete strength, or add drop panel.")
        else:
            st.success(f"**RATIO = {ratio:.2f} (OK) ✅**")
            
    with psc2:
        # Parameter info
        b0_est = 2*(c1_display + inp['d']*100) + 2*(c2_display + inp['d']*100)
        st.info(f"""
        **Params:**
        - $d$: {inp['d']*100:.1f} cm
        - $b_o$: {b0_est:.1f} cm
        - $\phi$: 0.75
        """)

    # Beam Shear
    oneway = shear['oneway']
    with st.expander("See One-Way Shear Details (Beam Action)"):
        st.write(f"**$V_u$ (at d):** {oneway['Vu']:.2f} kN")
        st.write(f"**$\phi V_c$:** {oneway['phi_Vc']:.2f} kN")
        if oneway['status'] == 'PASS':
            st.success("Status: PASS")
        else:
            st.error("Status: FAIL")
