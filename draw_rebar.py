# draw_rebar.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.projections import register_projection

# --- Helper Function: Draw Modern CAD Dimension Line ---
def draw_cad_dimension(ax, x1, x2, y, text, text_offset=18, is_vertical=False):
    """Draws a clean, standard CAD dimension line with ticks."""
    line_color = '#555555' # Dark gray for dimension lines
    text_color = 'black'
    
    if not is_vertical:
        # Horizontal Dimension
        # Main Line
        ax.plot([x1, x2], [y, y], color=line_color, lw=0.8)
        # Extension Lines
        ext_len = 20
        ax.plot([x1, x1], [y-ext_len, y+ext_len], color=line_color, lw=0.5)
        ax.plot([x2, x2], [y-ext_len, y+ext_len], color=line_color, lw=0.5)
        # Architectural Ticks (45-degree slashes)
        tick_len = 10
        ax.plot([x1-tick_len, x1+tick_len], [y-tick_len, y+tick_len], color=text_color, lw=1.2)
        ax.plot([x2-tick_len, x2+tick_len], [y-tick_len, y+tick_len], color=text_color, lw=1.2)
        # Text
        ax.text((x1+x2)/2, y + text_offset, text, ha='center', va='center', fontsize=9, color=text_color, weight='bold')
    else:
        # Vertical Dimension (e.g., slab thickness)
        dim_x = x1
        ax.plot([dim_x, dim_x], [x2, y], color=line_color, lw=0.8)
        ax.plot([dim_x-ext_len, dim_x+ext_len], [x2, x2], color=line_color, lw=0.5)
        ax.plot([dim_x-ext_len, dim_x+ext_len], [y, y], color=line_color, lw=0.5)
        # Ticks
        ax.plot([dim_x-tick_len, dim_x+tick_len], [x2-tick_len, x2+tick_len], color=text_color, lw=1.2)
        ax.plot([dim_x-tick_len, dim_x+tick_len], [y-tick_len, y+tick_len], color=text_color, lw=1.2)
        # Text
        ax.text(dim_x + text_offset, (x2+y)/2, text, va='center', ha='left', fontsize=9, color=text_color, weight='bold', rotation='vertical')

# ✅ อัปเดตฟังก์ชันหลักให้เน้นความสะอาดและลดการซ้อนกัน
def draw_drafting_details(L1_l, L1_r, L2, c1_cm, c2_cm, h_cm, 
                          top_col_sz, top_col_sp, bot_col_sz, bot_col_sp,
                          top_mid_sz, top_mid_sp, bot_mid_sz, bot_mid_sp):
    
    st.subheader("🛠️ Full Framing & Detailing Plan (L1-Direction)")
    st.markdown("แบบร่างผังการเสริมเหล็กเต็มช่วงเสา (Full Panel) แสดงทั้งแถบเสา (Column Strip) และแถบกลาง (Middle Strip) จัดองค์ประกอบใหม่เพื่อลดการซ้อนกันของข้อความ")
    
    # Geometry in cm
    x_l = -L1_l * 100 / 2
    x_r = L1_r * 100 / 2
    y_t = L2 * 100 / 2
    y_b = -L2 * 100 / 2
    
    # Calculate Strip Widths
    col_strip_w = (min(max(L1_l, L1_r), L2) / 2.0) * 100
    cs_half = col_strip_w / 2
    
    st.divider()

    # ==========================================
    # 1. PLAN VIEW (Full Panel Framing Plan)
    # ==========================================
    # Increased vertical size to accommodate dimensions without crowding
    fig_plan, ax_plan = plt.subplots(figsize=(10, 7))
    
    # 🏗️ Concrete Boundaries & Zone Indications
    # Main Slab Outline
    ax_plan.plot([x_l, x_r], [y_t, y_t], color='black', lw=1.5)
    ax_plan.plot([x_l, x_r], [y_b, y_b], color='black', lw=1.5)
    
    # Column Strip / Middle Strip Boundary (Gray dashed line)
    # Move boundaries slightly away from 0 to provide more central drawing space
    ax_plan.axhline(cs_half, color='#888888', linestyle='--', lw=1.2)
    ax_plan.axhline(-cs_half, color='#888888', linestyle='--', lw=1.2)
    
    # Light gray solid fill for strips to give CAD depth
    ax_plan.add_patch(patches.Rectangle((x_l, -cs_half), x_r - x_l, col_strip_w, facecolor='#F1F3F5', zorder=1))
    ax_plan.add_patch(patches.Rectangle((x_l, cs_half), x_r - x_l, y_t - cs_half, facecolor='#DEE2E6', zorder=1))
    ax_plan.add_patch(patches.Rectangle((x_l, y_b), x_r - x_l, cs_half + y_b, facecolor='#DEE2E6', zorder=1))

    # Centerlines (Grid Lines A & 1)
    ax_plan.axhline(0, color='#666666', linestyle='-.', lw=0.8, zorder=2) # X Grid
    ax_plan.axvline(0, color='#666666', linestyle='-.', lw=0.8, zorder=2) # Y Grid
    
    # Column intersection (Solid gray)
    ax_plan.add_patch(patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, facecolor='#495057', edgecolor='black', lw=1, zorder=5))

    # Zone Labels (Static, out of rebar way)
    ax_plan.text(x_l + 20, 10, "COLUMN STRIP (CS)", color='#333333', fontsize=8, weight='bold')
    ax_plan.text(x_l + 20, cs_half + 10, "MIDDLE STRIP (MS)", color='#333333', fontsize=8, weight='bold')

    # ---- 🟥 TOP REINFORCEMENT (Support - Red Lines) ----
    top_ext_l, top_ext_r = -0.3 * (L1_l * 100), 0.3 * (L1_r * 100)
    top_ext_mid_l, top_ext_mid_r = -0.22 * (L1_l * 100), 0.22 * (L1_r * 100)
    
    # Lineweights hierarchy: Rebars are thickest (3)
    
    # Top CS Bar
    y_top_cs = c2_cm / 2 + 30 # Offset from column face
    ax_plan.plot([top_ext_l, top_ext_r], [y_top_cs, y_top_cs], color='#E63946', lw=3, solid_capstyle='round', zorder=6)
    ax_plan.plot([top_ext_l, top_ext_l], [y_top_cs-12, y_top_cs+12], color='#E63946', lw=2)
    ax_plan.plot([top_ext_r, top_ext_r], [y_top_cs-12, y_top_cs+12], color='#E63946', lw=2)

    # Top MS Bar
    y_top_ms = cs_half + 30
    ax_plan.plot([top_ext_mid_l, top_ext_mid_r], [y_top_ms, y_top_ms], color='#E63946', lw=3, solid_capstyle='round', zorder=6)
    ax_plan.plot([top_ext_mid_l, top_ext_mid_l], [y_top_ms-10, y_top_ms+10], color='#E63946', lw=2)
    ax_plan.plot([top_ext_mid_r, top_ext_mid_r], [y_top_ms-10, y_top_ms+10], color='#E63946', lw=2)

    # ---- 🟦 BOTTOM REINFORCEMENT (Mid-span - Navy Dashed Lines) ----
    bot_cover = 25 # Distance from span ends
    
    # Bottom CS Bar
    y_bot_cs = -c2_cm / 2 - 30
    ax_plan.plot([x_l+bot_cover, x_r-bot_cover], [y_bot_cs, y_bot_cs], color='#1D3557', lw=3, linestyle='--', solid_capstyle='round', zorder=6)

    # Bottom MS Bar
    y_bot_ms = -cs_half - 30
    ax_plan.plot([x_l+bot_cover, x_r-bot_cover], [y_bot_ms, y_bot_ms], color='#1D3557', lw=3, linestyle='--', solid_capstyle='round', zorder=6)

    # ---- 🏷️ REBAR CALLOUTS (Clean & Spaced Multi-leaders) ----
    # Multi-leaders use strict 90-degree elbows to separate text from structure
    
    # 🟥 Top Bar Callouts (Red)
    # Placing Top CS label on the Right, Top MS label on the Left
    ax_plan.annotate(f"TOP (CS):\n{top_col_sz}@{top_col_sp}\n(L=0.3L)", 
                     xy=(top_ext_r - 30, y_top_cs), xytext=(top_ext_r + 60, y_top_cs + 80),
                     fontsize=9, weight='bold', color='#E63946',
                     arrowprops=dict(arrowstyle="-|>", connectionstyle="angle,angleA=0,angleB=90,rad=0", color='#E63946', lw=1.5))

    ax_plan.annotate(f"TOP (MS):\n{top_mid_sz}@{top_mid_sp}\n(L=0.22L)", 
                     xy=(top_ext_mid_l + 30, y_top_ms), xytext=(top_ext_mid_l - 120, y_top_ms + 80),
                     fontsize=9, weight='bold', color='#E63946',
                     arrowprops=dict(arrowstyle="-|>", connectionstyle="angle,angleA=0,angleB=90,rad=0", color='#E63946', lw=1.5))

    # 🟦 Bottom Bar Callouts (Navy)
    # Placing Bottom CS label on the Right, Bottom MS label on the Left
    ax_plan.annotate(f"BOT (CS):\n{bot_col_sz}@{bot_col_sp}", 
                     xy=(x_r - bot_cover - 30, y_bot_cs), xytext=(x_r - 20, y_bot_cs - 100),
                     fontsize=9, weight='bold', color='#1D3557',
                     arrowprops=dict(arrowstyle="-|>", connectionstyle="angle,angleA=0,angleB=90,rad=0", color='#1D3557', lw=1.5))

    ax_plan.annotate(f"BOT (MS):\n{bot_mid_sz}@{bot_mid_sp}", 
                     xy=(x_l + bot_cover + 30, y_bot_ms), xytext=(x_l - 60, y_bot_ms - 100),
                     fontsize=9, weight='bold', color='#1D3557',
                     arrowprops=dict(arrowstyle="-|>", connectionstyle="angle,angleA=0,angleB=90,rad=0", color='#1D3557', lw=1.5))

    # 📐 DIMENSIONS (Engineering Style below the slab)
    dim_y = y_b - 120
    draw_cad_dimension(ax_plan, x_l, 0, dim_y, f"L1 (Left) = {L1_l} m")
    draw_cad_dimension(ax_plan, 0, x_r, dim_y, f"L1 (Right) = {L1_r} m")

    ax_plan.set_title("FRAMING PLAN - FULL PANEL REINFORCEMENT", fontsize=11, weight='bold', loc='left')
    ax_plan.set_xlim(x_l - 180, x_r + 200) # Increased margin for callouts
    ax_plan.set_ylim(y_b - 180, y_t + 100) # Increased margin for dimensions/zones
    ax_plan.set_aspect('equal')
    ax_plan.axis('off')
    
    st.pyplot(fig_plan)
    st.divider()

    # ==========================================
    # 2. SECTION VIEW (Section A-A: At Support)
    # ==========================================
    fig_sec, ax_sec = plt.subplots(figsize=(10, 4))
    
    # Concrete fills (Solid gray CAD look)
    ax_sec.add_patch(patches.Rectangle((x_l, 0), x_r - x_l, h_cm, facecolor='#F1F3F5', edgecolor='black', lw=1.5))
    ax_sec.add_patch(patches.Rectangle((-c1_cm/2, -h_cm*1.5), c1_cm, h_cm*1.5, facecolor='#DEE2E6', edgecolor='black', lw=1.5))
    
    # Centerline Grid 1
    ax_sec.axvline(0, color='#888888', linestyle='-.', lw=0.8)

    cov = 3.0 # Standard covering in cm
    
    # Section view shows Column Strip reinforcement (because it cuts through the joint)
    
    # Top CS Bar (Red)
    ax_sec.plot([top_ext_l, top_ext_r], [h_cm - cov, h_cm - cov], color='#E63946', lw=3, zorder=4)
    ax_sec.plot([top_ext_l, top_ext_l], [h_cm - cov, h_cm - cov - 10], color='#E63946', lw=3) # Hook Down
    ax_sec.plot([top_ext_r, top_ext_r], [h_cm - cov, h_cm - cov - 10], color='#E63946', lw=3) # Hook Down

    # Bottom CS Bar (Navy)
    ax_sec.plot([x_l+10, x_r-10], [cov, cov], color='#1D3557', lw=3, zorder=4)

    # Annotations (Spaced vertically)
    ax_sec.annotate(f"TOP (CS): {top_col_sz}@{top_col_sp}", 
                    xy=(top_ext_l/2, h_cm - cov), xytext=(top_ext_l/2 - 20, h_cm + 50),
                    ha='center', fontsize=9, weight='bold', color='#E63946',
                    arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=0", color='#E63946', lw=1.2))
    
    ax_sec.annotate(f"BOT (CS): {bot_col_sz}@{bot_col_sp}", 
                    xy=(x_r/2, cov), xytext=(x_r/2 + 20, -h_cm - 20),
                    ha='center', fontsize=9, weight='bold', color='#1D3557',
                    arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=0", color='#1D3557', lw=1.2))

    # Dimensions
    draw_cad_dimension(ax_sec, top_ext_l, 0, h_cm + 90, "0.3 L1")
    draw_cad_dimension(ax_sec, 0, top_ext_r, h_cm + 90, "0.3 L1")
    
    # Slab Thickness Dimension on Right
    dim_x_s = x_r + 40
    ax_sec.plot([dim_x_s, dim_x_s], [0, h_cm], color='#555555', lw=0.8)
    ax_sec.plot([dim_x_s-8, dim_x_s+8], [0, 0], color='black', lw=1.2)
    ax_sec.plot([dim_x_s-8, dim_x_s+8], [h_cm, h_cm], color='black', lw=1.2)
    ax_sec.text(dim_x_s + 20, h_cm/2, f"h={h_cm:.0f}cm", va='center', ha='left', fontsize=9, color='black', weight='bold')

    ax_sec.set_title("SECTION A-A (AT JOINT SUPPORT)", fontsize=11, weight='bold', loc='left')
    
    # Dynamic scaling for section proportion (keeps h look proportional to L)
    ax_sec.set_xlim(x_l - 70, x_r + 150)
    ax_sec.set_ylim(-h_cm*2.5, h_cm*5) 
    ax_sec.axis('off')

    st.pyplot(fig_sec)
