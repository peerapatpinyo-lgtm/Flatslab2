# app_efm.py
import streamlit as st
import pandas as pd
import math
import calc_efm

def render_efm_tab(calc_obj):
    # เอา st.header เดิมออกเพื่อไม่ให้ซ้ำกับ app.py
    st.markdown("วิเคราะห์และออกแบบจุดต่อพื้นไร้คาน (Single Joint Analysis) อย่างละเอียดตามมาตรฐาน ACI 318")
    
    try:
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"❌ Error in Calculation: {e}")
        return

    # --- ฟังก์ชันช่วยจัดฟอร์แมต ---
    def fmt_sci(val): return f"{val:.3e}"
    def fmt_num(val, dec=2): return f"{val:,.{dec}f}"

    # --- ข้อมูล Rebar Database ---
    rebar_db = {
        "DB12": 1.131,
        "DB16": 2.011,
        "DB20": 3.142,
        "DB25": 4.909
    }

    # --- ตัวแปรทางเรขาคณิตและโหลด ---
    L1_l = calc_obj['geom'].get('L1_l', 6.0)
    L1_r = calc_obj['geom'].get('L1_r', 6.0)
    L2 = calc_obj['geom'].get('L2', 6.0)
    c1_cm = calc_obj['geom']['c1_cm']
    c2_cm = calc_obj['geom']['c2_cm']
    h = calc_obj['geom']['h_slab_cm'] / 100.0
    
    wu_kgm2 = calc_obj['loads']['wu']
    wu_line = wu_kgm2 * L2
    fc = calc_obj['mat']['fc']
    fy = calc_obj['mat']['fy']
    
    # ความลึกประสิทธิผล (d)
    cover_cm = 2.5
    db_cm = 1.2
    d_cm = (h * 100) - cover_cm - (db_cm / 2)

    col_type = calc_obj['geom'].get('col_loc', 'Interior Column')
    st.info(f"**📍 ตำแหน่งของจุดต่อ:** `{col_type}` (ความลึกประสิทธิผล $d$ = {d_cm:.1f} cm)")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ Stiffness & DF", 
        "2️⃣ Moment Distribution", 
        "3️⃣ Flexural Design (เลือกเหล็ก)", 
        "4️⃣ Punching Shear"
    ])

    # ------------------------------------------
    # TAB 1: Stiffness & Distribution Factors
    # ------------------------------------------
    with tab1:
        st.subheader("Frame Stiffness & Distribution Factors")
        st.markdown("""
        **ที่มาของการคำนวณ (ตาม ACI 318):**
        * **$K_s$ (Slab Stiffness):** ความแข็งของแผ่นพื้น อ้างอิงจาก $4EI/L$ 
        * **$\Sigma K_c$ (Column Stiffness):** ความแข็งรวมของเสาชั้นบนและชั้นล่าง
        * **$K_t$ (Torsional Stiffness):** ความแข็งต้านทานการบิดของคานขอบหรือแถบพื้นด้านข้าง
        * **$K_{ec}$ (Equivalent Column Stiffness):** ความแข็งเสาเทียบเท่า $\frac{1}{K_{ec}} = \frac{1}{\Sigma K_c} + \frac{1}{K_t}$
        """)
        
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
    # TAB 2: Moment Distribution
    # ------------------------------------------
    with tab2:
        st.subheader("Longitudinal Moment Analysis")
        st.markdown("**1. คำนวณ Fixed End Moment (FEM)** สมมติปลายยึดแน่นทั้งสองข้าง")
        
        FEM_L = (wu_line * (L1_l**2)) / 12 if L1_l > 0 else 0
        FEM_R = (wu_line * (L1_r**2)) / 12 if L1_r > 0 else 0
        if "Edge" in col_type or "Corner" in col_type: FEM_L = 0 
            
        M_unbal = abs(FEM_L - FEM_R)
        M_col = M_unbal * df_col
        M_slab_dist = M_unbal * df_slab
        Mu_neg = max(FEM_L, FEM_R) - (M_slab_dist / 2)

        st.latex(fr"FEM_{{Right}} = \frac{{w_u L_2 \times L_{{1,R}}^2}}{{12}} = \frac{{{fmt_num(wu_kgm2,0)} \times {L2:.2f} \times {L1_r:.2f}^2}}{{12}} = {fmt_num(FEM_R, 0)} \text{{ kg-m}}")
        if FEM_L > 0:
            st.latex(fr"FEM_{{Left}} = \frac{{w_u L_2 \times L_{{1,L}}^2}}{{12}} = {fmt_num(FEM_L, 0)} \text{{ kg-m}}")
        
        st.markdown("**2. คำนวณ Unbalanced Moment และกระจายลงจุดต่อ**")
        st.latex(fr"M_{{unbal}} = |FEM_{{Left}} - FEM_{{Right}}| = {fmt_num(M_unbal, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{col}} = M_{{unbal}} \times DF_{{col}} = {fmt_num(M_col, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{slab}} = M_{{unbal}} \times DF_{{slab}} = {fmt_num(M_slab_dist, 0)} \text{{ kg-m}}")
        
        st.markdown("**3. โมเมนต์ลบสุทธิสำหรับออกแบบแผ่นพื้น ($M_{u,neg}$)**")
        st.latex(fr"M_{{u,neg}} = \max(FEM_{{L}}, FEM_{{R}}) - \frac{{M_{{slab}}}}{{2}} = {fmt_num(Mu_neg, 0)} \text{{ kg-m}}")

    # ------------------------------------------
    # TAB 3: Flexural Design & Rebar Selection
    # ------------------------------------------
    with tab3:
        st.subheader("Transverse Strip & Flexural Design")
        st.markdown("แบ่งโมเมนต์ดัดลบลง Column Strip (75%) และ Middle Strip (25%) พร้อมจัดเหล็กเสริมจริง")
        
        pct_col_neg = 0.75
        Mu_col_neg = Mu_neg * pct_col_neg
        Mu_mid_neg = Mu_neg * (1 - pct_col_neg)
        
        b_col_cm = (min(max(L1_l, L1_r), L2) / 2.0) * 100
        b_mid_cm = (L2 * 100) - b_col_cm

        def design_flexure_detailed(Mu_kgm, b_cm, d_cm, fc, fy, strip_name):
            phi = 0.9
            Mu_kgcm = Mu_kgm * 100
            Rn = Mu_kgcm / (phi * b_cm * d_cm**2) if b_cm > 0 and d_cm > 0 else 0
            term = 1 - (2 * Rn) / (0.85 * fc)
            rho_req = (0.85 * fc / fy) * (1 - math.sqrt(term)) if term > 0 else 0
            rho_min = 0.0018 if fy >= 4000 else 0.0020
            rho_des = max(rho_req, rho_min)
            As_req = rho_des * b_cm * d_cm
            
            with st.expander(f"📝 รายการคำนวณ {strip_name}"):
                st.latex(fr"R_n = \frac{{M_u}}{{\phi b d^2}} = \frac{{{fmt_num(Mu_kgcm,0)}}}{{0.9 \times {b_cm:.0f} \times {d_cm:.1f}^2}} = {fmt_num(Rn, 2)} \text{{ ksc}}")
                st.latex(fr"\rho_{{req}} = \frac{{0.85 f'_c}}{{f_y}} \left( 1 - \sqrt{{1 - \frac{{2R_n}}{{0.85f'_c}}}} \right) = {rho_req:.5f}")
                st.markdown(f"*ใช้ $\\rho$ ออกแบบที่ {rho_des:.5f} (ควบคุมด้วย $\\rho_{{min}} = {rho_min}$)*" if rho_min > rho_req else f"*ใช้ $\\rho$ ออกแบบที่ {rho_des:.5f}*")
                st.latex(fr"A_{{s,req}} = \rho_{{des}} b d = {rho_des:.5f} \times {b_cm:.0f} \times {d_cm:.1f} = {fmt_num(As_req, 2)} \text{{ cm}}^2")
            
            return As_req

        def user_rebar_selection(As_req, b_cm, key_prefix):
            c1, c2 = st.columns(2)
            with c1:
                rb_size = st.selectbox("ขนาดเหล็ก", options=list(rebar_db.keys()), key=f"{key_prefix}_size")
            with c2:
                spacing = st.number_input("ระยะ @ (cm)", min_value=5.0, max_value=30.0, value=20.0, step=2.5, key=f"{key_prefix}_sp")
            
            As_per_bar = rebar_db[rb_size]
            As_prov = (100 / spacing) * As_per_bar * (b_cm / 100) # พื้นที่เหล็กทั้งหมดในแถบความกว้าง b
            
            st.markdown(f"**$A_{{s,prov}}$ (ให้จริง):** {fmt_num(As_prov, 2)} cm² / แถบความกว้าง {b_cm:.0f} cm")
            
            if As_prov >= As_req:
                st.success("✅ **ผ่าน:** ให้เหล็กเพียงพอ")
            else:
                st.error("❌ **ไม่ผ่าน:** กรุณาลดระยะแอด (@) หรือเพิ่มขนาดเหล็ก")

        c_col1, c_col2 = st.columns(2)
        
        with c_col1:
            st.markdown(f"#### 🟥 Column Strip ($b = {b_col_cm:.0f}$ cm)")
            st.markdown(f"**$M_u$ = {fmt_num(Mu_col_neg, 0)} kg-m**")
            As_req_col = design_flexure_detailed(Mu_col_neg, b_col_cm, d_cm, fc, fy, "Column Strip")
            st.info(f"**ต้องการ $A_{{s,req}}$ = {fmt_num(As_req_col, 2)} cm²**")
            user_rebar_selection(As_req_col, b_col_cm, "col_strip")

        with c_col2:
            st.markdown(f"#### 🟦 Middle Strip ($b = {b_mid_cm:.0f}$ cm)")
            st.markdown(f"**$M_u$ = {fmt_num(Mu_mid_neg, 0)} kg-m**")
            As_req_mid = design_flexure_detailed(Mu_mid_neg, b_mid_cm, d_cm, fc, fy, "Middle Strip")
            st.info(f"**ต้องการ $A_{{s,req}}$ = {fmt_num(As_req_mid, 2)} cm²**")
            user_rebar_selection(As_req_mid, b_mid_cm, "mid_strip")

    # ------------------------------------------
    # TAB 4: Punching Shear & Unbalanced Moment
    # ------------------------------------------
    with tab4:
        st.subheader("Punching Shear & Unbalanced Moment")
        st.markdown("ตรวจสอบหน้าตัดวิกฤตที่ระยะ $d/2$ จากขอบเสา (รับแรงเฉือนร่วมกับโมเมนต์ไม่สมดุล)")
        
        if "Interior" in col_type:
            b1, b2 = c1_cm + d_cm, c2_cm + d_cm
            Ac = 2 * d_cm * (b1 + b2)
            c_AB = b1 / 2.0
            Jc = (d_cm * b1**3 / 6.0) + (b1 * d_cm**3 / 6.0) + (d_cm * b2 * (b1**2) / 2.0)
        elif "Edge" in col_type:
            b1, b2 = c1_cm + (d_cm / 2.0), c2_cm + d_cm
            Ac = d_cm * (2*b1 + b2)
            c_AB = (b1**2) / (2*b1 + b2)
            Jc = (d_cm * b1**3 / 6.0) + (b1 * d_cm**3 / 6.0) + 2*d_cm*b1*((b1/2 - c_AB)**2) + d_cm*b2*(c_AB**2)
        else: # Corner
            b1, b2 = c1_cm + (d_cm / 2.0), c2_cm + (d_cm / 2.0)
            Ac = d_cm * (b1 + b2)
            c_AB = (b1**2) / (2*(b1 + b2))
            Jc = (d_cm * b1**3 / 12.0) + (b1 * d_cm**3 / 12.0) + d_cm*b1*((b1/2 - c_AB)**2) + d_cm*b2*(c_AB**2)

        gamma_f = 1.0 / (1.0 + (2.0/3.0) * math.sqrt(b1 / b2)) if b2 > 0 else 1.0
        gamma_v = 1.0 - gamma_f
        
        trib_area = max(L1_l, L1_r) * L2
        if "Edge" in col_type: trib_area /= 2
        if "Corner" in col_type: trib_area /= 4
        
        crit_area_m2 = (b1 * b2) / 10000.0
        Vu_kg = wu_kgm2 * (trib_area - crit_area_m2)

        vu_shear = Vu_kg / Ac if Ac > 0 else 0
        vu_moment = (gamma_v * M_col * 100 * c_AB) / Jc if Jc > 0 else 0
        vu_total = vu_shear + vu_moment
        phi_vc = 0.85 * 1.06 * math.sqrt(fc)

        with st.expander("📝 ดูรายการคำนวณ Punching Shear แบบละเอียด", expanded=True):
            st.markdown("**1. คุณสมบัติหน้าตัดวิกฤต (Critical Section Properties)**")
            st.latex(fr"A_c = {fmt_num(Ac,1)} \text{{ cm}}^2 \quad (\text{{พื้นที่หน้าตัดรับแรงเฉือน}})")
            st.latex(fr"J_c = {fmt_num(Jc,1)} \text{{ cm}}^4 \quad (\text{{Polar Moment of Inertia}})")
            st.latex(fr"c_{{AB}} = {c_AB:.2f} \text{{ cm}} \quad (\text{{ระยะจากเซนทรอยด์ถึงขอบหน้าตัด}})")

            st.markdown("**2. สัดส่วนการถ่ายโอนโมเมนต์ (Transfer Fractions)**")
            st.latex(fr"\gamma_f = \frac{{1}}{{1 + \frac{{2}}{{3}}\sqrt{{\frac{{b_1}}{{b_2}}}}}} = {gamma_f:.3f} \quad (\text{{รับด้วยการดัด}})")
            st.latex(fr"\gamma_v = 1 - \gamma_f = {gamma_v:.3f} \quad (\text{{รับด้วยแรงเฉือน}})")

            st.markdown("**3. ตรวจสอบหน่วยแรง (Stress Check)**")
            st.latex(fr"v_{{u(Shear)}} = \frac{{V_u}}{{A_c}} = \frac{{{fmt_num(Vu_kg,0)}}}{{{fmt_num(Ac,1)}}} = {fmt_num(vu_shear, 2)} \text{{ ksc}}")
            st.latex(fr"v_{{u(Moment)}} = \frac{{\gamma_v M_{{col}} c_{{AB}}}}{{J_c}} = \frac{{{gamma_v:.3f} \times ({fmt_num(M_col,0)} \times 100) \times {c_AB:.2f}}}{{{fmt_num(Jc,1)}}} = {fmt_num(vu_moment, 2)} \text{{ ksc}}")
            st.latex(fr"\mathbf{{v_{{u,total}}}} = v_{{u(Shear)}} + v_{{u(Moment)}} = {fmt_num(vu_total, 2)} \text{{ ksc}}")
            st.latex(fr"\phi v_c = 0.85 \times 1.06 \times \sqrt{{{fc}}} = {fmt_num(phi_vc, 2)} \text{{ ksc}}")

        if vu_total <= phi_vc:
            st.success(f"✅ **PASS:** หน่วยแรงเฉือนทะลุ $v_u$ ({vu_total:.2f} ksc) $\le \phi v_c$ ({phi_vc:.2f} ksc)")
        else:
            st.error(f"❌ **FAIL:** หน่วยแรงเฉือนทะลุ $v_u$ ({vu_total:.2f} ksc) > $\phi v_c$ ({phi_vc:.2f} ksc) — แนะนำให้เพิ่มความหนาพื้นหรือใส่ Drop Panel/Shear Stud")
