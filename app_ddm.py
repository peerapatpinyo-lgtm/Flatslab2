import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("🏗️ Direct Design Method (DDM) Analysis")
    st.markdown("---")

    # ==========================================================================
    # 1. DATA ADAPTER (Safe Extraction)
    # ==========================================================================
    try:
        geom = calc_obj.get('geom', {})
        L1 = geom.get('L1_l', 6.0) if geom.get('L1_l', 0) > 0.1 else geom.get('L1_r', 6.0)
        L2 = geom.get('L2', 6.0)
        h_slab = geom.get('h_slab', 0.20)
        has_drop = geom.get('has_drop', False)
        h_drop = geom.get('h_drop', h_slab)
        
        col_data = calc_obj.get('col_size', {})
        c1 = col_data.get('c1', 50) / 100.0
        c2 = col_data.get('c2', 50) / 100.0
        ln = L1 - c1
        
        case_type = "Exterior" if geom.get('L1_l', 1.0) <= 0.01 else "Interior"
        
        # ดึงข้อมูลคานขอบแบบละเอียด (แปลงเป็นเมตร)
        edge_beam = calc_obj.get('edge_beam', {})
        has_edge_beam = edge_beam.get('has_beam', False)
        eb_width = edge_beam.get('width_cm', 0) / 100.0
        eb_depth = edge_beam.get('depth_cm', 0) / 100.0
        
        mat = calc_obj.get('mat', {})
        fc = mat.get('fc', 240)
        fy_val = str(mat.get('fy', "4000"))
        fy = 3000 if "30" in fy_val else (5000 if "50" in fy_val else 4000)

        # ดึงโหลดแยกประเภทเพื่อใช้ตรวจสอบเงื่อนไข DDM
        loads = calc_obj.get('loads', {})
        # ใช้ Load Factor ปัจจุบัน 1.2 DL + 1.6 LL
        dl = loads.get('w_dead', 2400 * h_slab)
        ll = loads.get('LL', 300)
        wu = (1.2 * dl) + (1.6 * ll)
        
        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln, 'c1': c1, 'c2': c2,
            'wu': wu, 'dl': dl, 'll': ll,
            'h_slab': h_slab, 'h_drop': h_drop, 'has_drop': has_drop,
            'fc': fc, 'fy': fy, 'case_type': case_type, 
            'has_edge_beam': has_edge_beam,
            'eb_width': eb_width, 'eb_depth': eb_depth
        }
    except Exception as e:
        st.error(f"⚠️ Input Data Missing: {e}")
        return

    # ==========================================================================
    # 1.5 DDM LIMITATIONS CHECK
    # ==========================================================================
    st.subheader("🔍 ACI 318 DDM Constraints Check")
    col1, col2 = st.columns(2)
    
    # Check 1: LL <= 2*DL
    is_load_ok = ll <= 2 * dl
    col1.info(f"**Load Ratio Check:**\n\nLive Load ({ll} kg/m²) ≤ 2 × Dead Load ({2*dl} kg/m²)\n\n**Status:** {'✅ OK' if is_load_ok else '❌ Exceeds Limit (Requires EFM)'}")
    
    # Check 2: Ln >= 0.65 L1
    is_span_ok = ln >= 0.65 * L1
    col2.info(f"**Clear Span Check:**\n\nLn ({ln:.2f} m) ≥ 0.65 × L1 ({0.65*L1:.2f} m)\n\n**Status:** {'✅ OK' if is_span_ok else '⚠️ Modified Ln required in calculation'}")

    # ==========================================================================
    # 2. CALCULATION
    # ==========================================================================
    df_results, Mo, warning_msgs = calc_ddm.calculate_ddm(ddm_inputs)

    # --- Display Metrics ---
    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("Design Load (Wu)", f"{wu:,.0f} kg/m²")
    m2.metric("Total Static Moment (Mo)", f"{Mo:,.2f} kg-m")

    if warning_msgs:
        for msg in warning_msgs: st.warning(msg)

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
        st.info("กรุณาตรวจสอบความหนาพื้น (Slab Thickness) หรือขนาดเสาอีกครั้ง")

    st.markdown("---")
