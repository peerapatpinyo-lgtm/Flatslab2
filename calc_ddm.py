import pandas as pd
import numpy as np

def get_moment_coefficients(case_type, has_edge_beam):
    """
    Selects ACI 318 Moment Coefficients based on panel location.
    
    Returns dict: { 'neg_int': %, 'pos': %, 'neg_ext': % }
    
    Ref: ACI 318 Direct Design Method Coefficients
    """
    if case_type == "Interior":
        # Case 1: Interior Panel
        # Neg Total: 0.65 | Pos Total: 0.35
        return {'neg_int': 0.65, 'pos': 0.35, 'neg_ext': 0.65} # Symmetric
    
    else: # "Exterior" (Edge or Corner)
        if has_edge_beam:
            # Case 2: Exterior Panel WITH Edge Beam (Restrained)
            # ACI Table: Neg Int=0.70, Pos=0.50, Neg Ext=0.30
            return {'neg_int': 0.70, 'pos': 0.50, 'neg_ext': 0.30}
        else:
            # Case 3: Exterior Panel WITHOUT Edge Beam (Unrestrained / Flat Plate)
            # ACI Table: Neg Int=0.70, Pos=0.52, Neg Ext=0.26
            return {'neg_int': 0.70, 'pos': 0.52, 'neg_ext': 0.26}

def calculate_ddm(inputs):
    """
    Advanced DDM Calculation Logic (ACI 318 Compliant)
    """
    results = []
    messages = []
    
    # --- 1. Unpack & Validate Inputs ---
    try:
        l1 = float(inputs['l1'])
        l2 = float(inputs['l2'])
        ln_actual = float(inputs['ln'])
        wu = float(inputs['wu'])
        
        # ACI 318 limitation: ln shall not be less than 0.65 * l1
        ln = max(ln_actual, 0.65 * l1)
        if ln > ln_actual:
            messages.append(f"ℹ️ Clear span Ln adjusted to 0.65*L1 ({ln:.2f} m) for Mo calculation.")
        
        # Depths
        h_slab = float(inputs['h_slab'])
        h_drop = float(inputs.get('h_drop', h_slab))
        has_drop = inputs.get('has_drop', False)
        
        # Material
        fc = float(inputs['fc'])
        fy = float(inputs['fy'])
        
        # Conditions
        case_type = inputs.get('case_type', 'Interior')
        has_edge_beam = inputs.get('has_edge_beam', False)
        
    except Exception as e:
        return pd.DataFrame(), 0.0, [f"Input Error: {str(e)}"]

    # --- 2. Calculate Total Static Moment (Mo) ---
    # Mo = (Wu * L2 * ln^2) / 8
    Mo = (wu * l2 * (ln**2)) / 8.0 # kg-m

    # --- 3. Get Coefficients ---
    coeffs = get_moment_coefficients(case_type, has_edge_beam)
    
    m_neg_int_total = coeffs['neg_int'] * Mo
    m_pos_total     = coeffs['pos'] * Mo
    m_neg_ext_total = coeffs['neg_ext'] * Mo
    
    # --- 4. Distribute to Column Strip (CS) & Middle Strip (MS) ---
    cs_neg_int = 0.75 * m_neg_int_total
    ms_neg_int = 0.25 * m_neg_int_total
    
    cs_pos = 0.60 * m_pos_total
    ms_pos = 0.40 * m_pos_total
    
    if has_edge_beam:
        cs_neg_ext = 0.85 * m_neg_ext_total
        ms_neg_ext = 0.15 * m_neg_ext_total
    else:
        cs_neg_ext = 1.00 * m_neg_ext_total
        ms_neg_ext = 0.00 
        
    # --- 5. Reinforcement Calculation Function ---
    def solve_rebar(moment_kgm, b_cm, h_cm, loc_name):
        if moment_kgm <= 0.1: return None 
        
        cover = 3.0 # cm
        d_cm = h_cm - cover
        mu_kgcm = moment_kgm * 100
        phi = 0.9
        
        if d_cm <= 0: return {"Status": "Error (d<=0)"}

        try:
            Rn = mu_kgcm / (phi * b_cm * (d_cm**2)) # ksc
        except:
            return {"Status": "Calc Error"}

        # Check Failure (limit Rn to avoid complex roots)
        limit_rn = 0.35 * fc 
        if Rn > limit_rn:
            return {
                "Location": loc_name,
                "Moment (kg-m)": round(moment_kgm, 2),
                "As Req (cm²)": 0,
                "Rebar Suggestion": "❌ Section Too Thin",
                "Status": "Fail",
                "Design Depth (d)": f"{d_cm:.0f} cm"
            }

        try:
            term = 1 - (2 * Rn) / (0.85 * fc)
            if term < 0: raise ValueError("Complex Root")
            rho = (0.85 * fc / fy) * (1 - np.sqrt(term))
        except:
             return {
                "Location": loc_name,
                "Moment (kg-m)": round(moment_kgm, 2),
                "As Req (cm²)": 0,
                "Rebar Suggestion": "❌ Concrete Fail",
                "Status": "Fail",
                "Design Depth (d)": f"{d_cm:.0f} cm"
            }
            
        # Min Steel based on fy
        rho_min = 0.0020 if fy < 4000 else 0.0018
        rho_used = max(rho, rho_min)
        
        as_calc = rho * b_cm * d_cm
        as_temp = rho_min * b_cm * h_cm # ACI Min Temp Steel
        as_final = max(as_calc, as_temp)
        
        # Bar Selection (DB12)
        db12_area = 1.13
        n_bars = max(2, int(np.ceil(as_final / db12_area)))
        spacing = b_cm / n_bars
        
        # Spacing limit check (max 2h or 45cm)
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
            "Design Depth (d)": f"{d_cm:.0f} cm"
        }

    # --- 6. Execution Loop ---
    
    # ACI Rule: Column strip width is 0.25 * min(l1, l2) on each side
    # So total width b_cs = 0.5 * min(l1, l2)
    width_cs_m = 0.5 * min(l1, l2)
    width_ms_m = l2 - width_cs_m
    
    b_cs = width_cs_m * 100 # cm
    b_ms = width_ms_m * 100 # cm

    h_cs_neg = h_drop if has_drop else h_slab
    
    if case_type == "Interior":
        sections = [
            ("Col Strip (Neg)", cs_neg_int, b_cs, h_cs_neg),
            ("Col Strip (Pos)", cs_pos, b_cs, h_slab),
            ("Mid Strip (Neg)", ms_neg_int, b_ms, h_slab),
            ("Mid Strip (Pos)", ms_pos, b_ms, h_slab)
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
                messages.append(f"⚠️ {name}: Section insufficient.")

    return pd.DataFrame(results), Mo, messages
