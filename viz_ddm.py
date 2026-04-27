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
# 1. วาดรูป Plan View (แปลนพื้นแบบ Fixed Axis)
# ==========================================
def draw_rebar_plan_view(inputs, edited_df):
    # 💡 1. ปรับการรับค่าให้รองรับทั้งพิมพ์เล็ก/ใหญ่ (เผื่อส่ง l1 มาแทน L1)
    L1 = float(inputs.get('l1', inputs.get('L1', 5.0))) 
    L2 = float(inputs.get('l2', inputs.get('L2', 5.0))) 
    c1 = float(inputs.get('c1', 0.5))
    c2 = float(inputs.get('c2', 0.5))
    
    # 🚨 2. จุดแก้ปัญหาหลัก: ทำให้การเช็กแกน ไม่สนตัวพิมพ์เล็ก/ใหญ่
    analysis_dir = str(inputs.get('analysis_dir', 'X')).lower()
    is_y_axis = 'y' in analysis_dir or 'l2' in analysis_dir
    
    fig, ax = plt.subplots(figsize=(9, 7))
    # ... (ส่วนที่เหลือวาดรูปเหมือนเดิม ปล่อยไว้ได้เลยครับ) ...
    # วาดพื้น (L1 แนวนอน, L2 แนวตั้งเสมอ)
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, fill=True, facecolor='#f8fafc', edgecolor='#94a3b8', lw=2))
    
    # ... (ส่วนการดึง rebar_text และ if is_y_axis อื่นๆ ของคุณเขียนไว้ดีแล้วครับ) ...
    # ดึงข้อมูลเหล็ก
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False)
    ms_top = get_rebar_text(edited_df, is_col_strip=False, is_negative=True)
    ms_bot = get_rebar_text(edited_df, is_col_strip=False, is_negative=False)

    if is_y_axis:
        # ----------------------------------------------------
        # วิเคราะห์ตามแนวแกน Y (L2) -> Strip พาดแนวตั้ง
        # ----------------------------------------------------
        cs_width = L1 / 2.0 # กว้าง L1/2
        cs_x0 = (L1 - cs_width) / 2.0
        
        # วาดขอบเขต Column Strip แนวตั้ง
        ax.add_patch(patches.Rectangle((cs_x0, 0), cs_width, L2, fill=True, facecolor='#e2e8f0', alpha=0.6, edgecolor='none'))
        ax.axvline(cs_x0, color='#94a3b8', linestyle='-.', lw=1)
        ax.axvline(L1 - cs_x0, color='#94a3b8', linestyle='-.', lw=1)
        
        ax.text(L1/2, -0.3, f'Column Strip\n(Width = {cs_width:.2f}m)', va='top', ha='center', color='#334155', fontweight='bold', fontsize=9)
        ax.text(cs_x0/2, -0.3, f'Middle Strip', va='top', ha='center', color='#64748b', fontsize=8)
        
        # เหล็กบน CS (แนวตั้ง)
        ax.plot([L1/2 + c1/2 + 0.2, L1/2 + c1/2 + 0.2], [L2/2 - L2/4, L2/2 + L2/4], color='#ef4444', lw=2.5, linestyle='--')
        ax.text(L1/2 + c1/2 + 0.35, L2/2, f"Top Bar(CS)\n{cs_top}", color='#ef4444', va='center', ha='left', fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        # เหล็กล่าง CS (แนวตั้ง)
        ax.plot([L1/2 - c1/2 - 0.2, L1/2 - c1/2 - 0.2], [L2/8, L2/2 - c2/2 - 0.2], color='#3b82f6', lw=2.5)
        ax.text(L1/2 - c1/2 - 0.35, L2/4, f"Bot Bar(CS)\n{cs_bot}", color='#3b82f6', va='center', ha='right', fontweight='bold', fontsize=9)
        
        # เหล็กล่าง MS (แนวตั้ง)
        ax.plot([cs_x0/2, cs_x0/2], [L2/4, 3*L2/4], color='#3b82f6', lw=2)
        ax.text(cs_x0/2 - 0.1, L2/2, f"Bot(MS): {ms_bot}", color='#3b82f6', va='center', ha='right', rotation=90, fontsize=9)
        
        # เหล็กบน MS (แนวตั้ง)
        ax.plot([cs_x0/2 - 0.3, cs_x0/2 - 0.3], [0.1, L2/3], color='#ef4444', lw=2, linestyle='--')
        ax.text(cs_x0/2 - 0.4, L2/6, f"Top(MS): {ms_top}", color='#ef4444', va='center', ha='right', rotation=90, fontsize=9)

        axis_title = "Y-Axis Frame (Analysis along L2)"
        
    else:
        # ----------------------------------------------------
        # วิเคราะห์ตามแนวแกน X (L1) -> Strip พาดแนวนอน
        # ----------------------------------------------------
        cs_width = L2 / 2.0 # กว้าง L2/2
        cs_y0 = (L2 - cs_width) / 2.0
        
        # วาดขอบเขต Column Strip แนวนอน
        ax.add_patch(patches.Rectangle((0, cs_y0), L1, cs_width, fill=True, facecolor='#e2e8f0', alpha=0.6, edgecolor='none'))
        ax.axhline(cs_y0, color='#94a3b8', linestyle='-.', lw=1)
        ax.axhline(L2 - cs_y0, color='#94a3b8', linestyle='-.', lw=1)
        
        ax.text(-0.3, L2/2, f'Column Strip\n(Width = {cs_width:.2f}m)', rotation=90, va='center', ha='right', color='#334155', fontweight='bold', fontsize=9)
        ax.text(-0.3, cs_y0/2, f'Middle Strip', rotation=90, va='center', ha='right', color='#64748b', fontsize=8)
        
        # เหล็กบน CS (แนวนอน)
        ax.plot([L1/2 - L1/4, L1/2 + L1/4], [L2/2 + c2/2 + 0.2, L2/2 + c2/2 + 0.2], color='#ef4444', lw=2.5, linestyle='--')
        ax.text(L1/2, L2/2 + c2/2 + 0.35, f"Top Bar (CS): {cs_top}", color='#ef4444', ha='center', fontweight='bold', fontsize=9, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
        
        # เหล็กล่าง CS (แนวนอน)
        ax.plot([L1/8, L1/2 - c1/2 - 0.2], [L2/2 - c2/2 - 0.2, L2/2 - c2/2 - 0.2], color='#3b82f6', lw=2.5)
        ax.text(L1/4, L2/2 - c2/2 - 0.45, f"Bot Bar (CS): {cs_bot}", color='#3b82f6', ha='center', fontweight='bold', fontsize=9)
        
        # เหล็กล่าง MS (แนวนอน)
        ax.plot([L1/4, 3*L1/4], [cs_y0/2, cs_y0/2], color='#3b82f6', lw=2)
        ax.text(L1/2, cs_y0/2 - 0.25, f"Bot(MS): {ms_bot}", color='#3b82f6', ha='center', fontsize=9)
        
        # เหล็กบน MS (แนวนอน)
        ax.plot([0.1, L1/3], [cs_y0/2 + 0.4, cs_y0/2 + 0.4], color='#ef4444', lw=2, linestyle='--')
        ax.text(L1/6, cs_y0/2 + 0.55, f"Top(MS): {ms_top}", color='#ef4444', ha='center', fontsize=9)

        axis_title = "X-Axis Frame (Analysis along L1)"

    # วาดเสาตรงกลาง (อยู่ตำแหน่งเดิมเสมอ ไม่หมุน)
    ax.add_patch(patches.Rectangle(((L1 - c1)/2, (L2 - c2)/2), c1, c2, fill=True, facecolor='#1e293b'))
    
    # Dimension Lines ของพื้น
    ax.annotate('', xy=(0, L2+0.4), xytext=(L1, L2+0.4), arrowprops=dict(arrowstyle='<|-|>', color='black'))
    ax.text(L1/2, L2+0.55, f"L1 = {L1:.2f} m", ha='center', fontweight='bold')
    
    ax.annotate('', xy=(L1+0.4, 0), xytext=(L1+0.4, L2), arrowprops=dict(arrowstyle='<|-|>', color='black'))
    ax.text(L1+0.55, L2/2, f"L2 = {L2:.2f} m", va='center', rotation=270, fontweight='bold')
    
    ax.set_xlim(-1.0, L1 + 1.0)
    ax.set_ylim(-1.0, L2 + 1.0)
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
