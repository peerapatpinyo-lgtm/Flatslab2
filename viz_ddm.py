import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# Helper Function สำหรับดึงข้อความเหล็กเสริม (แก้ไข Logic แล้ว)
# ==========================================
def get_rebar_text(df, is_col_strip, is_negative, col_loc='Interior'):
    """
    ดึงขนาดและระยะแอดของเหล็กจาก edited_df 
    *อัปเดต: กรองกรณี Edge/Corner แยกต่างหาก
    """
    if df is None or df.empty or 'Location' not in df.columns:
        return "N/A"
        
    strip_kw = "Col" if is_col_strip else "Mid"
    
    # เงื่อนไขพิเศษสำหรับเสาริมและเสามุม
    if col_loc in ['Edge', 'Corner']:
        if is_negative:
            if is_col_strip:
                mom_kw = "Ext Neg" # ดึงเฉพาะเหล็กที่ขอบนอก (ไม่เอา Int Neg)
            else:
                return "N/A" # Middle Strip ไม่มีโมเมนต์ลบที่ขอบนอก ข้ามไปเลย
        else:
            mom_kw = "Pos"
    else:
        mom_kw = "Neg" if is_negative else "Pos"
    
    try:
        mask = df['Location'].str.contains(strip_kw, case=False, na=False) & \
               df['Location'].str.contains(mom_kw, case=False, na=False)
        
        match = df[mask]
        if not match.empty:
            row = match.iloc[0]
            bar_size = int(row.get('Bar Size (mm)', 12))
            spacing = float(row.get('Spacing (cm)', 20.0))
            return f"DB{bar_size} @{spacing:.1f}"
        return "N/A"
    except:
        return "N/A"

# --- ใน viz_ddm.py ---
# ==========================================
# 1. วาดรูป Plan View (แก้ไขการวาดเส้นเหล็ก Top MS แล้ว)
# ==========================================
def draw_rebar_plan_view(inputs, edited_df):
    # ดึงค่าพารามิเตอร์พื้นฐาน
    L1 = float(inputs.get('l1', inputs.get('L1', 5.0))) 
    L2 = float(inputs.get('l2', inputs.get('L2', 5.0))) 
    c1 = float(inputs.get('c1', 0.5))
    c2 = float(inputs.get('c2', 0.5))
    
    col_loc = str(inputs.get('col_loc', inputs.get('column_location', 'Interior'))).strip().title()
    analysis_dir = str(inputs.get('analysis_dir', 'X')).lower()
    is_y_axis = 'y' in analysis_dir or 'l2' in analysis_dir
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # ----------------------------------------------------
    # 🌟 1. Bounding Box (เสาอยู่ 0,0 เสมอ)
    # ----------------------------------------------------
    x_min, x_max = -L1/2.0, L1/2.0
    y_min, y_max = -L2/2.0, L2/2.0
    
    if col_loc == 'Edge':
        if not is_y_axis: 
            x_min = -c1/2.0
        else:
            y_min = -c2/2.0
    elif col_loc == 'Corner':
        x_min = -c1/2.0
        y_min = -c2/2.0

    slab_w = x_max - x_min
    slab_h = y_max - y_min
    
    # วาดแผ่นพื้น
    ax.add_patch(patches.Rectangle((x_min, y_min), slab_w, slab_h, fill=True, facecolor='#f8fafc', edgecolor='#94a3b8', lw=2, zorder=1))
    # วาดเสาตรงกลาง
    ax.add_patch(patches.Rectangle((-c1/2.0, -c2/2.0), c1, c2, fill=True, facecolor='#1e293b', zorder=2))
    
    # ดึงข้อความเหล็กเสริม (ส่ง col_loc เข้าไปด้วย)
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True, col_loc=col_loc)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False, col_loc=col_loc)
    ms_top = get_rebar_text(edited_df, is_col_strip=False, is_negative=True, col_loc=col_loc)
    ms_bot = get_rebar_text(edited_df, is_col_strip=False, is_negative=False, col_loc=col_loc)

    if is_y_axis:
        # ----------------------------------------------------
        # 🌟 2. Y-Axis Frame (วิเคราะห์ตามแนว L2)
        # ----------------------------------------------------
        cs_x_min = max(-L1/4.0, x_min)
        cs_x_max = min(L1/4.0, x_max)
        cs_w = cs_x_max - cs_x_min
        
        # วาดแถบ Column Strip
        ax.add_patch(patches.Rectangle((cs_x_min, y_min), cs_w, slab_h, fill=True, facecolor='#e2e8f0', alpha=0.6, edgecolor='none', zorder=1.5))
        if cs_x_min > x_min: ax.axvline(cs_x_min, color='#94a3b8', linestyle='-.', lw=1, zorder=1.5)
        if cs_x_max < x_max: ax.axvline(cs_x_max, color='#94a3b8', linestyle='-.', lw=1, zorder=1.5)
        
        ax.text((cs_x_min + cs_x_max)/2, y_min - 0.2, f'Column Strip\n(W = {cs_w:.2f}m)', va='top', ha='center', color='#334155', fontweight='bold', fontsize=9)
        
        x_top_pos = cs_x_min + cs_w * 0.75
        x_bot_pos = cs_x_min + cs_w * 0.25
        
        # เหล็ก CS
        top_y1, top_y2 = max(-L2/4, y_min), min(L2/4, y_max)
        ax.plot([x_top_pos, x_top_pos], [top_y1, top_y2], color='#ef4444', lw=2.5, linestyle='--', zorder=3)
        ax.text(x_top_pos + 0.15, (top_y1+top_y2)/2, f"Top(CS)\n{cs_top}", color='#ef4444', va='center', ha='left', fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        bot_y1, bot_y2 = y_min + 0.15, y_max - 0.15
        ax.plot([x_bot_pos, x_bot_pos], [bot_y1, bot_y2], color='#3b82f6', lw=2.5, zorder=3)
        ax.text(x_bot_pos - 0.15, (bot_y1+bot_y2)/2, f"Bot(CS)\n{cs_bot}", color='#3b82f6', va='center', ha='right', fontweight='bold', fontsize=9)
        
        # เหล็ก MS
        has_ms_right = (x_max - cs_x_max) > 0.1
        has_ms_left = (cs_x_min - x_min) > 0.1
        
        ms_x_list = []
        if has_ms_right: ms_x_list.append((cs_x_max + x_max)/2)
        if has_ms_left: ms_x_list.append((x_min + cs_x_min)/2)
        
        for ms_x in ms_x_list:
            ax.plot([ms_x, ms_x], [bot_y1, bot_y2], color='#3b82f6', lw=2, zorder=3)
            ax.text(ms_x - 0.1, (bot_y1+bot_y2)/2, f"Bot(MS): {ms_bot}", color='#3b82f6', va='center', ha='right', rotation=90, fontsize=9)
            
            # วาดเส้น Top MS เฉพาะเมื่อมีข้อมูล (ไม่เป็น N/A)
            if ms_top != "N/A":
                ax.plot([ms_x - 0.3, ms_x - 0.3], [top_y1, top_y2], color='#ef4444', lw=2, linestyle='--', zorder=3)
                ax.text(ms_x - 0.4, (top_y1+top_y2)/2, f"Top(MS): {ms_top}", color='#ef4444', va='center', ha='right', rotation=90, fontsize=9)

        axis_title = "Y-Axis Frame"
        
    else:
        # ----------------------------------------------------
        # 🌟 3. X-Axis Frame (วิเคราะห์ตามแนว L1)
        # ----------------------------------------------------
        cs_y_min = max(-L2/4.0, y_min)
        cs_y_max = min(L2/4.0, y_max)
        cs_w = cs_y_max - cs_y_min
        
        # วาดแถบ Column Strip
        ax.add_patch(patches.Rectangle((x_min, cs_y_min), slab_w, cs_w, fill=True, facecolor='#e2e8f0', alpha=0.6, edgecolor='none', zorder=1.5))
        if cs_y_min > y_min: ax.axhline(cs_y_min, color='#94a3b8', linestyle='-.', lw=1, zorder=1.5)
        if cs_y_max < y_max: ax.axhline(cs_y_max, color='#94a3b8', linestyle='-.', lw=1, zorder=1.5)
        
        ax.text(x_min - 0.2, (cs_y_min + cs_y_max)/2, f'Column Strip\n(W = {cs_w:.2f}m)', rotation=90, va='center', ha='right', color='#334155', fontweight='bold', fontsize=9)
        
        y_top_pos = cs_y_min + cs_w * 0.75
        y_bot_pos = cs_y_min + cs_w * 0.25
        
        # เหล็ก CS
        top_x1, top_x2 = max(-L1/4, x_min), min(L1/4, x_max)
        ax.plot([top_x1, top_x2], [y_top_pos, y_top_pos], color='#ef4444', lw=2.5, linestyle='--', zorder=3)
        ax.text((top_x1+top_x2)/2, y_top_pos + 0.15, f"Top(CS): {cs_top}", color='#ef4444', ha='center', va='bottom', fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        bot_x1, bot_x2 = x_min + 0.15, x_max - 0.15
        ax.plot([bot_x1, bot_x2], [y_bot_pos, y_bot_pos], color='#3b82f6', lw=2.5, zorder=3)
        ax.text((bot_x1+bot_x2)/2, y_bot_pos - 0.15, f"Bot(CS): {cs_bot}", color='#3b82f6', ha='center', va='top', fontweight='bold', fontsize=9)
        
        # เหล็ก MS
        has_ms_top = (y_max - cs_y_max) > 0.1
        has_ms_bot = (cs_y_min - y_min) > 0.1
        
        ms_y_list = []
        if has_ms_top: ms_y_list.append((cs_y_max + y_max)/2)
        if has_ms_bot: ms_y_list.append((y_min + cs_y_min)/2)
        
        for ms_y in ms_y_list:
            ax.plot([bot_x1, bot_x2], [ms_y, ms_y], color='#3b82f6', lw=2, zorder=3)
            ax.text((bot_x1+bot_x2)/2, ms_y - 0.15, f"Bot(MS): {ms_bot}", color='#3b82f6', ha='center', va='top', fontsize=9)
            
            # วาดเส้น Top MS เฉพาะเมื่อมีข้อมูล (ไม่เป็น N/A)
            if ms_top != "N/A":
                ax.plot([top_x1, top_x2], [ms_y + 0.3, ms_y + 0.3], color='#ef4444', lw=2, linestyle='--', zorder=3)
                ax.text((top_x1+top_x2)/2, ms_y + 0.45, f"Top(MS): {ms_top}", color='#ef4444', ha='center', va='bottom', fontsize=9)

        axis_title = "X-Axis Frame"

    # ----------------------------------------------------
    # 🌟 4. ระบบ Dimension แยกซ้าย-ขวาจากศูนย์กลางเสา
    # ----------------------------------------------------
    dim_y = y_max + 0.4
    if abs(x_min) > 0.01:
        ax.annotate('', xy=(x_min, dim_y), xytext=(0, dim_y), arrowprops=dict(arrowstyle='<|-|>', color='black'))
        ax.text(x_min/2, dim_y + 0.15, f"{abs(x_min):.2f} m", ha='center', fontweight='bold', fontsize=9)
    if abs(x_max) > 0.01:
        ax.annotate('', xy=(0, dim_y), xytext=(x_max, dim_y), arrowprops=dict(arrowstyle='<|-|>', color='black'))
        ax.text(x_max/2, dim_y + 0.15, f"{x_max:.2f} m", ha='center', fontweight='bold', fontsize=9)
        
    dim_x = x_max + 0.4
    if abs(y_min) > 0.01:
        ax.annotate('', xy=(dim_x, y_min), xytext=(dim_x, 0), arrowprops=dict(arrowstyle='<|-|>', color='black'))
        ax.text(dim_x + 0.15, y_min/2, f"{abs(y_min):.2f} m", va='center', rotation=270, fontweight='bold', fontsize=9)
    if abs(y_max) > 0.01:
        ax.annotate('', xy=(dim_x, 0), xytext=(dim_x, y_max), arrowprops=dict(arrowstyle='<|-|>', color='black'))
        ax.text(dim_x + 0.15, y_max/2, f"{y_max:.2f} m", va='center', rotation=270, fontweight='bold', fontsize=9)
    
    # ปรับแต่งมุมมองให้พอดี
    padding = 1.0
    ax.set_xlim(x_min - padding, x_max + padding)
    ax.set_ylim(y_min - padding, y_max + padding)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Plan View: {axis_title} ({col_loc} Column)", pad=30, fontweight='bold', fontsize=12)
    
    plt.tight_layout()
    return fig
    
# ==========================================
# 2. วาดรูป Cross Section (ตัดหน้าตัดตามแกนที่วิเคราะห์)
# ==========================================
def draw_slab_section_with_rebar(inputs, edited_df):
    L1 = inputs.get('L1', 5.0)
    L2 = inputs.get('L2', 5.0)
    c1 = inputs.get('c1', 0.5)
    c2 = inputs.get('c2', 0.5)
    h_slab = inputs.get('h_slab_cm', 20.0) / 100.0
    has_drop = inputs.get('has_drop', False)
    h_drop = inputs.get('h_drop', 20.0) / 100.0 if has_drop else h_slab
    
    analysis_dir = inputs.get('analysis_dir', 'X-Axis')
    is_y_axis = "Y-Axis" in analysis_dir or "L2" in analysis_dir
    
    col_loc = str(inputs.get('col_loc', inputs.get('column_location', 'Interior'))).strip().title()
    
    # Section จะต้องยาวเท่ากับแกนที่ถูกตัดวิเคราะห์
    if is_y_axis:
        span_len = L2
        col_w = c2
        span_label = "L2 (Y-Axis)"
    else:
        span_len = L1
        col_w = c1
        span_label = "L1 (X-Axis)"

    fig, ax = plt.subplots(figsize=(9, 3.5))
    
    ax.add_patch(patches.Rectangle((0, -1), col_w/2, 1, fill=True, color='#64748b'))
    ax.add_patch(patches.Rectangle((span_len - col_w/2, -1), col_w, 1, fill=True, color='#64748b'))
    ax.add_patch(patches.Rectangle((0, 0), span_len, h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155', lw=1.5))
    
    if has_drop and h_drop > h_slab:
        drop_w = span_len / 3.0 
        ax.add_patch(patches.Rectangle((0, -(h_drop - h_slab)), drop_w/2, h_drop - h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155'))
        ax.add_patch(patches.Rectangle((span_len - drop_w/2, -(h_drop - h_slab)), drop_w, h_drop - h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155'))
    
    # ส่ง col_loc เข้าไปช่วยกรองข้อความด้วย
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True, col_loc=col_loc)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False, col_loc=col_loc)
    cover = 0.03 
    
    ax.plot([0, span_len/3], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5)
    ax.plot([span_len/3, span_len/3], [h_slab - cover, h_slab - cover - 0.05], color='#ef4444', lw=2.5) 
    ax.plot([span_len - span_len/3, span_len], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5)
    ax.plot([span_len - span_len/3, span_len - span_len/3], [h_slab - cover, h_slab - cover - 0.05], color='#ef4444', lw=2.5) 
    
    ax.text(span_len/6, h_slab + 0.05, f"Top: {cs_top}", color='#ef4444', ha='center', fontweight='bold', fontsize=9)
    ax.text(span_len - span_len/6, h_slab + 0.05, f"Top: {cs_top}", color='#ef4444', ha='center', fontweight='bold', fontsize=9)
    
    ax.plot([span_len/5, 4*span_len/5], [cover, cover], color='#3b82f6', lw=2.5)
    ax.plot([span_len/5, span_len/5], [cover, cover + 0.05], color='#3b82f6', lw=2.5) 
    ax.plot([4*span_len/5, 4*span_len/5], [cover, cover + 0.05], color='#3b82f6', lw=2.5) 
    ax.text(span_len/2, cover - 0.15, f"Bot: {cs_bot}", color='#3b82f6', ha='center', fontweight='bold', fontsize=9)
    
    ax.annotate('', xy=(0, h_slab/2), xytext=(span_len, h_slab/2), arrowprops=dict(arrowstyle='<|-|>', color='black', lw=1))
    ax.text(span_len/2, h_slab/2 + 0.03, f"Section Cut Along {span_label} = {span_len:.2f} m", ha='center', color='black', fontweight='bold', fontsize=10, bbox=dict(facecolor='white', edgecolor='none', pad=0.5))
    
    ax.set_xlim(-0.5, span_len + 0.5)
    ax.set_ylim(-1.2, h_slab + 0.4)
    ax.axis('off')
    ax.set_title(f"Column Strip Elevation Section", pad=15, fontweight='bold')
    
    plt.tight_layout()
    return fig

# ==========================================
# 3. วาดรูป Punching Shear Perimeter (แกนคงที่)
# ==========================================
def draw_punching_plan(col_loc, c1_cm, c2_cm, d_cm):
    fig, ax = plt.subplots(figsize=(5, 5))
    
    c1 = c1_cm / 100.0 # แกน X
    c2 = c2_cm / 100.0 # แกน Y
    d = d_cm / 100.0
    
    if col_loc == "Interior":
        b1, b2 = c1 + d, c2 + d
        ax.add_patch(patches.Rectangle((-c1/2, -c2/2), c1, c2, fill=True, color='#475569'))
        ax.add_patch(patches.Rectangle((-b1/2, -b2/2), b1, b2, fill=False, edgecolor='#ef4444', lw=2, linestyle='--'))
        
        ax.text(0, 0, f'c1={c1*100:.0f}\nc2={c2*100:.0f}', color='white', ha='center', va='center', fontweight='bold', fontsize=8)
        
        ax.annotate('', xy=(-c1/2, c2/2+0.05), xytext=(-b1/2, c2/2+0.05), arrowprops=dict(arrowstyle='<|-|>', color='blue'))
        ax.text(-(c1/2 + d/4), c2/2+0.1, 'd/2', color='blue', ha='center', fontsize=9)
        
        ax.annotate('', xy=(-b1/2, -b2/2 - 0.1), xytext=(b1/2, -b2/2 - 0.1), arrowprops=dict(arrowstyle='<|-|>', color='black'))
        ax.text(0, -b2/2 - 0.25, f'b1 = {b1*100:.1f} cm', ha='center', fontsize=9)
        
        ax.annotate('', xy=(b1/2 + 0.1, -b2/2), xytext=(b1/2 + 0.1, b2/2), arrowprops=dict(arrowstyle='<|-|>', color='black'))
        ax.text(b1/2 + 0.2, 0, f'b2 = {b2*100:.1f}\ncm', va='center', fontsize=9)

        ax.set_xlim(-b1 - 0.3, b1 + 0.5)
        ax.set_ylim(-b2 - 0.4, b2 + 0.3)

    elif col_loc == "Edge":
        b1, b2 = c1 + d/2, c2 + d
        ax.add_patch(patches.Rectangle((-c1/2, 0), c1, c2, fill=True, color='#475569'))
        ax.plot([-b1/2, -b1/2, b1/2, b1/2], [0, b2, b2, 0], color='#ef4444', lw=2, linestyle='--')
        
        ax.axhline(0, color='black', lw=2)
        ax.fill_between([-b1-0.2, b1+0.2], -0.2, 0, color='#f1f5f9', hatch='//')
        ax.text(0, -0.1, 'Slab Edge', ha='center', fontweight='bold', color='#64748b')
        
        ax.set_xlim(-b1 - 0.3, b1 + 0.3)
        ax.set_ylim(-0.3, b2 + 0.3)
        
    elif col_loc == "Corner":
        b1, b2 = c1 + d/2, c2 + d/2
        ax.add_patch(patches.Rectangle((0, 0), c1, c2, fill=True, color='#475569'))
        ax.plot([b1, b1, 0], [0, b2, b2], color='#ef4444', lw=2, linestyle='--')
        
        ax.axvline(0, color='black', lw=2)
        ax.axhline(0, color='black', lw=2)
        ax.fill_between([-0.3, b1+0.3], -0.3, 0, color='#f1f5f9', hatch='//')
        ax.fill_between([-0.3, 0], 0, b2+0.3, color='#f1f5f9', hatch='//')
        
        ax.set_xlim(-0.3, b1 + 0.3)
        ax.set_ylim(-0.3, b2 + 0.3)
    
    ax.plot([], [], color='#ef4444', linestyle='--', lw=2, label='Critical Section (bo)')
    ax.legend(loc='upper right', fontsize=8)
    
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Punching Perimeter ({col_loc})", fontweight='bold')
    
    plt.tight_layout()
    return fig
