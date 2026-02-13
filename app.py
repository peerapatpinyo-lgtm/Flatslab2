import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design", layout="wide")

# ==============================================================================
# 🧱 UNIT CONVERSION SYSTEM (ระบบแปลงหน่วยมาตรฐาน)
# ==============================================================================
# เราจะสร้าง Dictionary เพื่อเก็บค่าที่ "พร้อมคำนวณ" (Converted Values)
# กฎ: Length = Meter, Force = kg, Stress = kg/m^2
calc_data = {} 

# --- Function วาด Plan View (Top View) ---
def draw_plan_view(L1, L2, c1_m, c2_m, col_loc, dl, ll):
    """
    วาดแปลนพื้นพร้อมระบุ Load และตำแหน่งเสา
    L1, L2, c1, c2 : หน่วยเมตร
    """
    fig, ax = plt.subplots(figsize=(6, 5))
    
    # 1. วาดขอบเขตพื้นที่รับผิดชอบ (Tributary Area / Panel)
    # สมมติวาดแค่ครึ่ง span รอบเสา หรือ 1 Panel เต็มๆ
    # เพื่อความง่ายใน EFM เรามักมอง Span L1 (Analysis) กับ L2 (Transverse)
    
    # สร้างกรอบ Panel
    rect = patches.Rectangle((0, 0), L1, L2, linewidth=2, edgecolor='#2c3e50', facecolor='#ecf0f1', alpha=0.5)
    ax.add_patch(rect)
    
    # 2. วาดเสา (ตามตำแหน่ง)
    col_x, col_y = 0, 0 # Default Center
    
    # ปรับตำแหน่งเสาตาม Location (เพื่อให้เห็นภาพจริง)
    if col_loc == "Corner Column":
        col_origin = (0, 0) # มุมซ้ายล่าง
        ax.text(0.2, 0.2, "Corner Col", color='red', fontweight='bold')
    elif col_loc == "Edge Column":
        col_origin = (0, L2/2 - c2_m/2) # กึ่งกลางด้านซ้าย
        ax.text(0.2, L2/2, "Edge Col", color='red', fontweight='bold')
    else: # Interior
        col_origin = (L1/2 - c1_m/2, L2/2 - c2_m/2) # กึ่งกลางแผ่น
        ax.text(L1/2, L2/2 + c2_m, "Interior Col", ha='center', color='red', fontweight='bold')

    # วาดเสา
    col_patch = patches.Rectangle(col_origin, c1_m, c2_m, color='red', alpha=0.8)
    ax.add_patch(col_patch)
    
    # 3. ใส่ Dimension
    # L1 Dimension (แนวนอน)
    ax.annotate('', xy=(0, -0.5), xytext=(L1, -0.5), arrowprops=dict(arrowstyle='<->', color='blue'))
    ax.text(L1/2, -0.8, f"L1 (Analysis) = {L1:.2f} m", ha='center', color='blue')

    # L2 Dimension (แนวตั้ง)
    ax.annotate('', xy=(-0.5, 0), xytext=(-0.5, L2), arrowprops=dict(arrowstyle='<->', color='green'))
    ax.text(-0.8, L2/2, f"L2 (Transverse) = {L2:.2f} m", va='center', rotation=90, color='green')

    # 4. ระบุ Load ตรงกลางแผ่น
    info_text = (
        f"DESIGN LOADS:\n"
        f"SDL = {dl} kg/m²\n"
        f"LL  = {ll} kg/m²\n"
        f"Total = {dl+ll} kg/m²"
    )
    # วาดกล่องข้อความ
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(L1*0.7, L2*0.8, info_text, fontsize=10, verticalalignment='top', bbox=props)

    ax.set_xlim(-1.5, L1 + 1)
    ax.set_ylim(-1.5, L2 + 1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Plan View: {col_loc}", fontweight='bold')
    
    return fig

# --- Function วาดรูปตัด (Elevation) - ตัวเดิมที่ปรับปรุงแล้ว ---
def draw_elevation(scenario, h_upper, h_lower, support_cond):
    fig, ax = plt.subplots(figsize=(3, 4))
    ax.add_patch(patches.Rectangle((-1, -0.1), 2, 0.2, color='gray', alpha=0.5)) # Slab
    ax.text(1.1, 0, "Slab", va='center')
    col_width = 0.2
    
    if scenario != "Top Floor (Roof)":
        ax.add_patch(patches.Rectangle((-col_width/2, 0.1), col_width, 1.5, color='#3498db')) # Upper
        ax.text(0.2, 0.8, f"Upper: {h_upper}m", fontsize=8, color='blue')

    ax.add_patch(patches.Rectangle((-col_width/2, -1.6), col_width, 1.5, color='#e74c3c')) # Lower
    
    if scenario == "Foundation/First Floor":
        ax.text(0.2, -0.8, f"Lower: {h_lower}m", fontsize=8, color='red')
        if support_cond == "Fixed":
            ax.add_patch(patches.Rectangle((-0.4, -1.7), 0.8, 0.1, color='black')) # Base
            ax.text(0, -1.9, "FIXED", ha='center', fontsize=8, fontweight='bold')
        else: 
            ax.plot(0, -1.6, marker='^', markersize=10, color='black') # Pinned
            ax.text(0, -1.9, "PINNED", ha='center', fontsize=8, fontweight='bold')
    else:
        ax.text(0.2, -0.8, f"Lower: {h_lower}m", fontsize=8, color='red')

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-2.2, 2.0)
    ax.axis('off')
    return fig

# --- 2. Main Interface ---
st.title("🏗️ Flat Slab Design: Equivalent Frame Method")

# Layout แบ่งซ้ายขวา (Input | Visualization)
tab1, tab2 = st.tabs(["📝 Input Parameters", "📘 Theory & Manual"])

with tab1:
    col_input, col_viz = st.columns([1, 1.2])

    with col_input:
        st.subheader("1. Material & Loads")
        fc = st.number_input("f'c (ksc)", value=240)
        fy = st.number_input("fy (ksc)", value=4000)
        dl = st.number_input("Superimposed Dead Load (SDL) (kg/m²)", value=100)
        ll = st.number_input("Live Load (LL) (kg/m²)", value=200)
        
        st.subheader("2. Geometry (Span & Section)")
        h_slab = st.number_input("Slab Thickness (cm)", value=20)
        L1 = st.number_input("Span L1 (Analysis Direction) (m)", value=6.0)
        L2 = st.number_input("Span L2 (Transverse) (m)", value=6.0)
        
        c1 = st.number_input("Column c1 (Along L1) (cm)", value=40.0)
        c2 = st.number_input("Column c2 (Along L2) (cm)", value=40.0)

        st.subheader("3. Boundary Conditions")
        floor_scenario = st.selectbox("Floor Level", ["Typical Floor (Intermediate)", "Top Floor (Roof)", "Foundation/First Floor"])
        col_location = st.selectbox("Column Location", ["Interior Column", "Edge Column", "Corner Column"])
        
        # Logic รับค่าความสูง
        h_upper, h_lower, support_cond = 0.0, 0.0, "Fixed" # Default
        
        if floor_scenario != "Top Floor (Roof)":
            h_upper = st.number_input("Upper Storey Height (m)", value=3.0)
        
        if floor_scenario == "Foundation/First Floor":
            h_lower = st.number_input("Foundation Height (m)", value=1.5)
            support_cond = st.radio("Foundation Support", ["Fixed", "Pinned"], horizontal=True)
        else:
            h_lower = st.number_input("Lower Storey Height (m)", value=3.0)

        # =================================================================
        # 🧠 ENGINEERING BRAIN: Convert Input to Base Units (MKS)
        # =================================================================
        calc_data = {
            'L1': L1,             # m
            'L2': L2,             # m
            'h_slab': h_slab/100, # cm -> m
            'c1': c1/100,         # cm -> m
            'c2': c2/100,         # cm -> m
            'h_upper': h_upper,   # m
            'h_lower': h_lower,   # m
            'w_sdl': dl,          # kg/m^2
            'w_ll': ll,           # kg/m^2
            'fc_ksc': fc,         # ksc (เก็บไว้โชว์)
            'Ec': 15100 * (fc**0.5) * 10 # ksc -> tons/m^2 -> kg/m^2 (สูตร ACI/EIT โดยประมาณ)
        }
        # หมายเหตุ: Ec ถ้าจะเอาละเอียด เดี๋ยวเรามาจูนสูตรกันอีกทีครับ
        # =================================================================

    with col_viz:
        st.subheader("👁️ Structural Model Visualization")
        
        # Tab ย่อยสำหรับดูรูป
        viz_tab1, viz_tab2 = st.tabs(["Plan View (Load)", "Elevation (Stiffness)"])
        
        with viz_tab1:
            st.caption("Plan View แสดงทิศทางการวิเคราะห์และ Load")
            # เรียกใช้ตัวแปรที่แปลงหน่วยแล้ว (หน่วยเมตร)
            fig_plan = draw_plan_view(calc_data['L1'], calc_data['L2'], calc_data['c1'], calc_data['c2'], col_location, dl, ll)
            st.pyplot(fig_plan)
            
            # โชว์น้ำหนักรวม (Factored Load Calculation Preview)
            wu = 1.4*dl + 1.7*ll # กฎกระทรวง/EIT เก่า (หรือจะใช้ 1.2D+1.6L ก็แก้ตรงนี้)
            st.info(f"**Load Analysis:**\n\nDesign Load ($w_u$) = 1.4({dl}) + 1.7({ll}) = **{wu:.2f} kg/m²**")

        with viz_tab2:
            st.caption("Elevation View แสดงความสูงเสาและจุดรองรับ")
            fig_elev = draw_elevation(floor_scenario, h_upper, h_lower, support_cond)
            st.pyplot(fig_elev)
            
            st.success(f"""
            **System Parameters for Calculation:**
            - Column Stiffness ($K_c$) will use: $I_g$ based on {c1}x{c2} cm
            - Slab Stiffness ($K_s$) will use: Thickness {h_slab} cm
            - Far End Condition: **{support_cond}**
            """)
