# app.py
import streamlit as st
from app_config import Units
import app_calc
import app_viz
import app_theory 

# ==============================================================================
# MAIN APPLICATION INTERFACE
# ==============================================================================

st.set_page_config(page_title="Flat Slab Design Pro: Advanced", layout="wide")
st.title("🏗️ Flat Slab Design: Advanced Frame Analysis")
st.markdown("---")

if 'col_loc' not in st.session_state:
    st.session_state['col_loc'] = "Interior Column"

# --- Sidebar Report ---
st.sidebar.header("📊 Design Report")
status_container = st.sidebar.container()

# Define Tabs
tab1, tab2 = st.tabs(["📝 Input Parameters", "📘 Engineering Theory"])

# ==============================================================================
# TAB 1: INPUTS & VISUALIZATION
# ==============================================================================
with tab1:
    col_input, col_viz = st.columns([1.2, 1.4])

    # --------------------------------------------------------------------------
    # LEFT COLUMN: INPUTS ONLY
    # --------------------------------------------------------------------------
    with col_input:
        # 1. Materials
        st.subheader("1. Materials & Loads")
        c1_mat, c2_mat = st.columns(2)
        with c1_mat: fc = st.selectbox("Concrete f'c (ksc)", [240, 280, 320, 350, 400], index=1)
        with c2_mat: fy = st.selectbox("Steel Grade (fy)", ["SD30", "SD40", "SD50"], index=1)

        lf_col1, lf_col2 = st.columns(2)
        with lf_col1: lf_dl = st.number_input("DL Factor", value=1.2, step=0.1, format="%.2f")
        with lf_col2: lf_ll = st.number_input("LL Factor", value=1.6, step=0.1, format="%.2f")
        
        auto_sw = st.checkbox("✅ Auto-calculate Self-weight", value=True)
        dl = st.number_input("Superimposed Dead Load (SDL) [kg/m²]", value=100, step=10)
        ll = st.number_input("Live Load (LL) [kg/m²]", value=200, step=50)

        st.divider()

        # 2. Geometry & Boundary
        st.subheader("2. Geometry & Boundary Conditions")
        
        # Joint Type
        joint_type = st.radio(
            "Column Joint Condition:",
            ("Intermediate Floor", "Roof Joint"),
            horizontal=True
        )
        is_roof = (joint_type == "Roof Joint")
        joint_code = "Roof" if is_roof else "Interm."
        
        # Far End Conditions
        st.markdown("##### 📍 Column Far End Conditions (Stiffness)")
        f_col1, f_col2 = st.columns(2)
        
        far_end_up = "N/A"
        if not is_roof:
            with f_col1:
                far_end_up = st.selectbox("Upper Col Far End", ["Fixed (4EI/L)", "Pinned (3EI/L)"], index=0)
                far_end_up = far_end_up.split()[0] # Get 'Fixed' or 'Pinned'
        else:
             with f_col1: st.info("Upper Col: None")

        with f_col2:
            far_end_lo = st.selectbox("Lower Col Far End", ["Fixed (4EI/L)", "Pinned (3EI/L)"], index=0)
            far_end_lo = far_end_lo.split()[0]

        # Plan Layout
        st.markdown("##### 📏 Span Dimensions")
        col_location = st.selectbox("Plan Location", ["Interior Column", "Edge Column", "Corner Column"])
        is_corner = (col_location == "Corner Column")
        is_edge = (col_location == "Edge Column")
        
        col_l1a, col_l1b = st.columns(2)
        with col_l1a:
            l1_l_val = 0.0 if is_corner else 4.0
            L1_l = st.number_input("L1 - Left Span (m)", value=l1_l_val, disabled=is_corner)
        with col_l1b:
            L1_r = st.number_input("L1 - Right Span (m)", value=4.0)
            
        col_l2a, col_l2b = st.columns(2)
        with col_l2a:
            L2_t = st.number_input("L2 - Top Half (m)", value=4.0)
        with col_l2b:
            l2_b_val = 0.0 if (is_edge or is_corner) else 4.0
            L2_b = st.number_input("L2 - Bottom Half (m)", value=l2_b_val, disabled=(is_edge or is_corner))

        # Cantilever Settings
        st.markdown("##### 🏗️ Cantilever / Eave (Overhang)")
        with st.expander("Cantilever Configuration", expanded=True):
            cant_c1, cant_c2 = st.columns(2)
            has_cant_left = False
            L_cant_left = 0.0
            has_cant_right = False
            L_cant_right = 0.0
            
            with cant_c1:
                has_cant_left = st.checkbox("Left Cantilever", value=False, disabled=(L1_l > 0)) 
                if has_cant_left:
                    L_cant_left = st.number_input("Left Length (m)", value=1.5, step=0.1)
            
            with cant_c2:
                has_cant_right = st.checkbox("Right Cantilever", value=False)
                if has_cant_right:
                    L_cant_right = st.number_input("Right Length (m)", value=1.5, step=0.1)
            
            cant_params = {
                "has_left": has_cant_left, "L_left": L_cant_left,
                "has_right": has_cant_right, "L_right": L_cant_right
            }

        # Structural Dims
        st.markdown("##### 🧱 Member Sizes")
        h_slab_cm = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0)
        col_sz1, col_sz2 = st.columns(2)
        with col_sz1: c1_cm = st.number_input("Column c1 (Analysis) [cm]", value=50.0)
        with col_sz2: c2_cm = st.number_input("Column c2 (Transverse) [cm]", value=50.0)

        h_up = 0.0
        if not is_roof:
            h_up = st.number_input("Upper Storey Height (m)", value=3.0)
        h_lo = st.number_input("Lower Storey Height (m)", value=3.0)

        # Drop Panel
        has_drop = st.checkbox("Include Drop Panel", value=False)
        h_drop_cm, drop_w1, drop_w2 = 0.0, 0.0, 0.0
        if has_drop:
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1: h_drop_cm = st.number_input("Drop Depth (cm)", value=10.0)
            with d_col2: drop_w1 = st.number_input("Drop W1 (m)", value=2.5)
            with d_col3: drop_w2 = st.number_input("Drop W2 (m)", value=2.5)

        # --- PROCESS DATA (BUT DON'T SHOW YET) ---
        calc_obj = app_calc.prepare_calculation_data(
            h_slab_cm, h_drop_cm, has_drop, c1_cm, c2_cm, drop_w2,
            L1_l, L1_r, L2_t, L2_b, fc, fy, dl, ll, auto_sw, lf_dl, lf_ll,
            joint_type, h_up, h_lo, far_end_up, far_end_lo, cant_params
        )

        validator = app_calc.DesignCriteriaValidator(
            calc_obj['geom']['L1'], calc_obj['geom']['L2'], L1_l, L1_r, L2_t, L2_b,
            ll, (calc_obj['loads']['w_dead'] / Units.G), has_drop, cant_params,
            fy, col_location, h_slab_cm, (c1_cm/100), (c2_cm/100)
        )
        
        # Run Checks (Data only)
        thk_res = validator.check_min_thickness_detailed()
        ddm_ok, ddm_reasons = validator.check_ddm()


    # --------------------------------------------------------------------------
    # RIGHT COLUMN: VISUALIZATION & RESULTS
    # --------------------------------------------------------------------------
    with col_viz:
        st.subheader("👁️ Visualization & Analysis")
        v_tab1, v_tab2 = st.tabs(["📐 Plan View", "🔍 True-Scale Section"])
        
        with v_tab1:
            fig_plan = app_viz.draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_location, has_drop, drop_w1, drop_w2, cant_params)
            st.pyplot(fig_plan)
        
        with v_tab2:
            fig_elev = app_viz.draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, 
                                                         is_roof, far_end_up, far_end_lo, cant_params)
            st.pyplot(fig_elev)
            
        # Analysis Report
        st.markdown("### 📋 Analysis Results")
        
        # 1. Stiffness Report
        st.markdown("#### 1. Column Stiffness ($K_{col}$)")
        k_data = calc_obj['stiffness']
        c_k1, c_k2, c_k3 = st.columns(3)
        with c_k1: st.metric("K Top", f"{k_data['K_up']/1e6:.2f}", f"Factor: {k_data['k_fac_up']}EI")
        with c_k2: st.metric("K Bottom", f"{k_data['K_lo']/1e6:.2f}", f"Factor: {k_data['k_fac_lo']}EI")
        with c_k3: st.metric("Sum Kec", f"{k_data['Sum_K']/1e6:.2f}", "MN.m")
        
        # 2. Cantilever Moment Report
        if cant_params['has_left'] or cant_params['has_right']:
            st.markdown("#### 2. Cantilever Balancing Moment ($M_{cant}$)")
            st.caption("Moment from Cantilever helps balance the interior span moment.")
            m_data = calc_obj['moments']
            mc1, mc2 = st.columns(2)
            with mc1: 
                if cant_params['has_left']: st.metric("Left Moment (Neg)", f"{m_data['M_cant_L']/1000:.2f} kN.m")
            with mc2:
                if cant_params['has_right']: st.metric("Right Moment (Neg)", f"{m_data['M_cant_R']/1000:.2f} kN.m")
        
        st.divider()

        # ======================================================================
        #  MOVED SECTION: DESIGN CODE CHECKS (ACI 318)
        # ======================================================================
        st.markdown("### 🔍 Design Code Checks (ACI 318)")
        
        # --- 1. Minimum Thickness Check ---
        # Display Box
        if thk_res['status']:
            st.success(f"✅ **Slab Thickness OK** (Prov: {thk_res['actual_h']} cm >= Req: {thk_res['req_h']:.2f} cm)")
        else:
            st.error(f"❌ **Slab Thickness NOT OK** (Prov: {thk_res['actual_h']} cm < Req: {thk_res['req_h']:.2f} cm)")

        # Detailed Calculation (Toggle)
        with st.expander("📝 Show Calculation Steps: Slab Thickness"):
            st.markdown(f"**Case:** {thk_res['case_name']}")
            st.markdown(r"**Formula (ACI 318 Table 8.3.1.1):**")
            st.latex(r"h_{min} = \frac{L_n (0.8 + \frac{f_y}{1400})}{Denominator}")
            
            st.markdown("**Substitution:**")
            sub_str = r"h_{min} = \frac{" + f"{thk_res['Ln']:.2f}" + r"(" + f"0.8 + \\frac{{{thk_res['fy_mpa']}}}{{1400}}" + r")}{" + f"{thk_res['denom']}" + r"}"
            st.latex(sub_str)
            
            st.markdown("**Results:**")
            st.write(f"- Calculated Min = **{thk_res['calc_h']:.2f} cm**")
            st.write(f"- Absolute Code Min = **{thk_res['abs_min']} cm**")
            st.write(f"- **Final Required ($h_{{req}}$) = {thk_res['req_h']:.2f} cm**")

        # --- 2. Drop Panel Dashboard (Moved Here) ---
        if has_drop:
            drop_res = validator.check_drop_panel_detailed(h_drop_cm, drop_w1, drop_w2)
            
            st.markdown("#### 📉 Drop Panel Compliance Dashboard")
            
            # Create a clean layout for comparisons
            d_c1, d_c2, d_c3 = st.columns(3)
            
            # Helper Function
            def display_check_card(col, title, req_val, prov_val, unit, label_req="Required", label_prov="Provided"):
                ratio = prov_val / req_val if req_val > 0 else 0
                is_pass = prov_val >= req_val
                
                with col:
                    st.markdown(f"**{title}**")
                    if is_pass:
                        st.success(f"✅ **PASS** (Ratio: {ratio:.2f})")
                    else:
                        st.error(f"❌ **FAIL** (Ratio: {ratio:.2f})")
                    
                    # Comparison Metrics
                    c_m1, c_m2 = st.columns(2)
                    with c_m1:
                        st.metric(label=label_prov, value=f"{prov_val:.2f} {unit}")
                    with c_m2:
                        st.metric(label=label_req, value=f"{req_val:.2f} {unit}", delta=f"{req_val - prov_val:.2f} diff" if not is_pass else None, delta_color="inverse")
                    
                    # Visual Bar
                    prog_val = min(ratio / 2.0, 1.0)
                    st.progress(prog_val)
                    if is_pass:
                        st.caption(f"Safe by {(ratio-1)*100:.0f}%")
                    else:
                        st.caption(f"Insufficient by {(1-ratio)*100:.0f}%")

            # Display Cards
            display_check_card(d_c1, "1. Depth ($h_{drop}$)", 
                               drop_res['req_proj'], drop_res['act_proj'], "cm",
                               label_req="Min Req", label_prov="Actual")

            display_check_card(d_c2, "2. Width Dir 1", 
                               drop_res['req_total_w1'], drop_res['act_w1'], "m",
                               label_req="Min Req", label_prov="Actual")

            display_check_card(d_c3, "3. Width Dir 2", 
                               drop_res['req_total_w2'], drop_res['act_w2'], "m",
                               label_req="Min Req", label_prov="Actual")

            # Detailed Math Expander
            with st.expander("📝 View Detailed Math & Formulas (ACI 318 Ref.)", expanded=False):
                st.markdown("### Engineering Calculations")
                st.markdown("Reference: **ACI 318-19 Section 8.2.4 (Drop Panels)**")
                
                check_data = [
                    {"Parameter": "Drop Depth (Projection)", "Formula": r"h_s / 4", 
                     "Required": f"{drop_res['req_proj']:.2f} cm", "Provided": f"{drop_res['act_proj']:.2f} cm", 
                     "Status": "✅ PASS" if drop_res['chk_depth'] else "❌ FAIL"},
                    {"Parameter": "Total Width (Span 1)", "Formula": r"2 \times (L_1 / 6) = L_1 / 3", 
                     "Required": f"{drop_res['req_total_w1']:.2f} m", "Provided": f"{drop_res['act_w1']:.2f} m", 
                     "Status": "✅ PASS" if drop_res['chk_w1'] else "❌ FAIL"},
                    {"Parameter": "Total Width (Span 2)", "Formula": r"2 \times (L_2 / 6) = L_2 / 3", 
                     "Required": f"{drop_res['req_total_w2']:.2f} m", "Provided": f"{drop_res['act_w2']:.2f} m", 
                     "Status": "✅ PASS" if drop_res['chk_w2'] else "❌ FAIL"}
                ]
                
                st.markdown("#### Logic Verification")
                for item in check_data:
                    c1, c2, c3, c4 = st.columns([1.5, 1.5, 1, 1])
                    c1.markdown(f"**{item['Parameter']}**")
                    c2.latex(item['Formula'])
                    c3.markdown(f"Req: `{item['Required']}`")
                    c4.markdown(f"Prov: `{item['Provided']}` {item['Status']}")
                    st.divider()

        # --- 3. DDM/EFM Validity Check ---
        st.markdown("#### ✅ Method Validity (DDM vs EFM)")
        with st.expander(f"Code Check Details", expanded=True):
            for r in ddm_reasons: st.markdown(r)
        
        # Sidebar Update
        with status_container:
            st.markdown(f"**Condition:** `{joint_code}`")
            st.markdown(f"**Far Ends:** Top `{far_end_up}` | Bot `{far_end_lo}`")
            if ddm_ok: st.success("✅ **DDM:** Valid")
            else: st.error("❌ **DDM:** Invalid")
            st.info("✅ **EFM:** Valid")

# ==============================================================================
# TAB 2: ENGINEERING THEORY
# ==============================================================================
with tab2:
    app_theory.display_theory(calc_obj)
