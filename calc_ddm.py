import pandas as pd
import numpy as np

def calculate_ddm(inputs):
    """
    Core DDM Calculation Logic
    inputs expects dictionary with:
      - l1, l2 (m): Span lengths
      - ln (m): Clear span
      - wu (kg/m2): Factored load
      - h (m): Slab thickness
      - d (m): Effective depth
      - fc (ksc): Concrete strength
      - fy (ksc): Steel yield strength
      - c1, c2 (m): Column dimensions
    """
    
    # 1. Unpack Inputs
    l1 = inputs['l1']
    l2 = inputs['l2']
    ln = inputs['ln']
    wu = inputs['wu']
    h  = inputs['h']
    d  = inputs['d']
    fc = inputs['fc']
    fy = inputs['fy']
    
    # 2. Total Static Moment (Mo)
    # Mo = (Wu * L2 * ln^2) / 8
    # wu is kg/m2, l2 is m, ln is m -> Mo in kg-m
    Mo = (wu * l2 * (ln**2)) / 8.0
    
    # 3. Distribution Factors (Simplified ACI Table)
    # [Column Strip -, Middle Strip -, Column Strip +, Middle Strip +, Exterior -]
    # Assuming Interior Span for simplicity based on app flow, 
    # but logically splitting Total Static Moment
    
    # Interior Span Coefficients (Standard Flat Plate)
    # Negative Moment: 65% Total (75% to CS, 25% to MS)
    # Positive Moment: 35% Total (60% to CS, 40% to MS)
    
    # Moment Values (kg-m)
    m_neg_total = 0.65 * Mo
    m_pos_total = 0.35 * Mo
    
    # Column Strip (CS) & Middle Strip (MS) Distribution
    # Neg: CS=75%, MS=25%
    m_neg_cs = 0.75 * m_neg_total
    m_neg_ms = 0.25 * m_neg_total
    
    # Pos: CS=60%, MS=40%
    m_pos_cs = 0.60 * m_pos_total
    m_pos_ms = 0.40 * m_pos_total
    
    moments = {
        "Mo": Mo,
        "Neg_CS": m_neg_cs, "Neg_MS": m_neg_ms,
        "Pos_CS": m_pos_cs, "Pos_MS": m_pos_ms
    }
    
    # 4. Steel Calculation (As)
    # As = M / (phi * fy * j * d) approx or iterative
    # Using simplified Rho formula: As = rho * b * d
    # Mu is kg-m -> convert to kg-cm for formula: Mu * 100
    
    phi = 0.9
    b_cs = (l2 / 2.0) * 100 # Width of column strip (cm) approx half panel
    b_ms = (l2 / 2.0) * 100 # Width of middle strip (cm)
    
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
        
        # Rn = Mu / (phi * b * d^2)
        Rn = mu_kgcm / (phi * b_cm * (d_cm**2)) # ksc
        
        # Rho calculation (Formula: 0.85fc/fy * (1 - sqrt(1 - 2Rn/(0.85fc))))
        try:
            rho = (0.85 * fc / fy) * (1 - np.sqrt(1 - (2 * Rn) / (0.85 * fc)))
        except:
            rho = 0.0018 # Min temp steel fallback if calc fails
            
        # Check Min Rho (Temp steel)
        rho_min = 0.0018 # Simplified
        rho_used = max(rho, rho_min)
        
        As_req = rho_used * b_cm * d_cm # cm2
        
        # Suggest Rebar (e.g. DB12)
        db12_area = 1.13
        num_db12 = max(2, int(np.ceil(As_req / db12_area)))
        spacing = b_cm / num_db12
        
        results.append({
            "Location": name,
            "Moment (kg-m)": round(mu_kgm, 2),
            "As Req (cm²)": round(As_req, 2),
            "Rebar Suggestion": f"{num_db12}-DB12 @ {int(spacing)} cm"
        })
        
    return pd.DataFrame(results), Mo
