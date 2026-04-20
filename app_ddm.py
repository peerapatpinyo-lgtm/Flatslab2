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
        # STEP 1 & 2: SETUP (Side-by-side to save space)
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

        # Background calculations (Invisible to user unless needed)
        ln = max(L1 - c1, 0.65 * L1)
        h_slab_m = geom.get('h_s', 0.20)
        h_drop_m = geom.get('h_d', h_slab_m)
        has_drop = h_drop_m > h_slab_m
        edge_beam = geom.get('edge_beam_params', {})
        has_edge_beam = edge_beam.get('has_beam', False)
        eb_width = edge_beam.get('width_cm', 0) / 100.0
        eb_depth = edge_beam.get('depth_cm', 0) / 100.0
        case_type = "Exterior" if has_edge_beam else "Interior"
        
        KSC_TO_PA = 98066.5
        mat = calc_obj.get('mat', {})
        fc = mat.get('fc_pa', 240 * KSC_TO_PA) / KSC_TO_PA
        fy = mat.get('fy_pa', 4000 * KSC_TO_PA) / KSC_TO_PA

        loads = calc_obj.get('loads', {})
        G = 9.80665
        wu = loads.get('wu_pa', 0) / G
        dl = loads.get('w_dead', 0) / G
        ll = (wu - 1.4 * dl) / 1.7 if wu > 0 else 300

        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln, 'c1': c1, 'c2': c2,
            'wu': wu, 'dl': dl, 'll': ll,
            'h_slab': h_slab_m * 100, 'h_drop': h_drop_m * 100, 'has_drop': has_drop,
            'fc': fc, 'fy': fy, 'case_type': case_type, 
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
    
    # Show key numbers in a clean row
    c1, c2, c3 = st.columns(3)
    c1.metric("Design Load (Wu)", f"{wu:,.0f} kg/m²")
    c2.metric("Total Static Moment (Mo)", f"{Mo:,.0f} kg-m")
    c3.metric("Load Ratio (LL ≤ 2 DL)", "Pass" if ll <= 2*dl else "Fail")

    if warning_msgs:
        for msg in warning_msgs: 
            st.warning(msg) if "🚨" not in msg else st.error(msg)

    st.divider()

    # ==========================================================================
    # STEP 4: INTERACTIVE DETAILING
    # ==========================================================================
    st.markdown("### 🛠️ Step 4: Reinforcement Detailing")
    
    if not df_results.empty and 'Location' in df_results.columns:
        st.info("💡 **How to use:** Double-click on **[Bar Size]** or **[Spacing]** in the table to adjust rebar for each section. The status will update automatically.")
        
        cs_width = min(L1, L2) / 2.0
        ms_width = L2 - cs_width

        def get_strip_width(loc):
            return cs_width if 'column' in str(loc).lower() else ms_width

        df_design = df_results.copy()
        df_design['Strip Width (m)'] = df_design['Location'].apply(get_strip_width)
        df_design['Bar Size (mm)'] = selected_rebar
        df_design['Spacing (cm)'] = default_spacing

        # Minimal Editor Table
        editor_cols = ['Location', 'As Req (cm²)', 'Bar Size (mm)', 'Spacing (cm)']
        
        edited_df = st.data_editor(
            df_design[editor_cols],
            column_config={
                "Location": st.column_config.TextColumn("Strip Location", disabled=True),
                "As Req (cm²)": st.column_config.NumberColumn("Required Area (cm²)", disabled=True, format="%.2f"),
                "Bar Size (mm)": st.column_config.SelectboxColumn("Bar Size (mm) ✏️", options=[10, 12, 16, 20, 25]),
                "Spacing (cm)": st.column_config.NumberColumn("Spacing (cm) ✏️", min_value=2.5, max_value=50.0, step=2.5),
            },
            use_container_width=True,
            hide_index=True,
            key="rebar_editor"
        )

        # Recalculate based on user edits
        def compute_results(row, original_df):
            width_m = original_df.loc[original_df['Location'] == row['Location'], 'Strip Width (m)'].values[0]
            bar_area = math.pi * (row['Bar Size (mm)'] / 10.0)**2 / 4.0
            
            as_req = row['As Req (cm²)']
            as_prov = bar_area * ((width_m * 100.0) / row['Spacing (cm)'])
            num_bars = math.ceil((width_m * 100.0) / row['Spacing (cm)'])
            max_space = min((bar_area * width_m * 100.0) / as_req if as_req > 0 else 50.0, 2 * h_slab_m * 100) # ACI max spacing limit
            
            status = "✅ PASS" if as_prov >= as_req else "❌ FAIL"
            return pd.Series([width_m, num_bars, max_space, as_prov, status])

        edited_df[['Width (m)', 'Total Bars', 'Max Allowable Spacing (cm)', 'As Provided (cm²)', 'Status']] = edited_df.apply(lambda r: compute_results(r, df_design), axis=1)

        # Overall Status Alert
        if "❌ FAIL" in edited_df['Status'].values:
            st.error("⚠️ **Overall Status:** Some sections do NOT have enough reinforcement. Please reduce spacing or increase bar size.")
        else:
            st.success("🎉 **Overall Status:** All sections PASSED! The design is safe.")

        # Result Summary Table (Beautiful Format)
        st.markdown("#### 📊 Detailing Summary Report")
        display_cols = ['Location', 'Bar Size (mm)', 'Spacing (cm)', 'Total Bars', 'As Req (cm²)', 'As Provided (cm²)', 'Status']
        
        def highlight_status(val):
            return f"color: {'#ff4b4b' if 'FAIL' in str(val) else '#21c354'}; font-weight: bold;"
            
        styled_df = edited_df[display_cols].style.map(highlight_status, subset=['Status'])\
                                                .format({
                                                    'As Req (cm²)': "{:.2f}", 
                                                    'As Provided (cm²)': "{:.2f}",
                                                    'Total Bars': "{:.0f}"
                                                })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    else:
        st.error("❌ Cannot process calculation. Please check your slab thickness and load inputs.")

    # ==========================================================================
    # APPENDIX: CALC DETAILS (Hidden by default)
    # ==========================================================================
    with st.expander("📝 View Manual Calculation Steps & ACI Formulas"):
        st.markdown("**(1) Safety Checks**")
        if details.get('punch_step'): st.latex(rf"\begin{{aligned}} {details['punch_step']} \end{{aligned}}")
        if details.get('h_min_step'): st.latex(details['h_min_step'])
        
        st.markdown("**(2) Moment Variables**")
        if details.get('Mo_step'): st.latex(details['Mo_step'])
        if details.get('beta_t_step'): st.latex(details['beta_t_step'])
        
        st.markdown("**(3) Flexural Formulas**")
        st.latex(r"\rho = \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right)")
