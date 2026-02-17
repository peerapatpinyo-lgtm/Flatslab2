# calc_efm.py
import math

def calculate_efm(calc_obj):
    """
    Equivalent Frame Method - Stiffness Calculation
    Reference: ACI 318 & Wight/MacGregor Reinforced Concrete
    """
    # 1. Init Data
    col = calc_obj.get('col_size', {'c1': 50, 'c2': 50})
    geom = calc_obj.get('geom', {})
    bc = calc_obj.get('bc', {'h_up': 3.0, 'h_lo': 3.0})
    mat = calc_obj.get('mat', {'fc': 240})
    
    # Dimensions (m)
    c1 = col['c1'] / 100.0 # Dimension in direction of analysis
    c2 = col['c2'] / 100.0 # Transverse dimension
    L1 = geom.get('L1_r', 6.0) # Span length
    L2 = geom.get('L2', 6.0)   # Transverse width
    h_s = geom.get('h_slab', 0.20)
    
    # 2. Material Properties
    # E_c = 15100 sqrt(fc) ksc -> convert to kPa for consistency
    Ec_ksc = 15100 * (mat['fc']**0.5)
    Ec_kPa = Ec_ksc * 98.0665 
    
    # 3. Slab Stiffness (Ks)
    # Gross Inertia
    Is_gross = (L2 * (h_s**3)) / 12
    # In rigorous EFM, we increase I inside the column joint. 
    # But ACI allows using gross inertia for standard cases.
    # Ks = 4EI/L (Far end fixed assumption for stiffness factor)
    Ks = (4 * Ec_kPa * Is_gross) / L1
    
    # 4. Column Stiffness (Kc)
    # Inertia of Column
    Ic = (c2 * (c1**3)) / 12 
    
    h_up = bc.get('h_up', 3.0)
    h_lo = bc.get('h_lo', 3.0)
    
    # Factor k for column
    # If far end is fixed, k=4. If pinned, k=3.
    # Usually in multistory, we assume fixed far ends (k=4)
    k_col = 4.0 
    
    Kc_up = (k_col * Ec_kPa * Ic) / h_up if h_up > 0 else 0
    Kc_lo = (k_col * Ec_kPa * Ic) / h_lo if h_lo > 0 else 0
    
    Sum_Kc = Kc_up + Kc_lo
    
    # 5. Torsional Member Stiffness (Kt) - ACI R8.11.5
    # This is the "Effective" stiffness of the slab strip attached to column
    # Formula: Kt = sum( 9 * Ecs * C / (L2 * (1 - c2/L2)^3) )
    
    # Torsion Constant C (for rectangular section x by y)
    # x = shorter side (slab thickness h_s), y = longer side (c1)
    x = h_s
    y = c1
    # Eq for C
    C = (1 - 0.63 * (x/y)) * (x**3) * y / 3
    
    term1 = 9 * Ec_kPa * C
    term2 = L2 * ((1 - (c2/L2))**3)
    if term2 == 0: term2 = 0.001
    
    Kt_one_side = term1 / term2
    
    # Interior column has torsion arm on both sides? 
    # Actually Kt represents the transverse strip. 
    # For interior column, it acts on both sides of the column if we consider the full transverse beam.
    # Standard practice: Kt is for the connection.
    Kt = Kt_one_side * 2 # Assuming symmetric transverse span
    
    # 6. Equivalent Column Stiffness (Kec)
    # 1/Kec = 1/Sum_Kc + 1/Kt
    if Sum_Kc > 0 and Kt > 0:
        Kec = 1 / ((1/Sum_Kc) + (1/Kt))
    else:
        Kec = 0
        
    # 7. Distribution Factors (DF) at the Joint
    # DF_slab = Ks / (Ks + Kec)
    # DF_col = Kec / (Ks + Kec)
    Sum_K_Joint = Ks + Kec
    if Sum_K_Joint > 0:
        df_slab = Ks / Sum_K_Joint
        df_col = Kec / Sum_K_Joint
    else:
        df_slab, df_col = 0, 0
        
    return {
        'Ic': Ic,
        'Is': Is_gross,
        'Ec_kPa': Ec_kPa,
        'Kc_up': Kc_up,
        'Kc_lo': Kc_lo,
        'Sum_Kc': Sum_Kc,
        'C': C,
        'Kt': Kt,
        'Kec': Kec,
        'Ks': Ks,
        'df_slab': df_slab,
        'df_col': df_col
    }
