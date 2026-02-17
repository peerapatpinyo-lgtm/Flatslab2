import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import calc_ddm  # ต้องแน่ใจว่าไฟล์ calc_ddm.py อยู่ในโฟลเดอร์เดียวกัน

def render_ddm_tab(calc_obj):
    """
    Render Direct Design Method (DDM) Analysis Tab
    High-End UI Version with Visualization & Error Handling
    """
    st.header("🏗️ Direct Design Method (DDM) Analysis")
    st.markdown("---")

    # ==========================================================================
    # 1. DATA ADAPTER (แปลงข้อมูลจาก app.py เข้าสู่ระบบคำนวณ)
    # ==========================================================================
    try:
        # --- Geometry ---
        geom = calc_obj.get('geom', {})
        L1_l = geom.get('L1_l', 6.0)
        L1_r = geom.get('L1_r', 6.0)
        
        # Logic: ถ้า L1 ซ้ายเป็น 0 (Edge Column) ให้ใช้ L1 ขวาเป็น Span หลักแทน
        if L1_l < 0.1:
            L1 = L1_r
            default_case = "Exterior" # สันนิษฐานว่าเป็นขอบนอก
        else:
            L1 = L1_l
            default_case = "Interior" # สันนิษฐานว่าเป็นภายใน

        L2 = geom.get('L2', 6.0)
        h_slab = geom.get('h_slab', 0.20)
        
        # --- Drop Panel ---
        has_drop = geom.get('has_drop', False)
        h_drop = geom.get('h_drop', h_slab)
        
        # --- Column Size ---
        col_data = calc_obj.get('col_size', {})
        c1 = col_data.get('c1', 50) / 100.0
        ln = L1 - c1  # Clear Span (L_n)
        
        # --- Edge Conditions ---
        # พยายามดึงค่า Location ที่แม่นยำที่สุด
        # ถ้าไม่มีส่งมา ให้ใช้ Logic default_case ด้านบน
        final_case_type = default_case 
        
        # ตรวจสอบว่ามี Edge Beam หรือไม่
        edge_params = calc_obj.get('edge_beam', {})
        has_edge_beam = edge_params.get('has_beam', False)
        
        # --- Materials ---
        mat = calc_obj.get('mat', {})
        fc = mat.get('fc', 240)
        
        # แปลง Fy จาก String (เช่น "SD40") เป็นตัวเลข
        fy_input = mat.get('fy', "4000")
        fy_str = str(fy_input)
        if "30" in fy_str: fy = 3000
        elif "50" in fy_str: fy = 5000
        else: fy = 4000
        
        # --- Loads ---
        loads = calc_obj.get('loads', {})
        # คำนวณ Wu ใหม่เพื่อความชัวร์ (1.4DL + 1.7LL)
        # ถ้าไม่มีข้อมูล ให้ใช้ค่า Default โดยประมาณ
        w_dead = loads.get('w_dead', 2400 * h_slab)
        w_live = loads.get('LL', 300)
        lf_dl = loads.get('lf_dl', 1.4)
        lf_ll = loads.get('lf_ll', 1.7)
        wu = (lf_dl * w_dead) + (lf_ll * w_live)
        
        # --- Packaging Inputs ---
        ddm_inputs = {
            'l1': L1, 
            'l2': L2, 
            'ln': ln, 
            'wu': wu,
            'h_slab': h_slab, 
            'h_drop': h_drop, 
            'has_drop': has_drop,
            'fc': fc, 
            'fy': fy,
            'case_type': final_case_type, 
            'has_edge_beam': has_edge_beam
        }

    except Exception as e:
        st.error(f"❌ **Data Preparation Error:** {e}")
        st.write("Debug Data:", calc_obj)
        return

    # ==========================================================================
    # 2. CALCULATION ENGINE
    # ==========================================================================
    # เรียกใช้ฟังก์ชันคำนวณจาก calc_ddm.py
    # คืนค่ากลับมา 3 ตัวแปร: ตารางผลลัพธ์, โมเมนต์รวม, และรายการแจ้งเตือน
    df_results, Mo, warning_msgs = calc_ddm.calculate_ddm(ddm_inputs)

    # ==========================================================================
    # 3. DASHBOARD DISPLAY
    # ==========================================================================
    
    # --- A. Configuration Summary ---
    with st.expander("⚙️ Analysis Settings & Inputs", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Panel Type:** {final_case_type}")
        c1.write(f"**Clear Span ($L_n$):** {ln:.2f} m")
        
        c2.write(f"**Slab Thickness:** {h_slab*100:.0f} cm")
        drop_txt = f"{h_drop*100:.0f} cm" if has_drop else "None"
        c2.write(f"**Drop Panel:** {drop_txt}")
        
        beam_txt = "Yes" if has_edge_beam else "No"
        c3.write(f"**Edge Beam:** {beam_txt}")
        c3.write(f"**Load ($w_u$):** {wu:.0f} kg/m²")

    # --- B. Key Metrics ---
    st.subheader("1. Static Moment & Load")
    m1, m2, m3 = st.columns(3)
    
    m1.metric(
        label="Total Static Moment ($M_o$)",
        value=f"{Mo:,.2f} kg-m",
        delta="ACI 318 Limit",
        delta_color="off"
    )
    
    m2.metric(
        label="Design Load ($w_u$)",
        value=f"{wu:,.0f} kg/m²",
        help="1.4DL + 1.7LL"
    )
    
    status_text = "✅ PASS"
    status_color = "normal"
    if warning_msgs:
        status_text = "⚠️ WARNING"
        status_color = "inverse"
        
    m3.metric(
        label="Design Status",
        value=status_text,
        delta_color=status_color
    )

    # --- C. Warning Messages ---
    if warning_msgs:
        st.warning("### ⚠️ Design Warnings Detected")
        for msg in warning_msgs:
            st.write(f"- {msg}")
        st.markdown("---")

    # --- D. Main Results Table ---
    st.subheader("2. Reinforcement Schedule")
    
    if not df_results.empty:
        # Styling Function for Pandas
        def highlight_status(val):
            color = ''
            if 'Fail' in str(val):
                color = 'background-color: #ffcccc; color: red; font-weight: bold'
            elif 'Min Steel' in str(val):
                color = 'background-color: #ffffe0; color: #b38600'
            return color

        # Display Dataframe with Style
        st.dataframe(
            df_results.style
            .format({
                "Moment (kg-m)": "{:,.2f}",
                "As Req (cm²)": "{:.2f}",
            })
            .applymap(highlight_status, subset=['Status']),
            use_container_width=True,
            height=300
        )
        
        st.caption("""
        **Note:** - **Min Steel:** เหล็กเสริมขั้นต่ำตามมาตรฐาน ($A_{s,min} = 0.0018bh$)
        - **Fail:** หน้าตัดรับแรงไม่ไหว (ความหนาพื้นน้อยเกินไป หรือคอนกรีตกำลังต่ำเกินไป)
        """)
    else:
        st.info("No calculation results available.")

    # --- E. Visualization (Chart) ---
    st.subheader("3. Rebar Distribution Visualization")
    
    if not df_results.empty:
        # Create Bar Chart using Matplotlib
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Prepare Data
        locations = df_results['Location']
        as_req = df_results['As Req (cm²)']
        
        # Plot
        bars = ax.bar(locations, as_req, color='#4c72b0', zorder=3)
        
        # Formatting
        ax.set_ylabel("Required Steel Area ($cm^2$)")
        ax.set_title("Required Rebar by Location ($A_s$)")
        ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
        plt.xticks(rotation=45, ha='right')
        
        # Add Value Labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
        
        # Render in Streamlit
        st.pyplot(fig)
        
    st.markdown("---")
    st.success("✅ **Direct Design Method Analysis Complete**")
