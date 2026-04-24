# draw_rebar.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Helper: Draw Professional CAD Dimensions ---
def draw_dim_line(ax, x1, x2, y, text, text_offset=15):
    # Thin lines for dimensions
    ax.plot([x1, x2], [y, y], color='#555555', lw=0.8)
    ax.plot([x1, x1], [y-15, y+15], color='#555555', lw=0.5)
    ax.plot([x2, x2], [y-15, y+15], color='#555555', lw=0.5)
    
    # Standard Architectural Ticks
    tick = 10
    ax.plot([x1-tick, x1+tick], [y-tick, y+tick], color='black', lw=1.2)
    ax.plot([x2-tick, x2+tick], [y-tick, y+tick], color='black', lw=1.2)
    
    # Clean text
    ax.text((x1+x2)/2, y + text_offset, text, ha='center', va='center', fontsize=9, color='black', weight='bold')

def draw_drafting_details(L1_l, L1_r, L2, c1_cm, c2_cm, h_cm, top_col_sz, top_col_sp, bot_col_sz, bot_col_sp):
    st.subheader("📐 Construction Detailing (Clean Style)")
    
    # Geometry in cm
    x_l = -L1_l * 100 / 2
    x_r = L1_r * 100 / 2
    y_t = L2 * 100 / 2
    y_b = -L2 * 100 / 2
    col_strip = (min(max(L1_l, L1_r), L2) / 2.0) * 100
    
    st.divider()

    # ==========================================
    # 1. PLAN VIEW (Clean Structural Plan)
    # ==========================================
    fig_plan, ax_plan = plt.subplots(figsize=(10, 5.5))
    
    # Slab Outline
    ax_plan.plot([x_l, x_r], [y_t, y_t], color='black', lw=1.5)
    ax_plan.plot([x_l, x_r], [y_b, y_b], color='black', lw=1.5)
    
    # Column Strip Indication (Very light dash)
    ax_plan.axhline(col_strip/2, color='#CCCCCC', linestyle='--', lw=1)
    ax_plan.axhline(-col_strip/2, color='#CCCCCC', linestyle='--', lw=1)
    ax_plan.text(x_l + 20, col_strip/2 + 10, "COLUMN STRIP", color='#999999', fontsize=8, weight='bold')

    # Grid & Column
    ax_plan.axhline(0, color='#888888', linestyle='-.', lw=0.8) # X Grid
    ax_plan.axvline(0, color='#888888', linestyle='-.', lw=0.8) # Y Grid
    
    # Solid dark gray column for strong contrast
    ax_plan.add_patch(patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, facecolor='#333333', edgecolor='black', zorder=5))

    # --- Rebars (Thick lines for emphasis) ---
    # Top Bars (Red)
    top_ext_l, top_ext_r = -0.3 * (L1_l * 100), 0.3 * (L1_r * 100)
    y_top_bar = c2_cm/2 + 25
    ax_plan.plot([top_ext_l, top_ext_r], [y_top_bar, y_top_bar], color='#E63946', lw=3, zorder=6)
    ax_plan.plot([top_ext_l, top_ext_l], [y_top_bar-10, y_top_bar+10], color='#E63946', lw=2) # End marks
    ax_plan.plot([top_ext_r, top_ext_r], [y_top_bar-10, y_top_bar+10], color='#E63946', lw=2)
    
    # Bottom Bars (Navy Blue)
    y_bot_bar = -c2_cm/2 - 25
    ax_plan.plot([x_l+25, x_r-25], [y_bot_bar, y_bot_bar], color='#1D3557', lw=3, linestyle='--', zorder=6)
    
    # Multi-leaders (Strict 90-degree angles)
    ax_plan.annotate(f"TOP: {top_col_sz}@{top_col_sp} (L=0.3L)", 
                     xy=(top_ext_r - 40, y_top_bar), xytext=(top_ext_r, y_top_bar + 60),
                     fontsize=9, weight='bold', color='#E63946',
                     arrowprops=dict(arrowstyle="-|>", connectionstyle="angle,angleA=0,angleB=90,rad=0", color='#E63946', lw=1.5))

    ax_plan.annotate(f"BOT: {bot_col_sz}@{bot_col_sp}", 
                     xy=(x_l + 60, y_bot_bar), xytext=(x_l + 20, y_bot_bar - 80),
                     fontsize=9, weight='bold', color='#1D3557',
                     arrowprops=dict(arrowstyle="-|>", connectionstyle="angle,angleA=0,angleB=90,rad=0", color='#1D3557', lw=1.5))

    # Dimensions
    draw_dim_line(ax_plan, x_l, 0, y_b - 50, f"L1 = {L1_l} m")
    draw_dim_line(ax_plan, 0, x_r, y_b - 50, f"L1 = {L1_r} m")

    ax_plan.set_title("PLAN VIEW (Structural)", fontsize=11, weight='bold', loc='left')
    ax_plan.set_xlim(x_l - 50, x_r + 50)
    ax_plan.set_ylim(y_b - 120, y_t + 50)
    ax_plan.set_aspect('equal')
    ax_plan.axis('off')
    
    st.pyplot(fig_plan)
    st.divider()

    # ==========================================
    # 2. SECTION VIEW (Proportional Cross-Section)
    # ==========================================
    fig_sec, ax_sec = plt.subplots(figsize=(10, 3.5))
    
    # Concrete fills (Solid light gray for modern CAD look)
    ax_sec.add_patch(patches.Rectangle((x_l, 0), x_r - x_l, h_cm, facecolor='#F1F3F5', edgecolor='black', lw=1.5))
    ax_sec.add_patch(patches.Rectangle((-c1_cm/2, -h_cm*1.5), c1_cm, h_cm*1.5, facecolor='#DEE2E6', edgecolor='black', lw=1.5))
    
    # Centerline
    ax_sec.axvline(0, color='#888888', linestyle='-.', lw=0.8)

    cov = 3.0 # Covering
    
    # Top Bar (Red)
    ax_sec.plot([top_ext_l, top_ext_r], [h_cm - cov, h_cm - cov], color='#E63946', lw=3, zorder=4)
    ax_sec.plot([top_ext_l, top_ext_l], [h_cm - cov, h_cm - cov - 10], color='#E63946', lw=3) # Hook down
    ax_sec.plot([top_ext_r, top_ext_r], [h_cm - cov, h_cm - cov - 10], color='#E63946', lw=3) # Hook down

    # Bottom Bar (Navy)
    ax_sec.plot([x_l+10, x_r-10], [cov, cov], color='#1D3557', lw=3, zorder=4)

    # Annotations
    ax_sec.annotate(f"TOP BAR: {top_col_sz}@{top_col_sp}", 
                    xy=(top_ext_l/2, h_cm - cov), xytext=(top_ext_l/2, h_cm + 30),
                    ha='center', fontsize=9, weight='bold', color='#E63946',
                    arrowprops=dict(arrowstyle="-|>", color='#E63946', lw=1.2))
    
    ax_sec.annotate(f"BOT BAR: {bot_col_sz}@{bot_col_sp}", 
                    xy=(x_r/2, cov), xytext=(x_r/2, -h_cm),
                    ha='center', fontsize=9, weight='bold', color='#1D3557',
                    arrowprops=dict(arrowstyle="-|>", color='#1D3557', lw=1.2))

    # Dimensions
    draw_dim_line(ax_sec, top_ext_l, 0, h_cm + 60, "0.3 L1")
    draw_dim_line(ax_sec, 0, top_ext_r, h_cm + 60, "0.3 L1")
    
    # Slab Thickness Dimension
    dim_x = x_r + 30
    ax_sec.plot([dim_x, dim_x], [0, h_cm], color='#555555', lw=0.8)
    ax_sec.plot([dim_x-8, dim_x+8], [0, 0], color='black', lw=1.2)
    ax_sec.plot([dim_x-8, dim_x+8], [h_cm, h_cm], color='black', lw=1.2)
    ax_sec.text(dim_x + 15, h_cm/2, f"h={h_cm:.0f}cm", va='center', fontsize=9, weight='bold')

    ax_sec.set_title("SECTION AT SUPPORT", fontsize=11, weight='bold', loc='left')
    
    # Adjust dynamic limits so the section doesn't look overly stretched or squeezed
    ax_sec.set_xlim(x_l - 50, x_r + 120)
    # The Y limit is scaled relative to the slab thickness to ensure it always looks like a slab
    ax_sec.set_ylim(-h_cm*2, h_cm*4) 
    ax_sec.axis('off')

    st.pyplot(fig_sec)
