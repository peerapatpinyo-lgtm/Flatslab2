import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==============================================================================
# 1. SETUP & CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="Flat Slab Design Pro", layout="wide")

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
    'ms_text': '#566573'
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
    def __init__(self, L1, L2, L1_l, L1_r, L2_t, L2_b, ll, dl, has_drop):
        self.L1 = L1
        self.L2 = L2
        self.L1_spans = [l for l in [L1_l, L1_r] if l > 0]
        self.L2_spans = [l for l in [L2_t, L2_b] if l > 0]
        self.ll = ll
        self.dl = dl
        self.has_drop = has_drop

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

        # 3. Successive Span Difference
        if len(self.L1_spans) == 2:
            l_max = max(self.L1_spans)
            l_min = min(self.L1_spans)
            diff_ratio = (l_max - l_min) / l_max
            if diff_ratio > 0.33:
                status = False
                reasons.append(f"❌ **Span Diff:** Difference {diff_ratio*100:.1f}% > 33%")
            else:
                reasons.append(f"✅ **Span Diff:** Pass ({diff_ratio*100:.1f}%)")
        
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

        # Extension L1
        max_L1 = max(L1_l, L1_r) if (L1_l + L1_r) > 0 else 1.0
        min_ext_L1 = max_L1 / 6
        if (drop_w1 / 2) < min_ext_L1:
            warnings.append(f"⚠️ **Drop Width L1:** Extension {drop_w1/2:.2f} m < Min {min_ext_L1:.2f} m (L1/6)")

        # Extension L2
        max_L2 = max(L2_t, L2_b) if (L2_t + L2_b) > 0 else 1.0
        min_ext_L2 = max_L2 / 6
        if (drop_w2 / 2) < min_ext_L2:
            warnings.append(f"⚠️ **Drop Width L2:** Extension {drop_w2/2:.2f} m < Min {min_ext_L2:.2f} m (L2/6)")
            
        return warnings

def prepare_calculation_data(
    h_slab_cm, h_drop_cm, has_drop, 
    c1_cm, c2_cm, drop_w2,
    L1_l, L1_r, L2_t, L2_b,
    fc_ksc, fy_grade, 
    dl_kgm2, ll_kgm2,
    auto_sw, lf_dl, lf_ll,
    joint_type, h_up, h_lo 
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
    
    # Roof Logic (Force h_up to 0 if Roof)
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
    wu_pa = (lf_dl * w_dead_pa) + (lf_ll * ll_pa)
    
    # Structural Concept Metadata
    stiffness_concept = {
        "joint_type": joint_type,
        "rotation_resistance": "K_col_bot" if is_roof else "K_col_top + K_col_bot",
        "unbalanced_moment_dist": "To Bottom Column Only" if is_roof else "Distributed to Top & Bottom"
    }

    return {
        "geom": {"L1": L1, "L2": L2, "Ln": Ln, "c1": c1, "c2": c2, "h_s": h_s, "h_d": h_d, "b_drop": b_drop},
        "vertical_geom": {"h_up": calc_h_up, "h_lo": h_lo, "is_roof": is_roof},
        "mat": {"Ec_pa": Ec_pa, "fc_pa": fc_pa, "fy_pa": fy_pa},
        "loads": {"wu_pa": wu_pa, "sw_pa": sw_pa, "sdl_pa": sdl_pa, "ll_pa": ll_pa, "w_dead": w_dead_pa},
        "raw": {"dl": dl_kgm2, "ll": ll_kgm2},
        "concept": stiffness_concept
    }

# ==============================================================================
# 4. VISUALIZATION SYSTEM
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

def draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_loc, has_drop, d_w1, d_w2):
    """High-fidelity Plan View with Zone Labeling and Dimensions"""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 1. Config & Scales
    c1_m = c1_cm / 100
    c2_m = c2_cm / 100
    
    # Boundary Calculation
    slab_L = c1_m/2 if col_loc == "Corner Column" else L1_l
    slab_R = L1_r
    slab_T = L2_t
    slab_B = c2_m/2 if col_loc in ["Edge Column", "Corner Column"] else L2_b
    
    # 2. Draw Zones
    ax.add_patch(patches.Rectangle((-slab_L, -slab_B), slab_L + slab_R, slab_B + slab_T,
                                   facecolor=COLORS['ms_bg'], edgecolor='gray', linewidth=1, zorder=0))
    
    min_span = min(L1_l + L1_r, L2_t + L2_b)
    cs_width = 0.25 * min_span
    cs_top = min(cs_width, slab_T)
    cs_bot = min(cs_width, slab_B)
    
    ax.add_patch(patches.Rectangle((-slab_L, -cs_bot), slab_L + slab_R, cs_top + cs_bot,
                                   facecolor=COLORS['cs_bg'], edgecolor='none', alpha=0.6, zorder=1))
    
    line_props = dict(color=COLORS['strip_line'], linestyle='--', linewidth=0.8, alpha=0.7)
    if cs_top < slab_T: ax.axhline(y=cs_top, **line_props)
    if cs_bot < slab_B: ax.axhline(y=-cs_bot, **line_props)

    # Labeling
    text_x_pos = slab_R * 0.6
    ax.text(text_x_pos, 0, "COLUMN STRIP", color=COLORS['cs_text'], 
            fontsize=10, fontweight='bold', ha='center', va='center',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.3, pad=1))
    
    if cs_top < slab_T:
        ax.text(text_x_pos, (cs_top + slab_T) / 2, "MIDDLE STRIP", color=COLORS['ms_text'], 
                fontsize=9, fontweight='bold', ha='center', va='center')     
    if cs_bot < slab_B:
        ax.text(text_x_pos, -(cs_bot + slab_B) / 2, "MIDDLE STRIP", color=COLORS['ms_text'], 
                fontsize=9, fontweight='bold', ha='center', va='center')

    # 3. Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w1/2, -d_w2/2), d_w1, d_w2, 
                                       facecolor='none', edgecolor=COLORS['drop_panel_plan'], 
                                       linestyle='-', linewidth=2, zorder=5))
        ax.text(0, d_w2/2 + 0.15, f"Drop W1 = {d_w1:.2f}m", color=COLORS['drop_panel_plan'], fontsize=8, fontweight='bold', ha='center')
        ax.text(d_w1/2 + 0.15, 0, f"Drop W2\n{d_w2:.2f}m", color=COLORS['drop_panel_plan'], fontsize=8, fontweight='bold', va='center')

    # 4. Columns
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                   facecolor=COLORS['column'], edgecolor='black', hatch='//', zorder=10))
    ghost_props = dict(facecolor='white', edgecolor=COLORS['concrete_cut'], linestyle='--', linewidth=1.5, zorder=4)
    if L1_r > 0: ax.add_patch(patches.Rectangle((L1_r - c1_m/2, -c2_m/2), c1_m, c2_m, **ghost_props))
    if L1_l > 0 and col_loc != "Corner Column": ax.add_patch(patches.Rectangle((-L1_l - c1_m/2, -c2_m/2), c1_m, c2_m, **ghost_props))
    if L2_t > 0: ax.add_patch(patches.Rectangle((-c1_m/2, L2_t - c2_m/2), c1_m, c2_m, **ghost_props))
    if L2_b > 0 and col_loc == "Interior Column": ax.add_patch(patches.Rectangle((-c1_m/2, -L2_b - c2_m/2), c1_m, c2_m, **ghost_props))

    # 5. External Dimensions (Simplified for brevity in update, keep original logic)
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

    m_x, m_y = -slab_L - 0.8, -slab_B - 0.8
    if L1_l > 0 and col_loc != "Corner Column": draw_ext_dim(-L1_l, -slab_B, 0, -slab_B, f"L1(L)={L1_l:.2f}", m_y - (-slab_B))
    draw_ext_dim(0, -slab_B, L1_r, -slab_B, f"L1(R)={L1_r:.2f}", m_y - (-slab_B))
    draw_ext_dim(-slab_L, 0, -slab_L, L2_t, f"L2(T)={L2_t:.2f}", m_x - (-slab_L))
    if L2_b > 0 and col_loc == "Interior Column": draw_ext_dim(-slab_L, -L2_b, -slab_L, 0, f"L2(B)={L2_b:.2f}", m_x - (-slab_L))

    ax.set_title(f"STRUCTURAL LAYOUT: {col_loc.upper()}", fontsize=12, pad=20, fontweight='bold', color='#566573')
    ax.set_xlim(-slab_L - 2.0, slab_R + 1.0)
    ax.set_ylim(-slab_B - 2.0, slab_T + 1.0)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, is_roof):
    """
    High-fidelity Section View with Hatching, Break Lines, Side Dims, AND Joint Type Logic
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    s_m = h_slab_cm / 100
    d_m = h_drop_cm / 100 if has_drop else 0
    c_m = c1_cm / 100
    d_w = drop_w1 if has_drop else 0
    
    # View Settings
    view_width = 1.5
    view_top = 0.8 if not is_roof else 0.1 # Reduced top view if roof
    view_bot = -(s_m + d_m + 0.8)
    
    col_concrete = '#ECF0F1'
    col_hatch = '#BDC3C7'
    col_dim = '#2C3E50'
    
    # Helper: Side Dimension
    def draw_side_dim(y_start, y_end, x_loc, label, side='left'):
        ax.annotate('', xy=(x_loc, y_start), xytext=(x_loc, y_end),
                    arrowprops=dict(arrowstyle='<|-|>', color=col_dim, linewidth=0.8, shrinkA=0, shrinkB=0))
        ext_len = 0.1
        ax.plot([x_loc - ext_len/2, x_loc + ext_len/2], [y_start, y_start], color=col_dim, linewidth=0.6)
        ax.plot([x_loc - ext_len/2, x_loc + ext_len/2], [y_end, y_end], color=col_dim, linewidth=0.6)
        connect_x = -view_width if side == 'left' else c_m/2
        ax.plot([connect_x, x_loc], [y_start, y_start], color=col_dim, linestyle=':', linewidth=0.5, alpha=0.5)
        ax.plot([connect_x, x_loc], [y_end, y_end], color=col_dim, linestyle=':', linewidth=0.5, alpha=0.5)
        mid_y = (y_start + y_end) / 2
        text_offset = -0.15 if side == 'left' else 0.15
        ax.text(x_loc + text_offset, mid_y, label, ha='center', va='center', rotation=90, 
                fontsize=9, color=col_dim, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
    
    def draw_break(x, y, w):
        ax.plot([x-w/2, x-w/4, x+w/4, x+w/2], [y, y-0.05, y+0.05, y], color='black', linewidth=1)

    # 1. Structure
    # Column Upper (Only if not Roof)
    if not is_roof:
        ax.add_patch(patches.Rectangle((-c_m/2, 0), c_m, view_top, facecolor='white', edgecolor='black', linewidth=1))
        draw_break(0, view_top, c_m)
        
    # Column Lower
    bot_struct = -(s_m + d_m)
    ax.add_patch(patches.Rectangle((-c_m/2, view_bot), c_m, abs(view_bot - bot_struct), facecolor='white', edgecolor='black', linewidth=1))
    draw_break(0, view_bot, c_m)

    # Slab (Continuous)
    ax.add_patch(patches.Rectangle((-view_width, -s_m), view_width*2, s_m, facecolor=col_concrete, edgecolor='black', linewidth=1, zorder=5))
    ax.add_patch(patches.Rectangle((-view_width, -s_m), view_width*2, s_m, fill=False, edgecolor=col_hatch, hatch='///', linewidth=0, zorder=6))

    # Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w/2, bot_struct), d_w, d_m, facecolor=col_concrete, edgecolor='black', linewidth=1, zorder=5))
        ax.add_patch(patches.Rectangle((-d_w/2, bot_struct), d_w, d_m, fill=False, edgecolor=col_hatch, hatch='///', linewidth=0, zorder=6))

    # 2. Dimensions
    dim_x_left = -view_width - 0.5
    draw_side_dim(0, -s_m, dim_x_left, f"Slab {h_slab_cm} cm", side='left')
    if has_drop:
        draw_side_dim(-s_m, -(s_m+d_m), dim_x_left - 0.4, f"Drop {h_drop_cm} cm", side='left')

    dim_x_right = c_m/2 + 0.8
    if not is_roof:
        draw_side_dim(0, view_top, dim_x_right, f"Upper H. {h_up:.2f} m", side='right')
    
    draw_side_dim(-(s_m+d_m), view_bot, dim_x_right, f"Lower H. {h_lo:.2f} m", side='right')

    if has_drop:
        dim_y_bot = view_bot - 0.2
        ax.annotate('', xy=(-d_w/2, dim_y_bot), xytext=(d_w/2, dim_y_bot), arrowprops=dict(arrowstyle='<|-|>', color=col_dim, linewidth=0.8))
        ax.text(0, dim_y_bot - 0.15, f"Drop Width {drop_w1:.2f} m", ha='center', color=col_dim, fontsize=9)
        ax.plot([-d_w/2, -d_w/2], [-(s_m+d_m), dim_y_bot], linestyle=':', color='gray', linewidth=0.5)
        ax.plot([d_w/2, d_w/2], [-(s_m+d_m), dim_y_bot], linestyle=':', color='gray', linewidth=0.5)

    # T.O.S Marker
    ax.text(-view_width + 0.2, 0.05, "▼ T.O. Slab (+0.00)", color='blue', fontsize=8, fontweight='bold')
    ax.axhline(0, color='blue', linestyle='-.', linewidth=0.5, alpha=0.5)

    ax.set_aspect('equal')
    ax.set_xlim(-view_width - 1.2, view_width + 1.2)
    ax.set_ylim(view_bot - 0.5, view_top + 0.2)
    ax.axis('off')
    
    title_text = "SECTION DETAIL: INTERMEDIATE JOINT" if not is_roof else "SECTION DETAIL: ROOF JOINT"
    ax.set_title(title_text, fontsize=10, color='gray', pad=10, fontweight='bold')
    return fig

# ==============================================================================
# 5. MAIN APPLICATION INTERFACE
# ==============================================================================

st.title("🏗️ Flat Slab Design: Equivalent Frame Method (EFM)")
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
        st.subheader("1. Materials")
        c1_mat, c2_mat = st.columns(2)
        with c1_mat: fc = st.selectbox("Concrete f'c (ksc)", [240, 280, 320, 350, 400], index=1)
        with c2_mat: fy = st.selectbox("Steel Grade (fy)", ["SD30", "SD40", "SD50"], index=1)

        # 2. Loads
        st.subheader("2. Loads & Factors")
        lf_col1, lf_col2 = st.columns(2)
        with lf_col1: lf_dl = st.number_input("DL Factor", value=1.2, step=0.1, format="%.2f")
        with lf_col2: lf_ll = st.number_input("LL Factor", value=1.6, step=0.1, format="%.2f")
        
        auto_sw = st.checkbox("✅ Auto-calculate Self-weight (Concrete 2400 kg/m³)", value=True)
        dl_label = "Superimposed Dead Load (SDL) [kg/m²]" if auto_sw else "Total Dead Load (SW + SDL) [kg/m²]"
        dl = st.number_input(dl_label, value=100, step=10)
        ll = st.number_input("Live Load (LL) [kg/m²]", value=200, step=50)

        st.divider()

        # 3. Geometry (Updated with Joint Type)
        st.subheader("3. Geometry & Boundary")
        
        # --- NEW: Joint Type Selection ---
        st.markdown("##### 📍 Column Joint Condition")
        joint_type = st.radio(
            "Select Joint Type:",
            ("Intermediate Floor (Upper & Lower Columns)", "Roof Joint (Lower Column Only)"),
            help="Determines column stiffness contribution and moment distribution."
        )
        is_roof = "Roof" in joint_type
        joint_code = "Roof Joint" if is_roof else "Intermediate Joint"
        
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

        h_slab_cm = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0)
        col_sz1, col_sz2 = st.columns(2)
        with col_sz1: c1_cm = st.number_input("Column c1 (cm) [Analysis Dir]", value=50.0)
        with col_sz2: c2_cm = st.number_input("Column c2 (cm) [Transverse]", value=50.0)

        # Storey Heights (Conditioned)
        st.caption("Storey Heights")
        h_up = 0.0
        if not is_roof:
            h_up = st.number_input("Upper Storey Height (m)", value=3.0)
        else:
            st.info("ℹ️ Roof Joint: No Upper Column")
            
        h_lo = st.number_input("Lower Storey Height (m)", value=3.0)

        has_drop = st.checkbox("Include Drop Panel", value=False)
        h_drop_cm, drop_w1, drop_w2 = 0.0, 0.0, 0.0
        if has_drop:
            st.caption("Drop Panel Settings")
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1: h_drop_cm = st.number_input("Drop Depth (cm)", value=10.0)
            with d_col2: drop_w1 = st.number_input("Drop Width L1 (m)", value=2.5)
            with d_col3: drop_w2 = st.number_input("Drop Width L2 (m)", value=2.5)

        # --- Calculation & Validation ---
        calc_obj = prepare_calculation_data(
            h_slab_cm, h_drop_cm, has_drop, c1_cm, c2_cm, drop_w2,
            L1_l, L1_r, L2_t, L2_b, fc, fy, dl, ll, auto_sw, lf_dl, lf_ll,
            joint_code, h_up, h_lo
        )

        validator = DesignCriteriaValidator(
            calc_obj['geom']['L1'], calc_obj['geom']['L2'], L1_l, L1_r, L2_t, L2_b,
            ll, (calc_obj['loads']['w_dead'] / Units.G), has_drop
        )

        ddm_ok, ddm_reasons = validator.check_ddm()
        efm_ok, efm_reasons = validator.check_efm()
        drop_warnings = validator.check_drop_panel(h_slab_cm, h_drop_cm, drop_w1, drop_w2, L1_l, L1_r, L2_t, L2_b)

        # Sidebar Update
        with status_container:
            st.markdown(f"**Joint:** `{joint_code}`")
            if ddm_ok: st.success("✅ **DDM:** Valid")
            else: st.error("❌ **DDM:** Invalid")
            st.info("✅ **EFM:** Valid")

    with col_viz:
        st.subheader("👁️ Visualization & Analysis")
        v_tab1, v_tab2 = st.tabs(["📐 Plan View", "🔍 True-Scale Section"])
        
        with v_tab1:
            fig_plan = draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_location, has_drop, drop_w1, drop_w2)
            st.pyplot(fig_plan)
        
        with v_tab2:
            # Pass is_roof to visualization
            fig_elev = draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, is_roof)
            st.pyplot(fig_elev)
            
        # Analysis Report (Merged)
        st.markdown("### 📋 Analysis Results")
        
        st.markdown(f"""
        **Structure Behavior ({joint_code}):**
        - **Stiffness Source:** {calc_obj['concept']['rotation_resistance']}
        - **Moment Distribution:** {calc_obj['concept']['unbalanced_moment_dist']}
        """)
        
        if drop_warnings:
            st.warning("**⚠️ Drop Panel Geometry Warnings:**")
            for w in drop_warnings: st.write(f"- {w}")

        with st.expander(f"Direct Design Method (DDM) Criteria [{'PASS' if ddm_ok else 'FAIL'}]", expanded=not ddm_ok):
            for r in ddm_reasons: st.markdown(r)
            
        with st.expander("Equivalent Frame Method (EFM) Criteria", expanded=False):
            for r in efm_reasons: st.markdown(r)

        # Load Summary
        loads = calc_obj['loads']
        st.info(f"""
        **Design Load Summary:**
        - Total DL: `{loads['w_dead']/Units.G:.1f}` kg/m²
        - Live Load: `{loads['ll_pa']/Units.G:.1f}` kg/m²
        - **Factored Load ($w_u$):** `{loads['wu_pa']/Units.G:.1f}` kg/m²
        """)

with tab2:
    st.header("📘 Engineering Theory")
    st.markdown("""
    ### 1. Joint Behavior & Stiffness ($K_{ec}$)
    
    The behavior of the slab-column connection depends critically on the **Joint Type** selected:

    #### Case 1: Intermediate Joint (Floor Level)
    This joint occurs at intermediate floors where columns exist both above and below the slab.
    * **Stiffness ($K_{ec}$):** The joint is stiffened by both columns. 
        $$ K_{col} \approx K_{col\_top} + K_{col\_bot} $$
    * **Moment Transfer:** Unbalanced moments ($M_{unb}$) are distributed to both the upper and lower columns proportional to their stiffness.
    
    #### Case 2: Roof Joint (Top Level)
    This joint occurs at the roof where there is no column above.
    * **Stiffness ($K_{ec}$):** The joint relies solely on the column below.
        $$ K_{col} \approx K_{col\_bot} $$
    * **Moment Transfer:** All unbalanced moment must be resisted by the column below, often governing the design of the top-storey column.

    ---

    ### 2. Direct Design Method (DDM)
    Approximate method permissible if:
    - Minimum 3 continuous spans.
    - Rectangular panels with aspect ratio $\le 2.0$.
    - Successive span lengths differ by $\le 33\%$.
    - Unfactored LL/DL $\le 2.0$.

    ### 3. Equivalent Frame Method (EFM)
    - Represents the 3D slab system as a series of 2D frames.
    - Accounts for the stiffness of the slab, columns, and torsional members.
    - Applicable to irregular layouts and loading where DDM fails.
    """)
