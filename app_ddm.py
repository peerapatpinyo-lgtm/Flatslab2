# app_ddm.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import calc_ddm

def render_ddm_tab(calc_obj):
    st.header("1️⃣ Direct Design Method (ACI 318)")
    st.markdown("---")

    try:
        res = calc_ddm.calculate_ddm(calc_obj)
    except Exception as e:
        st.error(f"Calculation Error: {e}")
        return

    # 1. INPUT PARAMETERS CHECK
    with st.expander("ℹ️ Design Parameters Check", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Span Ratio ($l_2/l_1$)", f"{res['l2_l1']:.2f}")
        c2.metric("Clear Span ($l_n$)", f"{res['Ln']:.2f} m")
        c3.metric("Load ($w_u$)", f"{res['w_u']:.0f} kg/m²")

    # 2. STATIC MOMENT
    st.subheader("Step 1: Total Static Moment ($M_0$)")
    st.latex(r"M_0 = \frac{w_u \ell_2 (\ell_n)^2}{8}")
    st.info(f"**$M_0$ = {res['M0_kNm']:.2f} kN.m**")

    st.markdown("---")

    # 3. MOMENT DISTRIBUTION TABLE (Professional View)
    st.subheader("Step 2 & 3: Moment Distribution")
    st.caption(f"Condition: {res['coeffs']['desc']}")

    # Prepare Data
    moments = res['moments']
    dfs = res['dist_factors']
    
    # Define Rows
    rows = [
        ("Exterior Negative (-)", moments['neg_ext'], dfs['neg_ext_cs']),
        ("Positive (+)",          moments['pos'],     dfs['pos_cs']),
        ("Interior Negative (-)", moments['neg_int'], dfs['neg_int_cs'])
    ]
    
    data = []
    for loc, m_total, pct_cs in rows:
        m_cs = m_total * pct_cs
        m_ms = m_total * (1 - pct_cs)
        data.append({
            "Location": loc,
            "Total Moment (kN.m)": f"{m_total:.2f}",
            "CS Dist. Factor": f"{pct_cs*100:.1f}%",
            "CS Moment": m_cs,
            "MS Dist. Factor": f"{(1-pct_cs)*100:.1f}%",
            "MS Moment": m_ms
        })

    df = pd.DataFrame(data)
    
    # Highlight specific columns
    st.dataframe(
        df.style.format({
            "CS Moment": "{:.2f}", 
            "MS Moment": "{:.2f}"
        }).background_gradient(subset=["CS Moment"], cmap="Reds", vmin=0, vmax=res['M0_kNm']*0.5),
        use_container_width=True
    )
    
    st.caption("*CS = Column Strip (แถบเสา), MS = Middle Strip (แถบกลาง)*")

    # 4. PLOT ENVELOPE
    st.markdown("### 📈 Moment Envelope")
    
    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.linspace(0, res['Ln'], 100)
    
    # Simple Parabolic approximation for visualization
    m_left = -moments['neg_ext']
    m_mid = moments['pos']
    m_right = -moments['neg_int']
    
    # Fit parabola y = ax^2 + bx + c
    # x=0 -> m_left
    # x=L/2 -> m_mid
    # x=L -> m_right
    L = res['Ln']
    # Solving 3 equations... simpler method:
    # M(x) approx via shape functions (Structural Analysis basics)
    # Just for UI curve:
    poly = np.polyfit([0, L/2, L], [m_left, m_mid, m_right], 2)
    y_vals = np.polyval(poly, x)
    
    ax.plot(x, y_vals, color='black', linewidth=2, label='Total Moment')
    
    # Fill areas
    ax.fill_between(x, y_vals, 0, where=(y_vals>0), color='green', alpha=0.1, label='Positive')
    ax.fill_between(x, y_vals, 0, where=(y_vals<0), color='red', alpha=0.1, label='Negative')
    
    ax.axhline(0, color='black', linewidth=0.5)
    ax.set_xlabel("Distance along span (m)")
    ax.set_ylabel("Moment (kN.m)")
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()
    
    st.pyplot(fig)
