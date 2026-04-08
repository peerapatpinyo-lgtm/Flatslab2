# app_ddm.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("🏗️ Direct Design Method (DDM) Analysis")
    st.markdown("---")

    # ==========================================================================
    # 1. DATA ADAPTER (Safe Extraction & Unit Match)
    # ==========================================================================
    try:
        geom = calc_obj.get('geom', {})
        # ดึง L1, L2, Ln จาก geom (หน่วยเป็นเมตรทั้งหมด)
        L1 = geom.get('L1', 6.0)
        L2 = geom.get('L2', 6.0)
        ln = geom.get('Ln', L1)
        c1 = geom.get('c1', 0.5)
        c2 = geom.get('c2', 0.5)
        
        # 🚨 BUG FIX: แปลงความหนาจากเมตรกลับเป็น เซนติเมตร (cm) ให้ calc_ddm.py
        h_slab_m = geom.get('h_s', 0.20)
        h_drop_m = geom.get('h_d', h_slab_m)
        h_slab = h_slab_m * 100 
        h_drop = h_drop_m * 100 
        has_drop = h_drop > h_slab
        
        edge_beam = geom.get('edge_beam_params', {})
        has_edge_beam = edge_beam.get('has_beam', False)
        eb_width = edge_beam.get('width_cm', 0) / 100.0
        eb_depth = edge_beam.get('depth_cm', 0) / 100.0
        
        # อนุมานเคสของเสา (หากมีคานขอบ ให้ถือเป็น Exterior)
        case_type = "Exterior" if has_edge_beam else "Interior"
        
        mat = calc_obj.get('mat', {})
        # 🚨 BUG FIX: แปลงหน่วยกำลังจาก Pascal (Pa) กลับเป็น ksc
        KSC_TO_PA = 98066.5
        fc = mat.get('fc_pa', 240 * KSC_TO_PA) / KSC_TO_PA
        fy = mat.get('fy_pa', 4000 * KSC_TO_PA) / KSC_TO_PA

        loads = calc_obj.get('loads', {})
        G = 9.80665
        # 🚨 BUG FIX: แปลงหน่วย Load จาก Pascal (N/m2) เป็น kg/m2
        wu = loads.get('wu_pa', 0) / G
        dl = loads.get('w_dead', 0) / G
        # ประมาณค่า LL กลับมาเพื่อใช้เช็คเงื่อนไข ACI
        ll = (wu - 1.4 * dl) / 1.7 if wu > 0 else 300

        # ✨ [เพิ่มโค้ดส่วนนี้ 1] สร้างตัวเลือกขนาดเหล็กเสริม ✨
        st.markdown("### ⚙️ Rebar Settings (ตั้งค่าเหล็กเสริม)")
        selected_rebar = st.selectbox(
            "เลือกขนาดเหล็กเสริมหลัก (mm):", 
            options=[10, 12, 16, 20, 25], 
            index=1, # ค่า Default คือ Index 1 (DB12)
            format_func=lambda x: f"DB{x}" # ทำให้แสดงผลเป็น DB12, DB16 แทนที่จะเป็นเลขโดดๆ
        )

        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln, 'c1': c1, 'c2': c2,
            'wu': wu, 'dl': dl, 'll': ll,
            'h_slab': h_slab, 'h_drop': h_drop, 'has_drop': has_drop,
            'fc': fc, 'fy': fy, 'case_type': case_type, 
            'has_edge_beam': has_edge_beam,
            'eb_width': eb_width, 'eb_depth': eb_depth,
            'rebar_size': selected_rebar  # ✨ [เพิ่มโค้ดส่วนนี้ 2] ส่งค่าขนาดเหล็กไปให้ calc_ddm.py ✨
        }
    except Exception as e:
        st.error(f"⚠️ Input Data Missing: {e}")
        return


    # ==========================================================================
    # 1.5 DDM LIMITATIONS CHECK
    # ==========================================================================
    st.subheader("🔍 ACI 318 DDM Constraints Check")
    col1, col2 = st.columns(2)
    
    is_load_ok = ll <= 2 * dl
    col1.info(f"**Load Ratio Check:**\n\nLive Load ({ll:.0f} kg/m²) ≤ 2 × Dead Load ({2*dl:.0f} kg/m²)\n\n**Status:** {'✅ OK' if is_load_ok else '❌ Exceeds Limit'}")
    
    is_span_ok = ln >= 0.65 * L1
    col2.info(f"**Clear Span Check:**\n\nLn ({ln:.2f} m) ≥ 0.65 × L1 ({0.65*L1:.2f} m)\n\n**Status:** {'✅ OK' if is_span_ok else '⚠️ Modified Ln required'}")

    # ==========================================================================
    # 2. CALCULATION
    # ==========================================================================
    # 🚨 อัปเดตให้รับค่าตัวที่ 4 (details) มาด้วย
    df_results, Mo, warning_msgs, details = calc_ddm.calculate_ddm(ddm_inputs)

    # --- Display Metrics ---
    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("Design Load (Wu)", f"{wu:,.0f} kg/m²")
    m2.metric("Total Static Moment (Mo)", f"{Mo:,.2f} kg-m")

    # แสดงข้อความแจ้งเตือน (Warning & Safety Errors)
    if warning_msgs:
        for msg in warning_msgs: 
            if "🚨" in msg or "❌" in msg:
                st.error(msg)
            else:
                st.warning(msg)

    # ==========================================================================
    # 3. REBAR SCHEDULE & VISUALIZATION
    # ==========================================================================
    st.subheader("📋 Reinforcement Results")

    if not df_results.empty and 'Location' in df_results.columns:
        st.dataframe(df_results, use_container_width=True)

        if 'As Req (cm²)' in df_results.columns:
            st.subheader("📊 Steel Area Distribution")
            fig, ax = plt.subplots(figsize=(10, 4))
            
            locations = df_results['Location']
            as_req = df_results['As Req (cm²)']
            
            bars = ax.bar(locations, as_req, color='#1f77b4')
            ax.set_ylabel("As Required (sq.cm)")
            plt.xticks(rotation=15)
            
            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, round(yval, 2), ha='center')
            
            st.pyplot(fig)
    else:
        st.error("❌ ไม่สามารถแสดงผลการคำนวณได้ เนื่องจากข้อมูลไม่ครบถ้วน หรือหน้าตัดไม่เพียงพอ")
        st.info("💡 ข้อสังเกต: ตรวจสอบความลึกหน้าตัดและหน่วยอีกครั้ง")

    # ==========================================================================
    # 4. CALCULATION STEPS & DETAILS (EXPANDER)
    # ==========================================================================
    st.markdown("---")
    with st.expander("📝 ดูขั้นตอนการคำนวณและตรวจสอบข้อกำหนด (Calculation & Safety Checks)"):
        st.markdown("### 🛡️ การตรวจสอบด้านความปลอดภัย (Safety Checks)")
        st.markdown(f"**1. ตรวจสอบ Punching Shear (แรงเฉือนทะลุ):** {details.get('punch_status', 'ข้อมูลไม่เพียงพอ')}")
        st.latex(details.get('punch_step', ''))
        
        st.markdown("**2. ตรวจสอบการแอ่นตัว (Minimum Thickness):**")
        st.latex(details.get('h_min_step', ''))
        
        st.markdown("---")
        st.markdown("### 📊 การกระจายโมเมนต์ (Moment Distribution)")
        st.markdown("**1. โมเมนต์สถิตรวม (Total Static Moment)**")
        st.latex(details.get('Mo_step', ''))
        
        st.markdown("**2. สติฟเนสแรงบิด (Torsional Stiffness, $\\beta_t$)**")
        st.latex(details.get('beta_t_step', ''))
        st.markdown(f"**สัดส่วนโมเมนต์ลบขอบนอกที่เข้า Column Strip:** `{details.get('cs_ext_pct', 100):.1f}%`")

        st.markdown("---")
        st.markdown("### 💡 สมการออกแบบเหล็กเสริม (Flexural Design)")
        st.markdown("โปรแกรมใช้สมการของ ACI 318 ในการคำนวณหาปริมาณเหล็กเสริมดังนี้:")
        st.latex(r"R_n = \frac{M_u}{\phi b d^2}")
        st.latex(r"\rho = \frac{0.85 f'_c}{f_y} \left( 1 - \sqrt{1 - \frac{2 R_n}{0.85 f'_c}} \right)")
        st.latex(r"A_{s,req} = \rho b d \geq A_{s,min}")

    st.markdown("---")
