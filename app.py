import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==============================================================================
# 1. SETUP & CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="Flat Slab Design Pro: Advanced", layout="wide")

# Professional Matplotlib Style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 9,
    'axes.titlesize': 11,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'axes.grid': False,
    'axes.facecolor': 'white',
    'figure.facecolor': 'white'
})

# Professional Color Palette
COLORS = {
    'concrete_plan': '#F0F2F5',
    'concrete_cut': '#BDC3C7',
    'column': '#34495E',
    'drop_panel_plan': '#F39C12', 
    'drop_panel_cut': '#9BA4B0', 
    'dim_line': '#566573',
    'strip_line': '#3498DB', 
    'hatch_color': '#7F8C8D',
    'cs_bg': '#D6EAF8',
    'cs_text': '#154360',
    'ms_bg': '#FDFEFE',
    'ms_text': '#566573',
    'cantilever_bg': '#E8DAEF', # Purple tint for cantilever
    'support_symbol': '#2C3E50'
}

# ==============================================================================
# 2. UNIT CONVERSION & CONSTANTS
# ==============================================================================
class Units:
    G = 9.80665  # m/s^2
    CM_TO_M = 0.01
    KG_TO_N = G  # 1 kgf = 9.80665 N
    KSC_TO_PA = 98066.5 
    KSC_TO_MPA = 0.0980665

# ==============================================================================
# 3. ENGINEERING LOGIC & VALIDATOR
# ==============================================================================

class DesignCriteriaValidator:
    """
    Validates design criteria according to ACI 318 for DDM and EFM.
    """
    def __init__(self, L1, L2, L1_l, L1_r, L2_t, L2_b, ll, dl, has_drop, cant_data):
        self.L1 = L1
        self.L2 = L2
        self.L1_spans = [l for l in [L1_l, L1_r] if l > 0]
        self.L2_spans = [l for l in [L2_t, L2_b] if l > 0]
        self.ll = ll
        self.dl = dl
        self.has_drop = has_drop
        self.cant = cant_data

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

    def check_drop_panel(self, h_slab, h_drop, drop_w1, drop_w2, L1_l, L1_r, L2_t, L2_b):
        """Validates Drop Panel dimensions."""
        warnings = []
        if not self.has_drop:
            return warnings

        # Thickness
        if h_drop < (h_slab / 4):
            warnings.append(f"⚠️ **Drop Thickness:** {h_drop} cm < Min {h_slab/4:.2f} cm (h_slab/4)")
            
        return warnings

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
    
    # ---------------------------------------------------------
    # NEW: Stiffness Factor Calculation (4EI vs 3EI)
    # ---------------------------------------------------------
    # I_column (approx uncracked) = b*h^3 / 12
    I_col = (c2 * (c1**3)) / 12 
    
    # Upper Column Stiffness
    k_factor_up = 3 if far_end_up == 'Pinned' else 4
    K_col_up = (k_factor_up * Ec_pa * I_col) / calc_h_up if calc_h_up > 0 else 0
    
    # Lower Column Stiffness
    k_factor_lo = 3 if far_end_lo == 'Pinned' else 4
    K_col_lo = (k_factor_lo * Ec_pa * I_col) / h_lo if h_lo > 0 else 0
    
    sum_K_col = K_col_up + K_col_lo

    # ---------------------------------------------------------
    # NEW: Cantilever Moment Calculation
    # ---------------------------------------------------------
    # Note: We assume cantilever carries the same Area Load as the slab
    # Design Strip Width for Moment Calculation -> Usually L2 (Total Width)
    strip_width = L2 
    
    # Line Load on Strip (N/m)
    w_u_line = w_u_pa * strip_width 
    
    m_cant_left = 0.0
    if cant_params['has_left']:
        lc = cant_params['L_left']
        # M = w * L^2 / 2
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

# ==============================================================================
# 4. VISUALIZATION SYSTEM (ENHANCED)
# ==============================================================================

def draw_dim_line(ax, start, end, text, offset=0.5, axis='x'):
    """Helper function for professional engineering dimension lines"""
    arrow_style = dict(arrowstyle='<|-|>', color=COLORS['dim_line'], linewidth=1.0, shrinkA=0, shrinkB=0)
    ext_line_style = dict(color=COLORS['dim_line'], linewidth=0.5, linestyle='-')
    
    if axis == 'x':
        ax.annotate('', xy=(start[0], start[1]-offset), xytext=(end[0], end[1]-offset), arrowprops=arrow_style)
        ax.plot([start[0], start[0]], [start[1]-0.1, start[1]-offset-0.2], **ext_line_style)
        ax.plot([end[0], end[0]], [end[1]-0.1, end[1]-offset-0.2], **ext_line_style)
        ax.text((start[0]+end[0])/2, start[1]-offset-0.3, text, ha='center', va='top', color=COLORS['dim_line'])
    elif axis == 'y':
        ax.annotate('', xy=(start[0]-offset, start[1]), xytext=(end[0]-offset, end[1]), arrowprops=arrow_style)
        ax.plot([start[0]-0.1, start[0]-offset-0.2], [start[1], start[1]], **ext_line_style)
        ax.plot([end[0]-0.1, end[0]-offset-0.2], [end[1], end[1]], **ext_line_style)
        ax.text(start[0]-offset-0.3, (start[1]+end[1])/2, text, ha='right', va='center', rotation=90, color=COLORS['dim_line'])

def draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_loc, has_drop, d_w1, d_w2, cant_params):
    """High-fidelity Plan View with Cantilevers"""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    c1_m = c1_cm / 100
    c2_m = c2_cm / 100
    
    # Basic Boundary
    slab_L = c1_m/2 if col_loc == "Corner Column" else L1_l
    slab_R = L1_r
    slab_T = L2_t
    slab_B = c2_m/2 if col_loc in ["Edge Column", "Corner Column"] else L2_b
    
    # 1. Cantilever Logic (Expand Boundary)
    cant_L_ext = cant_params['L_left'] if cant_params['has_left'] else 0
    cant_R_ext = cant_params['L_right'] if cant_params['has_right'] else 0
    
    # Adjust total drawing limits
    draw_L = slab_L + cant_L_ext
    draw_R = slab_R + cant_R_ext
    
    # 2. Draw Main Zones (Middle Strip)
    ax.add_patch(patches.Rectangle((-slab_L, -slab_B), slab_L + slab_R, slab_B + slab_T,
                                   facecolor=COLORS['ms_bg'], edgecolor='gray', linewidth=1, zorder=0))
    
    # 3. Draw Cantilever Zones (Distinct Color)
    if cant_params['has_left']:
        ax.add_patch(patches.Rectangle((-slab_L - cant_L_ext, -slab_B), cant_L_ext, slab_B + slab_T,
                                       facecolor=COLORS['cantilever_bg'], edgecolor='gray', linestyle='--', linewidth=1, zorder=0))
        # Label
        ax.text(-slab_L - cant_L_ext/2, 0, "CANTILEVER", rotation=90, ha='center', va='center', 
                color='#8E44AD', fontsize=8, fontweight='bold')

    if cant_params['has_right']:
        ax.add_patch(patches.Rectangle((slab_R, -slab_B), cant_R_ext, slab_B + slab_T,
                                       facecolor=COLORS['cantilever_bg'], edgecolor='gray', linestyle='--', linewidth=1, zorder=0))
        # Label
        ax.text(slab_R + cant_R_ext/2, 0, "CANTILEVER", rotation=90, ha='center', va='center', 
                color='#8E44AD', fontsize=8, fontweight='bold')

    # 4. Column Strip
    min_span = min(L1_l + L1_r, L2_t + L2_b)
    cs_width = 0.25 * min_span
    cs_top = min(cs_width, slab_T)
    cs_bot = min(cs_width, slab_B)
    
    # Draw CS Rect (Main Span)
    ax.add_patch(patches.Rectangle((-slab_L, -cs_bot), slab_L + slab_R, cs_top + cs_bot,
                                   facecolor=COLORS['cs_bg'], edgecolor='none', alpha=0.6, zorder=1))
    
    # Extend CS into Cantilever? Usually CS extends into cantilever.
    if cant_params['has_left']:
         ax.add_patch(patches.Rectangle((-slab_L - cant_L_ext, -cs_bot), cant_L_ext, cs_top + cs_bot,
                                   facecolor=COLORS['cs_bg'], edgecolor='none', alpha=0.4, zorder=1))
    if cant_params['has_right']:
         ax.add_patch(patches.Rectangle((slab_R, -cs_bot), cant_R_ext, cs_top + cs_bot,
                                   facecolor=COLORS['cs_bg'], edgecolor='none', alpha=0.4, zorder=1))

    # Dashed Separators
    line_props = dict(color=COLORS['strip_line'], linestyle='--', linewidth=0.8, alpha=0.7)
    if cs_top < slab_T: ax.axhline(y=cs_top, **line_props)
    if cs_bot < slab_B: ax.axhline(y=-cs_bot, **line_props)

    # Labeling
    ax.text((slab_R - slab_L)/2, 0, "COLUMN STRIP", color=COLORS['cs_text'], 
            fontsize=10, fontweight='bold', ha='center', va='center',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.3, pad=1))

    # 5. Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w1/2, -d_w2/2), d_w1, d_w2, 
                                       facecolor='none', edgecolor=COLORS['drop_panel_plan'], 
                                       linestyle='-', linewidth=2, zorder=5))

    # 6. Columns
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                   facecolor=COLORS['column'], edgecolor='black', hatch='//', zorder=10))
    
    # Ghost Columns (Only in spans, not cantilevers)
    ghost_props = dict(facecolor='white', edgecolor=COLORS['concrete_cut'], linestyle='--', linewidth=1.5, zorder=4)
    if L1_r > 0: ax.add_patch(patches.Rectangle((L1_r - c1_m/2, -c2_m/2), c1_m, c2_m, **ghost_props))
    if L1_l > 0 and col_loc != "Corner Column": ax.add_patch(patches.Rectangle((-L1_l - c1_m/2, -c2_m/2), c1_m, c2_m, **ghost_props))
    
    # 7. Dimensions (Updated for Cantilever)
    def draw_ext_dim(x1, y1, x2, y2, text, offset):
        mid_x, mid_y = (x1 + x2)/2, (y1 + y2)/2
        if x1 == x2: # Vertical
            x1 += offset; x2 += offset; mid_x += offset
            rot = 90; ha, va = ('right', 'center') if offset < 0 else ('left', 'center')
            ax.plot([x1-0.1, x1+0.1], [y1, y1], color=COLORS['dim_line'], lw=0.5)
            ax.plot([x2-0.1, x2+0.1], [y2, y2], color=COLORS['dim_line'], lw=0.5)
        else: # Horizontal
            y1 += offset; y2 += offset; mid_y += offset
            rot = 0; ha, va = ('center', 'top') if offset < 0 else ('center', 'bottom')
            ax.plot([x1, x1], [y1-0.1, y1+0.1], color=COLORS['dim_line'], lw=0.5)
            ax.plot([x2, x2], [y2-0.1, y2+0.1], color=COLORS['dim_line'], lw=0.5)
            
        ax.annotate('', xy=(x1, y1), xytext=(x2, y2), arrowprops=dict(arrowstyle='<|-|>', color=COLORS['dim_line'], lw=0.8))
        ax.text(mid_x, mid_y, text, rotation=rot, ha=ha, va=va, fontsize=9, color=COLORS['dim_line'], fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1))

    m_x, m_y = -draw_L - 0.8, -slab_B - 0.8
    
    # L1 Dimensions
    if cant_params['has_left']:
        draw_ext_dim(-slab_L - cant_L_ext, -slab_B, -slab_L, -slab_B, f"Cant L={cant_L_ext:.2f}", m_y - (-slab_B))
    
    if L1_l > 0 and col_loc != "Corner Column": 
        draw_ext_dim(-L1_l, -slab_B, 0, -slab_B, f"L1(L)={L1_l:.2f}", m_y - (-slab_B))
    
    draw_ext_dim(0, -slab_B, L1_r, -slab_B, f"L1(R)={L1_r:.2f}", m_y - (-slab_B))
    
    if cant_params['has_right']:
        draw_ext_dim(L1_r, -slab_B, L1_r + cant_R_ext, -slab_B, f"Cant R={cant_R_ext:.2f}", m_y - (-slab_B))

    # L2 Dimensions
    draw_ext_dim(-draw_L, 0, -draw_L, L2_t, f"L2(T)={L2_t:.2f}", m_x - (-draw_L))

    ax.set_title(f"STRUCTURAL LAYOUT: {col_loc.upper()}", fontsize=12, pad=20, fontweight='bold', color='#566573')
    ax.set_xlim(-draw_L - 1.5, draw_R + 1.5)
    ax.set_ylim(-slab_B - 2.0, slab_T + 1.0)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, 
                              is_roof, far_end_up, far_end_lo, cant_params):
    """
    High-fidelity Section View with Boundary Conditions and Cantilevers
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    
    s_m = h_slab_cm / 100
    d_m = h_drop_cm / 100 if has_drop else 0
    c_m = c1_cm / 100
    d_w = drop_w1 if has_drop else 0
    
    # Setup Views
    # Cantilever View Extension
    cant_L_draw = cant_params['L_left'] if cant_params['has_left'] else 1.5
    cant_R_draw = cant_params['L_right'] if cant_params['has_right'] else 1.5
    
    # Boundary logic for drawing
    x_min = -cant_L_draw if cant_params['has_left'] else -1.5
    x_max = cant_R_draw if cant_params['has_right'] else 1.5
    
    view_top = 0.8 if not is_roof else 0.1
    view_bot = -(s_m + d_m + 0.8)
    
    col_concrete = '#ECF0F1'
    col_cant = '#F4ECF7' # Lighter purple for section
    col_hatch = '#BDC3C7'
    col_dim = '#2C3E50'
    
    # --- Helper: Draw Support Symbols ---
    def draw_support_symbol(x, y, kind, orientation='bottom'):
        """Draws Fixed or Pinned symbols"""
        sz = 0.15
        if kind == 'Fixed':
            # Horizontal line
            ax.plot([x-sz, x+sz], [y, y], color='black', linewidth=2)
            # Hatch lines
            hatch_step = sz/2
            if orientation == 'bottom':
                for i in np.arange(x-sz, x+sz, 0.05):
                    ax.plot([i, i-0.05], [y, y-0.05], color='black', linewidth=0.5)
            else: # top
                for i in np.arange(x-sz, x+sz, 0.05):
                    ax.plot([i, i-0.05], [y, y+0.05], color='black', linewidth=0.5)
        elif kind == 'Pinned':
            # Triangle
            if orientation == 'bottom':
                triangle = patches.Polygon([[x, y], [x-sz/1.5, y-sz], [x+sz/1.5, y-sz]], 
                                           closed=True, facecolor='white', edgecolor='black', linewidth=1)
                base = patches.Rectangle((x-sz, y-sz-0.02), sz*2, 0.02, color='black')
            else: # top
                triangle = patches.Polygon([[x, y], [x-sz/1.5, y+sz], [x+sz/1.5, y+sz]], 
                                           closed=True, facecolor='white', edgecolor='black', linewidth=1)
                base = patches.Rectangle((x-sz, y+sz), sz*2, 0.02, color='black')
            
            ax.add_patch(triangle)
            ax.add_patch(base)
            # Hinge circle
            circle = patches.Circle((x, y), 0.02, facecolor='white', edgecolor='black')
            ax.add_patch(circle)

    def draw_break(x, y, w):
        if y != 0: # Don't draw break on joint
            ax.plot([x-w/2, x-w/4, x+w/4, x+w/2], [y, y-0.05, y+0.05, y], color='black', linewidth=1)

    # 1. Structure
    # Column Upper
    if not is_roof:
        ax.add_patch(patches.Rectangle((-c_m/2, 0), c_m, view_top, facecolor='white', edgecolor='black', linewidth=1))
        draw_support_symbol(0, view_top, far_end_up, 'top')
    
    # Column Lower
    bot_struct = -(s_m + d_m)
    ax.add_patch(patches.Rectangle((-c_m/2, view_bot), c_m, abs(view_bot - bot_struct), facecolor='white', edgecolor='black', linewidth=1))
    draw_support_symbol(0, view_bot, far_end_lo, 'bottom')

    # Slab (Continuous)
    # Define left/right extent
    left_x = -cant_params['L_left'] if cant_params['has_left'] else -1.5
    right_x = cant_params['L_right'] if cant_params['has_right'] else 1.5
    
    # Main Slab
    ax.add_patch(patches.Rectangle((left_x, -s_m), (abs(left_x)+right_x), s_m, facecolor=col_concrete, edgecolor='black', linewidth=1, zorder=5))
    ax.add_patch(patches.Rectangle((left_x, -s_m), (abs(left_x)+right_x), s_m, fill=False, edgecolor=col_hatch, hatch='///', linewidth=0, zorder=6))
    
    # Cantilever Highlighting (Optional overlay)
    if cant_params['has_left']:
        ax.add_patch(patches.Rectangle((-cant_params['L_left'], -s_m), cant_params['L_left'], s_m, facecolor=col_cant, alpha=0.3, zorder=7))
    if cant_params['has_right']:
        ax.add_patch(patches.Rectangle((0, -s_m), cant_params['L_right'], s_m, facecolor=col_cant, alpha=0.3, zorder=7))

    # Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w/2, bot_struct), d_w, d_m, facecolor=col_concrete, edgecolor='black', linewidth=1, zorder=5))
        ax.add_patch(patches.Rectangle((-d_w/2, bot_struct), d_w, d_m, fill=False, edgecolor=col_hatch, hatch='///', linewidth=0, zorder=6))

    # 2. Dimensions
    def draw_side_dim(y_start, y_end, x_loc, label):
        ax.annotate('', xy=(x_loc, y_start), xytext=(x_loc, y_end),
                    arrowprops=dict(arrowstyle='<|-|>', color=col_dim, linewidth=0.8, shrinkA=0, shrinkB=0))
        mid_y = (y_start + y_end) / 2
        ax.text(x_loc + 0.15, mid_y, label, ha='center', va='center', rotation=90, 
                fontsize=9, color=col_dim, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))

    # Slab Thickness
    ax.text(left_x, -s_m/2, f" {h_slab_cm}cm", va='center', ha='right', fontsize=9, color=col_dim)

    # Height Dims
    dim_x_right = c_m/2 + 0.5
    if not is_roof:
        draw_side_dim(0, view_top, dim_x_right, f"Up: {h_up:.2f}m")
    draw_side_dim(-(s_m+d_m), view_bot, dim_x_right, f"Lo: {h_lo:.2f}m")

    # Cantilever Dims
    dim_y_top = 0.3
    if cant_params['has_left']:
        L = cant_params['L_left']
        ax.annotate('', xy=(-L, dim_y_top), xytext=(0, dim_y_top), arrowprops=dict(arrowstyle='<|-|>', color='purple'))
        ax.text(-L/2, dim_y_top + 0.05, f"Cantilever {L:.2f}m", color='purple', ha='center', fontsize=9, fontweight='bold')
        ax.plot([-L, -L], [0, dim_y_top], linestyle=':', color='purple', lw=0.5)

    if cant_params['has_right']:
        L = cant_params['L_right']
        ax.annotate('', xy=(0, dim_y_top), xytext=(L, dim_y_top), arrowprops=dict(arrowstyle='<|-|>', color='purple'))
        ax.text(L/2, dim_y_top + 0.05, f"Cantilever {L:.2f}m", color='purple', ha='center', fontsize=9, fontweight='bold')
        ax.plot([L, L], [0, dim_y_top], linestyle=':', color='purple', lw=0.5)

    # T.O.S Marker
    ax.text(left_x + 0.2, 0.05, "▼ T.O. Slab (+0.00)", color='blue', fontsize=8, fontweight='bold')
    ax.axhline(0, color='blue', linestyle='-.', linewidth=0.5, alpha=0.5)

    ax.set_aspect('equal')
    ax.set_xlim(left_x - 0.5, right_x + 0.5)
    ax.set_ylim(view_bot - 0.5, view_top + 0.5)
    ax.axis('off')
    
    title_suffix = " (Pinned Ends)" if (far_end_lo == 'Pinned' or far_end_up == 'Pinned') else ""
    ax.set_title(f"SECTION DETAIL: {is_roof and 'ROOF' or 'INTERMEDIATE'} JOINT{title_suffix}", 
                 fontsize=10, color='gray', pad=10, fontweight='bold')
    return fig

# ==============================================================================
# 5. MAIN APPLICATION INTERFACE
# ==============================================================================

st.title("🏗️ Flat Slab Design: Advanced Frame Analysis")
st.markdown("---")

if 'col_loc' not in st.session_state:
    st.session_state['col_loc'] = "Interior Column"

# --- Sidebar Report ---
st.sidebar.header("📊 Design Report")
status_container = st.sidebar.container()

tab1, tab2 = st.tabs(["📝 Input Parameters", "📘 Engineering Theory"])

with tab1:
    col_input, col_viz = st.columns([1.2, 1.4])

    with col_input:
        # 1. Materials
        st.subheader("1. Materials & Loads")
        c1_mat, c2_mat = st.columns(2)
        with c1_mat: fc = st.selectbox("Concrete f'c (ksc)", [240, 280, 320, 350, 400], index=1)
        with c2_mat: fy = st.selectbox("Steel Grade (fy)", ["SD30", "SD40", "SD50"], index=1)

        lf_col1, lf_col2 = st.columns(2)
        with lf_col1: lf_dl = st.number_input("DL Factor", value=1.2, step=0.1, format="%.2f")
        with lf_col2: lf_ll = st.number_input("LL Factor", value=1.6, step=0.1, format="%.2f")
        
        auto_sw = st.checkbox("✅ Auto-calculate Self-weight", value=True)
        dl = st.number_input("Superimposed Dead Load (SDL) [kg/m²]", value=100, step=10)
        ll = st.number_input("Live Load (LL) [kg/m²]", value=200, step=50)

        st.divider()

        # 3. Geometry (Updated)
        st.subheader("2. Geometry & Boundary Conditions")
        
        # Joint Type
        joint_type = st.radio(
            "Column Joint Condition:",
            ("Intermediate Floor", "Roof Joint"),
            horizontal=True
        )
        is_roof = (joint_type == "Roof Joint")
        joint_code = "Roof" if is_roof else "Interm."
        
        # --- NEW: Far End Conditions ---
        st.markdown("##### 📍 Column Far End Conditions (Stiffness)")
        f_col1, f_col2 = st.columns(2)
        
        far_end_up = "N/A"
        if not is_roof:
            with f_col1:
                far_end_up = st.selectbox("Upper Col Far End", ["Fixed (4EI/L)", "Pinned (3EI/L)"], index=0)
                far_end_up = far_end_up.split()[0] # Get 'Fixed' or 'Pinned'
        else:
             with f_col1: st.info("Upper Col: None")

        with f_col2:
            far_end_lo = st.selectbox("Lower Col Far End", ["Fixed (4EI/L)", "Pinned (3EI/L)"], index=0)
            far_end_lo = far_end_lo.split()[0]

        # Plan Layout
        st.markdown("##### 📏 Span Dimensions")
        col_location = st.selectbox("Plan Location", ["Interior Column", "Edge Column", "Corner Column"])
        is_corner = (col_location == "Corner Column")
        is_edge = (col_location == "Edge Column")
        
        col_l1a, col_l1b = st.columns(2)
        with col_l1a:
            l1_l_val = 0.0 if is_corner else 4.0
            L1_l = st.number_input("L1 - Left Span (m)", value=l1_l_val, disabled=is_corner)
        with col_l1b:
            L1_r = st.number_input("L1 - Right Span (m)", value=4.0)
            
        col_l2a, col_l2b = st.columns(2)
        with col_l2a:
            L2_t = st.number_input("L2 - Top Half (m)", value=4.0)
        with col_l2b:
            l2_b_val = 0.0 if (is_edge or is_corner) else 4.0
            L2_b = st.number_input("L2 - Bottom Half (m)", value=l2_b_val, disabled=(is_edge or is_corner))

        # --- NEW: Cantilever Settings ---
        st.markdown("##### 🏗️ Cantilever / Eave (Overhang)")
        with st.expander("Cantilever Configuration", expanded=True):
            cant_c1, cant_c2 = st.columns(2)
            has_cant_left = False
            L_cant_left = 0.0
            has_cant_right = False
            L_cant_right = 0.0
            
            with cant_c1:
                has_cant_left = st.checkbox("Left Cantilever", value=False, disabled=(L1_l > 0)) # Disable if there is a backspan? Actually cantilever usually is on free edge.
                # Allow cantilever even if backspan exists? Usually cantilever is the end. 
                # Simplification: Allow cantilever only if Span is 0 OR explicitly enabled for double cantilever (rare but possible). 
                # Let's trust the engineer, just enable input.
                if has_cant_left:
                    L_cant_left = st.number_input("Left Length (m)", value=1.5, step=0.1)
            
            with cant_c2:
                has_cant_right = st.checkbox("Right Cantilever", value=False)
                if has_cant_right:
                    L_cant_right = st.number_input("Right Length (m)", value=1.5, step=0.1)
            
            cant_params = {
                "has_left": has_cant_left, "L_left": L_cant_left,
                "has_right": has_cant_right, "L_right": L_cant_right
            }

        # Structural Dims
        st.markdown("##### 🧱 Member Sizes")
        h_slab_cm = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0)
        col_sz1, col_sz2 = st.columns(2)
        with col_sz1: c1_cm = st.number_input("Column c1 (Analysis) [cm]", value=50.0)
        with col_sz2: c2_cm = st.number_input("Column c2 (Transverse) [cm]", value=50.0)

        h_up = 0.0
        if not is_roof:
            h_up = st.number_input("Upper Storey Height (m)", value=3.0)
        h_lo = st.number_input("Lower Storey Height (m)", value=3.0)

        # Drop Panel
        has_drop = st.checkbox("Include Drop Panel", value=False)
        h_drop_cm, drop_w1, drop_w2 = 0.0, 0.0, 0.0
        if has_drop:
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1: h_drop_cm = st.number_input("Drop Depth (cm)", value=10.0)
            with d_col2: drop_w1 = st.number_input("Drop W1 (m)", value=2.5)
            with d_col3: drop_w2 = st.number_input("Drop W2 (m)", value=2.5)

        # --- Calculation ---
        calc_obj = prepare_calculation_data(
            h_slab_cm, h_drop_cm, has_drop, c1_cm, c2_cm, drop_w2,
            L1_l, L1_r, L2_t, L2_b, fc, fy, dl, ll, auto_sw, lf_dl, lf_ll,
            joint_type, h_up, h_lo, far_end_up, far_end_lo, cant_params
        )

        validator = DesignCriteriaValidator(
            calc_obj['geom']['L1'], calc_obj['geom']['L2'], L1_l, L1_r, L2_t, L2_b,
            ll, (calc_obj['loads']['w_dead'] / Units.G), has_drop, cant_params
        )

        ddm_ok, ddm_reasons = validator.check_ddm()
        efm_ok, efm_reasons = validator.check_efm()
        drop_warnings = validator.check_drop_panel(h_slab_cm, h_drop_cm, drop_w1, drop_w2, L1_l, L1_r, L2_t, L2_b)

        # Sidebar Update
        with status_container:
            st.markdown(f"**Condition:** `{joint_code}`")
            st.markdown(f"**Far Ends:** Top `{far_end_up}` | Bot `{far_end_lo}`")
            if ddm_ok: st.success("✅ **DDM:** Valid")
            else: st.error("❌ **DDM:** Invalid")
            st.info("✅ **EFM:** Valid")

    with col_viz:
        st.subheader("👁️ Visualization & Analysis")
        v_tab1, v_tab2 = st.tabs(["📐 Plan View", "🔍 True-Scale Section"])
        
        with v_tab1:
            fig_plan = draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_location, has_drop, drop_w1, drop_w2, cant_params)
            st.pyplot(fig_plan)
        
        with v_tab2:
            fig_elev = draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, 
                                                is_roof, far_end_up, far_end_lo, cant_params)
            st.pyplot(fig_elev)
            
        # Analysis Report
        st.markdown("### 📋 Analysis Results")
        
        # 1. Stiffness Report
        st.markdown("#### 1. Column Stiffness ($K_{col}$)")
        k_data = calc_obj['stiffness']
        c_k1, c_k2, c_k3 = st.columns(3)
        with c_k1: st.metric("K Top", f"{k_data['K_up']/1e6:.2f}", f"Factor: {k_data['k_fac_up']}EI")
        with c_k2: st.metric("K Bottom", f"{k_data['K_lo']/1e6:.2f}", f"Factor: {k_data['k_fac_lo']}EI")
        with c_k3: st.metric("Sum Kec", f"{k_data['Sum_K']/1e6:.2f}", "MN.m")
        
        # 2. Cantilever Moment Report
        if cant_params['has_left'] or cant_params['has_right']:
            st.markdown("#### 2. Cantilever Balancing Moment ($M_{cant}$)")
            st.caption("Moment from Cantilever helps balance the interior span moment.")
            m_data = calc_obj['moments']
            mc1, mc2 = st.columns(2)
            with mc1: 
                if cant_params['has_left']: st.metric("Left Moment (Neg)", f"{m_data['M_cant_L']/1000:.2f} kN.m")
            with mc2:
                if cant_params['has_right']: st.metric("Right Moment (Neg)", f"{m_data['M_cant_R']/1000:.2f} kN.m")
        
        st.divider()
        with st.expander(f"Code Check Details", expanded=False):
            if drop_warnings:
                st.warning("Drop Panel Geometry Warnings:")
                for w in drop_warnings: st.write(f"- {w}")
            for r in ddm_reasons: st.markdown(r)

with tab2:
    st.header("📘 Advanced Engineering Theory")
    st.markdown(r"""
    ### 1. Column Far End Conditions
    The boundary condition at the far end of the column significantly affects its flexural stiffness ($K_c$).
    
    * **Fixed End:** Represents a rigid connection (e.g., to a massive footing or a rigid floor below).
        $$ K_{col} = \frac{4EI}{L} $$
    * **Pinned End:** Represents a hinged connection (e.g., a simple footing on soil or a theoretical pin).
        $$ K_{col} = \frac{3EI}{L} $$
    
    *Selecting "Pinned" reduces the column's ability to resist unbalanced moments by 25%.*

    ---

    ### 2. Cantilever Action (Balancing Moment)
    Cantilevers (Overhangs) provide a static negative moment ($M_{cant}$) at the joint, which counteracts the unbalanced moment from the interior span.
    
    $$ M_{cant} = \frac{w_u \cdot L_{cant}^2}{2} $$

    * **Benefit:** This reduces the net unbalanced moment ($M_{unb}$) that the column must resist.
    * **Design Note:** For Roof Joints, adding a cantilever is the most effective way to eliminate Punching Shear problems caused by high unbalanced moments.
    """)
