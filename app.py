import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design Pro", layout="wide")

# Set professional matplotlib style
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
    'drop_panel_plan': '#F39C12', # Orange for highlight
    'drop_panel_cut': '#9BA4B0', # Slightly darker concrete texture
    'dim_line': '#566573',
    'strip_line': '#3498DB', # Blue for strips
    'hatch_color': '#7F8C8D'
}

# ==============================================================================
# ⚙️ UNIT CONVERSION & CONSTANTS (Global Settings)
# ==============================================================================
class Units:
    G = 9.80665  # m/s^2
    CM_TO_M = 0.01
    KG_TO_N = G  # 1 kgf = 9.80665 N
    KSC_TO_PA = 98066.5 
    KSC_TO_MPA = 0.0980665

# ==============================================================================
# 🧱 ENGINEERING CALCULATIONS & VALIDATION
# ==============================================================================

def validate_aci_standard(h_slab, h_drop, L1_left, L1_right, L2_top, L2_bot, drop_w1, drop_w2, has_drop):
    """ตรวจสอบมาตรฐาน ACI 318 สำหรับความหนาและความกว้างของ Drop Panel"""
    warnings = []
    if has_drop:
        if h_drop < (h_slab / 4):
            warnings.append(f"⚠️ **Drop Thickness:** {h_drop} cm < เกณฑ์ขั้นต่ำ {h_slab/4:.2f} cm (h_slab/4)")
        
        max_L1 = max(L1_left, L1_right)
        max_L2 = max(L2_top, L2_bot)
        min_extend_L1 = max_L1 / 6
        min_extend_L2 = max_L2 / 6
        
        if (drop_w1 / 2) < min_extend_L1:
            warnings.append(f"⚠️ **Drop Width L1:** ระยะยื่น {drop_w1/2:.2f} m < เกณฑ์ {min_extend_L1:.2f} m (L1_max/6)")
        if (drop_w2 / 2) < min_extend_L2:
            warnings.append(f"⚠️ **Drop Width L2:** ระยะยื่น {drop_w2/2:.2f} m < เกณฑ์ {min_extend_L2:.2f} m (L2_max/6)")
    return warnings

# ==============================================================================
# 🧮 DATA NORMALIZATION ENGINE (SI UNITS)
# ==============================================================================

def prepare_calculation_data(
    h_slab_cm, h_drop_cm, has_drop, 
    c1_cm, c2_cm, drop_w2,
    L1_l, L1_r, L2_t, L2_b,
    fc_ksc, fy_grade, 
    dl_kgm2, ll_kgm2,
    auto_sw, lf_dl, lf_ll
):
    """
    แปลง User Input ทั้งหมดให้เป็น SI Units พร้อมจัดการ Load Logic
    """
    # Geometry
    h_s = h_slab_cm * Units.CM_TO_M
    h_d = (h_slab_cm + h_drop_cm) * Units.CM_TO_M if has_drop else h_s
    c1 = c1_cm * Units.CM_TO_M
    c2 = c2_cm * Units.CM_TO_M
    b_drop = drop_w2 if has_drop else 0.0
    L1 = L1_l + L1_r
    L2 = L2_t + L2_b
    Ln = L1 - c1
    
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
    wu_pa = (lf_dl * (sw_pa + sdl_pa)) + (lf_ll * ll_pa)

    # Stiffness Inertia
    Ig_slab = (L2 * (h_s**3)) / 12
    Ig_drop = (b_drop * (h_d**3)) / 12 + ((L2 - b_drop) * (h_s**3)) / 12 if has_drop else Ig_slab

    return {
        "geom": {"L1": L1, "L2": L2, "Ln": Ln, "c1": c1, "c2": c2, "h_s": h_s, "h_d": h_d, "b_drop": b_drop},
        "mat": {"Ec_pa": Ec_pa, "fc_pa": fc_pa, "fy_pa": fy_pa},
        "loads": {"wu_pa": wu_pa, "sw_pa": sw_pa, "sdl_pa": sdl_pa, "ll_pa": ll_pa, "lf_dl": lf_dl, "lf_ll": lf_ll},
        "stiffness": {"Ig_slab": Ig_slab, "Ig_drop": Ig_drop}
    }

# ==============================================================================
# 🎨 VISUALIZATION SYSTEM (PROFESSIONAL STYLE)
# ==============================================================================

def draw_dim_line(ax, start, end, text, offset=0.5, axis='x'):
    """Helper function for professional engineering dimension lines"""
    arrow_style = dict(arrowstyle='<|-|>', color=COLORS['dim_line'], linewidth=1.0, shrinkA=0, shrinkB=0)
    ext_line_style = dict(color=COLORS['dim_line'], linewidth=0.5, linestyle='-')
    
    if axis == 'x':
        # Dimension Line
        ax.annotate('', xy=(start[0], start[1]-offset), xytext=(end[0], end[1]-offset), arrowprops=arrow_style)
        # Extension Lines
        ax.plot([start[0], start[0]], [start[1]-0.1, start[1]-offset-0.2], **ext_line_style)
        ax.plot([end[0], end[0]], [end[1]-0.1, end[1]-offset-0.2], **ext_line_style)
        # Text
        ax.text((start[0]+end[0])/2, start[1]-offset-0.3, text, ha='center', va='top', color=COLORS['dim_line'])
    elif axis == 'y':
        # Dimension Line
        ax.annotate('', xy=(start[0]-offset, start[1]), xytext=(end[0]-offset, end[1]), arrowprops=arrow_style)
        # Extension Lines
        ax.plot([start[0]-0.1, start[0]-offset-0.2], [start[1], start[1]], **ext_line_style)
        ax.plot([end[0]-0.1, end[0]-offset-0.2], [end[1], end[1]], **ext_line_style)
        # Text
        ax.text(start[0]-offset-0.3, (start[1]+end[1])/2, text, ha='right', va='center', rotation=90, color=COLORS['dim_line'])

def draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_loc, has_drop, d_w1, d_w2):
    """วาดรูปแปลนพื้น (Professional Style)"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    c1_m = c1_cm / 100
    c2_m = c2_cm / 100
    
    slab_L = c1_m/2 if col_loc == "Corner Column" else L1_l
    slab_R = L1_r
    slab_T = L2_t
    slab_B = c2_m/2 if col_loc in ["Edge Column", "Corner Column"] else L2_b
    
    # 1. Slab (Concrete Base)
    slab = patches.Rectangle((-slab_L, -slab_B), slab_L + slab_R, slab_B + slab_T,
                             facecolor=COLORS['concrete_plan'], edgecolor=COLORS['dim_line'], linewidth=1, zorder=1)
    ax.add_patch(slab)

    # 2. Column Strips (Professional dashed lines)
    L_min = min((L1_l + L1_r), (L2_t + L2_b))
    cs_width = 0.25 * L_min
    cs_top = min(cs_width, slab_T)
    cs_bot = min(cs_width, slab_B)
    
    strip_style = dict(color=COLORS['strip_line'], linestyle=(0, (5, 5)), linewidth=1.0, alpha=0.7, zorder=2)
    ax.axhline(y=cs_top, **strip_style)
    ax.axhline(y=-cs_bot, **strip_style)
    
    # 3. Columns (Solid Supports)
    col_style = dict(facecolor=COLORS['column'], edgecolor='black', zorder=10)
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, **col_style))
    
    neighbor_style = dict(facecolor='none', edgecolor=COLORS['concrete_cut'], linestyle=':', linewidth=1, zorder=5)
    ax.add_patch(patches.Rectangle((L1_r - c1_m/2, -c2_m/2), c1_m, c2_m, **neighbor_style))
    if col_loc != "Corner Column":
        ax.add_patch(patches.Rectangle((-L1_l - c1_m/2, -c2_m/2), c1_m, c2_m, **neighbor_style))

    # 4. Drop Panel (Dashed line indicating below slab)
    if has_drop:
        # Use dashed orange line for drop panel below
        ax.add_patch(patches.Rectangle((-d_w1/2, -d_w2/2), d_w1, d_w2, 
                                       facecolor='none', edgecolor=COLORS['drop_panel_plan'], 
                                       linestyle='--', linewidth=2, zorder=8))
        ax.text(d_w1/2 + 0.2, -d_w2/2 + 0.2, "Drop Panel\n(Below)", color=COLORS['drop_panel_plan'], fontsize=8, ha='left')

    # 5. Annotations (Cleaner text)
    txt_style = dict(ha='center', va='center', fontsize=9, fontweight='bold', color=COLORS['strip_line'], alpha=0.8)
    ax.text(slab_R/2, 0, "COLUMN STRIP", **txt_style)
    if slab_T > cs_top:
        ax.text(slab_R/2, cs_top + (slab_T-cs_top)/2, "MIDDLE STRIP", **txt_style)
    
    # 6. Professional Dimensions
    # X-Axis
    if col_loc != "Corner Column":
        draw_dim_line(ax, (-slab_L, -slab_B), (0, -slab_B), f"{L1_l:.2f}m", offset=0.6, axis='x')
    draw_dim_line(ax, (0, -slab_B), (slab_R, -slab_B), f"{L1_r:.2f}m", offset=0.6, axis='x')
    
    # Y-Axis
    draw_dim_line(ax, (-slab_L, 0), (-slab_L, slab_T), f"{L2_t:.2f}m", offset=0.6, axis='y')
    if col_loc == "Interior Column":
        draw_dim_line(ax, (-slab_L, -slab_B), (-slab_L, 0), f"{L2_b:.2f}m", offset=0.6, axis='y')

    # Centerlines
    ax.axhline(0, color=COLORS['dim_line'], linestyle='-.', linewidth=0.5)
    ax.axvline(0, color=COLORS['dim_line'], linestyle='-.', linewidth=0.5)

    ax.set_title(f"Structural Plan View: {col_loc}", pad=20)
    ax.set_xlim(-slab_L - 1.5, slab_R + 1.5)
    ax.set_ylim(-slab_B - 1.5, slab_T + 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm):
    """
    วาดรูปตัด Elevation แบบ True Scale (Professional Style with Hatching)
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    s_m = h_slab_cm / 100
    d_m = h_drop_cm / 100 if has_drop else 0
    c_m = c1_cm / 100
    d_w = drop_w1 if has_drop else 0
    view_width = 2.0
    
    # Concrete Hatch Style
    hatch_style = {'hatch': '///', 'edgecolor': COLORS['hatch_color'], 'linewidth': 0.5}

    # 1. Columns (Solid support, lighter color)
    col_props = dict(facecolor=COLORS['concrete_plan'], edgecolor=COLORS['dim_line'], linewidth=1, zorder=1)
    bottom_of_structure = -(s_m + d_m)
    # Lower Column
    ax.add_patch(patches.Rectangle((-c_m/2, -h_lo + bottom_of_structure), c_m, h_lo, **col_props))
    # Upper Column
    ax.add_patch(patches.Rectangle((-c_m/2, 0), c_m, h_up, **col_props))

    # 2. Slab (Cut section with hatching)
    slab_cut = patches.Rectangle((-view_width, -s_m), view_width*2, s_m, 
                                 facecolor=COLORS['concrete_cut'], edgecolor='black', linewidth=1.2, zorder=5, **hatch_style)
    ax.add_patch(slab_cut)

    # 3. Drop Panel (Cut section with hatching, same material)
    if has_drop:
        drop_cut = patches.Rectangle((-d_w/2, -(s_m + d_m)), d_w, d_m, 
                                     facecolor=COLORS['concrete_cut'], edgecolor='black', linewidth=1.2, zorder=5, **hatch_style)
        ax.add_patch(drop_cut)
        
        # Professional Dim for Drop
        draw_dim_line(ax, (d_w/2, -s_m), (d_w/2, -(s_m+d_m)), f"Drop {h_drop_cm}cm", offset=-0.4, axis='y')

    # 4. Dimensions & Annotations
    # Slab Thickness
    draw_dim_line(ax, (-view_width/2, 0), (-view_width/2, -s_m), f"Slab {h_slab_cm}cm", offset=0.5, axis='y')

    # Center Line
    ax.axvline(0, color=COLORS['dim_line'], linestyle='-.', linewidth=0.8, alpha=0.7)

    # Level Marker (Professional Style)
    ax.annotate('▼ T.O. Slab (+0.00m)', xy=(0.1, 0), xytext=(0.4, 0.2),
                arrowprops=dict(arrowstyle='->', color=COLORS['dim_line']),
                fontsize=9, color=COLORS['column'], fontweight='bold')

    # View Settings
    ax.set_aspect('equal')
    ax.set_xlim(-view_width, view_width)
    ax.set_ylim(-(s_m + d_m + 0.8), 0.8)
    ax.axis('off')
    ax.set_title("True-Scale Section at Support A-A", pad=15)
    
    return fig

# ==============================================================================
# 🚀 MAIN APPLICATION INTERFACE
# ==============================================================================

st.title("🏗️ Flat Slab Design: Equivalent Frame Method (EFM)")
st.markdown("---")

if 'col_loc' not in st.session_state:
    st.session_state['col_loc'] = "Interior Column"

tab1, tab2 = st.tabs(["📝 Input Parameters", "📘 Engineering Theory"])

with tab1:
    col_input, col_viz = st.columns([1.2, 1.4])

    with col_input:
        # --- 1. MATERIALS ---
        st.subheader("1. Materials")
        c1_mat, c2_mat = st.columns(2)
        with c1_mat:
            fc = st.selectbox("Concrete Strength f'c (ksc)", options=[240, 280, 320, 350, 400], index=1)
        with c2_mat:
            fy_label = st.selectbox("Steel Grade (fy)", options=["SD30", "SD40", "SD50"], index=1)

        # --- 2. LOADS ---
        st.subheader("2. Loads & Factors")
        lf_col1, lf_col2 = st.columns(2)
        with lf_col1:
            lf_dl = st.number_input("DL Factor", value=1.2, step=0.1, format="%.2f")
        with lf_col2:
            lf_ll = st.number_input("LL Factor", value=1.6, step=0.1, format="%.2f")
            
        auto_sw = st.checkbox("✅ Auto-calculate Self-weight (Concrete 2400 kg/m³)", value=True)
        dl_label = "Superimposed Dead Load (SDL) [kg/m²]" if auto_sw else "Total Dead Load (SW + SDL) [kg/m²]"
        dl = st.number_input(dl_label, value=100, step=10)
        ll = st.number_input("Live Load (LL) [kg/m²]", value=200, step=50)

        st.divider()

        # --- 3. GEOMETRY ---
        st.subheader("3. Geometry")
        col_location = st.selectbox("Column Location", ["Interior Column", "Edge Column", "Corner Column"])
        floor_scenario = st.selectbox("Floor Level", ["Typical Floor", "Top Floor (Roof)", "Foundation Level"])
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
        with col_sz1:
            c1_cm = st.number_input("Column c1 (cm) [Analysis Dir]", value=50.0)
        with col_sz2:
            c2_cm = st.number_input("Column c2 (cm) [Transverse]", value=50.0)

        has_drop = st.checkbox("Include Drop Panel", value=False)
        h_drop_cm, drop_w1, drop_w2 = 0.0, 0.0, 0.0
        if has_drop:
            st.caption("Drop Panel Settings")
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                h_drop_cm = st.number_input("Drop Depth (cm)", value=10.0, help="Measured from slab bottom")
            with d_col2:
                drop_w1 = st.number_input("Drop Width L1 (m)", value=2.5)
            with d_col3:
                drop_w2 = st.number_input("Drop Width L2 (m)", value=2.5)
        
        warnings = validate_aci_standard(h_slab_cm, h_drop_cm, L1_l, L1_r, L2_t, L2_b, drop_w1, drop_w2, has_drop)
        for w in warnings:
            st.warning(w)

        h_up, h_lo = 0.0, 3.0
        if floor_scenario != "Top Floor (Roof)":
            h_up = st.number_input("Upper Storey Height (m)", value=3.0)
        h_lo = st.number_input("Lower Storey Height (m)", value=3.0)

        # --- CALL ENGINE ---
        calc_obj = prepare_calculation_data(
            h_slab_cm, h_drop_cm, has_drop, c1_cm, c2_cm, drop_w2,
            L1_l, L1_r, L2_t, L2_b, fc, fy_label, dl, ll, auto_sw, lf_dl, lf_ll
        )

    with col_viz:
        st.subheader("👁️ Visualization & Analysis")
        v_tab1, v_tab2 = st.tabs(["📐 Plan View", "🔍 True-Scale Section"])
        
        with v_tab1:
            fig_plan = draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_location, has_drop, drop_w1, drop_w2)
            st.pyplot(fig_plan)
            
        with v_tab2:
            fig_elev = draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm)
            st.pyplot(fig_elev)
            
        # Summary Box
        loads = calc_obj['loads']
        geom = calc_obj['geom']
        sw_disp = loads['sw_pa'] / Units.G
        sdl_disp = loads['sdl_pa'] / Units.G
        ll_disp = loads['ll_pa'] / Units.G
        wu_disp = loads['wu_pa'] / Units.G
        total_ton = (loads['wu_pa'] * geom['L1'] * geom['L2']) / (1000 * Units.G)

        st.success(f"""
        **📋 Design Load Summary (Strip Basis):**
        
        **1. Loads Breakdown:**
        - Self-weight (SW): `{sw_disp:.1f}` kg/m² ({'Auto' if auto_sw else 'Manual'})
        - Superimposed DL: `{sdl_disp:.1f}` kg/m²
        - Live Load (LL): `{ll_disp:.1f}` kg/m²
        
        **2. Factored Load Combination:**
        $$w_u = {loads['lf_dl']}({sw_disp:.0f} + {sdl_disp:.0f}) + {loads['lf_ll']}({ll_disp:.0f})$$
        - **Design Pressure ($w_u$):** `{wu_disp:.1f}` kg/m²
        
        **3. Total Force on Strip:**
        - Strip Size: {geom['L1']:.2f} m x {geom['L2']:.2f} m
        - **Total Factored Load ($W_u$):** `{total_ton:.2f}` Tons
        """)

with tab2:
    st.header("📘 Equivalent Frame Method (EFM) Theory")
    st.markdown("""
    ### Professional Visualization Notes
    - **Plan View:** Shows the structural layout with standard engineering conventions. Dashed orange lines indicate drop panels located below the slab. Column strips are marked with professional dashed blue lines.
    - **True-Scale Section:** Renders a cross-section at the support with a 1:1 aspect ratio. Concrete elements (slab and drop panel) are hatched to indicate section cuts, providing a clear visual check of proportions and constructability. Level markers (e.g., T.O. Slab) are included.
    """)
