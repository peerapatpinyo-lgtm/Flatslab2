# app_ddm.py
import streamlit as st
import pandas as pd
import math
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("🏢 Professional Slab Design Report (DDM)")
    st.caption("Detailed Engineering Calculation Note according to ACI 318")
    st.divider()

    try:
        # --- 1. INITIAL DATA & AXIS SELECTION ---
        geom = calc_obj.get('geom', {})
        orig_L1, orig_L2 = geom.get('L1', 6.0), geom.get('L2', 6.0)
        orig_c1, orig_c2 = geom.get('c1', 0.5), geom.get('c2', 0.5)
        
        c_dir1, c_dir2 = st.columns([2, 1])
        with c_dir1:
            analysis_dir = st.radio("Analysis Direction:", 
                                  ["Direction 1 (Span L1)", "Direction 2 (Span L2)"], 
                                  horizontal=True)
        
        if "Direction 1" in analysis_dir:
            L1, L2, c1, c2 = orig_L1, orig_L2, orig_c1, orig_c2
        else:
            L1, L2, c1, c2 = orig_L2, orig_L1, orig_c2, orig_c1

        # --- 2. INPUT PREPARATION ---
        ln = max(L1 - c1, 0.65 * L1)
        h_slab_m = geom.get('h_s', 0.20)
        h_drop_m = geom.get('h_d', h_slab_m)
        has_drop = h_drop_m > h_slab_m
        
        mat = calc_obj.get('mat', {})
        KSC_TO_PA = 98066.5
        fc = mat.get('fc_pa', 240 * KSC_TO_PA) / KSC_TO_PA
        fy = mat.get('fy_pa', 4000 * KSC_TO_PA) / KSC_TO_PA

        loads = calc_obj.get('loads', {})
        G = 9.80665
        wu = loads.get('wu_pa', 0) / G
        dl = loads.get('w_dead', 0) / G
        ll = (wu - 1.4 * dl) / 1.7 if wu > 0 else 300

        # Global Rebar
        st.sidebar.markdown("### 🛠️ Global Design Settings")
        selected_rebar = st.sidebar.selectbox("Standard Bar Size:", [10, 12, 16, 20, 25], index=1, format_func=lambda x: f"DB{x}")
        default_spacing = st.sidebar.slider("Initial Spacing (cm):", 7.5, 30.0, 20.0, 2.5)

        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln, 'c1': c1, 'c2': c2,
            'wu': wu, 'dl': dl, 'll': ll,
            'h_slab': h_slab_m * 100, 'h_drop': h_drop_m * 100, 'has_drop': has_drop,
            'fc': fc, 'fy': fy, 'rebar_size': selected_rebar,
            'case_type': "Exterior" if geom.get('edge_beam_params', {}).get('has_beam') else "Interior"
        }

        # --- 3. CALCULATION ENGINE ---
        df_results, Mo, warning_msgs, details = calc_ddm.calculate_ddm(ddm_inputs)

    except Exception as e:
        st.error(f"Waiting for input data... ({e})")
        return

    # ==========================================================================
    # DISPLAY SECTION: CALCULATION REPORT
    # ==========================================================================
    
    # --- Part A: Design Summary ---
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Static Moment (Mo)", f"{Mo:,.0f} kg-m")
    col_m2.metric("Clear Span (Ln)", f"{ln:.2f} m")
    col_m3.metric("Slab Thickness", f"{h_slab_m*100:.1f} cm")

    # --- Part B: Detailed Calculation Note ---
    st.markdown("### 📝 Detailed Calculation Note")
    
    with st.container(border=True):
        tab_flow, tab_moment, tab_shear = st.tabs(["📐 Geometry & Loading", "📊 Moment Distribution", "🛡️ Shear & Safety"])
        
        with tab_flow:
            st.markdown("#### 1.1 Dimensional Verification")
            st.write(f"- Span Ratio (L1/L2): **{L1/L2:.2f}** (Limit: 0.5 to 2.0) {'✅' if 0.5 <= L1/L2 <= 2.0 else '❌'}")
            st.write(f"- Live/Dead Load Ratio: **{ll/dl:.2f}** (Limit: ≤ 2.0) {'✅' if ll/dl <= 2.0 else '❌'}")
            
            st.markdown("#### 1.2 Minimum Thickness (Deflection Check)")
            if details.get('h_min_step'):
                st.latex(details['h_min_step'])
                st.info(f"Required $h_{{min}}$ = {details.get('h_min_val', 0):.2f} cm | Provided $h$ = {h_slab_m*100:.1f} cm")

        with tab_moment:
            st.markdown("#### 2.1 Total Static Moment ($M_o$)")
            if details.get('Mo_step'): st.latex(details['Mo_step'])
            
            st.markdown("#### 2.2 Longitudinal Distribution Factors")
            # Create a small table for distribution factors
            dist_data = {
                "Location": ["Ext. Negative", "Positive", "Int. Negative"],
                "Factor (%)": [details.get('ext_neg_pct', 0), details.get('pos_pct', 0), details.get('int_neg_pct', 0)],
                "Moment (kg-m)": [details.get('ext_neg_m', 0), details.get('pos_m', 0), details.get('int_neg_m', 0)]
            }
            st.table(pd.DataFrame(dist_data))

        with tab_shear:
            st.markdown("#### 3.1 Punching Shear at Critical Section ($d/2$)")
            if details.get('punch_step'):
                st.latex(rf"\begin{{aligned}} {details['punch_step']} \end{{aligned}}")
            
            status_color = "green" if "Safe" in details.get('punch_status', '') else "red"
            st.markdown(f"Status: :{status_color}[**{details.get('punch_status', 'N/A')}**]")

    # --- Part C: Interactive Rebar Table ---
    st.markdown("### 🛠️ Final Reinforcement Design")
    
    if not df_results.empty:
        # Configuration for Editor
        cs_width = min(L1, L2) / 2.0
        ms_width = L2 - cs_width
        
        df_design = df_results.copy()
        df_design['Strip Width (m)'] = df_design['Location'].apply(lambda x: cs_width if 'column' in str(x).lower() else ms_width)
        df_design['Bar Size (mm)'] = selected_rebar
        df_design['Spacing (cm)'] = default_spacing

        edited_df = st.data_editor(
            df_design[['Location', 'As Req (cm²)', 'Bar Size (mm)', 'Spacing (cm)']],
            column_config={
                "As Req (cm²)": st.column_config.NumberColumn("As Required", format="%.2f", disabled=True),
                "Bar Size (mm)": st.column_config.SelectboxColumn("Bar Size ✏️", options=[10, 12, 16, 20, 25]),
                "Spacing (cm)": st.column_config.NumberColumn("Spacing ✏️", min_value=5.0, max_value=30.0, step=2.5),
            },
            use_container_width=True, hide_index=True
        )

        # Result Logic
        def verify(row):
            w = cs_width if 'column' in str(row['Location']).lower() else ms_width
            as_prov = (math.pi * (row['Bar Size (mm)']/10)**2 / 4) * (w * 100 / row['Spacing (cm)'])
            return pd.Series([as_prov, "✅ PASS" if as_prov >= row['As Req (cm²)'] else "❌ FAIL"])

        edited_df[['As Provided', 'Status']] = edited_df.apply(verify, axis=1)
        
        st.markdown("#### 📋 Design Summary Report")
        st.dataframe(edited_df.style.applymap(lambda x: 'color: red' if x == "❌ FAIL" else 'color: green', subset=['Status']), 
                     use_container_width=True, hide_index=True)

    st.divider()
    st.caption("Note: This calculation is based on ACI 318 Direct Design Method (DDM) constraints.")
