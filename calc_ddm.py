import pandas as pd
import numpy as np

def get_moment_coefficients(case_type, has_edge_beam):
    """
    Selects ACI 318 Moment Coefficients based on panel location.
    """
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
    details = {} # 📌 เพิ่มตัวแปรเก็บรายละเอียดสมการ
    
    # --- 1. Unpack Inputs ---
    try:
        l1 = float(inputs['l1'])
        l2 = float(inputs['l2'])
        ln_actual = float(inputs['ln'])
        wu = float(inputs['wu'])
        
        # ACI 318 Limitation
        ln = max(ln_actual, 0.65 * l1)
        if ln > ln_actual:
            messages.append(f"ℹ️ Clear span Ln adjusted to 0.65*L1 ({ln:.2f} m) for Mo calculation.")
        
        h_slab = float(inputs['h_slab']) # cm
        h_drop = float(inputs.get('h_drop', h_slab)) # cm
        has_drop = inputs.get('has_drop', False)
        
        fc = float(inputs['fc'])
        fy = float(inputs['fy'])
        
        case_type = inputs.get('case_type', 'Interior')
        has_edge_beam = inputs.get('has_edge_beam', False)
        eb_width = float(inputs.get('eb_width', 0)) * 100 # Convert m to cm
        eb_depth = float(inputs.get('eb_depth', 0)) * 100 # Convert m to cm
        
    except Exception as e:
        return pd.DataFrame(), 0.0, [f"Input Error: {str(e)}"], details

    # --- 2. Calculate Total Static Moment (Mo) ---
    Mo = (wu * l2 * (ln**2)) / 8.0 # kg-m
    
    # 📌 เก็บสมการ Mo
    details['Mo_step'] = rf"M_o = \frac{{w_u L_2 L_n^2}}{{8}} = \frac{{{wu:,.0f} \times {l2:.2f} \times {ln:.2f}^2}}{{8}} = {Mo:,.2f} \text{{ kg-m}}"

    # --- 3. Get Moment Distribution Coefficients ---
    coeffs = get_moment_coefficients(case_type, has_edge_beam)
    m_neg_int_total = coeffs['neg_int'] * Mo
    m_pos_total     = coeffs['pos'] * Mo
    m_neg_ext_total = coeffs['neg_ext'] * Mo
    
    # --- 4. ACI 318 Moment Distribution to Strips ---
    # 4.1 Calculate Torsional Stiffness (beta_t) for Exterior Edge
    beta_t = 0.0
    if has_edge_beam and eb_width > 0 and eb_depth > 0:
        x = min(eb_width, eb_depth)
        y = max(eb_width, eb_depth)
        C = (1 - 0.63 * (x / y)) * (x**3) * y / 3.0
        Is = (l2 * 100) * (h_slab**3) / 12.0
        beta_t = C / (2 * Is)
        messages.append(f"🔧 Calculated Torsional Stiffness (βt) = {beta_t:.2f}")
        # 📌 เก็บสมการ beta_t
        details['beta_t_step'] = rf"\beta_t = \frac{{C}}{{2 I_s}} = \frac{{{C:,.0f}}}{{2 \times {Is:,.0f}}} = {beta_t:.3f}"
    else:
        details['beta_t_step'] = r"\text{No Edge Beam (ไม่มีคานขอบ), } \beta_t = 0"

    # 4.2 Interpolate Column Strip Percentages
    l2_l1 = min(max(l2 / l1, 0.5), 2.0) # Limit between 0.5 and 2.0 per ACI
    
    # Positive & Interior Negative (Assuming alpha_f1 = 0 for Flat Plate)
    cs_pos_pct = 0.60
    cs_int_neg_pct = 0.75
    
    # Exterior Negative (Interpolation based on beta_t and l2/l1)
    if beta_t == 0:
        cs_ext_neg_pct = 1.00 # 100% to CS
    else:
        # P25 is the percentage when beta_t >= 2.5
        p_25 = 75 if l2_l1 <= 1.0 else 75 + 15 * (l2_l1 - 1.0)
        # Interpolate between beta_t = 0 (100%) and beta_t = 2.5 (P25%)
        cs_ext_neg_pct = (100 - (100 - p_25) * min(beta_t, 2.5) / 2.5) / 100.0

    # 📌 เก็บค่าเปอร์เซ็นต์
    details['cs_ext_pct'] = cs_ext_neg_pct * 100

    # 4.3 Apply Percentages to Total Moments
    cs_neg_int = cs_int_neg_pct * m_neg_int_total
    ms_neg_int = (1.0 - cs_int_neg_pct) * m_neg_int_total
    
    cs_pos = cs_pos_pct * m_pos_total
    ms_pos = (1.0 - cs_pos_pct) * m_pos_total
    
    cs_neg_ext = cs_ext_neg_pct * m_neg_ext_total
    ms_neg_ext = (1.0 - cs_ext_neg_pct) * m_neg_ext_total
        
    # --- 5. Reinforcement Calculation Function ---
    def solve_rebar(moment_kgm, b_cm, h_cm, loc_name):
        if moment_kgm <= 0.1: return None 
        
        cover = 3.0 # cm
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
        
        db12_area = 1.13
        n_bars = max(2, int(np.ceil(as_final / db12_area)))
        spacing = b_cm / n_bars
        
        max_spacing = min(2 * h_cm, 45)
        if spacing > max_spacing:
            spacing = max_spacing
            n_bars = int(np.ceil(b_cm / spacing))
        
        status = "OK"
        if as_calc < as_temp: status = "Min Steel"
        
        return {
            "Location": loc_name,
            "Moment (kg-m)": round(moment_kgm, 2),
            "As Req (cm²)": round(as_final, 2),
            "Rebar Suggestion": f"{n_bars}-DB12 @ {int(spacing)} cm",
            "Status": status,
            "d (cm)": f"{d_cm:.0f}"
        }

    # --- 6. Execution Loop ---
    width_cs_m = 0.5 * min(l1, l2)
    width_ms_m = l2 - width_cs_m
    
    b_cs = width_cs_m * 100 # cm
    b_ms = width_ms_m * 100 # cm
    h_cs_neg = h_drop if has_drop else h_slab
    
    if case_type == "Interior":
        sections = [
            ("Col Strip (Int Neg)", cs_neg_int, b_cs, h_cs_neg),
            ("Col Strip (Pos)",     cs_pos,     b_cs, h_slab),
            ("Mid Strip (Int Neg)", ms_neg_int, b_ms, h_slab),
            ("Mid Strip (Pos)",     ms_pos,     b_ms, h_slab)
        ]
    else: 
        sections = [
            ("Ext: Col Strip (Int Neg)", cs_neg_int, b_cs, h_cs_neg),
            ("Ext: Col Strip (Pos)",     cs_pos,     b_cs, h_slab),
            ("Ext: Col Strip (Ext Neg)", cs_neg_ext, b_cs, h_cs_neg),
            ("Ext: Mid Strip (Int Neg)", ms_neg_int, b_ms, h_slab),
            ("Ext: Mid Strip (Pos)",     ms_pos,     b_ms, h_slab),
            ("Ext: Mid Strip (Ext Neg)", ms_neg_ext, b_ms, h_slab) 
        ]

    for name, mom, width, thk in sections:
        res = solve_rebar(mom, width, thk, name)
        if res:
            results.append(res)
            if "Fail" in res.get("Status", ""):
                messages.append(f"⚠️ {name}: Section insufficient (Depth too low for applied moment).")

    # 📌 ส่ง details กลับไปด้วยเป็นตัวที่ 4
    return pd.DataFrame(results), Mo, messages, details
