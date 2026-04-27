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
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_slab_section_with_rebar(inputs, df_design=None):
    """
    Generates a Cross-Section View of the slab showing top and bottom reinforcement.
    """
    fig, ax = plt.subplots(figsize=(10, 3.5))
    
    # Extract Geometry from inputs
    L1 = inputs.get('L1', 8.0)
    h_slab = inputs.get('h_slab_cm', 20.0) / 100.0  # Convert to meters
    c1 = inputs.get('c1', 0.5)
    has_drop = inputs.get('has_drop', False)
    h_drop = inputs.get('h_drop', h_slab * 100) / 100.0
    
    # Visual limits
    plot_width = L1 + 2 * c1
    
    # 1. Draw Columns (Supports)
    # Left Column
    ax.add_patch(patches.Rectangle((-c1/2, -1.0), c1, 1.0, fill=True, color='#64748b', zorder=2))
    # Right Column
    ax.add_patch(patches.Rectangle((L1 - c1/2, -1.0), c1, 1.0, fill=True, color='#64748b', zorder=2))
    
    # 2. Draw Drop Panels (if any)
    if has_drop and h_drop > h_slab:
        drop_w = L1 / 3.0  # Approximate drop panel width for visual
        drop_depth = h_drop - h_slab
        ax.add_patch(patches.Rectangle((-drop_w/2, -drop_depth), drop_w, drop_depth, fill=True, color='#e2e8f0', edgecolor='#0f172a', zorder=3))
        ax.add_patch(patches.Rectangle((L1 - drop_w/2, -drop_depth), drop_w, drop_depth, fill=True, color='#e2e8f0', edgecolor='#0f172a', zorder=3))

    # 3. Draw Slab
    ax.add_patch(patches.Rectangle((-c1, 0), plot_width, h_slab, fill=True, facecolor='#e2e8f0', edgecolor='#0f172a', lw=1.5, zorder=4))
    
    # 4. Draw Rebars
    cover = 0.03  # 3 cm concrete cover
    
    # Top Rebars (over supports - Negative Moment)
    ax.plot([-c1*0.8, L1*0.3], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5, zorder=5, label='Top Rebar (Support)')
    ax.plot([L1*0.7, L1 + c1*0.8], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5, zorder=5)
    
    # Bottom Rebars (midspan - Positive Moment)
    ax.plot([L1*0.1, L1*0.9], [cover, cover], color='#3b82f6', lw=2.5, zorder=5, label='Bottom Rebar (Midspan)')
    
    # 5. Annotations & Dimension Lines
    # Slab thickness dimension
    ax.annotate('', xy=(L1/2, 0), xytext=(L1/2, h_slab), arrowprops=dict(arrowstyle='<->', color='#0f172a', lw=1.5), zorder=6)
    ax.text(L1/2 + 0.1, h_slab/2, f'h = {h_slab*100:.1f} cm', va='center', fontweight='bold', fontsize=10)
    
    # Span dimension
    ax.annotate('', xy=(0, -0.5), xytext=(L1, -0.5), arrowprops=dict(arrowstyle='<->', color='#475569', lw=1.5), zorder=6)
    ax.text(L1/2, -0.4, f'Span L = {L1:.2f} m', ha='center', va='bottom', color='#334155', fontweight='bold', fontsize=10)

    # Styling
    ax.set_title("Slab Cross-Section Details", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(-c1*1.5, L1 + c1*1.5)
    ax.set_ylim(-0.8, h_slab + 0.2)
    ax.axis('off')
    
    # Add legend at top right
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.15), frameon=False, ncol=2)
    
    plt.tight_layout()
    return fig
    
    return fig
