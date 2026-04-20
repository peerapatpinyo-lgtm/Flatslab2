# app_ddm.py
import streamlit as st
import pandas as pd
import math
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("🏗️ Direct Design Method (DDM) Analysis")
    st.markdown("---")

    # ==========================================================================
    # 1. DATA ADAPTER & DIRECTION SELECTION
    # ==========================================================================
    try:
        geom = calc_obj.get('geom', {})
        
        # Extract initial dimensions
        orig_L1 = geom.get('L1', 6.0)
        orig_L2 = geom.get('L2', 6.0)
        orig_c1 = geom.get('c1', 0.5)
        orig_c2 = geom.get('c2', 0.5)
        
        # --- Analysis Direction Toggle ---
        st.markdown("### 🧭 Analysis Direction")
        analysis_dir = st.radio(
            "Select Orthogonal Direction:",
            ["Direction 1 (Analyze along L1)", "Direction 2 (Analyze along L2)"],
            horizontal=True
        )
        
        # Axis Swapping Logic
        if analysis_dir == "Direction 1 (Analyze along L1)":
            L1, L2 = orig_L1, orig_L2
            c1, c2 = orig_c1, orig_c2
        else:
            # Swap axes for Direction 2
            L1, L2 = orig_L2, orig_L1
            c1, c2 = orig_c2, orig_c1
            st.info(f"🔄 **Swapped Axes:** Analyzing along L2 (Span = {L1:.2f} m, Transverse Width = {L2:.2f} m)")

        # Calculate new Clear Span (Ln)
        ln = L1 - c1
        # ACI 318 Limit: Ln >= 0.65 * L1
        if ln < 0.65 * L1:
            ln = 0.65 * L1

        # Convert thickness back to cm for calc_ddm.py
        h_slab_m = geom.get('h_s', 0.20)
        h_drop_m = geom.get('h_d', h_slab_m)
        h_slab = h_slab_m * 100 
        h_drop = h_drop_m * 100 
        has_drop = h_drop > h_slab
        
        edge_beam = geom.get('edge_beam_params', {})
        has_edge_beam = edge_beam.get('has_beam', False)
        eb_width = edge_beam.get('width_cm', 0) / 100.0
        eb_depth = edge_beam.get('depth_cm', 0) / 100.0
        
        # Infer column case (Assume Exterior if edge beam is present)
        case_type = "Exterior" if has_edge_beam else "Interior"
        
        mat = calc_obj.get('mat', {})
        # Convert strength from Pa back to ksc
        KSC_TO_PA = 98066.5
        fc = mat.get('fc_pa', 240 * KSC_TO_PA) / KSC_TO_PA
        fy = mat.get('fy_pa', 4000 * KSC_TO_PA) / KSC_TO_PA

        loads = calc_obj.get('loads', {})
        G = 9.80665
        # Convert Loads from Pa to kg/m2
        wu = loads.get('wu_pa', 0) / G
        dl = loads.get('w_dead', 0) / G
        ll = (wu - 1.4 * dl) / 1.7 if wu > 0 else 300

        # --- Global Rebar Settings ---
        st.markdown("### ⚙️ Global Rebar Preferences")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            selected_rebar = st.selectbox(
                "Default Rebar Size (mm):", 
                options=[10, 12, 16, 20, 25], 
                index=1, 
                format_func=lambda x: f"DB{x}" 
            )
        with col_r2:
            default_spacing = st.number_input("Default Spacing (cm):", min_value=5.0, max_value=50.0, value=20.0, step=2.5)

        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln, 'c1': c1, 'c2': c2,
            'wu': wu, 'dl': dl, 'll': ll,
            'h_slab': h_slab, 'h_drop': h_drop, 'has_drop': has_drop,
            'fc': fc, 'fy': fy, 'case_type': case_type, 
            'has_edge_beam': has_edge_beam,
            'eb_width': eb_width, 'eb_depth': eb_depth,
            'rebar_size': selected_rebar 
        }
    except Exception as e:
        st.error(f"⚠️ Input Data Missing: {e}")
        return


    # ==========================================================================
    # 1.5 DDM LIMITATIONS CHECK
    # ==========================================================================
    st.subheader("🔍 ACI 318 DDM Constraints Check")
    col1, col2 = st.columns(2)
    
    is_load_ok = ll <= 2 * dl
    col1.info(f"**Load Ratio Check:**\n\nLive Load ({ll:.0f} kg/m²) ≤ 2 × Dead Load ({2*dl:.0f} kg/m²)\n\n**Status:** {'✅ OK' if is_load_ok else '❌ Exceeds Limit'}")
    
    is_span_ok = ln >= 0.65 * L1
    col2.info(f"**Clear Span Check:**\n\nLn ({ln:.2f} m) ≥ 0.65 × L1 ({0.65*L1:.2f} m)\n\n**Status:** {'✅ OK' if is_span_ok else '⚠️ Modified Ln required'}")

    # ==========================================================================
    # 2. CALCULATION
    # ==========================================================================
    df_results, Mo, warning_msgs, details = calc_ddm.calculate_ddm(ddm_inputs)

    # --- Display Metrics ---
    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("Factored Design Load (Wu)", f"{wu:,.0f} kg/m²")
    m2.metric("Total Static Moment (Mo)", f"{Mo:,.0f} kg-m")

    # Display Warnings
    if warning_msgs:
        for msg in warning_msgs: 
            if "🚨" in msg or "❌" in msg:
                st.error(msg)
            else:
                st.warning(msg)

    # ==========================================================================
    # 3. INTERACTIVE REBAR DESIGN
    # ==========================================================================
    st.subheader("🛠️ Interactive Reinforcement Design")

    if not df_results.empty and 'Location' in df_results.columns and 'As Req (cm²)' in df_results.columns:
        st.markdown("Adjust the **Bar Size** and **Spacing** in the table below to satisfy the required steel area for each strip.")
        
        # Calculate approximate strip widths (ACI 318)
        cs_width = min(L1, L2) / 2.0
        ms_width = L2 - cs_width

        def get_strip_width(loc):
            loc_str = str(loc).lower()
            if 'column' in loc_str:
                return cs_width
            elif 'middle' in loc_str:
                return ms_width
            return L2

        df_design = df_results.copy()
        df_design['Strip Width (m)'] = df_design['Location'].apply(get_strip_width)
        df_design['Bar Size (mm)'] = selected_rebar
        df_design['Spacing (cm)'] = default_spacing

        # Arrange columns for the editor
        editor_cols = ['Location', 'Strip Width (m)', 'As Req (cm²)', 'Bar Size (mm)', 'Spacing (cm)']
        
        # Display interactive dataframe
        edited_df = st.data_editor(
            df_design[editor_cols],
            column_config={
                "Location": st.column_config.TextColumn("Strip Location", disabled=True),
                "Strip Width (m)": st.column_config.NumberColumn("Width (m)", disabled=True, format="%.2f"),
                "As Req (cm²)": st.column_config.NumberColumn("As Req (cm²)", disabled=True, format="%.2f"),
                "Bar Size (mm)": st.column_config.SelectboxColumn("Bar Size (mm)", options=[10, 12, 16, 20, 25], required=True),
                "Spacing (cm)": st.column_config.NumberColumn("Spacing (cm)", min_value=5.0, max_value=50.0, step=1.0, required=True),
            },
            use_container_width=True,
            hide_index=True,
            key="rebar_editor"
        )

        # Process the edited data to calculate Provided Area
        def calculate_prov_area(row):
            d_mm = row['Bar Size (mm)']
            spacing_cm = row['Spacing (cm)']
            width_m = row['Strip Width (m)']
            
            # Area of single bar
            bar_area_cm2 = math.pi * (d_mm / 10.0)**2 / 4.0
            # Number of bars in the strip
            num_bars = (width_m * 100.0) / spacing_cm
            # Total provided area
            return bar_area_cm2 * num_bars

        edited_df['As Prov (cm²)'] = edited_df.apply(calculate_prov_area, axis=1)
        
        # Check Design Status
        edited_df['Status'] = edited_df.apply(
            lambda r: "✅ Pass" if r['As Prov (cm²)'] >= r['As Req (cm²)'] else "❌ Fail", axis=1
        )

        # --- Final Verification Summary ---
        st.markdown("#### 🏁 Design Verification Summary")
        verify_cols = ['Location', 'As Req (cm²)', 'As Prov (cm²)', 'Status']
        
        # Apply custom styling to highlight failed rows
        def highlight_status(val):
            color = '#ff4b4b' if 'Fail' in str(val) else '#21c354'
            return f'color: {color}; font-weight: bold;'
            
        styled_df = edited_df[verify_cols].style.map(highlight_status, subset=['Status'])\
                                                .format({'As Req (cm²)': "{:.2f}", 'As Prov (cm²)': "{:.2f}"})
                                                
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    else:
        st.error("❌ Calculation results are incomplete or cross-section limits were exceeded.")
        st.info("💡 Tip: Double-check the slab thickness and load values in the input tab.")

    # ==========================================================================
    # 4. CALCULATION STEPS & DETAILS (EXPANDER)
    # ==========================================================================
    st.markdown("---")
    with st.expander("📝 Show Calculation Steps & Safety Checks", expanded=True):
        st.markdown("### 🛡️ Safety Checks")
        st.markdown(f"**1. Punching Shear Verification:** {details.get('punch_status', 'Insufficient Data')}")
        
        punch_tex = details.get('punch_step', '')
        if punch_tex:
            st.latex(rf"\begin{{aligned}} {punch_tex} \end{{aligned}}")
        
        st.markdown("**2. Minimum Thickness (Deflection) Verification:**")
        h_min_tex = details.get('h_min_step', '')
        if h_min_tex:
            st.latex(h_min_tex)
        
        st.markdown("---")
        st.markdown("### 📊 Moment Distribution Variables")
        st.markdown("**1. Total Static Moment ($M_0$)**")
        mo_tex = details.get('Mo_step', '')
        if mo_tex:
            st.latex(mo_tex)
        
        st.markdown("**2. Torsional Stiffness ($\\beta_t$)**")
        beta_t_tex = details.get('beta_t_step', '')
        if beta_t_tex:
            st.latex(beta_t_tex)
            
        st.markdown(f"> **💡 Exterior Negative Moment assigned to Column Strip:** `{details.get('cs_ext_pct', 100):.1f}%`")

        st.markdown("---")
        st.markdown("### 💡 Flexural Design Equations")
        st.markdown("The program utilizes ACI 318 flexural design formulas to determine the required reinforcement:")
        st.latex(r"""
        \begin{aligned} 
        R_n &= \frac{M_u}{\phi b d^2} \\ 
        \rho &= \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right) \\ 
        A_{s,req} &= \rho b d \ge A_{s,min} 
        \end{aligned}
        """)

    st.markdown("---")
