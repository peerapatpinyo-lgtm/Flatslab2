import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Flat Slab EFM Design", layout="wide")

st.title("🏗️ Flat Slab Design: Equivalent Frame Method")
st.markdown("### Phase 1: Structural Modeling & Inputs")

# --- 1. Global Parameters (Load & Materials) ---
with st.sidebar:
    st.header("1. Material & Loads")
    fc = st.number_input("f'c (ksc)", value=240)
    fy = st.number_input("fy (ksc)", value=4000)
    
    st.subheader("Load Combinations")
    # รับค่า Load เพื่อเตรียมไปทำ Load Combination 1.4D+1.7L หรือ 1.2D+1.6L
    dl = st.number_input("Superimposed Dead Load (kg/m²)", value=100)
    ll = st.number_input("Live Load (kg/m²)", value=200)
    
    # Slab Geometry พื้นฐาน
    st.header("2. Slab Geometry")
    h_slab = st.number_input("Slab Thickness (cm)", value=20)
    L1 = st.number_input("Span L1 (Direction of Analysis) (m)", value=6.0)
    L2 = st.number_input("Span L2 (Transverse) (m)", value=6.0)

# --- 2. Column Scenarios (The Core Logic) ---
st.header("📍 Column Scenario Definition")

col1, col2 = st.columns([1, 1])

with col1:
    # เลือกตำแหน่งในแปลน (ส่งผลต่อ Kt)
    col_location = st.selectbox(
        "Column Location (Plan View)",
        ["Interior Column", "Edge Column", "Corner Column"],
        help="ส่งผลต่อการคำนวณ Torsional Stiffness (Kt) และ Unbalanced Moment"
    )

    # เลือกตำแหน่งชั้น (ส่งผลต่อ Kc และ Topology)
    floor_scenario = st.selectbox(
        "Floor Scenario (Elevation View)",
        ["Typical Floor (Intermediate)", "Top Floor (Roof)", "Foundation/First Floor"]
    )

    st.info(f"Condition: **{col_location}** at **{floor_scenario}**")

# --- Function สำหรับวาดรูป Diagram อัตโนมัติ ---
def draw_scenario(scenario, location, h_col_above, h_col_below, support_cond):
    fig, ax = plt.subplots(figsize=(4, 4))
    
    # วาดพื้น (Slab)
    ax.add_patch(patches.Rectangle((-1, -0.1), 2, 0.2, color='gray', alpha=0.5))
    ax.text(1.1, 0, "Slab", va='center')

    # วาดเสาตาม Scenario
    col_width = 0.2
    
    # เสาบน (Column Above)
    if scenario != "Top Floor (Roof)":
        ax.add_patch(patches.Rectangle((-col_width/2, 0.1), col_width, 1.5, color='#3498db'))
        ax.text(0.2, 0.8, f"Upper Col\nHi={h_col_above}m", fontsize=9, color='blue')
        # Far end condition visual
        ax.plot([-0.2, 0.2], [1.6, 1.6], 'k-', lw=2) # Roof line or continuity

    # เสาล่าง (Column Below)
    if scenario != "Foundation/First Floor":
        ax.add_patch(patches.Rectangle((-col_width/2, -1.6), col_width, 1.5, color='#e74c3c'))
        ax.text(0.2, -0.8, f"Lower Col\nHi={h_col_below}m", fontsize=9, color='red')
    
    # กรณี Foundation
    if scenario == "Foundation/First Floor":
        # วาดเสาที่ตั้งอยู่บนฐานราก (ใน EFM มักมองเสาชั้น 1 เป็น Col Above ของ Foundation หรือ Col Below ของชั้น 2)
        # แต่ในบริบทนี้ ถ้าเราออกแบบพื้นชั้น 1 (ที่ไม่มีพื้นดินรองรับ) หรือพื้นชั้น 2:
        # สมมติว่าเป็นพื้นชั้นล่างสุดที่มีเสาตอม่อลงไป
        ax.add_patch(patches.Rectangle((-col_width/2, -1.6), col_width, 1.5, color='#e74c3c'))
        
        # วาด Support
        if support_cond == "Fixed":
            ax.add_patch(patches.Rectangle((-0.4, -1.7), 0.8, 0.1, color='black')) # Base
            ax.text(0, -1.9, "FIXED Base", ha='center', fontweight='bold')
        else: # Pinned
            ax.plot(0, -1.6, marker='^', markersize=15, color='black')
            ax.text(0, -1.9, "PINNED Base", ha='center', fontweight='bold')

    # จัดระเบียบกราฟ
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2.5, 2.5)
    ax.axis('off')
    return fig

# --- 3. Dynamic Inputs based on Scenario ---
with col2:
    st.markdown("### Column & Support Details")
    
    # ---------------------------------------------------------
    # ✅ FIX: กำหนดค่าเริ่มต้นก่อน เพื่อป้องกัน NameError
    h_upper = 0.0
    h_lower = 0.0
    support_condition = "Fixed"  # ค่า Default ป้องกัน error
    # ---------------------------------------------------------

    c1 = st.number_input("Column Dimension c1 (direction of analysis) (cm)", value=30.0)
    c2 = st.number_input("Column Dimension c2 (transverse) (cm)", value=30.0)
    
    # Logic: ถามหาเสาบน ถ้าไม่ใช่ชั้นหลังคา
    if floor_scenario != "Top Floor (Roof)":
        st.markdown("---")
        st.markdown("**⬆️ Upper Column Properties**")
        h_upper = st.number_input("Upper Storey Height (m)", value=3.0, key="h_up")
        
    # Logic: ถามหาเสาล่าง และ Support Condition
    if floor_scenario == "Foundation/First Floor":
        st.markdown("---")
        st.markdown("**⬇️ Lower Column (Foundation) Properties**")
        h_lower = st.number_input("Height to Foundation (m)", value=1.5, key="h_low")
        # รับค่า Support Condition ที่นี่
        support_condition = st.radio("Foundation Support Condition", ["Fixed", "Pinned"])
        
    elif floor_scenario != "Foundation/First Floor":
        st.markdown("---")
        st.markdown("**⬇️ Lower Column Properties**")
        h_lower = st.number_input("Lower Storey Height (m)", value=3.0, key="h_low")
        support_condition = "Fixed" # สำหรับชั้น Typical มักสมมติ Far end เป็น Fixed

    # --- แสดง Visualization ---
    st.markdown("---")
    st.caption("Structural Model Visualization")
    # ตอนนี้ตัวแปรทุกตัวมีค่าแน่นอนแล้ว เรียกใช้ฟังก์ชันได้ไม่ error
    fig = draw_scenario(floor_scenario, col_location, h_upper, h_lower, support_condition)
    st.pyplot(fig)

# --- 4. Slenderness & Stiffness Prep (Preview) ---
st.header("📊 Calculation Preview (Next Step)")

# คำนวณ Moment of Inertia พื้นฐาน (Gross Section)
Ig_col = (c2 * (c1**3)) / 12  # cm^4

st.write(f"**Column Moment of Inertia ($I_g$):** {Ig_col:,.2f} cm$^4$")

if floor_scenario == "Typical Floor (Intermediate)":
    st.info("System will calculate stiffness for BOTH Upper ($K_{c,top}$) and Lower ($K_{c,bot}$) columns.")
elif floor_scenario == "Top Floor (Roof)":
    st.info("System will calculate stiffness for LOWER column only ($K_{c,bot}$). Upper Stiffness = 0.")
elif floor_scenario == "Foundation/First Floor":
    st.info(f"System will calculate stiffness for Upper column ($K_{c,top}$) and Lower column with **{support_condition}** far-end condition.")
