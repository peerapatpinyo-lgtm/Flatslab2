import streamlit as st
import pandas as pd
import math
from calc_ddm import calculate_ddm

def render_ddm_page():
    st.title("📘 Direct Design Method (DDM)")
    st.markdown("---")

    # --- 1. Sidebar Inputs ---
    with st.sidebar:
        st.header("1. Geometry & Material")
        
        # Geometry
        col_c1 = st.number_input("Column C1 (cm)", 30, 100, 50, help="Dimension in direction of analysis")
        col_c2 = st.number_input("Column C2 (cm)", 30, 100, 50, help="Transverse dimension")
        
        L1 = st.number_input("Span Length L1 (m)", 3.0, 15.0, 6.0, help="Center-to-center span in direction of analysis")
        L2 = st.number_input("Span Width L2 (m)", 3.0, 15.0, 6.0, help="Transverse span width")
        h_slab = st.number_input("Slab Thickness (m)", 0.10, 0.50, 0.20, step=0.01)
        
        # Edge Beam
        has_edge_beam = st.checkbox("Has Edge Beam?", value=False)
        
        st.header("2. Loads")
        dl = st.number_input("Superimposed DL (kg/m²)", 0, 1000, 150)
        ll = st.number_input("Live Load (kg/m²)", 0, 2000, 300)
        
        st.header("3. Properties")
        fc = st.number_input("f'c (ksc)", 180, 500, 240)
        fy = st.number_input("fy (ksc)", 2400, 5000, 4000)

    # --- Prepare Data Object ---
    calc_obj = {
        'geom': {'L1_l': L1, 'L1_r': L1, 'L2': L2, 'h_slab': h_slab}, # Simplify L1 left/right for now
        'col_size': {'c1': col_c1, 'c2': col_c2},
        'loads': {'DL': dl, 'LL': ll}, # Separate DL/LL for validation
        'edge_beam': {'has_beam': has_edge_beam},
        'mat': {'fc': fc, 'fy': fy}
    }

    # --- Calculate Button ---
    if st.button("🚀 Calculate Design", type="primary"):
        results = calculate_ddm(calc_obj)
        
        # --- Check for Validation Warnings ---
        if results.get('warnings'):
            for warn in results['warnings']:
                st.warning(f"⚠️ ACI LIMITATION: {warn}")
        
        # Extract Data
        inp = results['inputs']
        m_tot = results['moments_total']
        pct = results['cs_percents']
        steel = results['steel_required']
        shear = results['shear_check']
        chk_h = results['check_h']
        
        # ==========================================
        # REPORT SECTION
        # ==========================================
        
        # --- Tab 1: Design Summary ---
        st.subheader("📝 1. Design Parameters & Validation")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Clear Span (Ln)", f"{inp['Ln']:.2f} m")
        c2.metric("Factored Load (Wu)", f"{inp['w_u_kn']:.2f} kN/m²", f"1.2D+1.6L")
        c3.metric("Min. Thickness", f"{chk_h['req']:.3f} m", 
                  delta="PASS" if chk_h['status'] == 'OK' else "FAIL",
                  delta_color="normal" if chk_h['status'] == 'OK' else "inverse")
        c4.metric("Effective Depth (d)", f"{inp['d']*100:.1f} cm")

        st.info(f"**Load Calculation:** $w_u = 1.2({dl} + 2400\\times{h_slab}) + 1.6({ll}) = {inp['w_u_kn']:.2f} \\; kN/m^2$")
        
        st.markdown("---")
        
        # --- Tab 2: Moment Analysis ---
        st.subheader("📐 2. Moment Analysis & Distribution")
        
        # Step 2.1 Static Moment
        st.markdown("**Step 2.1: Total Static Moment ($M_0$)**")
        st.latex(r"M_0 = \frac{w_u L_2 L_n^2}{8}")
        st.write(f"$$M_0 = \\frac{{{inp['w_u_kn']:.2f} \\cdot {inp['L2']:.2f} \\cdot {inp['Ln']:.2f}^2}}{{8}} = \\mathbf{{{results['M0_kNm']:.2f} \\; kN\\cdot m}}$$")
        
        # Step 2.2 Distribution Table
        st.markdown("**Step 2.2: Distribution to Strips**")
        
        # Create a nice DataFrame for display
        data = {
            "Location": ["Exterior Negative", "Positive (+)", "Interior Negative"],
            "Total Coeff.": [results['long_coeffs']['neg_ext'], results['long_coeffs']['pos'], results['long_coeffs']['neg_int']],
            "Total Moment (kNm)": [m_tot['neg_ext'], m_tot['pos'], m_tot['neg_int']],
            "Col Strip %": [pct['neg_ext_cs']*100, pct['pos_cs']*100, pct['neg_int_cs']*100],
            "CS Moment (kNm)": [results['design_moments']['neg_ext_cs'], results['design_moments']['pos_cs'], results['design_moments']['neg_int_cs']],
            "MS Moment (kNm)": [results['design_moments']['neg_ext_ms'], results['design_moments']['pos_ms'], results['design_moments']['neg_int_ms']],
        }
        df_moments = pd.DataFrame(data)
        st.dataframe(df_moments.style.format({
            "Total Coeff.": "{:.2f}",
            "Total Moment (kNm)": "{:.2f}",
            "Col Strip %": "{:.1f}%",
            "CS Moment (kNm)": "{:.2f}",
            "MS Moment (kNm)": "{:.2f}"
        }), use_container_width=True)
        
        st.markdown("---")

        # --- Tab 3: Reinforcement ---
        st.subheader("⛓️ 3. Reinforcement Design (Required Area)")
        st.markdown("Calculating $A_s$ using $M_u = \phi A_s f_y (d - a/2)$ with $\phi=0.9$")
        
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

        # --- Tab 4: Shear Check ---
        st.subheader("🛡️ 4. Shear Safety Checks")
        
        # Punching Shear
        punch = shear['punching']
        st.markdown("#### 4.1 Punching Shear (Two-Way Action) - Critical")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.latex(r"V_u \le \phi V_c")
            st.write(f"**Applied Shear ($V_u$):** {punch['Vu']:.2f} kN")
            st.write(f"**Capacity ($\phi V_c$):** {punch['phi_Vc']:.2f} kN")
            
            # Progress bar for ratio
            ratio = punch['ratio']
            if ratio > 1.0:
                st.error(f"**RATIO = {ratio:.2f} (> 1.0) ❌ FAIL**")
                st.write("👉 Suggestion: Increase slab thickness, concrete strength, or add drop panel.")
            else:
                st.success(f"**RATIO = {ratio:.2f} (OK) ✅**")
                
        with col2:
            # Simple visual for logic
            st.info("""
            **Parameters:**
            - $d = {:.1f}$ cm
            - $b_o = {:.1f}$ cm
            - $\phi = 0.75$
            """.format(inp['d']*100, (2*(col_c1+inp['d']*100) + 2*(col_c2+inp['d']*100))))

        # Beam Shear
        oneway = shear['oneway']
        with st.expander("See One-Way Shear Details (Beam Action)"):
            st.write(f"**$V_u$ (at d):** {oneway['Vu']:.2f} kN")
            st.write(f"**$\phi V_c$:** {oneway['phi_Vc']:.2f} kN")
            if oneway['status'] == 'PASS':
                st.success("Status: PASS")
            else:
                st.error("Status: FAIL")

    else:
        st.info("👈 Please adjust parameters in the sidebar and click 'Calculate Design'")

if __name__ == "__main__":
    render_ddm_page()
