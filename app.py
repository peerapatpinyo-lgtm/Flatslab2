import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design Pro", layout="wide")

# ==============================================================================
# ⚙️ UNIT CONVERSION & CONSTANTS (Global Settings)
# ==============================================================================
class Units:
    """
    คลาสสำหรับจัดการตัวคูณแปลงหน่วย (Conversion Factors)
    เป้าหมาย: แปลงทุก Input ให้เป็น SI Units (N, m, Pa) สำหรับการคำนวณภายใน
    """
    # Gravity
    G = 9.80665  # m/s^2

    # Length
    CM_TO_M = 0.01
    
    # Force
    KG_TO_N = G  # 1 kgf = 9.80665 N
    TON_TO_N = 1000 * G

    # Stress / Strength
    # 1 ksc (kg/cm^2) = 9.80665 N / 0.0001 m^2 = 98,066.5 Pa
    KSC_TO_PA = 98066.5 
    KSC_TO_MPA = 0.0980665

# ==============================================================================
# 🧱 ENGINEERING CALCULATIONS & VALIDATION
# ==============================================================================

def validate_aci_standard(h_slab, h_drop, L1_left, L1_right, L2_top, L2_bot, drop_w1, drop_w2, has_drop):
    """ตรวจสอบมาตรฐาน ACI 318 สำหรับความหนาและความกว้างของ Drop Panel"""
    warnings = []
    
    if has_drop:
        # 1. Thickness Check (min h/4)
        if h_drop < (h_slab / 4):
            warnings.append(f"⚠️ **Drop Thickness:** {h_drop} cm < เกณฑ์ขั้นต่ำ {h_slab/4:.2f} cm (h_slab/4)")
        
        # 2. Width Check (min L/6 from centerline)
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
    auto_sw, lf_dl, lf_ll  # <--- New Arguments for Load Management
):
    """
    แปลง User Input ทั้งหมดให้เป็น SI Units พร้อมจัดการ Load Logic
    """
    
    # --- 1. Geometry Normalization (cm -> m) ---
    h_s = h_slab_cm * Units.CM_TO_M
    h_d = (h_slab_cm + h_drop_cm) * Units.CM_TO_M if has_drop else h_s
    
    c1 = c1_cm * Units.CM_TO_M
    c2 = c2_cm * Units.CM_TO_M
    
    b_drop = drop_w2 if has_drop else 0.0

    L1 = L1_l + L1_r
    L2 = L2_t + L2_b
    Ln = L1 - c1
    
    # --- 2. Material Properties ---
    fc_mpa = fc_ksc * Units.KSC_TO_MPA
    fc_pa = fc_ksc * Units.KSC_TO_PA
    
    Ec_mpa = 4700 * np.sqrt(fc_mpa)
    Ec_pa = Ec_mpa * 1e6
    
    fy_ksc = 3000 if fy_grade == "SD30" else (4000 if fy_grade == "SD40" else 5000)
    fy_pa = fy_ksc * Units.KSC_TO_PA

    # --- 3. Load Logic (Enhanced) ---
    
    # 3.1 Self-weight Calculation
    density_conc_kg = 2400
    if auto_sw:
        # SW = thickness * density
        sw_pa = h_s * density_conc_kg * Units.G
    else:
        # User manual input (SW is assumed 0 here, user puts it in DL)
        sw_pa = 0.0
    
    # 3.2 Superimposed DL & LL
    sdl_pa = dl_kgm2 * Units.KG_TO_N
    ll_pa = ll_kgm2 * Units.KG_TO_N
    
    # 3.3 Factored Load (wu) with User defined Factors
    # wu = LF_DL * (SW + SDL) + LF_LL * (LL)
    wu_pa = (lf_dl * (sw_pa + sdl_pa)) + (lf_ll * ll_pa)

    # --- 4. Stiffness Parameters ---
    Ig_slab = (L2 * (h_s**3)) / 12
    Ig_drop = (b_drop * (h_d**3)) / 12 + ((L2 - b_drop) * (h_s**3)) / 12 if has_drop else Ig_slab

    return {
        "geom": {
            "L1": L1, "L2": L2, "Ln": Ln,
            "c1": c1, "c2": c2,
            "h_s": h_s, "h_d": h_d,
            "b_drop": b_drop
        },
        "mat": {
            "Ec_pa": Ec_pa, "fc_pa": fc_pa, "fy_pa": fy_pa
        },
        "loads": {
            "wu_pa": wu_pa,
            "sw_pa": sw_pa,
            "sdl_pa": sdl_pa,
            "ll_pa": ll_pa,
            "lf_dl": lf_dl,
            "lf_ll": lf_ll
        },
        "stiffness": {
            "Ig_slab": Ig_slab, "Ig_drop": Ig_drop
        }
    }

# ==============================================================================
# 🎨 VISUALIZATION SYSTEM (TRUE SCALE)
# ==============================================================================

def draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_loc, has_drop, d_w1, d_w2):
    """วาดรูปแปลนพื้น (Plan View)"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    c1_m = c1_cm / 100
    c2_m = c2_cm / 100
    
    slab_L = c1_m/2 if col_loc == "Corner Column" else L1_l
    slab_R = L1_r
    slab_T = L2_t
    slab_B = c2_m/2 if col_loc in ["Edge Column", "Corner Column"] else L2_b
    
    # Slab
    slab = patches.Rectangle((-slab_L, -slab_B), slab_L + slab_R, slab_B + slab_T,
                             facecolor='#f8f9fa', edgecolor='#2c3e50', linewidth=2, alpha=0.6, zorder=1)
    ax.add_patch(slab)

    # Column Strip Lines
    L_min = min((L1_l + L1_r), (L2_t + L2_b))
    cs_width = 0.25 * L_min
    cs_top = min(cs_width, slab_T)
    cs_bot = min(cs_width, slab_B)
    
    ax.axhline(y=cs_top, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.8, zorder=2)
    ax.axhline(y=-cs_bot, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.8, zorder=2)
    
    # Columns
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, facecolor='#34495e', hatch='///', zorder=10))
    
    neighbor_props = dict(facecolor='none', edgecolor='#bdc3c7', linestyle=':', linewidth=1, zorder=5)
    ax.add_patch(patches.Rectangle((L1_r - c1_m/2, -c2_m/2), c1_m, c2_m, **neighbor_props))
    if col_loc != "Corner Column":
        ax.add_patch(patches.Rectangle((-L1_l - c1_m/2, -c2_m/2), c1_m, c2_m, **neighbor_props))

    # Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w1/2, -d_w2/2), d_w1, d_w2, 
                                       facecolor='#f1c40f', edgecolor='#f39c12', alpha=0.5, zorder=8))

    # Annotations
    txt_style = dict(ha='center', va='center', fontsize=9, fontweight='bold', alpha=0.5)
    ax.text(slab_R/2, 0, "COLUMN STRIP", color='#27ae60', **txt_style)
    if slab_T > cs_top:
        ax.text(slab_R/2, cs_top + (slab_T-cs_top)/2, "MIDDLE STRIP", color='#2980b9', **txt_style)
    
    ax.set_title(f"Plan View: {col_loc}", fontsize=12, pad=20)
    ax.set_xlim(-slab_L - 1.0, slab_R + 1.0)
    ax.set_ylim(-slab_B - 1.0, slab_T + 1.0)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm):
    """
    วาดรูปตัด Elevation แบบ True Scale (1:1 Aspect Ratio)
    เพื่อให้ User เห็นความหนาจริงเทียบกับขนาดเสาและ Drop Panel
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # แปลงหน่วยเป็นเมตรทั้งหมด
    s_m = h_slab_cm / 100
    d_m = h_drop_cm / 100 if has_drop else 0
    c_m = c1_cm / 100
    d_w = drop_w1 if has_drop else 0
    
    # กำหนดขอบเขตการวาด (View Port) - ตัดมาดูเฉพาะช่วงหัวเสา +- 2.0 เมตร
    view_width = 2.0
    
    # 1. วาดเสา (Columns)
    # เสาล่าง (Lower Column) - วาดจาก -h_lo ถึงท้อง Drop/Slab
    bottom_of_structure = -(s_m + d_m)
    ax.add_patch(patches.Rectangle((-c_m/2, -h_lo + bottom_of_structure), c_m, h_lo, 
                                   color='#95a5a6', alpha=0.8, label='Column'))
    
    # เสาบน (Upper Column) - วาดจากหลังพื้น (0) ขึ้นไป
    ax.add_patch(patches.Rectangle((-c_m/2, 0), c_m, h_up, 
                                   color='#95a5a6', alpha=0.8))

    # 2. วาดพื้น (Slab) - ยึด Top of Slab = 0
    # วาดพื้นยาวตลอด View Port
    ax.add_patch(patches.Rectangle((-view_width, -s_m), view_width*2, s_m, 
                                   color='#bdc3c7', edgecolor='black', linewidth=1, label='Slab'))

    # 3. วาด Drop Panel
    if has_drop:
        # Drop Panel อยู่ใต้พื้น (เริ่มที่ -s_m ลงไป d_m)
        ax.add_patch(patches.Rectangle((-d_w/2, -(s_m + d_m)), d_w, d_m, 
                                       color='#f1c40f', edgecolor='#e67e22', linewidth=1, label='Drop Panel'))
        
        # Dimension Line for Drop Thickness
        ax.annotate(f"{h_drop_cm}cm", xy=(d_w/2 + 0.1, -(s_m + d_m/2)), 
                    xytext=(d_w/2 + 0.4, -(s_m + d_m/2)),
                    arrowprops=dict(arrowstyle="->", color='red'), fontsize=9, color='red', va='center')

    # Dimensions
    # Slab Thickness
    ax.annotate(f"Slab {h_slab_cm}cm", xy=(-view_width/2, -s_m/2), xytext=(-view_width/2 - 0.5, -s_m/2),
                arrowprops=dict(arrowstyle="->"), fontsize=9, va='center')

    # Center Line
    ax.axvline(0, color='black', linestyle='-.', linewidth=0.5, alpha=0.5)

    # Set Chart Properties
    ax.set_aspect('equal') # หัวใจสำคัญ: บังคับสัดส่วนจริง 1:1
    ax.set_xlim(-view_width, view_width)
    
    # Set Y-Limit to focus on the connection (not the whole column height)
    ax.set_ylim(-(s_m + d_m + 1.0), 1.0) 
    
    ax.axis('off')
    ax.set_title("True-Scale Elevation Detail (Section at Column)", fontsize=12)
    
    # Legend manually placed
    ax.text(0, 0.8, "Top of Slab (+0.00)", ha='center', fontsize=8, color='blue')
    
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

        # --- 2. LOADS (Updated Logic) ---
        st.subheader("2. Loads & Factors")
        
        # 2.1 Load Factors
        lf_col1, lf_col2 = st.columns(2)
        with lf_col1:
            lf_dl = st.number_input("DL Factor", value=1.2, step=0.1, format="%.2f")
        with lf_col2:
            lf_ll = st.number_input("LL Factor", value=1.6, step=0.1, format="%.2f")
            
        # 2.2 Load Values
        auto_sw = st.checkbox("✅ Auto-calculate Self-weight (Concrete 2400 kg/m³)", value=True)
        
        if auto_sw:
            st.info("ℹ️ Self-weight will be calculated based on Slab & Drop thickness.")
            dl_label = "Superimposed Dead Load (SDL) [kg/m²]"
        else:
            st.warning("⚠️ You must include Self-weight in the Dead Load below.")
            dl_label = "Total Dead Load (SW + SDL) [kg/m²]"
            
        dl = st.number_input(dl_label, value=100, step=10)
        ll = st.number_input("Live Load (LL) [kg/m²]", value=200, step=50)

        st.divider()

        # --- 3. GEOMETRY ---
        st.subheader("3. Geometry")
        
        # 3.1 Structure Layout
        col_location = st.selectbox("Column Location", ["Interior Column", "Edge Column", "Corner Column"])
        floor_scenario = st.selectbox("Floor Level", ["Typical Floor", "Top Floor (Roof)", "Foundation Level"])
        is_corner = (col_location == "Corner Column")
        is_edge = (col_location == "Edge Column")
        
        # 3.2 Spans
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

        # 3.3 Elements
        h_slab_cm = st.number_input("Slab Thickness (cm)", value=20.0, step=1.0)
        
        col_sz1, col_sz2 = st.columns(2)
        with col_sz1:
            c1_cm = st.number_input("Column c1 (cm) [Analysis Dir]", value=50.0)
        with col_sz2:
            c2_cm = st.number_input("Column c2 (cm) [Transverse]", value=50.0)

        # 3.4 Drop Panel
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
        
        # Validation
        warnings = validate_aci_standard(h_slab_cm, h_drop_cm, L1_l, L1_r, L2_t, L2_b, drop_w1, drop_w2, has_drop)
        for w in warnings:
            st.warning(w)

        # Heights
        h_up, h_lo = 0.0, 3.0
        if floor_scenario != "Top Floor (Roof)":
            h_up = st.number_input("Upper Storey Height (m)", value=3.0)
        h_lo = st.number_input("Lower Storey Height (m)", value=3.0)

        # --- CALL CALCULATION ENGINE ---
        calc_obj = prepare_calculation_data(
            h_slab_cm, h_drop_cm, has_drop,
            c1_cm, c2_cm, drop_w2,
            L1_l, L1_r, L2_t, L2_b,
            fc, fy_label, dl, ll,
            auto_sw, lf_dl, lf_ll  # <--- New Params Passed
        )

    with col_viz:
        st.subheader("👁️ Visualization & Analysis")
        v_tab1, v_tab2 = st.tabs(["📐 Plan View", "🔍 True-Scale Section"])
        
        with v_tab1:
            fig_plan = draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_location, has_drop, drop_w1, drop_w2)
            st.pyplot(fig_plan)
            
        with v_tab2:
            # ใช้ฟังก์ชันใหม่ True Scale
            fig_elev = draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm)
            st.pyplot(fig_elev)
            
        # Summary Box
        loads = calc_obj['loads']
        geom = calc_obj['geom']
        
        # Display Conversions
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
    ### 1. Data Processing Logic
    - **Unit Consistency:** All calculations are performed in SI Units (Pa, N, m) to ensure accuracy in Stiffness Matrix calculations.
    - **Load Factors:** User-defined load factors allow for flexibility (e.g., ACI 1.2D+1.6L or older 1.4D+1.7L).
    
    ### 2. Visualization
    - **True-Scale Section:** The Elevation view is rendered with a 1:1 aspect ratio. This allows engineers to visually verify the proportions of the Drop Panel depth relative to the Slab thickness, which is a critical constructability check.
    """)
