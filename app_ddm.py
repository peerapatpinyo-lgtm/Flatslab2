import streamlit as st
import pandas as pd
import calc_ddm  # Import logic file

def render_ddm_tab(calc_obj):
    """
    Main function to render DDM tab content.
    Accepts 'calc_obj' from app.py and adapts it for calculation.
    """
    st.header("🏗️ Direct Design Method (DDM) Analysis")
    
    # --- 1. DATA ADAPTER (The Bridge) ---
    # แปลงข้อมูลจาก app.py ให้เป็นรูปแบบที่ calc_ddm ต้องการ
    try:
        # Extract Geometry
        geom = calc_obj.get('geom', {})
        L1 = geom.get('L1_l', 6.0) # Analysis direction
        L2 = geom.get('L2', 6.0)   # Transverse direction
        h_slab = geom.get('h_slab', 0.20) # meters
        
        # Extract Materials
        mat = calc_obj.get('mat', {})
        fc = mat.get('fc', 240)
        
        # HANDLE FY: Convert String "SD40" -> 4000 if needed
        fy_input = mat.get('fy', 4000)
        if isinstance(fy_input, str):
            if "30" in fy_input: fy = 3000
            elif "40" in fy_input: fy = 4000
            elif "50" in fy_input: fy = 5000
            else: fy = 4000 # Default
        else:
            fy = float(fy_input)

        # Extract Loads
        loads = calc_obj.get('loads', {})
        # Recalculate Factored Load (Wu) just to be safe
        lf_dl = loads.get('lf_dl', 1.4)
        lf_ll = loads.get('lf_ll', 1.7)
        # Assuming loads are stored as raw or we calculate from inputs
        # Try to find w_total_factored, otherwise estimate
        # Note: app.py seems to calculate w_total in app_calc. Assuming it's in loads['w_u'] or similar
        # Let's try to calculate manually to be robust:
        # We assume calc_obj has enough info, if not we default.
        # Fallback logic:
        w_dead = loads.get('w_dead', 2400*h_slab + 150) # Selfweight + SDL
        w_live = loads.get('LL', 300)
        wu = (1.4 * w_dead) + (1.7 * w_live) # Conservative fallback

        # Extract Columns
        col = calc_obj.get('col_size', {})
        c1 = col.get('c1', 50) / 100.0 # Convert cm to m
        c2 = col.get('c2', 50) / 100.0
        
        # Calculate Effective Params
        ln = L1 - c1 # Clear span
        d_eff = h_slab - 0.03 # cover 3cm
        
        # Package for calc_ddm
        ddm_inputs = {
            'l1': L1, 'l2': L2, 'ln': ln,
            'wu': wu, 'h': h_slab, 'd': d_eff,
            'fc': fc, 'fy': fy, 'c1': c1, 'c2': c2
        }

    except Exception as e:
        st.error(f"⚠️ Error preparing data: {e}")
        st.write("Debug Data:", calc_obj)
        return

    # --- 2. DISPLAY INPUT SUMMARY ---
    with st.expander("📊 Calculation Parameters (Check)", expanded=False):
        c1_ui, c2_ui, c3_ui = st.columns(3)
        c1_ui.metric("Clear Span (Ln)", f"{ln:.2f} m")
        c2_ui.metric("Factored Load (Wu)", f"{wu:.0f} kg/m²")
        c3_ui.metric("Steel Strength (fy)", f"{fy:.0f} ksc")

    # --- 3. PERFORM CALCULATION ---
    df_results, Mo = calc_ddm.calculate_ddm(ddm_inputs)

    # --- 4. SHOW RESULTS ---
    st.subheader("1. Static Moment ($M_o$)")
    st.latex(r"M_o = \frac{w_u \ell_2 \ell_n^2}{8}")
    st.info(f"**Total Static Moment ($M_o$): {Mo:,.2f} kg-m**")
    
    st.subheader("2. Moment Distribution & Reinforcement")
    st.markdown("Distribution based on ACI 318 Coefficients for Interior Panel.")
    
    # Style the dataframe
    st.dataframe(
        df_results.style.format({
            "Moment (kg-m)": "{:,.2f}",
            "As Req (cm²)": "{:.2f}"
        }),
        use_container_width=True
    )
    
    # --- 5. SIMPLE VISUALIZATION ---
    st.subheader("3. Reinforcement Sketch")
    st.caption("Simplified representation of top (negative) and bottom (positive) steel.")
    
    # Draw a simple SVG or Matplotlib chart
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(8, 3))
    # Draw Beam line
    ax.plot([0, L1], [0, 0], color='black', linewidth=2)
    # Draw Supports
    ax.plot([0, 0], [-0.5, 0.5], color='grey', linewidth=4)
    ax.plot([L1, L1], [-0.5, 0.5], color='grey', linewidth=4)
    
    # Plot Reinforcement Zones
    # Neg Steel (Top)
    ax.plot([0, L1*0.3], [0.2, 0.2], color='red', linewidth=3, label='Top Steel (Col Strip)')
    ax.plot([L1*0.7, L1], [0.2, 0.2], color='red', linewidth=3)
    
    # Pos Steel (Bottom)
    ax.plot([L1*0.15, L1*0.85], [-0.2, -0.2], color='blue', linewidth=3, label='Bot Steel (Col/Mid Strip)')
    
    ax.set_ylim(-1, 1)
    ax.set_title(f"Span Length L1 = {L1} m")
    ax.axis('off')
    ax.legend(loc='lower center', ncol=2)
    
    st.pyplot(fig)
