# app_viz.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from app_config import COLORS, setup_matplotlib_style

# Apply style immediately when imported
setup_matplotlib_style()

def draw_dim_line(ax, start, end, text, offset=0.5, axis='x'):
    """Helper function for professional engineering dimension lines"""
    arrow_style = dict(arrowstyle='<|-|>', color=COLORS['dim_line'], linewidth=1.0, shrinkA=0, shrinkB=0)
    ext_line_style = dict(color=COLORS['dim_line'], linewidth=0.5, linestyle='-')
    
    if axis == 'x':
        ax.annotate('', xy=(start[0], start[1]-offset), xytext=(end[0], end[1]-offset), arrowprops=arrow_style)
        ax.plot([start[0], start[0]], [start[1]-0.1, start[1]-offset-0.2], **ext_line_style)
        ax.plot([end[0], end[0]], [end[1]-0.1, end[1]-offset-0.2], **ext_line_style)
        ax.text((start[0]+end[0])/2, start[1]-offset-0.3, text, ha='center', va='top', color=COLORS['dim_line'])
    elif axis == 'y':
        ax.annotate('', xy=(start[0]-offset, start[1]), xytext=(end[0]-offset, end[1]), arrowprops=arrow_style)
        ax.plot([start[0]-0.1, start[0]-offset-0.2], [start[1], start[1]], **ext_line_style)
        ax.plot([end[0]-0.1, end[0]-offset-0.2], [end[1], end[1]], **ext_line_style)
        ax.text(start[0]-offset-0.3, (start[1]+end[1])/2, text, ha='right', va='center', rotation=90, color=COLORS['dim_line'])

def draw_plan_view(L1_l, L1_r, L2_t, L2_b, c1_cm, c2_cm, col_loc, has_drop, d_w1, d_w2, cant_params, edge_beam_params):
    """High-fidelity Plan View with Cantilevers and Complete Dimensions"""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    c1_m = c1_cm / 100
    c2_m = c2_cm / 100
    
    # --- 1. FIXED BOUNDARY LOGIC (CORRECTED) ---
    # ถ้าค่า L เป็น 0 (ขอบเขต) ให้วาดพื้นคลุมถึงแค่ขอบเสา (c/2) เพื่อความสมจริง
    # ไม่ใช้ Logic เช็คชื่อ String แล้ว แต่เช็คจากค่า L ที่ส่งมาจริง
    slab_L = L1_l if L1_l > 0 else c1_m/2
    slab_R = L1_r if L1_r > 0 else c1_m/2  # เผื่อกรณีเสาขอบขวา
    slab_T = L2_t if L2_t > 0 else c2_m/2
    slab_B = L2_b if L2_b > 0 else c2_m/2

    # 2. Cantilever Logic (Expand Boundary)
    cant_L_ext = cant_params['L_left'] if cant_params['has_left'] else 0
    cant_R_ext = cant_params['L_right'] if cant_params['has_right'] else 0
    
    # Adjust total drawing limits
    draw_L = slab_L + cant_L_ext
    draw_R = slab_R + cant_R_ext
    
    # 3. Draw Main Zones (Middle Strip)
    # วาดพื้นหลัก
    ax.add_patch(patches.Rectangle((-slab_L, -slab_B), slab_L + slab_R, slab_B + slab_T,
                                   facecolor=COLORS['ms_bg'], edgecolor='gray', linewidth=1, zorder=0))
    
    # 4. Draw Cantilever Zones (Distinct Color)
    if cant_params['has_left']:
        ax.add_patch(patches.Rectangle((-slab_L - cant_L_ext, -slab_B), cant_L_ext, slab_B + slab_T,
                                              facecolor=COLORS['cantilever_bg'], edgecolor='gray', linestyle='--', linewidth=1, zorder=0))
        # Label
        ax.text(-slab_L - cant_L_ext/2, 0, "CANTILEVER", rotation=90, ha='center', va='center', 
                color='#8E44AD', fontsize=8, fontweight='bold')

    if cant_params['has_right']:
        ax.add_patch(patches.Rectangle((slab_R, -slab_B), cant_R_ext, slab_B + slab_T,
                                              facecolor=COLORS['cantilever_bg'], edgecolor='gray', linestyle='--', linewidth=1, zorder=0))
        # Label
        ax.text(slab_R + cant_R_ext/2, 0, "CANTILEVER", rotation=90, ha='center', va='center', 
                color='#8E44AD', fontsize=8, fontweight='bold')

    # 5. Column Strip Logic
    min_span = min(L1_l + L1_r, L2_t + L2_b)
    # ถ้า span ด้านใดเป็น 0 (Edge) ให้ใช้ span อีกฝั่งคำนวณแทน หรือใช้ค่าพื้นฐาน
    if min_span < 1.0: # กรณี Corner ที่ L รวมเหลือน้อย
        valid_spans = [x for x in [L1_l, L1_r, L2_t, L2_b] if x > 0]
        if valid_spans:
            min_span = min(valid_spans) * 2 # Approximate
        else:
            min_span = 4.0 # Fallback

    cs_width = 0.25 * min_span
    cs_top = min(cs_width, slab_T)
    cs_bot = min(cs_width, slab_B)
    
    # Draw CS Rect (Main Span)
    ax.add_patch(patches.Rectangle((-slab_L, -cs_bot), slab_L + slab_R, cs_top + cs_bot,
                                   facecolor=COLORS['cs_bg'], edgecolor='none', alpha=0.6, zorder=1))
    
    # Extend CS into Cantilever
    if cant_params['has_left']:
         ax.add_patch(patches.Rectangle((-slab_L - cant_L_ext, -cs_bot), cant_L_ext, cs_top + cs_bot,
                                    facecolor=COLORS['cs_bg'], edgecolor='none', alpha=0.4, zorder=1))
    if cant_params['has_right']:
         ax.add_patch(patches.Rectangle((slab_R, -cs_bot), cant_R_ext, cs_top + cs_bot,
                                    facecolor=COLORS['cs_bg'], edgecolor='none', alpha=0.4, zorder=1))

    # Dashed Separators
    line_props = dict(color=COLORS['strip_line'], linestyle='--', linewidth=0.8, alpha=0.7)
    if cs_top < slab_T: ax.axhline(y=cs_top, **line_props)
    if cs_bot < slab_B: ax.axhline(y=-cs_bot, **line_props)

    # Labeling
    ax.text((slab_R - slab_L)/2, 0, "COLUMN STRIP", color=COLORS['cs_text'], 
            fontsize=10, fontweight='bold', ha='center', va='center',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.3, pad=1))

    # --- Edge Beam (New Feature) ---
    if edge_beam_params and edge_beam_params.get('has_beam'):
        beam_w = edge_beam_params['width_cm'] / 100.0
        beam_color = '#C0392B' # Dark Red
        
        beam_rects = []
        # Logic: วาด Beam ตามขอบเขตที่มีอยู่จริง
        # กรณี Edge Column (L1_l=0) หรือ Corner -> มี Beam แนวตั้งที่ขอบซ้าย?
        # หรือมี Beam แนวนอนที่ขอบล่าง?
        # เพื่อความง่ายในการ Visualization: วาดรอบนอกสุดของ Slab
        
        # Top Edge
        if L2_t > 0: # Assume beam usually on free edge, but let's just outline the boundary
             pass 
        
        # Simplified: ถ้าเป็น Edge/Corner ให้วาด Beam ที่ขอบที่ "หายไป"
        # แต่ User Config มาแค่ "Has Beam" ไม่ได้บอกทิศทาง
        # สมมติ: วาด Beam ที่ขอบล่างเสมอถ้าเป็น Edge/Corner เพื่อสื่อความหมาย
        if col_loc in ["Edge Column", "Corner Column"]:
            beam_rect = patches.Rectangle((-draw_L, -slab_B), draw_L + draw_R, beam_w, 
                                          facecolor='none', edgecolor=beam_color, linestyle='--', linewidth=1.5, zorder=3)
            beam_rects.append(beam_rect)
            ax.text(0, -slab_B + beam_w/2, "EDGE BEAM", color=beam_color, fontsize=8, ha='center', va='center', fontweight='bold')

        for br in beam_rects:
            ax.add_patch(br)

    # 6. Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w1/2, -d_w2/2), d_w1, d_w2, 
                                          facecolor='none', edgecolor=COLORS['drop_panel_plan'], 
                                          linestyle='-', linewidth=2, zorder=5))

    # 7. Columns
    ax.add_patch(patches.Rectangle((-c1_m/2, -c2_m/2), c1_m, c2_m, 
                                   facecolor=COLORS['column'], edgecolor='black', hatch='//', zorder=10))
    
    # Ghost Columns (Only where span exists)
    ghost_props = dict(facecolor='white', edgecolor=COLORS['concrete_cut'], linestyle='--', linewidth=1.5, zorder=4)
    if L1_r > 1.0: ax.add_patch(patches.Rectangle((L1_r - c1_m/2, -c2_m/2), c1_m, c2_m, **ghost_props))
    if L1_l > 1.0: ax.add_patch(patches.Rectangle((-L1_l - c1_m/2, -c2_m/2), c1_m, c2_m, **ghost_props))
    if L2_t > 1.0: ax.add_patch(patches.Rectangle((-c1_m/2, L2_t - c2_m/2), c1_m, c2_m, **ghost_props)) # Top Ghost
    if L2_b > 1.0: ax.add_patch(patches.Rectangle((-c1_m/2, -L2_b - c2_m/2), c1_m, c2_m, **ghost_props)) # Bot Ghost
    
    # 8. Dimensions
    def draw_ext_dim(x1, y1, x2, y2, text, offset, fontsize=9):
        mid_x, mid_y = (x1 + x2)/2, (y1 + y2)/2
        if abs(x1 - x2) < 0.01: # Vertical
            x1 += offset; x2 += offset; mid_x += offset
            rot = 90; ha, va = ('right', 'center') if offset < 0 else ('left', 'center')
            ax.plot([x1-0.1, x1+0.1], [y1, y1], color=COLORS['dim_line'], lw=0.5)
            ax.plot([x2-0.1, x2+0.1], [y2, y2], color=COLORS['dim_line'], lw=0.5)
        else: # Horizontal
            y1 += offset; y2 += offset; mid_y += offset
            rot = 0; ha, va = ('center', 'top') if offset < 0 else ('center', 'bottom')
            ax.plot([x1, x1], [y1-0.1, y1+0.1], color=COLORS['dim_line'], lw=0.5)
            ax.plot([x2, x2], [y2-0.1, y2+0.1], color=COLORS['dim_line'], lw=0.5)
            
        ax.annotate('', xy=(x1, y1), xytext=(x2, y2), arrowprops=dict(arrowstyle='<|-|>', color=COLORS['dim_line'], lw=0.8))
        ax.text(mid_x, mid_y, text, rotation=rot, ha=ha, va=va, fontsize=fontsize, color=COLORS['dim_line'], fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1))

    m_x, m_y = -draw_L - 0.8, -slab_B - 0.8
    
    # --- Main Span Dimensions (Bottom) ---
    if cant_params['has_left']:
        draw_ext_dim(-slab_L - cant_L_ext, -slab_B, -slab_L, -slab_B, f"Cant L={cant_L_ext:.2f}", m_y - (-slab_B))
    
    if L1_l > 0.1: # Only draw if span exists
        draw_ext_dim(-L1_l, -slab_B, 0, -slab_B, f"L1(L)={L1_l:.2f}", m_y - (-slab_B))
    
    if L1_r > 0.1:
        draw_ext_dim(0, -slab_B, L1_r, -slab_B, f"L1(R)={L1_r:.2f}", m_y - (-slab_B))
    
    if cant_params['has_right']:
        draw_ext_dim(L1_r, -slab_B, L1_r + cant_R_ext, -slab_B, f"Cant R={cant_R_ext:.2f}", m_y - (-slab_B))

    # --- Main Span Dimensions (Left) ---
    # L2 Top
    if L2_t > 0.1:
        draw_ext_dim(-draw_L, 0, -draw_L, L2_t, f"L2(T)={L2_t:.2f}", m_x - (-draw_L))
    # L2 Bottom
    if L2_b > 0.1:
         draw_ext_dim(-draw_L, -L2_b, -draw_L, 0, f"L2(B)={L2_b:.2f}", m_x - (-draw_L))

    # --- Member Size Dimensions (Near Center) ---
    # Column c1/c2
    draw_ext_dim(-c1_m/2, c2_m/2 + 0.3, c1_m/2, c2_m/2 + 0.3, f"c1={c1_cm:.0f}cm", 0, fontsize=8)
    draw_ext_dim(c1_m/2 + 0.3, -c2_m/2, c1_m/2 + 0.3, c2_m/2, f"c2={c2_cm:.0f}cm", 0, fontsize=8)

    # Drop Panel w1/w2 (if present)
    if has_drop:
        draw_ext_dim(-d_w1/2, -d_w2/2 - 0.3, d_w1/2, -d_w2/2 - 0.3, f"w1={d_w1:.2f}m", 0, fontsize=8)
        draw_ext_dim(-d_w1/2 - 0.3, -d_w2/2, -d_w1/2 - 0.3, d_w2/2, f"w2={d_w2:.2f}m", 0, fontsize=8)


    ax.set_title(f"STRUCTURAL LAYOUT: {col_loc.upper()}", fontsize=12, pad=20, fontweight='bold', color='#566573')
    ax.set_xlim(-draw_L - 1.5, draw_R + 1.5)
    ax.set_ylim(-slab_B - 2.0, slab_T + 1.0)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_elevation_real_scale(h_up, h_lo, has_drop, h_drop_cm, drop_w1, c1_cm, h_slab_cm, 
                              is_roof, far_end_up, far_end_lo, cant_params, edge_beam_params):
    """High-fidelity Section View with Boundary Conditions, Cantilevers, and Complete Dimensions"""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    s_m = h_slab_cm / 100
    d_m = h_drop_cm / 100 if has_drop else 0
    c_m = c1_cm / 100
    d_w = drop_w1 if has_drop else 0
    
    # Setup Views
    # Cantilever View Extension
    cant_L_draw = cant_params['L_left'] if cant_params['has_left'] else 1.5
    cant_R_draw = cant_params['L_right'] if cant_params['has_right'] else 1.5
    
    # Boundary logic for drawing
    x_min = -cant_L_draw if cant_params['has_left'] else -1.5
    x_max = cant_R_draw if cant_params['has_right'] else 1.5
    
    view_top = 0.8 if not is_roof else 0.1
    bot_struct = -(s_m + d_m)
    # INCREASED BOTTOM MARGIN for dimensions
    view_bot = bot_struct - 1.2 
    
    col_concrete = '#ECF0F1'
    col_cant = '#F4ECF7'
    col_hatch = '#BDC3C7'
    col_dim = '#2C3E50'
    
    # --- Helper: Draw Support Symbols ---
    def draw_support_symbol(x, y, kind, orientation='bottom'):
        """Draws Fixed or Pinned symbols"""
        sz = 0.15
        if kind == 'Fixed':
            ax.plot([x-sz, x+sz], [y, y], color='black', linewidth=2)
            if orientation == 'bottom':
                for i in np.arange(x-sz, x+sz, 0.05):
                    ax.plot([i, i-0.05], [y, y-0.05], color='black', linewidth=0.5)
            else: # top
                for i in np.arange(x-sz, x+sz, 0.05):
                    ax.plot([i, i-0.05], [y, y+0.05], color='black', linewidth=0.5)
        elif kind == 'Pinned':
            if orientation == 'bottom':
                triangle = patches.Polygon([[x, y], [x-sz/1.5, y-sz], [x+sz/1.5, y-sz]], 
                                           closed=True, facecolor='white', edgecolor='black', linewidth=1)
                base = patches.Rectangle((x-sz, y-sz-0.02), sz*2, 0.02, color='black')
            else: # top
                triangle = patches.Polygon([[x, y], [x-sz/1.5, y+sz], [x+sz/1.5, y+sz]], 
                                           closed=True, facecolor='white', edgecolor='black', linewidth=1)
                base = patches.Rectangle((x-sz, y+sz), sz*2, 0.02, color='black')
            
            ax.add_patch(triangle)
            ax.add_patch(base)
            circle = patches.Circle((x, y), 0.02, facecolor='white', edgecolor='black')
            ax.add_patch(circle)

    # 1. Structure
    if not is_roof:
        ax.add_patch(patches.Rectangle((-c_m/2, 0), c_m, view_top, facecolor='white', edgecolor='black', linewidth=1))
        draw_support_symbol(0, view_top, far_end_up, 'top')
    
    # Column Lower
    ax.add_patch(patches.Rectangle((-c_m/2, view_bot+0.4), c_m, abs((view_bot+0.4) - bot_struct), facecolor='white', edgecolor='black', linewidth=1))
    draw_support_symbol(0, view_bot+0.4, far_end_lo, 'bottom')

    # Slab
    left_x = -cant_params['L_left'] if cant_params['has_left'] else -1.5
    right_x = cant_params['L_right'] if cant_params['has_right'] else 1.5
    
    ax.add_patch(patches.Rectangle((left_x, -s_m), (abs(left_x)+right_x), s_m, facecolor=col_concrete, edgecolor='black', linewidth=1, zorder=5))
    ax.add_patch(patches.Rectangle((left_x, -s_m), (abs(left_x)+right_x), s_m, fill=False, edgecolor=col_hatch, hatch='///', linewidth=0, zorder=6))
    
    if cant_params['has_left']:
        ax.add_patch(patches.Rectangle((-cant_params['L_left'], -s_m), cant_params['L_left'], s_m, facecolor=col_cant, alpha=0.3, zorder=7))
    if cant_params['has_right']:
        ax.add_patch(patches.Rectangle((0, -s_m), cant_params['L_right'], s_m, facecolor=col_cant, alpha=0.3, zorder=7))

    if has_drop:
        ax.add_patch(patches.Rectangle((-d_w/2, bot_struct), d_w, d_m, facecolor=col_concrete, edgecolor='black', linewidth=1, zorder=5))
        ax.add_patch(patches.Rectangle((-d_w/2, bot_struct), d_w, d_m, fill=False, edgecolor=col_hatch, hatch='///', linewidth=0, zorder=6))

    # --- Edge Beam (Section View) ---
    if edge_beam_params and edge_beam_params.get('has_beam'):
        beam_h = edge_beam_params['depth_cm'] / 100.0
        beam_w = edge_beam_params['width_cm'] / 100.0
        # Draw beam on the Right side (Arbitrary convention for "Edge" view)
        beam_x_pos = right_x - beam_w if cant_params['has_right'] else 1.0 
        
        # Beam rectangle (hanging below slab)
        proj_h = beam_h - s_m
        if proj_h > 0:
            ax.add_patch(patches.Rectangle((beam_x_pos, -beam_h), beam_w, beam_h, 
                                           facecolor='#D98880', edgecolor='black', linewidth=1, zorder=8))
            ax.text(beam_x_pos + beam_w/2, -beam_h/2, "BM", color='white', fontsize=7, ha='center', va='center')

    # 2. Dimensions
    def draw_side_dim(y_start, y_end, x_loc, label, fontsize=9):
        ax.annotate('', xy=(x_loc, y_start), xytext=(x_loc, y_end),
                    arrowprops=dict(arrowstyle='<|-|>', color=col_dim, linewidth=0.8, shrinkA=0, shrinkB=0))
        mid_y = (y_start + y_end) / 2
        ax.text(x_loc + 0.15, mid_y, label, ha='center', va='center', rotation=90, 
                fontsize=fontsize, color=col_dim, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
        ax.plot([x_loc-0.1, x_loc+0.1], [y_start, y_start], color=col_dim, lw=0.5)
        ax.plot([x_loc-0.1, x_loc+0.1], [y_end, y_end], color=col_dim, lw=0.5)

    def draw_bot_dim(x_start, x_end, y_loc, label, fontsize=9):
         ax.annotate('', xy=(x_start, y_loc), xytext=(x_end, y_loc),
                    arrowprops=dict(arrowstyle='<|-|>', color=col_dim, linewidth=0.8, shrinkA=0, shrinkB=0))
         mid_x = (x_start + x_end) / 2
         ax.text(mid_x, y_loc - 0.1, label, ha='center', va='top',
                fontsize=fontsize, color=col_dim, fontweight='bold',
                 bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
         ax.plot([x_start, x_start], [y_loc-0.1, y_loc+0.1], color=col_dim, lw=0.5)
         ax.plot([x_end, x_end], [y_loc-0.1, y_loc+0.1], color=col_dim, lw=0.5)

    # Dimensions placement
    ax.text(left_x, -s_m/2, f" h_s={h_slab_cm}cm", va='center', ha='right', fontsize=9, color=col_dim)

    dim_x_right = right_x + 0.5
    if not is_roof:
        draw_side_dim(0, view_top, dim_x_right, f"Up: {h_up:.2f}m")
    draw_side_dim(bot_struct, view_bot+0.4, dim_x_right, f"Lo: {h_lo:.2f}m")

    if has_drop:
        # Ensure dimensions are FAR outside the drop panel width
        dim_x_outside_drop = -d_w/2 - 0.8 
        draw_side_dim(-s_m, bot_struct, dim_x_outside_drop, f"h_d={h_drop_cm}cm", fontsize=8)
        draw_side_dim(0, bot_struct, dim_x_outside_drop - 0.5, f"Total={h_slab_cm+h_drop_cm}cm", fontsize=8)
        draw_bot_dim(-d_w/2, d_w/2, bot_struct - 0.2, f"w1={d_w:.2f}m", fontsize=8)

    # Column Width (Moved up slightly to fit)
    draw_bot_dim(-c_m/2, c_m/2, view_bot - 0.05, f"c1={c1_cm}cm", fontsize=9)

    dim_y_top = 0.3
    if cant_params['has_left']:
        L = cant_params['L_left']
        ax.annotate('', xy=(-L, dim_y_top), xytext=(0, dim_y_top), arrowprops=dict(arrowstyle='<|-|>', color='purple'))
        ax.text(-L/2, dim_y_top + 0.05, f"Cantilever {L:.2f}m", color='purple', ha='center', fontsize=9, fontweight='bold')
        ax.plot([-L, -L], [0, dim_y_top], linestyle=':', color='purple', lw=0.5)

    if cant_params['has_right']:
        L = cant_params['L_right']
        ax.annotate('', xy=(0, dim_y_top), xytext=(L, dim_y_top), arrowprops=dict(arrowstyle='<|-|>', color='purple'))
        ax.text(L/2, dim_y_top + 0.05, f"Cantilever {L:.2f}m", color='purple', ha='center', fontsize=9, fontweight='bold')
        ax.plot([L, L], [0, dim_y_top], linestyle=':', color='purple', lw=0.5)

    ax.text(left_x + 0.2, 0.05, "▼ T.O. Slab (+0.00)", color='blue', fontsize=8, fontweight='bold')
    ax.axhline(0, color='blue', linestyle='-.', linewidth=0.5, alpha=0.5)

    ax.set_aspect('equal')
    
    # EXPANDED LIMITS TO PREVENT CLIPPING
    ax.set_xlim(left_x - 1.5, right_x + 1.5)
    ax.set_ylim(view_bot - 0.8, view_top + 0.5) 
    
    ax.axis('off')
    
    title_suffix = " (Pinned Ends)" if (far_end_lo == 'Pinned' or far_end_up == 'Pinned') else ""
    ax.set_title(f"SECTION DETAIL: {is_roof and 'ROOF' or 'INTERMEDIATE'} JOINT{title_suffix}", 
                 fontsize=10, color='gray', pad=10, fontweight='bold')
    
    # AUTO ADJUST LAYOUT
    fig.tight_layout()
    
    return fig
