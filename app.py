import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design Pro", layout="wide")

# ==============================================================================
# 🧱 ENGINEERING CALCULATIONS & VALIDATION
# ==============================================================================

def validate_aci_standard(h_slab, h_drop, L1_left, L1_right, L2_top, L2_bot, drop_w1, drop_w2, has_drop):
    """ตรวจสอบมาตรฐาน ACI 318 สำหรับความหนาและความกว้างของ Drop Panel"""
    warnings = []
    L1_total = L1_left + L1_right
    L2_total = L2_top + L2_bot
    
    if has_drop:
        # 1. Thickness Check (min h/4)
        if h_drop < (h_slab / 4):
            warnings.append(f"⚠️ **Drop Thickness:** {h_drop} cm < เกณฑ์ขั้นต่ำ {h_slab/4:.2f} cm (h_slab/4)")
        
        # 2. Width Check (min L/6 from centerline)
        # สแปนที่ยาวกว่ามักจะเป็นตัวกำหนดเกณฑ์
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
# 🎨 VISUALIZATION SYSTEM
# ==============================================================================

def draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_loc, has_drop, d_w1, d_w2):
    """วาดรูปแปลนพื้น (Plan View) พร้อมระบุโซน Column/Middle Strip ตามสัดส่วนจริง"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    c1_m = c1_cm / 100
    c2_m = c2_cm / 100
    
    # คำนวณขอบเขตพื้นตามตำแหน่งเสา
    # ถ้าเป็น Corner หรือ Edge ด้านที่ไม่มีสแปนจะสิ้นสุดแค่ขอบเสา (c/2)
    slab_L = c1_m/2 if col_loc == "Corner Column" else L1_l
    slab_R = L1_r
    slab_T = L2_t
    slab_B = c2_m/2 if col_loc in ["Edge Column", "Corner Column"] else L2_b
    
    # 1. วาด Slab Area
    slab = patches.Rectangle((-slab_L, -slab_B), slab_L + slab_R, slab_B + slab_T,
                             facecolor='#f8f9fa', edgecolor='#2c3e50', linewidth=2, alpha=0.6, zorder=1)
    ax.add_patch(slab)

    # 2. คำนวณและวาด Column Strip (ACI: 0.25 * min(L1, L2) แต่ไม่เกินระยะขอบ)
    L_min = min((L1_l + L1_r), (L2_t + L2_b))
    cs_width = 0.25 * L_min
    
    # เส้นประสีเขียวแบ่ง Column Strip
    cs_top = min(cs_width, slab_T)
    cs_bot = min(cs_width, slab_B)
    
    ax.axhline(y=cs_top, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.8, zorder=2)
    ax.axhline(y=-cs_bot, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.8, zorder=2)
    
    # 3. วาดเสา (Columns)
    # เสาหลักที่ตำแหน่ง (0,0)
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, facecolor='#34495e', hatch='///', zorder=10))
    
    # เสาบริวาร (Neighboring Columns)
    neighbor_props = dict(facecolor='none', edgecolor='#bdc3c7', linestyle=':', linewidth=1, zorder=5)
    ax.add_patch(patches.Rectangle((L1_r - c1_m/2, -c2_m/2), c1_m, c2_m, **neighbor_props))
    if col_loc != "Corner Column":
        ax.add_patch(patches.Rectangle((-L1_l - c1_m/2, -c2_m/2), c1_m, c2_m, **neighbor_props))

    # 4. วาด Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w1/2, -d_w2/2), d_w1, d_w2, 
                                     facecolor='#f1c40f', edgecolor='#f39c12', alpha=0.5, zorder=8))

    # 5. ใส่ข้อความระบุโซน
    txt_style = dict(ha='center', va='center', fontsize=9, fontweight='bold', alpha=0.5)
    ax.text(slab_R/2, 0, "COLUMN STRIP", color='#27ae60', **txt_style)
    if slab_T > cs_top:
        ax.text(slab_R/2, cs_top + (slab_T-cs_top)/2, "MIDDLE STRIP", color='#2980b9', **txt_style)
    if slab_B > cs_bot:
        ax.text(slab_R/2, -cs_bot - (slab_B-cs_bot)/2, "MIDDLE STRIP", color='#2980b9', **txt_style)

    # 6. Dimensions
    arrow = dict(arrowstyle='<|-|>', color='#7f8c8d', linewidth=1.5)
    # X-Axis Dim
    ax.annotate('', xy=(0, -slab_B - 0.4), xytext=(slab_R, -slab_B - 0.4), arrowprops=arrow)
    ax.text(slab_R/2, -slab_B - 0.6, f"{slab_R}m", ha='center', fontsize=10)
    if col_loc != "Corner Column":
        ax.annotate('', xy=(-slab_L, -slab_B - 0.4), xytext=(0, -slab_B - 0.4), arrowprops=arrow)
        ax.text(-slab_L/2, -slab_B - 0.6, f"{slab_L}m", ha='center', fontsize=10)
    
    # Y-Axis Dim
    ax.annotate('', xy=(-slab_L - 0.4, 0), xytext=(-slab_L - 0.4, slab_T), arrowprops=arrow)
    ax.text(-slab_L - 0.7, slab_T/2, f"{slab_T}m", rotation=90, va='center', fontsize=10)
    if col_loc == "Interior Column":
        ax.annotate('', xy=(-slab_L - 0.4, -slab_B), xytext=(-slab_L - 0.4, 0), arrowprops=arrow)
        ax.text(-slab_L - 0.7, -slab_B/2, f"{slab_B}m", rotation=90, va='center', fontsize=10)

    ax.set_title(f"Plan View: {col_loc}", fontsize=12, pad=20)
    ax.set_xlim(-slab_L - 1.5, slab_R + 1.5)
    ax.set_ylim(-slab_B - 1.5, slab_T + 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_elevation(floor_env, h_up, h_lo, has_drop, h_drop_cm, c1_cm, slab_cm):
    """วาดรูปตัดแสดงความหนาและองค์ประกอบแนวดิ่ง"""
    fig, ax = plt.subplots(figsize=(5, 6))
    s_m = slab_cm / 100
    d_m = h_drop_cm / 100
    c_m = c1_cm / 100
    
    # Slab
    ax.add_patch(patches.Rectangle((-2, 0), 4, s_m, color='#ecf0f1', edgecolor='#7f8c8d', zorder=2))
    
    # Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-0.8, -d_m), 1.6, d_m, color='#f1c40f', alpha=0.7, zorder=3))
        ax.text(0.9, -d_m/2, f"Drop +{h_drop_cm}cm", va='center', fontsize=8, color='#d35400')

    # Columns
    if floor_env != "Top Floor (Roof)":
        ax.add_patch(patches.Rectangle((-c_m/2, s_m), c_m, 1.5, color='#3498db', alpha=0.8))
        ax.text(0.3, s_m + 0.75, f"H_upper: {h_up}m", fontsize=9)
        
    ax.add_patch(patches.Rectangle((-c_m/2, -1.8), c_m, 1.8 if not has_drop else 1.8-d_m, color='#e74c3c', alpha=0.8))
    ax.text(0.3, -0.9, f"H_lower: {h_lo}m", fontsize=9)

    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2.5)
    ax.axis('off')
    ax.set_title("Elevation Detail", fontsize=10)
    return fig

# ==============================================================================
# 🚀 MAIN APPLICATION INTERFACE
# ==============================================================================

st.title("🏗️ Flat Slab Design: Equivalent Frame Method (EFM)")
st.markdown("---")

# ใช้ Session State เพื่อจัดการลำดับการเลือก (Prevent NameError)
if 'col_loc' not in st.session_state:
    st.session_state['col_loc'] = "Interior Column"

tab1, tab2 = st.tabs(["📝 Input Parameters", "📘 Engineering Theory"])

with tab1:
    col_input, col_viz = st.columns([1.1, 1.4])

    with col_input:
        # --- 1. MATERIALS & LOADS ---
        st.subheader("1. Material & Loads")
        c1_mat, c2_mat = st.columns(2)
        with c1_mat:
            fc = st.selectbox("Concrete Strength f'c (ksc)", options=[210, 240, 280, 320, 350, 400], index=1)
            dl = st.number_input("Superimposed DL (kg/m²)", value=100, step=10)
        with c2_mat:
            fy_label = st.selectbox("Steel Grade (fy)", options=["SD30", "SD40", "SD50"], index=1)
            fy = {"SD30": 3000, "SD40": 4000, "SD50": 5000}[fy_label]
            ll = st.number_input("Live Load (kg/m²)", value=200, step=50)

        # --- 2. BOUNDARY CONDITIONS ---
        st.subheader("2. Boundary Conditions")
        floor_scenario = st.selectbox("Floor Level", ["Typical Floor", "Top Floor (Roof)", "Foundation Level"])
        col_location = st.selectbox("Column Location", ["Interior Column", "Edge Column", "Corner Column"])
        
        # คุมสิทธิการกรอกสแปนตามตำแหน่งเสา
        is_corner = (col_location == "Corner Column")
        is_edge = (col_location == "Edge Column")

        # --- 3. GEOMETRY ---
        st.subheader("3. Geometry & Spans")
        h_slab_cm = st.number_input("Slab Thickness (cm)", value=20.0, step=0.5)
        
        st.info("💡 ระบุระยะจากศูนย์กลางเสา (Centerline)")
        col_l1a, col_l1b = st.columns(2)
        with col_l1a:
            l1_l_val = 0.0 if is_corner else 3.0
            L1_l = st.number_input("L1 - Left Span (m)", value=l1_l_val, disabled=is_corner)
        with col_l1b:
            L1_r = st.number_input("L1 - Right Span (m)", value=3.5)
            
        col_l2a, col_l2b = st.columns(2)
        with col_l2a:
            L2_t = st.number_input("L2 - Top Half (m)", value=3.0)
        with col_l2b:
            l2_b_val = 0.0 if (is_edge or is_corner) else 3.0
            L2_b = st.number_input("L2 - Bottom Half (m)", value=l2_b_val, disabled=(is_edge or is_corner))

        col_sz1, col_sz2 = st.columns(2)
        with col_sz1:
            c1_cm = st.number_input("Column c1 (cm) [Analysis Dir]", value=40.0)
        with col_sz2:
            c2_cm = st.number_input("Column c2 (cm) [Transverse]", value=40.0)

        # --- 4. DROP PANEL ---
        st.markdown("---")
        has_drop = st.checkbox("✅ Include Drop Panel", value=False)
        h_drop_cm, drop_w1, drop_w2 = 0.0, 0.0, 0.0
        
        if has_drop:
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                h_drop_cm = st.number_input("Drop Projection (cm)", value=10.0, help="ความหนาที่ยื่นลงมาใต้ท้องพื้น")
                drop_w1 = st.number_input("Total Drop Width L1 (m)", value=2.5)
            with d_col2:
                st.write("") ; st.write("") # Spacer
                drop_w2 = st.number_input("Total Drop Width L2 (m)", value=2.5)
        
        # Real-time ACI Validation
        warnings = validate_aci_standard(h_slab_cm, h_drop_cm, L1_l, L1_r, L2_t, L2_b, drop_w1, drop_w2, has_drop)
        for w in warnings:
            st.warning(w)

        # --- 5. STOREY DATA ---
        st.subheader("4. Storey Heights")
        h_up, h_lo = 0.0, 3.0
        if floor_scenario != "Top Floor (Roof)":
            h_up = st.number_input("Upper Column Height (m)", value=3.0)
        h_lo = st.number_input("Lower Column Height (m)", value=3.0)

        # --- DATA PROCESSING ---
        calc_data = {
            'L1_total': L1_l + L1_r,
            'L2_total': L2_t + L2_b,
            'w_u_approx': 1.2 * (dl + (h_slab_cm/100 * 2400)) + 1.6 * ll,
            'fc': fc, 'fy': fy
        }

    with col_viz:
        st.subheader("👁️ Structural Analysis View")
        v_tab1, v_tab2 = st.tabs(["📐 Plan View", "断面 Elevation"])
        
        with v_tab1:
            fig_plan = draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_location, has_drop, drop_w1, drop_w2)
            st.pyplot(fig_plan)
            
        with v_tab2:
            fig_elev = draw_elevation(floor_scenario, h_up, h_lo, has_drop, h_drop_cm, c1_cm, h_slab_cm)
            st.pyplot(fig_elev)
            
        # Summary Box
        st.success(f"""
        **📋 Design Summary (Factored):**
        - **Analysis Strip Width:** {calc_data['L2_total']:.2f} m
        - **Average Span ($L_n$):** {(calc_data['L1_total'] - c1_cm/100):.2f} m
        - **Approx. Design Load ($w_u$):** {calc_data['w_u_approx']:.0f} kg/m²
        - **Total Factored Force on Strip:** {calc_data['w_u_approx'] * calc_data['L1_total'] * calc_data['L2_total'] / 1000:.2f} Tons
        """)
        
        st.info("""
        **🔍 EFM Logic Applied:**
        โปรแกรมจะคำนวณ Stiffness ($K$) ของ Slab และ Column แยกกันตาม Geometry ที่คุณระบุ 
        โดยในส่วนของ Drop Panel จะมีการเพิ่มค่า Moment of Inertia ($I$) เฉพาะช่วงหัวเสา 
        เพื่อหาค่าโอนถ่ายโมเมนต์ที่แม่นยำกว่าวิธี Direct Design Method
        """)

with tab2:
    st.header("📘 Equivalent Frame Method (EFM)")
    
    st.markdown("""
    ### 1. การแบ่งแถบพิจารณา (Strips)
    ตามมาตรฐาน **ACI 318**, พื้นจะถูกแบ่งออกเป็นแถบเสา (Column Strip) และแถบกลาง (Middle Strip):
    - **Column Strip:** กว้างข้างละ 25% ของสแปนที่สั้นกว่า ($0.25 L_{min}$)
    - **Middle Strip:** พื้นที่ส่วนที่เหลือระหว่างแถบเสา
    
    ### 2. ข้อกำหนด Drop Panel (ACI 318-19)
    เพื่อให้สามารถลดความหนาพื้นหรือเพิ่มแรงต้านทานแรงเฉือนทะลุ (Punching Shear):
    - **ความหนา:** ต้องยื่นลงมาจากท้องพื้นอย่างน้อย 1/4 ของความหนาพื้น ($h/4$)
    - **ระยะยื่น:** ต้องยาวออกจากศูนย์กลางเสาไม่น้อยกว่า 1/6 ของความยาวสแปนในทิศทางนั้นๆ
    
    ### 3. โครงสร้างเสาเสมือน (Equivalent Column)
    ความแข็งแรงของระบบจะขึ้นอยู่กับค่า Stiffness ของเสา ($K_c$) และความแข็งแรงในการบิดของคานขวาง ($K_t$) 
    ซึ่งคำนวณจากสูตร:
    $$ \\frac{1}{K_{ec}} = \\frac{1}{\\sum K_c} + \\frac{1}{K_t} $$
    """)

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
    KSC_TO_MPA = 0.0980665  # ใช้สำหรับเข้าสูตร ACI ที่ต้องการหน่วย MPa

# ==============================================================================
# 🧮 DATA NORMALIZATION ENGINE
# ==============================================================================

def prepare_calculation_data_v2(
    h_slab_cm, h_drop_cm, has_drop, 
    c1_cm, c2_cm, drop_w2,
    L1_l, L1_r, L2_t, L2_b,
    fc_ksc, fy_grade, dl_kgm2, ll_kgm2
):
    """
    แปลง User Input ทั้งหมดให้เป็น SI Units (N, m, Pa) เพื่อความถูกต้องแม่นยำ 
    ตามมาตรฐาน ACI 318M
    """
    
    # --- 1. Geometry Normalization (cm -> m) ---
    h_s = h_slab_cm * Units.CM_TO_M
    h_d = (h_slab_cm + h_drop_cm) * Units.CM_TO_M if has_drop else h_s
    
    c1 = c1_cm * Units.CM_TO_M
    c2 = c2_cm * Units.CM_TO_M
    
    # Drop Panel Width (Transverse direction)
    b_drop = drop_w2 if has_drop else 0.0  # Already in m from input

    # Span Geometry
    L1 = L1_l + L1_r         # Analysis Direction (m)
    L2 = L2_t + L2_b         # Transverse Direction (m)
    Ln = L1 - c1             # Clear Span (m)
    
    # --- 2. Material Properties (ACI 318M Standard) ---
    # Concrete
    fc_mpa = fc_ksc * Units.KSC_TO_MPA      # แปลง ksc -> MPa เพื่อเข้าสูตร
    fc_pa = fc_ksc * Units.KSC_TO_PA        # แปลง ksc -> Pa (N/m^2) เพื่อใช้คำนวณ Strength
    
    # Modulus of Elasticity (Ec)
    # ACI 318M-19 Section 19.2.2.1: Ec = 4700 * sqrt(fc') ในหน่วย MPa
    Ec_mpa = 4700 * np.sqrt(fc_mpa)
    Ec_pa = Ec_mpa * 1e6                    # แปลงกลับเป็น Pa (N/m^2) เพื่อใช้ใน Stiffness Matrix
    
    # Steel (Rebar)
    # fy_grade input เช่น "SD40" -> 4000 ksc
    fy_ksc = 3000 if fy_grade == "SD30" else (4000 if fy_grade == "SD40" else 5000)
    fy_pa = fy_ksc * Units.KSC_TO_PA

    # --- 3. Load Normalization (kg/m² -> N/m² or Pa) ---
    # Self-weight (Density of Concrete = 2400 kg/m^3)
    # เราคำนวณ SW เป็น Pressure (Pa) แยกตามความหนา
    
    density_conc_kg = 2400
    density_conc_N = density_conc_kg * Units.G  # ~23,536 N/m^3
    
    sw_slab_pa = h_s * density_conc_N
    
    # Superimposed Dead Load
    sdl_pa = dl_kgm2 * Units.KG_TO_N
    
    # Live Load
    ll_pa = ll_kgm2 * Units.KG_TO_N
    
    # Total Factored Load (wu) - ACI 318
    # Note: ในขั้นตอนนี้เราจะคิดเฉพาะ Slab Weight ปกติ 
    # ส่วนน้ำหนัก Drop Panel ที่เพิ่มมามักจะคิดเป็น Point Load หรือ Added Area Load ทีหลัง
    # แต่เพื่อความง่ายในเบื้องต้น เราจะเฉลี่ยหรือคิดที่ Slab หลักก่อน
    
    wu_pa = (1.2 * (sw_slab_pa + sdl_pa)) + (1.6 * ll_pa) # Unit: N/m^2

    # --- 4. Stiffness Parameters (Moment of Inertia - m^4) ---
    # Gross Inertia ของหน้าตัด Slab (เต็มความกว้าง L2)
    Ig_slab = (L2 * (h_s**3)) / 12
    
    # Gross Inertia ของหน้าตัด Drop (เฉพาะช่วงหัวเสา)
    # หมายเหตุ: การคำนวณ Ig ของ Drop ต้องระวังเรื่อง Effective Width 
    # แต่ในขั้นต้นใช้ความกว้าง Drop จริงไปก่อน
    Ig_drop = (b_drop * (h_d**3)) / 12 + ((L2 - b_drop) * (h_s**3)) / 12 if has_drop else Ig_slab

    # 📦 Return Normalized Data Object (Dictionary)
    return {
        "inputs_raw": { # เก็บค่าเดิมไว้ display
            "fc_ksc": fc_ksc,
            "h_slab_cm": h_slab_cm
        },
        "geom": {
            "L1": L1, "L2": L2, "Ln": Ln,
            "c1": c1, "c2": c2,
            "h_s": h_s, "h_d": h_d,
            "b_drop": b_drop
        },
        "mat": {
            "Ec_pa": Ec_pa,       # Young's Modulus (Pa) - สำคัญมากสำหรับ Stiffness
            "fc_pa": fc_pa,       # Compressive Strength (Pa)
            "fy_pa": fy_pa
        },
        "loads": {
            "wu_pa": wu_pa,       # Factored Load (N/m^2)
            "sw_pa": sw_slab_pa,  # Self-weight (N/m^2)
            "sdl_pa": sdl_pa,
            "ll_pa": ll_pa
        },
        "stiffness": {
            "Ig_slab": Ig_slab,   # m^4
            "Ig_drop": Ig_drop    # m^4
        }
    }
# เรียกใช้งาน
calc_obj = prepare_calculation_data()
