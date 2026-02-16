# app_theory.py
import streamlit as st
import numpy as np

def display_theory(calc_data):
    """
    Renders the engineering theory with REAL-TIME SUBSTITUTION 
    of values based on user inputs.
    """
    
    # Extract Data for easy access
    g = calc_data['geom']
    mat = calc_data['mat']
    loads = calc_data['loads']
    stiff = calc_data['stiffness']
    mom = calc_data['moments']
    
    st.markdown("## 📘 Detailed Calculation Sheet")
    st.markdown("Reference Code: **ACI 318-19** & **EIT Standard (W.S.T.)**")
    
    # ==========================================================================
    # 1. LOAD ANALYSIS
    # ==========================================================================
    with st.expander("1. Load Analysis (Design Loads)", expanded=True):
        st.markdown("### 1.1 Ultimate Design Load ($w_u$)")
        st.markdown("The factored load is calculated based on the Load Factors (LF) provided.")

        # Prepare variables for display (Convert Pa to kN/m2 for readability)
        wd_kn = loads['w_dead'] / 1000
        wu_kn = loads['wu_pa'] / 1000
        # Back-calculate LL (approx) assuming standard factors were used in substitution, 
        # or just display the total since we have the final wu.
        
        st.latex(r"""
        w_u = (LF_{DL} \cdot w_{DL}) + (LF_{LL} \cdot w_{LL})
        """)
        
        st.write(f"Substituting the calculated area loads:")
        
        # Displaying the final summation
        st.latex(f"w_u = {wu_kn:.2f} \\text{{ kN/m}}^2")
        
        st.markdown("---")
        st.markdown("### 1.2 Clear Span ($L_n$)")
        st.markdown("In the Equivalent Frame Method, moments are based on the clear span face-to-face of columns/supports.")
        
        ln_val = g['Ln']
        l1_val = g['L1']
        c1_val = g['c1']
        
        st.latex(r"L_n = L_1 - c_1")
        st.latex(f"L_n = {l1_val:.2f} - {c1_val:.2f} = \\mathbf{{{ln_val:.2f}}} \\text{{ m}}")

    # ==========================================================================
    # 2. STATIC MOMENT
    # ==========================================================================
    with st.expander("2. Total Static Moment ($M_o$)", expanded=True):
        st.markdown("The total factored static moment for the span is determined by:")
        st.info("💡 This moment represents the total capacity required for the strip (sum of positive + negative moments).")
        
        # Formula
        st.latex(r"M_o = \frac{w_u L_2 L_n^2}{8}")
        
        # Substitution
        # wu is in Pa (N/m2), L is in m. Result in N.m -> /1000 for kN.m
        wu_val = loads['wu_pa']
        l2_val = g['L2']
        ln_val = g['Ln']
        
        mo_val_Nm = (wu_val * l2_val * (ln_val**2)) / 8
        mo_val_kNm = mo_val_Nm / 1000
        
        # Display Substitution
        st.markdown("**Substitution:**")
        st.latex(f"M_o = \\frac{{{wu_val/1000:.2f} \\times {l2_val:.2f} \\times {ln_val:.2f}^2}}{{8}}")
        
        # Result
        st.latex(f"M_o = \\mathbf{{{mo_val_kNm:.2f}}} \\text{{ kN}} \\cdot \\text{{m}}")
        
        

    # ==========================================================================
    # 3. EQUIVALENT FRAME PROPERTIES
    # ==========================================================================
    with st.expander("3. Equivalent Column Stiffness ($K_{ec}$)", expanded=False):
        st.markdown("The equivalent column stiffness ($K_{ec}$) accounts for the flexibility of the slab-column joint (torsional flexibility).")
        
        st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}")
        
        # Column Stiffness Kc
        st.markdown("#### 3.1 Column Stiffness ($K_c$)")
        k_up = stiff['K_up']
        k_lo = stiff['K_lo']
        sum_kc = stiff['Sum_K']
        
        st.latex(r"K_c = \frac{kEI}{L}")
        st.write("Using effective length factors (k) based on far-end conditions:")
        
        st.latex(f"K_{{c,top}} = {k_up/1e6:.2f} \\text{{ MN}} \\cdot \\text{{m}}")
        st.latex(f"K_{{c,bot}} = {k_lo/1e6:.2f} \\text{{ MN}} \\cdot \\text{{m}}")
        st.latex(f"\\Sigma K_c = {sum_kc/1e6:.2f} \\text{{ MN}} \\cdot \\text{{m}}")
        
        

    # ==========================================================================
    # 4. SHEAR CAPACITY CHECK
    # ==========================================================================
    with st.expander("4. Concrete Shear Capacity ($V_c$)", expanded=False):
        st.markdown("The nominal shear strength of concrete for non-prestressed slabs (ACI 318).")
        
        fc_pa = mat['fc_pa']
        fc_mpa = fc_pa / 1e6 # Convert Pa to MPa
        
        st.markdown("**Governing Formula (Approximate for Square Column):**")
        st.latex(r"V_c = 0.33 \sqrt{f'_c} b_o d")
        
        st.markdown("**Concrete Strength Used:**")
        st.latex(f"f'_c = {fc_mpa:.1f} \\text{{ MPa}}")
        
        st.markdown("> *Note: This calculation requires determining the effective depth ($d$) and critical perimeter ($b_o$), which depends on the rebar layout and cover.*")
        
        

    # ==========================================================================
    # 5. CANTILEVER MOMENT
    # ==========================================================================
    if calc_data['cantilever']['has_left'] or calc_data['cantilever']['has_right']:
        with st.expander("5. Cantilever Balancing Moment ($M_{cant}$)", expanded=True):
            st.markdown("The moment due to the cantilever load acts as a balancing moment at the support.")
            
            st.latex(r"M_{cant} = \frac{w_u L_{cant}^2}{2} \cdot L_2")
            
            w_u_line = loads['wu_pa'] * g['L2'] # N/m
            
            if calc_data['cantilever']['has_left']:
                lc = calc_data['cantilever']['L_left']
                mc = mom['M_cant_L'] / 1000 # kNm
                st.markdown("**Left Cantilever:**")
                st.latex(f"M_{{L}} = \\frac{{{w_u_line/1000:.2f} \\times {lc:.2f}^2}}{{2}} = \\mathbf{{{mc:.2f}}} \\text{{ kN}} \\cdot \\text{{m}}")
                
            if calc_data['cantilever']['has_right']:
                lc = calc_data['cantilever']['L_right']
                mc = mom['M_cant_R'] / 1000 # kNm
                st.markdown("**Right Cantilever:**")
                st.latex(f"M_{{R}} = \\frac{{{w_u_line/1000:.2f} \\times {lc:.2f}^2}}{{2}} = \\mathbf{{{mc:.2f}}} \\text{{ kN}} \\cdot \\text{{m}}")
