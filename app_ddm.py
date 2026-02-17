import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import calc_ddm  # เรียกไฟล์คำนวณ

def render_ddm_tab(calc_obj):
    st.header("1️⃣ Direct Design Method (DDM)")
    st.markdown("---")

    # 1. RUN CALCULATION
    try:
        res = calc_ddm.calculate_ddm(calc_obj)
    except Exception as e:
        st.error(f"❌ Calculation Error: {e}")
        st.info("กรุณาตรวจสอบข้อมูล Input อีกครั้ง (ขนาดเสา, ระยะช่วงคาน)")
        return

    inp = res['inputs']
    moments = res['moments_total']
    pcts = res['cs_percents']

    # 2. SHOW PARAMETERS & M0
    st.subheader("Step 1: Design Parameters & Static Moment ($M_0$)")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Geometry Info:**")
        st.write(f"- Span $L_1$: {inp['L1']:.2f} m")
        st.write(f"- Width $L_2$: {inp['L2']:.2f} m")
        st.write(f"- Clear Span $\ell_n$: {inp['Ln']:.2f} m")
        st.caption(f"Ratio $\ell_2/\ell_1$ = {inp['l2_l1_ratio']:.2f}")
    
    with c2:
        st.markdown("**Load Info:**")
        st.write(f"- Factored Load ($w_u$): {inp['w_u_kn']:.2f} kN/m²")
        st.latex(r"M_0 = \frac{w_u \ell_2 \ell_n^2}{8}")
    
    with c3:
        st.success(f"**$M_0$ = {res['M0_kNm']:.2f} kN.m**")
        st.markdown(f"**Condition:** {res['span_desc']}")

    st.markdown("---")

    # 3. DETAILED DISTRIBUTION TABLE
    st.subheader("Step 2 & 3: Moment Distribution Table")
    st.write("ตารางแสดงการกระจายโมเมนต์เข้าสู่ Column Strip (CS) และ Middle Strip (MS)")

    # สร้างข้อมูลสำหรับ Table
    # Row 1: Exterior Negative
    row_ext = {
        "Position": "Exterior Negative (-)",
        "Coeff (Long.)": res['long_coeffs']['neg_ext'],
        "Total M (kN.m)": moments['neg_ext'],
        "% to CS": pcts['neg_ext_cs'],
        "M @ CS": moments['neg_ext'] * pcts['neg_ext_cs'],
        "% to MS": 1.0 - pcts['neg_ext_cs'],
        "M @ MS": moments['neg_ext'] * (1.0 - pcts['neg_ext_cs'])
    }
    
    # Row 2: Positive
    row_pos = {
        "Position": "Positive Midspan (+)",
        "Coeff (Long.)": res['long_coeffs']['pos'],
        "Total M (kN.m)": moments['pos'],
        "% to CS": pcts['pos_cs'],
        "M @ CS": moments['pos'] * pcts['pos_cs'],
        "% to MS": 1.0 - pcts['pos_cs'],
        "M @ MS": moments['pos'] * (1.0 - pcts['pos_cs'])
    }
    
    # Row 3: Interior Negative
    row_int = {
        "Position": "Interior Negative (-)",
        "Coeff (Long.)": res['long_coeffs']['neg_int'],
        "Total M (kN.m)": moments['neg_int'],
        "% to CS": pcts['neg_int_cs'],
        "M @ CS": moments['neg_int'] * pcts['neg_int_cs'],
        "% to MS": 1.0 - pcts['neg_int_cs'],
        "M @ MS": moments['neg_int'] * (1.0 - pcts['neg_int_cs'])
    }
    
    df = pd.DataFrame([row_ext, row_pos, row_int])
    
    # Formatting for display
    # แปลง % เป็น string 
    df_disp = df.copy()
    df_disp['% to CS'] = (df['% to CS'] * 100).map('{:.0f}%'.format)
    df_disp['% to MS'] = (df['% to MS'] * 100).map('{:.0f}%'.format)
    
    # Highlight Columns
    st.dataframe(
        df_disp.style.format({
            "Total M (kN.m)": "{:.2f}",
            "M @ CS": "{:.2f}",
            "M @ MS": "{:.2f}"
        }).background_gradient(subset=["M @ CS"], cmap="Oranges"),
        use_container_width=True
    )
    
    st.info("""
    **คำอธิบายเพิ่มเติม (ACI Logic):**
    * **CS (Column Strip):** แถบเสา รับโมเมนต์เป็นหลัก (คิดเป็น % ตามตาราง ACI 8.10.5)
    * **MS (Middle Strip):** แถบกลาง รับโมเมนต์ส่วนที่เหลือจาก CS
    """)

    # 4. PLOT GRAPH (VISUALIZATION)
    st.markdown("### 📈 Moment Envelope Diagram")
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Create simple curve points
    L = inp['Ln']
    x = np.linspace(0, L, 100)
    
    m_left = -moments['neg_ext']
    m_mid = moments['pos']
    m_right = -moments['neg_int']
    
    # Curve fitting for visualization (Parabola passing through 3 points)
    # y = ax^2 + bx + c
    # x=0, y=m_left | x=L/2, y=m_mid | x=L, y=m_right
    # Note: This is an approximation for visual purposes. Real moment diagram depends on exact load dist.
    
    # Using numpy polyfit
    X_fit = [0, L/2, L]
    Y_fit = [m_left, m_mid, m_right]
    poly = np.polyfit(X_fit, Y_fit, 2)
    y_plot = np.polyval(poly, x)
    
    ax.plot(x, y_plot, color='#E74C3C', linewidth=2, label='Total Moment')
    ax.fill_between(x, y_plot, 0, where=(y_plot>0), color='#F1C40F', alpha=0.3, label='Positive Zone')
    ax.fill_between(x, y_plot, 0, where=(y_plot<0), color='#E74C3C', alpha=0.1, label='Negative Zone')
    
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_title(f"Moment Distribution along Span Ln ({inp['Ln']:.2f} m)")
    ax.set_ylabel("Moment (kN.m)")
    ax.set_xlabel("Distance (m)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    
    st.pyplot(fig)
