import pandas as pd
import numpy as np

def get_moment_coefficients(case_type, has_edge_beam):
    if case_type == "Interior":
        return {'neg_int': 0.65, 'pos': 0.35, 'neg_ext': 0.65} 
    else: # "Exterior" 
        if has_edge_beam:
            return {'neg_int': 0.70, 'pos': 0.50, 'neg_ext': 0.30}
        else:
            return {'neg_int': 0.70, 'pos': 0.52, 'neg_ext': 0.26}

def calculate_ddm(inputs):
    results = []
    messages = []
    details = {}
    
    # --- 1. Unpack Inputs ---
    try:
        l1 = float(inputs['l1'])
        l2 = float(inputs['l2'])
        ln_actual = float(inputs['ln'])
        wu = float(inputs['wu'])
        
        c1 = float(inputs['c1']) # ขนาดเสาขนาน l1 (m)
        c2 = float(inputs['c2']) # ขนาดเสาขนาน l2 (m)
        
        h_slab = float(inputs['h_slab']) # cm
        h_drop = float(inputs.get('h_drop', h_slab)) # cm
        has_drop = inputs.get('has_drop', False)
        
        fc = float(inputs['fc'])
        fy = float(inputs['fy'])
        
        case_type = inputs.get('case_type', 'Interior')
        has_edge_beam = inputs.get('has_edge_beam', False)
        eb_width = float(inputs.get('eb_width', 0)) * 100 # cm
        eb_depth = float(inputs.get('eb_depth', 0)) * 100 # cm
        
    except Exception as e:
        return pd.DataFrame(), 0.0, [f"Input Error: {str(e)}"], details

    # ==========================================
    # --- 2. SAFETY & LIMITATION CHECKS (ACI 318) ---
    # ==========================================
    
    # Check 2.1: DDM Limitation (L2/L1 ratio)
    ratio_l = l2 / l1 if l1 > 0 else 0
    if ratio_l > 2.0 or ratio_l < 0.5:
        messages.append(f"⚠️ ข้อจำกัด DDM: สัดส่วน L2/L1 = {ratio_l:.2f} (เกินข้อกำหนด 2.0)")

    # Check 2.2: Minimum Thickness
    fy_mpa = fy * 0.0980665 
    fy_mult = 0.8 + (fy_mpa / 1400)
    
    if case_type == "Interior":
        alpha_val = 33 if not has_drop else 36
    else: 
        alpha_val = 33 if has_edge_beam and not has_drop else 36 if has_edge_beam and has_drop else 30 if not has_drop else 33
            
    h_min_cm = (ln_actual * 100 * fy_mult) / alpha_val
    if h_slab < h_min_cm:
        messages.append(f"⚠️ การแอ่นตัว: ความหนาพื้น {h_slab:.0f} cm น้อยกว่าค่า ACI แนะนำ ({h_min_cm:.1f} cm)")
    details['h_min_step'] = rf"h_{{min}} = \frac{{L_n (0.8 + \frac{{f_y}}{{1400}})}}{{\alpha}} = {h_min_cm:.1f} \text{{ cm}}"

    # ==========================================
    # Check 2.3: PUNCHING SHEAR (Rigorous Check)
    # ==========================================
    c1_cm, c2_cm = c1 * 100, c2 * 100
    beta_c = max(c1_cm, c2_cm) / min(c1_cm, c2_cm)
    
    is_interior = (case_type == "Interior")
    alpha_s = 40 if is_interior else 30  # Assume Edge for Exterior
    
    # Helper function: Calculate vc per ACI 318 (metric equivalent kg/cm2)
    def calc_vc_aci(f_c, bo_val, d_val, alpha_s_val, beta_c_val):
        sq_fc = np.sqrt(f_c)
        v1 = 1.06 * sq_fc
        v2 = 0.53 * (1 + (2 / beta_c_val)) * sq_fc
        v3 = 0.265 * ((alpha_s_val * d_val / bo_val) + 2) * sq_fc
        return min(v1, v2, v3)

    punch_msgs = []
    punch_steps = ""
    punch_pass = True

    # --- Section 1: At distance d/2 from Column Face ---
    d1 = (h_drop if has_drop else h_slab) - 3.0 # cm
    
    if is_interior:
        bo1 = 2 * (c1_cm + d1) + 2 * (c2_cm + d1)
        area_out_1 = (l1 * l2) - ((c1_cm + d1)/100 * (c2_cm + d1)/100)
    else: # Edge (assuming c1 is perpendicular to edge)
        bo1 = 2 * (c1_cm + d1/2) + (c2_cm + d1)
        area_out_1 = (l1 * l2 / 2) - ((c1_cm + d1/2)/100 * (c2_cm + d1)/100)
        
    Vu1 = wu * area_out_1 # Direct Shear force
    vc1 = calc_vc_aci(fc, bo1, d1, alpha_s, beta_c)
    phi_Vc1 = 0.75 * vc1 * bo1 * d1
    
    # 🚨 แก้ไข Typo เปลี่ยน {d_1:.0f} เป็น {d1:.0f} ตรงนี้ครับ
    punch_steps += rf"\textbf{{1. รอบหัวเสา ($d_1={d1:.0f}$ cm, $b_{{o1}}={bo1:.0f}$ cm):}} \\ \phi V_{{c1}} = {phi_Vc1:,.0f} \text{{ kg}}, V_{{u1}} = {Vu1:,.0f} \text{{ kg}}\\"
    
    if Vu1 > phi_Vc1:
        punch_msgs.append(f"🚨 ทะลุรอบหัวเสา: Vu ({Vu1:,.0f} kg) > φVc ({phi_Vc1:,.0f} kg)")
        punch_pass = False

    # --- Section 2: At distance d/2 from Drop Panel Face (If present) ---
    if has_drop:
        d2 = h_slab - 3.0
        # ACI minimum drop panel dimensions (L/3)
        w_drop1_cm, w_drop2_cm = (l1 / 3) * 100, (l2 / 3) * 100 
        
        if is_interior:
            bo2 = 2 * (w_drop1_cm + d2) + 2 * (w_drop2_cm + d2)
            area_out_2 = (l1 * l2) - ((w_drop1_cm + d2)/100 * (w_drop2_cm + d2)/100)
        else:
            bo2 = 2 * (w_drop1_cm + d2/2) + (w_drop2_cm + d2)
            area_out_2 = (l1 * l2 / 2) - ((w_drop1_cm + d2/2)/100 * (w_drop2_cm + d2)/100)
            
        Vu2 = wu * max(area_out_2, 0)
        vc2 = calc_vc_aci(fc, bo2, d2, alpha_s, 1.0) # beta_c ≈ 1.0 for drop panel proportion
        phi_Vc2 = 0.75 * vc2 * bo2 * d2
        
        punch_steps += rf"\textbf{{2. รอบ Drop Panel ($d_2={d2:.0f}$ cm, $b_{{o2}}={bo2:.0f}$ cm):}} \\ \phi V_{{c2}} = {phi_Vc2:,.0f} \text{{ kg}}, V_{{u2}} = {Vu2:,.0f} \text{{ kg}}"
        
        if Vu2 > phi_Vc2:
            punch_msgs.append(f"🚨 ทะลุรอบ Drop Panel: Vu ({Vu2:,.0f} kg) > φVc ({phi_Vc2:,.0f} kg)")
            punch_pass = False

    details['punch_step'] = punch_steps
    
    if punch_pass:
        details['punch_status'] = "✅ ผ่านเกณฑ์ (ปลอดภัยจากแรงเฉือนทะลุดิ่ง)"
    else:
        details['punch_status'] = "❌ ไม่ผ่านเกณฑ์ (หน้าตัดรับแรงเฉือนไม่พอ)"
        messages.extend(punch_msgs)

    # ==========================================
    # --- 3. DDM MOMENT CALCULATION ---
    # ==========================================
    ln = max(ln_actual, 0.65 * l1)
    if ln > ln_actual:
        messages.append(f"ℹ️ Clear span Ln ถูกปรับค่าเป็น 0.65*L1 ({ln:.2f} m)")

    Mo = (wu * l2 * (ln**2)) / 8.0 
    details['Mo_step'] = rf"M_o = \frac{{w_u L_2 L_n^2}}{{8}} = \frac{{{wu:,.0f} \times {l2:.2f} \times {ln:.2f}^2}}{{8}} = {Mo:,.0f} \text{{ kg-m}}"

    coeffs = get_moment_coefficients(case_type, has_edge_beam)
    m_neg_int_total = coeffs['neg_int'] * Mo
    m_pos_total     = coeffs['pos'] * Mo
    m_neg_ext_total = coeffs['neg_ext'] * Mo
    
    beta_t = 0.0
    if has_edge_beam and eb_width > 0 and eb_depth > 0:
        x, y = min(eb_width, eb_depth), max(eb_width, eb_depth)
        C = (1 - 0.63 * (x / y)) * (x**3) * y / 3.0
        Is = (l2 * 100) * (h_slab**3) / 12.0
        beta_t = C / (2 * Is)
        details['beta_t_step'] = rf"\beta_t = \frac{{C}}{{2 I_s}} = {beta_t:.3f}"
    else:
        details['beta_t_step'] = r"\text{No Edge Beam (ไม่มีคานขอบ), } \beta_t = 0"

    l2_l1 = min(max(l2 / l1, 0.5), 2.0) 
    cs_pos_pct = 0.60
    cs_int_neg_pct = 0.75
    
    if beta_t == 0:
        cs_ext_neg_pct = 1.00 
    else:
        p_25 = 75 if l2_l1 <= 1.0 else 75 + 15 * (l2_l1 - 1.0)
        cs_ext_neg_pct = (100 - (100 - p_25) * min(beta_t, 2.5) / 2.5) / 100.0

    details['cs_ext_pct'] = cs_ext_neg_pct * 100

    cs_neg_int = cs_int_neg_pct * m_neg_int_total
    ms_neg_int = (1.0 - cs_int_neg_pct) * m_neg_int_total
    cs_pos = cs_pos_pct * m_pos_total
    ms_pos = (1.0 - cs_pos_pct) * m_pos_total
    cs_neg_ext = cs_ext_neg_pct * m_neg_ext_total
    ms_neg_ext = (1.0 - cs_ext_neg_pct) * m_neg_ext_total
        
    def solve_rebar(moment_kgm, b_cm, h_cm, loc_name):
        if moment_kgm <= 0.1: return None 
        
        cover = 3.0 
        d_cm = h_cm - cover
        mu_kgcm = moment_kgm * 100
        phi = 0.9
        
        if d_cm <= 0: return {"Status": "Error (d<=0)"}

        try:
            Rn = mu_kgcm / (phi * b_cm * (d_cm**2))
            limit_rn = 0.35 * fc 
            if Rn > limit_rn:
                return {
                    "Location": loc_name, "Moment (kg-m)": round(moment_kgm, 2), "As Req (cm²)": 0,
                    "Rebar Suggestion": "❌ Section Too Thin", "Status": "Fail", "d (cm)": f"{d_cm:.0f}"
                }

            term = 1 - (2 * Rn) / (0.85 * fc)
            if term < 0: raise ValueError("Complex Root")
            rho = (0.85 * fc / fy) * (1 - np.sqrt(term))
        except:
             return {
                "Location": loc_name, "Moment (kg-m)": round(moment_kgm, 2), "As Req (cm²)": 0,
                "Rebar Suggestion": "❌ Concrete Fail", "Status": "Fail", "d (cm)": f"{d_cm:.0f}"
            }
            
        rho_min = 0.0020 if fy < 4000 else 0.0018
        rho_used = max(rho, rho_min)
        
        as_calc = rho * b_cm * d_cm
        as_temp = rho_min * b_cm * h_cm 
        as_final = max(as_calc, as_temp)
        
        n_bars = max(2, int(np.ceil(as_final / 1.13)))
        spacing = min(b_cm / n_bars, min(2 * h_cm, 45))
        n_bars = int(np.ceil(b_cm / spacing))
        
        status = "Min Steel" if as_calc < as_temp else "OK"
        
        return {
            "Location": loc_name, "Moment (kg-m)": round(moment_kgm, 2), "As Req (cm²)": round(as_final, 2),
            "Rebar Suggestion": f"{n_bars}-DB12 @ {int(spacing)} cm", "Status": status, "d (cm)": f"{d_cm:.0f}"
        }

    width_cs_m = 0.5 * min(l1, l2)
    width_ms_m = l2 - width_cs_m
    b_cs, b_ms = width_cs_m * 100, width_ms_m * 100 
    h_cs_neg = h_drop if has_drop else h_slab
    
    if case_type == "Interior":
        sections = [
            ("Col Strip (Int Neg)", cs_neg_int, b_cs, h_cs_neg), ("Col Strip (Pos)", cs_pos, b_cs, h_slab),
            ("Mid Strip (Int Neg)", ms_neg_int, b_ms, h_slab), ("Mid Strip (Pos)", ms_pos, b_ms, h_slab)
        ]
    else: 
        sections = [
            ("Ext: Col Strip (Int Neg)", cs_neg_int, b_cs, h_cs_neg), ("Ext: Col Strip (Pos)", cs_pos, b_cs, h_slab),
            ("Ext: Col Strip (Ext Neg)", cs_neg_ext, b_cs, h_cs_neg),
            ("Ext: Mid Strip (Int Neg)", ms_neg_int, b_ms, h_slab), ("Ext: Mid Strip (Pos)", ms_pos, b_ms, h_slab),
            ("Ext: Mid Strip (Ext Neg)", ms_neg_ext, b_ms, h_slab) 
        ]

    for name, mom, width, thk in sections:
        res = solve_rebar(mom, width, thk, name)
        if res:
            results.append(res)
            if "Fail" in res.get("Status", ""):
                messages.append(f"⚠️ {name}: ความหนาไม่พอรับโมเมนต์ดัด")

    return pd.DataFrame(results), Mo, messages, details
