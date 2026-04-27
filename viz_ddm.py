import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# 1. ฟังก์ชันดึงค่า (แก้บั๊กคำซ้อนทับกัน ดึงเป๊ะทุกบรรทัด)
# ==========================================
def get_rebar_exact(df, is_col_strip, mom_type):
    if df is None or df.empty or 'Location' not in df.columns:
        return "N/A"
        
    strip_kw = "Col" if is_col_strip else "Mid"
    
    try:
        # กรองเอาเฉพาะ Col หรือ Mid ก่อน
        df_strip = df[df['Location'].str.contains(strip_kw, case=False, na=False)]
        
        # ค้นหาคำแบบเจาะจงขั้นสุด ป้องกันบั๊ก "Neg" ไปชนกับ "Ext Neg"
        if mom_type == "Ext Neg":
            mask = df_strip['Location'].str.contains('Ext', case=False, na=False)
        elif mom_type == "Int Neg":
            mask = df_strip['Location'].str.contains('Int', case=False, na=False)
        elif mom_type == "Pos":
            mask = df_strip['Location'].str.contains('Pos', case=False, na=False)
        elif mom_type == "Neg":
            # ถ้าหา Neg เฉยๆ ต้องดักไม่ให้ไปดึงบรรทัด Ext หรือ Int มามั่วๆ
            mask = df_strip['Location'].str.contains('Neg', case=False, na=False) & \
                   ~df_strip['Location'].str.contains('Ext', case=False, na=False)
        else:
            mask = df_strip['Location'].str.contains(mom_type, case=False, na=False)
               
        match = df_strip[mask]
        if not match.empty:
            row = match.iloc[0]
            bar_size = int(row.get('Bar Size (mm)', 12))
            spacing = float(row.get('Spacing (cm)', 20.0))
            return f"DB{bar_size} @{spacing:.1f}"
        return "N/A"
    except:
        return "N/A"

# ==========================================
# 2. Plan View (ดักจับ Edge/Corner ให้ทำงานจริง พร้อมโชว์ Label ยืนยัน)
# ==========================================
def draw_rebar_plan_view(inputs, edited_df):
    L1 = float(inputs.get('l1', inputs.get('L1', 5.0))) 
    L2 = float(inputs.get('l2', inputs.get('L2', 5.0))) 
    c1 = float(inputs.get('c1', 0.5))
    c2 = float(inputs.get('c2', 0.5))
    
    col_loc_raw = ""
    for k, v in inputs.items():
        if 'loc' in k.lower() or 'column' in k.lower():
            col_loc_raw = str(v).strip().title()
            break
            
    is_corner = 'Corner' in col_loc_raw
    is_edge = 'Edge' in col_loc_raw
    is_edge_or_corner = is_corner or is_edge
    
    analysis_dir = str(inputs.get('analysis_dir', 'X')).lower()
    is_y_axis = 'y' in analysis_dir or 'l2' in analysis_dir
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 🌟 ลอจิกใหม่: ปรับขอบเขตพื้น (Slab Boundary) ตาม Case ที่เลือก 🌟
    col_x, col_y = -c1/2.0, -c2/2.0
    
    if is_corner:
        # เสามุม: ตัดพื้นซ้ายและล่างทิ้ง
        x_min, x_max = col_x, L1/2.0
        y_min, y_max = col_y, L2/2.0
    elif is_edge:
        # เสาริม: ตัดพื้นทิ้ง 1 ด้านตามแกน
        if is_y_axis:
            x_min, x_max = -L1/2.0, L1/2.0
            y_min, y_max = col_y, L2/2.0 # ขอบอยู่ด้านล่าง
        else:
            x_min, x_max = col_x, L1/2.0 # ขอบอยู่ด้านซ้าย
            y_min, y_max = -L2/2.0, L2/2.0
    else:
        # เสาใน: พื้นล้อมรอบ
        x_min, x_max = -L1/2.0, L1/2.0
        y_min, y_max = -L2/2.0, L2/2.0

    slab_w, slab_h = x_max - x_min, y_max - y_min
    
    # วาดพื้น (ใช้พิกัดที่ตัดแล้ว) และเสา
    ax.add_patch(patches.Rectangle((x_min, y_min), slab_w, slab_h, fill=True, facecolor='#f8fafc', edgecolor='#94a3b8', lw=2, zorder=1))
    ax.add_patch(patches.Rectangle((col_x, col_y), c1, c2, fill=True, facecolor='#1e293b', zorder=2))
    
    # ดึงค่าเหล็กเสริม
    if is_edge_or_corner:
        cs_top = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Ext Neg")
        ms_top = get_rebar_exact(edited_df, is_col_strip=False, mom_type="Ext Neg")
        label_cs_top, label_ms_top = "Top(CS, Ext)", "Top(MS, Ext)"
    else:
        cs_top = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Int Neg")
        if cs_top == "N/A": cs_top = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Neg")
        ms_top = get_rebar_exact(edited_df, is_col_strip=False, mom_type="Int Neg")
        if ms_top == "N/A": ms_top = get_rebar_exact(edited_df, is_col_strip=False, mom_type="Neg")
        label_cs_top, label_ms_top = "Top(CS, Int)", "Top(MS, Int)"
        
    cs_bot = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Pos")
    ms_bot = get_rebar_exact(edited_df, is_col_strip=False, mom_type="Pos")

    # วาดแนวเหล็กให้อยู่ในขอบเขตพื้นใหม่เสมอ
    if is_y_axis:
        cs_x_min, cs_x_max = max(-L1/4.0, x_min), min(L1/4.0, x_max)
        cs_w = cs_x_max - cs_x_min
        ax.add_patch(patches.Rectangle((cs_x_min, y_min), cs_w, slab_h, fill=True, facecolor='#e2e8f0', alpha=0.6, zorder=1.5))
        
        x_top_pos = cs_x_min + cs_w * 0.75
        x_bot_pos = cs_x_min + cs_w * 0.25
        
        top_y1, top_y2 = max(-L2/4, y_min), min(L2/4, y_max)
        ax.plot([x_top_pos, x_top_pos], [top_y1, top_y2], color='#ef4444', lw=2.5, linestyle='--', zorder=3)
        ax.text(x_top_pos + 0.1, (top_y1+top_y2)/2, f"{label_cs_top}\n{cs_top}", color='#ef4444', va='center', ha='left', fontweight='bold', fontsize=9)
        
        bot_y1, bot_y2 = y_min + 0.15, y_max - 0.15
        if bot_y2 > bot_y1:
            ax.plot([x_bot_pos, x_bot_pos], [bot_y1, bot_y2], color='#3b82f6', lw=2.5, zorder=3)
            ax.text(x_bot_pos - 0.1, (bot_y1+bot_y2)/2, f"Bot(CS)\n{cs_bot}", color='#3b82f6', va='center', ha='right', fontweight='bold', fontsize=9)
        
        for ms_x in [(cs_x_max + x_max)/2, (x_min + cs_x_min)/2]:
            if ms_x > x_max - 0.1 or ms_x < x_min + 0.1: continue
            ax.plot([ms_x, ms_x], [bot_y1, bot_y2], color='#3b82f6', lw=2, zorder=3)
            ax.text(ms_x - 0.1, (bot_y1+bot_y2)/2, f"Bot(MS): {ms_bot}", color='#3b82f6', va='center', ha='right', rotation=90, fontsize=9)
            if ms_top != "N/A":
                ax.plot([ms_x - 0.3, ms_x - 0.3], [top_y1, top_y2], color='#ef4444', lw=2, linestyle='--', zorder=3)
        axis_title = "Y-Axis Frame"
    else:
        cs_y_min, cs_y_max = max(-L2/4.0, y_min), min(L2/4.0, y_max)
        cs_w = cs_y_max - cs_y_min
        ax.add_patch(patches.Rectangle((x_min, cs_y_min), slab_w, cs_w, fill=True, facecolor='#e2e8f0', alpha=0.6, zorder=1.5))
        
        y_top_pos = cs_y_min + cs_w * 0.75
        y_bot_pos = cs_y_min + cs_w * 0.25
        
        top_x1, top_x2 = max(-L1/4, x_min), min(L1/4, x_max)
        ax.plot([top_x1, top_x2], [y_top_pos, y_top_pos], color='#ef4444', lw=2.5, linestyle='--', zorder=3)
        ax.text((top_x1+top_x2)/2, y_top_pos + 0.1, f"{label_cs_top}: {cs_top}", color='#ef4444', ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        bot_x1, bot_x2 = x_min + 0.15, x_max - 0.15
        if bot_x2 > bot_x1:
            ax.plot([bot_x1, bot_x2], [y_bot_pos, y_bot_pos], color='#3b82f6', lw=2.5, zorder=3)
            ax.text((bot_x1+bot_x2)/2, y_bot_pos - 0.1, f"Bot(CS): {cs_bot}", color='#3b82f6', ha='center', va='top', fontweight='bold', fontsize=9)
        
        for ms_y in [(cs_y_max + y_max)/2, (y_min + cs_y_min)/2]:
            if ms_y > y_max - 0.1 or ms_y < y_min + 0.1: continue
            ax.plot([bot_x1, bot_x2], [ms_y, ms_y], color='#3b82f6', lw=2, zorder=3)
            ax.text((bot_x1+bot_x2)/2, ms_y - 0.1, f"Bot(MS): {ms_bot}", color='#3b82f6', ha='center', va='top', fontsize=9)
            if ms_top != "N/A":
                ax.plot([top_x1, top_x2], [ms_y + 0.3, ms_y + 0.3], color='#ef4444', lw=2, linestyle='--', zorder=3)
        axis_title = "X-Axis Frame"

    # ทำให้กรอบขยายครอบคลุมพอดี ไม่วาดส่วนที่แหว่งไป
    ax.set_xlim(x_min - 0.5, x_max + 0.5)
    ax.set_ylim(y_min - 0.5, y_max + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    case_name = col_loc_raw if col_loc_raw else "Interior"
    ax.set_title(f"Plan View: {axis_title} ({case_name} Column)", pad=20, fontweight='bold', fontsize=12)
    plt.tight_layout()
    return fig
    
# ==========================================
# 3. Section View (สลับ Case ซ้าย/ขวา ให้เห็นแบบจะๆ)
# ==========================================
def draw_slab_section_with_rebar(inputs, edited_df):
    L1, L2 = inputs.get('L1', 5.0), inputs.get('L2', 5.0)
    c1, c2 = inputs.get('c1', 0.5), inputs.get('c2', 0.5)
    h_slab = inputs.get('h_slab_cm', 20.0) / 100.0
    
    col_loc_raw = ""
    for k, v in inputs.items():
        if 'loc' in k.lower() or 'column' in k.lower():
            col_loc_raw = str(v).strip().title()
            break
            
    is_edge_or_corner = ('Edge' in col_loc_raw) or ('Corner' in col_loc_raw)
    
    analysis_dir = inputs.get('analysis_dir', 'X-Axis')
    is_y_axis = "Y-Axis" in analysis_dir or "L2" in analysis_dir
    span_len = L2 if is_y_axis else L1
    col_w = c2 if is_y_axis else c1

    fig, ax = plt.subplots(figsize=(9, 3.5))
    
    # เสาซ้าย (x=0) และ เสาขวา (x=span_len)
    ax.add_patch(patches.Rectangle((-col_w/2, -1), col_w, 1, fill=True, color='#64748b'))
    ax.add_patch(patches.Rectangle((span_len - col_w/2, -1), col_w, 1, fill=True, color='#64748b'))
    
    # 🌟 ลอจิก Section พื้น: ถ้าเป็น Edge/Corner พื้นซ้ายสุดจะหยุดที่หน้าเสา 🌟
    slab_start = -col_w/2 if is_edge_or_corner else -span_len/4
    slab_end = span_len + span_len/4
    ax.add_patch(patches.Rectangle((slab_start, 0), slab_end - slab_start, h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155', lw=1.5))
    
    if is_edge_or_corner:
        cs_top_left = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Ext Neg")
        cs_top_right = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Int Neg")
        label_left, label_right = "Top(Ext)", "Top(Int)"
    else:
        cs_top_left = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Int Neg")
        if cs_top_left == "N/A": cs_top_left = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Neg")
        cs_top_right = cs_top_left
        label_left, label_right = "Top(Int)", "Top(Int)"
        
    cs_bot = get_rebar_exact(edited_df, is_col_strip=True, mom_type="Pos")
    cover = 0.03 
    
    # 🌟 ลอจิกวาดเหล็กบนซ้าย (ใส่ Hook ดักไว้ถ้าเป็นขอบ) 🌟
    left_rebar_start = slab_start + 0.04 if is_edge_or_corner else slab_start
    ax.plot([left_rebar_start, span_len/3], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5)
    ax.plot([span_len/3, span_len/3], [h_slab - cover, h_slab - cover - 0.05], color='#ef4444', lw=2.5) 
    if is_edge_or_corner:
        # วาดเหล็กงอฉากลงมาในเสาให้ดูสมจริงว่าเป็นเสาริม
        ax.plot([left_rebar_start, left_rebar_start], [h_slab - cover, h_slab - cover - 0.1], color='#ef4444', lw=2.5)

    # เหล็กบนขวา
    ax.plot([span_len - span_len/3, slab_end], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5)
    ax.plot([span_len - span_len/3, span_len - span_len/3], [h_slab - cover, h_slab - cover - 0.05], color='#ef4444', lw=2.5) 
    
    ax.text(span_len/6, h_slab + 0.05, f"{label_left}: {cs_top_left}", color='#ef4444', ha='center', fontweight='bold', fontsize=9)
    ax.text(span_len - span_len/6, h_slab + 0.05, f"{label_right}: {cs_top_right}", color='#ef4444', ha='center', fontweight='bold', fontsize=9)
    
    # เหล็กล่าง
    ax.plot([span_len/5, 4*span_len/5], [cover, cover], color='#3b82f6', lw=2.5)
    ax.plot([span_len/5, span_len/5], [cover, cover + 0.05], color='#3b82f6', lw=2.5) 
    ax.plot([4*span_len/5, 4*span_len/5], [cover, cover + 0.05], color='#3b82f6', lw=2.5) 
    ax.text(span_len/2, cover - 0.15, f"Bot: {cs_bot}", color='#3b82f6', ha='center', fontweight='bold', fontsize=9)
    
    ax.set_xlim(slab_start - 0.2, slab_end + 0.2)
    ax.set_ylim(-0.5, h_slab + 0.3)
    ax.axis('off')
    
    case_name = col_loc_raw if col_loc_raw else "Interior"
    ax.set_title(f"Column Strip Section ({case_name})", pad=15, fontweight='bold')
    
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
