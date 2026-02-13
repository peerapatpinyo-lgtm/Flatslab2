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
    วาด Plan View แบบ Professional Engineering Schematic
    - แสดง Real Slab Edge vs Continuous Edge
    - จัดการ Layer (Z-order) ให้สวยงาม
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # --- 1. CONFIG & STYLES ---
    # Colors
    col_color = '#c0392b'      # สีเสา (แดงเข้ม)
    slab_fill = '#e3f2fd'      # สีพื้น (ฟ้าอ่อนมาก)
    slab_edge_col = '#2980b9'  # สีขอบพื้น
    grid_color = '#95a5a6'     # สี Grid
    drop_fill = '#f39c12'      # สี Drop Panel
    dim_color = '#2c3e50'      # สี Dimension
    
    # Z-Orders (ลำดับการซ้อนทับ)
    Z_GRID = 1
    Z_SLAB = 2
    Z_DROP = 3
    Z_COL = 4
    Z_TEXT = 5

    # --- 2. CALCULATE BOUNDARIES (Head Logic) ---
    # Center Column @ (0,0)
    # L1 Direction = X axis (Right is Next Column)
    # L2 Direction = Y axis
    
    # Default Interior Condition
    y_top = L2 / 2
    y_bot = -L2 / 2
    x_left = -1.5  # วาดเลยเสาไปทางซ้ายนิดหน่อย
    x_right = L1   # ถึงเสาถัดไป
    
    # Boundary Style Flags
    top_is_edge = False
    bot_is_edge = False
    left_is_edge = False
    
    # Logic ปรับตามตำแหน่งเสา
    if col_loc == "Edge Column":
        # สมมติ: เป็นเสาริมล่าง (Bottom Edge)
        # พื้นที่รับแรง: จากกึ่งกลางบน (L2/2) ถึง ขอบเสาล่าง (-c2/2)
        y_bot = -c2_m / 2
        bot_is_edge = True
        
    elif col_loc == "Corner Column":
        # สมมติ: เป็นเสามุมซ้ายล่าง
        # พื้นที่รับแรง: ขอบเสาล่าง ถึง กึ่งกลางบน และ ขอบเสาซ้าย ถึง กึ่งกลางขวา
        y_bot = -c2_m / 2
        x_left = -c1_m / 2
        bot_is_edge = True
        left_is_edge = True

    # Strip Width รวม
    strip_width = y_top - y_bot

    # --- 3. DRAWING LAYERS ---
    
    # A. GRID LINES (Infinite Lines)
    ax.axhline(y=0, color=grid_color, linestyle='-.', linewidth=0.8, zorder=Z_GRID)
    ax.axvline(x=0, color=grid_color, linestyle='-.', linewidth=0.8, zorder=Z_GRID)
    ax.axvline(x=L1, color=grid_color, linestyle='-.', linewidth=0.8, alpha=0.5, zorder=Z_GRID)

    # B. SLAB STRIP (Design Strip)
    # วาดสี่เหลี่ยมพื้น
    rect_slab = patches.Rectangle((x_left, y_bot), (L1 + abs(x_left) + 0.5), strip_width, 
                                  facecolor=slab_fill, edgecolor='none', alpha=0.6, zorder=Z_SLAB)
    ax.add_patch(rect_slab)
    
    # C. BOUNDARY LINES (เส้นขอบ)
    # วาดเส้นขอบตามประเภท (ทึบ = Edge, ประ = Continuous)
    
    # Top Line
    ax.plot([x_left, L1+0.5], [y_top, y_top], color=slab_edge_col, 
            linestyle='-' if top_is_edge else '--', linewidth=2 if top_is_edge else 1, zorder=Z_SLAB)
    # Bottom Line
    ax.plot([x_left, L1+0.5], [y_bot, y_bot], color=slab_edge_col, 
            linestyle='-' if bot_is_edge else '--', linewidth=2 if bot_is_edge else 1, zorder=Z_SLAB)
    # Left Line
    ax.plot([x_left, x_left], [y_bot, y_top], color=slab_edge_col, 
            linestyle='-' if left_is_edge else '--', linewidth=2 if left_is_edge else 1, zorder=Z_SLAB)

    # D. DROP PANEL (With Clipping Logic)
    if has_drop:
        # คำนวณขอบ Drop Panel ปกติ
        d_top = drop_w2/2
        d_bot = -drop_w2/2
        d_left = -drop_w1/2
        d_right = drop_w1/2
        
        # Clip Drop Panel ไม่ให้เกินขอบ Slab
        if d_top > y_top: d_top = y_top
        if d_bot < y_bot: d_bot = y_bot
        if d_left < x_left: d_left = x_left
        
        d_h = d_top - d_bot
        d_w = d_right - d_left
        
        drop_rect = patches.Rectangle((d_left, d_bot), d_w, d_h,
                                      facecolor=drop_fill, edgecolor='#d35400', 
                                      alpha=0.5, linestyle='--', zorder=Z_DROP)
        ax.add_patch(drop_rect)
        
        # Label Drop
        ax.text(0, d_bot - 0.3, f"Drop {drop_w1}x{drop_w2}m", 
                ha='center', va='top', fontsize=8, color='#d35400', zorder=Z_TEXT)

    # E. COLUMNS
    # Main Column (Center)
    col_main = patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                 facecolor=col_color, edgecolor='black', hatch='///', zorder=Z_COL)
    ax.add_patch(col_main)
    
    # Next Column (Ghost - แสดงเพื่อให้รู้ว่า L1 ไปจบที่ไหน)
    if col_loc != "Corner Column": # Corner ปกติมีด้านเดียว แต่ EFM assume frame ต่อไป
        col_next = patches.Rectangle((L1 - c1_m/2, -c2_m/2), c1_m, c2_m, 
                                     facecolor='white', edgecolor='gray', linestyle=':', alpha=0.5, zorder=Z_COL)
        ax.add_patch(col_next)
        ax.text(L1, 0, "Next\nCol", ha='center', va='center', fontsize=7, color='gray', zorder=Z_TEXT)

    # --- 4. DIMENSIONS (Clean & Offset) ---
    
    # L1 (Horizontal) - วาดด้านล่าง
    dim_y_pos = y_bot - 1.0 # ขยับลงมาจากขอบล่าง
    ax.annotate('', xy=(0, dim_y_pos), xytext=(L1, dim_y_pos),
                arrowprops=dict(arrowstyle='<|-|>', color='blue', linewidth=1.5))
    ax.text(L1/2, dim_y_pos + 0.1, f"L1 (Span) = {L1:.2f} m", 
            ha='center', color='blue', fontweight='bold', zorder=Z_TEXT)
    
    # Connector Lines for L1
    ax.plot([0, 0], [-c2_m/2, dim_y_pos], color='gray', linestyle=':', linewidth=0.5)
    ax.plot([L1, L1], [-c2_m/2, dim_y_pos], color='gray', linestyle=':', linewidth=0.5)

    # L2 (Vertical) - วาดด้านซ้าย
    dim_x_pos = x_left - 0.5 # ขยับซ้าย
    
    # Arrow for Total Width
    ax.annotate('', xy=(dim_x_pos, y_bot), xytext=(dim_x_pos, y_top),
                arrowprops=dict(arrowstyle='<|-|>', color='green', linewidth=1.5))
    ax.text(dim_x_pos - 0.1, (y_top+y_bot)/2, f"L2 (Width) = {strip_width:.2f} m", 
            va='center', ha='right', rotation=90, color='green', fontweight='bold', zorder=Z_TEXT)

    # Sub-dimensions (Components of L2)
    # เช่นบอกว่า L2/2 หรือ Edge Distance
    if col_loc == "Edge Column":
        ax.text(dim_x_pos + 0.2, y_top/2, "L2/2", fontsize=8, color='green', ha='center', alpha=0.7)
        ax.text(dim_x_pos + 0.2, y_bot/2, "Edge", fontsize=8, color='green', ha='center', alpha=0.7)

    # --- 5. FINISHING ---
    ax.set_title(f"EFM Plan View: {col_loc}\n(Showing Analysis Strip)", fontweight='bold', pad=15)
    
    # Load Info Box
    wu = 1.4*dl + 1.7*ll
    info_text = f"DESIGN LOADS ($w_u$)\nTotal = {wu:.2f} kg/m²"
    ax.text(L1*0.7, y_top + 0.5, info_text, fontsize=9, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9), zorder=Z_TEXT)

    # Set Aspect Ratio & Limits
    ax.set_aspect('equal')
    ax.set_xlim(x_left - 1.5, L1 + 1.5)
    ax.set_ylim(y_bot - 1.5, y_top + 1.5)
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
