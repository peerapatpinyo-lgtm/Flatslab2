# app_ddm.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import calc_ddm  # <--- เรียกใช้ไฟล์ Logic

def render_ddm_tab(calc_obj):
    st.header("1️⃣ Direct Design Method (DDM)")
    st.markdown("---")

    # เรียกฟังก์ชันคำนวณ
    try:
        res = calc_ddm.calculate_ddm(calc_obj)
    except Exception as e:
        st.error(f"Calculation Error: {e}")
        return

    # 1. SHOW M0
    st.subheader("Step 1: Total Static Moment ($M_0$)")
    st.latex(r"M_0 = \frac{w_u \ell_2 (\ell_n)^2}{8}")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.write(f"- $w_u$ = {res['w_u']:.2f} kg/m²")
        st.write(f"- $\ell_n$ = {res['Ln']:.2f} m")
        st.write(f"- $\ell_2$ = {res['L2']:.2f} m")
    with c2:
        st.info(f"**$M_0$ = {res['M0_kNm']:.2f} kN.m**")

    st.markdown("---")

    # 2. LONGITUDINAL DISTRIBUTION
    st.subheader("Step 2: Longitudinal Distribution")
    coeffs = res['coeffs']
    moments = res['moments']
    
    st.write(f"**Condition:** {coeffs['desc']}")
    
    col_ext, col_pos, col_int = st.columns(3)
    
    def stat_card(col, title, coef, val):
        col.markdown(f"**{title}**")
        col.caption(f"Coef: {coef}")
        col.metric("Moment", f"{val:.2f}", "kN.m")

    stat_card(col_ext, "Ext. Neg (-)", coeffs['neg_ext'], moments['neg_ext'])
    stat_card(col_pos, "Positive (+)", coeffs['pos'], moments['pos'])
    stat_card(col_int, "Int. Neg (-)", coeffs['neg_int'], moments['neg_int'])

    st.markdown("---")

    # 3. STRIP DISTRIBUTION
    st.subheader("Step 3: Strip Distribution")
    dfs = res['dist_factors']
    
    # สร้าง Data List แบบ Manual เพื่อความชัวร์ (ป้องกัน KeyError ใน Loop)
    data = []
    
    # Row 1: Ext Neg
    m_total = moments['neg_ext']
    pct_cs = dfs.get('neg_ext_cs', 0.75) # ใช้ .get ป้องกัน Error
    data.append({
        "Location": "Exterior Neg",
        "Total M": f"{m_total:.2f}",
        "% CS": f"{pct_cs*100:.0f}%",
        "M_CS (kN.m)": m_total * pct_cs,
        "% MS": f"{(1-pct_cs)*100:.0f}%",
        "M_MS (kN.m)": m_total * (1-pct_cs)
    })
    
    # Row 2: Positive
    m_total = moments['pos']
    pct_cs = dfs.get('pos_cs', 0.60)
    data.append({
        "Location": "Positive (+)",
        "Total M": f"{m_total:.2f}",
        "% CS": f"{pct_cs*100:.0f}%",
        "M_CS (kN.m)": m_total * pct_cs,
        "% MS": f"{(1-pct_cs)*100:.0f}%",
        "M_MS (kN.m)": m_total * (1-pct_cs)
    })
    
    # Row 3: Int Neg
    m_total = moments['neg_ext'] # ใช้ค่านี้สำหรับการแสดงผล row สุดท้าย (จริงๆควรเป็น int)
    # แก้ไข: ใช้ moments['neg_int'] ให้ถูกต้อง
    m_total = moments['neg_int']
    pct_cs = dfs.get('neg_int_cs', 0.75)
    data.append({
        "Location": "Interior Neg",
        "Total M": f"{m_total:.2f}",
        "% CS": f"{pct_cs*100:.0f}%",
        "M_CS (kN.m)": m_total * pct_cs,
        "% MS": f"{(1-pct_cs)*100:.0f}%",
        "M_MS (kN.m)": m_total * (1-pct_cs)
    })
    
    df = pd.DataFrame(data)
    st.dataframe(df.style.format({"M_CS (kN.m)": "{:.2f}", "M_MS (kN.m)": "{:.2f}"}), use_container_width=True)

    # 4. PLOT GRAPH
    st.markdown("### 📊 Moment Envelope")
    fig, ax = plt.subplots(figsize=(8, 3))
    x = np.linspace(0, 1, 100)
    
    y_ext = -moments['neg_ext']
    y_pos = moments['pos']
    y_int = -moments['neg_int']
    
    poly = np.polyfit([0, 0.5, 1], [y_ext, y_pos, y_int], 2)
    y_plot = np.polyval(poly, x)
    
    ax.plot(x, y_plot, color='#C0392B', lw=2)
    ax.fill_between(x, y_plot, 0, alpha=0.1, color='red')
    ax.axhline(0, color='black', lw=0.5)
    ax.set_title("Moment Diagram (Approximate)")
    ax.set_ylabel("kN.m")
    st.pyplot(fig)
