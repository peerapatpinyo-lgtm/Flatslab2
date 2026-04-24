# app_efm.py
import streamlit as st
import pandas as pd
import math
import calc_efm

def render_efm_tab(calc_obj):
    st.header("📐 Equivalent Frame Method (EFM) - Full Design")
    st.markdown("การวิเคราะห์และออกแบบพื้นไร้คานด้วยวิธี Equivalent Frame ตามมาตรฐาน ACI 318")
    st.markdown("---")
    
    try:
        # ดึงค่า Stiffness จาก module เดิมของคุณ
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"❌ Error in Calculation: {e}")
        return

    # --- ฟังก์ชันช่วยจัดฟอร์แมต ---
    def fmt_sci(val): return f"{val:.3e}"
    def fmt_num(val): return f"{val:,.2f}"

    # ดึงตัวแปรที่จำเป็นจาก calc_obj สำหรับกระบวนการออกแบบ
    L1_l = calc_obj['geom']['L1_l']
    L1_r = calc_obj['geom']['L1_r']
    L2 = calc_obj['geom']['L2']
    c1 = calc_obj['geom']['c1_cm'] / 100.0  # เมตร
    c2 = calc_obj['geom']['c2_cm'] / 100.0  # เมตร
    h = calc_obj['geom']['h_slab_cm'] / 100.0  # เมตร
    
    # แปลงโหลดเป็น kg/m
    wu_kgm2 = calc_obj['loads']['wu']
    wu_line = wu_kgm2 * L2  # Load ต่อความยาว (kg/m)
    
    # กำหนดคุณสมบัติวัสดุ
    fc = calc_obj['mat']['fc']  # ksc
    fy = calc_obj['mat']['fy']  # ksc

    # =========================================================================
    # 1️⃣ STIFFNESS & DISTRIBUTION FACTORS (สรุปผลจาก calc_efm)
    # =========================================================================
    st.subheader("1️⃣ Frame Stiffness & Distribution Factors")
    c1_stiff, c2_stiff, c3_stiff, c4_stiff = st.columns(4)
    c1_stiff.metric("Slab ($K_s$)", fmt_sci(res.get('Ks', 0)))
    c2_stiff.metric("Column ($\Sigma K_c$)", fmt_sci(res.get('Sum_Kc', 0)))
    c3_stiff.metric("Torsion ($K_t$)", fmt_sci(res.get('Kt', 0)))
    c4_stiff.metric("Equiv. Col ($K_{ec}$)", fmt_sci(res.get('Kec', 0)))

    df_slab = res.get('df_slab', 0.5)
    df_col = res.get('df_col', 0.5)

    df_data = pd.DataFrame({
        "Member": ["Slab Strip (พื้น)", "Equivalent Column (เสาเสมือน)"],
        "Stiffness (K)": [fmt_sci(res.get('Ks', 0)), fmt_sci(res.get('Kec', 0))],
        "DF (Ratio)": [f"{df_slab:.4f}", f"{df_col:.4f}"],
        "Percentage": [f"{df_slab*100:.1f}%", f"{df_col*100:.1f}%"]
    })
    st.table(df_data)

    # =========================================================================
    # 2️⃣ LONGITUDINAL MOMENT ANALYSIS (FEM & Distribution)
    # =========================================================================
    st.subheader("2️⃣ Longitudinal Moment Analysis")
    st.markdown("การคำนวณ Fixed End Moment (FEM) และการกระจายโมเมนต์ (Moment Distribution) ที่รอยต่อเสา")
    
    # คำนวณ FEM (kg-m)
    FEM_L = (wu_line * (L1_l**2)) / 12 if L1_l > 0 else 0
    FEM_R = (wu_line * (L1_r**2)) / 12 if L1_r > 0 else 0
    
    # Unbalanced Moment ที่ Joint
    M_unbal = abs(FEM_L - FEM_R)
    
    # โมเมนต์ที่ถ่ายลงเสา และโมเมนต์ที่ปรับแก้ในพื้น
    M_col = M_unbal * df_col
    M_dist_slab = M_unbal * df_slab
    
    # Design Moments (ตัวอย่างการประมาณค่า EFM แบบรวดเร็วที่หน้าตัดวิกฤต)
    # ในการทำงานจริงต้องกระจายโมเมนต์ทั้ง Frame แต่เพื่อแสดงผลราย Joint:
    Mu_neg_design = max(FEM_L, FEM_R) - M_dist_slab  # โมเมนต์ลบออกแบบ (ปรับลดแล้ว)
    Mu_pos_design = (wu_line * (max(L1_l, L1_r)**2)) / 24  # โมเมนต์บวกกลางช่วง (โดยประมาณ)

    col_fem1, col_fem2, col_fem3 = st.columns(3)
    col_fem1.metric("Load per meter ($w_u \cdot L_2$)", f"{wu_line:,.0f} kg/m")
    col_fem2.metric("Unbalanced Moment", f"{M_unbal:,.0f} kg-m")
    col_fem3.metric("Moment to Column", f"{M_col:,.0f} kg-m", "Design for Punching & Col", delta_color="off")

    with st.expander("🔍 ดูรายการคำนวณโมเมนต์ตามยาว (Longitudinal Moments)"):
        st.latex(r"w_{u,line} = w_u \times L_2 = " + f"{wu_kgm2:,.0f} \\times {L2:.2f} = {wu_line:,.0f} \\text{{ kg/m}}")
        st.latex(r"FEM = \frac{w_{u,line} L_1^2}{12}")
        st.write(f"- **FEM Left Span:** {FEM_L:,.0f} kg-m")
        st.write(f"- **FEM Right Span:** {FEM_R:,.0f} kg-m")
        st.latex(r"M_{unbalance} = |FEM_L - FEM_R| = " + f"{M_unbal:,.0f} \\text{{ kg-m}}")
        st.latex(r"M_{column} = M_{unbalance} \times DF_{col} = " + f"{M_col:,.0f} \\text{{ kg-m}}")

    # =========================================================================
    # 3️⃣ TRANSVERSE DISTRIBUTION (Column vs Middle Strip)
    # =========================================================================
    st.subheader("3️⃣ Transverse Strip Distribution (ACI 318)")
    st.info("แบ่งโมเมนต์ที่ได้จากการวิเคราะห์ Frame ลงใน Column Strip และ Middle Strip")

    # สัดส่วนตาม ACI (สำหรับ Flat Slab ไม่มีคานขอบ α1=0)
    pct_col_neg = 0.75
    pct_mid_neg = 0.25
    pct_col_pos = 0.60
    pct_mid_pos = 0.40

    df_strip = pd.DataFrame({
        "Location": ["Negative Moment (Support)", "Positive Moment (Midspan)"],
        "Total $M_u$ (kg-m)": [fmt_num(Mu_neg_design), fmt_num(Mu_pos_design)],
        "Column Strip %": [f"{pct_col_neg*100}%", f"{pct_col_pos*100}%"],
        "Col Strip $M_u$": [fmt_num(Mu_neg_design * pct_col_neg), fmt_num(Mu_pos_design * pct_col_pos)],
        "Middle Strip %": [f"{pct_mid_neg*100}%", f"{pct_mid_pos*100}%"],
        "Mid Strip $M_u$": [fmt_num(Mu_neg_design * pct_mid_neg), fmt_num(Mu_pos_design * pct_mid_pos)]
    })
    st.table(df_strip)

    # =========================================================================
    # 4️⃣ FLEXURAL REINFORCEMENT DESIGN
    # =========================================================================
    st.subheader("4️⃣ Flexural Reinforcement Design")
    
    # Helper Function สำหรับออกแบบเหล็ก
    def calc_rebar(Mu_kgm, b_cm, d_cm, fc_ksc, fy_ksc):
        phi = 0.9
        Mu_kgcm = Mu_kgm * 100
        Rn = Mu_kgcm / (phi * b_cm * d_cm**2)
        # ตรวจสอบสูตร p
        term = 1 - (2 * Rn) / (0.85 * fc_ksc)
        if term < 0: return "Over-reinforced", 0, 0
        
        rho = (0.85 * fc_ksc / fy_ksc) * (1 - math.sqrt(term))
        rho_min = 0.0018  # ACI Shrinkage & Temp min for Grade 60 (หรือปรับตามเกรด)
        if fy_ksc < 4000: rho_min = 0.0020
        
        rho_design = max(rho, rho_min)
        As_req = rho_design * b_cm * d_cm
        return rho_design, As_req, Rn

    # คำนวณ d (effective depth)
    cover_cm = 2.5
    db_cm = 1.2  # สมมติเหล็ก DB12
    d_cm = (h * 100) - cover_cm - (db_cm / 2)
    
    # ความกว้าง Strip (คิดที่ L2/2 ต่อฝั่ง หรือ L2/4)
    # Column strip width = min(L1, L2)/2 
    width_col_m = min(max(L1_l, L1_r), L2) / 2.0
    width_mid_m = L2 - width_col_m
    
    b_col_cm = width_col_m * 100
    b_mid_cm = width_mid_m * 100

    Mu_col_neg = Mu_neg_design * pct_col_neg
    _, As_col_neg, _ = calc_rebar(Mu_col_neg, b_col_cm, d_cm, fc, fy)

    Mu_mid_neg = Mu_neg_design * pct_mid_neg
    _, As_mid_neg, _ = calc_rebar(Mu_mid_neg, b_mid_cm, d_cm, fc, fy)

    col_reb1, col_reb2 = st.columns(2)
    with col_reb1:
        st.markdown("#### 🟥 Column Strip Design")
        st.write(f"**Width ($b$):** {b_col_cm:.0f} cm")
        st.write(f"**Eff. Depth ($d$):** {d_cm:.1f} cm")
        st.metric("Req. As (Support Negative)", f"{As_col_neg:.2f} cm²", f"~ {As_col_neg/(b_col_cm/100):.2f} cm²/m")
        # กะระยะแอดเหล็กสมมติ DB12
        spacing = (1.13 * b_col_cm) / As_col_neg if As_col_neg > 0 else 0
        st.caption(f"💡 Suggestion: DB12 @ {min(spacing, 30):.0f} cm")

    with col_reb2:
        st.markdown("#### 🟦 Middle Strip Design")
        st.write(f"**Width ($b$):** {b_mid_cm:.0f} cm")
        st.write(f"**Eff. Depth ($d$):** {d_cm:.1f} cm")
        st.metric("Req. As (Support Negative)", f"{As_mid_neg:.2f} cm²", f"~ {As_mid_neg/(b_mid_cm/100):.2f} cm²/m")
        spacing_m = (1.13 * b_mid_cm) / As_mid_neg if As_mid_neg > 0 else 0
        st.caption(f"💡 Suggestion: DB12 @ {min(spacing_m, 30):.0f} cm")

    # =========================================================================
    # 5️⃣ UNBALANCED MOMENT TRANSFER & PUNCHING SHEAR
    # =========================================================================
    st.subheader("5️⃣ Shear & Unbalanced Moment Transfer (Critical Check)")
    st.markdown("ACI 318 กำหนดให้ถ่ายเทโมเมนต์ดัดที่ไม่สมดุล ($M_{unbalance}$) เข้าเสาผ่าน **Flexure ($\gamma_f$)** และ **Eccentric Shear ($\gamma_v$)**")

    # คำนวณ Fraction
    c1_d = (c1 * 100) + d_cm
    c2_d = (c2 * 100) + d_cm
    gamma_f = 1.0 / (1.0 + (2.0/3.0) * math.sqrt(c1_d / c2_d))
    gamma_v = 1.0 - gamma_f

    M_flexure = M_col * gamma_f
    M_shear = M_col * gamma_v

    # ประมาณค่าแรงเฉือน V_u (พื้นที่ Tributary Area ลบหน้าตัดวิกฤต)
    trib_area = max(L1_l, L1_r) * L2  # พื้นที่รับน้ำหนักโดยประมาณ
    crit_area = (c1_d * c2_d) / 10000.0  # ตร.ม.
    Vu_kg = wu_kgm2 * (trib_area - crit_area)

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.markdown("**1. Moment Transfer Fractions**")
        st.latex(r"\gamma_f = \frac{1}{1 + \frac{2}{3}\sqrt{\frac{c_1+d}{c_2+d}}} = " + f"{gamma_f:.3f}")
        st.latex(r"\gamma_v = 1 - \gamma_f = " + f"{gamma_v:.3f}")
        
    with col_v2:
        st.markdown("**2. Distributed Transfer**")
        st.write(f"- **Transfer by Flexure ($M_f$):** {M_flexure:,.0f} kg-m (เพิ่มเหล็กเสริมพิเศษหน้าเสา)")
        st.write(f"- **Transfer by Shear ($M_v$):** {M_shear:,.0f} kg-m (นำไปคิดหน่วยแรงเฉือนทะลุ)")

    # การตรวจสอบ Punching Shear เบื้องต้น
    bo_cm = 2 * (c1_d + c2_d)
    Ac_cm2 = bo_cm * d_cm
    Jc = (d_cm * c1_d**3 / 6) + (c1_d * d_cm**3 / 6) + (d_cm * c2_d * (c1_d**2) / 2) # Approximation for interior column
    
    # Stress calculation
    vu_shear_only = Vu_kg / Ac_cm2
    vu_moment = (M_shear * 100 * (c1_d / 2)) / Jc if Jc > 0 else 0
    vu_total = vu_shear_only + vu_moment
    
    phi_vc = 0.85 * 1.06 * math.sqrt(fc) # ACI formula (ksc) (1.06 ในหน่วยเมตริกเทียบเท่า 4 in US Customary)
    
    st.markdown("**3. Punching Shear Stress Check at $d/2$ from Column Face**")
    st.latex(r"v_u = \frac{V_u}{A_c} \pm \frac{\gamma_v M_{unbal} c}{J_c}")
    
    st.info(f"$$ v_{{u,max}} = {vu_shear_only:.2f} \\text{{ (Shear)}} + {vu_moment:.2f} \\text{{ (Moment)}} = {vu_total:.2f} \\text{{ ksc}} $$")
    
    if vu_total <= phi_vc:
        st.success(f"✅ **Punching Shear OK:** $v_u$ ({vu_total:.2f} ksc) $\le \phi v_c$ ({phi_vc:.2f} ksc)")
    else:
        st.error(f"❌ **Punching Shear FAILS:** $v_u$ ({vu_total:.2f} ksc) > $\phi v_c$ ({phi_vc:.2f} ksc). แนะนำให้เพิ่มความหนา, Drop Panel หรือเหล็กเสริมรับแรงเฉือน (Shear Studs)")
