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
    วาด Plan View แบบ Correct EFM Boundary Condition
    แสดง L2 (Design Strip Width) ที่ถูกต้องตามตำแหน่งเสา (Interior/Edge/Corner)
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # --- 1. DEFINITIONS & LOGIC ---
    # Center Column อยู่ที่ (0,0) เสมอ
    # L1 Direction = แกน X (Analysis Direction)
    # L2 Direction = แกน Y (Transverse Direction)
    
    # ตัวแปรสำหรับวาดขอบเขตพื้น (Slab Boundaries)
    y_top = 0.0   # ขอบบน
    y_bot = 0.0   # ขอบล่าง
    x_left = 0.0  # ขอบซ้าย (จุดเริ่ม)
    
    # Logic การกำหนดขอบเขตตามประเภทเสา
    if col_loc == "Interior Column":
        # เสากลาง: รับพื้นจากกึ่งกลางถึงกึ่งกลาง (Mid-span to Mid-span)
        # พื้นที่รับผิดชอบ = L2 เต็มๆ (L2/2 บน + L2/2 ล่าง)
        y_top = L2 / 2
        y_bot = -L2 / 2
        x_left = -1.0 # วาดเลยไปหน่อยให้เห็นความต่อเนื่อง
        
        l2_text_top = "L2/2 (To Mid-span)"
        l2_text_bot = "L2/2 (To Mid-span)"
        edge_style = '--' # เส้นประ (ต่อเนื่อง)

    elif col_loc == "Edge Column":
        # เสาริม (สมมติริมล่าง พื้นอยู่ด้านบน)
        # รับพื้นจากกึ่งกลาง Span บน (L2/2) ถึง ขอบอาคารล่าง (c2/2)
        y_top = L2 / 2
        y_bot = -c2_m / 2 # สุดที่ผิวเสา (Edge of Slab)
        x_left = -1.0 # L1 ต่อเนื่องซ้ายขวา
        
        l2_text_top = "L2/2 (To Mid-span)"
        l2_text_bot = "Edge (c2/2)"
        edge_style = '-' # เส้นทึบ (สุดขอบปูน)

    elif col_loc == "Corner Column":
        # เสาเข้ามุม (สมมติมุมซ้ายล่าง)
        # รับพื้นจากกึ่งกลาง Span บน (L2/2) ถึง ขอบอาคารล่าง
        # และจากขอบอาคารซ้าย ถึง กึ่งกลาง Span ขวา (L1)
        y_top = L2 / 2
        y_bot = -c2_m / 2 # สุดที่ผิวเสาล่าง
        x_left = -c1_m / 2 # สุดที่ผิวเสาซ้าย
        
        l2_text_top = "L2/2"
        l2_text_bot = "Edge"
        edge_style = '-'

    # คำนวณความกว้างรวมของ Strip ที่ใช้คำนวณจริง (Total Strip Width)
    strip_width = y_top - y_bot

    # --- 2. DRAWING LAYERS ---
    
    # A. The Slab Strip (Design Strip)
    # วาดสี่เหลี่ยมตามขอบเขตที่คำนวณมา
    rect_slab = patches.Rectangle((x_left, y_bot), (L1 + abs(x_left) + 0.5), strip_width, 
                                  facecolor='#e3f2fd', edgecolor='blue', 
                                  linestyle=edge_style, linewidth=1.5, alpha=0.5, label='Design Strip')
    ax.add_patch(rect_slab)

    # B. Grid Lines (Center Lines)
    ax.axhline(y=0, color='gray', linestyle='-.', linewidth=1)
    ax.axvline(x=0, color='gray', linestyle='-.', linewidth=1)
    ax.axvline(x=L1, color='gray', linestyle='-.', linewidth=1, alpha=0.5)

    # C. Drop Panel (ถ้ามี)
    if has_drop:
        # Drop Panel ก็ต้องถูกตัดถ้าอยู่ที่ Edge/Corner
        # แต่เพื่อความง่ายในการมอง วาดเต็มไปก่อน แล้ว Clip ด้วยความคิด หรือวาดตัด
        # Logic: วาด Drop ปกติ แต่ถ้ายื่นเกิน Edge ให้ตัดทิ้ง (Visual Clip)
        
        drop_y_min = -drop_w2/2
        drop_y_max = drop_w2/2
        
        # Adjust for Edge condition visually
        if col_loc != "Interior Column":
             if drop_y_min < y_bot: drop_y_min = y_bot # ไม่ให้ Drop เกินขอบปูน
        
        final_drop_h = drop_y_max - drop_y_min
        
        drop_rect = patches.Rectangle((-drop_w1/2, drop_y_min), drop_w1, final_drop_h,
                                      facecolor='#f39c12', edgecolor='#d35400', alpha=0.6, linestyle='--')
        ax.add_patch(drop_rect)

    # D. Column (Center)
    col_rect = patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                 facecolor='#c0392b', edgecolor='black', hatch='///', zorder=5)
    ax.add_patch(col_rect)
    
    # Next Column (Ghost)
    if col_loc != "Corner Column" or True: # Corner ก็มีเสาถัดไปทางขวา
        next_col = patches.Rectangle((L1 - c1_m/2, -c2_m/2), c1_m, c2_m, 
                                     facecolor='white', edgecolor='black', linestyle=':', alpha=0.5, zorder=5)
        ax.add_patch(next_col)

    # --- 3. DIMENSIONS & ANNOTATIONS (The Correction) ---
    
    # L1 Span
    ax.annotate('', xy=(0, 0), xytext=(L1, 0), arrowprops=dict(arrowstyle='<|-|>', color='blue'))
    ax.text(L1/2, 0.1, f"L1 Span = {L1}m", color='blue', ha='center', fontweight='bold')

    # L2 Width Components (สำคัญมาก!)
    # แสดงระยะย่อยด้านข้างเพื่อบอกที่มาของความกว้าง Strip
    dim_x = -1.2 if col_loc == "Interior Column" else -0.8
    
    # Arrow Top (L2/2)
    ax.annotate('', xy=(dim_x, 0), xytext=(dim_x, y_top), arrowprops=dict(arrowstyle='<|-|>', color='green'))
    ax.text(dim_x - 0.1, y_top/2, l2_text_top, rotation=90, va='center', ha='right', color='green', fontsize=9)
    
    # Arrow Bottom (L2/2 or Edge)
    ax.annotate('', xy=(dim_x, 0), xytext=(dim_x, y_bot), arrowprops=dict(arrowstyle='<|-|>', color='green'))
    ax.text(dim_x - 0.1, y_bot/2, l2_text_bot, rotation=90, va='center', ha='right', color='green', fontsize=9)

    # Summary Text
    ax.text(L1*0.6, y_top + 0.5, 
            f"DESIGN STRIP WIDTH (Frame Width):\n"
            f"= {strip_width:.2f} m\n"
            f"({col_loc} Condition)", 
            fontsize=10, fontweight='bold', bbox=dict(facecolor='white', edgecolor='green'))

    # Setup View
    ax.set_title(f"EFM Plan View: {col_loc}\n(Correct Transverse Width)", fontweight='bold')
    ax.set_xlim(-2, L1+1)
    ax.set_ylim(y_bot - 1, y_top + 1)
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
