# app_efm.py
import streamlit as st
import pandas as pd
import math
import calc_efm

def render_efm_tab(calc_obj):
    st.header("📐 Equivalent Frame Method (EFM) - Detailed Design")
    st.markdown("วิเคราะห์และออกแบบจุดต่อพื้นไร้คาน (Single Joint Analysis) ตามมาตรฐาน ACI 318")
    
    try:
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"❌ Error in Calculation: {e}")
        return

    # --- ฟังก์ชันช่วยจัดฟอร์แมต ---
    def fmt_sci(val): return f"{val:.3e}"
    def fmt_num(val, dec=2): return f"{val:,.{dec}f}"

    # --- ตัวแปรทางเรขาคณิตและโหลด ---
    L1_l = calc_obj['geom'].get('L1_l', 6.0)
    L1_r = calc_obj['geom'].get('L1_r', 6.0)
    L2 = calc_obj['geom'].get('L2', 6.0)
    c1_cm = calc_obj['geom']['c1_cm']
    c2_cm = calc_obj['geom']['c2_cm']
    c1 = c1_cm / 100.0
    c2 = c2_cm / 100.0
    h = calc_obj['geom']['h_slab_cm'] / 100.0
    
    wu_kgm2 = calc_obj['loads']['wu']
    wu_line = wu_kgm2 * L2
    fc = calc_obj['mat']['fc']
    fy = calc_obj['mat']['fy']
    
    # ความลึกประสิทธิผล (d)
    cover_cm = 2.5
    db_cm = 1.2
    d_cm = (h * 100) - cover_cm - (db_cm / 2)

    # ผู้ใช้เลือกตำแหน่งเสา
    col_type = st.radio(
        "📍 เลือกตำแหน่งของจุดต่อ (Column Location):",
        ["Interior (เสากลาง)", "Edge (เสาริม - โมเมนต์ตั้งฉากขอบ)", "Corner (เสามุม)"],
        horizontal=True
    )
    st.markdown("---")

    # ==========================================
    # สร้าง TABS ย่อย 4 แท็บ
    # ==========================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ Stiffness & DF", 
        "2️⃣ Moment Distribution", 
        "3️⃣ Flexural Design", 
        "4️⃣ Punching Shear"
    ])

    # ------------------------------------------
    # TAB 1: Stiffness & Distribution Factors
    # ------------------------------------------
    with tab1:
        st.subheader("Frame Stiffness & Distribution Factors")
        st.markdown("ดึงค่าความแข็ง (Stiffness) จากโมดูล `calc_efm` เพื่อหาอัตราส่วนกระจายโมเมนต์ (DF)")
        
        c1_stiff, c2_stiff, c3_stiff, c4_stiff = st.columns(4)
        c1_stiff.metric("Slab ($K_s$)", fmt_sci(res.get('Ks', 0)))
        c2_stiff.metric("Column ($\Sigma K_c$)", fmt_sci(res.get('Sum_Kc', 0)))
        c3_stiff.metric("Torsion ($K_t$)", fmt_sci(res.get('Kt', 0)))
        c4_stiff.metric("Equiv. Col ($K_{ec}$)", fmt_sci(res.get('Kec', 0)))

        df_slab = res.get('df_slab', 0.5)
        df_col = res.get('df_col', 0.5)

        st.latex(fr"DF_{{col}} = \frac{{K_{{ec}}}}{{K_{{ec}} + \Sigma K_s}} = {df_col:.4f}")
        st.latex(fr"DF_{{slab}} = \frac{{\Sigma K_s}}{{K_{{ec}} + \Sigma K_s}} = {df_slab:.4f}")

    # ------------------------------------------
    # TAB 2: Moment Distribution (Longitudinal)
    # ------------------------------------------
    with tab2:
        st.subheader("Longitudinal Moment Analysis")
        
        # คำนวณ FEM (kg-m)
        FEM_L = (wu_line * (L1_l**2)) / 12 if L1_l > 0 else 0
        FEM_R = (wu_line * (L1_r**2)) / 12 if L1_r > 0 else 0
        
        if "Edge" in col_type or "Corner" in col_type:
            FEM_L = 0  # สมมติให้ขอบอยู่ด้านซ้าย
            
        M_unbal = abs(FEM_L - FEM_R)
        M_col = M_unbal * df_col
        M_slab_dist = M_unbal * df_slab
        Mu_neg = max(FEM_L, FEM_R) - (M_slab_dist / 2) # โมเมนต์ลบออกแบบในพื้น

        st.markdown("**การคำนวณ Unbalanced Moment และการกระจายลงเสา**")
        st.latex(fr"FEM_{{Right}} = \frac{{w_u L_2 \times L_{{1,R}}^2}}{{12}} = \frac{{{fmt_num(wu_kgm2,0)} \times {L2} \times {L1_r}^2}}{{12}} = {fmt_num(FEM_R, 0)} \text{{ kg-m}}")
        if FEM_L > 0:
            st.latex(fr"FEM_{{Left}} = \frac{{w_u L_2 \times L_{{1,L}}^2}}{{12}} = {fmt_num(FEM_L, 0)} \text{{ kg-m}}")
        
        st.latex(fr"M_{{unbal}} = |FEM_{{Left}} - FEM_{{Right}}| = {fmt_num(M_unbal, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{col}} = M_{{unbal}} \times DF_{{col}} = {fmt_num(M_unbal,0)} \times {df_col:.3f} = {fmt_num(M_col, 0)} \text{{ kg-m}}")
        st.info(f"💡 โมเมนต์ที่ถ่ายลงเสา ($M_{{col}}$) = **{fmt_num(M_col, 0)} kg-m** จะถูกส่งไปคำนวณ Punching Shear ใน Tab 4")

    # ------------------------------------------
    # TAB 3: Flexural Design (Transverse)
    # ------------------------------------------
    with tab3:
        st.subheader("Transverse Strip & Flexural Design")
        st.markdown("แบ่งโมเมนต์ดัดลบ ($M_{u,neg}$) ลง Column Strip (75%) และ Middle Strip (25%) ตาม ACI 318")
        
        pct_col_neg = 0.75
        Mu_col_neg = Mu_neg * pct_col_neg
        Mu_mid_neg = Mu_neg * (1 - pct_col_neg)
        
        b_col_cm = (min(max(L1_l, L1_r), L2) / 2.0) * 100
        b_mid_cm = (L2 * 100) - b_col_cm

        def design_flexure(Mu_kgm, b_cm, d_cm, fc, fy):
            phi = 0.9
            Mu_kgcm = Mu_kgm * 100
            Rn = Mu_kgcm / (phi * b_cm * d_cm**2)
            term = 1 - (2 * Rn) / (0.85 * fc)
            rho_req = (0.85 * fc / fy) * (1 - math.sqrt(term)) if term > 0 else 0
            rho_min = 0.0018 if fy >= 4000 else 0.0020
            rho_des = max(rho_req, rho_min)
            As_req = rho_des * b_cm * d_cm
            return Mu_kgcm, Rn, rho_req, rho_min, As_req

        c_col1, c_col2 = st.columns(2)
        
        with c_col1:
            st.markdown(f"#### 🟥 Column Strip ($b = {b_col_cm:.0f}$ cm)")
            Mu_kgcm, Rn, rho_req, rho_min, As_req = design_flexure(Mu_col_neg, b_col_cm, d_cm, fc, fy)
            st.latex(fr"M_u = {fmt_num(Mu_col_neg, 0)} \text{{ kg-m}}")
            st.latex(fr"R_n = \frac{{{fmt_num(Mu_kgcm,0)}}}{{0.9 \times {b_col_cm:.0f} \times {d_cm:.1f}^2}} = {fmt_num(Rn, 2)} \text{{ ksc}}")
            st.latex(fr"\rho_{{req}} = {rho_req:.5f} \quad (\rho_{{min}} = {rho_min})")
            st.success(f"**$A_{{s,req}}$ = {fmt_num(As_req, 2)} cm²**")

        with c_col2:
            st.markdown(f"#### 🟦 Middle Strip ($b = {b_mid_cm:.0f}$ cm)")
            Mu_kgcm_m, Rn_m, rho_req_m, rho_min_m, As_req_m = design_flexure(Mu_mid_neg, b_mid_cm, d_cm, fc, fy)
            st.latex(fr"M_u = {fmt_num(Mu_mid_neg, 0)} \text{{ kg-m}}")
            st.latex(fr"R_n = \frac{{{fmt_num(Mu_kgcm_m,0)}}}{{0.9 \times {b_mid_cm:.0f} \times {d_cm:.1f}^2}} = {fmt_num(Rn_m, 2)} \text{{ ksc}}")
            st.latex(fr"\rho_{{req}} = {rho_req_m:.5f} \quad (\rho_{{min}} = {rho_min_m})")
            st.success(f"**$A_{{s,req}}$ = {fmt_num(As_req_m, 2)} cm²**")

    # ------------------------------------------
    # TAB 4: Punching Shear & Unbalanced Moment
    # ------------------------------------------
    with tab4:
        st.subheader("Punching Shear & Unbalanced Moment")
        
        # จัดรูปทรงหน้าตัดวิกฤต
        if "Interior" in col_type:
            b1 = c1_cm + d_cm
            b2 = c2_cm + d_cm
            Ac = 2 * d_cm * (b1 + b2)
            c_AB = b1 / 2.0
            Jc = (d_cm * b1**3 / 6.0) + (b1 * d_cm**3 / 6.0) + (d_cm * b2 * (b1**2) / 2.0)
        elif "Edge" in col_type:
            b1 = c1_cm + (d_cm / 2.0)
            b2 = c2_cm + d_cm
            Ac = d_cm * (2*b1 + b2)
            c_AB = (b1**2) / (2*b1 + b2)
            Jc = (d_cm * b1**3 / 6.0) + (b1 * d_cm**3 / 6.0) + 2*d_cm*b1*((b1/2 - c_AB)**2) + d_cm*b2*(c_AB**2)
        else: # Corner
            b1 = c1_cm + (d_cm / 2.0)
            b2 = c2_cm + (d_cm / 2.0)
            Ac = d_cm * (b1 + b2)
            c_AB = (b1**2) / (2*(b1 + b2))
            Jc = (d_cm * b1**3 / 12.0) + (b1 * d_cm**3 / 12.0) + d_cm*b1*((b1/2 - c_AB)**2) + d_cm*b2*(c_AB**2)

        # Fraction & Shear Forces
        gamma_f = 1.0 / (1.0 + (2.0/3.0) * math.sqrt(b1 / b2))
        gamma_v = 1.0 - gamma_f
        
        trib_area = max(L1_l, L1_r) * L2
        if "Edge" in col_type: trib_area /= 2
        if "Corner" in col_type: trib_area /= 4
        
        crit_area_m2 = (b1 * b2) / 10000.0
        Vu_kg = wu_kgm2 * (trib_area - crit_area_m2)

        # Stresses
        vu_shear = Vu_kg / Ac
        vu_moment = (gamma_v * M_col * 100 * c_AB) / Jc if Jc > 0 else 0
        vu_total = vu_shear + vu_moment
        phi_vc = 0.85 * 1.06 * math.sqrt(fc)

        st.markdown("**1. Critical Section Properties (ตามประเภทเสา)**")
        c_prop1, c_prop2 = st.columns(2)
        with c_prop1:
            st.latex(fr"b_1 = {b1:.1f} \text{{ cm}}, \quad b_2 = {b2:.1f} \text{{ cm}}")
            st.latex(fr"A_c = {fmt_num(Ac,1)} \text{{ cm}}^2")
        with c_prop2:
            st.latex(fr"c_{{AB}} = {c_AB:.2f} \text{{ cm}}")
            st.latex(fr"J_c = {fmt_num(Jc,1)} \text{{ cm}}^4")

        st.divider()
        st.markdown("**2. Transfer Fractions**")
        st.latex(fr"\gamma_f = \frac{{1}}{{1 + \frac{{2}}{{3}}\sqrt{{\frac{{{b1:.1f}}}{{{b2:.1f}}}}}}} = {gamma_f:.3f} \quad \rightarrow \quad \gamma_v = 1 - {gamma_f:.3f} = {gamma_v:.3f}")

        st.divider()
        st.markdown("**3. Stress Check**")
        st.latex(fr"v_{{u(Shear)}} = \frac{{{fmt_num(Vu_kg,0)}}}{{{fmt_num(Ac,1)}}} = {fmt_num(vu_shear, 2)} \text{{ ksc}}")
        st.latex(fr"v_{{u(Moment)}} = \frac{{{gamma_v:.3f} \times ({fmt_num(M_col,0)} \times 100) \times {c_AB:.2f}}}{{{fmt_num(Jc,1)}}} = {fmt_num(vu_moment, 2)} \text{{ ksc}}")
        st.latex(fr"v_{{u,total}} = {fmt_num(vu_shear,2)} + {fmt_num(vu_moment,2)} = {fmt_num(vu_total, 2)} \text{{ ksc}}")
        st.latex(fr"\phi v_c = 0.85 \times 1.06 \times \sqrt{{{fc}}} = {fmt_num(phi_vc, 2)} \text{{ ksc}}")

        if vu_total <= phi_vc:
            st.success(f"✅ **PASS:** หน่วยแรงเฉือนทะลุ $v_u$ ({vu_total:.2f} ksc) $\le \phi v_c$ ({phi_vc:.2f} ksc)")
        else:
            st.error(f"❌ **FAIL:** หน่วยแรงเฉือนทะลุ $v_u$ ({vu_total:.2f} ksc) > $\phi v_c$ ({phi_vc:.2f} ksc)")
