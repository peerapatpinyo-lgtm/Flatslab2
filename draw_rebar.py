# draw_rebar.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_rebar_plan(L1_m, L2_m, b_col_cm, bar_top_type, bar_bot_type):
    """Generates a matplotlib figure for Typical Flat Slab Rebar Plan View."""
    
    L1_cm = L1_m * 100
    L2_cm = L2_m * 100
    
    fig, ax = plt.figure(figsize=(10, 8)), plt.gca()
    
    # Boundary and Geometry (simulate 2x2 bay to show strips)
    ax.add_patch(patches.Rectangle((0, 0), L1_cm*2, L2_cm*2, facecolor='#f8f9fa', edgecolor='black', linewidth=1.5, hatch='//'))
    
    # Grid lines and Columns centers
    col_x = [0, L1_cm, L1_cm*2]
    col_y = [0, L2_cm, L2_cm*2]
    for x in col_x:
        ax.axvline(x, color='gray', linestyle='--')
    for y in col_y:
        ax.axhline(y, color='gray', linestyle='--')
        
    # Highlighting Column Strip Analyzed Area (Central Joint)
    ax.add_patch(patches.Rectangle((L1_cm/2, L2_cm/2), L1_cm, b_col_cm, facecolor='#ffcccc66', edgecolor='none'))
    
    # columns (simplified points)
    ax.scatter(col_x * 3, col_y * 3, color='black', marker='s', s=200, zorder=10)
    
    # --- Drawing Top Rebar (Support) - RED ---
    # Typical ACI detail: top bars extend approx 0.3L into adjacent span
    top_extend = L1_cm * 0.3
    bars_y_neg = [L2_cm - b_col_cm/3, L2_cm + b_col_cm/3]
    for y in bars_y_neg:
        # Rebar line
        ax.plot([L1_cm - top_extend, L1_cm + top_extend], [y, y], color='red', linewidth=2.5, solid_capstyle='round')
        # Arrows indicating hooks/cutoffs
        ax.arrow(L1_cm + top_extend, y, 5, 0, head_width=8, head_length=15, fc='red', ec='red')
        ax.arrow(L1_cm - top_extend, y, -5, 0, head_width=8, head_length=15, fc='red', ec='red')

    # --- Drawing Bottom Rebar (Mid-Span) - BLUE ---
    # Typical ACI detail: bottom bars usually full span or overlapping near column
    bars_y_pos = [L2_cm*0.25, L2_cm*0.75, L2_cm*1.25, L2_cm*1.75]
    for y in bars_y_pos:
        ax.plot([L1_cm*0.05, L1_cm*1.95], [y, y], color='blue', linewidth=1.5, linestyle=':', dash_capstyle='round')

    # --- Annotations ---
    # Legend simulates selected rebar
    legend_top = f"Top Bar Detail: {bar_top_type} (Typical ACI Cutoff)"
    legend_bot = f"Bottom Bar Detail: {bar_bot_type} (Typical Continuous)"
    
    ax.text(L1_cm*2 * 0.02, L2_cm*2 * 0.95, legend_top, color='red', weight='bold', fontsize=12)
    ax.text(L1_cm*2 * 0.02, L2_cm*2 * 0.90, legend_bot, color='blue', weight='bold', fontsize=12)
    
    # Dimension Lines
    ax.annotate('', xy=(0, -20), xytext=(L1_cm, -20), arrowprops=dict(arrowstyle='<->', color='gray'))
    ax.text(L1_cm/2, -60, f"Bay L1: {L1_m:.2f} m", color='gray', ha='center')
    
    ax.annotate('', xy=(-20, 0), xytext=(-20, L2_cm), arrowprops=dict(arrowstyle='<->', color='gray'))
    ax.text(-60, L2_cm/2, f"Bay L2:\n{L2_m:.2f} m", color='gray', va='center', rotation='vertical')

    plt.title("TYPICAL FLAT SLAB REINFORCEMENT PLAN (Analyzed Direction)", fontsize=16, weight='bold')
    plt.xlabel("L1 direction (cm)", fontsize=12)
    plt.ylabel("L2 direction (cm)", fontsize=12)
    plt.grid(color='#f0f0f0')
    plt.axis('equal') # Maintain proper engineering scale
    return fig

def draw_rebar_section(h_cm, L1_m, c1_cm, bar_top_type, bar_bot_type):
    """Generates a matplotlib figure for Typical Flat Slab Rebar Section View."""
    
    L_draw_cm = L1_m * 100 * 1.5 # Draw 1.5 bays for context
    c1_cm_val = c1_cm
    
    fig, ax = plt.figure(figsize=(10, 5)), plt.gca()
    
    # Hatching for Concrete
    ax.fill_between([0, L_draw_cm], [0, 0], [h_cm, h_cm], facecolor='#e9ecef', hatch='.', edgecolor='black', linewidth=2)
    
    # Columns stub (simulated centers)
    col_xs = [L1_m*100 * 0.25, L1_m*100 * 1.25]
    for x in col_xs:
        ax.fill_between([x - c1_cm_val/2, x + c1_cm_val/2], [-h_cm/2, h_cm], [0, 2*h_cm], facecolor='#adb5bd', hatch='.', edgecolor='gray')
    
    # Cover settings
    cover_top_cm = 2.5
    cover_bot_cm = 2.5
    d_top_rebar_cm = h_cm - cover_top_cm
    d_bot_rebar_cm = cover_bot_cm
    
    # --- Drawing Top Rebar (Support Negative) - RED ---
    top_extend = L1_m * 100 * 0.3 # 0.3L extend
    for col_x in col_xs:
        bar_start, bar_end = col_x - top_extend, col_x + top_extend
        # Line with standard hooks at cutoffs for Flat Slab
        ax.plot([bar_start, bar_end], [d_top_rebar_cm, d_top_rebar_cm], color='red', linewidth=3, solid_capstyle='round')
        ax.plot([bar_start, bar_start], [d_top_rebar_cm, d_top_rebar_cm - h_cm/4], color='red', linewidth=3)
        ax.plot([bar_end, bar_end], [d_top_rebar_cm, d_top_rebar_cm - h_cm/4], color='red', linewidth=3)

    # --- Drawing Bottom Rebar (Continuous Positive) - BLUE ---
    # Represented as continuous lines near bottom
    ax.plot([0, L_draw_cm], [d_bot_rebar_cm, d_bot_rebar_cm], color='blue', linewidth=2, linestyle='-')
    ax.plot([0, L_draw_cm], [d_bot_rebar_cm + h_cm/8, d_bot_rebar_cm + h_cm/8], color='blue', linewidth=2, linestyle='-', alpha=0.5)

    # --- Annotation Callouts ---
    # Top Rebar label callout
    ax.annotate(f"TOP REBAR:\n{bar_top_type}", xy=(col_xs[1] + top_extend*0.8, d_top_rebar_cm), xytext=(col_xs[1] + top_extend*1.5, h_cm * 1.5),
                arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=6), color='red', weight='bold')
    
    # Bottom Rebar label callout
    ax.annotate(f"BOTTOM REBAR:\n{bar_bot_type}", xy=(L_draw_cm/2, d_bot_rebar_cm), xytext=(L_draw_cm/2, -h_cm * 1.0),
                arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=6), color='blue', ha='center', weight='bold')

    # Dimensions
    plt.title("TYPICAL FLAT SLAB CROSS-SECTION DRAFT", fontsize=16, weight='bold')
    ax.annotate('', xy=(-30, 0), xytext=(-30, h_cm), arrowprops=dict(arrowstyle='<->', color='gray'))
    ax.text(-60, h_cm/2, f"h_slab:\n{h_cm:.1f} cm", color='gray', va='center')
    
    # Center lines annotation
    for x in col_xs:
        ax.axvline(x, color='gray', linestyle='-.')
        ax.text(x, -h_cm*0.8, "CL Column", color='gray', rotation='vertical', va='top', ha='center')

    plt.grid(False)
    plt.axis('equal')
    ax.get_yaxis().set_visible(False) # Hide mathematical Y axis
    return fig
