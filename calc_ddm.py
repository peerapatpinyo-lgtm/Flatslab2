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
        # มีคานขอบ
        return 0.30, 0.50, 0.70, "End Span (With Edge Beam)"
    else:
        # พื้นไร้คาน (Flat Plate) ไม่มีคานขอบ
        return 0.26, 0.52, 0.70, "End Span (Flat Plate / No Beam)"

def get_col_strip_percent(location, l2_l1, alpha_f1=0, beta_t=0):
    """
    คำนวณ % โมเมนต์ลงแถบเสา (Column Strip) ตาม ACI 318 Section 8.10.5
    """
    # 1. Interior Negative (Table 8.10.5.1)
    if location == 'neg_int':
        # ถ้า alpha = 0 (Flat Plate) -> 75% ตลอด
        pct_alpha0 = 75.0
        # ถ้า alpha >= 1.0 -> ขึ้นกับ l2/l1
        pct_alpha1 = linear_interp(l2_l1, 0.5, 90.0, 2.0, 45.0)
        
        return linear_interp(alpha_f1, 0, pct_alpha0, 1.0, pct_alpha1) / 100.0

    # 2. Exterior Negative (Table 8.10.5.2)
    elif location == 'neg_ext':
        # ขึ้นกับ beta_t (Torsional Stiffness)
        # beta_t = 0 (ไม่มีคานขอบ) -> 100%
        # beta_t >= 2.5 -> ขึ้นกับ alpha
        
        # กรณี beta_t = 0
        pct_beta0 = 100.0
        
        # กรณี beta_t >= 2.5
        # ถ้า alpha = 0 -> 75%
        # ถ้า alpha >= 1.0 -> ขึ้นกับ l2/l1 (0.5->90%, 2.0->45%)
        val_alpha0 = 75.0
        val_alpha1 = linear_interp(l2_l1, 0.5, 90.0, 2.0, 45.0)
        pct_beta25 = linear_interp(alpha_f1, 0, val_alpha0, 1.0, val_alpha1)
        
        # Interpolate ตามค่า beta_t จริงๆ
        return linear_interp(beta_t, 0.0, pct_beta0, 2.5, pct_beta25) / 100.0

    # 3. Positive Moment (Table 8.10.5.5)
    elif location == 'pos':
        # alpha = 0 -> 60%
        pct_alpha0 = 60.0
        # alpha >= 1.0 -> ขึ้นกับ l2/l1 (0.5->90%, 2.0->45%)
        pct_alpha1 = linear_interp(l2_l1, 0.5, 90.0, 2.0, 45.0)
        
        return linear_interp(alpha_f1, 0, pct_alpha0, 1.0, pct_alpha1) / 100.0
    
    return 0.75 # Default fallback

# --- MAIN CALCULATION FUNCTION ---
def calculate_ddm(calc_obj):
    """
    ฟังก์ชันหลักในการคำนวณ DDM
    รับค่า dict: calc_obj
    คืนค่า dict: ผลลัพธ์ทั้งหมด
    """
    # 1. Extract Inputs (ใช้ .get เพื่อป้องกัน KeyError)
    geom = calc_obj.get('geom', {})
    loads = calc_obj.get('loads', {})
    col = calc_obj.get('col_size', {'c1': 50, 'c2': 50})
    edge_beam = calc_obj.get('edge_beam', {'has_beam': False})
    
    # Geometry Values
    l1_left = geom.get('L1_l', 6.0)
    l1_right = geom.get('L1_r', 6.0)
    L2 = geom.get('L2', 6.0)
    h_slab = geom.get('h_slab', 0.20)
    
    # 2. Identify Span Type
    # ถ้าด้านใดด้านหนึ่งสั้นมาก (<0.1m) ถือว่าเป็น End Span (เสาริม)
    if l1_left < 0.1 or l1_right < 0.1:
        span_type = 'end'
        L1 = max(l1_left, l1_right)
    else:
        span_type = 'interior'
        L1 = max(l1_left, l1_right) # ปกติควรเฉลี่ย แต่ DDM มักใช้ค่ามากสุดหรือค่าของ span นั้นๆ

    # 3. Calculate Clear Span (Ln) - ACI 8.10.3.1
    c1 = col['c1'] / 100.0 # column dimension in direction of span (m)
    ln_calc = L1 - c1
    ln_min = 0.65 * L1
    Ln = max(ln_calc, ln_min)
    
    # 4. Calculate Static Moment (M0) - ACI 8.10.3.2
    w_u_kg = loads.get('w_total', 1000)
    # Convert kg/m^2 to kN/m^2 approx (multiply by g/1000)
    w_u_kn = w_u_kg * 9.80665 / 1000.0 
    
    # M0 = (wu * L2 * Ln^2) / 8
    M0_kNm = (w_u_kn * L2 * (Ln**2)) / 8
    
    # 5. Longitudinal Distribution Factors
    has_edge_beam = edge_beam.get('has_beam', False)
    # สมมติว่าไม่ได้ Restrained หมุนฟรี (ถ้าจะแก้ ให้เพิ่ม input checkbox ที่ UI)
    is_restrained = False 
    
    coef_neg_ext, coef_pos, coef_neg_int, desc = get_longitudinal_coeffs(span_type, has_edge_beam, is_restrained)
    
    moments_long = {
        'neg_ext': M0_kNm * coef_neg_ext,
        'pos': M0_kNm * coef_pos,
        'neg_int': M0_kNm * coef_neg_int
    }
    
    # 6. Transverse Distribution (Column Strip %)
    # Parameters for interpolation
    l2_l1_ratio = L2 / L1
    
    # Alpha (Beam Stiffness Ratio) - For Flat Plate = 0
    # ถ้าอนาคตมีคานภายใน ต้องคำนวณ alpha1 จริงๆ
    alpha_f1 = 0.0 
    
    # Beta_t (Torsional Stiffness) - For Edge Beam
    # ถ้ามีคานขอบ ACI แนะนำค่าประมาณ > 2.5 ถ้าไม่มี = 0
    beta_t = 2.5 if has_edge_beam else 0.0
    
    # Calculate %
    pct_cs_neg_ext = get_col_strip_percent('neg_ext', l2_l1_ratio, alpha_f1, beta_t)
    pct_cs_pos = get_col_strip_percent('pos', l2_l1_ratio, alpha_f1, beta_t)
    pct_cs_neg_int = get_col_strip_percent('neg_int', l2_l1_ratio, alpha_f1, beta_t)
    
    # กรณี Interior Span ค่า Ext Neg จะเท่ากับ Int Neg (สมมาตร)
    if span_type == 'interior':
        pct_cs_neg_ext = pct_cs_neg_int
        moments_long['neg_ext'] = moments_long['neg_int']

    dist_factors = {
        'neg_ext_cs': pct_cs_neg_ext,
        'pos_cs': pct_cs_pos,
        'neg_int_cs': pct_cs_neg_int
    }
    
    # 7. Return complete data package
    return {
        'status': 'success',
        'inputs': {
            'L1': L1, 'L2': L2, 'Ln': Ln, 'w_u_kn': w_u_kn,
            'l2_l1_ratio': l2_l1_ratio, 'alpha_f1': alpha_f1, 'beta_t': beta_t
        },
        'M0_kNm': M0_kNm,
        'span_desc': desc,
        'long_coeffs': {'neg_ext': coef_neg_ext, 'pos': coef_pos, 'neg_int': coef_neg_int},
        'moments_total': moments_long,
        'cs_percents': dist_factors
    }
