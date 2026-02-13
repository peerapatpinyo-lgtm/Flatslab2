import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design", layout="wide")

# ==============================================================================
# ✅ SAFETY ZONE: ประกาศตัวแปรทุกตัวไว้ที่นี่ (กัน Error 100%)
# ==============================================================================
h_upper = 0.0
h_lower = 0.0
support_condition = "Fixed" # ค่า Default ป้องกัน NameError
# ==============================================================================

# --- Function สำหรับวาดรูป (Diagram) ---
def draw_scenario(scenario, location, h_col_above, h_col_below, support_cond):
    """ฟังก์ชันสำหรับวาดรูปจำลองโครงสร้างตาม Scenario"""
    fig, ax = plt.subplots(figsize=(4, 4))
    
    # วาดพื้น (Slab)
    ax.add_patch(patches.Rectangle((-1, -0.1), 2, 0.2, color='gray', alpha=0.5))
    ax.text(1.1, 0, "Slab", va='center')

    col_width = 0.2
    
    # --- วาดเสาบน ---
    if scenario != "Top Floor (Roof)":
        ax.add_patch(patches.Rectangle((-col_width/2, 0.1), col_width, 1.5, color='#3498db'))
        ax.text(0.2, 0.8, f"Upper Col\nHi={h_col_above}m", fontsize=9, color='blue')
        # เส้น Continuity
        ax.plot([-0.2, 0.2], [1.6, 1.6], 'k-', lw=2)

    # --- วาดเสาล่าง ---
    ax.add_patch(patches.Rectangle((-col_width/2, -1.6), col_width, 1.5, color='#e74c3c'))
    
    # กรณี Foundation ให้แสดง Support
    if scenario == "Foundation/First Floor":
        ax.text(0.2, -0.8, f"Lower Col\nHi={h_col_below}m", fontsize=9, color='red')
        if support_cond == "Fixed":
            ax.add_patch(patches.Rectangle((-0.4, -1.7), 0.8, 0.1, color='black'))
            ax.text(0, -1.9, "FIXED Base", ha='center', fontweight='bold')
        else: # Pinned
            ax.plot(0, -1.6, marker='^', markersize=15, color='black')
            ax.text(0, -1.9, "PINNED Base", ha='center', fontweight='bold')
    else:
        # กรณีทั่วไป
        ax.text(0.2, -0.8, f"Lower Col\nHi={h_col_below}m", fontsize=9, color='red')

    ax.set_xlim(-2, 2)
    ax.set_ylim(-2.5, 2.5)
    ax.axis('off')
    return fig

# --- 2. Main Interface ---
st.title("🏗️ Flat Slab Design: Equivalent Frame Method")
st.markdown("### Phase 1: Structural Modeling & Inputs")

with st.sidebar:
    st.header("1. Material & Loads")
    fc = st.number_input("f'c (ksc)", value=240)
    fy = st.number_input("fy (ksc)", value=4000)
    
    st.subheader("Load Combinations")
    dl = st.number_input("Superimposed Dead Load (kg/m²)", value=100)
    ll = st.number_input("Live Load (kg/m²)", value=200)
    
    st.header("2. Slab Geometry")
    h_slab = st.number_input("Slab Thickness (cm)", value=20)
    L1 = st.number_input("Span L1 (Direction of Analysis) (m)", value=6.0)
    L2 = st.number_input("Span L2 (Transverse) (m)", value=6.0)

# --- 3. Scenario Logic ---
st.header("📍 Column Scenario Definition")

col1, col2 = st.columns([1, 1])

with col1:
    col_location = st.selectbox(
        "Column Location (Plan View)",
        ["Interior Column", "Edge Column", "Corner Column"],
        help="ส่งผลต่อการคำนวณ Torsional Stiffness (Kt)"
    )

    floor_scenario = st.selectbox(
        "Floor Scenario (Elevation View)",
        ["Typical Floor (Intermediate)", "Top Floor (Roof)", "Foundation/First Floor"]
    )

    st.info(f"Condition: **{col_location}** at **{floor_scenario}**")

with col2:
    st.markdown("### Column & Support Details")
    c1 = st.number_input("Column Dimension c1 (analysis dir) (cm)", value=30.0)
    c2 = st.number_input("Column Dimension c2 (transverse) (cm)", value=30.0)
    
    # Logic ปรับค่าตาม Scenario
    # 1. เสาบน
    if floor_scenario != "Top Floor (Roof)":
        st.markdown("---")
        h_upper = st.number_input("Upper Storey Height (m)", value=3.0, key="h_up")
        
    # 2. เสาล่าง และ Support
    if floor_scenario == "Foundation/First Floor":
        st.markdown("---")
        h_lower = st.number_input("Height to Foundation (m)", value=1.5, key="h_low")
        # รับค่าและอัปเดตตัวแปร support_condition
        support_condition = st.radio("Foundation Support Condition", ["Fixed", "Pinned"])
    else:
        st.markdown("---")
        h_lower = st.number_input("Lower Storey Height (m)", value=3.0, key="h_low")
        support_condition = "Fixed" # บังคับเป็น Fixed สำหรับชั้นอื่น

    # แสดงรูป
    st.markdown("---")
    st.caption("Structural Model Visualization")
    # เรียกใช้ฟังก์ชันวาดรูป (ตอนนี้ตัวแปรทุกตัวมีค่าครบแน่นอน)
    fig = draw_scenario(floor_scenario, col_location, h_upper, h_lower, support_condition)
    st.pyplot(fig)

# --- 4. Slenderness & Stiffness Prep (Preview) ---
st.header("📊 Calculation Preview (Next Step)")

# คำนวณ Moment of Inertia พื้นฐาน
Ig_col = (c2 * (c1**3)) / 12  # cm^4

st.write(f"**Column Moment of Inertia ($I_g$):** {Ig_col:,.2f} cm$^4$")

# แสดงผลสรุป (จุดที่เคย Error)
if floor_scenario == "Typical Floor (Intermediate)":
    st.info("System will calculate stiffness for BOTH Upper ($K_{c,top}$) and Lower ($K_{c,bot}$) columns.")
elif floor_scenario == "Top Floor (Roof)":
    st.info("System will calculate stiffness for LOWER column only ($K_{c,bot}$). Upper Stiffness = 0.")
elif floor_scenario == "Foundation/First Floor":
    # ตัวแปร support_condition ถูกประกาศไว้บนสุดแล้ว ไม่มีทาง Error
    st.info(f"System will calculate stiffness for Upper column ($K_{c,top}$) and Lower column with **{support_condition}** far-end condition.")
