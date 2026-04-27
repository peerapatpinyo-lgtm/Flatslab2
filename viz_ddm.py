import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# Helper Function สำหรับดึงข้อความเหล็กเสริม
# ==========================================
def get_rebar_text(df, is_col_strip, is_negative):
    """
    ดึงขนาดและระยะแอดของเหล็กจาก edited_df 
    """
    if df is None or df.empty or 'Location' not in df.columns:
        return "N/A"
        
    strip_kw = "Col" if is_col_strip else "Mid"
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
# 1. วาดรูป Plan View (รองรับ Edge และ Corner)
# ==========================================
def draw_rebar_plan_view(inputs, edited_df):
    L1 = float(inputs.get('l1', inputs.get('L1', 5.0))) 
    L2 = float(inputs.get('l2', inputs.get('L2', 5.0))) 
    c1 = float(inputs.get('c1', 0.5))
    c2 = float(inputs.get('c2', 0.5))
    
    # ดึงระยะ Span ย่อย เพื่อเช็กว่าเป็น Edge / Corner หรือไม่
    geom = inputs.get('geom', inputs)
    L1_l = float(geom.get('L1_l', L1/2))
    L1_r = float(geom.get('L1_r', L1/2))
    L2_t = float(geom.get('L2_t', L2/2))
    L2_b = float(geom.get('L2_b', L2/2))
    
    # เช็กว่ามีแผ่นพื้นฝั่งไหนบ้าง (> 0)
    has_left = L1_l > 0.01
    has_right = L1_r > 0.01
    has_top = L2_t > 0.01
    has_bot = L2_b > 0.01

    analysis_dir = str(inputs.get('analysis_dir', 'X')).lower()
    is_y_axis = 'y' in analysis_dir or 'l2' in analysis_dir
    
    fig, ax = plt.subplots(figsize=(9, 7))
    
    # 🌟 1. คำนวณขอบเขตแผ่นพื้นที่แท้จริง (ถ้าไม่มีฝั่งไหน ให้ตัดขอบฝั่งนั้นทิ้ง)
    slab_x_start = 0 if has_left else L1/2
    slab_x_end = L1 if has_right else L1/2
    slab_y_start = 0 if has_bot else L2/2
    slab_y_end = L2 if has_top else L2/2
    
    slab_width = slab_x_end - slab_x_start
    slab_height = slab_y_end - slab_y_start

    # วาดพื้นตามขอบเขตจริง
    ax.add_patch(patches.Rectangle((slab_x_start, slab_y_start), slab_width, slab_height, fill=True, facecolor='#f8fafc', edgecolor='#94a3b8', lw=2))
    
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False)
    ms_top = get_rebar_text(edited_df, is_col_strip=False, is_negative=True)
    ms_bot = get_rebar_text(edited_df, is_col_strip=False, is_negative=False)

    if is_y_axis:
        # ----------------------------------------------------
        # Y-Axis Frame
        # ----------------------------------------------------
        cs_width = L1 / 2.0 
        cs_x0 = (L1 - cs_width) / 2.0
        
        # ตัดขอบ Column Strip ไม่ให้ลอยทะลุขอบพื้น
        cs_x_start = max(cs_x0, slab_x_start)
        cs_x_end = min(cs_x0 + cs_width, slab_x_end)
        
        if cs_x_end > cs_x_start:
            ax.add_patch(patches.Rectangle((cs_x_start, slab_y_start), cs_x_end - cs_x_start, slab_height, fill=True, facecolor='#e2e8f0', alpha=0.6, edgecolor='none'))
        
        if has_left: ax.axvline(cs_x0, color='#94a3b8', linestyle='-.', lw=1)
        if has_right: ax.axvline(L1 - cs_x0, color='#94a3b8', linestyle='-.', lw=1)
        
        ax.text(L1/2, slab_y_start - 0.3, f'Column Strip\n(Width = {cs_width:.2f}m)', va='top', ha='center', color='#334155', fontweight='bold', fontsize=9)
        
        # 🌟 2. ขยับเหล็ก Top/Bot CS ให้ไปอยู่ฝั่งที่มีแผ่นพื้น
        tx = L1/2 + c1/2 + 0.2 if has_right else L1/2 - c1/2 - 0.2
        tha = 'left' if has_right else 'right'
        ax.plot([tx, tx], [L2/2 - L2/4, L2/2 + L2/4], color='#ef4444', lw=2.5, linestyle='--')
        ax.text(tx + (0.15 if has_right else -0.15), L2/2, f"Top Bar(CS)\n{cs_top}", color='#ef4444', va='center', ha=tha, fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        bx = L1/2 - c1/2 - 0.2 if has_left else L1/2 + c1/2 + 0.2
        bha = 'right' if has_left else 'left'
        by_start = L2/8 if has_bot else L2/2 + c2/2 + 0.2
        by_end = L2/2 - c2/2 - 0.2 if has_bot else L2 - L2/8
        ax.plot([bx, bx], [by_start, by_end], color='#3b82f6', lw=2.5)
        ax.text(bx + (-0.15 if has_left else 0.15), (by_start+by_end)/2, f"Bot Bar(CS)\n{cs_bot}", color='#3b82f6', va='center', ha=bha, fontweight='bold', fontsize=9)
        
        # ขยับ Middle Strip ไปฝั่งที่ถูกต้อง
        ms_x = cs_x0/2 if has_left else L1 - cs_x0/2
        if has_left or has_right:
            ax.text(ms_x, slab_y_start - 0.3, f'Middle Strip', va='top', ha='center', color='#64748b', fontsize=8)
            ax.plot([ms_x, ms_x], [L2/4, 3*L2/4], color='#3b82f6', lw=2)
            ax.text(ms_x - 0.1, L2/2, f"Bot(MS): {ms_bot}", color='#3b82f6', va='center', ha='right', rotation=90, fontsize=9)
            ax.plot([ms_x - 0.3, ms_x - 0.3], [slab_y_start + 0.1, slab_y_start + L2/3], color='#ef4444', lw=2, linestyle='--')
            ax.text(ms_x - 0.4, slab_y_start + L2/6, f"Top(MS): {ms_top}", color='#ef4444', va='center', ha='right', rotation=90, fontsize=9)

        axis_title = "Y-Axis Frame (Analysis along L2)"
        
    else:
        # ----------------------------------------------------
        # X-Axis Frame
        # ----------------------------------------------------
        cs_width = L2 / 2.0 
        cs_y0 = (L2 - cs_width) / 2.0
        
        cs_y_start = max(cs_y0, slab_y_start)
        cs_y_end = min(cs_y0 + cs_width, slab_y_end)
        
        if cs_y_end > cs_y_start:
            ax.add_patch(patches.Rectangle((slab_x_start, cs_y_start), slab_width, cs_y_end - cs_y_start, fill=True, facecolor='#e2e8f0', alpha=0.6, edgecolor='none'))
        
        if has_bot: ax.axhline(cs_y0, color='#94a3b8', linestyle='-.', lw=1)
        if has_top: ax.axhline(L2 - cs_y0, color='#94a3b8', linestyle='-.', lw=1)
        
        ax.text(slab_x_start - 0.3, L2/2, f'Column Strip\n(Width = {cs_width:.2f}m)', rotation=90, va='center', ha='right', color='#334155', fontweight='bold', fontsize=9)
        
        ty = L2/2 + c2/2 + 0.2 if has_top else L2/2 - c2/2 - 0.2
        ty_va = 'bottom' if has_top else 'top'
        ax.plot([L1/2 - L1/4, L1/2 + L1/4], [ty, ty], color='#ef4444', lw=2.5, linestyle='--')
        ax.text(L1/2, ty + (0.15 if has_top else -0.25), f"Top Bar (CS): {cs_top}", color='#ef4444', ha='center', va=ty_va, fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        by = L2/2 - c2/2 - 0.2 if has_bot else L2/2 + c2/2 + 0.2
        by_va = 'top' if has_bot else 'bottom'
        bx_start = L1/8 if has_left else L1/2 + c1/2 + 0.2
        bx_end = L1/2 - c1/2 - 0.2 if has_left else L1 - L1/8
        ax.plot([bx_start, bx_end], [by, by], color='#3b82f6', lw=2.5)
        ax.text((bx_start+bx_end)/2, by + (-0.15 if has_bot else 0.15), f"Bot Bar (CS): {cs_bot}", color='#3b82f6', ha='center', va=by_va, fontweight='bold', fontsize=9)
        
        ms_y = cs_y0/2 if has_bot else L2 - cs_y0/2
        if has_bot or has_top:
            ax.text(slab_x_start - 0.3, ms_y, f'Middle Strip', rotation=90, va='center', ha='right', color='#64748b', fontsize=8)
            ax.plot([L1/4, 3*L1/4], [ms_y, ms_y], color='#3b82f6', lw=2)
            ax.text(L1/2, ms_y - 0.25, f"Bot(MS): {ms_bot}", color='#3b82f6', ha='center', fontsize=9)
            ax.plot([slab_x_start + 0.1, slab_x_start + L1/3], [ms_y + 0.4, ms_y + 0.4], color='#ef4444', lw=2, linestyle='--')
            ax.text(slab_x_start + L1/6, ms_y + 0.55, f"Top(MS): {ms_top}", color='#ef4444', ha='center', fontsize=9)

        axis_title = "X-Axis Frame (Analysis along L1)"

    # วาดเสาตรงกลาง (พิกัดอยู่ที่เดิมเสมอ แต่ตัวแผ่นพื้นด้านบนจะหดตัวล้อมกรอบเสาเอาไว้)
    ax.add_patch(patches.Rectangle(((L1 - c1)/2, (L2 - c2)/2), c1, c2, fill=True, facecolor='#1e293b'))
    
    # 🌟 3. ขยับเส้นบอกระยะ Dimension Lines
    ax.annotate('', xy=(slab_x_start, slab_y_end+0.4), xytext=(slab_x_end, slab_y_end+0.4), arrowprops=dict(arrowstyle='<|-|>', color='black'))
    ax.text((slab_x_start+slab_x_end)/2, slab_y_end+0.55, f"L1 = {slab_width:.2f} m", ha='center', fontweight='bold')
    
    ax.annotate('', xy=(slab_x_end+0.4, slab_y_start), xytext=(slab_x_end+0.4, slab_y_end), arrowprops=dict(arrowstyle='<|-|>', color='black'))
    ax.text(slab_x_end+0.55, (slab_y_start+slab_y_end)/2, f"L2 = {slab_height:.2f} m", va='center', rotation=270, fontweight='bold')
    
    # ซูมขอบเขตให้กระชับแผ่นพื้น
    ax.set_xlim(-1.0 + slab_x_start, slab_x_end + 1.0)
    ax.set_ylim(-1.0 + slab_y_start, slab_y_end + 1.0)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Plan View: {axis_title}", pad=20, fontweight='bold', fontsize=12)
    
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
    
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False)
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
