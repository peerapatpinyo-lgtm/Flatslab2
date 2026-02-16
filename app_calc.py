# app_calc.py
import numpy as np
from app_config import Units

# ==============================================================================
# ENGINEERING LOGIC & VALIDATOR
# ==============================================================================

class DesignCriteriaValidator:
    """
    Validates design criteria according to ACI 318 for DDM, EFM, and Serviceability.
    """
    def __init__(self, L1, L2, L1_l, L1_r, L2_t, L2_b, ll, dl, has_drop, cant_data, 
                 fy_ksc, col_location, h_slab_cm):
        self.L1 = L1
        self.L2 = L2
        self.Ln_long = max(L1, L2) - 0.50 # Approx Ln based on max span
        self.L1_spans = [l for l in [L1_l, L1_r] if l > 0]
        self.L2_spans = [l for l in [L2_t, L2_b] if l > 0]
        self.ll = ll
        self.dl = dl
        self.has_drop = has_drop
        self.cant = cant_data
        
        # New attributes for checks
        self.fy_mpa = (300 if fy_ksc == "SD30" else (400 if fy_ksc == "SD40" else 500))
        self.col_location = col_location # Interior, Edge, Corner
        self.h_slab_cm = h_slab_cm

    def check_min_thickness(self):
        """
        Calculates Minimum Slab Thickness based on ACI 318 Table 8.3.1.1
        Returns: (passed_boolean, min_h_cm, message)
        """
        # ACI 318 Table 8.3.1.1 Denominators
        # Setup denominators based on Location & Drop Panel
        # Note: Assuming 'Edge/Corner' has no edge beam for worst case (Flat Plate)
        
        is_ext = (self.col_location in ["Edge Column", "Corner Column"])
        
        if self.has_drop:
            # With Drop Panel
            denom = 36.0 if not is_ext else 33.0
        else:
            # Without Drop Panel
            denom = 33.0 if not is_ext else 30.0
            
        # Correction Factor for Fy other than 420 MPa (ACI 318-19)
        # Factor = (0.8 + fy/1400)
        fy_factor = 0.8 + (self.fy_mpa / 1400)
        
        # Calculate Min Thickness (Ln is critical span)
        # We use the longest clear span approximate
        min_h_m = (self.Ln_long * fy_factor) / denom
        min_h_cm = min_h_m * 100
        min_h_cm = max(min_h_cm, 10.0 if self.has_drop else 12.5) # Absolute min limits

        status = self.h_slab_cm >= min_h_cm
        msg = f"Req: {min_h_cm:.2f} cm (ACI Table 8.3.1.1)"
        
        return status, min_h_cm, msg

    def check_drop_panel(self, h_drop_cm, drop_w1, drop_w2):
        """Validates Drop Panel dimensions (Depth & Extension)."""
        warnings = []
        if not self.has_drop:
            return warnings

        # 1. Thickness Check (ACI: >= h_s/4 below slab)
        req_drop_h = self.h_slab_cm / 4
        if h_drop_cm < req_drop_h:
            warnings.append(f"❌ **Depth:** Drop {h_drop_cm}cm < Min {req_drop_h:.2f}cm (h_s/4)")
        else:
            warnings.append(f"✅ **Depth:** {h_drop_cm}cm >= {req_drop_h:.2f}cm")

        # 2. Extension Check (ACI: >= L/6 from center = L/3 total width if symmetric)
        # Note: Checking against total Span L1 and L2
        req_w1 = self.L1 / 3
        req_w2 = self.L2 / 3
        
        if drop_w1 < req_w1:
            warnings.append(f"❌ **Width W1:** {drop_w1:.2f}m < Min {req_w1:.2f}m (L1/3)")
        else:
            warnings.append(f"✅ **Width W1:** Pass")
            
        if drop_w2 < req_w2:
            warnings.append(f"❌ **Width W2:** {drop_w2:.2f}m < Min {req_w2:.2f}m (L2/3)")
        else:
            warnings.append(f"✅ **Width W2:** Pass")
            
        return warnings

    def check_ddm(self):
        """Checks Direct Design Method (DDM) criteria."""
        status = True
        reasons = []

        # 1. Rectangular Ratio (L_long / L_short <= 2.0)
        long_side = max(self.L1, self.L2)
        short_side = min(self.L1, self.L2)
        ratio = long_side / short_side if short_side > 0 else 0
        
        if ratio > 2.0:
            status = False
            reasons.append(f"❌ **Panel Ratio:** Long/Short ({ratio:.2f}) > 2.0 (ACI Limit)")
        else:
            reasons.append(f"✅ **Panel Ratio:** {ratio:.2f} <= 2.0 (Pass)")

        # 2. Load Ratio (LL/DL <= 2.0)
        load_ratio = self.ll / self.dl if self.dl > 0 else 0
        if load_ratio > 2.0:
            status = False
            reasons.append(f"❌ **Load Ratio:** LL/DL ({load_ratio:.2f}) > 2.0")
        else:
            reasons.append(f"✅ **Load Ratio:** {load_ratio:.2f} <= 2.0 (Pass)")

        # 3. Cantilever Check (Warning only)
        if self.cant['has_left'] and self.cant['L_left'] > (self.L1/3):
             reasons.append(f"⚠️ **Cantilever (Left):** Length {self.cant['L_left']:.2f}m is large relative to span.")
        if self.cant['has_right'] and self.cant['L_right'] > (self.L1/3):
             reasons.append(f"⚠️ **Cantilever (Right):** Length {self.cant['L_right']:.2f}m is large relative to span.")

        reasons.append("ℹ️ **Note:** DDM requires at least 3 continuous spans.")
        return status, reasons

    def check_efm(self):
        """Checks Equivalent Frame Method (EFM) criteria."""
        return True, ["✅ **General:** EFM is applicable for this geometry.", 
                      "✅ **Loads:** No specific restrictions on LL/DL ratio."]

def prepare_calculation_data(
    h_slab_cm, h_drop_cm, has_drop, 
    c1_cm, c2_cm, drop_w2,
    L1_l, L1_r, L2_t, L2_b,
    fc_ksc, fy_grade, 
    dl_kgm2, ll_kgm2,
    auto_sw, lf_dl, lf_ll,
    joint_type, h_up, h_lo,
    far_end_up, far_end_lo,
    cant_params
):
    # Geometry
    h_s = h_slab_cm * Units.CM_TO_M
    h_d = (h_slab_cm + h_drop_cm) * Units.CM_TO_M if has_drop else h_s
    c1 = c1_cm * Units.CM_TO_M
    c2 = c2_cm * Units.CM_TO_M
    b_drop = drop_w2 if has_drop else 0.0
    L1 = L1_l + L1_r
    L2 = L2_t + L2_b
    Ln = L1 - c1
    
    # Roof Logic
    is_roof = (joint_type == 'Roof Joint')
    calc_h_up = 0.0 if is_roof else h_up

    # Materials
    fc_pa = fc_ksc * Units.KSC_TO_PA
    Ec_pa = (4700 * np.sqrt(fc_ksc * Units.KSC_TO_MPA)) * 1e6
    fy_ksc = 3000 if fy_grade == "SD30" else (4000 if fy_grade == "SD40" else 5000)
    fy_pa = fy_ksc * Units.KSC_TO_PA

    # Loads
    density_conc_kg = 2400
    sw_pa = h_s * density_conc_kg * Units.G if auto_sw else 0.0
    sdl_pa = dl_kgm2 * Units.KG_TO_N
    ll_pa = ll_kgm2 * Units.KG_TO_N
    
    w_dead_pa = sw_pa + sdl_pa
    w_u_pa = (lf_dl * w_dead_pa) + (lf_ll * ll_pa) # Area Load (N/m2)
    
    # Stiffness Factor Calculation
    I_col = (c2 * (c1**3)) / 12 
    
    # Upper Column Stiffness
    k_factor_up = 3 if far_end_up == 'Pinned' else 4
    K_col_up = (k_factor_up * Ec_pa * I_col) / calc_h_up if calc_h_up > 0 else 0
    
    # Lower Column Stiffness
    k_factor_lo = 3 if far_end_lo == 'Pinned' else 4
    K_col_lo = (k_factor_lo * Ec_pa * I_col) / h_lo if h_lo > 0 else 0
    
    sum_K_col = K_col_up + K_col_lo

    # Cantilever Moment Calculation
    strip_width = L2 
    w_u_line = w_u_pa * strip_width 
    
    m_cant_left = 0.0
    if cant_params['has_left']:
        lc = cant_params['L_left']
        m_cant_left = (w_u_line * (lc**2)) / 2
        
    m_cant_right = 0.0
    if cant_params['has_right']:
        lc = cant_params['L_right']
        m_cant_right = (w_u_line * (lc**2)) / 2

    # Structural Concept Metadata
    stiffness_desc = []
    if not is_roof:
        stiffness_desc.append(f"Top: {far_end_up} ({k_factor_up}EI/L)")
    stiffness_desc.append(f"Bot: {far_end_lo} ({k_factor_lo}EI/L)")
    
    stiffness_concept = {
        "joint_type": joint_type,
        "rotation_resistance": " + ".join(stiffness_desc),
        "unbalanced_moment_dist": "To Bottom Column Only" if is_roof else "Distributed to Top & Bottom",
        "cantilever_effect": f"Counter-acting Moments: L={m_cant_left/1000:.1f} kN.m, R={m_cant_right/1000:.1f} kN.m"
    }

    return {
        "geom": {"L1": L1, "L2": L2, "Ln": Ln, "c1": c1, "c2": c2, "h_s": h_s, "h_d": h_d, "b_drop": b_drop},
        "vertical_geom": {
            "h_up": calc_h_up, "h_lo": h_lo, "is_roof": is_roof,
            "far_end_up": far_end_up, "far_end_lo": far_end_lo
        },
        "cantilever": cant_params,
        "mat": {"Ec_pa": Ec_pa, "fc_pa": fc_pa, "fy_pa": fy_pa},
        "loads": {"wu_pa": w_u_pa, "w_dead": w_dead_pa},
        "stiffness": {
            "K_up": K_col_up, "K_lo": K_col_lo, "Sum_K": sum_K_col,
            "k_fac_up": k_factor_up, "k_fac_lo": k_factor_lo
        },
        "moments": {
            "M_cant_L": m_cant_left, "M_cant_R": m_cant_right
        },
        "concept": stiffness_concept
    }
