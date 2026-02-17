# calc_ddm.py
import math

def get_moment_coefficients(is_end_span, has_edge_beam, is_fully_restrained=False):
    """คืนค่าสัมประสิทธิ์ ACI 318"""
    if not is_end_span:
        return {'neg_ext': 0.65, 'pos': 0.35, 'neg_int': 0.65, 'desc': "Interior Span"}
    
    if is_fully_restrained:
        return {'neg_ext': 0.65, 'pos': 0.35, 'neg_int': 0.65, 'desc': "End Span (Restrained)"}
    elif has_edge_beam:
        return {'neg_ext': 0.30, 'pos': 0.50, 'neg_int': 0.70, 'desc': "End Span (Edge Beam)"}
    else:
        return {'neg_ext': 0.26, 'pos': 0.52, 'neg_int': 0.70, 'desc': "End Span (Flat Plate)"}

def calculate_ddm(calc_obj):
    """
    ฟังก์ชันหลักคำนวณ DDM
    """
    geom = calc_obj.get('geom', {})
    loads = calc_obj.get('loads', {})
    col = calc_obj.get('col_size', {'c1': 50, 'c2': 50})
    
    # 1. ระบุ Span และ Geometry
    l1_left = geom.get('L1_l', 6.0)
    l1_right = geom.get('L1_r', 6.0)
    
    # ถ้าด้านใดด้านหนึ่งสั้นมาก (เช่น 0) แสดงว่าเป็นเสาขอบ
    is_edge_col = (l1_left < 0.1 or l1_right < 0.1)
    is_end_span = is_edge_col
    
    L1 = max(l1_left, l1_right)
    L2 = geom.get('L2', 6.0)
    c1 = col['c1'] / 100.0
    
    # 2. Clear Span (Ln)
    Ln = L1 - c1
    if Ln < 0.65 * L1: Ln = 0.65 * L1
    
    # 3. Static Moment (M0)
    w_u = loads.get('w_total', 1000) # Default if missing
    M0_kgm = (w_u * L2 * (Ln**2)) / 8
    M0_kNm = M0_kgm * 9.80665 / 1000
    
    # 4. Coefficients
    has_edge_beam = False
    if 'edge_beam' in calc_obj and calc_obj['edge_beam'].get('has_beam', False):
        has_edge_beam = True
        
    coeffs = get_moment_coefficients(is_end_span, has_edge_beam)
    
    # 5. Distribute M0 (Longitudinal)
    moments = {
        'neg_ext': M0_kNm * coeffs['neg_ext'],
        'pos': M0_kNm * coeffs['pos'],
        'neg_int': M0_kNm * coeffs['neg_int']
    }
    
    # 6. หา % เข้า Column Strip (Transverse)
    # เรากำหนด Key ให้ชัดเจนที่นี่ เพื่อกัน KeyError
    if is_end_span:
        # กรณี End Span
        neg_ext_cs_pct = 0.80 if has_edge_beam else 1.00
    else:
        # กรณี Interior Span
        neg_ext_cs_pct = 0.75

    dist_factors = {
        'neg_ext_cs': neg_ext_cs_pct,
        'pos_cs': 0.60,
        'neg_int_cs': 0.75
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
        'is_end_span': is_end_span
    }
