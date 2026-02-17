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
        return {'neg_int': 0.65, 'pos': 0.35, 'neg_ext': 0.65} # Symetric
    
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
    Advanced DDM Calculation Logic
    """
    results = []
    messages = []
    
    # --- 1. Unpack & Validate Inputs ---
    try:
        l1 = float(inputs['l1'])
        l2 = float(inputs['l2'])
        ln = float(inputs['ln'])
        wu = float(inputs['wu'])
        
        # Depths
        h_slab = float(inputs['h_slab'])
        h_drop = float(inputs.get('h_drop', h_slab)) # If no drop, equals slab
        has_drop = inputs.get('has_drop', False)
        
        # Material
        fc = float(inputs['fc'])
        fy = float(inputs['fy'])
        
        # Conditions
        case_type = inputs.get('case_type', 'Interior') # Interior / Exterior
        has_edge_beam = inputs.get('has_edge_beam', False)
        
    except Exception as e:
        return pd.DataFrame(), 0.0, [f"Input Error: {str(e)}"]

    # --- 2. Calculate Total Static Moment (Mo) ---
    # Mo = (Wu * L2 * ln^2) / 8
    Mo = (wu * l2 * (ln**2)) / 8.0 # kg-m

    # --- 3. Get Coefficients ---
    coeffs = get_moment_coefficients(case_type, has_edge_beam)
    
    # Calculate Total Strip Moments
    m_neg_int_total = coeffs['neg_int'] * Mo
    m_pos_total     = coeffs['pos'] * Mo
    m_neg_ext_total = coeffs['neg_ext'] * Mo
    
    # --- 4. Distribute to Column Strip (CS) & Middle Strip (MS) ---
    # Simplified ACI distribution rules
    
    # 4.1 Interior Negative
    # Standard: 75% CS, 25% MS
    cs_neg_int = 0.75 * m_neg_int_total
    ms_neg_int = 0.25 * m_neg_int_total
    
    # 4.2 Positive
    # Standard: 60% CS, 40% MS
    cs_pos = 0.60 * m_pos_total
    ms_pos = 0.40 * m_pos_total
    
    # 4.3 Exterior Negative
    # If Edge Beam exists: CS takes 80-90%, we use 85% approx
    # If No Edge Beam: CS takes 100%
    if has_edge_beam:
        cs_neg_ext = 0.85 * m_neg_ext_total
        ms_neg_ext = 0.15 * m_neg_ext_total
    else:
        cs_neg_ext = 1.00 * m_neg_ext_total
        ms_neg_ext = 0.00 # No stiffness at edge for middle strip
        
    # --- 5. Reinforcement Calculation Function ---
    def solve_rebar(moment_kgm, b_cm, h_cm, loc_name):
        if moment_kgm <= 0.1: return None # Skip zero moments
        
        cover = 3.0 # cm
        d_cm = h_cm - cover
        mu_kgcm = moment_kgm * 100
        phi = 0.9
        
        # Check d
        if d_cm <= 0: return {"Status": "Error (d<=0)"}

        # Rn
        try:
            Rn = mu_kgcm / (phi * b_cm * (d_cm**2)) # ksc
        except:
            return {"Status": "Calc Error"}

        # Check Failure
        # Limit Rn approx 0.3 fc' to avoid imaginary sqrt
        limit_rn = 0.35 * fc 
        if Rn > limit_rn:
            return {
                "Location": loc_name,
                "Moment": moment_kgm,
                "As Req": 0,
                "Rebar": "❌ Section Too Thin",
                "Status": "Fail",
                "Note": f"Moment too high for h={h_cm}cm"
            }

        # Rho
        try:
            term = 1 - (2 * Rn) / (0.85 * fc)
            if term < 0: raise ValueError("Complex Root")
            rho = (0.85 * fc / fy) * (1 - np.sqrt(term))
        except:
             return {
                "Location": loc_name,
                "Moment": moment_kgm,
                "As Req": 0,
                "Rebar": "❌ Concrete Fail",
                "Status": "Fail",
                "Note": "Math Domain Error"
            }
            
        # Min Steel
        rho_min = 0.0018
        rho_used = max(rho, rho_min)
        as_req = rho_used * b_cm * h_cm # Note: Min steel uses Gross Area (Ag = b*h) usually
        # But flexural design uses b*d. ACI says As_min = 0.0018*b*h for slabs.
        # Let's use standard As = rho_calc * b * d, but check against As_min = 0.0018*b*h
        
        as_calc = rho * b_cm * d_cm
        as_temp = 0.0018 * b_cm * h_cm
        as_final = max(as_calc, as_temp)
        
        # Bar Selection (DB12)
        db12_area = 1.13
        n_bars = max(2, int(np.ceil(as_final / db12_area)))
        spacing = b_cm / n_bars
        
        status = "OK"
        if as_calc < as_temp: status = "Min Steel"
        
        return {
            "Location": loc_name,
            "Moment (kg-m)": round(moment_kgm, 2),
            "As Req (cm²)": round(as_final, 2),
            "Rebar Suggestion": f"{n_bars}-DB12 @ {int(spacing)} cm",
            "Status": status,
            "Design Depth (d)": f"{d_cm:.0f} cm" # Info for user
        }

    # --- 6. Execution Loop ---
    # Define Strips Widths
    b_cs = (l2 / 2.0) * 100 # cm (Approx half width)
    b_ms = (l2 / 2.0) * 100 # cm

    # Define Sections to Analyze
    # Key: (Name, Moment, Width, Thickness to use)
    # Note: Column Strip Negative uses h_drop if has_drop is True
    
    h_cs_neg = h_drop if has_drop else h_slab
    
    # Determine Labels based on Case
    if case_type == "Interior":
        sections = [
            ("Col Strip (Neg)", cs_neg_int, b_cs, h_cs_neg),
            ("Col Strip (Pos)", cs_pos, b_cs, h_slab),
            ("Mid Strip (Neg)", ms_neg_int, b_ms, h_slab),
            ("Mid Strip (Pos)", ms_pos, b_ms, h_slab)
        ]
    else: # Exterior
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
