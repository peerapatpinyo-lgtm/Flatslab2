import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Setup & Configuration ---
st.set_page_config(page_title="Flat Slab EFM Design", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# 🖌️ VISUALIZATION FUNCTIONS (รองรับ Drop Panel & C-to-C Indication)
# ==============================================================================

def draw_plan_view(L1, L2, c1, c2, col_loc, wu, drop_data=None):
    """
    drop_data: dict or None. Keys: 'wd1' (width along L1), 'wd2' (width along L2)
    """
    fig, ax = plt.subplots(figsize=(6, 4.5))
    
    # Define colors
    slab_color = '#ecf0f1'
    drop_color = '#bdc3c7' # Darker gray for drop
    col_color = '#e74c3c'
    dim_color = '#2c3e50'
    
    # 1. Draw Slab Panel (Representing the tributary area / panel)
    # Center at (0,0)
    ax.add_patch(patches.Rectangle((-L1/2, -L2/2), L1, L2, facecolor=slab_color, edgecolor='#bdc3c7', hatch='///', alpha=0.3))
    
    # 2. Draw Drop Panel (New!)
    if drop_data and drop_data['has_drop']:
        wd1 = drop_data['wd1']
        wd2 = drop_data['wd2']
        # Draw Drop Rect centered
        drop_rect = patches.Rectangle((-wd1/2, -wd2/2), wd1, wd2, facecolor=drop_color, edgecolor='gray', alpha=0.8)
        ax.add_patch(drop_rect)
        # Label Drop
        ax.text(-wd1/2, -wd2/2 - 0.2, f"Drop Panel\n{wd1:.2f}x{wd2:.2f}m", fontsize=8, color='gray', va='top')

    # 3. Draw Column
    col_rect = patches.Rectangle((-c1/2, -c2/2), c1, c2, facecolor=col_color, edgecolor='black', zorder=5)
    ax.add_patch(col_rect)
    
    # 4. Analysis Direction Arrow
    ax.arrow(-L1/2 * 0.8, L2/2 * 1.2, L1 * 0.8, 0, head_width=0.2, head_length=0.3, fc='blue', ec='blue', width=0.05)
    ax.text(0, L2/2 * 1.4, "ANALYSIS DIRECTION (L1)\n(Center-to-Center Span)", ha='center', color='blue', fontweight='bold', fontsize=9)

    # 5. Dimensions (Center-to-Center Emphasis) 

[Image of engineering dimension lines]

    # ใช้ arrowstyle='|-|' เพื่อแสดงว่าเป็นระยะระบุตำแหน่ง (Dimension Line) ไม่ใช่ Vector
    
    # L1 Dimension
    ax.annotate(f'L1 (c/c) = {L1:.2f} m', xy=(-L1/2, -L2/2 - 0.8), xytext=(L1/2, -L2/2 - 0.8),
                arrowprops=dict(arrowstyle='|-|', color=dim_color, linewidth=1.5), ha='center', color=dim_color, fontweight='bold')
    
    # L2 Dimension
    ax.annotate(f'L2 (c/c) = {L2:.2f} m', xy=(-L1/2 - 0.8, -L2/2), xytext=(-L1/2 - 0.8, L2/2),
                arrowprops=dict(arrowstyle='|-|', color=dim_color, linewidth=1.5), va='center', rotation=90, color=dim_color, fontweight='bold')
    
    # 6. Load Info Box
    bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.9)
    ax.text(L1/2, L2/2, f"Total Factored Load\n$w_u = {wu:.2f}$ kg/m²", ha='right', va='top', bbox=bbox_props, fontsize=9)

    # Limits
    margin = 2.0
    ax.set_xlim(-L1/2 - margin, L1/2 + margin)
    ax.set_ylim(-L2/2 - margin, L2/2 + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_elevation(h_upper, h_lower, support_cond, floor_scenario, drop_data=None):
    fig, ax = plt.subplots(figsize=(4, 5))
    ax.axvline(0, color='gray', linestyle='--', alpha=0.3) # Center Line
    col_w = 0.3 
    
    # Draw Slab
    ax.add_patch(patches.Rectangle((-1, -0.1), 2, 0.2, color='#95a5a6')) # Main Slab (Assuming ~20cm scale visual)
    
    # Draw Drop Panel (New!)
    if drop_data and drop_data['has_drop']:
        # Scale Drop thickness relative to slab roughly for visual
        d_thick = 0.1 # Visual thickness for drop
        d_width = 0.8 # Visual width
        # Drop panel hangs BELOW the slab (y negative relative to slab bottom)
        ax.add_patch(patches.Rectangle((-d_width/2, -0.1 - d_thick), d_width, d_thick, color='#7f8c8d'))
        ax.text(0.5, -0.25, f"Drop +{drop_data['h_drop']*100:.0f}cm", fontsize=8, color='#2c3e50')

    # Draw Upper Column
    if h_upper > 0:
        ax.add_patch(patches.Rectangle((-col_w/2, 0.1), col_w, 2, color='#3498db', alpha=0.8))
        ax.text(0.4, 1.0, f"Upper\n{h_upper} m", color='#2980b9')
    else:
        ax.text(0, 0.3, "ROOF LEVEL", ha='center', fontsize=8, fontweight='bold', color='gray')

    # Draw Lower Column
    # Adjust start Y based on Drop Panel presence to look realistic
    start_y = -0.1 if not (drop_data and drop_data['has_drop']) else -0.2
    
    # Draw lower column starting from bottom of slab/drop
    ax.add_patch(patches.Rectangle((-col_w/2, -2.1), col_w, 2 - abs(start_y) - 0.1, color='#e74c3c', alpha=0.8))
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

    st.markdown("### 3. Geometry (Center-to-Center)")
    
    # --- Drop Panel Logic ---
    has_drop = st.checkbox("With Drop Panel (พื้นมีหัวเสา)?", value=False)
    
    col_geom1, col_geom2 = st.columns(2)
    h_slab = col_geom1.number_input("Slab Thickness (cm)", 20.0)
    
    # Drop Panel Inputs (Conditional)
    h_drop, wd1, wd2 = 0.0, 0.0, 0.0
    if has_drop:
        st.markdown("**Drop Panel Details:**")
        h_drop = st.number_input("Drop Projection (cm)", value=10.0, help="ความหนาที่ยื่นลงมาจากท้องพื้น (ไม่รวมพื้น)")
        c_drop1, c_drop2 = st.columns(2)
        wd1 = c_drop1.number_input("Width along L1 (m)", value=2.0)
        wd2 = c_drop2.number_input("Width along L2 (m)", value=2.0)
    
    st.markdown("---")
    st.caption("Frame Dimensions (Grid-to-Grid):")
    L1 = st.number_input("Span L1 (Analysis Dir) (m)", 6.0)
    L2 = st.number_input("Span L2 (Transverse) (m)", 6.0)
    st.caption("Column Size:")
    c1 = st.number_input("c1 (Parallel to L1) (cm)", 40.0)
    c2 = st.number_input("c2 (Parallel to L2) (cm)", 40.0)

    st.markdown("### 4. Location & Story")
    col_loc = st.selectbox("Column Type", ["Interior Column", "Edge Column", "Corner Column"])
    floor_scenario = st.selectbox("Floor Level", ["Typical Floor (Intermediate)", "Top Floor (Roof)", "Foundation/First Floor"])
    
    h_upper = 0.0
    h_lower = 3.0 
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
# 🚀 MAIN DASHBOARD
# ==============================================================================

st.title("🏗️ Flat Slab/Plate Design: Equivalent Frame Method")
st.markdown("---")

# --- 1. Key Metrics ---
wu = 1.4*dl + 1.7*ll
Ec = 15100 * (fc**0.5)

# Unit Conversion & Data Pack
calc_data = {
    'L1': L1, 'L2': L2, 'c1': c1/100, 'c2': c2/100, 
    'h_slab': h_slab/100, 'h_upper': h_upper, 'h_lower': h_lower,
    'has_drop': has_drop,
    'h_drop': h_drop/100 if has_drop else 0,
    'wd1': wd1 if has_drop else 0,
    'wd2': wd2 if has_drop else 0
}

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Concrete (f'c)", f"{fc} ksc", f"Ec = {Ec:,.0f} ksc")
col_m2.metric("Factored Load (wu)", f"{wu:,.2f} kg/m²", "1.4DL + 1.7LL")

# Dynamic Metric for Thickness
if has_drop:
    col_m3.metric("Slab Thickness", f"{h_slab} cm", f"+ Drop {h_drop} cm")
    col_m4.metric("Total Thickness (at Drop)", f"{h_slab + h_drop} cm", "For Neg. Moment Check")
else:
    col_m3.metric("Slab Thickness", f"{h_slab} cm", "Flat Plate")
    col_m4.metric("System Type", "Flat Plate", "No Drop Panel")

st.markdown("---")

# --- 2. Visualization & Properties ---
col_viz, col_prop = st.columns([1.5, 1])

with col_viz:
    st.subheader("👁️ Geometric Model")
    tab_plan, tab_elev = st.tabs(["📌 Plan View (L1 Analysis)", "📐 Elevation (Heights)"])
    
    with tab_plan:
        # Pass Drop Data to Visualization
        fig_plan = draw_plan_view(calc_data['L1'], calc_data['L2'], calc_data['c1'], calc_data['c2'], col_loc, wu, calc_data)
        st.pyplot(fig_plan)
        st.caption("✅ **Confirmed:** L1 & L2 are Center-to-Center (Grid-to-Grid) dimensions.")

    with tab_elev:
        fig_elev = draw_elevation(calc_data['h_upper'], calc_data['h_lower'], support_cond, floor_scenario, calc_data)
        st.pyplot(fig_elev)

with col_prop:
    st.subheader("⚙️ Section Properties")
    
    # Calculation Logic
    Ig_col = (calc_data['c2'] * (calc_data['c1']**3)) / 12 # m^4
    Ig_slab_mid = (calc_data['L2'] * (calc_data['h_slab']**3)) / 12 # m^4
    
    st.markdown(f"""
    **1. Column Properties ($c_1 \\times c_2$)**
    * Size: {c1:.0f} x {c2:.0f} cm
    * $I_g$ (Column): **{Ig_col:.6f} m⁴**
    
    **2. Slab Beam Strip ($L_2 \\times h$)**
    * Width ($L_2$): {L2:.2f} m
    * Main Thickness ($h$): {h_slab:.0f} cm
    * $I_g$ (Mid-Span): **{Ig_slab_mid:.6f} m⁴**
    """)
    
    if has_drop:
        # Inertia at Drop Panel Section (ใช้ความกว้าง L2 แต่ความหนาเพิ่มขึ้น)
        # Note: ตามทฤษฎีเป๊ะๆ อาจต้องพิจารณาความกว้าง Effective ของ Drop แต่ใน EFM เบื้องต้นมักใช้ L2 x Total_h
        h_total = (h_slab + h_drop) / 100
        Ig_slab_drop = (calc_data['L2'] * (h_total**3)) / 12
        
        st.success(f"""
        **🔹 Drop Panel Detected:**
        * Size: {wd1:.2f} x {wd2:.2f} m
        * Projection ($h_d$): {h_drop:.0f} cm
        * Total Thickness: {h_slab + h_drop:.0f} cm
        * $I_g$ (at Drop): **{Ig_slab_drop:.6f} m⁴**
        
        *System will use Variable Moment of Inertia for stiffness calculation.*
        """)
    else:
        st.info("No Drop Panel defined. Uniform slab stiffness will be used.")

    with st.expander("Show Internal Variables (Debug)"):
        st.write(calc_data)
