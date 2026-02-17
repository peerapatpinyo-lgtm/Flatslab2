import streamlit as st
import pandas as pd
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("🏗️ Direct Design Method (DDM) Analysis")
    
    # --- 1. DATA ADAPTER ---
    try:
        # > Geometry
        geom = calc_obj.get('geom', {})
        L1 = geom.get('L1_l', 6.0)
        # ตรวจสอบว่าถ้า L1 ด้านซ้ายเป็น 0 (Edge Column) ให้ใช้ L1 ด้านขวาแทน
        if L1 < 0.1: 
            L1 = geom.get('L1_r', 6.0) 
            
        L2 = geom.get('L2', 6.0)
        
        h_slab = geom.get('h_slab', 0.20)
        h_drop = geom.get('h_drop', h_slab)
        has_drop = geom.get('has_drop', False)
        
        # > Column & Location Logic
        col_data = calc_obj.get('col_size', {})
        c1 = col_data.get('c1', 50)/100.0
        ln = L1 - c1 # Clear Span
        
        # Default Case Type
        case_type = "Interior"
        
        # Logic: ถ้า Span ด้านซ้ายเป็น 0 แสดงว่าเป็น Edge Column -> Exterior Case
        if geom.get('L1_l', 1.0) <= 0.01:
            case_type = "Exterior"
        
        # > Edge Beam
        edge_params = calc_obj.get('edge_beam', {})
        has_edge_beam = edge_params.get('has_beam', False)
        
        # > Material & Loads
        mat = calc_obj.get('mat', {})
        fc = mat.get('fc', 240)
        
        # Handle Fy (String to Float)
        fy_input = mat.get('fy', "4000")
        fy_str = str(fy_input)
        if "30" in fy_str: fy = 3000
        elif "50" in fy_str: fy = 5000
        else: fy = 4000
        
        # Load Recalc (Robustness)
        loads = calc_obj.get('loads', {})
        w_dead = loads.get('w_dead', 2400*h_slab)
        w_live = loads.get('LL', 300)
        wu = 1.4*w_dead + 1.7*w_live
        
        # Package for Engine
        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln, 'wu': wu,
            'h_slab': h_slab, 'h_drop': h_drop, 'has_drop': has_drop,
            'fc': fc, 'fy': fy,
            'case_type': case_type, 
            'has_edge_beam': has_edge_beam
        }

    except Exception as e:
        st.error(f"⚠️ Data Error: {e}")
        return

    # --- 2. DISPLAY CONFIGURATION ---
    st.info(f"""
    **Analysis Configuration:**
    - **Panel Type:** `{case_type} Span`
    - **Drop Panel:** `{'✅ Yes' if has_drop else '❌ No'}` 
    - **Edge Beam:** `{'✅ Yes' if has_edge_beam else '❌ No'}`
    """)

    # --- 3. CALCULATION (บรรทัดนี้คือจุดที่แก้ครับ) ---
    # รับค่า 3 ตัว: DataFrame, Moment, และ ErrorMessages
    df, Mo, errors = calc_ddm.calculate_ddm(ddm_inputs)

    # แสดง Error ถ้ามี (เช่น Section รับแรงไม่ไหว)
    if errors:
        for err in errors: st.warning(err)
        
    # --- 4. RESULTS ---
    c1, c2 = st.columns(2)
    c1.metric("Static Moment (Mo)", f"{Mo:,.2f} kg-m")
    c2.metric("Factored Load (Wu)", f"{wu:.0f} kg/m²")

    st.subheader("📋 Reinforcement Results")
    
    if has_drop:
        st.caption("ℹ️ *Column Strip Negative moments use Drop Panel thickness for 'd'.*")
    
    # แสดงตารางผลลัพธ์
    st.dataframe(
        df.style.format({
            "Moment (kg-m)": "{:,.2f}",
            "As Req (cm²)": "{:.2f}"
        }),
        use_container_width=True
    )
    
    # --- 5. INTERPRETATION ---
    if not df.empty:
        # เช็คว่ามีคำว่า Fail ในคอลัมน์ Status หรือไม่
        if 'Status' in df.columns and df['Status'].str.contains('Fail').any():
             st.error("❌ **Design FAILED:** Some sections are too thin. Please increase thickness or concrete strength.")
        else:
             st.success("✅ **Design Passed:** All sections are adequate.")
