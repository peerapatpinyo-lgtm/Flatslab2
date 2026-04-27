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

# ==========================================
# 1. วาดรูป Plan View (แปลนพื้นแบบ Dynamic)
# ==========================================
def draw_rebar_plan_view(inputs, edited_df):
    L1 = inputs.get('L1', 5.0)
    L2 = inputs.get('L2', 5.0)
    c1 = inputs.get('c1', 0.5)
    c2 = inputs.get('c2', 0.5)
    
    # ตรวจสอบทิศทางการวิเคราะห์ (Analysis Direction)
    # สมมติว่าในหน้า UI คุณส่ง key 'analysis_dir' มา (เช่น "X-Axis Frame" หรือ "Y-Axis Frame")
    analysis_dir = inputs.get('analysis_dir', 'X-Axis')
    is_y_axis = "Y-Axis" in analysis_dir or "L2" in analysis_dir
    
    # สลับแกนตามทิศทางที่วิเคราะห์
    if is_y_axis:
        span_len, trans_len = L2, L1   # วิเคราะห์ตามแนวดิ่ง (หน้าจอแนวนอนคือ L2)
        col_w, col_h = c2, c1
        axis_title = "Y-Axis Frame (Analysis along L2)"
        span_label, trans_label = "L2", "L1"
    else:
        span_len, trans_len = L1, L2   # วิเคราะห์ตามแนวนอน
        col_w, col_h = c1, c2
        axis_title = "X-Axis Frame (Analysis along L1)"
        span_label, trans_label = "L1", "L2"
    
    fig, ax = plt.subplots(figsize=(9, 7))
    
    # วาดแผงพื้น (Slab Panel)
    ax.add_patch(patches.Rectangle((0, 0), span_len, trans_len, fill=True, facecolor='#f8fafc', edgecolor='#94a3b8', lw=2))
    
    # คำนวณความกว้าง Column Strip (ประมาณ L2/4 สองฝั่ง)
    cs_width = trans_len / 2.0
    ms_width = trans_len - cs_width
    cs_y0 = (trans_len - cs_width) / 2.0
    
    # วาดขอบเขต Column Strip / Middle Strip
    ax.add_patch(patches.Rectangle((0, cs_y0), span_len, cs_width, fill=True, facecolor='#e2e8f0', alpha=0.6, edgecolor='none'))
    ax.axhline(cs_y0, color='#94a3b8', linestyle='-.', lw=1)
    ax.axhline(trans_len - cs_y0, color='#94a3b8', linestyle='-.', lw=1)
    
    # Labels สำหรับ Strips
    ax.text(-0.3, trans_len/2, f'Column Strip\n(Width = {cs_width:.2f}m)', rotation=90, va='center', ha='center', color='#334155', fontweight='bold', fontsize=9)
    ax.text(-0.3, cs_y0/2, f'Middle Strip\n(Width = {ms_width/2:.2f}m)', rotation=90, va='center', ha='center', color='#64748b', fontsize=8)
    ax.text(-0.3, trans_len - cs_y0/2, f'Middle Strip\n(Width = {ms_width/2:.2f}m)', rotation=90, va='center', ha='center', color='#64748b', fontsize=8)
    
    # วาดเสา (กึ่งกลาง)
    ax.add_patch(patches.Rectangle(((span_len - col_w)/2, (trans_len - col_h)/2), col_w, col_h, fill=True, facecolor='#1e293b'))
    
    # --- ดึงข้อมูลเหล็กเสริม ---
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False)
    ms_top = get_rebar_text(edited_df, is_col_strip=False, is_negative=True)
    ms_bot = get_rebar_text(edited_df, is_col_strip=False, is_negative=False)
    
    # --- วาดสัญลักษณ์เหล็กเสริม (ทิศทางขนานกับ Span ที่วิเคราะห์) ---
    # 1. เหล็กบน (Top Bar) สีแดง ที่ Support (Column Strip)
    ax.plot([span_len/2 - span_len/4, span_len/2 + span_len/4], [trans_len/2 + col_h/2 + 0.2, trans_len/2 + col_h/2 + 0.2], color='#ef4444', lw=2.5, linestyle='--')
    ax.text(span_len/2, trans_len/2 + col_h/2 + 0.35, f"Top Bar (CS)\n{cs_top}", color='#ef4444', ha='center', fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
    
    # 2. เหล็กล่าง (Bottom Bar) สีน้ำเงิน ที่ Midspan (Column Strip)
    ax.plot([span_len/8, span_len/2 - col_w/2 - 0.2], [trans_len/2, trans_len/2], color='#3b82f6', lw=2.5)
    ax.text(span_len/4, trans_len/2 - 0.25, f"Bot Bar (CS)\n{cs_bot}", color='#3b82f6', ha='center', fontweight='bold', fontsize=9)
    
    # 3. เหล็ก Middle Strip
    # Bottom
    ax.plot([span_len/4, 3*span_len/4], [cs_y0/2, cs_y0/2], color='#3b82f6', lw=2)
    ax.text(span_len/2, cs_y0/2 - 0.25, f"Bot Bar (MS): {ms_bot}", color='#3b82f6', ha='center', fontsize=9)
    # Top
    ax.plot([0.1, span_len/3], [cs_y0/2 + 0.4, cs_y0/2 + 0.4], color='#ef4444', lw=2, linestyle='--')
    ax.text(span_len/6, cs_y0/2 + 0.55, f"Top Bar (MS): {ms_top}", color='#ef4444', ha='center', fontsize=9)
    
    # Dimension Lines
    ax.annotate('', xy=(0, -0.4), xytext=(span_len, -0.4), arrowprops=dict(arrowstyle='<|-|>', color='black'))
    ax.text(span_len/2, -0.65, f"Analysis Span ({span_label}) = {span_len:.2f} m", ha='center', fontweight='bold')
    
    ax.set_xlim(-0.8, span_len + 0.5)
    ax.set_ylim(-1.0, trans_len + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Plan View: {axis_title}", pad=20, fontweight='bold', fontsize=12)
    
    plt.tight_layout()
    return fig

# ==========================================
# 2. วาดรูป Cross Section (สลับ Span ตามแกน)
# ==========================================
def draw_slab_section_with_rebar(inputs, edited_df):
    L1 = inputs.get('L1', 5.0)
    L2 = inputs.get('L2', 5.0)
    c1 = inputs.get('c1', 0.5)
    c2 = inputs.get('c2', 0.5)
    h_slab = inputs.get('h_slab_cm', 20.0) / 100.0
    has_drop = inputs.get('has_drop', False)
    h_drop = inputs.get('h_drop', 20.0) / 100.0 if has_drop else h_slab
    
    # ตรวจสอบทิศทางการวิเคราะห์
    analysis_dir = inputs.get('analysis_dir', 'X-Axis')
    is_y_axis = "Y-Axis" in analysis_dir or "L2" in analysis_dir
    
    if is_y_axis:
        span_len = L2
        col_w = c2
        span_label = "L2"
    else:
        span_len = L1
        col_w = c1
        span_label = "L1"

    fig, ax = plt.subplots(figsize=(9, 3.5))
    
    # วาดเสา
    ax.add_patch(patches.Rectangle((0, -1), col_w/2, 1, fill=True, color='#64748b'))
    ax.add_patch(patches.Rectangle((span_len - col_w/2, -1), col_w, 1, fill=True, color='#64748b'))
    
    # วาดพื้น (Slab)
    ax.add_patch(patches.Rectangle((0, 0), span_len, h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155', lw=1.5))
    
    # วาด Drop Panel (ถ้ามี)
    if has_drop and h_drop > h_slab:
        drop_w = span_len / 3.0 # จำลองความกว้าง Drop Panel คร่าวๆ ตาม Span
        ax.add_patch(patches.Rectangle((0, -(h_drop - h_slab)), drop_w/2, h_drop - h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155'))
        ax.add_patch(patches.Rectangle((span_len - drop_w/2, -(h_drop - h_slab)), drop_w, h_drop - h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155'))
    
    # --- ดึงข้อมูลเหล็กเสริม (ดึง Column Strip เป็นหลัก) ---
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False)
    
    cover = 0.03 # m
    
    # วาดเส้นเหล็กบน (Top Bar) เหนือเสา (มีตะขอปลาย)
    ax.plot([0, span_len/3], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5)
    ax.plot([span_len/3, span_len/3], [h_slab - cover, h_slab - cover - 0.05], color='#ef4444', lw=2.5) # ตะขอ
    ax.plot([span_len - span_len/3, span_len], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5)
    ax.plot([span_len - span_len/3, span_len - span_len/3], [h_slab - cover, h_slab - cover - 0.05], color='#ef4444', lw=2.5) # ตะขอ
    
    ax.text(span_len/6, h_slab + 0.05, f"Top Bar: {cs_top}", color='#ef4444', ha='center', fontweight='bold', fontsize=9)
    ax.text(span_len - span_len/6, h_slab + 0.05, f"Top Bar: {cs_top}", color='#ef4444', ha='center', fontweight='bold', fontsize=9)
    
    # วาดเส้นเหล็กล่าง (Bottom Bar) กึ่งกลางช่วง
    ax.plot([span_len/5, 4*span_len/5], [cover, cover], color='#3b82f6', lw=2.5)
    ax.plot([span_len/5, span_len/5], [cover, cover + 0.05], color='#3b82f6', lw=2.5) # ตะขอ
    ax.plot([4*span_len/5, 4*span_len/5], [cover, cover + 0.05], color='#3b82f6', lw=2.5) # ตะขอ
    ax.text(span_len/2, cover - 0.15, f"Bottom Bar: {cs_bot}", color='#3b82f6', ha='center', fontweight='bold', fontsize=9)
    
    # Dimension Lines
    ax.annotate('', xy=(0, h_slab/2), xytext=(span_len, h_slab/2), arrowprops=dict(arrowstyle='<|-|>', color='black', lw=1))
    ax.text(span_len/2, h_slab/2 + 0.03, f"Analysis Span ({span_label}) = {span_len:.2f} m", ha='center', color='black', fontweight='bold', fontsize=10, bbox=dict(facecolor='white', edgecolor='none', pad=0.5))
    
    ax.set_xlim(-0.5, span_len + 0.5)
    ax.set_ylim(-1.2, h_slab + 0.4)
    ax.axis('off')
    ax.set_title(f"Column Strip Elevation Section (Along {span_label})", pad=15, fontweight='bold')
    
    plt.tight_layout()
    return fig

# ==========================================
# 3. วาดรูป Punching Shear Perimeter
# ==========================================
def draw_punching_plan(col_loc, c1_cm, c2_cm, d_cm):
    """
    Punching Shear วาดแบบ 2D (มอง Top View) 
    หน้าตัด c1 (แกน X), c2 (แกน Y) คงที่เสมอ
    """
    fig, ax = plt.subplots(figsize=(5, 5))
    
    c1 = c1_cm / 100.0
    c2 = c2_cm / 100.0
    d = d_cm / 100.0
    
    if col_loc == "Interior":
        cx, cy = 0, 0
        b1, b2 = c1 + d, c2 + d
        ax.add_patch(patches.Rectangle((-c1/2, -c2/2), c1, c2, fill=True, color='#475569'))
        ax.add_patch(patches.Rectangle((-b1/2, -b2/2), b1, b2, fill=False, edgecolor='#ef4444', lw=2, linestyle='--'))
        
        ax.text(0, 0, 'Column\n(c1 x c2)', color='white', ha='center', va='center', fontweight='bold', fontsize=8)
        
        # ใส่ Detail ระยะ d/2
        ax.annotate('', xy=(-c1/2, c2/2+0.05), xytext=(-b1/2, c2/2+0.05), arrowprops=dict(arrowstyle='<|-|>', color='blue'))
        ax.text(-(c1/2 + d/4), c2/2+0.1, 'd/2', color='blue', ha='center', fontsize=9)
        
        # ใส่ Dimension b1, b2
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
        ax.text(0, -0.1, 'Slab Edge / Void', ha='center', fontweight='bold', color='#64748b')
        
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
