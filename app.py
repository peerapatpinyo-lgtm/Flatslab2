import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# 🖌️ VISUALIZATION FUNCTIONS (วาดรูปสวยๆ แบบวิศวกร)
# ==============================================================================

def draw_plan_view(L1, L2, c1, c2, col_loc, wu):
    """
    L1: Analysis Span (m) -> Horizontal in Plot
    L2: Transverse Span (m) -> Vertical in Plot
    c1: Col dim parallel to L1 (m)
    c2: Col dim parallel to L2 (m)
    """
    fig, ax = plt.subplots(figsize=(6, 4.5))
    
    # Define colors
    slab_color = '#ecf0f1'
    col_color = '#e74c3c'
    dim_color = '#2c3e50'
    
    # 1. Draw Slab Panel (Representing the tributary area)
    # Center the plot at (0,0) being the column center
    ax.add_patch(patches.Rectangle((-L1/2, -L2/2), L1, L2, facecolor=slab_color, edgecolor='#bdc3c7', hatch='///', alpha=0.5))
    
    # 2. Draw Column (Correct Orientation)
    # c1 is along x-axis (L1), c2 is along y-axis (L2)
    col_rect = patches.Rectangle((-c1/2, -c2/2), c1, c2, facecolor=col_color, edgecolor='black', zorder=5)
    ax.add_patch(col_rect)
    
    # 3. Add Analysis Direction Arrow (The most important part!)
    ax.arrow(-L1/2 * 0.8, L2/2 * 1.2, L1 * 0.8, 0, head_width=0.2, head_length=0.3, fc='blue', ec='blue', width=0.05)
    ax.text(0, L2/2 * 1.4, "ANALYSIS DIRECTION (L1)", ha='center', color='blue', fontweight='bold', fontsize=10)

    # 4. Dimensions
    # L1 Dim
    ax.annotate(f'L1 = {L1:.2f} m', xy=(-L1/2, -L2/2 - 0.5), xytext=(L1/2, -L2/2 - 0.5),
                arrowprops=dict(arrowstyle='<->', color=dim_color), ha='center', color=dim_color)
    
    # L2 Dim
    ax.annotate(f'L2 = {L2:.2f} m', xy=(-L1/2 - 0.5, -L2/2), xytext=(-L1/2 - 0.5, L2/2),
                arrowprops=dict(arrowstyle='<->', color=dim_color), va='center', rotation=90, color=dim_color)
    
    # c1, c2 Labels
    ax.text(0, -c2/2 - 0.3, f"c1={c1*100:.0f}cm", ha='center', fontsize=8, color='red')
    ax.text(c1/2 + 0.1, 0, f"c2={c2*100:.0f}cm", va='center', rotation=90, fontsize=8, color='red')

    # 5. Load Info Box
    bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.9)
    ax.text(L1/2, L2/2, f"Total Factored Load\n$w_u = {wu:.2f}$ kg/m²", ha='right', va='top', bbox=bbox_props, fontsize=9)

    # Set Limits & Aspect
    margin = 1.5
    ax.set_xlim(-L1/2 - margin, L1/2 + margin)
    ax.set_ylim(-L2/2 - margin, L2/2 + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_elevation(h_upper, h_lower, support_cond, floor_scenario):
    fig, ax = plt.subplots(figsize=(4, 5))
    
    # Center Line
    ax.axvline(0, color='gray', linestyle='--', alpha=0.3)
    
    col_w = 0.3 # Visual width
    
    # Draw Slab
    ax.add_patch(patches.Rectangle((-1, -0.1), 2, 0.2, color='#95a5a6'))
    
    # Draw Upper Column
    if h_upper > 0:
        ax.add_patch(patches.Rectangle((-col_w/2, 0.1), col_w, 2, color='#3498db', alpha=0.8))
        ax.text(0.4, 1.0, f"Upper\n{h_upper} m", color='#2980b9')
    else:
        ax.text(0, 0.3, "ROOF LEVEL", ha='center', fontsize=8, fontweight='bold', color='gray')

    # Draw Lower Column
    ax.add_patch(patches.Rectangle((-col_w/2, -2.1), col_w, 2, color='#e74c3c', alpha=0.8))
    ax.text(0.4, -1.0, f"Lower\n{h_lower} m", color='#c0392b')

    # Draw Support
    if floor_scenario == "Foundation/First Floor":
        if support_cond == "Fixed":
            ax.add_patch(patches.Rectangle((-0.6, -2.2), 1.2, 0.1, color='black'))
            ax.text(0, -2.4, "FIXED BASE", ha='center', fontweight='bold')
        else:
            ax.plot(0, -2.1, marker='^', markersize=12, color='black')
            ax.text(0, -2.4, "PINNED BASE", ha='center', fontweight='bold')
    else:
        # Continuity text
        ax.text(0, -2.4, "To Lower Floor", ha='center', fontsize=8, color='gray')

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-3, 3)
    ax.axis('off')
    return fig

# ==============================================================================
# 🎛️ INPUT SECTION (Sidebar)
# ==============================================================================
st.sidebar.header("🏗️ Design Parameters")

with st.sidebar.form("input_form"):
    st.markdown("### 1. Material Properties")
    c_mat1, c_mat2 = st.columns(2)
    fc = c_mat1.number_input("f'c (ksc)", 240, step=10)
    fy = c_mat2.number_input("fy (ksc)", 4000, step=100)
    
    st.markdown("### 2. Loads (Service)")
    dl = st.number_input("SDL (kg/m²)", 100)
    ll = st.number_input("Live Load (kg/m²)", 200)

    st.markdown("### 3. Geometry (Dimensions)")
    h_slab = st.number_input("Slab Thickness (cm)", 20.0)
    st.caption("Frame Dimensions:")
    L1 = st.number_input("Span L1 (Analysis Dir) (m)", 6.0)
    L2 = st.number_input("Span L2 (Transverse) (m)", 6.0)
    st.caption("Column Size:")
    c1 = st.number_input("c1 (Parallel to L1) (cm)", 40.0)
    c2 = st.number_input("c2 (Parallel to L2) (cm)", 40.0)

    st.markdown("### 4. Location & Story")
    col_loc = st.selectbox("Column Type", ["Interior Column", "Edge Column", "Corner Column"])
    floor_scenario = st.selectbox("Floor Level", ["Typical Floor (Intermediate)", "Top Floor (Roof)", "Foundation/First Floor"])
    
    # Conditional Inputs for Height
    h_upper = 0.0
    h_lower = 3.0 # default
    support_cond = "Fixed"

    if floor_scenario != "Top Floor (Roof)":
        h_upper = st.number_input("Upper Story Height (m)", 3.0)
    
    if floor_scenario == "Foundation/First Floor":
        h_lower = st.number_input("Foundation Height (m)", 1.5)
        support_cond = st.radio("Support Condition", ["Fixed", "Pinned"], horizontal=True)
    else:
        h_lower = st.number_input("Lower Story Height (m)", 3.0)

    submit_btn = st.form_submit_button("✅ Update Calculation", type="primary")

# ==============================================================================
# 🚀 MAIN DASHBOARD (Layout แบบมืออาชีพ)
# ==============================================================================

st.title("🏗️ Flat Slab Design: Equivalent Frame Method")
st.markdown("---")

# --- 1. Key Metrics Bar (สรุปค่าสำคัญไว้บนสุด) ---
# คำนวณเบื้องต้น
wu = 1.4*dl + 1.7*ll # Design Load
Ec = 15100 * (fc**0.5) # ksc (EIT)

# แปลงหน่วยเป็น Standard (Meter, kg, kg/m2)
calc_data = {
    'L1': L1, 'L2': L2, 'c1': c1/100, 'c2': c2/100, 
    'h_slab': h_slab/100, 'h_upper': h_upper, 'h_lower': h_lower
}

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Concrete (f'c)", f"{fc} ksc", f"Ec = {Ec:,.0f} ksc")
col_m2.metric("Steel (fy)", f"{fy} ksc")
col_m3.metric("Factored Load (wu)", f"{wu:,.2f} kg/m²", "1.4DL + 1.7LL")
col_m4.metric("Slab Thickness", f"{h_slab} cm", f"L/33 = {(L1*100/33):.1f} cm")

st.markdown("---")

# --- 2. Visualization & Properties (แบ่ง 2 ฝั่ง) ---
col_viz, col_prop = st.columns([1.5, 1])

with col_viz:
    st.subheader("👁️ Geometric Model")
    tab_plan, tab_elev = st.tabs(["📌 Plan View (L1 Analysis)", "📐 Elevation (Heights)"])
    
    with tab_plan:
        fig_plan = draw_plan_view(calc_data['L1'], calc_data['L2'], calc_data['c1'], calc_data['c2'], col_loc, wu)
        st.pyplot(fig_plan)
        st.caption("Note: **L1** is the span direction for moment analysis. **c1** is the column dimension parallel to L1.")

    with tab_elev:
        fig_elev = draw_elevation(calc_data['h_upper'], calc_data['h_lower'], support_cond, floor_scenario)
        st.pyplot(fig_elev)

with col_prop:
    st.subheader("⚙️ Section Properties")
    
    # คำนวณ Inertia (Uncracked)
    # Column Inertia
    Ig_col = (calc_data['c2'] * (calc_data['c1']**3)) / 12 # m^4
    # Slab Inertia (เต็มหน้ากว้าง L2)
    Ig_slab = (calc_data['L2'] * (calc_data['h_slab']**3)) / 12 # m^4

    st.markdown(f"""
    **1. Column Properties ($c_1 \\times c_2$)**
    * Size: {c1:.0f} x {c2:.0f} cm
    * $I_g$ (Column): **{Ig_col:.6f} m⁴**
    
    **2. Slab Beam Strip ($L_2 \\times h$)**
    * Width ($L_2$): {L2:.2f} m
    * Thickness ($h$): {h_slab:.0f} cm
    * $I_g$ (Slab): **{Ig_slab:.6f} m⁴**
    
    **3. Analysis Settings**
    * Scenario: `{floor_scenario}`
    * Far-End Support: `{support_cond}`
    """)
    
    # พื้นที่สำหรับ Debug หรือ Next Step
    with st.expander("Show Unit Conversions (Debug)"):
        st.write(calc_data)

# --- 3. Next Steps Hint ---
st.info("✅ **Model Verified.** Ready to calculate Stiffness (K), Distribution Factors (DF), and Moments.")
