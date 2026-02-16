# app_efm.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def render_efm_tab(calc_obj):
    st.header("2️⃣ Equivalent Frame Method (EFM)")
    st.info("💡 วิธี EFM จำลองโครงสร้างเป็น 'โครงข้อแข็ง' โดยคำนึงถึงความแข็งของเสา (Kcol) และพื้น (Kslab) เพื่อหาโมเมนต์จริง")

    # 1. Stiffness Parameters
    st.markdown("### 🅰️ Stiffness Properties ($K$)")
    
    k_data = calc_obj['stiffness']
    
    # Column Stiffness
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("K Column (Top)", f"{k_data['K_up']/1e6:.2f}", "MN.m")
    with col2:
        st.metric("K Column (Bot)", f"{k_data['K_lo']/1e6:.2f}", "MN.m")
    with col3:
        st.metric("Sum $\Sigma K_{col}$", f"{k_data['Sum_K']/1e6:.2f}", "MN.m")
        
    # Equivalent Stiffness (Kec) - The heart of EFM
    st.markdown("---")
    st.markdown(r"#### Equivalent Stiffness ($K_{ec}$)")
    st.latex(r"\frac{1}{K_{ec}} = \frac{1}{\Sigma K_{col}} + \frac{1}{K_t}")
    st.caption("Where $K_t$ is Torsional Stiffness of the slab-beam member")
    
    # Placeholder for Kec calculation visualization (If available in calc_obj)
    # For now, we show the concept
    st.info(f"Analysis assumes effective stiffness factor based on geometry.")

    # 2. Distribution Factors (DF)
    st.markdown("### 🅱️ Distribution Factors (DF)")
    st.write("ตัวเลขที่บ่งบอกว่า 'ใครดูดแรงไปเท่าไหร่' ณ จุดต่อ (Joint)")
    
    # Mockup DF Calculation (In real app, this comes from Kslab / (Sum K))
    # สมมติ Kslab = 4000
    K_slab = 4000 * 1e5 # Mock
    Sum_K_Total = k_data['Sum_K'] + K_slab + K_slab # Col + Slab Left + Slab Right
    
    DF_col = k_data['Sum_K'] / Sum_K_Total
    DF_slab = (K_slab + K_slab) / Sum_K_Total
    
    c_df1, c_df2 = st.columns(2)
    with c_df1:
        st.metric("DF -> Columns", f"{DF_col:.2f}", "Transfer to Axial/Punching")
    with c_df2:
        st.metric("DF -> Slabs", f"{DF_slab:.2f}", "Transfer to Bending")

    # 3. Simple Frame Viz
    st.markdown("### ©️ Frame Model Visualization")
    st.caption("Simulation of the Equivalent Frame (Elastic Line)")
    
    # Simple plot to show the 'Frame' concept
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.plot([0, 0], [0, 3], 'k-', linewidth=3, label="Column") # Bot Col
    ax.plot([0, 0], [3, 6], 'k-', linewidth=3) # Top Col
    ax.plot([-4, 4], [3, 3], 'b-', linewidth=2, label="Slab") # Slab
    
    # Supports
    ax.plot([-4], [3], 'r^')
    ax.plot([4], [3], 'r^')
    
    ax.set_title("Equivalent Frame Model")
    ax.axis('equal')
    ax.axis('off')
    st.pyplot(fig)
