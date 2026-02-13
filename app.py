import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design", layout="wide")

# ==============================================================================
# 🧱 UNIT CONVERSION SYSTEM & LOGIC
# ==============================================================================
calc_data = {} 

# --- Function วาด Plan View (Top View) [UPDATED] ---

def draw_plan_view(L1, L2, c1_m, c2_m, col_loc, dl, ll, has_drop, drop_w1, drop_w2):
    """
    วาด Plan View แบบ Full Grid Geometry (4 Quadrants)
    ตามภาพวาดสีเหลือง: แสดง L1-1, L1-2, L2-1, L2-2
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # --- 1. SETUP PARAMETERS ---
    # แปลง input L1, L2 ให้เป็นแขน 4 ด้าน
    # สมมติว่า L1 ที่ input มาคือ "Analysis Span" (Right side)
    # ส่วน Left side ถ้าเป็น Interior ให้สมมติว่าเท่ากัน (หรือรับค่าเพิ่มในอนาคต)
    
    L1_right = L1         # L1-2
    L1_left  = L1         # L1-1 (สมมติเท่ากันเพื่อให้เห็นภาพ Grid)
    
    L2_top   = L2 / 2     # L2-1
    L2_bot   = L2 / 2     # L2-2
    
    # ถ้าเป็น Edge/Corner ให้ตัดแขนบางข้างออก
    if col_loc == "Edge Column":
        # สมมติ Edge ล่าง: ไม่มี L2_bot
        L2_bot = c2_m / 2 # สุดแค่ขอบเสา
    elif col_loc == "Corner Column":
        # สมมติ Corner ซ้ายล่าง: ไม่มี L1_left และ L2_bot
        L1_left = c1_m / 2
        L2_bot = c2_m / 2

    # --- 2. DRAWING GRID & AXES ---
    grid_color = '#7f8c8d'
    
    # เส้น Grid ยาวทะลุ
    ax.axhline(y=0, color=grid_color, linestyle='-.', linewidth=1)
    ax.axvline(x=0, color=grid_color, linestyle='-.', linewidth=1)
    
    # เส้น Grid ของเสาข้างเคียง (Boundaries)
    ax.axvline(x=L1_right, color=grid_color, linestyle=':', alpha=0.5)
    if col_loc == "Interior Column":
        ax.axvline(x=-L1_left, color=grid_color, linestyle=':', alpha=0.5)

    # --- 3. DRAWING SLAB AREA (Design Strip) ---
    # วาดพื้นที่สีฟ้าจางๆ คลุมพื้นที่
    slab_rect = patches.Rectangle((-L1_left, -L2_bot), L1_left + L1_right, L2_bot + L2_top,
                                  facecolor='#e3f2fd', edgecolor='blue', 
                                  linestyle='--', alpha=0.4, zorder=1)
    ax.add_patch(slab_rect)

    # --- 4. DRAWING COLUMNS ---
    # Center Column (Main)
    main_col = patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                 facecolor='#c0392b', edgecolor='black', hatch='///', zorder=10)
    ax.add_patch(main_col)
    
    # Ghost Columns (เพื่อบอกตำแหน่งเสาต้นถัดไป)
    # Right Col
    right_col = patches.Rectangle((L1_right - c1_m/2, -c2_m/2), c1_m, c2_m, 
                                  facecolor='white', edgecolor='gray', linestyle=':', zorder=5)
    ax.add_patch(right_col)
    
    if col_loc == "Interior Column":
        # Left Col
        left_col = patches.Rectangle((-L1_left - c1_m/2, -c2_m/2), c1_m, c2_m, 
                                     facecolor='white', edgecolor='gray', linestyle=':', zorder=5)
        ax.add_patch(left_col)

    # --- 5. DROP PANEL (ถ้ามี) ---
    if has_drop:
        # วาด Drop Center ที่ (0,0)
        drop = patches.Rectangle((-drop_w1/2, -drop_w2/2), drop_w1, drop_w2,
                                 facecolor='#f39c12', edgecolor='#d35400', alpha=0.5, linestyle='--', zorder=8)
        ax.add_patch(drop)

    # --- 6. DIMENSIONS (ตามภาพวาดสีเหลือง) ---
    # Style ของเส้น Dimension
    arrow_props = dict(arrowstyle='<|-|>', color='#f1c40f', linewidth=2.5) # สีเหลืองตามรูป
    text_props = dict(ha='center', va='center', fontsize=12, fontweight='bold', 
                      color='#d35400', backgroundcolor='white')
    
    dim_offset = 1.0 # ระยะห่างเส้นบอกระยะจากเสา

    # >>> L1-2 (Right Span)
    ax.annotate('', xy=(0, -dim_offset), xytext=(L1_right, -dim_offset), arrowprops=arrow_props)
    ax.text(L1_right/2, -dim_offset, f"L1-2 = {L1_right} m", **text_props)
    
    # >>> L1-1 (Left Span) - แสดงเฉพาะ Interior
    if col_loc == "Interior Column":
        ax.annotate('', xy=(-L1_left, -dim_offset), xytext=(0, -dim_offset), arrowprops=arrow_props)
        ax.text(-L1_left/2, -dim_offset, f"L1-1 = {L1_left} m", **text_props)

    # >>> L2-1 (Top Width)
    ax.annotate('', xy=(-dim_offset, 0), xytext=(-dim_offset, L2_top), arrowprops=arrow_props)
    ax.text(-dim_offset, L2_top/2, f"L2-1\n{L2_top}m", rotation=90, **text_props)
    
    # >>> L2-2 (Bottom Width)
    ax.annotate('', xy=(-dim_offset, 0), xytext=(-dim_offset, -L2_bot), arrowprops=arrow_props)
    ax.text(-dim_offset, -L2_bot/2, f"L2-2\n{L2_bot}m", rotation=90, **text_props)

    # --- 7. FINAL SETTINGS ---
    ax.set_title(f"Full Frame Geometry: {col_loc}", fontsize=14, fontweight='bold')
    
    # Limits (เผื่อที่ให้ Dimension)
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
        # Drop panel ใต้ท้องพื้น
        drop_w_view = 1.0 # สมมติความกว้างใน view นี้เพื่อการแสดงผล
        ax.add_patch(patches.Rectangle((-drop_w_view/2, -0.1 - h_drop), drop_w_view, h_drop, color='#f39c12', alpha=0.8))
        ax.text(0.6, -0.1 - h_drop/2, f"Drop +{h_drop*100:.0f}cm", fontsize=8, color='#d35400')

    col_width = c1_m # ใช้ความกว้างจริงตามสเกล
    
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
        h_slab = st.number_input("Slab Thickness (cm)", value=20)
        
        c1_geo, c2_geo = st.columns(2)
        with c1_geo:
            L1 = st.number_input("Span L1 (Analysis) (m)", value=6.0)
            c1 = st.number_input("Column c1 (cm)", value=40.0)
        with c2_geo:
            L2 = st.number_input("Span L2 (Transverse) (m)", value=6.0)
            c2 = st.number_input("Column c2 (cm)", value=40.0)

        # --- ส่วนที่เพิ่ม Drop Panel ---
        st.markdown("---")
        st.write("#### 🔸 Drop Panel Configuration")
        has_drop = st.checkbox("Has Drop Panel?", value=False)
        
        h_drop_val = 0.0
        drop_w1, drop_w2 = 0.0, 0.0
        
        if has_drop:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                h_drop_val = st.number_input("Drop Projection (cm)", value=15.0, help="ความหนาที่ยื่นลงมาจากท้องพื้น (ไม่รวมพื้นเดิม)")
                drop_w1 = st.number_input("Drop Size L1 (m)", value=2.5)
            with col_d2:
                st.write("") # Spacer
                st.write("")
                drop_w2 = st.number_input("Drop Size L2 (m)", value=2.5)
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
       - ระยะยื่นออกจากศูนย์กลางเสาในแต่ละทิศทาง ต้องไม่น้อยกว่า $L/6$
    """)
