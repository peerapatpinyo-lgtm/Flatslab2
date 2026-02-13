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
    วาด Plan View แบบ Grid Intersection (4 ด้าน)
    แสดง Design Strip ที่ถูกต้องตามหลัก EFM
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # --- 1. SETTINGS & STYLES ---
    grid_color = '#95a5a6'    # สีเส้น Grid
    strip_color = '#e3f2fd'   # สี Design Strip (สีฟ้าอ่อน)
    col_color = '#c0392b'     # สีเสา (แดงเข้ม)
    dim_color = '#2980b9'     # สี Dimension
    
    # --- 2. LAYOUT LOGIC ---
    # Center Column อยู่ที่ (0,0)
    # เราจะแสดง Design Strip ตามแกน X (Analysis Direction)
    # ความยาวแสดง L1 เต็ม Span, ความกว้างแสดง L2 เต็ม Width
    
    # ขอบเขตภาพ (Limits)
    x_margin = 1.5
    y_margin = 1.5
    
    # --- 3. DRAWING: DESIGN STRIP (L2 Width) ---
    # นี่คือ "แถบพื้น" ที่เรากำลังวิเคราะห์
    # กว้าง L2 (จาก -L2/2 ถึง L2/2)
    # ยาว L1 (จาก 0 ถึง L1) -> จริงๆ Strip ยาวต่อเนื่อง แต่เรา Focus ช่วงนี้
    
    # วาดพื้น (Slab Strip)
    # เราวาดเลยออกไปทางซ้ายนิดหน่อย (-1m) เพื่อแสดงความต่อเนื่อง
    rect_strip = patches.Rectangle((-1.0, -L2/2), L1 + 2.0, L2, 
                                   facecolor=strip_color, edgecolor='none', alpha=0.6, label='Design Strip')
    ax.add_patch(rect_strip)
    
    # วาดเส้นขอบเขตความกว้าง L2 (Transverse Boundaries)
    ax.axhline(y=L2/2, color='blue', linestyle='--', linewidth=0.8, alpha=0.5)  # ขอบบน
    ax.axhline(y=-L2/2, color='blue', linestyle='--', linewidth=0.8, alpha=0.5) # ขอบล่าง
    
    # --- 4. DRAWING: GRID SYSTEM (4 Sides) ---
    # Center Grid Lines (Main Axes)
    ax.axvline(x=0, color=grid_color, linestyle='-.', linewidth=1.2) # แกน Y ตัดผ่านเสา
    ax.axhline(y=0, color=grid_color, linestyle='-.', linewidth=1.2) # แกน X ตัดผ่านเสา
    
    # Next Column Grid Line (ที่ระยะ L1)
    ax.axvline(x=L1, color=grid_color, linestyle='-.', linewidth=1.0, alpha=0.6)
    
    # --- 5. DRAWING: DROP PANELS ---
    if has_drop:
        # Drop ที่เสาหลัก (0,0)
        # Drop Panel ก็ต้อง Center ที่เสา
        drop_rect = patches.Rectangle((-drop_w1/2, -drop_w2/2), drop_w1, drop_w2,
                                      facecolor='#f39c12', edgecolor='#d35400', alpha=0.5, linestyle='--')
        ax.add_patch(drop_rect)
        
        # Label Drop
        ax.text(drop_w1/2 + 0.1, drop_w2/2, f"Drop {drop_w1}x{drop_w2}m", 
                fontsize=8, color='#d35400', va='bottom')

    # --- 6. DRAWING: COLUMNS ---
    # เสาหลัก (Center)
    main_col = patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                 facecolor=col_color, edgecolor='black', hatch='///', zorder=10)
    ax.add_patch(main_col)
    
    # เสาต้นถัดไป (Ghost Column ที่ระยะ L1)
    next_col = patches.Rectangle((L1 - c1_m/2, -c2_m/2), c1_m, c2_m, 
                                 facecolor='white', edgecolor='black', linestyle=':', alpha=0.5, zorder=10)
    ax.add_patch(next_col)

    # --- 7. DIMENSIONS (Engineering Standard) ---
    
    # A. Span L1 (Analysis Direction)
    # วาดลูกศรบอกระยะระหว่าง Center เสา
    ax.annotate('', xy=(0, 0.5), xytext=(L1, 0.5),
                arrowprops=dict(arrowstyle='<|-|>', color=dim_color, linewidth=1.5))
    ax.text(L1/2, 0.6, f"L1 (Analysis Span) = {L1:.2f} m", 
            ha='center', va='bottom', color=dim_color, fontweight='bold')

    # B. Width L2 (Transverse Direction)
    # ต้องโชว์ว่า L2 คือความกว้างรวม (บน+ล่าง)
    # วาด Dimension ทางด้านซ้ายของเสาหลัก
    dim_x = -0.8
    ax.annotate('', xy=(dim_x, -L2/2), xytext=(dim_x, L2/2),
                arrowprops=dict(arrowstyle='<|-|>', color='green', linewidth=1.5))
    
    # Label L2 (หมุน 90 องศา)
    ax.text(dim_x - 0.1, 0, f"L2 (Design Strip Width) = {L2:.2f} m", 
            ha='right', va='center', rotation=90, color='green', fontweight='bold')
            
    # เพิ่มเส้น Sub-dimension เพื่อบอกว่ามาจาก 4 ด้าน (L2/2 + L2/2)
    # ถ้าเป็น Interior Column ปกติ L2 จะแบ่งครึ่งบนล่างเท่ากัน
    ax.text(dim_x + 0.2, L2/4, f"L2/2", fontsize=8, color='green', ha='center', alpha=0.7)
    ax.text(dim_x + 0.2, -L2/4, f"L2/2", fontsize=8, color='green', ha='center', alpha=0.7)

    # --- 8. INFO & CONTEXT ---
    # Title
    ax.set_title(f"Equivalent Frame Model: {col_loc}\n(Showing Analysis Strip)", fontweight='bold')
    
    # Loads Box
    wu = 1.4*dl + 1.7*ll
    info_text = f"LOADS ($w_u$)\nTotal = {wu:.2f} kg/m²"
    ax.text(L1*0.8, -L2/2 + 0.5, info_text, fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Set Axis Limits
    ax.set_xlim(-1.5, L1 + 1.0)
    ax.set_ylim(-L2/2 - 1.0, L2/2 + 1.0)
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
