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
        fc_ksc = mat.get('fc_pa', 240 * KSC_TO_PA) / KSC_TO_PA
        fy_ksc = mat.get('fy_pa', 4000 * KSC_TO_PA) / KSC_TO_PA
        fc = fc_ksc
        fy = fy_ksc

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
    
    c1_col, c2_col, c3_col = st.columns(3)
    c1_col.metric("Design Load (Wu)", f"{wu:,.0f} kg/m²")
    c2_col.metric("Total Static Moment (Mo)", f"{Mo:,.0f} kg-m")
    c3_col.metric("Load Ratio (LL ≤ 2 DL)", "Pass" if ll <= 2*dl else "Fail")

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
                "As Req (cm²)": st.column_config.NumberColumn("Required Area (cm²)", disabled=True, format="%.2f"),
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

        edited_df[['Width (m)', 'Total Bars', 'Max Allowable Spacing (cm)', 'As Provided (cm²)', 'Status']] = edited_df.apply(lambda r: compute_results(r, df_design), axis=1)

        if "❌ FAIL" in edited_df['Status'].values:
            st.error("⚠️ **Overall Status:** Some sections do NOT have enough reinforcement. Please reduce spacing or increase bar size.")
        else:
            st.success("🎉 **Overall Status:** All sections PASSED! The design is safe.")

        display_cols = ['Location', 'Bar Size (mm)', 'Spacing (cm)', 'Total Bars', 'As Req (cm²)', 'As Provided (cm²)', 'Status']
        def highlight_status(val):
            return f"color: {'#ff4b4b' if 'FAIL' in str(val) else '#21c354'}; font-weight: bold;"
            
        styled_df = edited_df[display_cols].style.map(highlight_status, subset=['Status']).format({
            'As Req (cm²)': "{:.2f}", 'As Provided (cm²)': "{:.2f}", 'Total Bars': "{:.0f}"
        })
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # ==========================================================================
    # STEP 5: COMPREHENSIVE CALCULATION NOTE (ACI 318)
    # ==========================================================================
    st.markdown("---")
    st.markdown("### 📑 รายการคำนวณโดยละเอียด (Detailed Calculation Report)")
    st.caption("อ้างอิงข้อกำหนดตามมาตรฐาน ACI 318-19 (Building Code Requirements for Structural Concrete)")

    tab_limit, tab_load, tab_moment, tab_design, tab_shear = st.tabs([
        "📏 1. ข้อกำหนด DDM", 
        "⚖️ 2. น้ำหนักบรรทุกประลัย", 
        "📈 3. โมเมนต์สถิตยศาสตร์", 
        "⚙️ 4. ออกแบบเหล็กเสริม", 
        "🛡️ 5. แรงเฉือนทะลุ"
    ])

    # --- TAB 1: Limitations ---
    with tab_limit:
        st.markdown("**ACI 318 Section 8.10.2: ข้อจำกัดสำหรับการใช้วิธี Direct Design Method**")
        st.markdown(f"- **Span Ratio (อัตราส่วนด้านยาวต่อด้านสั้น):** $L_1 / L_2 = {max(L1, L2) / min(L1, L2):.2f}$")
        st.markdown(f"  - *เงื่อนไข:* ต้องไม่เกิน 2.0 ➡️ **{'✅ ผ่าน' if (max(L1, L2)/min(L1, L2)) <= 2.0 else '❌ ไม่ผ่าน'}**")
        
        st.markdown(f"- **Load Ratio (อัตราส่วนน้ำหนักบรรทุก):** $LL / DL = {ll / dl:.2f}$")
        st.markdown(f"  - *เงื่อนไข:* Live Load ต้องไม่เกิน 2 เท่าของ Dead Load ($LL \le 2 DL$) ➡️ **{'✅ ผ่าน' if ll <= 2*dl else '❌ ไม่ผ่าน'}**")
        
        st.markdown(f"- **Clear Span ($L_n$):** $\max(L_1 - c_1, 0.65L_1) = {ln:.2f}$ m")
        st.markdown("  - *เงื่อนไข:* ระยะเคลียร์สแปนต้องไม่น้อยกว่า 65% ของระยะสแปนอ้างอิง")

    # --- TAB 2: Loads ---
    with tab_load:
        st.markdown("**ACI 318 Chapter 5: Loads & Load Combinations**")
        st.markdown("การคำนวณน้ำหนักบรรทุกประลัย (Factored Load) ที่กระทำลงบนพื้น")
        st.latex(r"W_u = 1.4 DL + 1.7 LL")
        st.markdown(f"โดยที่:")
        st.markdown(f"- $DL = {dl:,.0f}$ kg/m² (น้ำหนักบรรทุกคงที่ รวมน้ำหนักพื้น)")
        st.markdown(f"- $LL = {ll:,.0f}$ kg/m² (น้ำหนักบรรทุกจร)")
        st.latex(rf"W_u = 1.4({dl:,.0f}) + 1.7({ll:,.0f}) = {wu:,.0f} \text{{ kg/m}}^2")

    # --- TAB 3: Moments ---
    with tab_moment:
        st.markdown("**ACI 318 Section 8.10.3: Total Factored Static Moment ($M_o$)**")
        st.markdown("คำนวณค่าโมเมนต์สถิตยศาสตร์รวมทั้งหมดใน 1 สแปน")
        st.latex(r"M_o = \frac{W_u \ell_2 \ell_n^2}{8}")
        st.latex(rf"M_o = \frac{{({wu:,.0f})({L2:.2f})({ln:.2f})^2}}{{8}} = {Mo:,.0f} \text{{ kg-m}}")
        
        st.divider()
        st.markdown("**ACI 318 Section 8.10.4 & 8.10.5: Moment Distribution**")
        st.markdown("สัดส่วนการกระจายโมเมนต์ตามยาว (Longitudinal) และตามขวาง (Transverse) เข้าสู่ Column Strip และ Middle Strip")
        
        if details.get('Mo_step'): 
            st.info("💡 ตัวแปรที่ใช้ในการกระจายโมเมนต์ (Torsional Constant & Alpha)")
            st.latex(details['Mo_step'])
        if details.get('beta_t_step'): 
            st.latex(details['beta_t_step'])

    # --- TAB 4: Flexural Design ---
    with tab_design:
        st.markdown("**ACI 318 Chapter 22: Sectional Strength (Flexure)**")
        st.markdown("การคำนวณปริมาณเหล็กเสริมในแต่ละหน้าตัด อาศัยหลักการ Ultimate Strength Design (USD):")
        
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        st.latex(r"\rho = \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right)")
        st.latex(r"A_{s,req} = \rho b d \ge A_{s,min}")
        
        st.markdown("โดยมีข้อกำหนดเพิ่มเติมดังนี้:")
        st.markdown("- Strength Reduction Factor (ดัด), $\phi = 0.90$")
        st.markdown(f"- Minimum Reinforcement Area, $A_{{s,min}} = 0.0018 b h$")
        st.markdown("- ระยะแอดเหล็กสูงสุด (Max Spacing) $\le 2h$ หรือไม่เกิน 45 ซม.")

    # --- TAB 5: Punching Shear ---
    with tab_shear:
        st.markdown("**ACI 318 Section 22.6: Two-Way Shear (Punching Shear) Strength**")
        st.markdown("ตรวจสอบแรงเฉือนทะลุที่ระยะวิกฤต $d/2$ จากขอบเสา (Critical Section)")
        
        if details.get('punch_step'):
            st.latex(rf"\begin{{aligned}} {details['punch_step']} \end{{aligned}}")
        else:
            st.latex(r"V_u \le \phi V_c")
            st.latex(r"\phi V_c = \phi \cdot 0.33 \sqrt{f'_c} b_o d")
            st.markdown("*(หมายเหตุ: ต้องคำนวณค่า $V_u$ จากปฏิกิริยาเสาและหักลบน้ำหนักพื้นภายในพื้นที่ $b_o$)*")
            
        punch_status = details.get('punch_status', 'N/A')
        if 'Safe' in punch_status or 'Pass' in punch_status:
            st.success(f"**สถานะแรงเฉือนทะลุ:** {punch_status} ✅")
        elif 'Fail' in punch_status:
            st.error(f"**สถานะแรงเฉือนทะลุ:** {punch_status} ❌ (จำเป็นต้องเพิ่ม Drop Panel หรือ Shear Reinforcement)")
        else:
            st.info("สถานะแรงเฉือนทะลุ: รอการคำนวณจากโมดูลหลัก (calc_ddm)")
