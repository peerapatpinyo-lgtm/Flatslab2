# app_ddm.py
import streamlit as st
import pandas as pd
import math
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("🏗️ Direct Design Method (DDM)")
    st.caption("Step-by-step reinforcement design for 2-way slabs using ACI 318.")
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

        # Background calculations
        ln_actual = L1 - c1
        ln = max(ln_actual, 0.65 * L1)
        h_slab_m = geom.get('h_s', 0.20)
        h_drop_m = geom.get('h_d', h_slab_m)
        has_drop = h_drop_m > h_slab_m
        
        # Effective depth assumption (concrete cover = 2.5 cm, half bar diameter)
        d_eff_m = h_slab_m - 0.025 - (selected_rebar / 2000.0) 
        
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
    c1_col.metric("Factored Load (Wu)", f"{wu:,.0f} kg/m²")
    c2_col.metric("Total Static Moment (Mo)", f"{Mo:,.0f} kg-m")
    c3_col.metric("Load Ratio Limit", "PASS" if ll <= 2*dl else "FAIL")

    if warning_msgs:
        for msg in warning_msgs: 
            st.warning(msg) if "🚨" not in msg else st.error(msg)

    st.divider()

    # ==========================================================================
    # STEP 4: INTERACTIVE DETAILING
    # ==========================================================================
    st.markdown("### 🛠️ Step 4: Reinforcement Detailing")
    
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
                "Spacing (cm)": st.column_config.NumberColumn("Spacing (cm) ✏️", min_value=2.5, max_value=50.0, step=2.5),
            },
            use_container_width=True, hide_index=True, key="rebar_editor"
        )

        def compute_results(row, original_df):
            width_m = original_df.loc[original_df['Location'] == row['Location'], 'Strip Width (m)'].values[0]
            bar_area = math.pi * (row['Bar Size (mm)'] / 10.0)**2 / 4.0
            as_req = row['As Req (cm²)']
            as_prov = bar_area * ((width_m * 100.0) / row['Spacing (cm)'])
            num_bars = math.ceil((width_m * 100.0) / row['Spacing (cm)'])
            max_space = min((bar_area * width_m * 100.0) / as_req if as_req > 0 else 50.0, 2 * h_slab_m * 100)
            status = "✅ PASS" if as_prov >= as_req else "❌ FAIL"
            return pd.Series([width_m, num_bars, max_space, as_prov, status])

        edited_df[['Width (m)', 'Total Bars', 'Max Spacing (cm)', 'Prov. Area (cm²)', 'Status']] = edited_df.apply(lambda r: compute_results(r, df_design), axis=1)

        if "❌ FAIL" in edited_df['Status'].values:
            st.error("⚠️ **Overall Status:** Insufficient reinforcement in some sections. Decrease spacing or increase bar size.")
        else:
            st.success("🎉 **Overall Status:** All sections PASSED! Reinforcement is adequate.")

        display_cols = ['Location', 'Bar Size (mm)', 'Spacing (cm)', 'Total Bars', 'As Req (cm²)', 'Prov. Area (cm²)', 'Status']
        def highlight_status(val):
            return f"color: {'#ff4b4b' if 'FAIL' in str(val) else '#21c354'}; font-weight: bold;"
            
        styled_df = edited_df[display_cols].style.map(highlight_status, subset=['Status']).format({
            'As Req (cm²)': "{:.2f}", 'Prov. Area (cm²)': "{:.2f}", 'Total Bars': "{:.0f}"
        })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # ==========================================================================
    # STEP 5: COMPREHENSIVE CALCULATION NOTE (ACI 318)
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 📑 Detailed Calculation Report")
    st.caption("Reference: ACI 318 Building Code Requirements for Structural Concrete")

    tab_limit, tab_load, tab_moment, tab_design, tab_shear = st.tabs([
        "📏 1. DDM Limitations", 
        "⚖️ 2. Factored Loads", 
        "📈 3. Static Moment", 
        "⚙️ 4. Flexural Design", 
        "🛡️ 5. Punching Shear"
    ])

    # --- TAB 1: Limitations ---
    with tab_limit:
        st.markdown("#### 1.1 Span Aspect Ratio")
        st.markdown("**Explanation:** Verifies that the panel is two-way and appropriate for DDM analysis.")
        st.latex(r"\text{Ratio} = \frac{\max(L_1, L_2)}{\min(L_1, L_2)} \le 2.0")
        span_ratio_val = max(L1, L2) / min(L1, L2)
        span_status = "✅ PASS" if span_ratio_val <= 2.0 else "❌ FAIL"
        st.markdown(f"**Substitution:** Ratio $= {max(L1, L2):.2f} / {min(L1, L2):.2f} = {span_ratio_val:.2f}$ ➡️ **{span_status}**")
        
        st.divider()
        st.markdown("#### 1.2 Loading Ratio")
        st.markdown("**Explanation:** Live load must not exceed two times the dead load.")
        st.latex(r"\text{Ratio} = \frac{LL}{DL} \le 2.0")
        load_ratio_val = ll / dl if dl > 0 else 0
        load_status = "✅ PASS" if load_ratio_val <= 2.0 else "❌ FAIL"
        st.markdown(f"**Substitution:** Ratio $= {ll:.0f} / {dl:.0f} = {load_ratio_val:.2f}$ ➡️ **{load_status}**")

        st.divider()
        st.markdown("#### 1.3 Effective Clear Span ($L_n$)")
        st.markdown("**Explanation:** The clear span must not be less than 65% of the center-to-center span.")
        st.latex(r"L_n = \max(L_1 - c_1, \ 0.65 L_1)")
        st.markdown(f"**Substitution:** $L_n = \max({L1:.2f} - {c1:.2f}, \ 0.65 \times {L1:.2f}) = {ln:.2f}$ m")

    # --- TAB 2: Loads ---
    with tab_load:
        st.markdown("#### Ultimate Factored Load ($W_u$)")
        st.markdown("**Explanation:** Computes the total design load per square meter applying ACI load factors.")
        st.latex(r"W_u = 1.4 DL + 1.7 LL")
        st.markdown(f"**Substitution:** $W_u = 1.4({dl:,.0f}) + 1.7({ll:,.0f}) = {wu:,.0f}$ kg/m²")

    # --- TAB 3: Moments ---
    with tab_moment:
        st.markdown("#### Total Factored Static Moment ($M_o$)")
        st.markdown("**Explanation:** Calculates the total static moment in the designated span direction.")
        st.latex(r"M_o = \frac{W_u L_2 L_n^2}{8}")
        st.markdown(f"**Substitution:** $M_o = \frac{{({wu:,.0f}) \times ({L2:.2f}) \times ({ln:.2f})^2}}{{8}} = {Mo:,.0f}$ kg-m")
        
        if details.get('Mo_step'): 
            st.divider()
            st.markdown("#### Moment Distribution Coefficients")
            st.latex(details['Mo_step'])
            if details.get('beta_t_step'): 
                st.latex(details['beta_t_step'])

    # --- TAB 4: Flexural Design ---
    with tab_design:
        st.markdown("#### Flexural Reinforcement Calculation (Ultimate Strength Design)")
        st.markdown("**Explanation:** Step-by-step determination of required steel area ($A_s$) for the critical section.")
        
        st.markdown("**General Governing Formulas:**")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        st.latex(r"\rho = \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right)")
        st.latex(r"A_{s,req} = \rho b d \ge A_{s,min} \ (0.0018 b h)")

        # Display rigorous sample calculation for the maximum moment strip
        if not df_results.empty and 'As Req (cm²)' in df_results.columns:
            st.divider()
            max_row = df_results.loc[df_results['As Req (cm²)'].idxmax()]
            loc_name = max_row['Location']
            max_as = max_row['As Req (cm²)']
            
            b_width = get_strip_width(loc_name) * 100.0 # Convert to cm
            d_eff_cm = d_eff_m * 100.0
            
            st.markdown(f"**Sample Calculation for Critical Section: `{loc_name}`**")
            st.markdown(f"- Strip Width ($b$): **{b_width:.1f} cm**")
            st.markdown(f"- Effective Depth ($d$): **{d_eff_cm:.2f} cm**")
            st.markdown(f"- Concrete Strength ($f'_c$): **{fc_ksc:.0f} kg/cm²**")
            st.markdown(f"- Steel Yield Strength ($f_y$): **{fy_ksc:.0f} kg/cm²**")
            
            # Since Mu is not explicitly in df_design by default, we back-calculate Rn for demonstration
            # If backend calc_ddm passes the full string, we use it, otherwise show final derivation.
            if details.get('flexural_step'):
                st.latex(details['flexural_step'])
            else:
                rho_min = 0.0018
                as_min = rho_min * b_width * (h_slab_m * 100.0)
                st.markdown("**Substitution & Results:**")
                st.latex(rf"A_{{s,min}} = 0.0018 \times {b_width:.1f} \times {h_slab_m*100.0:.1f} = {as_min:.2f} \text{{ cm}}^2")
                st.latex(rf"A_{{s,req}} = \max(\text{{Calculated }} A_s, \ A_{{s,min}}) = \mathbf{{{max_as:.2f} \text{{ cm}}^2}}")

    # --- TAB 5: Punching Shear ---
    with tab_shear:
        st.markdown("#### Two-Way (Punching) Shear Capacity")
        st.markdown("**Explanation:** Verifies that the slab can resist punching shear at the critical perimeter ($d/2$ from the column face) without specialized shear reinforcement.")
        
        st.markdown("**Governing Formulas:**")
        st.latex(r"V_u = W_u \times (L_1 L_2 - c_1 c_2)")
        st.latex(r"\phi V_c = \phi \cdot 0.33 \sqrt{f'_c} b_o d")
        st.latex(r"V_u \le \phi V_c")
        
        st.divider()
        st.markdown("**Substitution & Check:**")
        if details.get('punch_step'):
            st.latex(rf"\begin{{aligned}} {details['punch_step']} \end{{aligned}}")
        else:
            # Rigorous manual calculation for demonstration if backend doesn't provide string
            phi_shear = 0.85
            d_shear_cm = d_eff_m * 100.0
            bo_cm = 2 * ((c1*100 + d_shear_cm) + (c2*100 + d_shear_cm))
            
            vu_kg = wu * ((L1 * L2) - ((c1 + d_eff_m) * (c2 + d_eff_m)))
            phi_vc_kg = phi_shear * 0.33 * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
            
            st.latex(rf"b_o = 2 \times [({c1*100:.1f} + {d_shear_cm:.1f}) + ({c2*100:.1f} + {d_shear_cm:.1f})] = {bo_cm:.1f} \text{{ cm}}")
            st.latex(rf"V_u \approx {wu:,.0f} \times [({L1:.2f} \times {L2:.2f}) - ({c1+d_eff_m:.2f} \times {c2+d_eff_m:.2f})] = {vu_kg:,.0f} \text{{ kg}}")
            st.latex(rf"\phi V_c = {phi_shear} \times 0.33 \times \sqrt{{{fc_ksc:.0f}}} \times {bo_cm:.1f} \times {d_shear_cm:.1f} = {phi_vc_kg:,.0f} \text{{ kg}}")
            
            punch_status = "SAFE ✅" if vu_kg <= phi_vc_kg else "FAIL ❌ (Thicker slab or shear reinforcement required)"
            st.markdown(f"**Result:** $V_u \le \phi V_c \implies {vu_kg:,.0f} \le {phi_vc_kg:,.0f}$ ➡️ **{punch_status}**")
