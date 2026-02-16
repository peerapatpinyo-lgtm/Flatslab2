import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==============================================================================
# 1. SETUP & CONFIGURATION (Global Settings)
# ==============================================================================
st.set_page_config(page_title="Flat Slab Design Pro", layout="wide")

# Professional Plotting Style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
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

# Color Palette (Engineering Standard)
COLORS = {
    'concrete': '#F0F2F5',
    'concrete_cut': '#E5E7E9',
    'column': '#2C3E50',
    'dim_line': '#566573',
    'highlight': '#E74C3C',    # Red for errors/warnings
    'pass': '#27AE60',         # Green for pass
    'drop_panel': '#F39C12',
    'text_main': '#17202A'
}

# ==============================================================================
# 2. ENGINEERING CONSTANTS & UTILITIES
# ==============================================================================
class Units:
    G = 9.80665
    CM_TO_M = 0.01
    KG_TO_N = G
    KSC_TO_PA = 98066.5
    KSC_TO_MPA = 0.0980665

# ==============================================================================
# 3. CRITERIA CHECK ENGINE (ACI 318 Logic)
# ==============================================================================
class DesignCriteriaValidator:
    """
    คลาสสำหรับตรวจสอบเงื่อนไขการออกแบบตามมาตรฐาน ACI 318
    แยกตรวจสอบระหว่าง DDM และ EFM
    """
    def __init__(self, L1, L2, L1_l, L1_r, L2_t, L2_b, ll, dl, has_drop):
        self.L1 = L1  # Total L1 (Analysis Direction)
        self.L2 = L2  # Total L2 (Transverse)
        self.L1_spans = [l for l in [L1_l, L1_r] if l > 0] # Filter 0 out (corner/edge)
        self.L2_spans = [l for l in [L2_t, L2_b] if l > 0]
        self.ll = ll
        self.dl = dl
        self.has_drop = has_drop

    def check_ddm(self):
        """ตรวจสอบเงื่อนไข Direct Design Method (DDM)"""
        status = True
        reasons = []

        # 1. เช็ค Rectangular Ratio (L_long / L_short <= 2.0)
        long_side = max(self.L1, self.L2)
        short_side = min(self.L1, self.L2)
        ratio = long_side / short_side if short_side > 0 else 0
        
        if ratio > 2.0:
            status = False
            reasons.append(f"❌ **Panel Ratio:** อัตราส่วนด้านยาว/สั้น ({ratio:.2f}) > 2.0 (ACI 318 Limit)")
        else:
            reasons.append(f"✅ **Panel Ratio:** {ratio:.2f} <= 2.0 (Pass)")

        # 2. เช็ค Load Ratio (LL/DL <= 2.0)
        load_ratio = self.ll / self.dl if self.dl > 0 else 0
        if load_ratio > 2.0:
            status = False
            reasons.append(f"❌ **Load Ratio:** Live Load / Dead Load ({load_ratio:.2f}) > 2.0")
        else:
            reasons.append(f"✅ **Load Ratio:** {load_ratio:.2f} <= 2.0 (Pass)")

        # 3. เช็คความต่างของช่วงเสา (Successive Span Length)
        # Note: เช็คจาก L1_left และ L1_right (ถ้ามีทั้งคู่)
        if len(self.L1_spans) == 2:
            l_max = max(self.L1_spans)
            l_min = min(self.L1_spans)
            diff_ratio = (l_max - l_min) / l_max
            if diff_ratio > 0.33:
                status = False
                reasons.append(f"❌ **Span Difference:** ความยาวช่วงเสาต่างกัน {diff_ratio*100:.1f}% > 33%")
            else:
                reasons.append(f"✅ **Span Difference:** ช่วงเสาใกล้เคียงกัน (Diff {diff_ratio*100:.1f}%)")
        
        # 4. General Warning for 3 Spans (Limitations of Single Strip Input)
        reasons.append("ℹ️ **Note:** DDM ต้องการช่วงเสาต่อเนื่องอย่างน้อย 3 ช่วงในแต่ละทิศทาง (โปรดตรวจสอบภาพรวมอาคาร)")

        return status, reasons

    def check_efm(self):
        """ตรวจสอบเงื่อนไข Equivalent Frame Method (EFM)"""
        # EFM ยืดหยุ่นกว่า DDM มาก ใช้ได้เกือบทุกกรณีถ้ายอมรับสมมติฐานการวิเคราะห์ได้
        status = True
        reasons = []
        
        reasons.append("✅ **General:** EFM สามารถใช้ได้ทั่วไป แม้โครงสร้างจะไม่เป็นสี่เหลี่ยมผืนผ้าสมบูรณ์")
        reasons.append("✅ **Loads:** ไม่จำกัดอัตราส่วน LL/DL เหมือน DDM")
        
        return status, reasons

    def check_drop_panel_geometry(self, h_slab, h_drop, drop_w1, drop_w2, L1_l, L1_r, L2_t, L2_b):
        """ตรวจสอบขนาด Drop Panel ตาม ACI"""
        warnings = []
        if not self.has_drop:
            return warnings

        # ความหนา Drop
        min_h_drop = h_slab / 4
        if h_drop < min_h_drop:
            warnings.append(f"⚠️ **Drop Thickness:** {h_drop} cm < ขั้นต่ำ {min_h_drop:.2f} cm (t_slab/4)")

        # ระยะยื่น (Projection)
        # เช็ค L1 Direction
        max_L1 = max(L1_l, L1_r) if (L1_l + L1_r) > 0 else 1.0
        req_proj_L1 = max_L1 / 6
        if (drop_w1 / 2) < req_proj_L1:
            warnings.append(f"⚠️ **Drop Width L1:** ระยะยื่น {drop_w1/2:.2f} m < ขั้นต่ำ {req_proj_L1:.2f} m (L1/6)")

        # เช็ค L2 Direction
        max_L2 = max(L2_t, L2_b) if (L2_t + L2_b) > 0 else 1.0
        req_proj_L2 = max_L2 / 6
        if (drop_w2 / 2) < req_proj_L2:
            warnings.append(f"⚠️ **Drop Width L2:** ระยะยื่น {drop_w2/2:.2f} m < ขั้นต่ำ {req_proj_L2:.2f} m (L2/6)")
            
        return warnings

# ==============================================================================
# 4. CALCULATION ENGINE (Preparation)
# ==============================================================================
def prepare_data(
    h_slab_cm, h_drop_cm, has_drop, 
    c1_cm, c2_cm, drop_w2,
    L1_l, L1_r, L2_t, L2_b,
    fc_ksc, fy_grade, 
    dl_kgm2, ll_kgm2,
    auto_sw, lf_dl, lf_ll
):
    # Geometry Conversion
    h_s = h_slab_cm * Units.CM_TO_M
    h_d = (h_slab_cm + h_drop_cm) * Units.CM_TO_M if has_drop else h_s
    c1 = c1_cm * Units.CM_TO_M
    c2 = c2_cm * Units.CM_TO_M
    b_drop = drop_w2 if has_drop else 0.0
    L1 = L1_l + L1_r
    L2 = L2_t + L2_b
    Ln = L1 - c1
    
    # Material
    fc_pa = fc_ksc * Units.KSC_TO_PA
    Ec_pa = (4700 * np.sqrt(fc_ksc * Units.KSC_TO_MPA)) * 1e6
    fy_ksc = 3000 if fy_grade == "SD30" else (4000 if fy_grade == "SD40" else 5000)
    
    # Load Calculation
    density_conc = 2400 # kg/m3
    sw_pa = h_s * density_conc * Units.G if auto_sw else 0.0
    sdl_pa = dl_kgm2 * Units.KG_TO_N
    ll_pa = ll_kgm2 * Units.KG_TO_N
    
    w_dead_pa = sw_pa + sdl_pa
    wu_pa = (lf_dl * w_dead_pa) + (lf_ll * ll_pa)
    
    # Stiffness Prep (Inertia)
    Ig_slab = (L2 * (h_s**3)) / 12
    # Simple Gross Inertia approximation for display
    Ig_drop = (b_drop*(h_d**3))/12 + ((L2-b_drop)*(h_s**3))/12 if has_drop else Ig_slab

    return {
        "geom": {"L1": L1, "L2": L2, "Ln": Ln, "h_s": h_s},
        "load": {"sw": sw_pa, "sdl": sdl_pa, "ll": ll_pa, "wu": wu_pa, "w_dead": w_dead_pa},
        "mat": {"fc": fc_pa, "Ec": Ec_pa, "fy": fy_ksc},
        "raw": {"dl_kgm2": dl_kgm2, "ll_kgm2": ll_kgm2} # store for validator
    }

# ==============================================================================
# 5. VISUALIZATION ENGINE (Professional Drawings)
# ==============================================================================

def draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_loc, has_drop, d_w1, d_w2):
    """ Plan View with Column Strip / Middle Strip Labeling """
    fig, ax = plt.subplots(figsize=(12, 10))
    
    c1_m = c1_cm / 100
    c2_m = c2_cm / 100
    
    # Boundaries
    slab_L = c1_m/2 if col_loc == "Corner Column" else L1_l
    slab_R = L1_r
    slab_T = L2_t
    slab_B = c2_m/2 if col_loc in ["Edge Column", "Corner Column"] else L2_b
    
    # 1. Base Layer (Middle Strip)
    ax.add_patch(patches.Rectangle((-slab_L, -slab_B), slab_L + slab_R, slab_B + slab_T,
                                   facecolor='white', edgecolor='gray', linewidth=1))
    
    # 2. Column Strip Layer
    min_span = min(L1_l + L1_r, L2_t + L2_b)
    cs_width = 0.25 * min_span
    cs_top = min(cs_width, slab_T)
    cs_bot = min(cs_width, slab_B)
    
    # Draw CS Rect (Light Blue Area)
    ax.add_patch(patches.Rectangle((-slab_L, -cs_bot), slab_L + slab_R, cs_top + cs_bot,
                                   facecolor='#D6EAF8', edgecolor='none', alpha=0.5))
    
    # Strip Labels
    ax.text(slab_R * 0.6, 0, "COLUMN STRIP", color='#2874A6', fontweight='bold', ha='center', va='center', fontsize=10)
    if cs_top < slab_T:
        ax.text(slab_R * 0.6, (cs_top + slab_T)/2, "MIDDLE STRIP", color='gray', ha='center', va='center', fontsize=9)
    if cs_bot < slab_B:
        ax.text(slab_R * 0.6, -(cs_bot + slab_B)/2, "MIDDLE STRIP", color='gray', ha='center', va='center', fontsize=9)

    # 3. Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w1/2, -d_w2/2), d_w1, d_w2, 
                                       facecolor='none', edgecolor=COLORS['drop_panel'], 
                                       linestyle='--', linewidth=1.5))
        # Drop Dims
        ax.text(d_w1/2, -d_w2/2 - 0.2, f"Drop {d_w1:.2f}x{d_w2:.2f}m", color=COLORS['drop_panel'], ha='center', fontsize=8)

    # 4. Columns
    # Center Column
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                   facecolor=COLORS['column'], edgecolor='black', hatch='//'))
    
    # Ghost Columns (Context)
    ghost_props = dict(facecolor='white', edgecolor='gray', linestyle=':', linewidth=1)
    if L1_r > 0: ax.add_patch(patches.Rectangle((L1_r - c1_m/2, -c2_m/2), c1_m, c2_m, **ghost_props))
    if L1_l > 0 and col_loc != "Corner Column": ax.add_patch(patches.Rectangle((-L1_l - c1_m/2, -c2_m/2), c1_m, c2_m, **ghost_props))
    
    # 5. Dimensions
    def draw_dim(x1, y1, x2, y2, text, offset=0.5):
        ax.annotate('', xy=(x1, y1+offset), xytext=(x2, y2+offset),
                    arrowprops=dict(arrowstyle='<|-|>', color=COLORS['dim_line'], lw=0.8))
        ax.text((x1+x2)/2, y1+offset+0.1, text, ha='center', va='bottom', color=COLORS['dim_line'], fontweight='bold')
        
    draw_dim(0, -slab_B, L1_r, -slab_B, f"L1(R)={L1_r:.2f}m", offset=-0.5)
    if L1_l > 0 and col_loc != "Corner Column":
        draw_dim(-L1_l, -slab_B, 0, -slab_B, f"L1(L)={L1_l:.2f}m", offset=-0.5)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"STRUCTURAL LAYOUT: {col_loc.upper()}", pad=15, fontweight='bold')
    return fig

def draw_elevation_view(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm):
    """ Section View (True Scale) with Side Dimensions """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    s_m = h_slab_cm / 100
    d_m = h_drop_cm / 100 if has_drop else 0
    c_m = c1_cm / 100
    d_w = drop_w1 if has_drop else 0
    
    view_w = 1.5
    
    # 1. Structure
    # Column
    ax.add_patch(patches.Rectangle((-c_m/2, -3.5), c_m, 4.5, facecolor='white', edgecolor='black'))
    
    # Slab
    ax.add_patch(patches.Rectangle((-view_w, -s_m), view_w*2, s_m, 
                                   facecolor=COLORS['concrete_cut'], edgecolor='black', hatch='///'))
    
    # Drop
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w/2, -(s_m+d_m)), d_w, d_m, 
                                       facecolor=COLORS['concrete_cut'], edgecolor='black', hatch='///'))

    # 2. Dimensions (Side)
    def draw_side_dim(y1, y2, x_pos, text):
        ax.annotate('', xy=(x_pos, y1), xytext=(x_pos, y2),
                    arrowprops=dict(arrowstyle='<|-|>', color=COLORS['dim_line']))
        ax.plot([x_pos-0.05, x_pos+0.05], [y1, y1], color=COLORS['dim_line']) # Tick
        ax.plot([x_pos-0.05, x_pos+0.05], [y2, y2], color=COLORS['dim_line']) # Tick
        ax.text(x_pos+0.1, (y1+y2)/2, text, rotation=90, va='center', color=COLORS['dim_line'])

    # Height Dims
    draw_side_dim(0, 1.0, c_m/2 + 0.5, f"Upper")
    draw_side_dim(-(s_m+d_m), -2.0, c_m/2 + 0.5, f"Lower")
    
    # Thickness Dims (Left)
    draw_side_dim(0, -s_m, -view_w - 0.3, f"Slab {h_slab_cm}cm")
    if has_drop:
        draw_side_dim(-s_m, -(s_m+d_m), -view_w - 0.3, f"Drop {h_drop_cm}cm")

    # Center Line
    ax.axhline(0, color='blue', linestyle='-.', lw=0.5, label='T.O.Slab')
    ax.text(-view_w, 0.05, "▼ T.O.S (+0.00)", color='blue', fontsize=8)

    ax.set_xlim(-view_w - 1, view_w + 1)
    ax.set_ylim(-2.5, 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("SECTION DETAIL A-A", pad=10, fontweight='bold')
    return fig

# ==============================================================================
# 6. MAIN APPLICATION UI
# ==============================================================================
st.title("🏗️ Flat Slab Design: EFM & DDM Analysis")
st.markdown("---")

# Session State for future expansion
if 'col_loc' not in st.session_state: st.session_state['col_loc'] = "Interior Column"

# --- SIDEBAR: METHOD ASSESSMENT REPORT (NEW FEATURE) ---
st.sidebar.header("📊 Method Eligibility Report")
st.sidebar.markdown("ผลการประเมินเบื้องต้นจาก Input ปัจจุบัน:")

# Placeholder for dynamic status
status_container = st.sidebar.container()

# --- MAIN INPUT AREA ---
tab1, tab2 = st.tabs(["📝 Input Parameters & Criteria Check", "📘 Engineering Theory"])

with tab1:
    col_input, col_viz = st.columns([1.2, 1.4])
    
    with col_input:
        st.subheader("1. Project & Materials")
        c1, c2 = st.columns(2)
        with c1: fc = st.selectbox("Concrete f'c (ksc)", [240, 280, 320, 350, 400], index=1)
        with c2: fy = st.selectbox("Rebar fy", ["SD30", "SD40", "SD50"], index=1)
        
        st.subheader("2. Loading Condition")
        l1, l2 = st.columns(2)
        with l1: lf_dl = st.number_input("DL Factor", 1.2, 1.6, 1.4, 0.1)
        with l2: lf_ll = st.number_input("LL Factor", 1.6, 2.0, 1.7, 0.1)
        
        auto_sw = st.checkbox("Include Self-Weight automatically", True)
        dl_label = "Superimposed DL (SDL) [kg/m²]" if auto_sw else "Total Dead Load [kg/m²]"
        dl_val = st.number_input(dl_label, value=100.0)
        ll_val = st.number_input("Live Load (LL) [kg/m²]", value=200.0)
        
        st.divider()
        
        st.subheader("3. Geometry & Dimensions")
        col_location = st.selectbox("Column Strip Location", ["Interior Column", "Edge Column", "Corner Column"])
        is_corner = (col_location == "Corner Column")
        
        # Span Inputs
        sp1, sp2 = st.columns(2)
        with sp1: 
            L1_l = st.number_input("Span L1 Left (m)", value=0.0 if is_corner else 5.0, disabled=is_corner)
        with sp2: 
            L1_r = st.number_input("Span L1 Right (m)", value=5.0)
            
        sp3, sp4 = st.columns(2)
        with sp3: L2_t = st.number_input("Span L2 Top (m)", value=4.0)
        with sp4: L2_b = st.number_input("Span L2 Bottom (m)", value=4.0)
        
        # Member Sizes
        h_slab = st.number_input("Slab Thickness (cm)", value=20.0)
        cz1, cz2 = st.columns(2)
        with cz1: c1_size = st.number_input("Col c1 (Analysis Dir.) [cm]", value=50.0)
        with cz2: c2_size = st.number_input("Col c2 (Transverse) [cm]", value=50.0)
        
        # Drop Panel
        has_drop = st.checkbox("Add Drop Panel", False)
        h_drop, dw1, dw2 = 0.0, 0.0, 0.0
        if has_drop:
            dp1, dp2, dp3 = st.columns(3)
            with dp1: h_drop = st.number_input("Drop Depth (cm)", value=10.0)
            with dp2: dw1 = st.number_input("Drop Width L1 (m)", value=2.5)
            with dp3: dw2 = st.number_input("Drop Width L2 (m)", value=2.5)

        # Storey Height
        h_story = st.number_input("Storey Height (m)", value=3.0)

        # --- RUN VALIDATION & CALCULATIONS ---
        # 1. Prepare Data
        data = prepare_data(
            h_slab, h_drop, has_drop, c1_size, c2_size, dw2,
            L1_l, L1_r, L2_t, L2_b, fc, fy, dl_val, ll_val, auto_sw, lf_dl, lf_ll
        )
        
        # 2. Run Criteria Checks (THE NEW PART)
        validator = DesignCriteriaValidator(
            data['geom']['L1'], data['geom']['L2'], 
            L1_l, L1_r, L2_t, L2_b,
            data['raw']['ll_kgm2'], 
            (data['load']['sw'] + data['load']['sdl'])/Units.G, # Total DL for ratio check
            has_drop
        )
        
        ddm_ok, ddm_reasons = validator.check_ddm()
        efm_ok, efm_reasons = validator.check_efm()
        drop_warnings = validator.check_drop_panel_geometry(h_slab, h_drop, dw1, dw2, L1_l, L1_r, L2_t, L2_b)

        # 3. Update Sidebar with Results
        with status_container:
            # DDM Status
            if ddm_ok:
                st.success("✅ **DDM:** สามารถใช้วิธี DDM ได้")
            else:
                st.error("❌ **DDM:** ไม่แนะนำให้ใช้ (ดูรายละเอียด)")
            
            # EFM Status
            st.info("✅ **EFM:** แนะนำให้ใช้ (ครอบคลุมกว่า)")

    # --- VISUALIZATION & DETAILED CHECK RESULTS ---
    with col_viz:
        st.subheader("👁️ Geometry Visualization")
        
        # Tabs for Visuals
        v1, v2 = st.tabs(["Plan View", "Section View"])
        with v1:
            st.pyplot(draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_size, c2_size, col_location, has_drop, dw1, dw2))
        with v2:
            st.pyplot(draw_elevation_view(h_story, h_story, has_drop, h_drop, dw1, c1_size, h_slab))

        # --- CRITERIA DETAIL BOX (IMPORTANT UPDATE) ---
        st.markdown("### 📋 Design Criteria Assessment")
        
        # Drop Panel Warnings
        if drop_warnings:
            st.warning("⚠️ **Drop Panel Geometry Issues:**")
            for w in drop_warnings: st.write(f"- {w}")
        
        # Method Expanders
        with st.expander(f"Direct Design Method (DDM) Criteria [{'PASS' if ddm_ok else 'FAIL'}]", expanded=not ddm_ok):
            for r in ddm_reasons:
                st.markdown(r)
        
        with st.expander("Equivalent Frame Method (EFM) Criteria [PASS]", expanded=False):
            for r in efm_reasons:
                st.markdown(r)
                
        # Load Summary
        st.info(f"""
        **Load Summary:**
        - $w_{{DL}} = {(data['load']['w_dead']/Units.G):.1f}$ kg/m²
        - $w_{{LL}} = {(data['load']['ll']/Units.G):.1f}$ kg/m²
        - **Design Load ($w_u$): {(data['load']['wu']/Units.G):.1f} kg/m²**
        """)

with tab2:
    st.header("📘 Engineering Theory: DDM vs EFM")
    st.markdown("""
    ### 1. Direct Design Method (DDM) Limitations
    วิธี DDM เป็นวิธีอย่างง่าย (Approximate Method) ที่ใช้สัมประสิทธิ์โมเมนต์ ($\alpha$) ได้เลย แต่มีข้อจำกัดเคร่งครัดตาม ACI 318:
    * ต้องมีช่วงเสาต่อเนื่องอย่างน้อย 3 ช่วงในทิศทางที่พิจารณา
    * แผ่นพื้นต้องเป็นรูปสี่เหลี่ยมผืนผ้า โดยอัตราส่วนด้านยาว/ด้านสั้น $\le 2.0$
    * ความยาวช่วงเสาที่ติดกันต้องต่างกันไม่เกิน 1/3 ของช่วงยาว
    * อัตราส่วน Live Load / Dead Load ต้องไม่เกิน 2.0 (Unfactored)
    
    ### 2. Equivalent Frame Method (EFM)
    วิธี EFM จำลองโครงสร้างเป็น Portal Frame 2 มิติ โดยรวม Stiffness ของพื้น เสา และ Torsional Member เข้าด้วยกัน:
    * **แม่นยำกว่า:** เพราะคำนวณการกระจายโมเมนต์จริง (Moment Distribution)
    * **ยืดหยุ่นกว่า:** ใช้ได้กับ Load ที่ไม่สม่ำเสมอ หรือ Geometry ที่แปลกไปจากมาตรฐาน
    * โปรแกรมนี้เตรียม Parameters (Inertia Slab $I_s$, Inertia Drop $I_d$) ไว้รองรับการคำนวณ Stiffness Matrix ใน Tab ถัดไปแล้ว
    """)
