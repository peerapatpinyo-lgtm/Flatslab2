# app.py
import streamlit as st

# ------------------------------------------------------------------------------
# SETUP & CONFIGURATION
# ------------------------------------------------------------------------------
try:
    from app_config import Units
except ImportError:
    class Units:
        G = 2400  # Default concrete density

import app_calc
import app_viz
import app_theory 
import app_ddm  
import app_efm

# ==============================================================================
# MAIN APPLICATION INTERFACE
# ==============================================================================

st.set_page_config(page_title="Flat Slab Design Pro: Advanced", layout="wide")
st.title("🏗️ Flat Slab Design: Advanced Frame Analysis")
st.markdown("---")

# Initialize Session State
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
        # LEFT COLUMN: INPUTS (ข้อมูล Physical Model ล้วนๆ)
        # --------------------------------------------------------------------------
        with col_input:
            st.subheader("1. Materials & Loads")
            c1_mat, c2_mat = st.columns(2)
            with c1_mat: 
                fc = st.selectbox("Concrete f'c (ksc)", [240, 280, 320, 350, 400], index=1)
            with c2_mat: 
                fy = st.selectbox("Steel Grade (fy)", ["SD30", "SD40", "SD50"], index=1)

            lf_col1, lf_col2 = st.columns(2)
            with lf_col1: lf_dl = st.number_input("DL Factor", value=1.4, step=0.1, format="%.2f")
            with lf_col2: lf_ll = st.number_input("LL Factor", value=1.7, step=0.1, format="%.2f")
            
            auto_sw = st.checkbox("✅ Auto-calculate Self-weight", value=True)
            dl = st.number_input("Superimposed Dead Load (SDL) [kg/m²]", value=150, step=10)
            ll = st.number_input("Live Load (LL) [kg/m²]", value=300, step=50)

            st.divider()

            # --- Geometry ---
            st.subheader("2. Geometry & Boundary Conditions")
            
            joint_type = st.radio("Column Joint Condition:", ("Intermediate Floor", "Roof Joint"), horizontal=True)
            is_roof = (joint_type == "Roof Joint")
            joint_code = "Roof" if is_roof else "Interm."
            
            st.markdown("##### 📍 Column Far End Conditions (Stiffness)")
            f_col1, f_col2 = st.columns(2)
            far_end_up = "Pinned"
            if not is_roof:
                with f_col1:
                    far_end_up_sel = st.selectbox("Upper Col Far End", ["Fixed (4EI/L)", "Pinned (3EI/L)"], index=1)
                    far_end_up = far_end_up_sel.split()[0]
            else:
                 with f_col1: st.info("Upper Col: None (Roof)")

            with f_col2:
                far_end_lo_sel = st.selectbox("Lower Col Far End", ["Fixed (4EI/L)", "Pinned (3EI/L)"], index=1)
                far_end_lo = far_end_lo_sel.split()[0]

            # --- PLAN LAYOUT ---
            st.markdown("##### 📏 Span Dimensions")
            col_location = st.selectbox("Plan Location", ["Interior Column", "Edge Column", "Corner Column"])
            
            is_interior = (col_location == "Interior Column")
            is_edge     = (col_location == "Edge Column")
            is_corner   = (col_location == "Corner Column")
            
            col_l1a, col_l1b = st.columns(2)
            with col_l1a:
                if is_interior: L1_l = st.number_input("L1 - Left Span (m)", value=6.0, step=0.5, key=f"L1_L_{col_location}")
                else:
                    st.markdown("**L1 - Left Span**")
                    st.info("🚫 0.00 m (Edge/Corner)")
                    L1_l = 0.0 
            with col_l1b: L1_r = st.number_input("L1 - Right Span (m)", value=6.0, step=0.5, key="L1_R_Common")

            col_l2a, col_l2b = st.columns(2)
            with col_l2a: L2_t = st.number_input("L2 - Top Half (m)", value=6.0, step=0.5, key="L2_T_Common")
            with col_l2b:
                if is_corner:
                    st.markdown("**L2 - Bottom Half**")
                    st.info("🚫 0.00 m (Corner)")
                    L2_b = 0.0
                else: L2_b = st.number_input("L2 - Bottom Half (m)", value=6.0, step=0.5, key=f"L2_B_{col_location}")

            # --- EDGE BEAM & CANTILEVER ---
            st.markdown("##### 🧱 Edge Condition")
            edge_beam_params = {"has_beam": False, "width_cm": 0.0, "depth_cm": 0.0}
            if not is_interior:
                has_edge_beam = st.checkbox("Has Edge Beam?", value=True)
                if has_edge_beam:
                    eb_c1, eb_c2 = st.columns(2)
                    with eb_c1: eb_w = st.number_input("Beam Width (cm)", value=30.0, step=5.0)
                    with eb_c2: eb_d = st.number_input("Beam Depth (cm)", value=50.0, step=5.0)
                    edge_beam_params = {"has_beam": True, "width_cm": eb_w, "depth_cm": eb_d}
                else: st.info("ℹ️ Unrestrained Edge (Flat Plate)")

            with st.expander("🏗️ Cantilever / Overhang", expanded=False):
                cant_c1, cant_c2 = st.columns(2)
                has_cant_left = False; L_cant_left = 0.0
                has_cant_right = False; L_cant_right = 0.0
                with cant_c1:
                    cant_l_disabled = (L1_l > 0.01) 
                    has_cant_left = st.checkbox("Left Cantilever", value=False, disabled=cant_l_disabled) 
                    if has_cant_left: L_cant_left = st.number_input("Left Length (m)", value=1.5, step=0.1)
                with cant_c2:
                    has_cant_right = st.checkbox("Right Cantilever", value=False)
                    if has_cant_right: L_cant_right = st.number_input("Right Length (m)", value=1.5, step=0.1)
                cant_params = {"has_left": has_cant_left, "L_left": L_cant_left, "has_right": has_cant_right, "L_right": L_cant_right}

            st.divider()

            # --- 3. Member Sizes ---
            st.subheader("3. Member Sizes")
            h_slab_cm = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0)
            
            col_sz1, col_sz2 = st.columns(2)
            with col_sz1: c1_cm = st.number_input("Column X-dir (c1) [cm]", value=50.0)
            with col_sz2: c2_cm = st.number_input("Column Y-dir (c2) [cm]", value=50.0)

            h_up = 0.0
            if not is_roof: h_up = st.number_input("Upper Storey Height (m)", value=3.0)
            h_lo = st.number_input("Lower Storey Height (m)", value=3.0)

            has_drop = st.checkbox("Include Drop Panel", value=False)
            h_drop_cm, drop_w1, drop_w2 = 0.0, 0.0, 0.0
            if has_drop:
                d_col1, d_col2, d_col3 = st.columns(3)
                with d_col1: h_drop_cm = st.number_input("Drop Depth (cm)", value=10.0)
                def_w1 = (L1_l + L1_r)/3.0 if is_interior else (L1_r/3.0) + (c1_cm/200.0)
                def_w2 = (L2_t + L2_b)/3.0 if not is_corner else (L2_t/3.0) + (c2_cm/200.0)
                with d_col2: drop_w1 = st.number_input("Drop Width W1 (m)", value=float(f"{def_w1:.2f}"))
                with d_col3: drop_w2 = st.number_input("Drop Width W2 (m)", value=float(f"{def_w2:.2f}"))

            # --- PROCESS DATA ---
            if 'SD30' in str(fy): fy_val = 3000
            elif 'SD40' in str(fy): fy_val = 4000
            else: fy_val = 5000

            calc_obj = app_calc.prepare_calculation_data(
                h_slab_cm, h_drop_cm, has_drop, c1_cm, c2_cm, drop_w1, drop_w2,
                col_location, L1_l, L1_r, L2_t, L2_b, fc, fy_val, dl, ll, auto_sw, lf_dl, lf_ll,
                joint_type, h_up, h_lo, far_end_up, far_end_lo, cant_params, edge_beam_params
            )

            if 'geom' not in calc_obj: calc_obj['geom'] = {}
            if 'loads' not in calc_obj: calc_obj['loads'] = {}
            if 'mat' not in calc_obj: calc_obj['mat'] = {}
            
            # ✅ คำนวณ L2 แบบ Equivalent Frame (เฉลี่ยระยะกึ่งกลางแผงบน-ล่าง)
            L2_eff = (L2_t / 2.0) + (L2_b / 2.0)

            # ✅ อัปเดตข้อมูลใส่ Dictionary
            calc_obj['geom'].update({
                'L1': max(L1_l, L1_r), 
                'L2': L2_eff, 
                'L2_t': L2_t, 
                'L2_b': L2_b, 
                'L1_l': L1_l, 
                'L1_r': L1_r, 
                'c1_cm': c1_cm, 
                'c2_cm': c2_cm, 
                'h_slab_cm': h_slab_cm, 
                'col_loc': col_location, 
                'has_drop': has_drop, 
                'h_drop_cm': h_drop_cm, 
                'drop_w1': drop_w1, 
                'drop_w2': drop_w2,
                'edge_beam': edge_beam_params
            })
            
            sw = (h_slab_cm / 100.0) * 2400 if auto_sw else 0
            calc_obj['loads'].update({'dl': dl, 'll': ll, 'wu': (lf_dl * (dl + sw)) + (lf_ll * ll)})
            calc_obj['mat'].update({'fc': fc, 'fy': fy_val})

            validator = app_calc.DesignCriteriaValidator(
                calc_obj['geom']['L1'], calc_obj['geom']['L2'], L1_l, L1_r, L2_t, L2_b,
                ll, dl, has_drop, cant_params, fy_val, col_location, h_slab_cm, (c1_cm/100), (c2_cm/100), edge_beam_params
            )
            thk_res = validator.check_min_thickness_detailed()
            ddm_ok, ddm_reasons = validator.check_ddm()

        # --------------------------------------------------------------------------
        # RIGHT COLUMN: VISUALIZATION 
        # --------------------------------------------------------------------------
        with col_viz:
            st.subheader(f"👁️ Visualization: {col_location} (Physical Plan)")
            v_tab1, v_tab2 = st.tabs(["📐 Plan View", "🔍 True-Scale Section (X-Axis)"])
            
            with v_tab1:
                fig_plan = app_viz.draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_location, has_drop, drop_w1, drop_w2, cant_params, edge_beam_params)
                st.pyplot(fig_plan)
            
            with v_tab2:
                fig_elev = app_viz.draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, is_roof, far_end_up, far_end_lo, cant_params, edge_beam_params)
                st.pyplot(fig_elev)

            st.divider()
            
            st.markdown("### 📋 Code Compliance & Calculations")
            
            st.markdown("#### 🔍 Method Applicability Check")
            actual_L1 = calc_obj['geom']['L1']
            actual_L2 = calc_obj['geom']['L2']
            ratio = actual_L2 / actual_L1 if actual_L1 > 0 else 0
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                if ddm_ok:
                    st.success(f"✅ **DDM (Direct Design Method)**\n\n**ผ่านเงื่อนไข ACI 318:**\n- สัดส่วน L2/L1 = {ratio:.2f}\n- น้ำหนักบรรทุกผ่านเกณฑ์")
                else:
                    st.error(f"❌ **DDM (Direct Design Method)**\n\n**ไม่ผ่านเงื่อนไข ACI 318:**")
                    for r in ddm_reasons:
                        st.write(f"- {r}")
                    st.caption(f"*(อ้างอิง: L1 = {actual_L1:.2f} m, L2 = {actual_L2:.2f} m, Ratio = {ratio:.2f})*")
                    
            with col_m2:
                st.info("✅ **EFM (Equivalent Frame Method)**\n\nสามารถใช้วิธีนี้ได้เสมอ")
                
            st.markdown("---")
            
            # 1. SLAB THICKNESS CALCULATION 
            if thk_res['status']:
                st.success(f"✅ **Slab Thickness OK** (Prov: {thk_res['actual_h']} cm >= Req: {thk_res['req_h']:.2f} cm)")
            else:
                st.error(f"❌ **Slab Thickness NOT OK** (Prov: {thk_res['actual_h']} cm < Req: {thk_res['req_h']:.2f} cm)")
                
            with st.expander("📝 Show Thickness Calculation (Detailed)", expanded=True):
                st.markdown(f"**Method:** ACI 318 Table 8.3.1.1")
                st.markdown(f"**Condition Case:** {thk_res['case_name']}")
                
                Ln_disp = thk_res['Ln']
                fy_disp = float(fy.replace('SD', '')) * 10 
                if 'SD30' in str(fy): fy_val = 3000
                elif 'SD40' in str(fy): fy_val = 4000
                else: fy_val = 5000
                
                st.latex(r"h_{min} = \frac{L_n (0.8 + \frac{f_y}{14000})}{N}")
                
                c1_cal, c2_cal = st.columns(2)
                with c1_cal:
                    st.write(f"- **Clear Span ($L_n$):** {Ln_disp:.3f} m")
                    st.write(f"- **Steel ($f_y$):** {fy_val} ksc")
                with c2_cal:
                    st.write(f"- **Minimum Req ($h_{{req}}$):** {thk_res['req_h']:.2f} cm")
                    st.write(f"- **Actual Slab ($h_{{slab}}$):** {h_slab_cm} cm")

                st.markdown("**Calculation Substitution:**")
                term_fy = 0.8 + (fy_val / 14000) 
                
                st.info(f"""
                $$ h_{{req}} = {thk_res['req_h']:.2f} \\text{{ cm}} $$
                
                Checking: $ {h_slab_cm} \\ge {thk_res['req_h']:.2f} $
                """)

            # 2. DROP PANEL CALCULATION 
            if has_drop:
                drop_res = validator.check_drop_panel_detailed(h_drop_cm, drop_w1, drop_w2)
                st.markdown("#### 📉 Drop Panel Checks")
                
                dp_c1, dp_c2, dp_c3 = st.columns(3)
                def status_mark(passed): return "✅" if passed else "❌"
                
                with dp_c1:
                    st.metric("Projection", f"{drop_res['act_proj']} cm", 
                              f"Min: {drop_res['req_proj']:.2f} cm {status_mark(drop_res['chk_depth'])}")
                with dp_c2:
                    st.metric("Width (W1)", f"{drop_res['act_w1']:.2f} m", 
                              f"Min: {drop_res['req_total_w1']:.2f} m {status_mark(drop_res['chk_w1'])}")
                with dp_c3:
                    st.metric("Width (W2)", f"{drop_res['act_w2']:.2f} m", 
                              f"Min: {drop_res['req_total_w2']:.2f} m {status_mark(drop_res['chk_w2'])}")
                
                with st.expander("📝 Drop Panel Calculation Details (Full)", expanded=True):
                    st.markdown("##### 1. Depth Check (ความหนา)")
                    st.markdown("Requirement: Drop panel projection below slab must be at least $h_s/4$.")
                    
                    st.latex(r"\text{Req Depth } (d_{drop}) \ge \frac{h_{slab}}{4}")
                    
                    req_proj_val = h_slab_cm / 4.0
                    st.latex(r"d_{drop} \ge \frac{" + f"{h_slab_cm}" + r"}{4} = " + f"{req_proj_val:.2f}" + r" \text{ cm}")
                    
                    chk_sym = "\ge" if h_drop_cm >= req_proj_val else "<"
                    st.latex(f"\\text{{Provided }} {h_drop_cm} \\text{{ cm }} {chk_sym} {req_proj_val:.2f} \\text{{ cm}}")
                    
                    if h_drop_cm >= req_proj_val:
                        st.success(f"✅ Depth Satisfied: {h_drop_cm} cm provided.")
                    else:
                        st.error(f"❌ Depth Insufficient: Need at least {req_proj_val:.2f} cm.")

                    st.markdown("---")
                    st.markdown("##### 2. Width Check (ความกว้าง)")
                    st.markdown("Requirement: Drop panel must extend $\ge L/6$ from center line in each direction (Total $\ge L/3$).")
                    
                    st.latex(r"\text{Req Width } (W) \ge \frac{L_{span}}{3}")
                    
                    st.markdown("**Direction 1 (L1 Analysis):**")
                    req_w1 = drop_res['req_total_w1']
                    st.latex(r"W_{1,req} = \frac{L_1}{3} = " + f"{req_w1:.2f} \\text{{ m}}")
                    st.write(f"Provided $W_1$ = {drop_w1:.2f} m")
                    if drop_res['chk_w1']: st.success("✅ W1 OK") 
                    else: st.error("❌ W1 Too Narrow")
                    
                    st.markdown("**Direction 2 (L2 Transverse):**")
                    req_w2 = drop_res['req_total_w2']
                    st.latex(r"W_{2,req} = \frac{L_2}{3} = " + f"{req_w2:.2f} \\text{{ m}}")
                    st.write(f"Provided $W_2$ = {drop_w2:.2f} m")
                    if drop_res['chk_w2']: st.success("✅ W2 OK") 
                    else: st.error("❌ W2 Too Narrow")

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
# TABS 2-4: THEORY & METHODS
# ==============================================================================
with tab2:
    app_theory.display_theory(calc_obj)

import copy

with tab3:
    if ddm_ok:
        st.header("Direct Design Method (DDM) Analysis")
        
        # ==========================================================
        # 🔄 เลือกทิศทาง Frame Analysis
        # ==========================================================
        st.markdown("### 🔄 Select Analysis Frame")
        st.info("เลือกทิศทางของ Equivalent Frame ที่ต้องการคำนวณโมเมนต์และเหล็กเสริม")
        
        analysis_dir = st.radio(
            "Analysis Direction:",
            ["X-Axis Frame (วิเคราะห์ตามแนว L1 เดิม)", "Y-Axis Frame (วิเคราะห์ตามแนว L2 เดิม)"],
            horizontal=True,
            key="ddm_analysis_dir"
        )
        
        st.divider()

        # สร้างตัวโคลนของ calc_obj เพื่อไม่ให้กระทบ Physical Model ใน Tab อื่น
        ddm_calc_obj = copy.deepcopy(calc_obj)
        
        # โลจิกสลับแกน: ถ้าเลือก Y-Axis ให้เอาค่าแกน Y มาสวมทับแกน X ของ DDM
        if "Y-Axis" in analysis_dir:
            # สลับความยาว Span (Frame รวม)
            ddm_calc_obj['geom']['L1'] = calc_obj['geom']['L2']
            ddm_calc_obj['geom']['L2'] = calc_obj['geom']['L1']
            
            # ✅ สลับความยาวแผงย่อย เพื่อคำนวณ Column Strip ฝั่งบน/ล่าง (ที่กลายเป็นซ้าย/ขวา)
            ddm_calc_obj['geom']['L2_t'] = calc_obj['geom']['L1_l']
            ddm_calc_obj['geom']['L2_b'] = calc_obj['geom']['L1_r']
            ddm_calc_obj['geom']['L1_l'] = calc_obj['geom']['L2_t']
            ddm_calc_obj['geom']['L1_r'] = calc_obj['geom']['L2_b']
            
            # สลับขนาดเสา
            ddm_calc_obj['geom']['c1_cm'] = calc_obj['geom']['c2_cm']
            ddm_calc_obj['geom']['c2_cm'] = calc_obj['geom']['c1_cm']
            
            # ถ้ามี Drop Panel ต้องสลับความกว้าง Drop ด้วย
            if ddm_calc_obj['geom'].get('has_drop'):
                if 'drop_w1' in ddm_calc_obj['geom'] and 'drop_w2' in ddm_calc_obj['geom']:
                    ddm_calc_obj['geom']['drop_w1'] = calc_obj['geom']['drop_w2']
                    ddm_calc_obj['geom']['drop_w2'] = calc_obj['geom']['drop_w1']
            
            st.success("🔄 **Y-Axis Frame Active:** โปรแกรมได้สลับค่า L และขนาดหน้าตัดเสา c สำหรับการคำนวณในแนวขวางเรียบร้อยแล้ว")
        else:
            st.success("➡️ **X-Axis Frame Active:** คำนวณ Frame ตามแนวยาวปกติ")

        # ==========================================================
        # ส่ง Object ที่จัดการทิศทางเรียบร้อยแล้ว เข้าไป Render DDM
        # ==========================================================
        app_ddm.render_ddm_tab(ddm_calc_obj) 
        
    else:
        st.error("❌ This structure DOES NOT meet DDM criteria.")
        for r in ddm_reasons: 
            st.write(f"- {r}")

with tab4:
    st.header("📐 Equivalent Frame Method (EFM)")
    st.info("✅ EFM is valid.")
    st.info("Module `app_efm` ready.")
