import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_rebar_plan_view(inputs, df_design):
    """
    Generates a Reinforcement Plan View.
    Draws horizontal rebars for L1 direction and vertical rebars for L2 direction.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Extract Geometry
    L1 = inputs.get('L1', 8.0)
    L2 = inputs.get('L2', 6.0)
    c1 = inputs.get('c1', 0.4)
    c2 = inputs.get('c2', 0.4)
    analysis_dir = str(inputs.get('analysis_dir', 'L1')).lower()
    
    # Draw Slab Outline
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, fill=False, edgecolor='black', linewidth=2.5, zorder=3))
    
    # Draw Columns (Assumed at corners for visual scale in a typical panel)
    col_coords = [(0,0), (L1,0), (0,L2), (L1,L2)]
    for (cx, cy) in col_coords:
        col = patches.Rectangle((cx - c1/2, cy - c2/2), c1, c2, fill=True, color='dimgray', zorder=4)
        ax.add_patch(col)
        
    # Check Direction to plot rebars
    # Assumes "l1" or "long" means X-direction (Horizontal)
    is_l1_dir = 'l1' in analysis_dir or 'long' in analysis_dir
    
    if is_l1_dir:
        # ➡️ Draw Horizontal Bars (L1 Direction)
        ax.set_title("Reinforcement Plan View - L1 Direction", fontsize=14, fontweight='bold', pad=15)
        
        # Draw Column Strip (Top Bars) - Representative lines
        ax.hlines(y=[L2*0.85, L2*0.90, L2*0.95], xmin=0, xmax=L1*0.3, color='red', lw=1.5, label='Top Rebar (Support)')
        ax.hlines(y=[L2*0.85, L2*0.90, L2*0.95], xmin=L1*0.7, xmax=L1, color='red', lw=1.5)
        
        # Draw Middle Strip (Bottom Bars) - Representative lines
        y_bottoms = np.linspace(L2*0.25, L2*0.75, 7)
        ax.hlines(y=y_bottoms, xmin=0.05*L1, xmax=0.95*L1, color='blue', lw=1.2, linestyle='--', label='Bottom Rebar (Midspan)')
        
    else:
        # ⬆️ Draw Vertical Bars (L2 Direction)
        ax.set_title("Reinforcement Plan View - L2 Direction", fontsize=14, fontweight='bold', pad=15)
        
        # Draw Column Strip (Top Bars) - Representative lines
        ax.vlines(x=[L1*0.85, L1*0.90, L1*0.95], ymin=0, ymax=L2*0.3, color='red', lw=1.5, label='Top Rebar (Support)')
        ax.vlines(x=[L1*0.85, L1*0.90, L1*0.95], ymin=L2*0.7, ymax=L2, color='red', lw=1.5)
        
        # Draw Middle Strip (Bottom Bars) - Representative lines
        x_bottoms = np.linspace(L1*0.25, L1*0.75, 7)
        ax.vlines(x=x_bottoms, ymin=0.05*L2, ymax=0.95*L2, color='blue', lw=1.2, linestyle='--', label='Bottom Rebar (Midspan)')

    # Formatting and Styling
    ax.set_aspect('equal')
    ax.set_xlim(-c1, L1 + c1)
    ax.set_ylim(-c2, L2 + c2)
    ax.set_xlabel("L1 Dimension (m)", fontsize=10, fontweight='bold')
    ax.set_ylabel("L2 Dimension (m)", fontsize=10, fontweight='bold')
    
    # Prevent duplicate labels in legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper right", bbox_to_anchor=(1.25, 1))
    
    ax.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()
    
    return fig
