import math

# --- Helper Function: Linear Interpolation ---
def linear_interp(x, x1, y1, x2, y2):
    """ช่วยเทียบบัญญัติไตรยางศ์ (ถ้า x อยู่นอกช่วง จะใช้ค่าขอบ)"""
    if x <= x1: return y1
    if x >= x2: return y2
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

# --- ACI 318 Table Lookup Logic ---
def get_longitudinal_coeffs(span_type, edge_beam_exists, is_restrained=False):
    """
    คืนค่าสัมประสิทธิ์การกระจายโมเมนต์ตามยาว (ACI 318 Table 8.10.4.2)
    Returns: (neg_ext, pos, neg_int, description)
    """
    if span_type == 'interior':
        return 0.65, 0.35, 0.65, "Interior Span"
    
    # กรณี End Span (ช่วงริม)
    if is_restrained:
        return 0.65, 0.35, 0.65, "End Span (Fully Restrained)"
    elif edge_beam_exists:
        return 0.30, 0.50, 0.70, "End Span (With Edge Beam)"
    else:
        return 0.26, 0.52, 0.70, "End Span (Flat Plate / No Beam)"

def get_col_strip_percent(location, l2_l1, alpha_f1=0, beta_t=0):
    """
    คำนวณ % โมเมนต์ลงแถบเสา (Column Strip) ตาม ACI 318 Section 8.10.5
    """
    # 1. Interior Negative (Table 8.10.5.1)
    if location == 'neg_int':
        pct_alpha0 = 75.0
        pct_alpha1 = linear_interp(l2_l1, 0.5, 90.0, 2.0, 45.0)
        return linear_interp(alpha_f1, 0, pct_alpha0, 1.0, pct_alpha1) / 100.0

    # 2. Exterior Negative (Table 8.10.5.2)
    elif location == 'neg_ext':
        pct_beta0 = 100.0
        val_alpha0 = 75.0
        val_alpha1 = linear_interp(l2_l1, 0.5, 90.0, 2.0, 45.0)
        pct_beta25 = linear_interp(alpha_f1, 0, val_alpha0, 1.0, val_alpha1)
        return linear_interp(beta_t, 0.0, pct_beta0, 2.5, pct_beta25) / 100.0

    # 3. Positive Moment (Table 8.10.5.5)
    elif location == 'pos':
        pct_alpha0 = 60.0
        pct_alpha1 = linear_interp(l2_l1, 0.5, 90.0, 2.0, 45.0)
        return linear_interp(alpha_f1, 0, pct_alpha0, 1.0, pct_alpha1) / 100.0
    
    return 0.75

# --- New Helper: Solve for As ---
def solve_As(Mu_kNm, d_m, fy_MPa, fc_MPa, b_m, phi=0.9):
    """
    คำนวณปริมาณเหล็กเสริมที่ต้องการ (As required) จาก Mu
    Mu: kNm, d: m, fy: MPa, fc: MPa, b: m
    Return: As (cm2)
    """
    if Mu_kNm <= 0: return 0.0
    
    # Convert units to N, mm
    Mu = Mu_kNm * 1e6
    d = d_m * 1000
    b = b_m * 1000
    
    # Quadratic Equation for As: As^2(m) - As(d) + (Mu / (phi * fy)) = 0
    # derived from Mu = phi * As * fy * (d - a/2) where a = As*fy / (0.85*fc*b)
    
    alpha = (phi * fy**2) / (1.7 * fc_MPa * b)
    beta = - (phi * fy * d)
    gamma = Mu
    
    # Solve quadratic: (-beta - sqrt(beta^2 - 4*alpha*gamma)) / (2*alpha)
    discriminant = beta**2 - 4 * alpha * gamma
    
    if discriminant < 0:
        return 9999.0 # Section too small / Failure
        
    As_req_mm2 = (-beta - math.sqrt(discriminant)) / (2 * alpha)
    return As_req_mm2 / 100.0 # convert to cm2

# --- MAIN CALCULATION FUNCTION ---
def calculate_ddm(calc_obj):
    """
    ฟังก์ชันหลักคำนวณ DDM (Updated for Senior Engineer Tasks)
    """
    # ----------------------------------------------------
    # 1. EXTRACT INPUTS & SETUP
    # ----------------------------------------------------
    geom = calc_obj.get('geom', {})
    loads = calc_obj.get('loads', {})
    col = calc_obj.get('col_size', {'c1': 50, 'c2': 50})
    edge_beam = calc_obj.get('edge_beam', {'has_beam': False})
    mat = calc_obj.get('mat', {'fc': 240, 'fy': 4000}) # ksc default
    
    # Material Conversion (ksc -> MPa)
    fc_MPa = mat['fc'] * 0.0980665
    fy_MPa = mat['fy'] * 0.0980665
    
    # Geometry (m)
    l1_left = geom.get('L1_l', 6.0)
    l1_right = geom.get('L1_r', 6.0)
    L2 = geom.get('L2', 6.0)
    h_slab = geom.get('h_slab', 0.20)
    c1 = col['c1'] / 100.0
    c2 = col['c2'] / 100.0
    
    # Span Type Logic
    if l1_left < 0.1 or l1_right < 0.1:
        span_type = 'end'
        L1 = max(l1_left, l1_right)
    else:
        span_type = 'interior'
        L1 = max(l1_left, l1_right) # Use max for conservative design

    # ----------------------------------------------------
    # 2. INPUT VALIDATION & LIMITATIONS (STEP 1)
    # ----------------------------------------------------
    warnings = []
    
    # Rectangular Ratio check
    long_span = max(L1, L2)
    short_span = min(L1, L2)
    if short_span > 0 and (long_span / short_span) > 2.0:
        warnings.append(f"Ratio > 2.0 ({long_span/short_span:.2f}). DDM not applicable.")
        
    # Load inputs
    # Try to get separated loads, fallback to w_total if not present
    dl_val = loads.get('DL', 0)
    ll_val = loads.get('LL', 0)
    w_total_input = loads.get('w_total', 0)
    
    if dl_val == 0 and ll_val == 0 and w_total_input > 0:
        # Case: Simple input mode (only w_total provided)
        # Cannot strictly check LL <= 2DL
        w_u_kn = w_total_input * 9.80665 / 1000.0
    else:
        # Case: Advanced input mode
        # Check LL <= 2DL
        # Assume slab weight if DL input doesn't likely include it? 
        # Usually user inputs superimposed DL. Let's calculate slab self-weight.
        slab_weight = h_slab * 2400 # kg/m2 (approx density)
        total_DL = dl_val + slab_weight
        
        if ll_val > 2 * total_DL:
             warnings.append(f"Live Load ({ll_val}) > 2 * Dead Load ({total_DL}). DDM Violation.")
             
        # Factored Load (Step 3A)
        # 1.2D + 1.6L
        w_u_kg = 1.2 * total_DL + 1.6 * ll_val
        w_u_kn = w_u_kg * 9.80665 / 1000.0

    # ----------------------------------------------------
    # 3. PRELIMINARY SIZING & PROPERTIES (STEP 2)
    # ----------------------------------------------------
    # Minimum Thickness (ACI Table 8.3.1.1)
    # Clear Span
    Ln = max(L1 - c1, 0.65 * L1)
    
    # Table logic (simplified for Fy=420MPa approx)
    # For Fy=420 (SD40), factors are slightly different but Ln/30 or Ln/33 is standard
    # Without Drop Panel: Ext(no edge beam)=Ln/30, Int=Ln/33
    if span_type == 'interior':
        h_min_req = Ln / 33.0
    else:
        # End span
        has_edge = edge_beam.get('has_beam', False)
        h_min_req = Ln / 33.0 if has_edge else Ln / 30.0
        
    status_h = "OK" if h_slab >= h_min_req else "FAIL"
    
    # Effective Depth (d)
    cover = 0.02 # 20mm
    bar_est = 0.012 # 12mm
    d = h_slab - cover - bar_est/2
    
    # Strip Widths
    width_cs = min(L1, L2) * 0.25 * 2 # Total CS width (half each side)
    width_cs = min(width_cs, L2) # Cap at total width
    width_ms = L2 - width_cs

    # ----------------------------------------------------
    # 4. MOMENT CALCULATION (STEP 3 & 4)
    # ----------------------------------------------------
    # Total Static Moment (M0)
    M0_kNm = (w_u_kn * L2 * (Ln**2)) / 8
    
    # Coefficients
    has_edge_beam = edge_beam.get('has_beam', False)
    coef_neg_ext, coef_pos, coef_neg_int, desc = get_longitudinal_coeffs(span_type, has_edge_beam)
    
    # Longitudinal Moments
    moments_long = {
        'neg_ext': M0_kNm * coef_neg_ext,
        'pos': M0_kNm * coef_pos,
        'neg_int': M0_kNm * coef_neg_int
    }
    
    # Transverse Distribution (CS %)
    l2_l1 = L2 / L1
    beta_t = 2.5 if has_edge_beam else 0.0
    alpha_f1 = 0.0 # Flat plate assumption
    
    pct_cs = {
        'neg_ext': get_col_strip_percent('neg_ext', l2_l1, alpha_f1, beta_t),
        'pos': get_col_strip_percent('pos', l2_l1, alpha_f1, beta_t),
        'neg_int': get_col_strip_percent('neg_int', l2_l1, alpha_f1, beta_t)
    }
    
    # Calculate Final Design Moments (Mu) for Strips
    design_moments = {}
    steel_results = {}
    
    phi_flexure = 0.9
    
    # Min Reinforcement (Temp & Shrinkage) ACI: 0.0018 b h
    As_min_CS = 0.0018 * (width_cs * 100) * (h_slab * 100) # cm2
    As_min_MS = 0.0018 * (width_ms * 100) * (h_slab * 100) # cm2

    # Loop through locations to calc As
    for loc in ['neg_ext', 'pos', 'neg_int']:
        M_total = moments_long[loc]
        pct_c = pct_cs[loc]
        
        # Column Strip
        M_cs = M_total * pct_c
        As_cs = solve_As(M_cs, d, fy_MPa, fc_MPa, width_cs, phi_flexure)
        As_cs_final = max(As_cs, As_min_CS)
        
        # Middle Strip
        M_ms = M_total * (1 - pct_c)
        As_ms = solve_As(M_ms, d, fy_MPa, fc_MPa, width_ms, phi_flexure)
        As_ms_final = max(As_ms, As_min_MS)
        
        design_moments[f'{loc}_cs'] = M_cs
        design_moments[f'{loc}_ms'] = M_ms
        
        steel_results[f'{loc}_cs'] = As_cs_final
        steel_results[f'{loc}_ms'] = As_ms_final

    # ----------------------------------------------------
    # 5. SHEAR CHECKS (STEP 5)
    # ----------------------------------------------------
    shear_results = {}
    phi_shear = 0.75
    lambda_conc = 1.0 (normal weight)
    
    # A. One-way Shear (Beam Action)
    # Vu at distance d from face of support
    # Vu = wu * L2 * (L1/2 - c1/2 - d)
    Vu_oneway = w_u_kn * L2 * ((L1/2) - (c1/2) - d)
    if Vu_oneway < 0: Vu_oneway = 0
    
    # Vc = 0.17 * lambda * sqrt(fc) * bw * d (ACI 22.5.5.1) -> fc in MPa, result in MN -> *1000 -> kN
    # bw = L2
    Vc_oneway = 0.17 * 1.0 * math.sqrt(fc_MPa) * L2 * d * 1000
    phi_Vc_oneway = phi_shear * Vc_oneway
    
    shear_results['oneway'] = {
        'Vu': Vu_oneway,
        'phi_Vc': phi_Vc_oneway,
        'status': 'PASS' if phi_Vc_oneway >= Vu_oneway else 'FAIL'
    }
    
    # B. Two-way Shear (Punching)
    # Critical perimeter b0 at d/2
    c1_d = c1 + d
    c2_d = c2 + d
    b0 = 2 * (c1_d + c2_d)
    
    # Vu_punch = wu * (L1*L2 - area_crit)
    # approximates trib area - critical area
    area_crit = c1_d * c2_d
    Vu_punch = w_u_kn * ((L1 * L2) - area_crit)
    
    # Vc Equations (ACI 22.6.5.2)
    beta = max(c1, c2) / min(c1, c2)
    alpha_s = 40 if span_type == 'interior' else 30 # Assume edge if not interior
    
    # Eq (a): 0.33 * sqrt(fc)
    vc1 = 0.33 * math.sqrt(fc_MPa)
    # Eq (b): 0.17 * (1 + 2/beta) * sqrt(fc)
    vc2 = 0.17 * (1 + 2/beta) * math.sqrt(fc_MPa)
    # Eq (c): 0.083 * (2 + alpha_s*d/b0) * sqrt(fc)
    vc3 = 0.083 * (2 + (alpha_s * d)/b0) * math.sqrt(fc_MPa)
    
    vc_min_stress = min(vc1, vc2, vc3) # MPa
    Vc_punch = vc_min_stress * b0 * d * 1000 # kN
    phi_Vc_punch = phi_shear * Vc_punch
    
    shear_results['punching'] = {
        'Vu': Vu_punch,
        'phi_Vc': phi_Vc_punch,
        'ratio': Vu_punch / phi_Vc_punch if phi_Vc_punch > 0 else 999,
        'status': 'PASS' if phi_Vc_punch >= Vu_punch else 'FAIL'
    }
    
    # ----------------------------------------------------
    # 6. RETURN COMPLETE DATA
    # ----------------------------------------------------
    
    # Preserve original keys for backward compatibility
    dist_factors = {
        'neg_ext_cs': pct_cs['neg_ext'],
        'pos_cs': pct_cs['pos'],
        'neg_int_cs': pct_cs['neg_int']
    }
    
    return {
        'status': 'success',
        'warnings': warnings,
        'inputs': {
            'L1': L1, 'L2': L2, 'Ln': Ln, 'w_u_kn': w_u_kn,
            'h_slab': h_slab, 'd': d,
            'h_min_req': h_min_req
        },
        'M0_kNm': M0_kNm,
        'span_desc': desc,
        'long_coeffs': {'neg_ext': coef_neg_ext, 'pos': coef_pos, 'neg_int': coef_neg_int},
        'moments_total': moments_long,
        'cs_percents': dist_factors,
        # NEW KEYS
        'design_moments': design_moments, # Actual M values per strip
        'steel_required': steel_results,  # As values per strip
        'shear_check': shear_results,
        'check_h': {'req': h_min_req, 'actual': h_slab, 'status': status_h}
    }
