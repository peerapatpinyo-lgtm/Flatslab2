# app.py
import streamlit as st

# ------------------------------------------------------------------------------
# SETUP & CONFIGURATION
# ------------------------------------------------------------------------------
# ตรวจสอบว่ามี app_config หรือไม่ ถ้าไม่มีให้ใช้ค่า Default
try:
    from app_config import Units
except ImportError:
    class Units:
        G = 2400  # Default concrete density if file missing

import app_calc
import app_viz
import app_theory 
# import app_ddm  # Placeholder for DDM module
# import app_efm  # Placeholder for EFM module

# ==============================================================================
# MAIN APPLICATION INTERFACE
# ==============================================================================

st.set_page_config(page_title="Flat Slab Design Pro: Advanced", layout="wide")
st.title("🏗️ Flat Slab Design: Advanced Frame Analysis")
st.markdown("---")

# Initialize Session State for Column Location if not exists
if 'col_loc' not in st.session_state:
    st.session_state['col_loc'] = "Interior Column"

# --- Sidebar Report ---
st.sidebar.header("📊 Design Report")
status_container = st.sidebar.container()

# Define Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Input Parameters", 
    "📘 Engineering Theory", 
    "🏗️ Direct Design Method (DDM)", 
    "📐 Equivalent Frame Method (EFM)"
])

# ==============================================================================
# TAB 1: INPUTS & VISUALIZATION
# ==============================================================================
with tab1:
    col_input, col_viz = st.columns([1.2, 1.4])

    # --------------------------------------------------------------------------
    # LEFT COLUMN: INPUTS ONLY
    # --------------------------------------------------------------------------
    with col_input:
        # --- 1. Materials ---
        st.subheader("1. Materials & Loads")
        c1_mat, c2_mat = st.columns(2)
        with c1_mat: 
            fc = st.selectbox("Concrete f'c (ksc)", [240, 280, 320, 350, 400], index=1)
        with c2_mat: 
            fy = st.selectbox("Steel Grade (fy)", ["SD30", "SD40", "SD50"], index=1)

        lf_col1, lf_col2 = st.columns(2)
        with lf_col1: 
            lf_dl = st.number_input("DL Factor", value=1.4, step=0.1, format="%.2f")
        with lf_col2: 
            lf_ll = st.number_input("LL Factor", value=1.7, step=0.1, format="%.2f")
        
        auto_sw = st.checkbox("✅ Auto-calculate Self-weight", value=True)
        dl = st.number_input("Superimposed Dead Load (SDL) [kg/m²]", value=150, step=10)
        ll = st.number_input("Live Load (LL) [kg/m²]", value=300, step=50)

        st.divider()

        # --- 2. Geometry & Boundary ---
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
        
        far_end_up = "Pinned" # Default
        if not is_roof:
            with f_col1:
                far_end_up_sel = st.selectbox("Upper Col Far End", ["Fixed (4EI/L)", "Pinned (3EI/L)"], index=1)
                far_end_up = far_end_up_sel.split()[0]
        else:
             with f_col1: st.info("Upper Col: None (Roof)")

        with f_col2:
            far_end_lo_sel = st.selectbox("Lower Col Far End", ["Fixed (4EI/L)", "Pinned (3EI/L)"], index=1)
            far_end_lo = far_end_lo_sel.split()[0]

        # --- PLAN LAYOUT & SPANS (CRITICAL FIX FOR VISUALIZATION) ---
        st.markdown("##### 📏 Span Dimensions")
        
        # Location Selector
        col_location = st.selectbox(
            "Plan Location", 
            ["Interior Column", "Edge Column", "Corner Column"],
            help="Interior (4 slabs), Edge (3 slabs), Corner (2 slabs)"
        )
        
        # Determine logical flags
        is_interior = (col_location == "Interior Column")
        is_edge     = (col_location == "Edge Column")
        is_corner   = (col_location == "Corner Column")
        
        # --- SPAN INPUTS WITH FORCE RESET LOGIC ---
        # Note: Using `key` ensures Streamlit resets the widget when location changes
        
        # Row 1: L1 (Left - Right)
        col_l1a, col_l1b = st.columns(2)
        
        # L1 LEFT Logic
        with col_l1a:
            if is_interior:
                L1_l = st.number_input("L1 - Left Span (m)", value=6.0, step=0.5, key=f"L1_L_{col_location}")
            else:
                # Edge/Corner: FORCE 0.0 explicitly
                st.markdown("**L1 - Left Span**")
                st.info("🚫 0.00 m (Edge/Corner)")
                L1_l = 0.0 

        # L1 RIGHT Logic
        with col_l1b:
            L1_r = st.number_input("L1 - Right Span (m)", value=6.0, step=0.5, key="L1_R_Common")

        # Row 2: L2 (Top - Bottom)
        col_l2a, col_l2b = st.columns(2)
        
        # L2 TOP Logic
        with col_l2a:
            L2_t = st.number_input("L2 - Top Half (m)", value=6.0, step=0.5, key="L2_T_Common")

        # L2 BOTTOM Logic
        with col_l2b:
            if is_corner:
                # Corner: FORCE 0.0 explicitly
                st.markdown("**L2 - Bottom Half**")
                st.info("🚫 0.00 m (Corner)")
                L2_b = 0.0
            else:
                # Interior/Edge: Allow input
                L2_b = st.number_input("L2 - Bottom Half (m)", value=6.0, step=0.5, key=f"L2_B_{col_location}")

        # --- EDGE BEAM LOGIC ---
        st.markdown("##### 🧱 Edge Condition")
        # Initialize default empty params to prevent KeyError in Interior mode
        edge_beam_params = {"has_beam": False, "width_cm": 0.0, "depth_cm": 0.0}
        
        if not is_interior:
            has_edge_beam = st.checkbox("Has Edge Beam (Spandrel Beam)?", value=True)
            if has_edge_beam:
                eb_c1, eb_c2 = st.columns(2)
                with eb_c1:
                    eb_w = st.number_input("Edge Beam Width (cm)", value=30.0, step=5.0)
                with eb_c2:
                    eb_d = st.number_input("Edge Beam Depth (cm)", value=50.0, step=5.0)
                edge_beam_params = {"has_beam": True, "width_cm": eb_w, "depth_cm": eb_d}
            else:
                st.info("ℹ️ Unrestrained Edge (Flat Plate)")
        else:
            st.caption("Interior columns typically assume continuous slab (no edge beam).")

        # --- CANTILEVER ---
        with st.expander("🏗️ Cantilever / Eave (Overhang)", expanded=False):
            cant_c1, cant_c2 = st.columns(2)
            has_cant_left = False
            L_cant_left = 0.0
            has_cant_right = False
            L_cant_right = 0.0
            
            with cant_c1:
                # Disable Left Cantilever if L1_Left exists (Interior)
                cant_l_disabled = (L1_l > 0.01) 
                has_cant_left = st.checkbox("Left Cantilever", value=False, disabled=cant_l_disabled) 
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

        st.divider()

        # --- 3. Member Sizes ---
        st.subheader("3. Member Sizes")
        h_slab_cm = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0)
        
        col_sz1, col_sz2 = st.columns(2)
        with col_sz1: c1_cm = st.number_input("Column c1 (Analysis Dir) [cm]", value=50.0)
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
            
            # Intelligent Defaults based on geometry
            def_w1 = (L1_l + L1_r)/3.0 if is_interior else (L1_r/3.0) + (c1_cm/200.0)
            def_w2 = (L2_t + L2_b)/3.0 if not is_corner else (L2_t/3.0) + (c2_cm/200.0)
            
            with d_col2: drop_w1 = st.number_input("Drop Width W1 (m)", value=float(f"{def_w1:.2f}"))
            with d_col3: drop_w2 = st.number_input("Drop Width W2 (m)", value=float(f"{def_w2:.2f}"))

        # --- PROCESS DATA ---
        calc_obj = app_calc.prepare_calculation_data(
            h_slab_cm, h_drop_cm, has_drop, c1_cm, c2_cm, drop_w2,
            L1_l, L1_r, L2_t, L2_b, fc, fy, dl, ll, auto_sw, lf_dl, lf_ll,
            joint_type, h_up, h_lo, far_end_up, far_end_lo, cant_params,
            edge_beam_params
        )

        validator = app_calc.DesignCriteriaValidator(
            calc_obj['geom']['L1'], calc_obj['geom']['L2'], L1_l, L1_r, L2_t, L2_b,
            ll, (calc_obj['loads']['w_dead'] / Units.G), has_drop, cant_params,
            fy, col_location, h_slab_cm, (c1_cm/100), (c2_cm/100),
            edge_beam_params
        )
        
        # Run Checks
        thk_res = validator.check_min_thickness_detailed()
        ddm_ok, ddm_reasons = validator.check_ddm()

    # --------------------------------------------------------------------------
    # RIGHT COLUMN: VISUALIZATION & RESULTS
    # --------------------------------------------------------------------------
    with col_viz:
        st.subheader(f"👁️ Visualization: {col_location}")
        v_tab1, v_tab2 = st.tabs(["📐 Plan View", "🔍 True-Scale Section"])
        
        with v_tab1:
            # Note: We pass the explicit L1_l and L2_b which are now guaranteed to be 0.0 for Edge/Corner
            fig_plan = app_viz.draw_plan_view(
                L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, 
                col_location, has_drop, drop_w1, drop_w2, cant_params, edge_beam_params
            )
            st.pyplot(fig_plan)
        
        with v_tab2:
            fig_elev = app_viz.draw_elevation_real_scale(
                h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, 
                is_roof, far_end_up, far_end_lo, cant_params, edge_beam_params
            )
            st.pyplot(fig_elev)
            
        # Analysis Report (Short)
        st.divider()
        st.markdown("### 📋 Code Compliance Check")
        
        # 1. Thickness
        if thk_res['status']:
            st.success(f"✅ **Slab Thickness OK** (Prov: {thk_res['actual_h']} cm >= Req: {thk_res['req_h']:.2f} cm)")
        else:
            st.error(f"❌ **Slab Thickness NOT OK** (Prov: {thk_res['actual_h']} cm < Req: {thk_res['req_h']:.2f} cm)")
            
        with st.expander("📝 Show Thickness Calculation"):
            st.markdown(f"**Method:** ACI 318 Table 8.3.1.1 ({thk_res['case_name']})")
            st.latex(r"h_{min} = \frac{L_n (0.8 + f_y/1400)}{30 \sim 36}")
            st.write(f"- $L_n$ (Clear Span) = {thk_res['Ln']:.2f} m")
            st.write(f"- Req $h$ = {thk_res['req_h']:.2f} cm")

        # 2. Drop Panel
        if has_drop:
            drop_res = validator.check_drop_panel_detailed(h_drop_cm, drop_w1, drop_w2)
            st.markdown("#### 📉 Drop Panel Checks")
            dp_c1, dp_c2, dp_c3 = st.columns(3)
            
            # Helper for displaying status
            def status_mark(passed): return "✅" if passed else "❌"
            
            with dp_c1:
                st.metric("Depth Check", f"{drop_res['act_proj']} cm", 
                          f"Req: {drop_res['req_proj']:.2f} cm {status_mark(drop_res['chk_depth'])}")
            with dp_c2:
                st.metric("Width (Dir 1)", f"{drop_res['act_w1']:.2f} m", 
                          f"Req: {drop_res['req_total_w1']:.2f} m {status_mark(drop_res['chk_w1'])}")
            with dp_c3:
                st.metric("Width (Dir 2)", f"{drop_res['act_w2']:.2f} m", 
                          f"Req: {drop_res['req_total_w2']:.2f} m {status_mark(drop_res['chk_w2'])}")
            
            with st.expander("📝 Drop Panel Calculation Details"):
                st.latex(r"\text{Req Depth } \ge h_s/4")
                st.latex(r"\text{Req Width } \ge L/3")

        # Sidebar Update
        with status_container:
            st.markdown(f"**Condition:** `{joint_code}`")
            st.markdown(f"**Loc:** `{col_location}`")
            if edge_beam_params['has_beam']:
                st.markdown(f"**Beam:** `{edge_beam_params['width_cm']}x{edge_beam_params['depth_cm']} cm`")
            if ddm_ok: st.success("✅ **DDM:** Valid")
            else: st.error("❌ **DDM:** Invalid")
            st.info("✅ **EFM:** Valid")

# ==============================================================================
# TAB 2: ENGINEERING THEORY
# ==============================================================================
with tab2:
    app_theory.display_theory(calc_obj)

# ==============================================================================
# TAB 3: DIRECT DESIGN METHOD (DDM)
# ==============================================================================
with tab3:
    st.header("🏗️ Direct Design Method (DDM)")
    if ddm_ok:
        st.success("✅ This structure meets the criteria for Direct Design Method.")
        st.info("🚧 Module `app_ddm.py` is required to display calculations here.")
        # if 'app_ddm' in globals():
        #     app_ddm.render_ddm(calc_obj)
    else:
        st.error("❌ This structure DOES NOT meet DDM criteria. Please use EFM.")
        st.warning("Issues Found:")
        for r in ddm_reasons: st.write(f"- {r}")

# ==============================================================================
# TAB 4: EQUIVALENT FRAME METHOD (EFM)
# ==============================================================================
with tab4:
    st.header("📐 Equivalent Frame Method (EFM)")
    st.info("✅ EFM is a general method valid for this structure.")
    st.info("🚧 Module `app_efm.py` is required to display calculations here.")
    # if 'app_efm' in globals():
    #     app_efm.render_efm(calc_obj)
