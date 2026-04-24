# app_efm.py
import streamlit as st
import pandas as pd
import math
import calc_efm
import draw_rebar  # ✅ นำเข้าไฟล์ใหม่ที่เพิ่งสร้าง

def render_efm_tab(calc_obj):
    st.markdown("Detailed single joint analysis and design of flat slabs according to ACI 318 Equivalent Frame Method (EFM).")
    
    try:
        res = calc_efm.calculate_efm(calc_obj)
    except Exception as e:
        st.error(f"❌ Error in Calculation: {e}")
        return

    # --- Formatting Helpers ---
    def fmt_sci(val): return f"{val:.3e}"
    def fmt_num(val, dec=2): return f"{val:,.{dec}f}"

    # --- Rebar Database ---
    rebar_db = {
        "DB12": 1.131,
        "DB16": 2.011,
        "DB20": 3.142,
        "DB25": 4.909
    }

    # --- Geometry & Load Variables ---
    L1_l = calc_obj['geom'].get('L1_l', 6.0)
    L1_r = calc_obj['geom'].get('L1_r', 6.0)
    L2 = calc_obj['geom'].get('L2', 6.0)
    c1_cm = calc_obj['geom']['c1_cm']
    c2_cm = calc_obj['geom']['c2_cm']
    h_cm = calc_obj['geom']['h_slab_cm']
    h = h_cm / 100.0
    
    # Define column height for stiffness (defaulting to 3.0m if not explicitly provided)
    Lc_m = calc_obj['geom'].get('H_col_m', 3.0) 
    Lc_cm = Lc_m * 100.0
    
    wu_kgm2 = calc_obj['loads']['wu']
    wu_line = wu_kgm2 * L2
    fc = calc_obj['mat']['fc']
    fy = calc_obj['mat']['fy']
    
    # Effective Depth (d)
    cover_cm = 2.5
    db_cm = 1.2
    d_cm = h_cm - cover_cm - (db_cm / 2.0)

    # ACI 318 Maximum Spacing Limit for Slabs: min(2h, 45 cm)
    s_max = min(2 * h_cm, 45.0)

    col_type = calc_obj['geom'].get('col_loc', 'Interior Column')
    st.info(f"**📍 Joint Location:** `{col_type}` | **Effective depth $d$:** {d_cm:.1f} cm | **Max Spacing Limit:** {s_max:.1f} cm")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1️⃣ Stiffness & DF", 
        "2️⃣ Moment Distribution", 
        "3️⃣ Flexural Design (Rebar)", 
        "4️⃣ Punching Shear",
        "5️⃣ Drafting Details"
    ])

    # ------------------------------------------
    # TAB 1: Stiffness & Distribution Factors
    # ------------------------------------------
    with tab1:
        st.subheader("Frame Stiffness & Distribution Factors")
        st.markdown("Calculation of member stiffnesses to determine Moment Distribution Factors (DF).")
        
        c1_stiff, c2_stiff, c3_stiff, c4_stiff = st.columns(4)
        Kec_val = res.get('Kec', 0)
        Ks_val = res.get('Ks', 0)
        Kt_val = res.get('Kt', 0)
        Kc_val = res.get('Sum_Kc', 0)
        
        c1_stiff.metric("Slab ($K_s$)", fmt_sci(Ks_val))
        c2_stiff.metric("Column ($\Sigma K_c$)", fmt_sci(Kc_val))
        c3_stiff.metric("Torsion ($K_t$)", fmt_sci(Kt_val))
        c4_stiff.metric("Equiv. Col ($K_{ec}$)", fmt_sci(Kec_val))

        df_slab = res.get('df_slab', 0.5)
        df_col = res.get('df_col', 0.5)

        st.latex(fr"DF_{{col}} = \frac{{K_{{ec}}}}{{K_{{ec}} + \Sigma K_s}} = \frac{{{fmt_sci(Kec_val)}}}{{{fmt_sci(Kec_val)} + {fmt_sci(Ks_val)}}} = {df_col:.4f}")
        st.latex(fr"DF_{{slab}} = \frac{{\Sigma K_s}}{{K_{{ec}} + \Sigma K_s}} = \frac{{{fmt_sci(Ks_val)}}}{{{fmt_sci(Kec_val)} + {fmt_sci(Ks_val)}}} = {df_slab:.4f}")

        with st.expander("📝 Explicit Stiffness Calculations (Base Properties)", expanded=True):
            Ec = 15100 * math.sqrt(fc)
            L2_cm = L2 * 100
            L1_avg_m = ((L1_l + L1_r) / 2) if (L1_l > 0 and L1_r > 0) else max(L1_l, L1_r)
            L1_cm = L1_avg_m * 100
            
            Is = (L2_cm * (h_cm**3)) / 12
            Ic = (c2_cm * (c1_cm**3)) / 12
            
            x_t, y_t = min(h_cm, c1_cm), max(h_cm, c1_cm)
            C_val = (1 - 0.63 * (x_t / y_t)) * (x_t**3) * y_t / 3.0
            
            st.markdown("**0. Material & Section Properties**")
            st.latex(fr"E_c = 15100 \sqrt{{f'_c}} = 15100 \sqrt{{{fc}}} = {fmt_num(Ec, 0)} \text{{ ksc}}")
            st.latex(fr"I_s = \frac{{l_2 h^3}}{{12}} = \frac{{{L2_cm:.0f} \times {h_cm:.0f}^3}}{{12}} = {fmt_num(Is, 0)} \text{{ cm}}^4")
            st.latex(fr"I_c = \frac{{c_2 c_1^3}}{{12}} = \frac{{{c2_cm:.0f} \times {c1_cm:.0f}^3}}{{12}} = {fmt_num(Ic, 0)} \text{{ cm}}^4")
            st.latex(fr"C = \left(1 - 0.63\frac{{x}}{{y}}\right) \frac{{x^3 y}}{{3}} = \left(1 - 0.63\frac{{{x_t:.1f}}}{{{y_t:.1f}}}\right) \frac{{{x_t:.1f}^3 \times {y_t:.1f}}}{{3}} = {fmt_num(C_val, 0)} \text{{ cm}}^4")

            st.markdown("**1. Slab Stiffness ($K_s$)** *(Assumed prismatic for explicit check)*")
            st.latex(fr"K_s \approx \frac{{4 E_c I_s}}{{L_1}} = \frac{{4 \times {fmt_num(Ec, 0)} \times {fmt_num(Is, 0)}}}{{{L1_cm:.0f}}} = {fmt_sci((4 * Ec * Is) / L1_cm)}")
            
            st.markdown("**2. Column Stiffness ($\Sigma K_c$)** *(Sum of top and bottom columns)*")
            st.latex(fr"\Sigma K_c \approx 2 \times \left(\frac{{4 E_c I_c}}{{L_c}}\right) = 2 \times \left(\frac{{4 \times {fmt_num(Ec, 0)} \times {fmt_num(Ic, 0)}}}{{{Lc_cm:.0f}}}\right) = {fmt_sci(2 * (4 * Ec * Ic) / Lc_cm)}")
            
            st.markdown("**3. Torsional Stiffness ($K_t$)**")
            c2_ratio = c2_cm / L2_cm if L2_cm > 0 else 0
            Kt_calc = (9 * Ec * C_val) / (L2_cm * (1 - c2_ratio)**3) if L2_cm > 0 else 0
            st.latex(fr"K_t = \frac{{9 E_c C}}{{l_2 \left(1 - \frac{{c_2}}{{l_2}}\right)^3}} = \frac{{9 \times {fmt_num(Ec, 0)} \times {fmt_num(C_val, 0)}}}{{{L2_cm:.0f} \left(1 - \frac{{{c2_cm:.0f}}}{{{L2_cm:.0f}}}\right)^3}} = {fmt_sci(Kt_calc)}")
            
            st.markdown("**4. Equivalent Column Stiffness ($K_{ec}$)**")
            st.latex(fr"K_{{ec}} = \frac{{\Sigma K_c \times K_t}}{{\Sigma K_c + K_t}} = \frac{{{fmt_sci(Kc_val)} \times {fmt_sci(Kt_val)}}}{{{fmt_sci(Kc_val)} + {fmt_sci(Kt_val)}}} = {fmt_sci(Kec_val)}")
            
            st.caption("*Note: The strict calculations in `calc_efm.py` may incorporate infinite joint rigidity modifiers resulting in slight variations from the purely prismatic $4EI/L$ approximations shown above, but the distribution logic remains identical.*")

    # ------------------------------------------
    # TAB 2: Moment Distribution
    # ------------------------------------------
    with tab2:
        st.subheader("Longitudinal Moment Analysis")
        st.markdown("**1. Negative Moments (Support)**")
        
        FEM_L = (wu_line * (L1_l**2)) / 12 if L1_l > 0 else 0
        FEM_R = (wu_line * (L1_r**2)) / 12 if L1_r > 0 else 0
        if "Edge" in col_type or "Corner" in col_type: FEM_L = 0 
            
        M_unbal = abs(FEM_L - FEM_R)
        M_col = M_unbal * df_col
        M_slab_dist = M_unbal * df_slab
        Mu_neg = max(FEM_L, FEM_R) - (M_slab_dist / 2)

        st.latex(fr"FEM_{{Right}} = \frac{{w_u l_2 l_{{1,R}}^2}}{{12}} = \frac{{{fmt_num(wu_kgm2,0)} \times {L2:.2f} \times {L1_r:.2f}^2}}{{12}} = {fmt_num(FEM_R, 0)} \text{{ kg-m}}")
        if FEM_L > 0:
            st.latex(fr"FEM_{{Left}} = \frac{{w_u l_2 l_{{1,L}}^2}}{{12}} = \frac{{{fmt_num(wu_kgm2,0)} \times {L2:.2f} \times {L1_l:.2f}^2}}{{12}} = {fmt_num(FEM_L, 0)} \text{{ kg-m}}")
        
        st.latex(fr"M_{{unbal}} = |FEM_{{Left}} - FEM_{{Right}}| = |{fmt_num(FEM_L, 0)} - {fmt_num(FEM_R, 0)}| = {fmt_num(M_unbal, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{col}} = M_{{unbal}} \times DF_{{col}} = {fmt_num(M_unbal, 0)} \times {df_col:.4f} = {fmt_num(M_col, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{slab}} = M_{{unbal}} \times DF_{{slab}} = {fmt_num(M_unbal, 0)} \times {df_slab:.4f} = {fmt_num(M_slab_dist, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{u,neg}} = \max(FEM_{{L}}, FEM_{{R}}) - \frac{{M_{{slab}}}}{{2}} = {fmt_num(max(FEM_L, FEM_R), 0)} - \frac{{{fmt_num(M_slab_dist, 0)}}}{{2}} = {fmt_num(Mu_neg, 0)} \text{{ kg-m}}")

        st.markdown("---")
        st.markdown("**2. Positive Moments (Mid-Span)**")
        
        max_L1 = max(L1_l, L1_r)
        M0_max = (wu_line * max_L1**2) / 8
        if "Edge" in col_type or "Corner" in col_type:
            Mu_pos = 0.50 * M0_max
            coef_txt = "0.50"
        else:
            Mu_pos = 0.35 * M0_max
            coef_txt = "0.35"
        
        st.latex(fr"M_0 = \frac{{w_u l_2 l_{{1}}^2}}{{8}} = \frac{{{fmt_num(wu_kgm2,0)} \times {L2:.2f} \times {max_L1:.2f}^2}}{{8}} = {fmt_num(M0_max, 0)} \text{{ kg-m}}")
        st.latex(fr"M_{{u,pos}} \approx {coef_txt} M_0 = {coef_txt} \times {fmt_num(M0_max, 0)} = {fmt_num(Mu_pos, 0)} \text{{ kg-m}}")

    # ------------------------------------------
    # TAB 3: Flexural Design & Rebar Selection
    # ------------------------------------------
    with tab3:
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
            
            with st.expander(f"📝 Calculations: {strip_name}"):
                st.latex(fr"R_n = \frac{{M_u}}{{\phi b d^2}} = \frac{{{fmt_num(Mu_kgcm,0)}}}{{0.9 \times {b_cm:.0f} \times {d_cm:.1f}^2}} = {fmt_num(Rn, 2)} \text{{ ksc}}")
                st.latex(fr"\rho_{{req}} = \frac{{0.85 f'_c}}{{f_y}} \left( 1 - \sqrt{{1 - \frac{{2R_n}}{{0.85f'_c}}}} \right) = \frac{{0.85({fc})}}{{{fy}}} \left( 1 - \sqrt{{1 - \frac{{2({Rn:.2f})}}{{0.85({fc})}}}} \right) = {rho_req:.5f}")
                
                if rho_min > rho_req:
                    st.latex(fr"\rho_{{des}} = \max(\rho_{{req}}, \rho_{{min}}) = \max({rho_req:.5f}, {rho_min}) = {rho_des:.5f}")
                else:
                    st.latex(fr"\rho_{{des}} = \rho_{{req}} = {rho_des:.5f}")
                    
                st.latex(fr"A_{{s,req}} = \rho_{{des}} b d = {rho_des:.5f} \times {b_cm:.0f} \times {d_cm:.1f} = {fmt_num(As_req, 2)} \text{{ cm}}^2")
            return As_req

        def user_rebar_selection(As_req, b_cm, key_prefix):
            c1, c2 = st.columns(2)
            with c1:
                rb_size = st.selectbox("Rebar Size", options=list(rebar_db.keys()), key=f"{key_prefix}_size")
            with c2:
                spacing = st.number_input("Spacing @ (cm)", min_value=5.0, max_value=50.0, value=20.0, step=2.5, key=f"{key_prefix}_sp")
            
            As_per_bar = rebar_db[rb_size]
            As_prov = (100 / spacing) * As_per_bar * (b_cm / 100)
            
            st.latex(fr"A_{{s,prov}} = \left(\frac{{100}}{{s}}\right) A_{{b}} \left(\frac{{b}}{{100}}\right) = \left(\frac{{100}}{{{spacing}}}\right) \times {As_per_bar} \times \left(\frac{{{b_cm:.0f}}}{{100}}\right) = {fmt_num(As_prov, 2)} \text{{ cm}}^2")
            
            if spacing > s_max:
                st.error(f"❌ **FAIL:** Spacing exceeds ACI limit ($s_{{max}} = {s_max:.1f}$ cm)")
            elif As_prov >= As_req:
                st.success("✅ **PASS:** Sufficient reinforcement")
            else:
                st.error("❌ **FAIL:** Increase rebar size or decrease spacing.")
            
            return rb_size, spacing

        st.subheader("1. Support Section (Top Reinforcement)")
        st.markdown("Negative moment distribution: Column Strip (75%), Middle Strip (25%)")
        
        Mu_col_neg = Mu_neg * 0.75
        Mu_mid_neg = Mu_neg * 0.25
        
        c_top1, c_top2 = st.columns(2)
        with c_top1:
            st.markdown(f"#### 🟥 Column Strip ($M_u = {fmt_num(Mu_col_neg, 0)}$)")
            As_req_col_top = design_flexure_detailed(Mu_col_neg, b_col_cm, d_cm, fc, fy, "Col Strip - Top")
            top_col_sz, top_col_sp = user_rebar_selection(As_req_col_top, b_col_cm, "col_top")

        with c_top2:
            st.markdown(f"#### 🟦 Middle Strip ($M_u = {fmt_num(Mu_mid_neg, 0)}$)")
            As_req_mid_top = design_flexure_detailed(Mu_mid_neg, b_mid_cm, d_cm, fc, fy, "Mid Strip - Top")
            top_mid_sz, top_mid_sp = user_rebar_selection(As_req_mid_top, b_mid_cm, "mid_top")

        st.markdown("---")

        st.subheader("2. Mid-Span Section (Bottom Reinforcement)")
        st.markdown("Positive moment distribution: Column Strip (60%), Middle Strip (40%)")
        
        Mu_col_pos = Mu_pos * 0.60
        Mu_mid_pos = Mu_pos * 0.40
        
        c_bot1, c_bot2 = st.columns(2)
        with c_bot1:
            st.markdown(f"#### 🟥 Column Strip ($M_u = {fmt_num(Mu_col_pos, 0)}$)")
            As_req_col_bot = design_flexure_detailed(Mu_col_pos, b_col_cm, d_cm, fc, fy, "Col Strip - Bottom")
            bot_col_sz, bot_col_sp = user_rebar_selection(As_req_col_bot, b_col_cm, "col_bot")

        with c_bot2:
            st.markdown(f"#### 🟦 Middle Strip ($M_u = {fmt_num(Mu_mid_pos, 0)}$)")
            As_req_mid_bot = design_flexure_detailed(Mu_mid_pos, b_mid_cm, d_cm, fc, fy, "Mid Strip - Bottom")
            bot_mid_sz, bot_mid_sp = user_rebar_selection(As_req_mid_bot, b_mid_cm, "mid_bot")

    # ------------------------------------------
    # TAB 4: Punching Shear & Unbalanced Moment
    # ------------------------------------------
    with tab4:
        st.subheader("Punching Shear & Unbalanced Moment")
        st.markdown("Checking the critical section at $d/2$ from the column face.")
        
        if "Interior" in col_type:
            b1, b2 = c1_cm + d_cm, c2_cm + d_cm
            Ac = 2 * d_cm * (b1 + b2)
            c_AB = b1 / 2.0
            Jc = (d_cm * b1**3 / 6.0) + (b1 * d_cm**3 / 6.0) + (d_cm * b2 * (b1**2) / 2.0)
            
            Ac_str = fr"2d(b_1 + b_2) = 2({d_cm:.1f})({b1:.1f} + {b2:.1f})"
            cAB_str = fr"\frac{{b_1}}{{2}} = \frac{{{b1:.1f}}}{{2}}"
        elif "Edge" in col_type:
            b1, b2 = c1_cm + (d_cm / 2.0), c2_cm + d_cm
            Ac = d_cm * (2*b1 + b2)
            c_AB = (b1**2) / (2*b1 + b2)
            Jc = (d_cm * b1**3 / 6.0) + (b1 * d_cm**3 / 6.0) + 2*d_cm*b1*((b1/2 - c_AB)**2) + d_cm*b2*(c_AB**2)
            
            Ac_str = fr"d(2b_1 + b_2) = {d_cm:.1f}(2({b1:.1f}) + {b2:.1f})"
            cAB_str = fr"\frac{{b_1^2}}{{2b_1 + b_2}} = \frac{{{b1:.1f}^2}}{{2({b1:.1f}) + {b2:.1f}}}"
        else: # Corner
            b1, b2 = c1_cm + (d_cm / 2.0), c2_cm + (d_cm / 2.0)
            Ac = d_cm * (b1 + b2)
            c_AB = (b1**2) / (2*(b1 + b2))
            Jc = (d_cm * b1**3 / 12.0) + (b1 * d_cm**3 / 12.0) + d_cm*b1*((b1/2 - c_AB)**2) + d_cm*b2*(c_AB**2)
            
            Ac_str = fr"d(b_1 + b_2) = {d_cm:.1f}({b1:.1f} + {b2:.1f})"
            cAB_str = fr"\frac{{b_1^2}}{{2(b_1 + b_2)}} = \frac{{{b1:.1f}^2}}{{2({b1:.1f} + {b2:.1f})}}"

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

        with st.expander(r"📝 Detailed Punching Shear Calculations", expanded=True):
            st.latex(fr"A_c = {Ac_str} = {fmt_num(Ac,1)} \text{{ cm}}^2")
            st.latex(fr"c_{{AB}} = {cAB_str} = {fmt_num(c_AB,2)} \text{{ cm}}")
            st.latex(fr"J_c = {fmt_num(Jc,1)} \text{{ cm}}^4")
            
            st.latex(fr"\gamma_f = \frac{{1}}{{1 + \frac{{2}}{{3}}\sqrt{{\frac{{b_1}}{{b_2}}}}}} = \frac{{1}}{{1 + \frac{{2}}{{3}}\sqrt{{\frac{{{b1:.1f}}}{{{b2:.1f}}}}}}} = {gamma_f:.3f}")
            st.latex(fr"\gamma_v = 1 - \gamma_f = 1 - {gamma_f:.3f} = {gamma_v:.3f}")
            
            st.latex(fr"V_u = w_u (A_{{trib}} - A_{{crit}}) = {fmt_num(wu_kgm2,0)} \times ({trib_area:.2f} - {crit_area_m2:.4f}) = {fmt_num(Vu_kg,0)} \text{{ kg}}")
            
            st.latex(fr"v_{{u(Shear)}} = \frac{{V_u}}{{A_c}} = \frac{{{fmt_num(Vu_kg,0)}}}{{{fmt_num(Ac,1)}}} = {fmt_num(vu_shear, 2)} \text{{ ksc}}")
            st.latex(fr"v_{{u(Moment)}} = \frac{{\gamma_v M_{{col}} c_{{AB}}}}{{J_c}} = \frac{{{gamma_v:.3f} \times ({fmt_num(M_col,0)} \times 100) \times {c_AB:.2f}}}{{{fmt_num(Jc,1)}}} = {fmt_num(vu_moment, 2)} \text{{ ksc}}")
            st.latex(fr"\mathbf{{v_{{u,total}}}} = v_{{u(Shear)}} + v_{{u(Moment)}} = {fmt_num(vu_shear, 2)} + {fmt_num(vu_moment, 2)} = {fmt_num(vu_total, 2)} \text{{ ksc}}")
            st.latex(fr"\phi v_c = 0.85 \times 1.06 \times \sqrt{{f'_c}} = 0.85 \times 1.06 \times \sqrt{{{fc}}} = {fmt_num(phi_vc, 2)} \text{{ ksc}}")

        if vu_total <= phi_vc:
            st.success(f"✅ **PASS:** Punching shear safe.")
        else:
            st.error(f"❌ **FAIL:** Exceeds capacity. Thicken slab or add shear reinforcement.")


# ------------------------------------------
    # TAB 5: Drafting Details
    # ------------------------------------------
    with tab5:
        draw_rebar.draw_drafting_details(
            L1_l=L1_l, 
            L1_r=L1_r, 
            L2=L2, 
            c1_cm=c1_cm, 
            c2_cm=c2_cm, 
            h_cm=h_cm, 
            top_col_sz=top_col_sz, 
            top_col_sp=top_col_sp, 
            bot_col_sz=bot_col_sz, 
            bot_col_sp=bot_col_sp,
            top_mid_sz=top_mid_sz,    # ✅ เพิ่มเหล็กบน Middle Strip
            top_mid_sp=top_mid_sp,    # ✅ เพิ่มระยะแอดบน Middle Strip
            bot_mid_sz=bot_mid_sz,    # ✅ เพิ่มเหล็กล่าง Middle Strip
            bot_mid_sp=bot_mid_sp     # ✅ เพิ่มระยะแอดล่าง Middle Strip
        )
