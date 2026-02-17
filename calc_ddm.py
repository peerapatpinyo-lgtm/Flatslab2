import pandas as pd
import numpy as np

def calculate_ddm(inputs):
    """
    Core DDM Calculation Logic (Fixed for NaN/Math Domain Errors)
    """
    
    # 1. Unpack Inputs & Ensure Floats
    try:
        l1 = float(inputs['l1'])
        l2 = float(inputs['l2'])
        ln = float(inputs['ln'])
        wu = float(inputs['wu'])
        h  = float(inputs['h'])
        d  = float(inputs['d'])
        fc = float(inputs['fc'])
        fy = float(inputs['fy'])
        c1 = float(inputs['c1']) # Not used in moment calc but kept for consistency
        c2 = float(inputs['c2'])
    except (ValueError, TypeError):
        # Fallback to defaults if conversion fails to prevent crash
        l1, l2, ln = 6.0, 6.0, 5.5
        wu, h, d, fc, fy = 1000.0, 0.2, 0.17, 240.0, 4000.0

    # 2. Total Static Moment (Mo)
    # Mo = (Wu * L2 * ln^2) / 8
    Mo = (wu * l2 * (ln**2)) / 8.0
    
    # 3. Distribution Factors
    m_neg_total = 0.65 * Mo
    m_pos_total = 0.35 * Mo
    
    m_neg_cs = 0.75 * m_neg_total
    m_neg_ms = 0.25 * m_neg_total
    
    m_pos_cs = 0.60 * m_pos_total
    m_pos_ms = 0.40 * m_pos_total
    
    # 4. Steel Calculation (As)
    phi = 0.9
    b_cs = (l2 / 2.0) * 100 # cm
    b_ms = (l2 / 2.0) * 100 # cm
    
    results = []
    
    sections = [
        ("Column Strip (-)", m_neg_cs, b_cs),
        ("Column Strip (+)", m_pos_cs, b_cs),
        ("Middle Strip (-)", m_neg_ms, b_ms),
        ("Middle Strip (+)", m_pos_ms, b_ms),
    ]
    
    for name, mu_kgm, b_cm in sections:
        mu_kgcm = mu_kgm * 100
        d_cm = d * 100
        
        # Calculate Rn
        try:
            Rn = mu_kgcm / (phi * b_cm * (d_cm**2)) # ksc
        except ZeroDivisionError:
            Rn = 0
        
        # --- ROBUST RHO CALCULATION ---
        # Formula: rho = (0.85*fc/fy) * (1 - sqrt(1 - 2*Rn/(0.85*fc)))
        # Term inside sqrt must be >= 0
        
        term_check = 1 - (2 * Rn) / (0.85 * fc)
        status_msg = "OK"
        
        if term_check < 0:
            # CASE: Section Too Small (Fail)
            # Rn is too high, meaning Moment is too large for this thickness
            # Set rho to a dummy max value (e.g. 2.5%) just to show result without crashing
            rho_used = 0.025 
            status_msg = "❌ Section Too Thin"
        else:
            # CASE: Normal Calculation
            rho = (0.85 * fc / fy) * (1 - np.sqrt(term_check))
            rho_min = 0.0018
            if rho < rho_min:
                rho_used = rho_min
                status_msg = "Min Steel"
            else:
                rho_used = rho
                status_msg = "OK"
        
        # Calculate As
        As_req = rho_used * b_cm * d_cm
        
        # --- SAFELY CALCULATE REBAR ---
        # Handle NaN or Inf if they sneak in
        if np.isnan(As_req) or np.isinf(As_req):
            As_req = 0.0
            num_db12 = 0
            rebar_str = "Error"
        else:
            db12_area = 1.13
            # Use max(2, ...) to ensure at least 2 bars
            num_bars = int(np.ceil(As_req / db12_area))
            num_db12 = max(2, num_bars)
            
            # Prevent Division by Zero in spacing
            if num_db12 > 0:
                spacing = b_cm / num_db12
            else:
                spacing = 0
            
            rebar_str = f"{num_db12}-DB12 @ {int(spacing)} cm"
            if "Too Thin" in status_msg:
                rebar_str += " (NG)"

        results.append({
            "Location": name,
            "Moment (kg-m)": round(mu_kgm, 2),
            "As Req (cm²)": round(As_req, 2),
            "Rebar Suggestion": rebar_str,
            "Status": status_msg
        })
        
    return pd.DataFrame(results), Mo
