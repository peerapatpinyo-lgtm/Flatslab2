# app_ddm.py
import streamlit as st
import pandas as pd
import math
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("🏗️ Direct Design Method (DDM) - Ultimate Professional Edition")
    st.caption("Comprehensive reinforcement and safety design for 2-way slabs according to ACI 318.")
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
                st.info(f"🔄 **Swapped:** Analyzing Span = {L1:.2f} m")

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
        
        # Concrete Cover and Effective Depth (ACI 20.5.1)
        # Assume 20 mm clear cover for slabs not exposed to weather
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
        st.error(f"⚠️ Missing Input Data: {e}")
        return

    st.divider()

    # ==========================================================================
    # STEP 3: CONSTRAINTS & FORCES
    # ==========================================================================
    df_results, Mo, warning_msgs, details = calc_ddm.calculate_ddm(ddm_inputs)

    st.markdown("### ✅ Step 3: Forces & Constraints")
    
    c1_col, c2_col, c3_col = st.columns(3)
    c1_col.metric("Factored Load ($W_u$)", f"{wu:,.0f} kg/m²")
    c2_col.metric("Total Static Moment ($M_o$)", f"{Mo:,.0f} kg-m")
    c3_col.metric("Effective Depth ($d$)", f"{d_eff_m*100:.1f} cm")

    if warning_msgs:
        for msg in warning_msgs: 
            st.warning(msg) if "🚨" not in msg else st.error(msg)

    st.divider()

    # ==========================================================================
    # STEP 4: INTERACTIVE DETAILING
    # ==========================================================================
    st.markdown("### 🛠️ Step 4: Reinforcement Detailing & Compliance")
    
    if not df_results.empty and 'Location' in df_results.columns:
        cs_width = min(L1, L2) / 2.0
        ms_width = L2 - cs_width

        def get_strip_width(loc):
            return cs_width if 'column' in str(loc).lower() else ms_width

        df_design = df_results.copy()
        df_design['Strip Width (m)'] = df_design['Location'].apply(get_strip_width)
        df_design['Bar Size (mm)'] = selected_rebar
        df_design['Spacing (cm)'] = default_spacing

        editor_cols = ['Location', 'As Req (cm²)', 'Bar Size (mm)', 'Spacing (cm)']
        
        edited_df = st.data_editor(
            df_design[editor_cols],
            column_config={
                "Location": st.column_config.TextColumn("Strip Location", disabled=True),
                "As Req (cm²)": st.column_config.NumberColumn("Req. Area (cm²)", disabled=True, format="%.2f"),
                "Bar Size (mm)": st.column_config.SelectboxColumn("Bar Size (mm) ✏️", options=[10, 12, 16, 20, 25]),
                "Spacing (cm)": st.column_config.NumberColumn("Spacing (cm) ✏️", min_value=2.5, max_value=45.0, step=2.5),
            },
            use_container_width=True, hide_index=True, key="rebar_editor"
        )

        def compute_results(row, original_df):
            width_m = original_df.loc[original_df['Location'] == row['Location'], 'Strip Width (m)'].values[0]
            bar_area = math.pi * (row['Bar Size (mm)'] / 10.0)**2 / 4.0
            as_req = row['As Req (cm²)']
            as_prov = bar_area * ((width_m * 100.0) / row['Spacing (cm)'])
            num_bars = math.ceil((width_m * 100.0) / row['Spacing (cm)'])
            
            # ACI Maximum Spacing Rule: Min of 2h or 450 mm
            max_spacing_aci = min(2 * h_slab_m * 100, 45.0)
            
            status = "✅ PASS" if (as_prov >= as_req and row['Spacing (cm)'] <= max_spacing_aci) else "❌ FAIL"
            return pd.Series([width_m, num_bars, max_spacing_aci, as_prov, status])

        edited_df[['Width (m)', 'Total Bars', 'Max Spacing (cm)', 'Prov. Area (cm²)', 'Status']] = edited_df.apply(lambda r: compute_results(r, df_design), axis=1)

        if "❌ FAIL" in edited_df['Status'].values:
            st.error("⚠️ **Overall Status:** Compliance failure. Ensure provided area exceeds required area AND spacing does not exceed ACI limits ($2h$ or 45 cm).")
        else:
            st.success("🎉 **Overall Status:** All sections PASSED! Reinforcement is structurally adequate and strictly complies with ACI 318 spacing limits.")

        display_cols = ['Location', 'Bar Size (mm)', 'Spacing (cm)', 'Max Spacing (cm)', 'As Req (cm²)', 'Prov. Area (cm²)', 'Status']
        def highlight_status(val):
            return f"color: {'#ff4b4b' if 'FAIL' in str(val) else '#21c354'}; font-weight: bold;"
            
        styled_df = edited_df[display_cols].style.map(highlight_status, subset=['Status']).format({
            'As Req (cm²)': "{:.2f}", 'Prov. Area (cm²)': "{:.2f}", 'Max Spacing (cm)': "{:.1f}"
        })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # ==========================================================================
    # STEP 5: COMPREHENSIVE CALCULATION NOTE (ACI 318)
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 📑 Detailed Engineering Calculation Report")
    st.caption("Strictly aligned with ACI 318 Building Code Requirements for Structural Concrete")

    tab_limit, tab_serv, tab_load, tab_flex, tab_shear = st.tabs([
        "📐 1. Geometry & Limitations", 
        "📏 2. Serviceability", 
        "⚖️ 3. Loads & Moments", 
        "⚙️ 4. Flexural Detailing", 
        "🛡️ 5. Punching Shear Capacity"
    ])

    # --- TAB 1: Limitations ---
    with tab_limit:
        st.markdown("#### 1.1 Dimensional Criteria for DDM Applicability")
        st.markdown("**Explanation:** ACI 318 restricts DDM to panels that are rectangular with a span ratio $\le 2.0$.")
        st.latex(r"\text{Ratio} = \frac{\max(L_1, L_2)}{\min(L_1, L_2)} \le 2.0")
        span_ratio_val = max(L1, L2) / min(L1, L2)
        st.markdown(f"**Verification:** Ratio $= {max(L1, L2):.2f} / {min(L1, L2):.2f} = {span_ratio_val:.2f}$ ➡️ **{'✅ PASS' if span_ratio_val <= 2.0 else '❌ FAIL'}**")
        
        st.divider()
        st.markdown("#### 1.2 Loading Ratio Limit")
        st.markdown("**Explanation:** Live load must not exceed two times the dead load to prevent severe pattern loading effects.")
        st.latex(r"\text{Ratio} = \frac{LL}{DL} \le 2.0")
        load_ratio_val = ll / dl if dl > 0 else 0
        st.markdown(f"**Verification:** Ratio $= {ll:.0f} / {dl:.0f} = {load_ratio_val:.2f}$ ➡️ **{'✅ PASS' if load_ratio_val <= 2.0 else '❌ FAIL'}**")

        st.divider()
        st.markdown("#### 1.3 Effective Clear Span ($L_n$)")
        st.latex(r"L_n = \max(L_1 - c_1, \ 0.65 L_1)")
        st.markdown(f"**Substitution:** $L_n = \max({L1:.2f} - {c1:.2f}, \ 0.65 \times {L1:.2f}) = {ln:.2f}$ m")

    # --- TAB 2: Serviceability ---
    with tab_serv:
        st.markdown("#### 2.1 Minimum Slab Thickness (Deflection Control)")
        st.markdown("**Explanation:** Per ACI 318 Section 8.3.1.1, slabs without interior beams spanning between supports must meet minimum thickness requirements to waive deflection computations.")
        
        fy_mpa = fy_ksc * 0.0980665
        st.markdown(f"- Steel Yield Strength ($f_y$): **{fy_mpa:.0f} MPa**")
        st.markdown(f"- Exterior Panel Condition: **{case_type}**")
        st.markdown(f"- Drop Panel Present: **{'Yes' if has_drop else 'No'}**")
        
        # Simplified ACI logic for h_min based on typical Grade 60 (420 MPa)
        h_min_formula = r"h_{min} = \frac{L_n}{30}" if case_type == "Exterior" and not has_edge_beam else r"h_{min} = \frac{L_n}{33}"
        h_min_req = (ln / 30) if (case_type == "Exterior" and not has_edge_beam) else (ln / 33)
        
        if has_drop: 
            h_min_req *= 0.90 # 10% reduction allowed if drop panels exist
            h_min_formula = r"0.90 \times " + h_min_formula
            
        st.latex(h_min_formula)
        st.markdown(f"**Required Thickness:** $h_{{min}} = {h_min_req*100:.1f}$ cm")
        st.markdown(f"**Provided Thickness:** $h_{{prov}} = {h_slab_m*100:.1f}$ cm ➡️ **{'✅ PASS (Deflection control satisfied)' if h_slab_m >= h_min_req else '❌ FAIL (Must compute deflections via FEM)'}**")
        
        if has_drop:
            st.divider()
            st.markdown("#### 2.2 Drop Panel Geometry Verification")
            st.markdown("**Explanation:** To qualify as a structural drop panel under ACI 318, it must extend $L/6$ in each direction and drop at least $h/4$.")
            st.latex(r"X_{drop} \ge \frac{L}{3} \quad \text{(Total width)}")
            st.latex(r"h_{drop} - h_{slab} \ge \frac{h_{slab}}{4}")
            st.info("Ensure your architectural/structural drawings reflect these minimum dimensions to validate the shear and flexural reductions used in this calculation.")

    # --- TAB 3: Loads & Moments ---
    with tab_load:
        st.markdown("#### 3.1 Ultimate Factored Load ($W_u$)")
        st.latex(r"W_u = 1.4 DL + 1.7 LL")
        st.markdown(f"**Substitution:** $W_u = 1.4({dl:,.0f}) + 1.7({ll:,.0f}) = {wu:,.0f}$ kg/m²")

        st.divider()
        st.markdown("#### 3.2 Total Factored Static Moment ($M_o$)")
        st.latex(r"M_o = \frac{W_u L_2 L_n^2}{8}")
        st.markdown(f"**Substitution:** $M_o = \frac{{({wu:,.0f}) \times ({L2:.2f}) \times ({ln:.2f})^2}}{{8}} = {Mo:,.0f}$ kg-m")
        
        if details.get('Mo_step'): 
            st.divider()
            st.markdown("#### 3.3 Moment Distribution Coefficients")
            st.latex(details['Mo_step'])

    # --- TAB 4: Flexural Design ---
    with tab_flex:
        st.markdown("#### 4.1 Ultimate Strength Design (USD) Formulas")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        st.latex(r"\rho = \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right)")
        st.latex(r"A_{s} = \rho b d")
        
        st.divider()
        st.markdown("#### 4.2 Shrinkage and Temperature Limits (ACI 24.4.3.2)")
        rho_min = 0.0020 if fy_ksc < 4000 else 0.0018
        st.markdown("**Explanation:** ACI mandates an absolute minimum reinforcement ratio ($\rho_{min}$) to control cracking.")
        st.latex(rf"\rho_{{min}} = {rho_min} \quad \text{{(Based on steel grade)}}")
        st.latex(r"A_{s,min} = \rho_{min} b h_{slab}")

        if not df_results.empty and 'As Req (cm²)' in df_results.columns:
            st.divider()
            max_row = df_results.loc[df_results['As Req (cm²)'].idxmax()]
            loc_name = max_row['Location']
            max_as = max_row['As Req (cm²)']
            b_width = get_strip_width(loc_name) * 100.0 
            
            st.markdown(f"#### 4.3 Rigorous Substitution for Critical Section: `{loc_name}`")
            st.markdown(f"- Strip Width ($b$): **{b_width:.1f} cm**")
            st.markdown(f"- Effective Depth ($d$): **{d_eff_m*100:.2f} cm**")
            
            as_min = rho_min * b_width * (h_slab_m * 100.0)
            st.latex(rf"A_{{s,min}} = {rho_min} \times {b_width:.1f} \times {h_slab_m*100.0:.1f} = {as_min:.2f} \text{{ cm}}^2")
            st.latex(rf"A_{{s,req}} = \max(\text{{Calculated }} A_s, \ A_{{s,min}}) = \mathbf{{{max_as:.2f} \text{{ cm}}^2}}")

    # --- TAB 5: Punching Shear ---
    with tab_shear:
        st.markdown("#### 5.1 Two-Way (Punching) Shear Capacity")
        st.markdown("**Explanation:** Evaluates the slab's capacity to resist shear failure at a critical perimeter located at $d/2$ from the column faces (ACI 22.6.4).")
        
        st.markdown("**Design Parameters:**")
        phi_shear = 0.85 # Using 0.85 (older codes) or adjust to 0.75 if following newest ACI strictly
        d_shear_cm = d_eff_m * 100.0
        bo_cm = 2 * ((c1*100 + d_shear_cm) + (c2*100 + d_shear_cm))
        alpha_s = 40 if case_type == "Interior" else 30 # Interior=40, Edge=30, Corner=20
        beta_c = max(c1, c2) / min(c1, c2)
        
        st.markdown(f"- Shear Reduction Factor ($\phi$): **{phi_shear}**")
        st.markdown(f"- Critical Perimeter ($b_o$): **{bo_cm:.1f} cm**")
        st.markdown(f"- Column Aspect Ratio ($\beta$): **{beta_c:.2f}**")
        st.markdown(f"- Position Factor ($\alpha_s$): **{alpha_s}** (assumed based on boundary conditions)")

        st.divider()
        st.markdown("#### 5.2 Ultimate Shear Force ($V_u$)")
        vu_kg = wu * ((L1 * L2) - ((c1 + d_eff_m) * (c2 + d_eff_m)))
        st.latex(r"V_u = W_u \left( L_1 L_2 - (c_1 + d)(c_2 + d) \right)")
        st.latex(rf"V_u = {wu:,.0f} \times \left[ ({L1:.2f} \times {L2:.2f}) - ({c1+d_eff_m:.2f} \times {c2+d_eff_m:.2f}) \right] = {vu_kg:,.0f} \text{{ kg}}")

        st.divider()
        st.markdown("#### 5.3 Concrete Shear Capacity ($V_c$)")
        st.markdown("**Explanation:** ACI 318 Section 22.6.5 dictates that $V_c$ shall be the smallest of three criteria:")
        
        vc1 = 0.33 * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc2 = 0.17 * (1 + (2/beta_c)) * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc3 = 0.083 * (2 + (alpha_s * d_shear_cm / bo_cm)) * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc_gov = min(vc1, vc2, vc3)
        phi_vc = phi_shear * vc_gov

        st.latex(r"V_{c1} = 0.33 \sqrt{f'_c} b_o d")
        st.markdown(f"$\quad \rightarrow V_{{c1}} = {vc1:,.0f}$ kg")
        
        st.latex(r"V_{c2} = 0.17 \left(1 + \frac{2}{\beta}\right) \sqrt{f'_c} b_o d")
        st.markdown(f"$\quad \rightarrow V_{{c2}} = {vc2:,.0f}$ kg")
        
        st.latex(r"V_{c3} = 0.083 \left(2 + \frac{\alpha_s d}{b_o}\right) \sqrt{f'_c} b_o d")
        st.markdown(f"$\quad \rightarrow V_{{c3}} = {vc3:,.0f}$ kg")
        
        st.markdown(f"**Governing Capacity ($\phi V_c$):** $\phi \times \min(V_{{c1}}, V_{{c2}}, V_{{c3}}) = {phi_shear} \times {vc_gov:,.0f} = \mathbf{{{phi_vc:,.0f} \text{{ kg}}}}$")
        
        punch_status = "SAFE ✅" if vu_kg <= phi_vc else "FAIL ❌ (Thicker slab, larger drop panel, or shear reinforcement required)"
        st.markdown(f"**Final Verdict:** $V_u \le \phi V_c \implies {vu_kg:,.0f} \le {phi_vc:,.0f}$ ➡️ **{punch_status}**")
