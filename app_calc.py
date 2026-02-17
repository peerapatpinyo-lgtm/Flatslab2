# app_calc.py
import numpy as np
from app_config import Units

class DesignCriteriaValidator:
    def __init__(self, L1, L2, L1_l, L1_r, L2_t, L2_b, ll, dl, has_drop, cant_data, 
                 fy_ksc, col_location, h_slab_cm, c1, c2, edge_beam_params=None):
        self.L1 = L1
        self.L2 = L2
        # ACI 318: Ln is clear span in long direction
        self.c_avg = (c1 + c2) / 2.0
        self.Ln_long = max(L1, L2) - self.c_avg 
        
        self.ll = ll
        self.dl = dl
        self.has_drop = has_drop
        self.cant = cant_data
        
        # Materials
        self.fy_mpa = (300 if fy_ksc == "SD30" else (400 if fy_ksc == "SD40" else 500))
        self.col_location = col_location 
        self.h_slab_cm = h_slab_cm
        
        # Edge Beam
        self.edge_beam = edge_beam_params if edge_beam_params else {"has_beam": False}

    def check_min_thickness_detailed(self):
        """Returns detailed calculation steps for Minimum Slab Thickness"""
        is_ext = (self.col_location in ["Edge Column", "Corner Column"])
        has_edge_beam = self.edge_beam.get('has_beam', False)
        
        # ACI 318 Table 8.3.1.1 Logic
        if self.has_drop:
            # Case: With Drop Panel
            if not is_ext:
                denom = 36.0 # Interior
                case_desc = "Interior Panel (With Drop)"
            else:
                # Exterior
                if has_edge_beam:
                    denom = 36.0 # Exterior with Edge Beam
                    case_desc = "Exterior Panel (With Drop & Edge Beam)"
                else:
                    denom = 33.0 # Exterior without Edge Beam
                    case_desc = "Exterior Panel (With Drop, No Beam)"
        else:
            # Case: Flat Plate (No Drop)
            if not is_ext:
                denom = 33.0 # Interior
                case_desc = "Interior Flat Plate"
            else:
                # Exterior
                if has_edge_beam:
                    denom = 33.0 # Exterior with Edge Beam
                    case_desc = "Exterior Flat Plate (With Edge Beam)"
                else:
                    denom = 30.0 # Exterior without Edge Beam
                    case_desc = "Exterior Flat Plate (No Beam)"

        # Fy Correction Factor (ACI 318-19)
        fy_factor = 0.8 + (self.fy_mpa / 1400)
        
        # Calculation
        min_h_m = (self.Ln_long * fy_factor) / denom
        min_h_cm_calc = min_h_m * 100
        
        # Absolute Minimum Limits
        abs_min = 10.0 if self.has_drop else 12.5
        req_h_cm = max(min_h_cm_calc, abs_min)

        status = self.h_slab_cm >= req_h_cm
        
        return {
            "status": status, "Ln": self.Ln_long, "fy_mpa": self.fy_mpa,
            "denom": denom, "case_name": case_desc, "calc_h": min_h_cm_calc,
            "abs_min": abs_min, "req_h": req_h_cm, "actual_h": self.h_slab_cm
        }

    def check_drop_panel_detailed(self, h_drop_cm, drop_w1, drop_w2):
        """Returns VERY detailed calculation for Drop Panel Check (ACI 318)"""
        if not self.has_drop:
            return None

        # --- 1. Depth Check (ACI 8.2.4) ---
        # Projection below slab must be >= h_s / 4
        req_proj = self.h_slab_cm / 4
        act_proj = h_drop_cm # In this app, input is the projection depth
        chk_depth = act_proj >= req_proj

        # --- 2. Extension Check (ACI 8.2.4) ---
        # Extend >= L/6 from center of support in each direction.
        # Total Width >= 2 * (L/6) = L/3
        
        # Direction 1 (L1)
        req_ext_1 = self.L1 / 6.0
        req_total_w1 = self.L1 / 3.0
        chk_w1 = drop_w1 >= req_total_w1
        
        # Direction 2 (L2)
        req_ext_2 = self.L2 / 6.0
        req_total_w2 = self.L2 / 3.0
        chk_w2 = drop_w2 >= req_total_w2
        
        status = chk_depth and chk_w1 and chk_w2
        
        return {
            "status": status,
            "h_slab": self.h_slab_cm,
            # Depth Data
            "req_proj": req_proj, "act_proj": act_proj, "chk_depth": chk_depth,
            # Width Data 1
            "L1": self.L1, "req_ext_1": req_ext_1, "req_total_w1": req_total_w1, 
            "act_w1": drop_w1, "chk_w1": chk_w1,
            # Width Data 2
            "L2": self.L2, "req_ext_2": req_ext_2, "req_total_w2": req_total_w2, 
            "act_w2": drop_w2, "chk_w2": chk_w2
        }

    def check_ddm(self):
        status = True
        reasons = []
        # Aspect Ratio
        long_side = max(self.L1, self.L2)
        short_side = min(self.L1, self.L2)
        ratio = long_side / short_side if short_side > 0 else 0
        if ratio > 2.0:
            status = False
            reasons.append(f"❌ **Panel Ratio:** Long/Short ({ratio:.2f}) > 2.0")
        else:
            reasons.append(f"✅ **Panel Ratio:** {ratio:.2f} <= 2.0")
            
        # Load Ratio
        load_ratio = self.ll / self.dl if self.dl > 0 else 0
        if load_ratio > 2.0:
            status = False
            reasons.append(f"❌ **Load Ratio:** LL/DL ({load_ratio:.2f}) > 2.0")
        else:
            reasons.append(f"✅ **Load Ratio:** {load_ratio:.2f} <= 2.0")

        return status, reasons

def prepare_calculation_data(
    h_slab_cm, h_drop_cm, has_drop, 
    c1_cm, c2_cm, drop_w2,
    L1_l, L1_r, L2_t, L2_b,
    fc_ksc, fy_grade, 
    dl_kgm2, ll_kgm2,
    auto_sw, lf_dl, lf_ll,
    joint_type, h_up, h_lo,
    far_end_up, far_end_lo,
    cant_params,
    edge_beam_params # <--- Added Argument here
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
    w_u_pa = (lf_dl * w_dead_pa) + (lf_ll * ll_pa) 
    
    # Stiffness Factor Calculation
    I_col = (c2 * (c1**3)) / 12 
    
    k_factor_up = 3 if far_end_up == 'Pinned' else 4
    K_col_up = (k_factor_up * Ec_pa * I_col) / calc_h_up if calc_h_up > 0 else 0
    
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
        "geom": {
            "L1": L1, "L2": L2, "Ln": Ln, "c1": c1, "c2": c2, 
            "h_s": h_s, "h_d": h_d, "b_drop": b_drop,
            "edge_beam_params": edge_beam_params # <--- Included in return dict
        },
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
