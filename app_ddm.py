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
    res = calc_ddm.calculate_ddm(calc_obj)
    
    # 1. SHOW M0
    st.subheader("Step 1: Total Static Moment ($M_0$)")
    st.latex(r"M_0 = \frac{w_u \ell_2 (\ell_n)^2}{8}")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.write(f"- $w_u$ = {res['w_u']:.2f} kg/m²")
        st.write(f"- $\ell_n$ = {res['Ln']:.2f} m (Clear Span)")
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
    
    # Helper function สำหรับสร้างการ์ดแสดงผล
    def stat_card(col, title, coef, val):
        col.markdown(f"**{title}**")
        col.caption(f"Coef: {coef}")
        if val > 0:
            col.metric("Moment", f"{val:.2f}", "kN.m")
        else:
            col.metric("Moment", f"{val:.2f}", "kN.m")

    stat_card(col_ext, "Ext. Neg (-)", coeffs['neg_ext'], moments['neg_ext'])
    stat_card(col_pos, "Positive (+)", coeffs['pos'], moments['pos'])
    stat_card(col_int, "Int. Neg (-)", coeffs['neg_int'], moments['neg_int'])

    st.markdown("---")

    # 3. STRIP DISTRIBUTION
    st.subheader("Step 3: Strip Distribution")
    dfs = res['dist_factors']
    
    data = []
    def add_row(loc, total_m, cs_pct):
        m_cs = total_m * cs_pct
        m_ms = total_m * (1 - cs_pct)
        return {
            "Location": loc,
            "Total M": f"{total_m:.2f}",
            "% CS": f"{cs_pct*100:.0f}%",
            "M_CS (kN.m)": m_cs,
            "% MS": f"{(1-cs_pct)*100:.0f}%",
            "M_MS (kN.m)": m_ms
        }
        
    data.append(add_row("Ext Neg", moments['neg_ext'], dfs['neg_ext_cs']))
    data.append(add_row("Positive", moments['pos'], dfs['pos_cs']))
    data.append(add_row("Int Neg", moments['neg_int'], dfs['neg_int_cs']))
    
    df = pd.DataFrame(data)
    st.dataframe(df.style.format({"M_CS (kN.m)": "{:.2f}", "M_MS (kN.m)": "{:.2f}"}), use_container_width=True)

    # 4. PLOT GRAPH
    st.markdown("### 📊 Moment Envelope")
    fig, ax = plt.subplots(figsize=(8, 3))
    x = np.linspace(0, 1, 100)
    
    # Plot พาราโบลาคว่ำแบบง่ายๆ
    y_ext, y_pos, y_int = -moments['neg_ext'], moments['pos'], -moments['neg_int']
    # สร้างเส้นโค้งผ่านจุด 3 จุด
    poly = np.polyfit([0, 0.5, 1], [y_ext, y_pos, y_int], 2)
    y_plot = np.polyval(poly, x)
    
    ax.plot(x, y_plot, color='#C0392B', lw=2)
    ax.fill_between(x, y_plot, 0, alpha=0.1, color='red')
    ax.axhline(0, color='black', lw=0.5)
    ax.set_title("Moment Diagram (Approximate)")
    ax.set_ylabel("kN.m")
    ax.set_xlabel("Span Ratio")
    st.pyplot(fig)
