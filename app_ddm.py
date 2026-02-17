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
        ln = L1 - c1
        
        case_type = "Exterior" if geom.get('L1_l', 1.0) <= 0.01 else "Interior"
        has_edge_beam = calc_obj.get('edge_beam', {}).get('has_beam', False)
        
        mat = calc_obj.get('mat', {})
        fc = mat.get('fc', 240)
        fy = 4000 # Default
        fy_val = str(mat.get('fy', "4000"))
        if "30" in fy_val: fy = 3000
        elif "50" in fy_val: fy = 5000

        loads = calc_obj.get('loads', {})
        wu = (1.4 * loads.get('w_dead', 2400*h_slab)) + (1.7 * loads.get('LL', 300))
        
        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln, 'wu': wu,
            'h_slab': h_slab, 'h_drop': h_drop, 'has_drop': has_drop,
            'fc': fc, 'fy': fy, 'case_type': case_type, 'has_edge_beam': has_edge_beam
        }
    except Exception as e:
        st.error(f"⚠️ Input Data Missing: {e}")
        return

    # ==========================================================================
    # 2. CALCULATION
    # ==========================================================================
    df_results, Mo, warning_msgs = calc_ddm.calculate_ddm(ddm_inputs)

    # --- Display Metrics ---
    m1, m2 = st.columns(2)
    m2.metric("Total Static Moment (Mo)", f"{Mo:,.2f} kg-m")
    m1.metric("Design Load (Wu)", f"{wu:,.0f} kg/m²")

    if warning_msgs:
        for msg in warning_msgs: st.warning(msg)

    # ==========================================================================
    # 3. REBAR SCHEDULE & VISUALIZATION (Fixed Section)
    # ==========================================================================
    st.subheader("📋 Reinforcement Results")

    # ตรวจสอบว่า DataFrame มีข้อมูลและมี Column ที่ต้องการหรือไม่
    if not df_results.empty and 'Location' in df_results.columns:
        
        # แสดงตาราง
        st.dataframe(df_results, use_container_width=True)

        # ส่วนของกราฟ: เพิ่มการตรวจสอบ 'As Req (cm²)' ด้วย
        if 'As Req (cm²)' in df_results.columns:
            st.subheader("📊 Steel Area Distribution")
            fig, ax = plt.subplots(figsize=(10, 4))
            
            # ดึงข้อมูลมาวาดกราฟ
            locations = df_results['Location']
            as_req = df_results['As Req (cm²)']
            
            bars = ax.bar(locations, as_req, color='#1f77b4')
            ax.set_ylabel("As Required (sq.cm)")
            plt.xticks(rotation=15)
            
            # ใส่ตัวเลขบนหัวแท่งกราฟ
            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, round(yval, 2), ha='center')
            
            st.pyplot(fig)
    else:
        st.error("❌ ไม่สามารถแสดงผลการคำนวณได้ เนื่องจากข้อมูลไม่ครบถ้วน หรือหน้าตัดไม่เพียงพอ")
        st.info("กรุณาตรวจสอบความหนาพื้น (Slab Thickness) หรือขนาดเสาอีกครั้ง")

    st.markdown("---")
