import streamlit as st
import pandas as pd
import math
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import copy
from calc_ddm import calculate_ddm

# หากมีการแยกไฟล์ viz_ddm ไว้ โหลดเข้ามาด้วย
try:
    import viz_ddm
except ImportError:
    pass

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

def render_ddm_tab(calc_obj):
    # =========================================================================
    # 🌟 1. ดึงข้อมูลพื้นฐาน (Physical Variables) และทำ MASTER SWAP
    # =========================================================================
    raw_loc = calc_obj.get('col_location_raw', 'Interior Column')
    col_loc = str(raw_loc).replace(" Column", "") 
    
    # ✅ ดึงตัวเลข fy มาใช้
    fy_val = calc_obj.get('mat', {}).get('fy', 4000)

    loads_data = calc_obj.get('loads', {})
    dl = loads_data.get('dl', loads_data.get('DL', 0))
    ll = loads_data.get('ll', loads_data.get('LL', 0))

    wu = loads_data.get('wu', (1.4 * dl) + (1.7 * ll))

    geom_data = calc_obj.get('geom', {})
    
    # 1.1 ดึงค่า Physical X-Y ดิบๆ จากหน้าจอมาก่อน (มองหน้าจอ X คือแนวนอน, Y คือแนวตั้ง)
    physical_Lx = geom_data.get('L1', 0)
    physical_Ly = geom_data.get('L2', 0)
    physical_L2_t = geom_data.get('L2_t', physical_Ly)
    physical_L2_b = geom_data.get('L2_b', physical_Ly)
    physical_cx_cm = geom_data.get('c1_cm', 50)
    physical_cy_cm = geom_data.get('c2_cm', 50)
    
    analysis_dir = calc_obj.get('analysis_dir', 'x-axis')

    # 1.2 🌟 MASTER SWAP LOGIC 🌟
    # สลับแกนตั้งแต่ต้นทาง! ให้ L1 เป็นแกนที่ใช้วิเคราะห์เสมอ
    if analysis_dir == 'y-axis':
        L1 = physical_Ly
        L2 = physical_Lx
        L2_t = physical_Lx  # แผงด้านข้างของแกน Y ก็คือความกว้างด้าน X
        L2_b = physical_Lx
        c1_cm = physical_cy_cm
        c2_cm = physical_cx_cm
    else:
        L1 = physical_Lx
        L2 = physical_Ly
        L2_t = physical_L2_t
        L2_b = physical_L2_b
        c1_cm = physical_cx_cm
        c2_cm = physical_cy_cm
        
    c1_m = c1_cm / 100.0
    c2_m = c2_cm / 100.0
    
    # 🌟 คำนวณ Clear Span (ln) จากแกนที่จัดเรียงถูกต้องแล้ว
    ln = max(L1 - c1_m, 0.65 * L1) if L1 > 0 else 0

    h_slab_cm = geom_data.get('h_slab_cm', geom_data.get('h_s', 0.20) * 100.0)
    has_drop = geom_data.get('has_drop', False)
    h_drop_cm = geom_data.get('h_drop_cm', h_slab_cm) if has_drop else h_slab_cm

    eb_data = geom_data.get('edge_beam', {})

    # =========================================================================
    # 🌟 2. แพ็กข้อมูล inputs (รับรองว่า calculate_ddm หาเจอทุกตัวแปรแบบไม่สลับแกนแล้ว!)
    # =========================================================================
    inputs = {
        'l1': L1, 'L1': L1,
        'l2': L2, 'L2': L2,
        'ln': ln,
        'wu': wu,
        'c1': c1_m, 
        'c2': c2_m,
        'c1_cm': c1_cm,
        'c2_cm': c2_cm,
        'h_slab': h_slab_cm,
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
        'analysis_dir': analysis_dir
    }

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
    
    fc_ksc = inputs['fc']
    fy_ksc = inputs['fy']
    has_edge_beam = inputs['has_edge_beam']
    case_type = inputs['case_type']

    # =========================================================================
    # 🌟 5. โค้ดส่วนแสดงผล UI (Step 3 ต่อด้วย Step 4)
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

    # ==========================================================================
    # STEP 4: INTERACTIVE DETAILING
    # ==========================================================================
    st.markdown("### Step 4: Reinforcement Detailing & Compliance")
    
    if not df_results.empty and 'Location' in df_results.columns:
        
        # ✅ หาความกว้าง Column Strip แบบแยกทีละฝั่งตาม ACI 318
        # ฝั่งบน (หรือซ้าย) = 0.25 * min(L1, L2_top)
        cs_top = 0.25 * min(L1, L2_t) if L2_t > 0 else 0
        
        # ฝั่งล่าง (หรือขวา) = 0.25 * min(L1, L2_bottom)
        cs_bot = 0.25 * min(L1, L2_b) if L2_b > 0 else 0
        
        # รวมความกว้างแถบเสา และคำนวณแถบกลางที่เหลือ
        cs_width = cs_top + cs_bot
        ms_width = max(L2 - cs_width, 0)  # ใช้ max กันค่าติดลบไว้

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
            width="stretch", hide_index=True, key="rebar_editor"
        )

        def compute_results(row, original_df):
            width_m = original_df.loc[original_df['Location'] == row['Location'], 'Strip Width (m)'].values[0]
            db_mm = row['Bar Size (mm)']
            bar_area = math.pi * (db_mm / 10.0)**2 / 4.0
            as_req = row['As Req (cm2)']
            
            spacing = row['Spacing (cm)'] if row['Spacing (cm)'] > 0 else 1.0
            width_cm = width_m * 100.0
            
            # คำนวณจำนวนเส้นและพื้นที่เหล็กเสริมที่จัดจริง
            num_bars = math.ceil(width_cm / spacing)
            as_prov = bar_area * num_bars
            
            # 1. ตรวจสอบระยะเรียงมากที่สุด (ACI 318-19 Sec 8.7.2.1): min(2h, 45 cm)
            max_spacing_aci = min(2 * h_slab_cm, 45.0)
            
            # 2. ตรวจสอบระยะเรียงน้อยที่สุด (ACI 318-19 Sec 25.2.1): max(db, 2.5 cm) เพื่อการเทคอนกรีตที่ดี
            min_spacing_aci = max(db_mm / 10.0, 2.5)
            
            # 3. คำนวณเหล็กเสริมขั้นต่ำต้านการยืดหดตัวและอุณหภูมิ (ACI 318-19 Sec 24.4)
            # ปรับตามความหนาจริง: แถบหัวเสาภายใน (Int Neg) ที่มี Drop Panel จะใช้ h_drop_cm นอกนั้นใช้ h_slab_cm
            h_current = h_drop_cm if ("Int Neg" in row['Location'] and has_drop) else h_slab_cm
            as_min_temp = 0.0018 * width_cm * h_current
            
            # ตรวจสอบเงื่อนไขแยกรายข้อเพื่อรายงานผลตรงจุด
            reasons = []
            if as_prov < as_req:
                reasons.append("⚠️ As ไม่พอ")
            if spacing > max_spacing_aci:
                reasons.append(f"❌ ห่างเกิน ({max_spacing_aci:.1f} cm)")
            if spacing < min_spacing_aci:
                reasons.append(f"❌ ชิดเกิน ({min_spacing_aci:.1f} cm)")
                
            status = "✅ PASS" if not reasons else " | ".join(reasons)
            return pd.Series([width_m, num_bars, min_spacing_aci, max_spacing_aci, as_min_temp, as_prov, status])

        # อัปเดตคอลัมน์ที่ส่งกลับมาจากฟังก์ชันดึงค่า
        edited_df[['Width (m)', 'Total Bars', 'Min Spacing (cm)', 'Max Spacing (cm)', 'As Min Temp (cm2)', 'Prov. Area (cm2)', 'Status']] = edited_df.apply(lambda r: compute_results(r, df_design), axis=1)

        # ปรับปรุงกล่องแจ้งเตือนภาพรวมตามสัญลักษณ์ใหม่
        if "❌" in "".join(edited_df['Status'].values) or "⚠️" in "".join(edited_df['Status'].values):
            st.error("Overall Status: Compliance issues found. Please adjust bar size or spacing to satisfy ACI limits.")
        else:
            st.success("Overall Status: PASS. Reinforcement layout complies fully with ACI 318 detailing criteria.")

        # เลือกคอลัมน์ที่จะนำมาแสดงผลบนตารางให้ครอบคลุมข้อมูลเชิงวิศวกรรม
        display_cols = [
            'Location', 'Bar Size (mm)', 'Spacing (cm)', 
            'Min Spacing (cm)', 'Max Spacing (cm)', 
            'As Req (cm2)', 'As Min Temp (cm2)', 
            'Prov. Area (cm2)', 'Status'
        ]
        
        def highlight_status(val):
            if "❌" in str(val):
                return "color: #ff4b4b; font-weight: bold;"
            elif "⚠️" in str(val):
                return "color: #f39c12; font-weight: bold;"
            return "color: #21c354; font-weight: bold;"
            
        styled_df = edited_df[display_cols].style.map(highlight_status, subset=['Status']).format({
            'As Req (cm2)': "{:.2f}", 'As Min Temp (cm2)': "{:.2f}", 
            'Prov. Area (cm2)': "{:.2f}", 'Min Spacing (cm)': "{:.1f}", 'Max Spacing (cm)': "{:.1f}"
        })
        st.dataframe(styled_df, width="stretch", hide_index=True)
        
    # ==========================================================================
    # STEP 5: COMPREHENSIVE CALCULATION NOTE (ACI 318)
    # ==========================================================================
    st.markdown("---")
    st.markdown("### Detailed Engineering Calculation Report")
    st.caption("Reference: ACI 318-19 Building Code Requirements for Structural Concrete")

    tab_limit, tab_load, tab_dist, tab_flex, tab_shear, tab_viz = st.tabs([
        "1. Geometry Limits", 
        "2. Loads & Moments", 
        "3. Distribution Factors",
        "4. Flexural Detailing", 
        "5. Punching Shear",
        "6. Drawings & Details"
    ])

    # --- TAB 1: Limitations ---
    with tab_limit:
        st.markdown("### 📐 ACI 318-19 Sec. 8.10.2: DDM Applicability Criteria")
        st.write("To ensure gravity loads safely distribute to supports using the Direct Design Method (DDM), the slab geometry must strictly conform to these criteria. Non-compliance **requires** the Equivalent Frame Method (EFM).")

        # ==========================================
        # 🌟 PRE-CALCULATE VARIABLES (Fixed logic)
        # ==========================================
        # 1. Geometry 
        l_long = max(L1, L2)
        l_short = min(L1, L2) if min(L1, L2) > 0 else 1.0
        span_ratio_val = l_long / l_short
        is_ratio_ok = span_ratio_val <= 2.0

        # 2. Total Dead Load (SDL + Slab Self-Weight)
        slab_wt = h_slab_m * 2400.0  # kg/m2 (Slab Self-Weight)
        total_dl = dl + slab_wt      # dl is assumed to be Superimposed DL
        
        load_ratio_val = ll / total_dl if total_dl > 0 else 0
        is_load_ok = load_ratio_val <= 2.0

        with st.container(border=True):
            # ==========================================
            # I. GENERAL CONSTRAINTS
            # ==========================================
            st.markdown("#### I. General Configuration")
            col_req1, col_req2 = st.columns(2)
            with col_req1:
                st.info("**1. Minimum Continuous Spans**\n\nRequires $\\ge$ 3 continuous spans in each direction. *(Assumed satisfied by user)*.")
            with col_req2:
                st.info(r"**2. Successive Span Diff.**\n\nAdjacent spans differ $\le 33.3\%$ of longer span: $|L_{i} - L_{i+1}| \le \frac{1}{3} L_{longer}$")

            st.divider()

            # ==========================================
            # II. CALCULATED CONSTRAINTS
            # ==========================================
            st.markdown("#### II. Panel Geometry & Loading Checks")
            col_calc1, col_calc2 = st.columns(2)

            with col_calc1:
                with st.container(border=True):
                    st.markdown("**3. Panel Aspect Ratio**")
                    st.caption(r"Limit: $L_{long} / L_{short} \le 2.0$")
                    
                    # 🎨 วาดรูป Plan View (ล็อก Scale ตาม Physical X-Y จริง เพื่อไม่ให้รูปหมุน)
                    fig_plan, ax_plan = plt.subplots(figsize=(6, 3.5))
                    physical_long = max(physical_Lx, physical_Ly)
                    scale = 3.0 / physical_long if physical_long > 0 else 1.0
                    viz_Lx, viz_Ly = physical_Lx * scale, physical_Ly * scale
                    x_c, y_c = 3.0, 1.75 
                    x0, y0 = x_c - viz_Lx/2, y_c - viz_Ly/2
                    
                    # 1. วาดพื้น (ใช้ viz_Lx, viz_Ly)
                    ax_plan.add_patch(patches.Rectangle((x0, y0), viz_Lx, viz_Ly, fill=True, facecolor='#f8fafc', edgecolor='#1e293b', lw=2))
                    
                    # 2. วาดเสา (ขยับตาม viz_Lx, viz_Ly)
                    col_w = 0.25
                    for x in [x0, x0 + viz_Lx]:
                        for y in [y0, y0 + viz_Ly]:
                            ax_plan.add_patch(patches.Rectangle((x-col_w/2, y-col_w/2), col_w, col_w, fill=True, color='#334155', zorder=3))
                            ax_plan.add_patch(patches.Rectangle((x-col_w/2, y-col_w/2), col_w, col_w, fill=False, edgecolor='#94a3b8', hatch='///', lw=0.5, zorder=4))
                    
                    # 3. วาดเส้นบอกระยะแกน (สลับสีและข้อความตามแกนที่วิเคราะห์)
                    if analysis_dir == 'x-axis':
                        # วิเคราะห์แกน X: L1 อยู่แนวนอน(น้ำเงิน), L2 อยู่แนวตั้ง(เขียว)
                        ax_plan.annotate('', xy=(x0, y0-0.3), xytext=(x0+viz_Lx, y0-0.3), arrowprops=dict(arrowstyle='<->', color='#2563eb', lw=2))
                        ax_plan.text(x_c, y0-0.5, f'L1 (Analysis Dir.) = {L1:.2f} m', ha='center', color='#2563eb', fontweight='bold', fontsize=9)
                        
                        ax_plan.annotate('', xy=(x0-0.3, y0), xytext=(x0-0.3, y0+viz_Ly), arrowprops=dict(arrowstyle='<->', color='#16a34a', lw=2))
                        ax_plan.text(x0-0.45, y_c, f'L2 (Transverse) = {L2:.2f} m', va='center', rotation=90, color='#16a34a', fontweight='bold', fontsize=9)
                    else:
                        # วิเคราะห์แกน Y: L1 อยู่แนวตั้ง(น้ำเงิน), L2 อยู่แนวนอน(เขียว)
                        ax_plan.annotate('', xy=(x0-0.3, y0), xytext=(x0-0.3, y0+viz_Ly), arrowprops=dict(arrowstyle='<->', color='#2563eb', lw=2))
                        ax_plan.text(x0-0.45, y_c, f'L1 (Analysis Dir.) = {L1:.2f} m', va='center', rotation=90, color='#2563eb', fontweight='bold', fontsize=9)
                        
                        ax_plan.annotate('', xy=(x0, y0-0.3), xytext=(x0+viz_Lx, y0-0.3), arrowprops=dict(arrowstyle='<->', color='#16a34a', lw=2))
                        ax_plan.text(x_c, y0-0.5, f'L2 (Transverse) = {L2:.2f} m', ha='center', color='#16a34a', fontweight='bold', fontsize=9)
                    
                    ax_plan.set_xlim(0, 6); ax_plan.set_ylim(0, 3.5); ax_plan.axis('off')
                    st.pyplot(fig_plan)
                    
                    # สมการแทนค่าที่ชัดเจน
                    st.latex(r"L_{long} = \max(" + f"{L1:.2f}, {L2:.2f}" + r") = \mathbf{" + f"{l_long:.2f}" + r" \text{ m}}")
                    st.latex(r"L_{short} = \min(" + f"{L1:.2f}, {L2:.2f}" + r") = \mathbf{" + f"{l_short:.2f}" + r" \text{ m}}")
                    st.latex(r"\text{Ratio} = \frac{L_{long}}{L_{short}} = \frac{" + f"{l_long:.2f}" + r"}{" + f"{l_short:.2f}" + r"} = \mathbf{" + f"{span_ratio_val:.2f}" + r"}")
                    
                    if is_ratio_ok:
                        st.success(f"**PASS:** Aspect ratio ≤ 2.0 (Two-way action).")
                    else:
                        st.error(f"**FAIL:** Ratio > 2.0 (One-way behavior, EFM Req).")
               
            with col_calc2:
                with st.container(border=True):
                    st.markdown("**4. Gravity Load Ratio**")
                    st.caption(r"Limit: Unfactored LL $\le 2 \times$ Unfactored Total DL")
                    
                    # 🎨 วาดรูป Section แสดง Load ที่แยกพื้นออกจาก SDL อย่างชัดเจน
                    fig_load, ax_load = plt.subplots(figsize=(6, 3.5))
                    
                    # วาดความหนาแผงพื้น
                    ax_load.add_patch(patches.Rectangle((1, 1), 4, 0.4, fill=True, facecolor='#cbd5e1', edgecolor='#1e293b', lw=2))
                    ax_load.text(3, 1.2, f"Slab Self-Weight: {slab_wt:.0f} kg/m²", ha='center', va='center', fontsize=9, color='#334155', fontweight='bold')
                    
                    for x in [1.5, 2.5, 3.5, 4.5]:
                        # SDL Arrows (วางบนพื้น)
                        ax_load.annotate('', xy=(x, 1.4), xytext=(x, 1.9), arrowprops=dict(arrowstyle='->', color='#64748b', lw=1.5))
                        # LL Arrows (วางบน SDL)
                        ax_load.annotate('', xy=(x, 1.9), xytext=(x, 2.5), arrowprops=dict(arrowstyle='->', color='#ca8a04', lw=3))
                    
                    ax_load.text(3, 2.7, f"Live Load (LL): {ll:.0f} kg/m²", ha='center', fontsize=10, fontweight='bold', color='#ca8a04')
                    ax_load.text(3, 2.1, f"Superimposed DL (SDL): {dl:.0f} kg/m²", ha='center', fontsize=10, color='#64748b')
                    
                    ax_load.set_xlim(0.5, 5.5); ax_load.set_ylim(0.5, 3.2); ax_load.axis('off')
                    st.pyplot(fig_load)
                    
                    # สมการแทนค่าที่ชัดเจน
                    st.latex(r"\text{Total DL} = \text{SDL} + \text{Self-Weight}")
                    st.latex(r"\text{Total DL} = " + f"{dl:.0f} + {slab_wt:.0f}" + r" = \mathbf{" + f"{total_dl:.0f}" + r"} \text{ kg/m}^2")
                    st.latex(r"\text{Ratio} = \frac{LL}{\text{Total DL}} = \frac{" + f"{ll:,.0f}" + r"}{" + f"{total_dl:,.0f}" + r"} = \mathbf{" + f"{load_ratio_val:.2f}" + r"}")
                    
                    if is_load_ok:
                        st.success("**PASS:** Live Load ratio within DDM limits.")
                    else:
                        st.error("**FAIL:** Pattern loading dictates EFM.")

            st.divider()

            # ==========================================
            # III. CLEAR SPAN (Ln) - DETAILED Substitution
            # ==========================================
            st.markdown("#### III. Critical Span Definition: Effective Clear Span ($L_n$)")
            
            with st.container(border=True):
                # 🎨 วาดรูป Section View
                fig_sec, ax_sec = plt.subplots(figsize=(8, 2.5))
                for x in [1.5, 5.5]:
                    ax_sec.add_patch(patches.Rectangle((x, 0), 0.6, 2, fill=True, color='#475569', zorder=3))
                    ax_sec.add_patch(patches.Rectangle((x, 0), 0.6, 2, fill=False, edgecolor='#94a3b8', hatch='///', lw=0.5, zorder=4))
                
                ax_sec.add_patch(patches.Rectangle((0.5, 2), 6.5, 0.4, fill=True, facecolor='#f8fafc', edgecolor='#1e293b', lw=2))
                
                # C-to-C
                ax_sec.plot([1.8, 1.8], [2.5, 3.2], color='gray', ls='-', lw=1.5, zorder=1)
                ax_sec.plot([5.8, 5.8], [2.5, 3.2], color='gray', ls='-', lw=1.5, zorder=1)
                ax_sec.annotate('', xy=(1.8, 3), xytext=(5.8, 3), arrowprops=dict(arrowstyle='<->', color='#1e293b', lw=1.2))
                ax_sec.text(3.8, 3.25, f'L1 (Analysis Dir.) = {L1:.2f} m', ha='center', fontsize=10, fontweight='bold')
                
                # Face-to-Face (Ln)
                ax_sec.plot([2.1, 2.1], [0.5, 1.8], color='#ca8a04', ls=':', lw=2, zorder=2)
                ax_sec.plot([5.5, 5.5], [0.5, 1.8], color='#ca8a04', ls=':', lw=2, zorder=2)
                ax_sec.annotate('', xy=(2.1, 1.5), xytext=(5.5, 1.5), arrowprops=dict(arrowstyle='<->', color='#ca8a04', lw=2.5, zorder=5))
                ax_sec.text(3.8, 1.65, 'Clear Span (Ln)', ha='center', color='#854d0e', fontweight='bold', fontsize=11)
                
                # c1
                ax_sec.annotate('', xy=(1.5, 0.8), xytext=(2.1, 0.8), arrowprops=dict(arrowstyle='<->', color='#b91c1c', lw=1.5))
                ax_sec.text(1.8, 1.0, f'c1={c1_cm:.0f}cm', ha='center', color='#b91c1c', fontweight='bold', fontsize=9)
                
                ax_sec.set_xlim(0, 7.5); ax_sec.set_ylim(-0.2, 4); ax_sec.axis('off')
                st.pyplot(fig_sec)

                st.markdown("**Detailed Substitution:**")
                st.caption("ACI 318-19 defines clear span face-to-face of columns, but not less than 65% of the centerline span:")
                
                term1 = L1 - c1
                term2 = 0.65 * L1
                
                with st.container(border=True):
                    st.latex(r"L_n = \max(\ L_1 - c_1,\ \ 0.65 L_1\ )")
                    st.divider()
                    st.latex(r"\text{Cond 1: } L_1 - c_1 = " + f"{L1:.2f}" + r" - " + f"{c1:.2f}" + r" = \mathbf{" + f"{term1:.2f}" + r" \text{ m}}")
                    st.latex(r"\text{Cond 2: } 0.65 \times L_1 = 0.65 \times " + f"{L1:.2f}" + r" = \mathbf{" + f"{term2:.2f}" + r" \text{ m}}")
                    st.divider()
                    st.latex(r"L_n = \max(\ " + f"{term1:.2f}" + r",\ \ " + f"{term2:.2f}" + r"\ )")
                    st.info(f"### 📏 Final Clear Span ($L_n$) = {ln:.2f} m")

    with tab_load:
        st.markdown("#### ACI 318 Section 5.3.1: Load Combinations")
        st.markdown(f"$$ W_u = 1.4 DL + 1.7 LL $$")
        st.markdown(f"**Result:** $W_u = 1.4({dl:,.0f}) + 1.7({ll:,.0f}) =$ **{wu:,.0f}** kg/m²")

        st.divider()
        st.markdown("#### ACI 318 Section 8.10.3.2: Total Factored Static Moment")
        st.markdown(f"$$ M_o = \\frac{{W_u \\times L_2 \\times L_n^2}}{{8}} $$")
    
        # FIXED: \times used properly to prevent the \t string bug
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
        # ==========================================
        # --- 🟢 ระบบตรวจสอบทิศทางเพื่อสลับแกน (แก้บัค Case Sensitive แล้ว) ---
        # ==========================================
        analysis_dir = inputs.get('analysis_dir', 'x-axis')
        
        # จับแปลงเป็นตัวพิมพ์เล็กทั้งหมดก่อนเช็ค เพื่อไม่ให้พลาดอีก
        dir_str = str(analysis_dir).lower()
        is_y_axis = 'y' in dir_str or 'l2' in dir_str

        if is_y_axis:
            # วิเคราะห์แกน Y (ขนาน L2)
            span_L, trans_L = L2, L1
            span_label, trans_label = "L_2", "L_1"
            rebar_dir_text = "เหล็กหลักขนานแนวแกน Y (L2)"
        else:
            # วิเคราะห์แกน X (ขนาน L1)
            span_L, trans_L = L1, L2
            span_label, trans_label = "L_1", "L_2"
            rebar_dir_text = "เหล็กหลักขนานแนวแกน X (L1)"

        st.markdown(f"#### ACI 318 Section 22.2: Flexural Reinforcement Required")
        st.markdown(f"**ทิศทางการออกแบบปัจจุบัน:** {rebar_dir_text}")
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
                    # Column Strip กว้าง min(0.5*L1, 0.5*L2) เสมอ (ตามหลัก ACI) ดังนั้นไม่ต้องสลับสูตรนี้
                    st.markdown(f"$$ b = \\min(0.5 L_1, 0.5 L_2) = \\min(0.5 \\times {L1:.2f}, 0.5 \\times {L2:.2f}) = {b_width_m:.2f} \\text{{ m}} = {b_width_cm:.1f} \\text{{ cm}} $$")
                else:
                    st.markdown("- **Strip Width ($b$):** Based on **Middle Strip** geometry")
                    # 🟢 Middle Strip จะใช้ความกว้างขวาง (Transverse) หักด้วยความกว้าง Column Strip
                    st.markdown(f"$$ b = {trans_label} - b_{{cs}} = {trans_L:.2f} - {cs_width:.2f} = {b_width_m:.2f} \\text{{ m}} = {b_width_cm:.1f} \\text{{ cm}} $$")
                    
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
        # --- 🟢 แกนอ้างอิงและการสลับแกน (MASTER SWAP) ---
        # ==========================================
        analysis_dir = inputs.get('analysis_dir', 'X-Axis')
        is_y_axis = "Y-Axis" in analysis_dir or "L2" in analysis_dir

        if is_y_axis:
            L_span, L_trans = L2, L1
            c_span, c_trans = c2, c1
            span_label, trans_label = "L2", "L1"
            c_span_label, c_trans_label = "c_2", "c_1"
        else:
            L_span, L_trans = L1, L2
            c_span, c_trans = c1, c2
            span_label, trans_label = "L1", "L2"
            c_span_label, c_trans_label = "c_1", "c_2"

        # ==========================================
        # --- PART 5.1: TWO-WAY SHEAR (PUNCHING) ---
        # ==========================================
        st.header("1. Two-Way (Punching) Shear Design")
        st.caption("มาตรฐานอ้างอิง: ACI 318 Section 22.6 & ทฤษฎีโมเมนต์ไม่สมดุล (Unbalanced Moment Transfer)")
        
        # --- 1. Critical Section Geometry ---
        d_shear_cm = d_eff_m * 100.0
        c_span_cm = c_span * 100.0
        c_trans_cm = c_trans * 100.0
        
        has_drop = calc_obj['geom'].get('has_drop', False)
        drop_span_cm = (calc_obj['geom'].get('drop_w2', 0) if is_y_axis else calc_obj['geom'].get('drop_w1', 0)) * 100.0
        drop_trans_cm = (calc_obj['geom'].get('drop_w1', 0) if is_y_axis else calc_obj['geom'].get('drop_w2', 0)) * 100.0
        
        # 🌟 คำนวณคุณสมบัติหน้าตัดวิกฤตตามหลักกลศาสตร์อย่างถูกต้อง (Rigorous Mechanics)
        if col_loc == "Corner":
            b1 = c_span_cm + (d_shear_cm / 2.0)  # ด้านขนานแกนพิจารณา (2 ด้านเปิด)
            b2 = c_trans_cm + (d_shear_cm / 2.0) # ด้านตั้งฉาก
            bo_cm = b1 + b2
            
            # Centroid จากขอบนอกเสา
            c_g = (b1**2) / (2 * (b1 + b2)) if (b1 + b2) > 0 else b1 / 2.0
            c_dist = b1 - c_g # ระยะไปถึงขอบหน้าตัดวิกฤตที่รับ Stress สูงสุด
            
            # Exact Jc สำหรับเสามุม (2-sided)
            Jc = ((d_shear_cm * (b1**3)) / 12.0) + (b1 * d_shear_cm * (b1/2.0 - c_g)**2) + (b2 * d_shear_cm * c_g**2) + (bo_cm * (d_shear_cm**3) / 12.0)
            eq_bo = fr"b_o = ({c_span_label} + d/2) + ({c_trans_label} + d/2)"
            
        elif col_loc == "Edge":
            b1 = c_span_cm + (d_shear_cm / 2.0)  # ด้านที่พุ่งจากขอบตึกเข้าหาข้างใน
            b2 = c_trans_cm + d_shear_cm         # ด้านที่ขนานกับขอบตึก
            bo_cm = (2 * b1) + b2
            
            # Centroid จากขอบนอกตึก
            c_g = (b1**2) / ((2 * b1) + b2) if ((2 * b1) + b2) > 0 else b1 / 2.0
            c_dist = b1 - c_g # ระยะไปถึงขอบในที่รับแรงตึงสูงสุด
            
            # Exact Jc สำหรับเสาขอบ (3-sided) ด้วย Parallel Axis Theorem
            Jc = 2 * (((d_shear_cm * (b1**3)) / 12.0) + (b1 * d_shear_cm * (b1/2.0 - c_g)**2)) + (b2 * d_shear_cm * c_g**2) + (bo_cm * (d_shear_cm**3) / 12.0)
            eq_bo = fr"b_o = 2({c_span_label} + d/2) + ({c_trans_label} + d)"
            
        else: # Interior Column
            b1 = c_span_cm + d_shear_cm
            b2 = c_trans_cm + d_shear_cm
            bo_cm = 2 * (b1 + b2)
            c_g = b1 / 2.0
            c_dist = b1 / 2.0
            
            # Exact Jc สำหรับเสาภายใน (4-sided)
            Jc = (d_shear_cm * (b1**3) / 6.0) + (b1 * (d_shear_cm**3) / 6.0) + (d_shear_cm * (b1**2) * b2 / 2.0)
            eq_bo = fr"b_o = 2[({c_span_label} + d) + ({c_trans_label} + d)]"

        Ac = bo_cm * d_shear_cm

        # --- ส่วนแสดงผล UI แบ่งคอลัมน์และวาดรูปภาพประกอบเพื่อความชัดเจน ---
        col_left, col_right = st.columns([1.1, 0.9])
        
        with col_left:
            st.markdown(f"##### 📐 1.1 รูปเรขาคณิตและคุณสมบัติหน้าตัดวิกฤต")
            st.latex(eq_bo)
            st.latex(f"b_o = {bo_cm:.1f} \\text{{ cm}}")
            st.latex(f"A_c = b_o \\times d = {bo_cm:.1f} \\times {d_shear_cm:.1f} = {Ac:,.1f} \\text{{ cm}}^2")
            st.latex(f"J_c = {Jc:,.0f} \\text{{ cm}}^4 \\quad (c = {c_dist:.1f} \\text{{ cm}})")
            
            st.markdown(f"**รายละเอียดสัดส่วนหน้าตัด:**")
            st.markdown(f"- ความลึกประสิทธิผลเฉือน ($d$): `{d_shear_cm:.2f} cm`")
            st.markdown(f"- ขนาดหน้าตัดวิกฤต: $b_1$ (แนวสแปน) = `{b1:.1f} cm`, $b_2$ (แนวตั้งฉาก) = `{b2:.1f} cm`")
        
        with col_right:
            # 🎨 ส่วนวาดรูปไดอะแกรมหน้าตัดวิกฤต (Critical Section Visualizer) แบบ Real-time
            fig, ax = plt.subplots(figsize=(4, 3.5))
            # วาดเสา (Column) เป็นสีเทาเข้ม เขยิบตามชนิดของเสา
            if col_loc == "Interior":
                ax.add_patch(patches.Rectangle((-c_span_cm/2, -c_trans_cm/2), c_span_cm, c_trans_cm, color='#34495E', label='Column'))
                ax.plot([-b1/2, b1/2, b1/2, -b1/2, -b1/2], [-b2/2, -b2/2, b2/2, b2/2, -b2/2], color='red', linestyle='--', lw=2, label='Critical Perimeter ($b_o$)')
            elif col_loc == "Edge":
                ax.add_patch(patches.Rectangle((-c_span_cm, -c_trans_cm/2), c_span_cm, c_trans_cm, color='#34495E', label='Column'))
                ax.plot([-b1, 0, 0, -b1], [b2/2, b2/2, -b2/2, -b2/2], color='red', linestyle='--', lw=2, label='$b_o$ (3-Sides)')
                ax.axvline(0, color='gray', lw=2, linestyle='-', alpha=0.7) # ขอบตึก
            elif col_loc == "Corner":
                ax.add_patch(patches.Rectangle((-c_span_cm, -c_trans_cm), c_span_cm, c_trans_cm, color='#34495E', label='Column'))
                ax.plot([-b1, 0, 0], [0, 0, -b2], color='red', linestyle='--', lw=2, label='$b_o$ (2-Sides)')
                ax.axvline(0, color='gray', lw=1.5); ax.axhline(0, color='gray', lw=1.5) # ขอบมุมตึก
            
            ax.set_aspect('equal', 'box')
            ax.axis('off')
            ax.legend(loc='upper right', fontsize=7)
            st.pyplot(fig)

        if has_drop and drop_span_cm > 0 and drop_trans_cm > 0:
            d_slab_cm = (calc_obj['geom']['h_s'] * 100.0) - (cc_m * 100.0) - (selected_rebar / 20.0) 
            if col_loc == "Corner": bo_drop = (drop_span_cm + d_slab_cm/2.0) + (drop_trans_cm + d_slab_cm/2.0)
            elif col_loc == "Edge": bo_drop = 2*(drop_span_cm + d_slab_cm/2.0) + (drop_trans_cm + d_slab_cm)
            else: bo_drop = 2 * ((drop_span_cm + d_slab_cm) + (drop_trans_cm + d_slab_cm))
            st.info(f"💡 **Drop Panel Control Perimeter ($b_{{o,drop}}$):** `{bo_drop:.1f} cm` (หน้าตัดวิกฤตนอกแผงดรอปเพื่อตรวจสอบความหนาพื้นหลัก)")

        st.divider()
        
        # --- 2. Demand Calculation (Vu and Munbal) ---
        st.markdown("##### 📈 1.2 แรงกระทำและความเค้นเฉือนสูงสุด ($v_{u,max}$)")
        
        col_v1, col_v2 = st.columns([1, 1])
        
        with col_v1:
            if col_loc == "Corner":
                trib_area = (L1 / 2.0) * (L2 / 2.0)
                punched_area = (c1 + d_eff_m/2.0) * (c2 + d_eff_m/2.0)
            elif col_loc == "Edge":
                trib_area = (L1 / 2.0) * L2
                punched_area = (c1 + d_eff_m/2.0) * (c2 + d_eff_m)
            else: 
                trib_area = L1 * L2
                punched_area = (c1 + d_eff_m) * (c2 + d_eff_m)

            vu_kg = wu * (trib_area - punched_area)
            st.markdown(f"- พื้นที่รับน้ำหนักเฉือนพั้นชิ่ง ($A_{{trib}}$): `{trib_area:.2f} m²`")
            st.latex(f"V_u = w_u (A_{{trib}} - A_{{punched}}) = {vu_kg:,.0f} \\text{{ kg}}")
            
            mu_at_column = 0
            if not df_design.empty and 'Location' in df_design.columns:
                try:
                    match_int_neg = df_design[df_design['Location'].str.contains("Interior Negative|Ext Neg", case=False, na=False)].iloc[0]
                    mu_at_column = match_int_neg.get('Mu (kg-m)', match_int_neg.get('Moment (kg-m)', 0))
                except IndexError:
                    pass
            st.latex(f"M_{{unbal}} = {mu_at_column:,.0f} \\text{{ kg-m}} \\quad \\text{{(จากแนวแกน {span_label})}}")
        
        with col_v2:
            gamma_f = 1.0 / (1.0 + (2.0/3.0) * math.sqrt(b1/b2))
            gamma_v = 1.0 - gamma_f
            
            vu_direct = vu_kg / Ac
            vu_moment = (gamma_v * (mu_at_column * 100.0) * c_dist) / Jc if Jc > 0 else 0
            vu_max = vu_direct + vu_moment
            
            st.latex(fr"\gamma_v = 1 - \gamma_f = 1 - {gamma_f:.3f} = {gamma_v:.3f}")
            st.latex(fr"v_{{u,direct}} = \frac{{V_u}}{{A_c}} = {vu_direct:.2f} \text{{ kg/cm}}^2")
            st.latex(fr"v_{{u,moment}} = \frac{{\gamma_v M_{{unbal}} c}}{{J_c}} = {vu_moment:.2f} \text{{ kg/cm}}^2")
            st.markdown(f"**ความเค้นเฉือนประลัยรวมสูงสุด:** $v_{{u,max}} = {vu_direct:.2f} + {vu_moment:.2f} = \\mathbf{{{vu_max:.2f} \\text{{ ksc}}}}$")

        st.divider()
        
        # --- 3. Capacity Calculation ---
        st.markdown("##### 🛡️ 1.3 กำลังรับแรงเฉือนพั้นชิ่งของคอนกรีต ($\\phi v_c$)")
        st.caption("คำนวณตามมาตรฐาน ACI 318 ในหน่วยเมตริก (kg/cm²) โดยเลือกค่าที่น้อยที่สุดควบคุมเสถียรภาพ")
        
        phi_shear = 0.85 
        alpha_s = 40 if case_type == "Interior" else (30 if has_edge_beam else 20)
        beta_c = max(c_span, c_trans) / min(c_span, c_trans)
        
        vc1_stress = 1.06 * math.sqrt(fc_ksc)
        vc2_stress = 0.53 * (1 + (2/beta_c)) * math.sqrt(fc_ksc)
        vc3_stress = 0.27 * (2 + (alpha_s * d_shear_cm / bo_cm)) * math.sqrt(fc_ksc)
        
        vc_gov_stress = min(vc1_stress, vc2_stress, vc3_stress)
        phi_vc_stress = phi_shear * vc_gov_stress
        
        c1_vc, c2_vc, c3_vc = st.columns(3)
        c1_vc.metric("สมการพื้นฐาน (a)", f"{vc1_stress:.2f} ksc")
        c2_vc.metric("สมการสัดส่วนเสา (b)", f"{vc2_stress:.2f} ksc", f"β = {beta_c:.2f}")
        c3_vc.metric("สมการตำแหน่งเสา (c)", f"{vc3_stress:.2f} ksc", f"αs = {alpha_s}")
        
        # --- 4. Demand vs Capacity Verification ---
        st.markdown("##### 📝 1.4 การตรวจสอบความปลอดภัยสองทาง")
        if vu_max <= phi_vc_stress:
            st.success(f"✅ **ปลอดภัย (SAFE):** $v_{{u,max}}$ ({vu_max:.2f} ksc) $\\le \\phi v_c$ ({phi_vc_stress:.2f} ksc) หน้าตัดแผ่นพื้นมีความหนาเพียงพอสำหรับรับ Punching Shear")
        else:
            st.error(f"❌ **ไม่ปลอดภัย (FAIL):** $v_{{u,max}}$ ({vu_max:.2f} ksc) $> \\phi v_c$ ({phi_vc_stress:.2f} ksc) กรุณาเพิ่มความหนาพื้นแผ่น (Slab Thickness), เพิ่มกำลังคอนกรีต ($f'_c$) หรือออกแบบเหล็กเสริมรับแรงเฉือน")

        # ==========================================
        # --- PART 5.2: ONE-WAY SHEAR (BEAM ACTION) ---
        # ==========================================
        st.header("2. One-Way (Beam Action) Shear Design")
        st.caption("ตรวจสอบหน้าตัดวิกฤตแบบคานที่ระยะ $d$ จากขอบเสา โดยพิจารณาความกว้างพื้นเต็มแถบวิเคราะห์ ($b_w$)")
        
        dist_crit_m = (c_span / 2.0) + d_eff_m
        L_trib_m = max((L_span / 2.0) - dist_crit_m, 0)
        b_w_m = L_trans
        b_w_cm = b_w_m * 100.0
        
        vu_1way_kg = wu * b_w_m * L_trib_m
        vc_1way_kg = 0.53 * math.sqrt(fc_ksc) * b_w_cm * d_shear_cm
        phi_vc_1way = 0.75 * vc_1way_kg
        
        c1_1w, c2_1w = st.columns(2)
        with c1_1w:
            st.markdown("**ความต้องการแรงเฉือน (Demand)**")
            st.markdown(f"- ระยะหน้าตัดวิกฤต (จากศูนย์กลางเสา): ${c_span_label}/2 + d = {dist_crit_m:.2f} \\text{{ m}}$")
            st.markdown(f"- ความยาวรับน้ำหนัก (Tributary Length): `{L_trib_m:.2f} m` (ความกว้าง $b_w = {b_w_m:.2f} \\text{{ m}}$)")
            st.latex(f"V_{{u,1way}} = w_u \\times b_w \\times L_{{trib}} = {vu_1way_kg:,.0f} \\text{{ kg}}")
        with c2_1w:
            st.markdown("**กำลังการรับแรงเฉือน (Capacity)**")
            st.latex(f"V_c = 0.53 \\sqrt{{f'_c}} b_w d = {vc_1way_kg:,.0f} \\text{{ kg}}")
            st.latex(f"\\phi V_{{c,1way}} = 0.75 \\times V_c = {phi_vc_1way:,.0f} \\text{{ kg}}")
            
        st.markdown("##### 📝 2.1 การตรวจสอบความปลอดภัยทิศทางเดียว")
        if vu_1way_kg <= phi_vc_1way:
            st.success(f"✅ **ปลอดภัย (SAFE):** $V_{{u,1way}}$ ({vu_1way_kg:,.0f} kg) $\\le \\phi V_{{c,1way}}$ ({phi_vc_1way:,.0f} kg)")
        else:
            st.error(f"❌ **ไม่ปลอดภัย (FAIL):** $V_{{u,1way}}$ ({vu_1way_kg:,.0f} kg) $> \\phi V_{{c,1way}}$ ({phi_vc_1way:,.0f} kg) ต้องขยายความหนาแผ่นพื้น")
    
    with tab_viz:
        st.markdown("#### 🎨 Detailed Engineering Drawings")
        st.markdown("Reinforcement detailing drawings based on physical proportions and ACI 318 specifications.")
        
        if 'viz_ddm' in sys.modules or 'viz_ddm' in globals():
            try:
                # --- Row 1: Reinforcement Plan View ---
                st.markdown("##### 1. Reinforcement Plan View (Top View)")
                if edited_df is not None and not edited_df.empty:
                    fig_plan = viz_ddm.draw_rebar_plan_view(inputs, edited_df)
                    st.pyplot(fig_plan)
                else:
                    st.warning("⚠️ No reinforcement data available to generate the plan view.")
                
                st.divider()
                
                # --- Row 2: Cross-Section and Punching Shear Details ---
                col_viz1, col_viz2 = st.columns(2)
                
                with col_viz1:
                    st.markdown("##### 2. Cross-Section Details")
                    if edited_df is not None and not edited_df.empty:
                        fig_sec = viz_ddm.draw_slab_section_with_rebar(inputs, edited_df)
                        st.pyplot(fig_sec)
                    else:
                        st.warning("⚠️ No reinforcement data available to generate the section details.")
                        
                with col_viz2:
                    st.markdown(f"##### 3. Punching Shear Perimeter ({col_loc} Column)")
                    fig_punch = viz_ddm.draw_punching_plan(col_loc, c1_cm, c2_cm, d_shear_cm)
                    st.pyplot(fig_punch)
                    
            except Exception as e:
                st.error(f"🚨 An error occurred while generating the drawings: {e}")
                
        else:
            st.error("❌ Unable to load the visualization module. Please ensure `viz_ddm.py` is correctly imported.")
