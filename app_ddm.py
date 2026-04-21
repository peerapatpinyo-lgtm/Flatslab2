# app_ddm.py
import streamlit as st
import pandas as pd
import math
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("🏗️ Direct Design Method (DDM) - Professional Edition")
    st.caption("Comprehensive reinforcement and two-way shear design per ACI 318-19.")
    st.divider()

    try:
        geom = calc_obj.get('geom', {})
        orig_L1, orig_L2 = geom.get('L1', 6.0), geom.get('L2', 6.0)
        orig_c1, orig_c2 = geom.get('c1', 0.5), geom.get('c2', 0.5)
        
        # ==========================================================================
        # STEP 1 & 2: SETUP
        # ==========================================================================
        col_setup1, col_setup2 = st.columns(2)
        
        with col_setup1:
            st.markdown("### 🎯 Step 1: Analysis Direction")
            analysis_dir = st.radio(
                "Select span direction to analyze:",
                ["Direction 1 (Span = L1)", "Direction 2 (Span = L2)"],
                horizontal=True,
                label_visibility="collapsed"
            )
            
            if "Direction 1" in analysis_dir:
                L1, L2, c1, c2 = orig_L1, orig_L2, orig_c1, orig_c2
                st.success(f"**Current:** Analyzing Span = {L1:.2f} m")
            else:
                L1, L2, c1, c2 = orig_L2, orig_L1, orig_c2, orig_c1
                st.info(f"**Swapped:** Analyzing Span = {L1:.2f} m")

        with col_setup2:
            st.markdown("### ⚙️ Step 2: Global Rebar Setup")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                selected_rebar = st.selectbox("Base Bar Size:", [10, 12, 16, 20, 25], index=1, format_func=lambda x: f"DB{x}")
            with col_r2:
                default_spacing = st.number_input("Base Spacing (cm):", 5.0, 50.0, 20.0, 2.5)

        # Background calculations & Geometry
        ln_actual = L1 - c1
        ln = max(ln_actual, 0.65 * L1)
        h_slab_m = geom.get('h_s', 0.20)
        h_drop_m = geom.get('h_d', h_slab_m)
        has_drop = h_drop_m > h_slab_m
        
        # ACI 20.5.1.3: Specified concrete cover for cast-in-place slabs (not exposed to weather) is generally 20 mm
        cc_m = 0.020 
        d_eff_m = h_slab_m - cc_m - (selected_rebar / 2000.0) 
        
        edge_beam = geom.get('edge_beam_params', {})
        has_edge_beam = edge_beam.get('has_beam', False)
        eb_width = edge_beam.get('width_cm', 0) / 100.0
        eb_depth = edge_beam.get('depth_cm', 0) / 100.0
        case_type = "Exterior" if has_edge_beam else "Interior"
        
        KSC_TO_PA = 98066.5
        mat = calc_obj.get('mat', {})
        fc_ksc = mat.get('fc_pa', 240 * KSC_TO_PA) / KSC_TO_PA
        fy_ksc = mat.get('fy_pa', 4000 * KSC_TO_PA) / KSC_TO_PA

        loads = calc_obj.get('loads', {})
        G = 9.80665
        wu = loads.get('wu_pa', 0) / G
        dl = loads.get('w_dead', 0) / G
        ll = (wu - 1.4 * dl) / 1.7 if wu > 0 else 300

        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln, 'c1': c1, 'c2': c2,
            'wu': wu, 'dl': dl, 'll': ll,
            'h_slab': h_slab_m * 100, 'h_drop': h_drop_m * 100, 'has_drop': has_drop,
            'fc': fc_ksc, 'fy': fy_ksc, 'case_type': case_type, 
            'has_edge_beam': has_edge_beam, 'eb_width': eb_width, 'eb_depth': eb_depth,
            'rebar_size': selected_rebar 
        }

    except Exception as e:
        st.error(f"Missing Input Data: {e}")
        return

    st.divider()

    # ==========================================================================
    # STEP 3: CONSTRAINTS & FORCES
    # ==========================================================================
    df_results, Mo, warning_msgs, details = calc_ddm.calculate_ddm(ddm_inputs)

    st.markdown("### Step 3: Forces & Constraints")
    
    c1_col, c2_col, c3_col = st.columns(3)
    c1_col.metric("Factored Load (Wu)", f"{wu:,.0f} kg/m2")
    c2_col.metric("Total Static Moment (Mo)", f"{Mo:,.0f} kg-m")
    c3_col.metric("Effective Depth (d)", f"{d_eff_m*100:.1f} cm")

    if warning_msgs:
        for msg in warning_msgs: 
            st.warning(msg) if "Fail" not in msg else st.error(msg)

    st.divider()

    # ==========================================================================
    # STEP 4: INTERACTIVE DETAILING
    # ==========================================================================
    st.markdown("### Step 4: Reinforcement Detailing & Compliance")
    
    if not df_results.empty and 'Location' in df_results.columns:
        cs_width = min(L1, L2) / 2.0
        ms_width = L2 - cs_width

        def get_strip_width(loc):
            return cs_width if 'column' in str(loc).lower() else ms_width

        df_design = df_results.copy()
        df_design['Strip Width (m)'] = df_design['Location'].apply(get_strip_width)
        df_design['Bar Size (mm)'] = selected_rebar
        df_design['Spacing (cm)'] = default_spacing

        # Clean column names to prevent Streamlit rendering issues
        if 'As Req (cm²)' in df_design.columns:
            df_design.rename(columns={'As Req (cm²)': 'As Req (cm2)'}, inplace=True)

        editor_cols = ['Location', 'As Req (cm2)', 'Bar Size (mm)', 'Spacing (cm)']
        
        edited_df = st.data_editor(
            df_design[editor_cols],
            column_config={
                "Location": st.column_config.TextColumn("Strip Location", disabled=True),
                "As Req (cm2)": st.column_config.NumberColumn("Req. Area (cm2)", disabled=True, format="%.2f"),
                "Bar Size (mm)": st.column_config.SelectboxColumn("Bar Size (mm)", options=[10, 12, 16, 20, 25]),
                "Spacing (cm)": st.column_config.NumberColumn("Spacing (cm)", min_value=2.5, max_value=45.0, step=2.5),
            },
            use_container_width=True, hide_index=True, key="rebar_editor"
        )

        def compute_results(row, original_df):
            width_m = original_df.loc[original_df['Location'] == row['Location'], 'Strip Width (m)'].values[0]
            bar_area = math.pi * (row['Bar Size (mm)'] / 10.0)**2 / 4.0
            as_req = row['As Req (cm2)']
            as_prov = bar_area * ((width_m * 100.0) / row['Spacing (cm)'])
            num_bars = math.ceil((width_m * 100.0) / row['Spacing (cm)'])
            
            # ACI Maximum Spacing Rule: Min of 2h or 450 mm
            max_spacing_aci = min(2 * h_slab_m * 100, 45.0)
            
            status = "PASS" if (as_prov >= as_req and row['Spacing (cm)'] <= max_spacing_aci) else "FAIL"
            return pd.Series([width_m, num_bars, max_spacing_aci, as_prov, status])

        edited_df[['Width (m)', 'Total Bars', 'Max Spacing (cm)', 'Prov. Area (cm2)', 'Status']] = edited_df.apply(lambda r: compute_results(r, df_design), axis=1)

        if "FAIL" in edited_df['Status'].values:
            st.error("Overall Status: FAIL. Ensure provided area exceeds required area AND spacing does not exceed ACI limits.")
        else:
            st.success("Overall Status: PASS. Reinforcement is structurally adequate and strictly complies with ACI 318 spacing limits.")

        display_cols = ['Location', 'Bar Size (mm)', 'Spacing (cm)', 'Max Spacing (cm)', 'As Req (cm2)', 'Prov. Area (cm2)', 'Status']
        def highlight_status(val):
            return f"color: {'#ff4b4b' if 'FAIL' in str(val) else '#21c354'}; font-weight: bold;"
            
        styled_df = edited_df[display_cols].style.map(highlight_status, subset=['Status']).format({
            'As Req (cm2)': "{:.2f}", 'Prov. Area (cm2)': "{:.2f}", 'Max Spacing (cm)': "{:.1f}"
        })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # ==========================================================================
    # STEP 5: COMPREHENSIVE CALCULATION NOTE (ACI 318)
    # ==========================================================================
    st.markdown("---")
    st.markdown("### Detailed Engineering Calculation Report")
    st.caption("Reference: ACI 318-19 Building Code Requirements for Structural Concrete")

    tab_limit, tab_load, tab_flex, tab_shear = st.tabs([
        "1. Geometry Limits", 
        "2. Loads & Moments", 
        "3. Flexural Detailing", 
        "4. Punching Shear"
    ])

    # --- TAB 1: Limitations ---
    with tab_limit:
        st.markdown("#### ACI 318 Section 8.10.2: Dimensional Criteria for DDM")
        st.latex(r"\text{Span Aspect Ratio} = \frac{\max(L_1, L_2)}{\min(L_1, L_2)} \le 2.0")
        span_ratio_val = max(L1, L2) / min(L1, L2)
        st.markdown(f"**Result:** Ratio = {max(L1, L2):.2f} / {min(L1, L2):.2f} = **{span_ratio_val:.2f}**")
        
        st.divider()
        st.latex(r"\text{Loading Ratio} = \frac{LL}{DL} \le 2.0")
        load_ratio_val = ll / dl if dl > 0 else 0
        st.markdown(f"**Result:** Ratio = {ll:.0f} / {dl:.0f} = **{load_ratio_val:.2f}**")

        st.divider()
        st.latex(r"L_n = \max(L_1 - c_1, \ 0.65 L_1)")
        st.markdown(f"**Result:** Ln = max({L1:.2f} - {c1:.2f}, 0.65 x {L1:.2f}) = **{ln:.2f}** m")

    # --- TAB 2: Loads & Moments ---
    with tab_load:
        st.markdown("#### ACI 318 Section 5.3.1: Load Combinations")
        st.latex(r"W_u = 1.4 DL + 1.7 LL")
        st.markdown(f"**Result:** Wu = 1.4({dl:,.0f}) + 1.7({ll:,.0f}) = **{wu:,.0f}** kg/m2")

        st.divider()
        st.markdown("#### ACI 318 Section 8.10.3.2: Total Factored Static Moment")
        st.latex(r"M_o = \frac{W_u L_2 L_n^2}{8}")
        st.markdown(f"**Result:** Mo = ({wu:,.0f} x {L2:.2f} x {ln:.2f}^2) / 8 = **{Mo:,.0f}** kg-m")

    # --- TAB 3: Flexural Design (ALL SECTIONS) ---
    with tab_flex:
        st.markdown("#### ACI 318 Section 22.2: Flexural Reinforcement Required")
        st.markdown("Calculations for **every strip** based on the equivalent rectangular concrete stress block.")
        
        st.markdown("**General Formulas & Limits:**")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}, \quad \rho = \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right)")
        st.latex(r"A_{s} = \rho b d")
        
        rho_min = 0.0020 if fy_ksc < 4000 else 0.0018
        st.markdown("**ACI 24.4.3.2 Shrinkage and Temperature Limit:**")
        st.latex(rf"\rho_{{min}} = {rho_min} \quad \rightarrow \quad A_{{s,min}} = \rho_{{min}} \cdot b \cdot h_{{slab}}")
        st.divider()
        
        if not df_results.empty and 'Location' in df_results.columns:
            # Iterating through every single location calculated by the system
            for index, row in df_results.iterrows():
                loc_name = row['Location']
                as_req = row.get('As Req (cm2)', 0)
                
                b_width_m = get_strip_width(loc_name)
                b_width_cm = b_width_m * 100.0 
                d_eff_cm = d_eff_m * 100.0
                
                # Derive rho from required area for step-by-step verification
                rho_calc = as_req / (b_width_cm * d_eff_cm) if (b_width_cm * d_eff_cm) > 0 else 0
                as_min = rho_min * b_width_cm * (h_slab_m * 100.0)
                
                st.markdown(f"**Section: `{loc_name}`**")
                st.markdown(f"- Width ($b$) = {b_width_cm:.1f} cm, Effective Depth ($d$) = {d_eff_cm:.2f} cm")
                
                st.latex(rf"\text{{Required }} \rho = \frac{{{as_req:.2f}}}{{{b_width_cm:.1f} \times {d_eff_cm:.2f}}} = {rho_calc:.5f}")
                st.latex(rf"A_{{s,min}} = {rho_min} \times {b_width_cm:.1f} \times {h_slab_m*100.0:.1f} = {as_min:.2f} \text{{ cm}}^2")
                
                # Highlight the governing area
                st.latex(rf"A_{{s,req}} = \max(\rho \cdot b \cdot d, \ A_{{s,min}}) = \mathbf{{{as_req:.2f} \text{{ cm}}^2}}")
                st.markdown("---")

    # --- TAB 4: Punching Shear ---
    with tab_shear:
        st.markdown("#### ACI 318 Section 22.6.4: Critical Section for Two-Way Shear")
        
        d_shear_cm = d_eff_m * 100.0
        bo_cm = 2 * ((c1*100 + d_shear_cm) + (c2*100 + d_shear_cm))
        
        st.latex(rf"b_o = 2 \times [({c1*100:.1f} + {d_shear_cm:.1f}) + ({c2*100:.1f} + {d_shear_cm:.1f})] = {bo_cm:.1f} \text{{ cm}}")
        
        st.divider()
        st.markdown("#### ACI 318 Table 22.6.5.2: Two-Way Shear Strength ($V_c$)")
        st.markdown("$V_c$ is strictly determined as the smallest value from the three equations below.")
        
        phi_shear = 0.85 # ACI 318-19 Table 21.2.1
        alpha_s = 40 if case_type == "Interior" else (30 if has_edge_beam else 20)
        beta_c = max(c1, c2) / min(c1, c2)
        
        vc1 = 0.33 * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc2 = 0.17 * (1 + (2/beta_c)) * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc3 = 0.083 * (2 + (alpha_s * d_shear_cm / bo_cm)) * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc_gov = min(vc1, vc2, vc3)
        phi_vc = phi_shear * vc_gov
        
        st.markdown(f"- $\\beta$ (Column Aspect Ratio) = **{beta_c:.2f}**")
        st.markdown(f"- $\\alpha_s$ (Position Factor) = **{alpha_s}**")

        st.markdown("**Equation (a):**")
        st.latex(r"V_{c1} = 0.33 \sqrt{f'_c} b_o d")
        st.latex(rf"V_{{c1}} = 0.33 \sqrt{{{fc_ksc:.0f}}} \times {bo_cm:.1f} \times {d_shear_cm:.1f} = {vc1:,.0f} \text{{ kg}}")
        
        st.markdown("**Equation (b):**")
        st.latex(r"V_{c2} = 0.17 \left( 1 + \frac{2}{\beta} \right) \sqrt{f'_c} b_o d")
        st.latex(rf"V_{{c2}} = 0.17 \left( 1 + \frac{{2}}{{{beta_c:.2f}}} \right) \sqrt{{{fc_ksc:.0f}}} \times {bo_cm:.1f} \times {d_shear_cm:.1f} = {vc2:,.0f} \text{{ kg}}")
        
        st.markdown("**Equation (c):**")
        st.latex(r"V_{c3} = 0.083 \left( 2 + \frac{\alpha_s d}{b_o} \right) \sqrt{f'_c} b_o d")
        st.latex(rf"V_{{c3}} = 0.083 \left( 2 + \frac{{{alpha_s} \times {d_shear_cm:.1f}}}{{{bo_cm:.1f}}} \right) \sqrt{{{fc_ksc:.0f}}} \times {bo_cm:.1f} \times {d_shear_cm:.1f} = {vc3:,.0f} \text{{ kg}}")
        
        st.markdown("**Governing Capacity:**")
        st.latex(rf"\phi V_c = {phi_shear} \times \min(V_{{c1}}, V_{{c2}}, V_{{c3}}) = {phi_shear} \times {vc_gov:,.0f} = \mathbf{{{phi_vc:,.0f} \text{{ kg}}}}")

        st.divider()
        st.markdown("#### Demand vs Capacity Verification")
        vu_kg = wu * ((L1 * L2) - ((c1 + d_eff_m) * (c2 + d_eff_m)))
        
        st.latex(r"V_u = W_u \left[ L_1 L_2 - (c_1 + d)(c_2 + d) \right]")
        st.latex(rf"V_u = {wu:,.0f} \times \left[ ({L1:.2f} \times {L2:.2f}) - ({c1+d_eff_m:.2f} \times {c2+d_eff_m:.2f}) \right] = {vu_kg:,.0f} \text{{ kg}}")
        
        punch_status = "SAFE (Demand <= Capacity)" if vu_kg <= phi_vc else "FAIL (Increase slab thickness or drop panel)"
        st.markdown(f"**Final Verification:** $V_u \le \phi V_c \implies {vu_kg:,.0f} \le {phi_vc:,.0f}$ ➡️ **{punch_status}**")
