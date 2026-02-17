# calc_efm.py
import math

def calculate_efm(calc_obj):
    """
    ฟังก์ชันหลักคำนวณ EFM (Stiffness Analysis)
    """
    col = calc_obj['col_size']
    geom = calc_obj['geom']
    bc = calc_obj['bc']
    mat = calc_obj['mat']
    
    c1 = col['c1'] / 100.0
    c2 = col['c2'] / 100.0
    L1 = geom['L1']
    L2 = geom['L2']
    h_s = geom['h_slab']
    
    # 1. Properties วัสดุ
    fc = mat['fc']
    # Ec = 15100 sqrt(fc) ksc -> แปลงเป็น kPa
    Ec_ksc = 15100 * (fc**0.5)
    Ec_kPa = Ec_ksc * 98.1
    
    # 2. Column Stiffness (Kc)
    Ic = (c2 * (c1**3)) / 12 # Moment of Inertia ของเสา
    h_up = bc['h_up']
    h_lo = bc['h_lo']
    
    # check far end fixity (k=4 fixed, k=3 pinned)
    k_up = 4.0 if "Fixed" in bc['far_end_up'] else 3.0
    k_lo = 4.0 if "Fixed" in bc['far_end_lo'] else 3.0
    
    Kc_up = (k_up * Ec_kPa * Ic) / h_up if h_up > 0 else 0
    Kc_lo = (k_lo * Ec_kPa * Ic) / h_lo
    Kc_total = Kc_up + Kc_lo
    
    # 3. Torsional Stiffness (Kt)
    # Torsion constant C
    x = h_s
    y = c1
    C_val = (1 - 0.63*(x/y)) * (x**3) * y / 3
    
    term_geom = L2 * ((1 - (c2/L2))**3)
    if term_geom == 0: term_geom = 0.001 # กัน error หารศูนย์
    Kt_one_arm = (9 * Ec_kPa * C_val) / term_geom
    Kt_total = Kt_one_arm * 2 # สมมติมีแขนซ้ายขวา (Interior)
    
    # 4. Equivalent Stiffness (Kec)
    # 1/Kec = 1/SKc + 1/Kt
    if Kt_total > 0 and Kc_total > 0:
        inv_Kec = (1/Kc_total) + (1/Kt_total)
        Kec = 1 / inv_Kec
    else:
        Kec = 0
        
    # 5. Distribution Factors (DF)
    Is = (L2 * (h_s**3)) / 12
    Ks = (4 * Ec_kPa * Is) / L1
    
    Sum_K = Ks + Kec
    df_slab = Ks / Sum_K if Sum_K > 0 else 0
    df_col = Kec / Sum_K if Sum_K > 0 else 0
    
    return {
        'Ic': Ic,
        'Ec_kPa': Ec_kPa,
        'Kc_up': Kc_up,
        'Kc_lo': Kc_lo,
        'Kc_total': Kc_total,
        'C_val': C_val,
        'Kt_total': Kt_total,
        'Kec': Kec,
        'Ks': Ks,
        'df_slab': df_slab,
        'df_col': df_col
    }
