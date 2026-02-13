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
    วาด Plan View แบบ Engineering Schematic
    แสดง Grid Line และระยะ Center-to-Center เพื่อไม่ให้สับสน
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # --- 1. SETTINGS ---
    # สีและสไตล์
    col_color = '#c0392b'      # สีเสา
    drop_color = '#f39c12'     # สี Drop Panel
    slab_color = '#ecf0f1'     # สีพื้น
    grid_color = '#7f8c8d'     # สี Grid Line
    dim_color = '#2980b9'      # สีเส้นบอกระยะ
    
    # --- 2. COORDINATES (Center at Main Column 0,0) ---
    # เราจะวาดเสาหลักที่ (0,0) และเสาข้างเคียง (Ghost) เพื่ออ้างอิงระยะ
    
    # กำหนดขอบเขต Slab (Tributary Area) ตาม Location
    # Interior: -L1/2 ถึง L1/2
    # Edge: เริ่มที่ 0 ถึง L1/2 (หรือตามระยะที่กำหนด)
    
    # เพื่อความเข้าใจง่ายใน EFM เราจะวาด "Full Design Strip" (กว้าง L2, ยาว L1)
    # โดยให้เสาหลักอยู่ทางซ้าย (Start Node) และเสาถัดไปอยู่ทางขวา (End Node)
    
    # ** จุดสำคัญ: EFM วิเคราะห์ทีละช่วง (Span) **
    # เราจะวาด Span L1 เต็มๆ คือจาก (0,0) ถึง (L1, 0)
    
    # ขอบเขตความกว้าง Design Strip (L2)
    y_top = L2 / 2
    y_bot = -L2 / 2
    
    # --- 3. DRAWING LAYERS ---
    
    # A. The Design Strip (Slab) - พื้นที่รับแรง
    # วาดสี่เหลี่ยมคลุม Span L1 และกว้าง L2
    # ถ้าเป็น Interior เราวาดเกินไปทางซ้ายนิดหน่อยเพื่อให้เห็นความต่อเนื่อง
    extension = 1.0 # เมตร (ระยะเลยเสาออกไป)
    
    if col_loc == "Corner Column":
        rect_slab = patches.Rectangle((-c1_m/2, -c2_m/2), L1 + c1_m, L2/2 + c2_m, 
                                      facecolor=slab_color, edgecolor='gray', alpha=0.5)
    elif col_loc == "Edge Column":
        # สมมติ Edge อยู่ซ้าย
        rect_slab = patches.Rectangle((-c1_m/2, -L2/2), L1 + c1_m, L2, 
                                      facecolor=slab_color, edgecolor='gray', alpha=0.5)
    else: # Interior
        # วาด Strip ยาวคลุม 2 เสา
        rect_slab = patches.Rectangle((-extension, -L2/2), L1 + extension*2, L2, 
                                      facecolor=slab_color, edgecolor='gray', alpha=0.5)

    ax.add_patch(rect_slab)
    
    # B. Grid Lines (Center Lines)
    # Main Grid X (Horizontal)
    ax.axhline(y=0, color=grid_color, linestyle='-.', linewidth=0.8)
    # Main Grid Y (Vertical at Origin)
    ax.axvline(x=0, color=grid_color, linestyle='-.', linewidth=0.8)
    # Next Grid Y (Vertical at L1)
    ax.axvline(x=L1, color=grid_color, linestyle='-.', linewidth=0.8, alpha=0.6)
    
    # C. Drop Panels (ถ้ามี)
    if has_drop:
        # Drop ที่เสาหลัก (0,0)
        drop1 = patches.Rectangle((-drop_w1/2, -drop_w2/2), drop_w1, drop_w2,
                                  facecolor=drop_color, edgecolor='#d35400', alpha=0.4, linestyle='--')
        ax.add_patch(drop1)
        ax.text(0, -drop_w2/2 - 0.2, f"Drop Size\n{drop_w1}x{drop_w2}m", 
                ha='center', va='top', fontsize=8, color='#d35400')
        
        # Drop ที่เสาถัดไป (L1, 0) - แสดงเพื่อให้เห็นภาพรวม
        drop2 = patches.Rectangle((L1 - drop_w1/2, -drop_w2/2), drop_w1, drop_w2,
                                  facecolor=drop_color, edgecolor='#d35400', alpha=0.4, linestyle='--')
        ax.add_patch(drop2)

    # D. Columns (เสา)
    # เสาหลัก (Main Column) ที่ (0,0)
    col1 = patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                             facecolor=col_color, edgecolor='black', hatch='///', zorder=10)
    ax.add_patch(col1)
    
    # เสาถัดไป (Next Column) ที่ (L1, 0) - วาดแบบจางๆ (Ghost)
    col2 = patches.Rectangle((L1 - c1_m/2, -c2_m/2), c1_m, c2_m, 
                             facecolor='white', edgecolor='black', linestyle='--', alpha=0.7, zorder=10)
    ax.add_patch(col2)
    ax.text(L1, 0, "Next\nCol", ha='center', va='center', fontsize=8, color='gray')

    # --- 4. DIMENSIONS (Engineering Style) ---
    
    # L1 Dimension (Longitudinal) - Span ระหว่างเสา
    ax.annotate('', xy=(0, 0), xytext=(L1, 0),
                arrowprops=dict(arrowstyle='<|-|>', color=dim_color, linewidth=1.5))
    
    # Label L1 ตรงกลางเส้น
    ax.text(L1/2, 0.2, f"L1 (Span) = {L1:.2f} m", 
            ha='center', va='bottom', color=dim_color, fontweight='bold', backgroundcolor='white')

    # L2 Dimension (Transverse) - ความกว้าง Strip
    # วาดด้านข้างเพื่อไม่ให้รก
    dim_x_pos = -0.8 # ขยับออกไปทางซ้าย
    ax.annotate('', xy=(dim_x_pos, -L2/2), xytext=(dim_x_pos, L2/2),
                arrowprops=dict(arrowstyle='<|-|>', color='green', linewidth=1.5))
    ax.text(dim_x_pos - 0.1, 0, f"L2 (Width) = {L2:.2f} m", 
            ha='right', va='center', rotation=90, color='green', fontweight='bold')

    # --- 5. INFO BOX ---
    wu = 1.4*dl + 1.7*ll
    info_text = (
        f"DESIGN PARAMETERS:\n"
        f"------------------\n"
        f"Span (L1) : {L1:.2f} m (c/c)\n"
        f"Width (L2): {L2:.2f} m\n"
        f"Load (Wu) : {wu:.2f} kg/m²"
    )
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
    ax.text(L1*0.5, -L2/2 + 0.5, info_text, fontsize=9, bbox=props, ha='center')

    # Final Config
    ax.set_title(f"Equivalent Frame Model: {col_loc}", fontweight='bold', pad=15)
    
    # Set Limits ให้สวยงาม
    ax.set_xlim(-1.5, L1 + 1.5)
    ax.set_ylim(-L2/2 - 1, L2/2 + 1)
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
