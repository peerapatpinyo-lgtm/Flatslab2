# app_ddm.py
import streamlit as st
import pandas as pd
import math
import calc_ddm
import viz_ddm

def translate_warnings(msg):
    """Intercepts and translates Thai messages from the backend calc_ddm file."""
    msg = str(msg)
    translations = {
        "การแอ่นตัว:": "Deflection Limit:",
        "ความหนาพื้น": "Slab thickness",
        "น้อยกว่าค่า ACI แนะนำ": "is less than the ACI recommended minimum",
        "ทะลุรอบหัวเสา:": "Punching Shear:",
        "ไม่ปลอดภัย": "Unsafe",
        "ปลอดภัย": "Safe"
    }
    for th, en in translations.items():
        msg = msg.replace(th, en)
    return msg

from calc_ddm import calculate_ddm

def render_ddm_tab(calc_obj):
    # =========================================================================
    # 🌟 1. ดึงข้อมูลพื้นฐานอย่างปลอดภัย (กัน KeyError และค่าเป็น 0)
    # =========================================================================
    raw_loc = calc_obj.get('col_location_raw', 'Interior Column')
    col_loc = str(raw_loc).replace(" Column", "") 
    
    # ✅ แก้ไขแล้ว: ดึงตัวเลข fy มาใช้ได้เลย
    fy_val = calc_obj.get('mat', {}).get('fy', 4000)

    loads_data = calc_obj.get('loads', {})
    dl = loads_data.get('dl', loads_data.get('DL', 0))
    ll = loads_data.get('ll', loads_data.get('LL', 0))
    # ... โค้ดส่วนอื่นๆ คงเดิม ...

    wu = loads_data.get('wu', (1.4 * dl) + (1.7 * ll))

    geom_data = calc_obj.get('geom', {})
    
    L1 = geom_data.get('L1', 0)
    L2 = geom_data.get('L2', 0)
    c1_cm = geom_data.get('c1_cm', 50)
    c2_cm = geom_data.get('c2_cm', 50)
    
    c1_m = c1_cm / 100.0
    c2_m = c2_cm / 100.0
    
    # 🌟 คำนวณ Clear Span (ln) ตรงนี้เลย เพื่อส่งเข้า inputs ทันที
    ln = max(L1 - c1_m, 0.65 * L1) if L1 > 0 else 0

    h_slab_cm = geom_data.get('h_slab_cm', geom_data.get('h_s', 0.20) * 100.0)
    has_drop = geom_data.get('has_drop', False)
    h_drop_cm = geom_data.get('h_drop_cm', h_slab_cm) if has_drop else h_slab_cm

    eb_data = geom_data.get('edge_beam', {})

    # =========================================================================
    # 🌟 2. แพ็กข้อมูล inputs (รับรองว่า calculate_ddm หาเจอทุกตัวแปร)
    # =========================================================================
    inputs = {
        'l1': L1, 'L1': L1,
        'l2': L2, 'L2': L2,
        'ln': ln,                # ✅ ส่ง ln เข้าไปแล้ว
        'wu': wu,
        'c1': c1_m, 
        'c2': c2_m,
        'c1_cm': c1_cm,
        'c2_cm': c2_cm,
        'h_slab': h_slab_cm,     # ✅ ส่ง h_slab เข้าไปแล้ว
        'h_slab_cm': h_slab_cm,
        'has_drop': has_drop,
        'h_drop': h_drop_cm,
        'fc': calc_obj.get('mat', {}).get('fc', 280),
        'fy': fy_val,
        'col_location': col_loc,
        'col_loc': col_loc,
        'case_type': "Interior" if col_loc == "Interior" else "Exterior",
        'has_edge_beam': eb_data.get('has_beam', False),
        'edge_beam': eb_data,
        'eb_width': eb_data.get('width_cm', 0) / 100.0,
        'eb_depth': eb_data.get('depth_cm', 0) / 100.0,
    }

    # ==========================================================
    # 🚨 DEBUG ZONE (ใส่ # ไว้ให้ ถ้ามีปัญหาค่อยเอา # ออกเพื่อดูค่า)
    # ==========================================================
    # st.error("🚨 ตรวจสอบข้อมูล inputs ที่จะส่งไปคำนวณ")
    # st.json(inputs)
    # ==========================================================

    # =========================================================================
    # 🌟 3. เรียกคำนวณ 
    # =========================================================================
    df_res, Mo, msgs, details = calculate_ddm(inputs)
    
    # =========================================================================
    # 🌟 4. MASTER VARIABLE BRIDGE (กระจายตัวแปรให้ UI ด้านล่างใช้)
    # =========================================================================
    df_results = df_res     
    df_design = df_res      
    warning_msgs = msgs 

    c1 = inputs['c1']
    c2 = inputs['c2']

    h_slab_m = h_slab_cm / 100.0
    cc_m = geom_data.get('cc_cm', geom_data.get('covering', 3.0)) / 100.0
    selected_rebar = geom_data.get('rebar', 12.0) 
    d_eff_m = h_slab_m - cc_m - ((selected_rebar / 1000.0) / 2.0)
    
    cs_width = min(L1/2, L2/2) 
    
    fc_ksc = inputs['fc']
    fy_ksc = inputs['fy']
    has_edge_beam = inputs['has_edge_beam']
    case_type = inputs['case_type']

    # =========================================================================
    # 🌟 5. โค้ดส่วนแสดงผล UI (Step 3 ต่อด้วย Step 4 ของคุณ)
    # =========================================================================
    st.markdown("### Step 3: Forces & Constraints")
    
    c1_col, c2_col, c3_col = st.columns(3)
    c1_col.metric("Factored Load (Wu)", f"{wu:,.0f} kg/m²")
    c2_col.metric("Total Static Moment (Mo)", f"{Mo:,.0f} kg-m")
    c3_col.metric("Effective Depth (d)", f"{d_eff_m*100:.1f} cm")

    if warning_msgs:
        for msg in warning_msgs: 
            clean_msg = translate_warnings(msg) if 'translate_warnings' in globals() else msg
            st.warning(clean_msg) if " > " not in clean_msg else st.error(clean_msg)

    st.divider()

    # **********************************************
    # (วางโค้ดสร้าง Tabs และ DataFrame ต่อจากตรงนี้ได้เลยครับ)
    # **********************************************

    # **********************************************
    # โค้ดส่วนนี้คือจุดที่คุณสร้าง edited_df หรือ Tab 1, 2, 3, 4, 5
    # (วางโค้ดของคุณต่อจากตรงนี้ได้เลย)
    # **********************************************

    # ==========================================================================
    # STEP 4: INTERACTIVE DETAILING
    # ==========================================================================
    st.markdown("### Step 4: Reinforcement Detailing & Compliance")
    
    if not df_results.empty and 'Location' in df_results.columns:
        cs_width = min(L1, L2) / 2.0
        ms_width = L2 - cs_width

        def get_strip_width(loc):
            return cs_width if 'col' in str(loc).lower() else ms_width

        df_design = df_results.copy()
        df_design['Strip Width (m)'] = df_design['Location'].apply(get_strip_width)
        df_design['Bar Size (mm)'] = selected_rebar
        default_spacing = 20.0
        df_design['Spacing (cm)'] = default_spacing

        # Normalize column names 
        if 'As Req (cm²)' in df_design.columns:
            df_design.rename(columns={'As Req (cm²)': 'As Req (cm2)'}, inplace=True)
        if 'Mu (kg-m)' not in df_design.columns and 'Moment (kg-m)' in df_design.columns:
            df_design.rename(columns={'Moment (kg-m)': 'Mu (kg-m)'}, inplace=True)

        editor_cols = ['Location', 'As Req (cm2)', 'Bar Size (mm)', 'Spacing (cm)']
        
        edited_df = st.data_editor(
            df_design[editor_cols],
            column_config={
                "Location": st.column_config.TextColumn("Strip Location", disabled=True),
                "As Req (cm2)": st.column_config.NumberColumn("Req. Area (cm²)", disabled=True, format="%.2f"),
                "Bar Size (mm)": st.column_config.SelectboxColumn("Bar Size (mm)", options=[10, 12, 16, 20, 25]),
                "Spacing (cm)": st.column_config.NumberColumn("Spacing (cm)", min_value=2.5, max_value=45.0, step=2.5),
            },
            use_container_width=True, hide_index=True, key="rebar_editor"
        )

        def compute_results(row, original_df):
            width_m = original_df.loc[original_df['Location'] == row['Location'], 'Strip Width (m)'].values[0]
            bar_area = math.pi * (row['Bar Size (mm)'] / 10.0)**2 / 4.0
            as_req = row['As Req (cm2)']
            
            spacing = row['Spacing (cm)'] if row['Spacing (cm)'] > 0 else 1.0
            as_prov = bar_area * ((width_m * 100.0) / spacing)
            num_bars = math.ceil((width_m * 100.0) / spacing)
            
            max_spacing_aci = min(2 * h_slab_m * 100, 45.0)
            status = "PASS" if (as_prov >= as_req and spacing <= max_spacing_aci) else "FAIL"
            return pd.Series([width_m, num_bars, max_spacing_aci, as_prov, status])

        edited_df[['Width (m)', 'Total Bars', 'Max Spacing (cm)', 'Prov. Area (cm2)', 'Status']] = edited_df.apply(lambda r: compute_results(r, df_design), axis=1)

        if "FAIL" in edited_df['Status'].values:
            st.error("Overall Status: FAIL. Ensure provided area exceeds required area AND spacing complies with ACI limits.")
        else:
            st.success("Overall Status: PASS. Reinforcement is structurally adequate per ACI 318 spacing limits.")

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

    tab_limit, tab_load, tab_dist, tab_flex, tab_shear = st.tabs([
        "1. Geometry Limits", 
        "2. Loads & Moments", 
        "3. Distribution Factors",
        "4. Flexural Detailing", 
        "5. Punching Shear",
        "6. Drawings & Details"
    ])

    # --- TAB 1: Limitations ---
    with tab_limit:
        st.markdown("#### ACI 318 Section 8.10.2: Dimensional Criteria for DDM")
        st.markdown(f"$$ \\text{{Span Aspect Ratio}} = \\frac{{\\max(L_1, L_2)}}{{\\min(L_1, L_2)}} \\le 2.0 $$")
        span_ratio_val = max(L1, L2) / min(L1, L2)
        st.markdown(f"**Result:** Ratio = {max(L1, L2):.2f} / {min(L1, L2):.2f} = **{span_ratio_val:.2f}**")
        
        st.divider()
        st.markdown(f"$$ \\text{{Loading Ratio}} = \\frac{{LL}}{{DL}} \\le 2.0 $$")
        load_ratio_val = ll / dl if dl > 0 else 0
        st.markdown(f"**Result:** Ratio = {ll:.0f} / {dl:.0f} = **{load_ratio_val:.2f}**")

        st.divider()
        st.markdown(f"$$ L_n = \\max(L_1 - c_1, \\ 0.65 L_1) $$")
        st.markdown(f"**Result:** $L_n = \\max({L1:.2f} - {c1:.2f}, 0.65 \\times {L1:.2f}) =$ **{ln:.2f}** m")

    # --- TAB 2: Loads & Moments ---
    with tab_load:
        st.markdown("#### ACI 318 Section 5.3.1: Load Combinations")
        st.markdown(f"$$ W_u = 1.4 DL + 1.7 LL $$")
        st.markdown(f"**Result:** $W_u = 1.4({dl:,.0f}) + 1.7({ll:,.0f}) =$ **{wu:,.0f}** kg/m²")

        st.divider()
        st.markdown("#### ACI 318 Section 8.10.3.2: Total Factored Static Moment")
        st.markdown(f"$$ M_o = \\frac{{W_u \\times L_2 \\times L_n^2}}{{8}} $$")
        # FIXED: \\times used properly to prevent the \t string bug
        st.markdown(f"**Result:** $M_o = \\frac{{{wu:,.0f} \\times {L2:.2f} \\times {ln:.2f}^2}}{{8}} =$ **{Mo:,.0f}** kg-m")

    # --- TAB 3: Distribution Factors (NEW TAB) ---
    with tab_dist:
        st.markdown("#### ACI 318 Section 8.10: Distribution of Factored Moments")
        st.markdown("The Direct Design Method allocates the total static moment ($M_o$) based on empirical tables from the ACI code.")
        
        st.markdown("##### 1. Longitudinal Distribution (ACI 318 Section 8.10.4)")
        st.markdown("Distribution of $M_o$ into Negative and Positive moments based on span position:")
        dist_data = {
            "Span Type": ["Interior Span", "Exterior Span (Flat Slab with Edge Beam)", "Exterior Span (Flat Slab without Edge Beam)"],
            "Interior Negative Moment": ["0.65 $M_o$", "0.70 $M_o$", "0.70 $M_o$"],
            "Positive Moment": ["0.35 $M_o$", "0.50 $M_o$", "0.52 $M_o$"],
            "Exterior Negative Moment": ["N/A", "0.30 $M_o$", "0.26 $M_o$"]
        }
        st.table(pd.DataFrame(dist_data))

        st.markdown("##### 2. Transverse Distribution (ACI 318 Section 8.10.5)")
        st.markdown("Distribution of longitudinal moments into Column Strip (CS) and Middle Strip (MS):")
        trans_data = {
            "Moment Type": ["Interior Negative", "Exterior Negative (with Edge Beam)", "Exterior Negative (no Edge Beam)", "Positive"],
            "Column Strip (CS) %": ["75%", "75% - 90% (depends on stiffness)", "100%", "60%"],
            "Middle Strip (MS) %": ["25%", "25% - 10%", "0%", "40%"]
        }
        st.table(pd.DataFrame(trans_data))
        st.info("*Note: The system backend (`calc_ddm.py`) automatically interpolates exact percentages dynamically based on actual span ratios ($L_2/L_1$) and torsional stiffness per ACI 318.*")

    # --- TAB 4: Flexural Design (ALL SECTIONS) ---

    with tab_flex:
        st.markdown("#### ACI 318 Section 22.2: Flexural Reinforcement Required")
        st.markdown("Calculations for **every strip** based on the equivalent rectangular concrete stress block. ($\\phi = 0.90$)")
        
        st.info("💡 **Concept:** $M_u = M_o \\times \\text{Longitudinal Factor} \\times \\text{Transverse Factor}$")
        
        st.markdown("**General Formulas:**")
        st.markdown(f"$$ M_u = \\text{{Net Distribution Factor}} \\times M_o $$")
        st.markdown(f"$$ R_n = \\frac{{M_u}}{{\\phi \\times b \\times d^2}} $$")
        st.markdown(f"$$ \\rho = \\frac{{0.85 f'_c}}{{f_y}} \\left( 1 - \\sqrt{{1 - \\frac{{2 R_n}}{{0.85 f'_c}}}} \\right) $$")
        
        rho_min = 0.0020 if fy_ksc < 4000 else 0.0018
        st.markdown("**ACI 24.4.3.2 Minimum Shrinkage and Temperature Steel:**")
        st.markdown(f"$$ \\rho_{{min}} = {rho_min} \\quad \\rightarrow \\quad A_{{s,min}} = \\rho_{{min}} \\times b \\times h_{{slab}} $$")
        st.divider()
        
        if not df_results.empty and 'Location' in df_results.columns:
            phi_flex = 0.90
            
            for index, row in edited_df.iterrows():
                loc_name = row['Location']
                bar_size = row['Bar Size (mm)']
                spacing_cm = row['Spacing (cm)']
                
                # Robustly extract Mu from the backend dataframe
                match_row = df_design[df_design['Location'] == loc_name].iloc[0]
                mu_val = match_row.get('Mu (kg-m)', match_row.get('Moment (kg-m)', 0))
                
                # Calculate distribution percentage from Mo
                net_factor = (mu_val / Mo) if Mo > 0 else 0
                dist_factor = net_factor * 100
                
                b_width_m = row['Width (m)']
                b_width_cm = b_width_m * 100.0 
                d_eff_cm = d_eff_m * 100.0
                
                # Active Calculation of Rn and Rho
                if b_width_cm > 0 and d_eff_cm > 0:
                    rn_calc = (mu_val * 100.0) / (phi_flex * b_width_cm * (d_eff_cm**2))
                    radicand = 1.0 - (2.0 * rn_calc) / (0.85 * fc_ksc)
                    
                    if radicand < 0:
                        rho_calc = 0  # Section fails, handle safely
                        st.error(f"Section {loc_name} is over-reinforced. Increase depth.")
                    else:
                        rho_calc = (0.85 * fc_ksc / fy_ksc) * (1.0 - math.sqrt(max(0, radicand)))
                else:
                    rn_calc, rho_calc = 0, 0
                    
                as_calc = rho_calc * b_width_cm * d_eff_cm
                as_min = rho_min * b_width_cm * (h_slab_m * 100.0)
                as_req_final = max(as_calc, as_min)
                
                # Actual Provided Reinforcement Calculation
                bar_dia_cm = bar_size / 10.0
                a_bar = math.pi * (bar_dia_cm**2) / 4.0
                as_prov = a_bar * b_width_cm / spacing_cm
                
                st.markdown(f"#### 📍 Section: `{loc_name}`")
                

                # --- NEW: Moment Distribution Breakdown ---
                st.markdown("**🔍 Moment Distribution Breakdown:**")
                is_col_strip = 'Col' in loc_name
                
                # 1. เช็คว่าเป็นช่วงภายใน (Interior Span) หรือช่วงภายนอก (Exterior Span)
                is_interior_span = "Ext:" not in loc_name
                
                # 2. หาค่า Longitudinal Factor (long_f) ให้ตรงกับ Backend
                if is_interior_span:
                    long_f = 0.65 if "Neg" in loc_name else 0.35
                else: # Exterior Span
                    if "Int Neg" in loc_name:
                        long_f = 0.70 # (ค่า default พื้นฐานอิงตาม Slab with/without edge beam)
                    elif "Ext Neg" in loc_name:
                        long_f = 0.30 if has_edge_beam else 0.26
                    else: # Pos
                        long_f = 0.50 if has_edge_beam else 0.52
                
                # ป้องกัน division by zero
                trans_f = net_factor / long_f if long_f > 0 else 0
                
                st.markdown(f"- **Longitudinal Factor:** {long_f:.3f} (ACI 8.10.4)")
                st.markdown(f"- **Transverse Factor:** {trans_f:.3f} (ACI 8.10.5 - to {'Column Strip' if is_col_strip else 'Middle Strip'})")
                st.markdown(f"- **Net Multiplier:** ${long_f:.3f} \\times {trans_f:.3f} = {net_factor:.4f}$")

                
                # --- EXPLICIT SOURCE OF b AND d ---
                st.markdown("**📌 Parameter Sources:**")
                
                if is_col_strip:
                    st.markdown("- **Strip Width ($b$):** Based on **Column Strip** geometry")
                    st.markdown(f"$$ b = \\min(0.5 L_1, 0.5 L_2) = \\min(0.5 \\times {L1:.2f}, 0.5 \\times {L2:.2f}) = {b_width_m:.2f} \\text{{ m}} = {b_width_cm:.1f} \\text{{ cm}} $$")
                else:
                    st.markdown("- **Strip Width ($b$):** Based on **Middle Strip** geometry")
                    st.markdown(f"$$ b = L_2 - b_{{cs}} = {L2:.2f} - {cs_width:.2f} = {b_width_m:.2f} \\text{{ m}} = {b_width_cm:.1f} \\text{{ cm}} $$")
                    
                st.markdown("- **Effective Depth ($d$):**")
                st.markdown(f"$$ d = h_{{slab}} - \\text{{Cover}} - \\frac{{d_b}}{{2}} = {h_slab_m*100:.1f} - {cc_m*100:.1f} - \\frac{{{selected_rebar/10:.1f}}}{{2}} = {d_eff_cm:.2f} \\text{{ cm}} $$")
                st.write("") # Spacer

                # --- PART 1: Required Steel ---
                st.markdown("##### 1. Required Steel Calculation ($A_{s,req}$)")
                st.markdown(f"$$ M_u = {net_factor:.4f} \\times M_o = {net_factor:.4f} \\times {Mo:,.0f} = {mu_val:,.0f} \\text{{ kg-m}} $$")
                st.markdown(f"$$ R_n = \\frac{{{mu_val:,.0f} \\times 100}}{{{phi_flex} \\times {b_width_cm:.1f} \\times {d_eff_cm:.2f}^2}} = {rn_calc:.2f} \\text{{ kg/cm}}^2 $$")
                st.markdown(f"$$ \\rho_{{calc}} = \\frac{{0.85 \\times {fc_ksc:.0f}}}{{{fy_ksc:.0f}}} \\left( 1 - \\sqrt{{1 - \\frac{{2 \\times {rn_calc:.2f}}}{{0.85 \\times {fc_ksc:.0f}}}}} \\right) = {rho_calc:.5f} $$")
                st.markdown(f"$$ A_{{s,calc}} = {rho_calc:.5f} \\times {b_width_cm:.1f} \\times {d_eff_cm:.2f} = {as_calc:.2f} \\text{{ cm}}^2 $$")
                st.markdown(f"$$ A_{{s,min}} = {rho_min} \\times {b_width_cm:.1f} \\times {h_slab_m*100.0:.1f} = {as_min:.2f} \\text{{ cm}}^2 $$")
                st.markdown(f"$$ A_{{s,req}} = \\max(A_{{s,calc}}, A_{{s,min}}) = {as_req_final:.2f} \\text{{ cm}}^2 $$")

                st.write("") # Spacer
                
                # --- PART 2: Provided Steel ---
                st.markdown("##### 2. Provided Steel Verification ($A_{s,prov}$)")
                st.info(f"**Selected Reinforcement in Table:** DB{bar_size} @ {spacing_cm:.1f} cm")
                st.markdown(f"$$ A_{{bar}} = \\frac{{\\pi \\times {bar_dia_cm:.2f}^2}}{{4}} = {a_bar:.3f} \\text{{ cm}}^2 $$")
                st.markdown(f"$$ A_{{s,prov}} = \\frac{{A_{{bar}} \\times b}}{{s}} = \\frac{{{a_bar:.3f} \\times {b_width_cm:.1f}}}{{{spacing_cm:.1f}}} = {as_prov:.2f} \\text{{ cm}}^2 $$")
                
                check_status = "✅ PASS" if as_prov >= as_req_final else "❌ FAIL"
                st.success(f"**Conclusion:** $A_{{s,prov}} \\ge A_{{s,req}} \\implies {as_prov:.2f} \\ge {as_req_final:.2f}$ ➡️ **{check_status}**")
                
                st.markdown("---")

    # --- TAB 5: Shear Design (Two-Way and One-Way) ---
    with tab_shear:
        # ==========================================
        # --- PART 5.1: TWO-WAY SHEAR (PUNCHING) ---
        # ==========================================

        st.markdown("#### ACI 318 Section 22.6: Two-Way Shear")
        
        # --- 1. Critical Section Geometry ---
        d_shear_cm = d_eff_m * 100.0
        c1_cm = c1 * 100.0
        c2_cm = c2 * 100.0
        
        # ดึงข้อมูล Drop Panel จาก calc_obj (ที่ถูกส่งมาจาก app_calc.py)
        has_drop = calc_obj['geom'].get('has_drop', False)
        drop_w1_cm = calc_obj['geom'].get('drop_w1', 0) * 100.0
        drop_w2_cm = calc_obj['geom'].get('drop_w2', 0) * 100.0
        
        st.markdown(f"**1. Critical Section Properties ($b_o$, $A_c$, $J_c$) - {col_loc} Column**")

        # คำนวณขอบเขตหน้าตัดวิกฤต (bo) อิงตามตำแหน่งเสา พร้อมแสดงสมการ
        if col_loc == "Corner":
            b1 = c1_cm + (d_shear_cm / 2.0)
            b2 = c2_cm + (d_shear_cm / 2.0)
            bo_cm = b1 + b2
            
            # แสดงสมการ Corner
            st.markdown(f"$$b_1=c_1+\\frac{{d}}{{2}}={c1_cm:.2f}+\\frac{{{d_shear_cm:.2f}}}{{2}}={b1:.2f}\\text{{ cm}}$$")
            st.markdown(f"$$b_2=c_2+\\frac{{d}}{{2}}={c2_cm:.2f}+\\frac{{{d_shear_cm:.2f}}}{{2}}={b2:.2f}\\text{{ cm}}$$")
            st.markdown(f"$$b_o=b_1+b_2={b1:.2f}+{b2:.2f}={bo_cm:.2f}\\text{{ cm}}$$")

            c_dist = (b1**2) / (2 * (b1 + b2)) if (b1 + b2) > 0 else b1 / 2.0
            Jc = (d_shear_cm * (b1**3) / 12.0) + ((b1 * (d_shear_cm**3)) / 12.0) + (d_shear_cm * b1 * (b2**2) / 4.0)

        elif col_loc == "Edge":
            b1 = c1_cm + (d_shear_cm / 2.0)
            b2 = c2_cm + d_shear_cm
            bo_cm = (2 * b1) + b2
            
            # แสดงสมการ Edge
            st.markdown(f"$$b_1=c_1+\\frac{{d}}{{2}}={c1_cm:.2f}+\\frac{{{d_shear_cm:.2f}}}{{2}}={b1:.2f}\\text{{ cm}}$$")
            st.markdown(f"$$b_2=c_2+d={c2_cm:.2f}+{d_shear_cm:.2f}={b2:.2f}\\text{{ cm}}$$")
            st.markdown(f"$$b_o=2b_1+b_2=2({b1:.2f})+{b2:.2f}={bo_cm:.2f}\\text{{ cm}}$$")

            c_dist = (b1**2) / ((2 * b1) + b2) if ((2 * b1) + b2) > 0 else b1 / 2.0
            Jc = (d_shear_cm * (b1**3) / 6.0) + ((b1 * (d_shear_cm**3)) / 6.0) + (d_shear_cm * b1 * (b2**2) / 2.0)

        else: # Interior
            b1 = c1_cm + d_shear_cm  
            b2 = c2_cm + d_shear_cm  
            bo_cm = 2 * (b1 + b2)
            
            # แสดงสมการ Interior
            st.markdown(f"$$b_1=c_1+d={c1_cm:.2f}+{d_shear_cm:.2f}={b1:.2f}\\text{{ cm}}$$")
            st.markdown(f"$$b_2=c_2+d={c2_cm:.2f}+{d_shear_cm:.2f}={b2:.2f}\\text{{ cm}}$$")
            st.markdown(f"$$b_o=2(b_1+b_2)=2({b1:.2f}+{b2:.2f})={bo_cm:.2f}\\text{{ cm}}$$")

            c_dist = b1 / 2.0
            Jc = (d_shear_cm * (b1**3) / 6.0) + ((b1 * (d_shear_cm**3)) / 6.0) + (d_shear_cm * b1 * (b2**2) / 2.0)

        # สรุปผลลัพธ์
        Ac = bo_cm * d_shear_cm

        st.markdown("---") # เพิ่มเส้นคั่นบางๆ ให้ดูแยกส่วนชัดเจน
        st.markdown(f"- $b_1$ (ทิศทาง $c_1$) = **{b1:.1f} cm**")
        st.markdown(f"- $b_2$ (ทิศทาง $c_2$) = **{b2:.1f} cm**")
        st.markdown(f"$$ b_o = {bo_cm:.1f} \\text{{ cm}} $$")
        st.markdown(f"$$ A_c = b_o \\times d = {bo_cm:.1f} \\times {d_shear_cm:.1f} = {Ac:,.1f} \\text{{ cm}}^2 $$")
        st.markdown(f"$$ J_c \\approx {Jc:,.0f} \\text{{ cm}}^4 $$")
        st.markdown(f"- ระยะศูนย์ถ่วงถึงขอบหน้าตัดวิกฤต ($c$) = **{c_dist:.1f} cm**")

        # --- ส่วนขยาย: ตรวจสอบหน้าตัดวิกฤตรอบ Drop Panel (ถ้ามี) ---
        if has_drop and drop_w1_cm > 0 and drop_w2_cm > 0:
            st.divider()
            st.markdown("**1.1 Critical Section outside Drop Panel**")
            
            # สมมติระยะ d นอก Drop Panel แบบคร่าวๆ (หัก Cover และเหล็ก)
            d_slab_cm = (calc_obj['geom']['h_s'] * 100.0) - (cc_m * 100.0) - (selected_rebar / 20.0) 
            
            if col_loc == "Corner":
                bo_drop = (drop_w1_cm + d_slab_cm/2.0) + (drop_w2_cm + d_slab_cm/2.0)
            elif col_loc == "Edge":
                bo_drop = 2*(drop_w1_cm + d_slab_cm/2.0) + (drop_w2_cm + d_slab_cm)
            else:
                bo_drop = 2 * ((drop_w1_cm + d_slab_cm) + (drop_w2_cm + d_slab_cm))
                
            st.info(f"💡 **Drop Panel Punching Perimeter ($b_{{o,drop}}$):** {bo_drop:.1f} cm (ใช้สำหรับตรวจสอบ Shear ความหนาพื้นปกติรอบนอก Drop Panel)")

        st.divider()
        
        
        # --- 2. Demand Calculation (Vu and Munbal) ---
        st.markdown("**2. Shear and Unbalanced Moment Demand**")
        vu_kg = wu * ((L1 * L2) - ((c1 + d_eff_m) * (c2 + d_eff_m)))
        st.markdown(f"$$ V_u = {wu:,.0f} \\times \\left[ ({L1:.2f} \\times {L2:.2f}) - ({c1+d_eff_m:.2f} \\times {c2+d_eff_m:.2f}) \\right] = {vu_kg:,.0f} \\text{{ kg}} $$")
        
        # ดึงค่าโมเมนต์ลบที่หัวเสาเพื่อมาเป็น Unbalanced Moment
        mu_at_column = 0
        if not df_design.empty and 'Location' in df_design.columns:
            try:
                # ดึง Mu จาก Interior Negative เป็นหลัก (หรือปรับตาม Location ที่พิจารณา)
                match_int_neg = df_design[df_design['Location'].str.contains("Interior Negative", case=False, na=False)].iloc[0]
                mu_at_column = match_int_neg.get('Mu (kg-m)', match_int_neg.get('Moment (kg-m)', 0))
            except IndexError:
                mu_at_column = 0
                
        st.markdown(f"$$ M_{{unbal}} = {mu_at_column:,.0f} \\text{{ kg-m}} $$ *(อ้างอิงจากโมเมนต์ลบที่หัวเสา)*")
        
        # คำนวณสัดส่วนการถ่ายโอนโมเมนต์ (Moment Transfer Fractions)
        gamma_f = 1.0 / (1.0 + (2.0/3.0) * math.sqrt(b1/b2))
        gamma_v = 1.0 - gamma_f
        st.markdown(f"$$ \\gamma_f = \\frac{{1}}{{1 + \\frac{{2}}{{3}}\\sqrt{{b_1/b_2}}}} = {gamma_f:.3f} \\implies \\gamma_v = {gamma_v:.3f} $$")
        
        # คำนวณหน่วยแรงเค้นเฉือนรวมสูงสุด (Maximum Combined Shear Stress)
        vu_direct = vu_kg / Ac
        vu_moment = (gamma_v * (mu_at_column * 100.0) * c_dist) / Jc if Jc > 0 else 0
        vu_max = vu_direct + vu_moment
        
        st.markdown(f"$$ v_{{u,direct}} = \\frac{{V_u}}{{A_c}} = {vu_direct:.2f} \\text{{ ksc}} $$")
        st.markdown(f"$$ v_{{u,moment}} = \\frac{{\\gamma_v M_{{unbal}} c}}{{J_c}} = \\frac{{{gamma_v:.3f} \\times {mu_at_column:,.0f} \\times 100 \\times {c_dist:.1f}}}{{{Jc:,.0f}}} = {vu_moment:.2f} \\text{{ ksc}} $$")
        st.markdown(f"$$ v_{{u,max}} = v_{{u,direct}} + v_{{u,moment}} = {vu_max:.2f} \\text{{ ksc}} $$")

        st.divider()
        
        # --- 3. Capacity Calculation ---
        st.markdown("#### ACI 318 Table 22.6.5.2: Two-Way Shear Strength ($v_c$)")
        st.info("💡 **Note:** Coefficients updated to **MKS System (kg/cm²)**: 1.06, 0.53, 0.27 (Equivalent to SI: 0.33, 0.17, 0.083)")
        
        phi_shear = 0.85 # ACI 318-19 Table 21.2.1
        alpha_s = 40 if case_type == "Interior" else (30 if has_edge_beam else 20)
        beta_c = max(c1, c2) / min(c1, c2)
        
        # คำนวณกำลังต้านทานในรูปแบบของแรง (Force: kg)
        vc1 = 1.06 * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc2 = 0.53 * (1 + (2/beta_c)) * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc3 = 0.27 * (2 + (alpha_s * d_shear_cm / bo_cm)) * math.sqrt(fc_ksc) * bo_cm * d_shear_cm
        vc_gov_force = min(vc1, vc2, vc3)
        phi_vc_force = phi_shear * vc_gov_force
        
        # แปลงเป็นหน่วยแรงเค้น (Stress: ksc) สำหรับตรวจสอบร่วมกับโมเมนต์
        phi_vc_stress = phi_vc_force / Ac
        
        st.markdown(f"- $\\beta$ (Column Aspect Ratio) = **{beta_c:.2f}**")
        st.markdown(f"- $\\alpha_s$ (Position Factor) = **{alpha_s}**")

        st.markdown("**Equation (a):**")
        st.markdown(f"$$ V_{{c1}} = 1.06 \\sqrt{{{fc_ksc:.0f}}} \\times {bo_cm:.1f} \\times {d_shear_cm:.1f} = {vc1:,.0f} \\text{{ kg}} $$")
        
        st.markdown("**Equation (b):**")
        st.markdown(f"$$ V_{{c2}} = 0.53 \\left( 1 + \\frac{{2}}{{{beta_c:.2f}}} \\right) \\sqrt{{{fc_ksc:.0f}}} \\times {bo_cm:.1f} \\times {d_shear_cm:.1f} = {vc2:,.0f} \\text{{ kg}} $$")
        
        st.markdown("**Equation (c):**")
        st.markdown(f"$$ V_{{c3}} = 0.27 \\left( 2 + \\frac{{{alpha_s} \\times {d_shear_cm:.1f}}}{{{bo_cm:.1f}}} \\right) \\sqrt{{{fc_ksc:.0f}}} \\times {bo_cm:.1f} \\times {d_shear_cm:.1f} = {vc3:,.0f} \\text{{ kg}} $$")
        
        st.markdown("**Governing Capacity:**")
        st.markdown(f"$$ \\phi V_c = {phi_shear} \\times \\min(V_{{c1}}, V_{{c2}}, V_{{c3}}) = {phi_vc_force:,.0f} \\text{{ kg}} $$")
        st.markdown(f"$$ \\phi v_c = \\frac{{\\phi V_c}}{{A_c}} = {phi_vc_stress:.2f} \\text{{ ksc}} $$")

        st.divider()
        
        # --- 4. Demand vs Capacity Verification ---
        st.markdown("#### Demand vs Capacity Verification (Stress Basis)")
        punch_status = "✅ SAFE" if vu_max <= phi_vc_stress else "❌ FAIL (Increase slab thickness / f'c)"
        
        st.markdown(f"**Final Verification:** $v_{{u,max}} \\le \\phi v_c \\implies {vu_max:.2f} \\text{{ ksc}} \\le {phi_vc_stress:.2f} \\text{{ ksc}}$ ➡️ **{punch_status}**")


        # ==========================================
        # --- PART 5.2: ONE-WAY SHEAR (BEAM ACTION) ---
        # ==========================================
        st.divider()
        st.markdown("#### ACI 318 Section 22.5: One-Way (Beam Action) Shear")
        st.markdown("ตรวจสอบหน้าตัดวิกฤตที่ระยะ $d$ จากขอบเสา โดยคิดความกว้างพื้นเต็มช่วง ($b_w = L_2$)")
        
        # --- 1. Geometry & Critical Section ---
        # ระยะห่างจากกึ่งกลางเสาถึงหน้าตัดวิกฤต = c1/2 + d
        dist_crit_m = (c1 / 2.0) + d_eff_m
        
        # ความยาวของพื้นที่รับน้ำหนัก (Tributary Length) ที่ทำให้เกิดแรงเฉือน ณ หน้าตัดวิกฤต
        L_trib_m = (L1 / 2.0) - dist_crit_m
        if L_trib_m < 0:
            L_trib_m = 0  # ป้องกันกรณีพื้นหนามากหรือช่วงสั้นมากจนหน้าตัดวิกฤตเลยกึ่งกลางช่วง
            
        b_w_m = L2
        b_w_cm = b_w_m * 100.0
        
        st.markdown("**1. Demand Calculation ($V_{u,1way}$)**")
        st.markdown(f"- ระยะหน้าตัดวิกฤตจากกึ่งกลางเสา = $c_1/2 + d = {c1/2:.2f} + {d_eff_m:.2f} = {dist_crit_m:.2f} \\text{{ m}}$")
        st.markdown(f"- ระยะรับน้ำหนักเฉือน (Tributary Length) = $L_1/2 - ({dist_crit_m:.2f}) = {(L1/2):.2f} - {dist_crit_m:.2f} = {L_trib_m:.2f} \\text{{ m}}$")
        
        vu_1way_kg = wu * b_w_m * L_trib_m
        st.markdown(f"$$ V_{{u,1way}} = w_u \\times L_2 \\times \\text{{Tributary Length}} $$")
        st.markdown(f"$$ V_{{u,1way}} = {wu:,.0f} \\times {b_w_m:.2f} \\times {L_trib_m:.2f} = {vu_1way_kg:,.0f} \\text{{ kg}} $$")
        
        # --- 2. Capacity Calculation ---
        st.markdown("**2. Capacity Calculation ($\\phi V_{c,1way}$)**")
        st.info("💡 **Note:** ใช้สัมประสิทธิ์ MKS: $0.53$ (เทียบเท่า $0.17$ ในระบบ SI) และ $\\phi = 0.75$ สำหรับแรงเฉือนแบบทางเดียว")
        
        # Vc สำหรับ One-way shear = 0.53 * sqrt(fc') * bw * d
        vc_1way_kg = 0.53 * math.sqrt(fc_ksc) * b_w_cm * d_shear_cm
        phi_vc_1way = 0.75 * vc_1way_kg
        
        st.markdown(f"$$ V_{{c,1way}} = 0.53 \\sqrt{{{fc_ksc:.0f}}} \\times b_w \\times d $$")
        st.markdown(f"$$ V_{{c,1way}} = 0.53 \\times {math.sqrt(fc_ksc):.2f} \\times {b_w_cm:.1f} \\times {d_shear_cm:.1f} = {vc_1way_kg:,.0f} \\text{{ kg}} $$")
        st.markdown(f"$$ \\phi V_{{c,1way}} = 0.75 \\times {vc_1way_kg:,.0f} = {phi_vc_1way:,.0f} \\text{{ kg}} $$")
        
        # --- 3. Verification ---
        st.markdown("**3. Demand vs Capacity Verification**")
        oneway_status = "✅ SAFE" if vu_1way_kg <= phi_vc_1way else "❌ FAIL (Increase slab thickness / f'c)"
        
        st.markdown(f"**Final Verification:** $V_{{u,1way}} \\le \\phi V_{{c,1way}} \\implies {vu_1way_kg:,.0f} \\text{{ kg}} \\le {phi_vc_1way:,.0f} \\text{{ kg}}$ ➡️ **{oneway_status}**")


# --- TAB 6: Drawings & Details ---
    with tab_viz:
        st.markdown("#### 🎨 Section & Punching Shear Perimeters")
        st.markdown("ภาพวาดหน้าตัดและขอบเขตหน้าตัดวิกฤต (Critical Section) อ้างอิงตามสัดส่วนจริง (Scaled to dimensions)")
        
        # ตรวจสอบว่าได้ import viz_ddm มาแล้วหรือไม่
        if 'viz_ddm' in sys.modules or 'viz_ddm' in globals():
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                st.markdown("**Slab-Column Cross Section**")
                # เรียกใช้ฟังก์ชันวาดหน้าตัด
                fig1 = viz_ddm.draw_slab_section(geom_data, edited_df)
                st.pyplot(fig1)
                
            with col_viz2:
                st.markdown(f"**Punching Perimeter (b_o) - {col_loc} Column**")
                # เรียกใช้ฟังก์ชันวาดแปลนทะลุ
                fig2 = viz_ddm.draw_punching_plan(col_loc, c1_cm, c2_cm, d_shear_cm)
                st.pyplot(fig2)
        else:
            st.info("กรุณาตรวจสอบว่าได้สร้างไฟล์ `viz_ddm.py` และใส่ `import viz_ddm` ไว้ที่ด้านบนสุดของไฟล์ `app_ddm.py` แล้ว")
   
