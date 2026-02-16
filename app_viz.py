# app_viz.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from app_config import COLORS, setup_matplotlib_style

setup_matplotlib_style()

def draw_smart_dim(ax, p1, p2, text, offset=0.5, orientation='h', color=COLORS['dim_line']):
    """
    Draws a professional engineering dimension line.
    p1, p2: tuples (x, y) start and end points
    offset: distance from the object to the dimension line
    orientation: 'h' (horizontal) or 'v' (vertical)
    """
    x1, y1 = p1
    x2, y2 = p2
    
    arrow_props = dict(arrowstyle='<|-|>', color=color, linewidth=0.8, shrinkA=0, shrinkB=0)
    ext_props = dict(color=color, linewidth=0.5, linestyle='-')
    
    if orientation == 'h':
        dim_y = y1 + offset
        mid_x = (x1 + x2) / 2
        
        # 1. Main Arrow Line
        ax.annotate('', xy=(x1, dim_y), xytext=(x2, dim_y), arrowprops=arrow_props)
        
        # 2. Extension Lines (Vertical)
        # Gap from object = 0.1, Overshoot = 0.1
        gap = 0.1 if offset > 0 else -0.1
        overshoot = 0.1 if offset > 0 else -0.1
        
        ax.plot([x1, x1], [y1 + gap, dim_y + overshoot], **ext_props)
        ax.plot([x2, x2], [y2 + gap, dim_y + overshoot], **ext_props)
        
        # 3. Text
        ax.text(mid_x, dim_y + (0.1 if offset > 0 else -0.3), text, 
                ha='center', va='bottom' if offset > 0 else 'top', 
                color=color, fontsize=9, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.9, pad=0.5))
                
    elif orientation == 'v':
        dim_x = x1 + offset
        mid_y = (y1 + y2) / 2
        
        # 1. Main Arrow Line
        ax.annotate('', xy=(dim_x, y1), xytext=(dim_x, y2), arrowprops=arrow_props)
        
        # 2. Extension Lines (Horizontal)
        gap = 0.1 if offset > 0 else -0.1
        overshoot = 0.1 if offset > 0 else -0.1
        
        ax.plot([x1 + gap, dim_x + overshoot], [y1, y1], **ext_props)
        ax.plot([x2 + gap, dim_x + overshoot], [y2, y2], **ext_props)
        
        # 3. Text
        ax.text(dim_x + (0.1 if offset > 0 else -0.1), mid_y, text, 
                ha='left' if offset > 0 else 'right', va='center', rotation=90,
                color=color, fontsize=9, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.9, pad=0.5))

def draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_loc, has_drop, d_w1, d_w2, cant_params):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    c1 = c1_cm/100
    c2 = c2_cm/100
    
    # Boundaries
    bound_L = L1_l if L1_l > 0 else c1/2
    bound_R = L1_r
    bound_T = L2_t
    bound_B = L2_b if L2_b > 0 else c2/2
    
    cant_L = cant_params['L_left'] if cant_params['has_left'] else 0
    cant_R = cant_params['L_right'] if cant_params['has_right'] else 0
    
    # 1. Main Slab (Concrete Area)
    total_L = -bound_L - cant_L
    total_W = bound_L + bound_R + cant_L + cant_R
    total_H = bound_T + bound_B
    
    # Cantilever Left
    if cant_params['has_left']:
        rect = patches.Rectangle((-bound_L-cant_L, -bound_B), cant_L, total_H, 
                               facecolor=COLORS['cantilever'], alpha=0.3, edgecolor='none')
        ax.add_patch(rect)
    
    # Cantilever Right
    if cant_params['has_right']:
        rect = patches.Rectangle((bound_R, -bound_B), cant_R, total_H, 
                               facecolor=COLORS['cantilever'], alpha=0.3, edgecolor='none')
        ax.add_patch(rect)
        
    # Main Span
    rect_main = patches.Rectangle((-bound_L, -bound_B), bound_L+bound_R, total_H,
                                  facecolor=COLORS['concrete'], edgecolor=COLORS['concrete_outline'], linewidth=1.5, zorder=0)
    ax.add_patch(rect_main)

    # 2. Center Lines
    ax.axhline(0, color=COLORS['center_line'], linestyle='-.', linewidth=0.8)
    ax.axvline(0, color=COLORS['center_line'], linestyle='-.', linewidth=0.8)
    
    # 3. Drop Panel
    if has_drop:
        dp = patches.Rectangle((-d_w1/2, -d_w2/2), d_w1, d_w2, 
                               fill=False, edgecolor=COLORS['rebar'], linestyle='--', linewidth=1.5)
        ax.add_patch(dp)
        ax.text(-d_w1/2, -d_w2/2 - 0.2, f"Drop Panel {d_w1}x{d_w2}m", color=COLORS['rebar'], fontsize=8)

    # 4. Column (Hatch)
    col = patches.Rectangle((-c1/2, -c2/2), c1, c2, facecolor='gray', hatch='///', edgecolor='black', zorder=10)
    ax.add_patch(col)
    
    # 5. Dimensions (The Smart Part)
    dim_offset_y = -bound_B - 0.8
    
    # Chain Dimensioning for Width (L1)
    current_x = -bound_L - cant_L
    
    if cant_params['has_left']:
        draw_smart_dim(ax, (current_x, -bound_B), (-bound_L, -bound_B), 
                       f"Cant={cant_L:.2f}m", offset=-0.8, orientation='h')
        current_x = -bound_L
        
    if L1_l > 0:
        draw_smart_dim(ax, (-bound_L, -bound_B), (0, -bound_B), 
                       f"L1(Left)={L1_l:.2f}m", offset=-0.8, orientation='h')
        
    draw_smart_dim(ax, (0, -bound_B), (bound_R, -bound_B), 
                   f"L1(Right)={bound_R:.2f}m", offset=-0.8, orientation='h')
                   
    if cant_params['has_right']:
        draw_smart_dim(ax, (bound_R, -bound_B), (bound_R+cant_R, -bound_B), 
                       f"Cant={cant_R:.2f}m", offset=-0.8, orientation='h')

    # Dimension for Height (L2)
    dim_offset_x = -bound_L - cant_L - 0.8
    draw_smart_dim(ax, (0, 0), (0, bound_T), f"L2(Top)={bound_T:.2f}m", offset=-(bound_L+cant_L+0.5), orientation='v')
    if bound_B > c2:
        draw_smart_dim(ax, (0, -bound_B), (0, 0), f"L2(Bot)={bound_B:.2f}m", offset=-(bound_L+cant_L+0.5), orientation='v')

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"PLAN VIEW: {col_loc}", pad=20)
    return fig

def draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, 
                              is_roof, far_end_up, far_end_lo, cant_params):
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Units to meters
    c1 = c1_cm/100
    hs = h_slab_cm/100
    hd = h_drop_cm/100 if has_drop else 0
    dw = drop_w1 if has_drop else 0
    
    # Coordinates
    slab_top = 0
    slab_bot = -hs
    drop_bot = -(hs + hd)
    
    # Span logic for drawing
    draw_L = cant_params['L_left'] if cant_params['has_left'] else 1.5
    draw_R = cant_params['L_right'] if cant_params['has_right'] else 1.5
    x_min = -draw_L
    x_max = draw_R
    
    # 1. Columns
    # Upper
    if not is_roof:
        ax.add_patch(patches.Rectangle((-c1/2, 0), c1, h_up, facecolor='white', edgecolor='black'))
        # Symbol Top
        if far_end_up == 'Fixed':
            ax.plot([-0.3, 0.3], [h_up, h_up], 'k-', lw=2)
            for i in np.arange(-0.3, 0.3, 0.05): ax.plot([i, i-0.05], [h_up, h_up+0.05], 'k-', lw=0.5)
        else: # Pinned
            ax.plot(0, h_up, 'wo', markeredgecolor='k')
            ax.plot([-0.1, 0, 0.1], [h_up+0.15, h_up, h_up+0.15], 'k-')
            
    # Lower
    col_bot_top = drop_bot if has_drop else slab_bot
    col_height = h_lo - (abs(col_bot_top)) # Net height
    ax.add_patch(patches.Rectangle((-c1/2, -h_lo), c1, h_lo+col_bot_top, facecolor='white', edgecolor='black'))
    
    # Symbol Bottom
    if far_end_lo == 'Fixed':
        ax.plot([-0.3, 0.3], [-h_lo, -h_lo], 'k-', lw=2)
        for i in np.arange(-0.3, 0.3, 0.05): ax.plot([i, i-0.05], [-h_lo, -h_lo-0.05], 'k-', lw=0.5)
    else: # Pinned
        ax.plot(0, -h_lo, 'wo', markeredgecolor='k', zorder=10)
        ax.plot([-0.15, 0, 0.15], [-h_lo-0.2, -h_lo, -h_lo-0.2], 'k-')
        ax.plot([-0.2, 0.2], [-h_lo-0.2, -h_lo-0.2], 'k-')

    # 2. Slab & Drop
    # Main Slab
    slab_poly = patches.Polygon([
        (x_min, slab_top), (x_max, slab_top), (x_max, slab_bot), (x_min, slab_bot)
    ], closed=True, facecolor=COLORS['concrete'], edgecolor='black')
    ax.add_patch(slab_poly)
    
    # Drop Panel
    if has_drop:
        drop_poly = patches.Polygon([
            (-dw/2, slab_bot), (dw/2, slab_bot), (dw/2, drop_bot), (-dw/2, drop_bot)
        ], closed=True, facecolor=COLORS['concrete'], edgecolor='black')
        ax.add_patch(drop_poly)

    # 3. Dimensions (Smart)
    # Vertical Dims (Right side)
    dim_x = x_max + 0.5
    
    if not is_roof:
        draw_smart_dim(ax, (0, 0), (0, h_up), f"H_up={h_up:.2f}m", offset=dim_x, orientation='v')
    
    draw_smart_dim(ax, (0, -h_lo), (0, 0), f"H_lo={h_lo:.2f}m", offset=dim_x, orientation='v')
    
    # Slab Thickness (Detailed)
    ax.annotate(f"t={h_slab_cm}cm", xy=(x_min, slab_bot/2), xytext=(x_min-0.8, slab_bot/2),
                arrowprops=dict(arrowstyle='->', color='blue'), color='blue', va='center')
    
    if has_drop:
        ax.annotate(f"Drop={h_drop_cm}cm", xy=(-dw/2, (slab_bot+drop_bot)/2), xytext=(-dw/2-0.8, drop_bot),
                    arrowprops=dict(arrowstyle='->', color='red'), color='red', va='center')

    # Horizontal Dims (Cantilever)
    if cant_params['has_left']:
        draw_smart_dim(ax, (-cant_params['L_left'], 0), (0, 0), 
                       f"Cant L={cant_params['L_left']:.2f}m", offset=0.5, orientation='h')

    ax.axhline(0, color='blue', linestyle=':', linewidth=0.5)
    ax.text(x_max+0.2, 0, "Level +0.00", color='blue', fontsize=8, va='center')

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("SECTION A-A (True Scale)", pad=20)
    return fig
