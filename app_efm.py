# app_efm.py
import streamlit as st
import pandas as pd
import math
import calc_efm

def render_efm_tab(calc_obj):
    st.header("📐 Equivalent Frame Method (EFM) - Detailed Design")
    st.markdown("การวิเคราะห์และออกแบบอย่างละเอียดตามมาตรฐาน ACI 318 พร้อมแสดงขั้นตอนการแทนค่า")
    st.markdown("---")
    
    try:
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"❌ Error in Calculation: {e}")
        return

    # --- ฟังก์ชันช่วยจัดฟอร์แมต ---
    def fmt_sci(val): return f"{val:.3e}"
    def fmt_num(val, dec=2): return f"{val:,.{dec}f}"

    # ดึงตัวแปร (สมมติโครงสร้างข้อมูลจาก calc_obj)
    L1_l = calc_obj['geom'].get('L1_l', 6.0) # Span ซ้าย (m)
    L1_r = calc_obj['geom'].get('L1_r', 6.0) # Span ขวา (m)
    L2 = calc_obj['geom'].get('L2', 6.0)     # ความกว้าง Transverse (m)
    c1 = calc_obj['geom']['c1_cm'] / 100.0   # เสาขนาน Span (m)
    c2 = calc_obj['geom']['c2_cm'] / 100.0   # เสาตั้งฉาก Span (m)
    h = calc_obj['geom']['h_slab_cm'] / 100.0# ความหนาพื้น (m)
    
    wu_kgm2 = calc_obj['loads']['wu']
    wu_line = wu_kgm2 * L2  # Load ต่อความยาว (kg/m)
    
    fc = calc_obj['mat']['fc']  # ksc
    fy = calc_obj['mat']['fy']  # ksc

    # ให้ผู้ใช้เลือกตำแหน่งของเสาเพื่อคำนวณ Punching Shear ให้ถูก Case
    st.subheader("📍 Column Location (ตำแหน่งเสา)")
    col_type = st.radio(
        "เลือกประเภทของจุดต่อ (มีผลต่อหน้าตัดวิกฤตแรงเฉือนและ Unbalanced Moment):",
        ["Interior (เสากลาง)", "Edge (เสาริม - โมเมนต์ตั้งฉากขอบ)", "Corner (เสามุม)"],
        horizontal=True
    )

    # =========================================================================
    # 1️⃣ MOMENT ANALYSIS & DISTRIBUTION
    # =========================================================================
    st.subheader("1️⃣ Fixed End Moment & Distribution (สมดุลจุดต่อ)")
    
    # คำนวณ FEM (kg-m)
    FEM_L = (wu_line * (L1_l**2)) / 12 if L1_l > 0 else 0
    FEM_R = (wu_line * (L1_r**2)) / 12 if L1_r > 0 else 0
    
    if col_type == "Edge (เสาริม - โมเมนต์ตั้งฉากขอบ)":
        FEM_L = 0 # สมมติเป็นขอบซ้าย
    elif col_type == "Corner (เสามุม)":
        FEM_L = 0
        
    M_unbal = abs(FEM_L - FEM_R)
    df_col = res.get('df_col', 0.5)
    M_col = M_unbal * df_col

    with st.expander("🔍 ดูสมการและการแทนค่า (Moment Distribution)", expanded=True):
        st.write("**Fixed End Moment (FEM)**")
        st.latex(fr"FEM_{{Right}} = \frac{{w_u L_2 \times L_{{1,R}}^2}}{{12}} = \frac{{{fmt_num(wu_kgm2,0)} \times {L2} \times {L1_r}^2}}{{12}} = {fmt_num(FEM_R, 0)} \text{{ kg-m}}")
        if FEM_L > 0:
            st.latex(fr"FEM_{{Left}} = \frac{{w_u L_2 \times L_{{1,L}}^2}}{{12}} = \frac{{{fmt_num(wu_kgm2,0)} \times {L2} \times {L1_l}^2}}{{12}} = {fmt_num(FEM_L, 0)} \text{{ kg-m}}")
        
        st.write("**Unbalanced Moment at Joint ($M_{unbal}$)**")
        st.latex(fr"M_{{unbal}} = |FEM_{{Left}} - FEM_{{Right}}| = |{fmt_num(FEM_L,0)} - {fmt_num(FEM_R,0)}| = {fmt_num(M_unbal, 0)} \text{{ kg-m}}")
        
        st.write("**Moment Transferred to Column ($M_{sc}$)**")
        st.latex(fr"M_{{sc}} = M_{{unbal}} \times DF_{{col}} = {fmt_num(M_unbal,0)} \times {df_col:.3f} = {fmt_num(M_col, 0)} \text{{ kg-m}}")

    # =========================================================================
    # 2️⃣ STRIP MOMENT DISTRIBUTION (ACI 318)
    # =========================================================================
    st.subheader("2️⃣ Transverse Strip Moment (การแบ่งโมเมนต์ลง Column/Middle Strip)")
    
    Mu_neg = max(FEM_L, FEM_R) # โมเมนต์ลบออกแบบเบื้องต้นที่ Support
    pct_col_neg = 0.75 # ACI Flat Slab (alpha_1 = 0) Support 
    pct_mid_neg = 0.25

    Mu_col_neg = Mu_neg * pct_col_neg
    Mu_mid_neg = Mu_neg * pct_mid_neg

    with st.expander("🔍 ดูสมการและการแทนค่า (Strip Distribution)"):
        st.write("อ้างอิง ACI 318: สำหรับ Flat Slab ($\alpha_1 = 0$) โมเมนต์ลบที่เสาจะลง Column Strip 75% และ Middle Strip 25%")
        st.latex(fr"M_{{u,neg}} = {fmt_num(Mu_neg, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{ColStrip}} = 0.75 \times {fmt_num(Mu_neg,0)} = {fmt_num(Mu_col_neg, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{MidStrip}} = 0.25 \times {fmt_num(Mu_neg,0)} = {fmt_num(Mu_mid_neg, 0)} \text{{ kg-m}}")

    # =========================================================================
    # 3️⃣ FLEXURAL DESIGN (การคำนวณเหล็กเสริม)
    # =========================================================================
    st.subheader("3️⃣ Flexural Design (ออกแบบเหล็กเสริมรับโมเมนต์ดัด)")
    
    cover_cm = 2.5
    db_cm = 1.2
    d_cm = (h * 100) - cover_cm - (db_cm / 2)
    b_col_cm = (min(max(L1_l, L1_r), L2) / 2.0) * 100
    b_mid_cm = (L2 * 100) - b_col_cm

    def design_flexure(Mu_kgm, b_cm, d_cm, fc, fy, name):
        phi = 0.9
        Mu_kgcm = Mu_kgm * 100
        Rn = Mu_kgcm / (phi * b_cm * d_cm**2)
        term = 1 - (2 * Rn) / (0.85 * fc)
        rho_req = (0.85 * fc / fy) * (1 - math.sqrt(term)) if term > 0 else 0
        rho_min = 0.0018 if fy >= 4000 else 0.0020
        rho_des = max(rho_req, rho_min)
        As_req = rho_des * b_cm * d_cm

        st.markdown(f"**การคำนวณ {name} (กว้าง $b$ = {b_cm:.0f} cm, ลึกประสิทธิผล $d$ = {d_cm:.1f} cm)**")
        st.latex(fr"R_n = \frac{{M_u}}{{\phi b d^2}} = \frac{{{fmt_num(Mu_kgcm,0)}}}{{0.9 \times {b_cm:.0f} \times {d_cm:.1f}^2}} = {fmt_num(Rn, 2)} \text{{ ksc}}")
        
        st.latex(fr"\rho_{{req}} = \frac{{0.85 f'_c}}{{f_y}} \left[ 1 - \sqrt{{1 - \frac{{2 R_n}}{{0.85 f'_c}}}} \right] = \frac{{0.85({fc})}}{{{fy}}} \left[ 1 - \sqrt{{1 - \frac{{2({Rn:.2f})}}{{0.85({fc})}}}} \right] = {rho_req:.5f}")
        
        st.latex(fr"A_{{s,req}} = \max(\rho_{{req}}, \rho_{{min}}) \times b \times d = \max({rho_req:.5f}, {rho_min}) \times {b_cm:.0f} \times {d_cm:.1f} = {fmt_num(As_req, 2)} \text{{ cm}}^2")
        return As_req

    with st.expander("🔍 ดูสมการและการแทนค่า (Flexure)", expanded=True):
        As_col = design_flexure(Mu_col_neg, b_col_cm, d_cm, fc, fy, "Column Strip Negative")
        st.divider()
        As_mid = design_flexure(Mu_mid_neg, b_mid_cm, d_cm, fc, fy, "Middle Strip Negative")

    # =========================================================================
    # 4️⃣ PUNCHING SHEAR & UNBALANCED MOMENT (ทุก Case)
    # =========================================================================
    st.subheader("4️⃣ Punching Shear & Unbalanced Moment Transfer")
    st.markdown("ตรวจสอบหน่วยแรงเฉือนทะลุร่วมกับโมเมนต์ดัดที่ไม่สมดุลตามหน้าตัดวิกฤตของเสาแต่ละประเภท")

    # การจัดรูปทรงหน้าตัดวิกฤต (Critical Section Geometry)
    c1_cm, c2_cm = c1*100, c2*100
    
    if "Interior" in col_type:
        b1 = c1_cm + d_cm
        b2 = c2_cm + d_cm
        Ac = 2 * d_cm * (b1 + b2)
        c_AB = b1 / 2.0
        Jc = (d_cm * b1**3 / 6.0) + (b1 * d_cm**3 / 6.0) + (d_cm * b2 * (b1**2) / 2.0)
        # สมการสำหรับโชว์
        Ac_eq = fr"A_c = 2d(b_1 + b_2) = 2({d_cm:.1f})({b1:.1f} + {b2:.1f}) = {fmt_num(Ac,1)} \text{{ cm}}^2"
        Jc_eq = fr"J_c = \frac{{d b_1^3}}{{6}} + \frac{{b_1 d^3}}{{6}} + \frac{{d b_2 b_1^2}}{{2}} = {fmt_num(Jc,1)} \text{{ cm}}^4"
        
    elif "Edge" in col_type:
        b1 = c1_cm + (d_cm / 2.0)
        b2 = c2_cm + d_cm
        Ac = d_cm * (2*b1 + b2)
        c_AB = (b1**2) / (2*b1 + b2) # ระยะจากขอบเสาด้านนอกถึง Centroid
        # Moment of Inertia ของเสาริม
        Jc = (d_cm * b1**3 / 6.0) + (b1 * d_cm**3 / 6.0) + 2*d_cm*b1*((b1/2 - c_AB)**2) + d_cm*b2*(c_AB**2)
        Ac_eq = fr"A_c = d(2b_1 + b_2) = {d_cm:.1f}(2({b1:.1f}) + {b2:.1f}) = {fmt_num(Ac,1)} \text{{ cm}}^2"
        Jc_eq = fr"J_c = \text{{(complex edge eq.)}} = {fmt_num(Jc,1)} \text{{ cm}}^4"
        
    else: # Corner
        b1 = c1_cm + (d_cm / 2.0)
        b2 = c2_cm + (d_cm / 2.0)
        Ac = d_cm * (b1 + b2)
        c_AB = (b1**2) / (2*(b1 + b2))
        Jc = (d_cm * b1**3 / 12.0) + (b1 * d_cm**3 / 12.0) + d_cm*b1*((b1/2 - c_AB)**2) + d_cm*b2*(c_AB**2)
        Ac_eq = fr"A_c = d(b_1 + b_2) = {d_cm:.1f}({b1:.1f} + {b2:.1f}) = {fmt_num(Ac,1)} \text{{ cm}}^2"
        Jc_eq = fr"J_c = \text{{(complex corner eq.)}} = {fmt_num(Jc,1)} \text{{ cm}}^4"

    # สัดส่วนการถ่ายโมเมนต์
    gamma_f = 1.0 / (1.0 + (2.0/3.0) * math.sqrt(b1 / b2))
    gamma_v = 1.0 - gamma_f

    # แรงเฉือนโดยตรง (Vu) - ประมาณการจาก Tributary Area ลบ Critical Area
    trib_area = max(L1_l, L1_r) * L2
    if "Edge" in col_type: trib_area /= 2
    if "Corner" in col_type: trib_area /= 4
    
    crit_area_m2 = (b1 * b2) / 10000.0
    Vu_kg = wu_kgm2 * (trib_area - crit_area_m2)

    # หน่วยแรงเฉือน (ksc)
    vu_shear = Vu_kg / Ac
    vu_moment = (gamma_v * M_col * 100 * c_AB) / Jc if Jc > 0 else 0
    vu_total = vu_shear + vu_moment
    
    phi_vc = 0.85 * 1.06 * math.sqrt(fc) # ACI Metrix: 1.06*sqrt(fc') เทียบเท่า 4*sqrt(fc') ของ US

    with st.expander(f"🔍 ดูสมการและการแทนค่า (Shear & Moment Transfer - {col_type})", expanded=True):
        st.write("**ก. คุณสมบัติหน้าตัดวิกฤต (Critical Section Properties)**")
        st.latex(fr"b_1 = {b1:.1f} \text{{ cm}}, \quad b_2 = {b2:.1f} \text{{ cm}}")
        st.latex(Ac_eq)
        st.latex(fr"c_{{AB}} = {c_AB:.2f} \text{{ cm}}")
        st.latex(Jc_eq)
        
        st.divider()
        st.write("**ข. สัดส่วนการถ่ายเทโมเมนต์ (Transfer Fractions)**")
        st.latex(fr"\gamma_f = \frac{{1}}{{1 + \frac{{2}}{{3}}\sqrt{{\frac{{b_1}}{{b_2}}}}}} = \frac{{1}}{{1 + \frac{{2}}{{3}}\sqrt{{\frac{{{b1:.1f}}}{{{b2:.1f}}}}}}} = {gamma_f:.3f}")
        st.latex(fr"\gamma_v = 1 - \gamma_f = 1 - {gamma_f:.3f} = {gamma_v:.3f}")
        
        st.divider()
        st.write("**ค. การตรวจสอบหน่วยแรงเฉือนทะลุ (Punching Shear Stress)**")
        st.latex(fr"v_{{u(Shear)}} = \frac{{V_u}}{{A_c}} = \frac{{{fmt_num(Vu_kg,0)}}}{{{fmt_num(Ac,1)}}} = {fmt_num(vu_shear, 2)} \text{{ ksc}}")
        st.latex(fr"v_{{u(Moment)}} = \frac{{\gamma_v M_{{sc}} c_{{AB}}}}{{J_c}} = \frac{{{gamma_v:.3f} \times ({fmt_num(M_col,0)} \times 100) \times {c_AB:.2f}}}{{{fmt_num(Jc,1)}}} = {fmt_num(vu_moment, 2)} \text{{ ksc}}")
        st.latex(fr"v_{{u,total}} = {fmt_num(vu_shear,2)} + {fmt_num(vu_moment,2)} = {fmt_num(vu_total, 2)} \text{{ ksc}}")
        
        st.latex(fr"\phi v_c = \phi (1.06\sqrt{{f'_c}}) = 0.85 \times 1.06 \times \sqrt{{{fc}}} = {fmt_num(phi_vc, 2)} \text{{ ksc}}")

    if vu_total <= phi_vc:
        st.success(f"✅ **PASS:** หน่วยแรงเฉือนทะลุ $v_u$ ({vu_total:.2f} ksc) $\le \phi v_c$ ({phi_vc:.2f} ksc)")
    else:
        st.error(f"❌ **FAIL:** หน่วยแรงเฉือนทะลุ $v_u$ ({vu_total:.2f} ksc) > $\phi v_c$ ({phi_vc:.2f} ksc)")
        st.info("💡 **ข้อแนะนำการแก้ไข:** เพิ่มความหนาพื้น, ออกแบบ Drop Panel บริเวณหัวเสา, หรือเสริมเหล็กรับแรงเฉือนทะลุ (Shear Studs / Stirrups)")
