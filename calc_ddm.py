# calc_ddm.py
import pandas as pd
import numpy as np
import math

def get_moment_coefficients(case_type, edge_condition="Slab with edge beam"):
    """
    อ้างอิง ACI 318-19 Table 8.10.4.2
    edge_condition options: "Unrestrained", "Slab with edge beam", "Slab without edge beam", "Fully restrained"
    """
    if case_type == "Interior":
        return {'neg_int': 0.65, 'pos': 0.35, 'neg_ext': 0.65} 
    else: # "Exterior" 
        if edge_condition == "Unrestrained": # เช่น วางบนกำแพงอิฐ
            return {'neg_int': 0.75, 'pos': 0.63, 'neg_ext': 0.00}
        elif edge_condition == "Slab with edge beam":
            return {'neg_int': 0.70, 'pos': 0.50, 'neg_ext': 0.30}
        elif edge_condition == "Slab without edge beam":
            return {'neg_int': 0.70, 'pos': 0.52, 'neg_ext': 0.26}
        elif edge_condition == "Fully restrained": # เช่น หล่อเป็นเนื้อเดียวกับกำแพงรับแรงเฉือน
            return {'neg_int': 0.65, 'pos': 0.35, 'neg_ext': 0.65}
        else:
            return {'neg_int': 0.70, 'pos': 0.50, 'neg_ext': 0.30} # Default

def calculate_ddm(inputs):
    results = []
    messages = []
    details = {}
    # ==========================================
    # --- 1. Unpack Inputs ---
    # ==========================================
    try:
        # 🌟 เพิ่มการรับค่าแกนที่ต้องการวิเคราะห์
        analysis_dir = inputs.get('analysis_dir', 'X-Axis')
        is_y_axis = "Y-Axis" in analysis_dir or "L2" in analysis_dir

        # ดึงค่าดิบที่กรอกมาจาก UI
        raw_l1 = float(inputs['l1'])
        raw_l2 = float(inputs['l2'])
        raw_c1 = float(inputs['c1']) # ขนาดเสาขนาน l1 (m)
        raw_c2 = float(inputs['c2']) # ขนาดเสาขนาน l2 (m)

        # 🌟 สลับแกนตามทิศทางวิเคราะห์ (ทิศทางวิเคราะห์ต้องเป็น l1 เสมอ)
        if is_y_axis:
            l1, l2 = raw_l2, raw_l1
            c1, c2 = raw_c2, raw_c1
        else:
            l1, l2 = raw_l1, raw_l2
            c1, c2 = raw_c1, raw_c2

        # คำนวณ Clear span (ln) ใหม่ให้สอดคล้องกับแกนที่ถูกสลับแล้ว
        ln_actual = l1 - c1

        wu = float(inputs['wu'])
        
        h_slab = float(inputs['h_slab']) # cm
    
        h_drop = float(inputs.get('h_drop', h_slab)) # cm
        has_drop = inputs.get('has_drop', False)
        
        fc = float(inputs['fc'])
        fy = float(inputs['fy'])
        
        case_type = inputs.get('case_type', 'Interior')
        has_edge_beam = inputs.get('has_edge_beam', False)
        eb_width = float(inputs.get('eb_width', 0)) * 100 # cm
        eb_depth = float(inputs.get('eb_depth', 0)) * 100 # cm
        
        # รับค่าขนาดเหล็กเสริมจาก UI (หน่วย mm) ค่าเริ่มต้นคือ 12
        rebar_size = float(inputs.get('rebar_size', 12)) 
        
        # แปลง boolean เป็น edge_condition แบบ ACI 
        edge_condition_input = inputs.get('edge_condition', None)
        if edge_condition_input is None:
            edge_condition = "Slab with edge beam" if has_edge_beam else "Slab without edge beam"
        else:
            edge_condition = edge_condition_input
            
    except Exception as e:
        return pd.DataFrame(), 0.0, [f"Input Error: {str(e)}"], details

    # ==========================================
    # --- 2. SAFETY & LIMITATION CHECKS (ACI 318-19) ---
    # ==========================================
    
    # Check 2.1: DDM Limitation (L2/L1 ratio)
    ratio_l = l2 / l1 if l1 > 0 else 0
    if ratio_l > 2.0 or ratio_l < 0.5:
        messages.append(f"⚠️ ข้อจำกัด DDM: สัดส่วน L2/L1 = {ratio_l:.2f} (เกินข้อกำหนด 2.0)")

    # Check 2.2: Minimum Thickness
    fy_mpa = fy * 0.0980665 
    fy_mult = 0.8 + (fy_mpa / 1400)
    
    if case_type == "Interior":
        alpha_val = 36 if has_drop else 33
    else: 
        if has_drop:
            alpha_val = 36 if has_edge_beam else 33
        else:
            alpha_val = 33 if has_edge_beam else 30
            
    h_min_cm = (ln_actual * 100 * fy_mult) / alpha_val
    if h_slab < h_min_cm:
        messages.append(f"⚠️ การแอ่นตัว: ความหนาพื้น {h_slab:.0f} cm น้อยกว่าค่า ACI แนะนำ ({h_min_cm:.1f} cm)")
    details['h_min_step'] = rf"h_{{min}} = \frac{{L_n (0.8 + \frac{{f_y}}{{1400}})}}{{{alpha_val}}} = {h_min_cm:.1f} \text{{ cm}}"

    # ==========================================
    # --- 3. DDM MOMENT CALCULATION ---
    # ==========================================
    ln = max(ln_actual, 0.65 * l1)
    if ln > ln_actual:
        messages.append(f"ℹ️ Clear span Ln ถูกปรับค่าเป็น 0.65*L1 ({ln:.2f} m)")

    Mo = (wu * l2 * (ln**2)) / 8.0 
    details['Mo_step'] = rf"M_o = \frac{{w_u L_2 L_n^2}}{{8}} = \frac{{{wu:,.0f} \times {l2:.2f} \times {ln:.2f}^2}}{{8}} = {Mo:,.0f} \text{{ kg-m}}"

    coeffs = get_moment_coefficients(case_type, edge_condition)
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
    
    # 🚨 แก้บั๊ก: ปรับสูตร Interpolation สำหรับ Column Strip (Exterior Negative) ให้ถูกต้องตาม ACI
    if beta_t == 0:
        cs_ext_neg_pct = 1.00 
    else:
        if l2_l1 <= 1.0:
            p_25 = 100.0
        else:
            p_25 = 100.0 - 25.0 * (l2_l1 - 1.0)
        cs_ext_neg_pct = (100.0 - (100.0 - p_25) * (min(beta_t, 2.5) / 2.5)) / 100.0

    details['cs_ext_pct'] = cs_ext_neg_pct * 100

    cs_neg_int = cs_int_neg_pct * m_neg_int_total
    ms_neg_int = (1.0 - cs_int_neg_pct) * m_neg_int_total
    cs_pos = cs_pos_pct * m_pos_total
    ms_pos = (1.0 - cs_pos_pct) * m_pos_total
    cs_neg_ext = cs_ext_neg_pct * m_neg_ext_total
    ms_neg_ext = (1.0 - cs_ext_neg_pct) * m_neg_ext_total

    # ==========================================
    # --- 4. PUNCHING SHEAR WITH UNBALANCED MOMENT ---
    # ==========================================

    # รับค่าตำแหน่งเสา (ถ้าไม่ส่งมาให้ประเมินจาก case_type)
    col_location = inputs.get('col_location', 'Interior' if case_type == 'Interior' else 'Edge')
    
    c1_cm, c2_cm = c1 * 100, c2 * 100
    beta_c = max(c1_cm, c2_cm) / min(c1_cm, c2_cm)
    
    # ค่า alpha_s ตาม ACI 318
    if col_location == "Interior": alpha_s = 40
    elif col_location == "Edge": alpha_s = 30
    elif col_location == "Corner": alpha_s = 20
    else: alpha_s = 40

    def calc_vc_aci(f_c, bo_val, d_val, alpha_s_val, beta_c_val):
        sq_fc = np.sqrt(f_c)
        
        # Size Effect Factor (lambda_s) ตาม ACI 318-19
        d_mm = d_val * 10
        lambda_s = min(np.sqrt(2 / (1 + d_mm / 254)), 1.0) 
        
        v1 = 1.06 * lambda_s * sq_fc
        v2 = 0.53 * (1 + (2 / beta_c_val)) * lambda_s * sq_fc
        v3 = 0.265 * ((alpha_s_val * d_val / bo_val) + 2) * lambda_s * sq_fc
        return min(v1, v2, v3)

    punch_msgs = []
    punch_steps = ""
    punch_pass = True

    # ดึงค่าโมเมนต์ถ่ายเท (ถ้าตัวแปร m_neg_ext_total ไม่ได้ถูกคำนวณไว้ก่อนหน้า ให้ดึงจาก inputs หรือตั้งเป็น 0)
    m_unbal_kgm = locals().get('m_neg_ext_total', inputs.get('m_neg_ext_total', 0))
    M_unbal_kgcm = m_unbal_kgm * 100

    # --- Section 1: At distance d/2 from Column Face ---
    d1 = (h_drop if has_drop else h_slab) - 3.0 # cm
    
    if col_location == "Interior":
        # หัวเสาใน (ทะลุ 4 ด้าน)
        b1 = c1_cm + d1
        b2 = c2_cm + d1
        bo1 = 2 * b1 + 2 * b2
        Ac = bo1 * d1
        
        area_out_1 = (l1 * l2) - ((b1/100) * (b2/100))
        Vu1 = wu * area_out_1
        
        vu_applied = Vu1 / Ac
        punch_steps += rf"\textbf{{1. รอบหัวเสาใน ($A_c={Ac:.0f} \text{{ cm}}^2$):}} \\ v_u = {vu_applied:.2f} \text{{ ksc}} \\"
        
    elif col_location == "Edge":
        # หัวเสาขอบ (ทะลุ 3 ด้าน, ตั้งฉากขอบคือ c1)
        b1 = c1_cm + d1/2  # ระยะตั้งฉากขอบ
        b2 = c2_cm + d1    # ระยะขนานขอบ
        bo1 = 2 * b1 + b2
        Ac = bo1 * d1
        
        # หาเซนทรอยด์ c_AB และ Jc
        c_AB = (b1**2 * d1) / Ac
        Jc = (d1 * b1**3)/6 + (b1 * d1**3)/6 + 2*(d1*b1)*((b1/2) - c_AB)**2 + (d1*b2)*c_AB**2
        
        gamma_f = 1 / (1 + (2/3) * np.sqrt(b1/b2))
        gamma_v = 1 - gamma_f
        
        area_out_1 = (l1 * l2 / 2) - ((b1/100) * (b2/100))
        Vu1 = wu * area_out_1
        
        vu_shear = Vu1 / Ac
        vu_moment = (gamma_v * M_unbal_kgcm * c_AB) / Jc if Jc > 0 else 0
        vu_applied = vu_shear + vu_moment
        
        punch_steps += rf"\textbf{{1. รอบหัวเสาขอบ ($b_o={bo1:.0f}$ cm):}} \\"
        punch_steps += rf"V_u = {Vu1:,.0f} \text{{ kg}}, M_{{unbal}} = {m_unbal_kgm:,.0f} \text{{ kg-m}} \\"
        punch_steps += rf"J_c = {Jc:,.0f} \text{{ cm}}^4, \gamma_v = {gamma_v:.2f} \\"
        punch_steps += rf"v_u = {vu_shear:.2f} + {vu_moment:.2f} = {vu_applied:.2f} \text{{ ksc}} \\"

    elif col_location == "Corner":
        # หัวเสามุม (ทะลุ 2 ด้าน)
        b1 = c1_cm + d1/2  
        b2 = c2_cm + d1/2  
        bo1 = b1 + b2
        Ac = bo1 * d1
        
        # หาเซนทรอยด์ c_AB และ Jc สำหรับมุม
        c_AB = (b1**2 * d1) / (2 * Ac)
        Jc = (d1 * b1**3)/12 + (b1 * d1**3)/12 + (d1*b1)*((b1/2) - c_AB)**2 + (d1*b2)*c_AB**2
        
        gamma_f = 1 / (1 + (2/3) * np.sqrt(b1/b2))
        gamma_v = 1 - gamma_f
        
        area_out_1 = (l1 * l2 / 4) - ((b1/100) * (b2/100))
        Vu1 = wu * area_out_1
        
        vu_shear = Vu1 / Ac
        vu_moment = (gamma_v * M_unbal_kgcm * c_AB) / Jc if Jc > 0 else 0
        vu_applied = vu_shear + vu_moment
        
        punch_steps += rf"\textbf{{1. รอบหัวเสามุม ($b_o={bo1:.0f}$ cm):}} \\"
        punch_steps += rf"V_u = {Vu1:,.0f} \text{{ kg}}, M_{{unbal}} = {m_unbal_kgm:,.0f} \text{{ kg-m}} \\"
        punch_steps += rf"J_c = {Jc:,.0f} \text{{ cm}}^4, \gamma_v = {gamma_v:.2f} \\"
        punch_steps += rf"v_u = {vu_shear:.2f} + {vu_moment:.2f} = {vu_applied:.2f} \text{{ ksc}} \\"

    # เช็คความต้านทานแรงเฉือนของคอนกรีต (Section 1)
    vc1 = calc_vc_aci(fc, bo1, d1, alpha_s, beta_c)
    phi_vc1_stress = 0.75 * vc1
    punch_steps += rf"\phi v_c = {phi_vc1_stress:.2f} \text{{ ksc}} \\"
    
    if vu_applied > phi_vc1_stress:
        punch_msgs.append(f"🚨 ทะลุรอบหัวเสา: vu ({vu_applied:.2f} ksc) > φvc ({phi_vc1_stress:.2f} ksc)")
        punch_pass = False

    # --- Section 2: At distance d/2 from Drop Panel Face (If present) ---
    if has_drop:
        d2 = h_slab - 3.0
        # 🌟 ดึงค่ากว้างยาวจาก inputs (ถ้าไม่มีให้ตั้งค่า Default เป็น L/3)
        w_drop1_cm = inputs.get('drop_w1', l1/3) * 100
        w_drop2_cm = inputs.get('drop_w2', l2/3) * 100 
        
        if col_location == "Interior":
            bo2 = 2 * (w_drop1_cm + d2) + 2 * (w_drop2_cm + d2)
            area_out_2 = (l1 * l2) - ((w_drop1_cm + d2)/100 * (w_drop2_cm + d2)/100)
        elif col_location == "Edge":
            bo2 = 2 * (w_drop1_cm + d2/2) + (w_drop2_cm + d2)
            area_out_2 = (l1 * l2 / 2) - ((w_drop1_cm + d2/2)/100 * (w_drop2_cm + d2)/100)
        elif col_location == "Corner":
            bo2 = (w_drop1_cm + d2/2) + (w_drop2_cm + d2/2)
            area_out_2 = (l1 * l2 / 4) - ((w_drop1_cm + d2/2)/100 * (w_drop2_cm + d2/2)/100)
            
        Vu2 = wu * max(area_out_2, 0)
        vc2 = calc_vc_aci(fc, bo2, d2, alpha_s, 1.0) # beta_c ≈ 1.0 สำหรับสัดส่วน Drop Panel
        phi_Vc2_force = 0.75 * vc2 * bo2 * d2
        
        punch_steps += rf"\textbf{{2. รอบ Drop Panel ($d_2={d2:.0f}$ cm, $b_{{o2}}={bo2:.0f}$ cm):}} \\"
        punch_steps += rf"\phi V_{{c2}} = {phi_Vc2_force:,.0f} \text{{ kg}}, V_{{u2}} = {Vu2:,.0f} \text{{ kg}}"
        
        if Vu2 > phi_Vc2_force:
            punch_msgs.append(f"🚨 ทะลุรอบ Drop Panel: Vu ({Vu2:,.0f} kg) > φVc ({phi_Vc2_force:,.0f} kg)")
            punch_pass = False

    details['punch_step'] = punch_steps
    
    if punch_pass:
        details['punch_status'] = "✅ ผ่านเกณฑ์ (ปลอดภัยจากแรงเฉือนทะลุดิ่ง + โมเมนต์ถ่ายเท)"
    else:
        details['punch_status'] = "❌ ไม่ผ่านเกณฑ์ (หน้าตัดรับแรงเฉือนไม่พอ)"
        messages.extend(punch_msgs)



    # ==========================================
    # --- 5. REBAR CALCULATION ---
    # ==========================================
    
    def round_down_spacing(s, step=2.5):
        """ฟังก์ชันช่วยปัดเศษระยะเรียงเหล็กให้ลงตัว เช่น 12.5, 15, 17.5"""
        return math.floor(s / step) * step
        
    def solve_rebar(moment_kgm, b_cm, h_cm, loc_name):
        if moment_kgm <= 0.1: return None 
        
        cover = 3.0 
        d_cm = h_cm - cover
        mu_kgcm = moment_kgm * 100
        phi = 0.9
        
        if d_cm <= 0: return {"Status": "Error (d<=0)"}

        try:
            Rn = mu_kgcm / (phi * b_cm * (d_cm**2))
            
            # ปรับปรุง: ใช้ค่า Rn_max ที่รัดกุมขึ้น (ประมาณ 0.25fc สำหรับ tension-controlled)
            limit_rn = 0.25 * fc 
            if Rn > limit_rn:
                return {
                    "Location": loc_name, "Moment (kg-m)": round(moment_kgm, 2), "As Req (cm²)": 0,
                    "Rebar Suggestion": "❌ Section Too Thin (Over-reinforced)", "Status": "Fail", "d (cm)": f"{d_cm:.0f}"
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
        
        rebar_dia_cm = rebar_size / 10.0
        rebar_area = (np.pi * (rebar_dia_cm ** 2)) / 4.0
        
        n_bars = max(2, int(np.ceil(as_final / rebar_area))) 
        
        # 💡 ปรับปรุง: ปัดเศษระยะ Spacing ให้เป็นระยะที่ทำงานได้จริง (ทีละ 2.5 cm)
        raw_spacing = min(b_cm / n_bars, min(2 * h_cm, 45))
        prac_spacing = round_down_spacing(raw_spacing, 2.5)
        
        # คำนวณจำนวนเหล็กใหม่ตามระยะที่ปัดเศษแล้ว
        n_bars_final = int(np.ceil(b_cm / prac_spacing))
        
        status = "Min Steel" if as_calc < as_temp else "OK"
        
        return {
            "Location": loc_name, "Moment (kg-m)": round(moment_kgm, 2), "As Req (cm²)": round(as_final, 2),
            "Rebar Suggestion": f"{n_bars_final}-DB{int(rebar_size)} @ {prac_spacing:g} cm", "Status": status, "d (cm)": f"{d_cm:.0f}"
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
