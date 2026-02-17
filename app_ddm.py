# app_ddm.py
import streamlit as st
import pandas as pd
import numpy as np

def get_moment_coefficients(is_end_span, has_edge_beam, is_fully_restrained=False):
    """
    Returns ACI 318 Coefficients for Direct Design Method.
    Returns dict: {'neg_ext': val, 'pos': val, 'neg_int': val}
    """
    if not is_end_span:
        # Case: Interior Span
        return {'neg_ext': 0.65, 'pos': 0.35, 'neg_int': 0.65, 'desc': "Interior Span (Flat Plate/Slab)"}
    
    # Case: End Span (Exterior)
    if is_fully_restrained:
        # Case: Restrained edge (e.g., rigid wall)
        return {'neg_ext': 0.65, 'pos': 0.35, 'neg_int': 0.65, 'desc': "End Span (Fully Restrained)"}
    elif has_edge_beam:
        # Case: Slab with Edge Beam (Spandrel) -> ACI Case D or similar
        # Approx values for slab with stiff edge beam
        return {'neg_ext': 0.30, 'pos': 0.50, 'neg_int': 0.70, 'desc': "End Span with Edge Beam"}
    else:
        # Case: Slab without beams (Unrestrained Edge) -> Flat Plate
        return {'neg_ext': 0.26, 'pos': 0.52, 'neg_int': 0.70, 'desc': "End Span (Unrestrained Edge)"}

def render_ddm_tab(calc_obj):
    st.header("1️⃣ Direct Design Method (DDM)")
    st.markdown("---")

    # --------------------------------------------------------------------------
    # 1. EXTRACT DATA & GEOMETRY CHECK
    # --------------------------------------------------------------------------
    geom = calc_obj['geom']
    loads = calc_obj['loads']
    mat = calc_obj['mat']
    
    # Identify Location Context
    # We need to know if we are designing an "Interior Span" or "End Span"
    # Logic: If user selected 'Edge Column' or 'Corner Column', we calculate the End Span.
    # If 'Interior Column', we calculate the Interior Span.
    
    # Retrieve flags (assuming calc_obj has these or we derive them)
    # Note: In app.py, we didn't explicitly store 'col_location' string in calc_obj, 
    # but we can infer from L1_l and L1_r.
    
    # Let's verify standard spans
    l1_left = geom.get('L1_l', 6.0)
    l1_right = geom.get('L1_r', 6.0)
    
    is_edge_col = (l1_left < 0.1 or l1_right < 0.1)
    is_end_span = is_edge_col # If calculating at edge column, we are analyzing the end span
    
    has_edge_beam = False
    if 'edge_beam' in calc_obj and calc_obj['edge_beam']['has_beam']:
        has_edge_beam = True

    # Define Analysis Span (L1) and Width (L2)
    # DDM creates a "Frame" along L1
    if is_edge_col:
        L1 = max(l1_left, l1_right) # Use the existing span
    else:
        L1 = l1_right # Default to right span for interior
        
    L2 = geom['L2'] # Transverse width
    c1 = calc_obj['col_size']['c1'] / 100.0 # m
    c2 = calc_obj['col_size']['c2'] / 100.0 # m
    
    # Clear Span Calculation (Ln)
    Ln = L1 - c1 # Simple face-to-face approximation
    if Ln < 0.65 * L1: Ln = 0.65 * L1 # Code limit

    # Load
    w_u = loads['w_total'] # kg/m2
    
    # --------------------------------------------------------------------------
    # 2. STATIC MOMENT (Mo) - SHOW FULL CALC
    # --------------------------------------------------------------------------
    st.subheader("Step 1: Total Static Moment ($M_0$)")
    
    # Formula Display
    st.latex(r"M_0 = \frac{w_u \ell_2 (\ell_n)^2}{8}")
    
    c_m1, c_m2 = st.columns([1.5, 1])
    with c_m1:
        st.write("**Substitution:**")
        st.write(f"- $w_u$ (Factored Load) = **{w_u:.2f}** kg/m²")
        st.write(f"- $\ell_2$ (Transverse Width) = **{L2:.2f}** m")
        st.write(f"- $\ell_1$ (Longitudinal Span) = {L1:.2f} m")
        st.write(f"- $c_1$ (Column dim) = {c1:.2f} m")
        st.write(f"- $\ell_n$ (Clear Span) = {L1:.2f} - {c1:.2f} = **{Ln:.2f}** m")
        
    # Calculation
    # M0 in kg-m
    M0_kgm = (w_u * L2 * (Ln**2)) / 8
    M0_kNm = M0_kgm * 9.80665 / 1000 # Convert to kN-m
    
    with c_m2:
        st.info(f"""
        **Result:**
        $$ M_0 = {M0_kgm:,.2f} \\text{{ kg-m}} $$
        $$ M_0 \\approx {M0_kNm:.2f} \\text{{ kN-m}} $$
        """)

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 3. LONGITUDINAL DISTRIBUTION (COEFFICIENTS)
    # --------------------------------------------------------------------------
    st.subheader("Step 2: Longitudinal Distribution")
    
    # Get Coefficients
    coeffs = get_moment_coefficients(is_end_span, has_edge_beam)
    
    st.markdown(f"**Condition:** `{coeffs['desc']}`")
    if is_end_span and has_edge_beam:
        st.caption("✅ Edge Beam detected: Exterior Negative Moment coefficient increased.")
    elif is_end_span and not has_edge_beam:
        st.caption("⚠️ No Edge Beam: Exterior Negative Moment is small (torsional flexibility).")

    # Calculate Moments
    m_neg_ext = M0_kNm * coeffs['neg_ext']
    m_pos     = M0_kNm * coeffs['pos']
    m_neg_int = M0_kNm * coeffs['neg_int']

    # Display in Columns
    col_ext, col_pos, col_int = st.columns(3)
    
    # Define styling helper
    def stat_card(col, title, coef, val, color="red"):
        with col:
            st.markdown(f"**{title}**")
            st.markdown(f"Factor: `{coef:.2f}`")
            if color=="green":
                st.success(f"**{val:.2f}** kN.m")
            else:
                st.error(f"**{val:.2f}** kN.m")

    # Show End Span vs Interior Span Layout
    if is_end_span:
        stat_card(col_ext, "Ext. Negative (-)", coeffs['neg_ext'], m_neg_ext)
        stat_card(col_pos, "Positive (+)", coeffs['pos'], m_pos, "green")
        stat_card(col_int, "Int. Negative (-)", coeffs['neg_int'], m_neg_int)
    else:
        # Interior Span (Symmetrical)
        stat_card(col_ext, "Negative (-)", coeffs['neg_ext'], m_neg_ext)
        stat_card(col_pos, "Positive (+)", coeffs['pos'], m_pos, "green")
        stat_card(col_int, "Negative (-)", coeffs['neg_int'], m_neg_int)

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 4. TRANSVERSE DISTRIBUTION (COL STRIP VS MID STRIP)
    # --------------------------------------------------------------------------
    st.subheader("Step 3: Transverse Distribution")
    st.info("💡 Distributing Total Moment into **Column Strip (CS)** and **Middle Strip (MS)**")

    # Percentages Logic (Simplified ACI Table)
    # Interior Negative: 75% CS, 25% MS
    # Positive: 60% CS, 40% MS
    # Exterior Negative: 
    #   - If Edge Beam (beta_t > 2.5): 75% CS
    #   - If No Beam (beta_t = 0): 100% CS (Theory says most goes to stiff col strip)
    
    # Setup Factors
    f_neg_int_cs = 0.75
    f_pos_cs = 0.60
    
    if is_end_span:
        if has_edge_beam:
            f_neg_ext_cs = 0.80 # Slightly higher for stiff edge
        else:
            f_neg_ext_cs = 1.00 # All to column strip if no edge beam torsion
    else:
        f_neg_ext_cs = 0.75 # Symmetrical Interior

    # Calculate
    data = []
    
    # Row 1: Ext Negative (or Left Neg)
    row1 = {
        "Location": "Exterior Neg (-)" if is_end_span else "Negative (-)",
        "Total M (kN.m)": f"{m_neg_ext:.2f}",
        "% CS": f"{f_neg_ext_cs*100:.0f}%",
        "M_CS (kN.m)": m_neg_ext * f_neg_ext_cs,
        "% MS": f"{(1-f_neg_ext_cs)*100:.0f}%",
        "M_MS (kN.m)": m_neg_ext * (1-f_neg_ext_cs)
    }
    data.append(row1)
    
    # Row 2: Positive
    row2 = {
        "Location": "Positive (+)",
        "Total M (kN.m)": f"{m_pos:.2f}",
        "% CS": f"{f_pos_cs*100:.0f}%",
        "M_CS (kN.m)": m_pos * f_pos_cs,
        "% MS": f"{(1-f_pos_cs)*100:.0f}%",
        "M_MS (kN.m)": m_pos * (1-f_pos_cs)
    }
    data.append(row2)

    # Row 3: Int Negative
    row3 = {
        "Location": "Interior Neg (-)" if is_end_span else "Negative (-)",
        "Total M (kN.m)": f"{m_neg_int:.2f}",
        "% CS": f"{f_neg_int_cs*100:.0f}%",
        "M_CS (kN.m)": m_neg_int * f_neg_int_cs,
        "% MS": f"{(1-f_neg_int_cs)*100:.0f}%",
        "M_MS (kN.m)": m_neg_int * (1-f_neg_int_cs)
    }
    data.append(row3)
    
    # Display DataFrame
    df = pd.DataFrame(data)
    
    # Formatting
    st.dataframe(
        df.style.format({
            "M_CS (kN.m)": "{:.2f}",
            "M_MS (kN.m)": "{:.2f}"
        }),
        use_container_width=True
    )
    
    # --------------------------------------------------------------------------
    # 5. VISUAL DIAGRAM
    # --------------------------------------------------------------------------
    st.markdown("### 📊 Moment Envelope (Approx)")
    
    # Simple matplotlib plot of the moment diagram
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(8, 3))
    x = [0, 0.5, 1.0] # Relative Length
    
    # Values
    y_ext = -m_neg_ext
    y_pos = m_pos
    y_int = -m_neg_int
    
    # Plot curve (Parabolic approx)
    x_plot = np.linspace(0, 1, 100)
    # Parabola fitting: y = ax^2 + bx + c
    # x=0, y=y_ext; x=1, y=y_int; max at x~0.4-0.6? 
    # Simplified visual: Just lines for now or a generic parabola
    # Let's use a Bezier or just scatter points connected
    
    ax.plot([0, 0], [0, y_ext], color='red', lw=2, label='Neg Moment')
    ax.plot([1, 1], [0, y_int], color='red', lw=2)
    
    # Draw simplified curve
    # Midpoint approx
    ax.plot([0, 0.5, 1], [y_ext, y_pos, y_int], 'o--', color='blue', alpha=0.5)
    
    # Smooth curve
    poly = np.polyfit([0, 0.5, 1], [y_ext, y_pos, y_int], 2)
    y_smooth = np.polyval(poly, x_plot)
    ax.plot(x_plot, y_smooth, color='black', lw=2, label='Moment Dist.')
    
    ax.axhline(0, color='black', lw=0.5)
    ax.set_title(f"Moment Diagram: {coeffs['desc']}")
    ax.set_ylabel("Moment (kN.m)")
    ax.set_xlabel("Span Ratio")
    ax.grid(True, linestyle='--', alpha=0.5)
    
    st.pyplot(fig)

    st.success("✅ DDM Calculation Complete. Ready for Reinforcement Design.")
