# calc_ddm.py
import math

def interpolate(x, x1, y1, x2, y2):
    """Linear Interpolation Helper"""
    if x <= x1: return y1
    if x >= x2: return y2
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

def get_col_strip_percent(l2_l1, alpha_l2_l1, beta_t, location_type):
    """
    Calculate % Moment to Column Strip based on ACI 318 Tables
    (Table 8.10.5.1, 8.10.5.2, 8.10.5.5)
    """
    # ---------------------------------------------------------
    # 1. INTERIOR NEGATIVE MOMENT (ACI Table 8.10.5.1)
    # ---------------------------------------------------------
    if location_type == 'neg_int':
        # l2/l1 ratio:    0.5     1.0     2.0
        # alpha = 0:      75%     75%     75%
        # alpha >= 1.0:   90%     75%     45%
        
        # Base values for alpha = 0
        pct_alpha0 = 75.0
        
        # Base values for alpha >= 1.0
        if l2_l1 <= 0.5: pct_alpha1 = 90.0
        elif l2_l1 >= 2.0: pct_alpha1 = 45.0
        else: pct_alpha1 = interpolate(l2_l1, 0.5, 90, 2.0, 45) # 1.0 -> 75
        
        # Interpolate between alpha 0 and 1
        return interpolate(alpha_l2_l1, 0, pct_alpha0, 1.0, pct_alpha1) / 100.0

    # ---------------------------------------------------------
    # 2. POSITIVE MOMENT (ACI Table 8.10.5.5)
    # ---------------------------------------------------------
    elif location_type == 'pos':
        # l2/l1 ratio:    0.5     1.0     2.0
        # alpha = 0:      60%     60%     60%
        # alpha >= 1.0:   90%     75%     45%
        
        pct_alpha0 = 60.0
        
        if l2_l1 <= 0.5: pct_alpha1 = 90.0
        elif l2_l1 >= 2.0: pct_alpha1 = 45.0
        else: pct_alpha1 = interpolate(l2_l1, 0.5, 90, 2.0, 45) # 1.0 -> 75
        
        return interpolate(alpha_l2_l1, 0, pct_alpha0, 1.0, pct_alpha1) / 100.0

    # ---------------------------------------------------------
    # 3. EXTERIOR NEGATIVE MOMENT (ACI Table 8.10.5.2)
    # ---------------------------------------------------------
    elif location_type == 'neg_ext':
        # This depends on beta_t (Torsional stiffness) and alpha
        # For Flat Plate (alpha=0), looking at beta_t row
        # beta_t = 0:     100%    100%    100%
        # beta_t >= 2.5:  75%     75%     75%
        
        # Case: alpha = 0 (Flat Plate/Slab)
        # Interpolate based on beta_t
        pct_beta0 = 100.0
        pct_beta25 = 75.0
        
        # Current Logic: Assuming alpha=0 for Flat Slab logic mostly
        # Proper ACI interpolation is complex here, but for Flat Slab:
        return interpolate(beta_t, 0.0, 100.0, 2.5, 75.0) / 100.0
        
    return 0.75 # Default fallback

def calculate_ddm(calc_obj):
    """
    Main DDM Calculation - Senior Engineer Level
    """
    # 1. Unpack & Validate
    geom = calc_obj.get('geom', {})
    loads = calc_obj.get('loads', {})
    col = calc_obj.get('col_size', {'c1': 50, 'c2': 50})
    
    # 2. Geometry
    l1_left = geom.get('L1_l', 6.0)
    l1_right = geom.get('L1_r', 6.0)
    L2 = geom.get('L2', 6.0)
    
    # Check Edge Condition
    is_edge_col = (l1_left < 0.1 or l1_right < 0.1)
    L1 = max(l1_left, l1_right)
    
    # Column Dimensions
    c1 = col['c1'] / 100.0
    
    # 3. Clear Span (Ln) - ACI 8.10.3.1
    # Ln must not be less than 0.65L1
    Ln_calc = L1 - c1
    Ln = max(Ln_calc, 0.65 * L1)
    
    # 4. Static Moment (M0) - ACI 8.10.3.2
    w_u = loads.get('w_total', 1000)
    M0_kgm = (w_u * L2 * (Ln**2)) / 8
    M0_kNm = M0_kgm * 9.80665 / 1000
    
    # 5. Determine Coefficients (ACI 8.10.4)
    # Default for Flat Plate (Unrestrained Edge)
    coeffs = {
        'neg_ext': 0.26, 
        'pos': 0.52, 
        'neg_int': 0.70, 
        'desc': "End Span (Flat Plate)"
    }
    
    if not is_edge_col:
        coeffs = {'neg_ext': 0.65, 'pos': 0.35, 'neg_int': 0.65, 'desc': "Interior Span"}
    else:
        # Check for Edge Beam or Restraint
        has_edge_beam = calc_obj.get('edge_beam', {}).get('has_beam', False)
        if has_edge_beam:
             coeffs = {'neg_ext': 0.30, 'pos': 0.50, 'neg_int': 0.70, 'desc': "End Span (Edge Beam)"}
    
    # 6. Calculate Longitudinal Moments
    moments = {
        'neg_ext': M0_kNm * coeffs['neg_ext'],
        'pos': M0_kNm * coeffs['pos'],
        'neg_int': M0_kNm * coeffs['neg_int']
    }
    
    # 7. Calculate Strip Distribution Factors (The Hard Part)
    # Parameters for interpolation
    l2_l1 = L2 / L1
    
    # For Flat Plate, alpha_f1 = 0 (No beams)
    # If you implement beams later, calculate alpha here.
    alpha_l2_l1 = 0 
    
    # Beta_t (Torsional stiffness ratio)
    # If no edge beam, beta_t = 0. If edge beam, typically > 2.5
    has_edge_beam = calc_obj.get('edge_beam', {}).get('has_beam', False)
    beta_t = 2.5 if has_edge_beam else 0.0 
    
    # Calculate % to Column Strip
    pct_neg_ext = get_col_strip_percent(l2_l1, alpha_l2_l1, beta_t, 'neg_ext')
    pct_pos = get_col_strip_percent(l2_l1, alpha_l2_l1, beta_t, 'pos')
    pct_neg_int = get_col_strip_percent(l2_l1, alpha_l2_l1, beta_t, 'neg_int')
    
    # If Interior Span, Exterior Negative isn't really "Exterior", it's just "Negative"
    # But for symmetry in dict, we keep the keys.
    if not is_edge_col:
        pct_neg_ext = pct_neg_int # Symmetric

    dist_factors = {
        'neg_ext_cs': pct_neg_ext,
        'pos_cs': pct_pos,
        'neg_int_cs': pct_neg_int
    }
    
    return {
        'M0_kNm': M0_kNm,
        'Ln': Ln,
        'L1': L1,
        'L2': L2,
        'w_u': w_u,
        'coeffs': coeffs,
        'moments': moments,
        'dist_factors': dist_factors,
        'is_edge_col': is_edge_col,
        'l2_l1': l2_l1,
        'alpha_term': alpha_l2_l1
    }
