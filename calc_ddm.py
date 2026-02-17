# calc_ddm.py
import math

def get_moment_coefficients(is_end_span, has_edge_beam, is_fully_restrained=False):
    """Return ACI 318 Coefficients dictionary"""
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
    Main DDM Calculation Logic
    Returns a dictionary with all results
    """
    geom = calc_obj['geom']
    loads = calc_obj['loads']
    col = calc_obj['col_size']
    
    # 1. Identify Spans
    l1_left = geom.get('L1_l', 6.0)
    l1_right = geom.get('L1_r', 6.0)
    is_edge_col = (l1_left < 0.1 or l1_right < 0.1)
    is_end_span = is_edge_col
    
    L1 = max(l1_left, l1_right)
    L2 = geom['L2']
    c1 = col['c1'] / 100.0
    
    # 2. Clear Span (Ln)
    Ln = L1 - c1
    if Ln < 0.65 * L1: Ln = 0.65 * L1
    
    # 3. Static Moment (M0)
    w_u = loads['w_total'] # kg/m2
    M0_kgm = (w_u * L2 * (Ln**2)) / 8
    M0_kNm = M0_kgm * 9.80665 / 1000
    
    # 4. Coefficients
    has_edge_beam = False
    if 'edge_beam' in calc_obj and calc_obj['edge_beam']['has_beam']:
        has_edge_beam = True
        
    coeffs = get_moment_coefficients(is_end_span, has_edge_beam)
    
    # 5. Distribute M0
    moments = {
        'neg_ext': M0_kNm * coeffs['neg_ext'],
        'pos': M0_kNm * coeffs['pos'],
        'neg_int': M0_kNm * coeffs['neg_int']
    }
    
    # 6. Column Strip vs Middle Strip Factors
    # Simplified ACI logic for distribution
    dist_factors = {
        'neg_ext_cs': 0.80 if has_edge_beam else 1.00, # 100% to CS if no beam
        'pos_cs': 0.60,
        'neg_int_cs': 0.75
    }
    if not is_end_span: dist_factors['neg_ext_cs'] = 0.75
    
    return {
        'M0_kNm': M0_kNm,
        'M0_kgm': M0_kgm,
        'Ln': Ln,
        'L1': L1,
        'L2': L2,
        'w_u': w_u,
        'coeffs': coeffs,
        'moments': moments,
        'dist_factors': dist_factors,
        'is_end_span': is_end_span
    }
