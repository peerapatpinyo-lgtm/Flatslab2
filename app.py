import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design Pro", layout="wide")

# ==============================================================================
# 🧱 UNIT CONVERSION SYSTEM & LOGIC
# ==============================================================================
calc_data = {}

# --- ฟังก์ชันตรวจสอบมาตรฐานวิศวกรรม (ACI 318 / วสท.) ---
def validate_aci_standard(h_slab, h_drop, L1_left, L1_right, L2_top, L2_bot, drop_w1, drop_w2, has_drop):
    warnings = []
    L1_total = L1_left + L1_right
    L2_total = L2_top + L2_bot
    
    if has_drop:
        # 1. ความหนา Drop (Thickness): ต้องยื่นลงมาอย่างน้อย h_slab / 4
        if h_drop < (h_slab / 4):
            warnings.append(f"⚠️ **Drop Thickness Low:** ส่วนที่ยื่น ({h_drop} cm) ต้อง ≥ h_slab/4 ({h_slab/4:.2f} cm)")
        
        # 2. ความกว้าง Drop (Width): ระยะจากศูนย์กลางเสาถึงขอบ Drop ต้อง ≥ L/6
        # ACI กำหนดว่าแผ่น Drop ต้องแผ่ออกไปจากศูนย์กลางเสาไม่น้อยกว่า L/6 ของสแปนนั้นๆ
        min_extend_L1 = L1_total / 6
        min_extend_L2 = L2_total / 6
        
        if (drop_w1 / 2) < min_extend_L1:
            warnings.append(f"⚠️ **Drop Width L1:** ระยะยื่นจากศูนย์กลาง ({drop_w1/2:.2f} m) น้อยกว่า L1/6 ({min_extend_L1:.2f} m)")
        if (drop_w2 / 2) < min_extend_L2:
            warnings.append(f"⚠️ **Drop Width L2:** ระยะยื่นจากศูนย์กลาง ({drop_w2/2:.2f} m) น้อยกว่า L2/6 ({min_extend_L2:.2f} m)")
            
    return warnings

# --- Function วาด Plan View (ปรับปรุงให้รองรับสัดส่วนซ้าย-ขวาไม่เท่ากัน) ---
def draw_plan_view(L1_left, L1_right, L2_top, L2_bot, c1_m, c2_m, col_loc, has_drop, drop_w1, drop_w2):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # กำหนดขอบเขตพื้นตามจริง
    # สำหรับ Interior: จะเห็นเต็มทั้ง 2 ฝั่ง
    # สำหรับ Edge/Corner: จะโดนตัดขอบตามตำแหน่งเสา
    
    # --- 1. DRAWING GRID & AXES ---
    grid_color = '#7f8c8d'
    ax.axhline(y=0, color=grid_color, linestyle='-.', linewidth=1)
    ax.axvline(x=0, color=grid_color, linestyle='-.', linewidth=1)

    # --- 2. DRAWING SLAB AREA (Design Strip) ---
    # สี่เหลี่ยมครอบคลุมพื้นที่จาก (-L1_left ถึง L1_right) และ (-L2_bot ถึง L2_top)
    slab_rect = patches.Rectangle((-L1_left, -L2_bot), L1_left + L1_right, L2_bot + L2_top,
                                  facecolor='#f0f2f6', edgecolor='#1f77b4', 
                                  linestyle='-', linewidth=2, alpha=0.4, zorder=1)
    ax.add_patch(slab_rect)

    # --- 3. COLUMN STRIP & MIDDLE STRIP BOUNDARIES ---
    # ACI: Column Strip กว้าง 0.25 * min(L1, L2) ในแต่ละด้านของเซ็นเตอร์ไลน์
    L_min = min((L1_left + L1_right), (L2_top + L2_bot))
    cs_width = 0.25 * L_min
    
    # วาดเส้นแบ่ง Column Strip (เส้นประสีเขียว)
    # ต้องระวังไม่ให้วาดเลยขอบพื้น (กรณี Edge Column)
    top_bound = min(cs_width, L2_top)
    bot_bound = min(cs_width, L2_bot)
    
    ax.axhline(y=top_bound, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.8, zorder=2)
    ax.axhline(y=-bot_bound, color='#27ae60', linestyle='--', linewidth=1.5, alpha=0.8, zorder=2)
    
    # Label Zones
    text_strip_props = dict(ha='center', va='center', fontsize=10, fontweight='bold', alpha=0.6)
    ax.text(L1_right/2, 0, "COLUMN STRIP", color='#27ae60', **text_strip_props)
    
    if L2_top > top_bound:
        ax.text(L1_right/2, top_bound + (L2_top - top_bound)/2, "MIDDLE STRIP", color='#2980b9', **text_strip_props)
    if L2_bot > bot_bound:
        ax.text(L1_right/2, -bot_bound - (L2_bot - bot_bound)/2, "MIDDLE STRIP", color='#2980b9', **text_strip_props)

    # --- 4. DRAWING COLUMNS ---
    # เสากลาง (Target Column)
    main_col = patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                 facecolor='#2c3e50', edgecolor='black', hatch='...', zorder=10)
    ax.add_patch(main_col)
    
    # เสาข้างเคียง (Neighboring Columns)
    col_style = dict(facecolor='white', edgecolor='gray', linestyle=':', zorder=5)
    ax.add_patch(patches.Rectangle((L1_right - c1_m/2, -c2_m/2), c1_m, c2_m, **col_style))
    if col_loc != "Corner Column":
        ax.add_patch(patches.Rectangle((-L1_left - c1_m/2, -c2_m/2), c1_m, c2_m, **col_style))

    # --- 5. DROP PANEL ---
    if has_drop:
        drop = patches.Rectangle((-drop_w1/2, -drop_w2/2), drop_w1, drop_w2,
                                 facecolor='#ffcc00', edgecolor='#d35400', alpha=0.4, 
                                 linestyle='-', linewidth=2, zorder=8)
        ax.add_patch(drop)

    # --- 6. DIMENSIONS ---
    arrow_props = dict(arrowstyle='<|-|>', color='#f1c40f', linewidth=2)
    text_props = dict(ha='center', va='center', fontsize=11, fontweight='bold', 
                      color='#d35400', backgroundcolor='white')
    
    # X-Dimension
    ax.annotate('', xy=(0, -L2_bot - 0.5), xytext=(L1_right, -L2_bot - 0.5), arrowprops=arrow_props)
    ax.text(L1_right/2, -L2_bot - 0.5, f"L1-R: {L1_right}m", **text_props)
    ax.annotate('', xy=(-L1_left, -L2_bot - 0.5), xytext=(0, -L2_bot - 0.5), arrowprops=arrow_props)
    ax.text(-L1_left/2, -L2_bot - 0.5, f"L1-L: {L1_left}m", **text_props)

    # Y-Dimension
    ax.annotate('', xy=(-L1_left - 0.5, 0), xytext=(-L1_left - 0.5, L2_top), arrowprops=arrow_props)
    ax.text(-L1_left - 0.5, L2_top/2, f"L2-T: {L2_top}m", rotation=90, **text_props)
    ax.annotate('', xy=(-L1_left - 0.5, -L2_bot), xytext=(-L1_left - 0.5, 0), arrowprops=arrow_props)
    ax.text(-L1_left - 0.5, -L2_bot/2, f"L2-B: {L2_bot}m", rotation=90, **text_props)

    ax.set_title(f"Plan Geometry: {col_loc}", fontsize=14, fontweight='bold')
    ax.set_xlim(-L1_left - 1.5, L1_right + 1.5)
    ax.set_ylim(-L2_bot - 1.5, L2_top + 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

# --- Function วาดรูปตัด (Elevation) ---
def draw_elevation(scenario, h_upper, h_lower, support_cond, has_drop, h_drop, c1_m):
    fig, ax = plt.subplots(figsize=(4, 5))
    ax.add_patch(patches.Rectangle((-1.5, -0.1), 3, 0.2, color='gray', alpha=0.5)) 
    ax.text(1.6, 0, "Slab", va='center', fontsize=9)
    
    if has_drop:
        drop_w_view = 1.0 
        ax.add_patch(patches.Rectangle((-drop_w_view/2, -0.1 - h_drop), drop_w_view, h_drop, color='#f39c12', alpha=0.8))
        ax.text(0.6, -0.1 - h_drop/2, f"Drop +{h_drop*100:.0f}cm", fontsize=8, color='#d35400')

    col_width = c1_m 
    if scenario != "Top Floor (Roof)":
        ax.add_patch(patches.Rectangle((-col_width/2, 0.1), col_width, 1.5, color='#3498db')) 
        ax.text(0.2, 0.8, f"Upper: {h_upper}m", fontsize=9, color='blue')

    ax.add_patch(patches.Rectangle((-col_width/2, -1.6), col_width, 1.5, color='#e74c3c')) 
    
    if scenario == "Foundation/First Floor":
        ax.text(0.2, -0.8, f"Lower: {h_lower}m", fontsize=9, color='red')
        if support_cond == "Fixed":
            ax.add_patch(patches.Rectangle((-0.4, -1.7), 0.8, 0.1, color='black')) 
            ax.text(0, -1.9, "FIXED", ha='center', fontsize=8, fontweight='bold')
        else: 
            ax.plot(0, -1.6, marker='^', markersize=10, color='black') 
            ax.text(0, -1.9, "PINNED", ha='center', fontsize=8, fontweight='bold')
    else:
        ax.text(0.2, -0.8, f"Lower: {h_lower}m", fontsize=9, color='red')

    ax.set_xlim(-2, 2)
    ax.set_ylim(-2.5, 2.5)
    ax.axis('off')
    return fig

# --- 2. Main Interface ---
st.title("🏗️ Flat Slab Design: Equivalent Frame Method")

tab1, tab2 = st.tabs(["📝 Input Parameters", "📘 Theory & Manual"])

with tab1:
    col_input, col_viz = st.columns([1, 1.2])

    with col_input:
        # --- Section 1: Materials ---
        st.subheader("1. Material & Loads")
        c1_mat, c2_mat = st.columns(2)
        with c1_mat:
            fc_options = [210, 240, 280, 320, 350, 400]
            fc = st.selectbox("Concrete Strength f'c (ksc)", options=fc_options, index=1)
            dl = st.number_input("SDL (kg/m²)", value=100)
        with c2_mat:
            fy_options = {"SD30": 3000, "SD40": 4000, "SD50": 5000}
            fy_label = st.selectbox("Steel Grade (fy)", options=list(fy_options.keys()), index=1)
            fy = fy_options[fy_label]
            ll = st.number_input("Live Load (kg/m²)", value=200)
        
        # --- Section 2: Geometry ---
        st.subheader("2. Geometry (Span & Section)")
        h_slab = st.number_input("Slab Thickness (cm)", value=20.0)
        
        st.write("**Span L1 (Analysis Direction)**")
        col_l1a, col_l1b = st.columns(2)
        with col_l1a:
            L1_left = st.number_input("L1 - Left Span (m)", value=3.0, help="ระยะจากศูนย์กลางเสาไปทางซ้าย")
        with col_l1b:
            L1_right = st.number_input("L1 - Right Span (m)", value=3.0, help="ระยะจากศูนย์กลางเสาไปทางขวา")
            
        st.write("**Span L2 (Transverse Width)**")
        col_l2a, col_l2b = st.columns(2)
        with col_l2a:
            L2_top = st.number_input("L2 - Top Half (m)", value=3.0, help="ความกว้าง Strip ครึ่งบน")
        with col_l2b:
            L2_bot = st.number_input("L2 - Bottom Half (m)", value=3.0, help="ความกว้าง Strip ครึ่งล่าง")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            c1 = st.number_input("Column c1 (cm)", value=40.0)
        with col_c2:
            c2 = st.number_input("Column c2 (cm)", value=40.0)

        # --- ส่วน Drop Panel ---
        st.markdown("---")
        st.write("#### 🔸 Drop Panel Configuration")
        has_drop = st.checkbox("Has Drop Panel?", value=False)
        
        h_drop_val, drop_w1, drop_w2 = 0.0, 0.0, 0.0
        if has_drop:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                h_drop_val = st.number_input("Drop Projection (cm)", value=15.0)
                drop_w1 = st.number_input("Drop Total Width L1 (m)", value=2.5)
            with col_d2:
                st.write("") ; st.write("")
                drop_w2 = st.number_input("Drop Total Width L2 (m)", value=2.5)
        
        # ACI Validation
        warnings = validate_aci_standard(h_slab, h_drop_val, L1_left, L1_right, L2_top, L2_bot, drop_w1, drop_w2, has_drop)
        for w in warnings:
            st.warning(w)

        # --- Section 3: Boundary Conditions ---
        st.subheader("3. Boundary Conditions")
        floor_scenario = st.selectbox("Floor Level", ["Typical Floor (Intermediate)", "Top Floor (Roof)", "Foundation/First Floor"])
        col_location = st.selectbox("Column Location", ["Interior Column", "Edge Column", "Corner Column"])
        
        h_upper, h_lower, support_cond = 0.0, 0.0, "Fixed"
        if floor_scenario != "Top Floor (Roof)":
            h_upper = st.number_input("Upper Storey Height (m)", value=3.0)
        
        if floor_scenario == "Foundation/First Floor":
            h_lower = st.number_input("Foundation Height (m)", value=1.5)
            support_cond = st.radio("Foundation Support", ["Fixed", "Pinned"], horizontal=True)
        else:
            h_lower = st.number_input("Lower Storey Height (m)", value=3.0)

        # ---------------------------------------------------------
        # แปลง Input สู่ Base Units (MKS) และเก็บข้อมูลลง calc_data
        # ---------------------------------------------------------
        calc_data = {
            'L1_left': L1_left, 'L1_right': L1_right,
            'L2_top': L2_top, 'L2_bot': L2_bot,
            'L1_total': L1_left + L1_right,
            'L2_total': L2_top + L2_bot,
            'h_slab': h_slab / 100,
            'c1': c1 / 100, 'c2': c2 / 100,
            'h_drop': (h_drop_val / 100) if has_drop else 0,
            'drop_w1': drop_w1, 'drop_w2': drop_w2,
            'fc': fc, 'fy': fy, 'dl': dl, 'll': ll
        }

    with col_viz:
        st.subheader("👁️ Structural Visualization")
        v_tab1, v_tab2 = st.tabs(["Plan View (Top)", "Elevation (Side)"])
        
        with v_tab1:
            st.caption("แสดงสัดส่วนจริงของพื้นและ Column Strip (เส้นประสีเขียว)")
            fig_plan = draw_plan_view(
                calc_data['L1_left'], calc_data['L1_right'],
                calc_data['L2_top'], calc_data['L2_bot'],
                calc_data['c1'], calc_data['c2'],
                col_location, has_drop, 
                calc_data['drop_w1'], calc_data['drop_w2']
            )
            st.pyplot(fig_plan)
            
        with v_tab2:
            st.caption("Elevation View: แสดงความหนาพื้นและตำแหน่งเสา")
            fig_elev = draw_elevation(
                floor_scenario, h_upper, h_lower, support_cond,
                has_drop, calc_data['h_drop'], calc_data['c1']
            )
            st.pyplot(fig_elev)
            
        st.info(f"""
        **Engineer's Summary:**
        - **Total Analysis Span ($L_1$):** {calc_data['L1_total']:.2f} m
        - **Design Strip Width ($L_2$):** {calc_data['L2_total']:.2f} m
        - **Concrete Grade:** {fc} ksc | **Steel Grade:** {fy_label} ({fy} ksc)
        - **Load Case:** $1.2DL + 1.6LL$ = {1.2*(dl + (h_slab/100)*2400) + 1.6*ll:.0f} kg/m² (โดยประมาณ)
        """)

with tab2:
    st.markdown("""
    ### ทฤษฎีและข้อกำหนด (ACI 318 / วสท.)
    
    1. **Design Strip:**
       - **Column Strip:** ความกว้างข้างละ 25% ของ $L_{min}$ วัดจากศูนย์กลางเสา
       - **Middle Strip:** พื้นที่ส่วนที่เหลือระหว่าง Column Strip สองข้าง
    
    2. **Drop Panel Requirements:**
       - ความหนาที่ยื่นลงมาต้อง $\geq h_{slab}/4$
       - ความกว้างจากศูนย์กลางเสาต้อง $\geq L/6$ ในแต่ละทิศทาง
    """)
