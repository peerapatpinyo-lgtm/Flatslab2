import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design", layout="wide")

# ==============================================================================
# 🧱 UNIT CONVERSION SYSTEM & LOGIC
# ==============================================================================
calc_data = {}

# --- ฟังก์ชันตรวจสอบมาตรฐานวิศวกรรม (ACI 318 / วสท.) ---
def validate_aci_standard(h_slab, h_drop, L1, L2, drop_w1, drop_w2, has_drop):
    warnings = []
    if has_drop:
        # 1. ความหนา Drop (ต้องยื่นลงมาอย่างน้อย h/4)
        if h_drop < (h_slab / 4):
            warnings.append(f"⚠️ **Drop Thickness Low:** ความหนา Drop Panel ใต้ท้องพื้น ({h_drop} cm) น้อยกว่ามาตรฐานที่กำหนดให้อย่างน้อย {h_slab/4:.2f} cm (h/4)")
        
        # 2. ความยาว Drop (ต้องกว้างอย่างน้อย L/3 เพื่อให้ยื่นจากศูนย์กลาง L/6)
        min_w1 = L1 / 3
        min_w2 = L2 / 3
        if drop_w1 < min_w1:
            warnings.append(f"⚠️ **Drop Width L1:** ความกว้าง Drop ทิศทาง L1 ({drop_w1} m) สั้นกว่ามาตรฐาน ควรยาวอย่างน้อย {min_w1:.2f} m (L1/3)")
        if drop_w2 < min_w2:
            warnings.append(f"⚠️ **Drop Width L2:** ความกว้าง Drop ทิศทาง L2 ({drop_w2} m) สั้นกว่ามาตรฐาน ควรยาวอย่างน้อย {min_w2:.2f} m (L2/3)")
            
    return warnings

# --- Function วาด Plan View (Top View) ---
def draw_plan_view(L1, L2, c1_m, c2_m, col_loc, dl, ll, has_drop, drop_w1, drop_w2):
    """
    วาด Plan View แบบ Full Grid Geometry (4 Quadrants)
    แสดงการตัดขอบพื้นที่ตามตำแหน่งเสาจริง (Interior, Edge, Corner)
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # --- 1. SETUP PARAMETERS ---
    L1_right = L1         # L1-2
    L1_left  = L1         # L1-1 (ค่าเริ่มต้นสำหรับ Interior)
    
    L2_top   = L2 / 2     # L2-1
    L2_bot   = L2 / 2     # L2-2
    
    # ตัดขอบพื้นตามตำแหน่งเสา
    if col_loc == "Edge Column":
        # สมมติ Edge อยู่ขอบล่าง: ตัด L2_bot ทิ้ง เหลือแค่ขอบเสา
        L2_bot = c2_m / 2 
    elif col_loc == "Corner Column":
        # สมมติ Corner อยู่ซ้ายล่าง: ตัด L1_left และ L2_bot ทิ้ง เหลือแค่ขอบเสา
        L1_left = c1_m / 2
        L2_bot = c2_m / 2

    # --- 2. DRAWING GRID & AXES ---
    grid_color = '#7f8c8d'
    
    ax.axhline(y=0, color=grid_color, linestyle='-.', linewidth=1)
    ax.axvline(x=0, color=grid_color, linestyle='-.', linewidth=1)
    
    # เส้น Grid ของเสาข้างเคียง
    ax.axvline(x=L1_right, color=grid_color, linestyle=':', alpha=0.5)
    if col_loc in ["Interior Column", "Edge Column"]:
        ax.axvline(x=-L1_left, color=grid_color, linestyle=':', alpha=0.5)

    # --- 3. DRAWING SLAB AREA (Design Strip) ---
    slab_rect = patches.Rectangle((-L1_left, -L2_bot), L1_left + L1_right, L2_bot + L2_top,
                                  facecolor='#f0f2f6', edgecolor='#1f77b4', 
                                  linestyle='-', linewidth=2, alpha=0.6, zorder=1)
    ax.add_patch(slab_rect)

    # --- 4. DRAWING COLUMNS ---
    # Center Column (Main)
    main_col = patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                 facecolor='#2c3e50', edgecolor='black', hatch='...', zorder=10)
    ax.add_patch(main_col)
    
    # Ghost Columns (เพื่อบอกตำแหน่งเสาต้นถัดไป)
    right_col = patches.Rectangle((L1_right - c1_m/2, -c2_m/2), c1_m, c2_m, 
                                  facecolor='white', edgecolor='gray', linestyle=':', zorder=5)
    ax.add_patch(right_col)
    
    if col_loc in ["Interior Column", "Edge Column"]:
        left_col = patches.Rectangle((-L1_left - c1_m/2, -c2_m/2), c1_m, c2_m, 
                                     facecolor='white', edgecolor='gray', linestyle=':', zorder=5)
        ax.add_patch(left_col)

    # --- 5. DROP PANEL (ถ้ามี) ---
    if has_drop:
        drop = patches.Rectangle((-drop_w1/2, -drop_w2/2), drop_w1, drop_w2,
                                 facecolor='#ffcc00', edgecolor='#d35400', alpha=0.4, 
                                 linestyle='--', linewidth=1.5, zorder=8)
        ax.add_patch(drop)

    # --- 6. DIMENSIONS ---
    arrow_props = dict(arrowstyle='<|-|>', color='#f1c40f', linewidth=2.5) 
    text_props = dict(ha='center', va='center', fontsize=12, fontweight='bold', 
                      color='#d35400', backgroundcolor='white')
    
    dim_offset = 1.0 

    # L1-2 (Right Span)
    ax.annotate('', xy=(0, -dim_offset), xytext=(L1_right, -dim_offset), arrowprops=arrow_props)
    ax.text(L1_right/2, -dim_offset, f"L1-2 = {L1_right} m", **text_props)
    
    # L1-1 (Left Span)
    if col_loc in ["Interior Column", "Edge Column"]:
        ax.annotate('', xy=(-L1_left, -dim_offset), xytext=(0, -dim_offset), arrowprops=arrow_props)
        ax.text(-L1_left/2, -dim_offset, f"L1-1 = {L1_left} m", **text_props)

    # L2-1 (Top Width)
    ax.annotate('', xy=(-dim_offset, 0), xytext=(-dim_offset, L2_top), arrowprops=arrow_props)
    ax.text(-dim_offset, L2_top/2, f"L2-1\n{L2_top}m", rotation=90, **text_props)
    
    # L2-2 (Bottom Width)
    if col_loc == "Interior Column" or col_loc == "Edge Column":
        # สำหรับ Edge Column เราตั้งให้ L2_bot กุดไปแล้ว ดังนั้น Dimension จะสั้นลง
        ax.annotate('', xy=(-dim_offset, 0), xytext=(-dim_offset, -L2_bot), arrowprops=arrow_props)
        ax.text(-dim_offset, -L2_bot/2, f"L2-2\n{L2_bot}m", rotation=90, **text_props)

    # --- 7. FINAL SETTINGS ---
    ax.set_title(f"Full Frame Geometry: {col_loc}", fontsize=14, fontweight='bold')
    ax.set_xlim(-L1_left - 2, L1_right + 2)
    ax.set_ylim(-L2_bot - 2, L2_top + 2)
    ax.set_aspect('equal')
    ax.axis('off')

    return fig

# --- Function วาดรูปตัด (Elevation) ---
def draw_elevation(scenario, h_upper, h_lower, support_cond, has_drop, h_drop, c1_m):
    fig, ax = plt.subplots(figsize=(4, 5))
    
    # Slab Layer
    ax.add_patch(patches.Rectangle((-1.5, -0.1), 3, 0.2, color='gray', alpha=0.5)) 
    ax.text(1.6, 0, "Slab", va='center', fontsize=9)
    
    # Drop Panel Layer (Elevation)
    if has_drop:
        drop_w_view = 1.0 
        ax.add_patch(patches.Rectangle((-drop_w_view/2, -0.1 - h_drop), drop_w_view, h_drop, color='#f39c12', alpha=0.8))
        ax.text(0.6, -0.1 - h_drop/2, f"Drop +{h_drop*100:.0f}cm", fontsize=8, color='#d35400')

    col_width = c1_m 
    
    # Upper Column
    if scenario != "Top Floor (Roof)":
        ax.add_patch(patches.Rectangle((-col_width/2, 0.1), col_width, 1.5, color='#3498db')) 
        ax.text(0.2, 0.8, f"Upper: {h_upper}m", fontsize=9, color='blue')

    # Lower Column
    ax.add_patch(patches.Rectangle((-col_width/2, -1.6), col_width, 1.5, color='#e74c3c')) 
    
    if scenario == "Foundation/First Floor":
        ax.text(0.2, -0.8, f"Lower: {h_lower}m", fontsize=9, color='red')
        if support_cond == "Fixed":
            ax.add_patch(patches.Rectangle((-0.4, -1.7), 0.8, 0.1, color='black')) # Base
            ax.text(0, -1.9, "FIXED", ha='center', fontsize=8, fontweight='bold')
        else: 
            ax.plot(0, -1.6, marker='^', markersize=10, color='black') # Pinned
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
    col_input, col_viz = st.columns([1, 1.3])

    with col_input:
        st.subheader("1. Material & Loads")
        c1_mat, c2_mat = st.columns(2)
        with c1_mat:
            fc = st.number_input("f'c (ksc)", value=240)
            dl = st.number_input("SDL (kg/m²)", value=100)
        with c2_mat:
            fy = st.number_input("fy (ksc)", value=4000)
            ll = st.number_input("Live Load (kg/m²)", value=200)
        
        st.subheader("2. Geometry (Span & Section)")
        h_slab = st.number_input("Slab Thickness (cm)", value=20.0)
        
        c1_geo, c2_geo = st.columns(2)
        with c1_geo:
            L1 = st.number_input("Span L1 (Right side) (m)", value=6.0, help="ระยะจากศูนย์กลางเสาถึงกึ่งกลางช่วงด้านขวา")
            c1 = st.number_input("Column c1 (cm)", value=40.0)
        with c2_geo:
            L2 = st.number_input("Span L2 (Total Width) (m)", value=6.0, help="ความกว้างรวมของ Strip (L2_top + L2_bot)")
            c2 = st.number_input("Column c2 (cm)", value=40.0)

        # --- ส่วน Drop Panel ---
        st.markdown("---")
        st.write("#### 🔸 Drop Panel Configuration")
        has_drop = st.checkbox("Has Drop Panel?", value=False)
        
        h_drop_val = 0.0
        drop_w1, drop_w2 = 0.0, 0.0
        
        if has_drop:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                h_drop_val = st.number_input("Drop Projection (cm)", value=15.0, help="ความหนาที่ยื่นลงมาจากท้องพื้น (ไม่รวมพื้นเดิม)")
                drop_w1 = st.number_input("Drop Total Width L1 (m)", value=2.5)
            with col_d2:
                st.write("") # Spacer
                st.write("")
                drop_w2 = st.number_input("Drop Total Width L2 (m)", value=2.5)
                
        # แจ้งเตือน Validation ตามมาตรฐาน ACI
        warnings = validate_aci_standard(h_slab, h_drop_val, L1, L2, drop_w1, drop_w2, has_drop)
        for w in warnings:
            st.warning(w)
        # -----------------------------

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

        # Convert Input to Base Units (MKS: m, kg)
        calc_data = {
            'L1': L1, 'L2': L2,
            'h_slab': h_slab/100,
            'c1': c1/100, 'c2': c2/100,
            'h_drop': h_drop_val/100 if has_drop else 0,
            'drop_w1': drop_w1, 'drop_w2': drop_w2
        }

    with col_viz:
        st.subheader("👁️ Structural Visualization")
        
        viz_tab1, viz_tab2 = st.tabs(["Plan View (Top)", "Elevation (Side)"])
        
        with viz_tab1:
            st.caption(f"Plan View: แสดงตำแหน่งเสา {col_location} และ Drop Panel")
            fig_plan = draw_plan_view(
                calc_data['L1'], calc_data['L2'], 
                calc_data['c1'], calc_data['c2'], 
                col_location, dl, ll,
                has_drop, calc_data['drop_w1'], calc_data['drop_w2']
            )
            st.pyplot(fig_plan)
            
        with viz_tab2:
            st.caption("Elevation View: แสดงความหนาพื้นและ Drop Panel")
            fig_elev = draw_elevation(
                floor_scenario, h_upper, h_lower, support_cond,
                has_drop, calc_data['h_drop'], calc_data['c1']
            )
            st.pyplot(fig_elev)
            
            # Engineering Note
            st.info(f"""
            **Engineer's Note (Calculation Logic):**
            - **Slab Thickness ($h$):** {h_slab} cm
            - **Drop Panel:** {'Yes' if has_drop else 'No'}
            {f'- Total Thickness at Drop: {h_slab} + {h_drop_val} = **{h_slab + h_drop_val} cm**' if has_drop else ''}
            
            *Effect on EFM Calculation:*
            เมื่อมี Drop Panel โปรแกรมจะต้องแบ่ง Slab Element เป็น 2 ส่วนในการหา Stiffness ($K_s$) และ Fixed End Moment (FEM) คือส่วนพื้นปกติและส่วนพื้นหนา (Inertia ต่างกัน)
            """)

with tab2:
    st.markdown("""
    ### ทฤษฎี Drop Panel ในวิธี EFM
    
    1. **ประโยชน์:** - เพิ่ม Shear Capacity (Punching Shear)
       - ลดเหล็กเสริมบริเวณหัวเสา (Negative Moment)
       - เพิ่มความแข็งแกร่ง (Stiffness) ให้โครงสร้าง
       
    2. **ข้อกำหนด ACI/EIT:**
       - ความหนา Drop Panel ใต้ท้องพื้นต้องไม่น้อยกว่า 1/4 ของความหนาพื้น
       - ระยะยื่นออกจากศูนย์กลางเสาในแต่ละทิศทาง ต้องไม่น้อยกว่า $L/6$ (หรือความกว้างรวม $L/3$)
    """)
