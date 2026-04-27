import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# Helper Function สำหรับดึงข้อความเหล็กเสริม
# ==========================================
def get_rebar_text(df, is_col_strip, is_negative):
    """
    ฟังก์ชันช่วยดึงขนาดและระยะแอดของเหล็กจาก edited_df 
    ตามประเภทแถบ (Column/Middle) และตำแหน่งโมเมนต์ (Negative/Positive)
    """
    if df is None or df.empty or 'Location' not in df.columns:
        return "N/A"
        
    # คัดกรองว่าเป็น Column Strip หรือ Middle Strip
    strip_kw = "Col" if is_col_strip else "Mid"
    # คัดกรองว่าเป็น Negative (เหล็กบน) หรือ Positive (เหล็กล่าง)
    mom_kw = "Neg" if is_negative else "Pos"
    
    try:
        # หา row ที่ตรงกับเงื่อนไข
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
# 1. วาดรูป Plan View (แปลนพื้น)
# ==========================================
def draw_rebar_plan_view(inputs, edited_df):
    L1 = inputs.get('L1', 5.0)
    L2 = inputs.get('L2', 5.0)
    c1 = inputs.get('c1', 0.5)
    c2 = inputs.get('c2', 0.5)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # วาดแผงพื้น (Slab Panel)
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, fill=True, facecolor='#f8fafc', edgecolor='#94a3b8', lw=2))
    
    # คำนวณความกว้าง Column Strip (ประมาณ L2/4 สองฝั่ง = L2/2)
    cs_width = L2 / 2.0
    ms_width = L2 - cs_width
    
    # วาดแรเงาแยก Column Strip และ Middle Strip (แนวนอนตามแกนวิเคราะห์ L1)
    # Column Strip จะอยู่ขอบบนขอบล่าง (สมมติแบ่งครึ่งโชว์)
    cs_y0 = (L2 - cs_width) / 2.0
    ax.add_patch(patches.Rectangle((0, cs_y0), L1, cs_width, fill=True, facecolor='#e2e8f0', alpha=0.5, edgecolor='none'))
    ax.text(-0.2, L2/2, 'Column Strip', rotation=90, va='center', ha='center', color='#475569', fontweight='bold')
    ax.text(-0.2, cs_y0/2, 'Middle Strip', rotation=90, va='center', ha='center', color='#475569', fontweight='bold')
    ax.text(-0.2, L2 - cs_y0/2, 'Middle Strip', rotation=90, va='center', ha='center', color='#475569', fontweight='bold')
    
    # วาดเสา (ตรงกลาง สมมติเป็น Interior)
    ax.add_patch(patches.Rectangle(((L1-c1)/2, (L2-c2)/2), c1, c2, fill=True, facecolor='#334155'))
    
    # --- ดึงข้อมูลเหล็กเสริม ---
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False)
    ms_top = get_rebar_text(edited_df, is_col_strip=False, is_negative=True)
    ms_bot = get_rebar_text(edited_df, is_col_strip=False, is_negative=False)
    
    # --- วาดสัญลักษณ์เหล็กเสริมลงบนแปลน ---
    # 1. เหล็กบน (Top Bar) สีแดง (ที่หัวเสา/Support)
    ax.plot([L1/2 - 1, L1/2 + 1], [L2/2 + c2, L2/2 + c2], color='#ef4444', lw=2, linestyle='--')
    ax.text(L1/2, L2/2 + c2 + 0.1, f"Top: {cs_top}", color='#ef4444', ha='center', fontweight='bold')
    
    # 2. เหล็กล่าง (Bottom Bar) สีน้ำเงิน (ที่กึ่งกลางช่วง/Midspan)
    ax.plot([L1/4, 3*L1/4], [L2/2, L2/2], color='#3b82f6', lw=2)
    ax.text(L1/2, L2/2 - 0.2, f"Bot: {cs_bot}", color='#3b82f6', ha='center', fontweight='bold')
    
    # เหล็ก Middle Strip
    ax.plot([L1/4, 3*L1/4], [cs_y0/2, cs_y0/2], color='#3b82f6', lw=2)
    ax.text(L1/2, cs_y0/2 - 0.2, f"Bot: {ms_bot}", color='#3b82f6', ha='center', fontweight='bold')
    
    ax.plot([0.1, L1/4], [cs_y0/2, cs_y0/2], color='#ef4444', lw=2, linestyle='--')
    ax.text(L1/8, cs_y0/2 + 0.1, f"Top: {ms_top}", color='#ef4444', ha='center', fontweight='bold')
    
    ax.set_xlim(-0.5, L1 + 0.5)
    ax.set_ylim(-0.5, L2 + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Reinforcement Plan View (Analysis Direction: L1)", pad=20, fontweight='bold')
    
    plt.tight_layout()
    return fig

# ==========================================
# 2. วาดรูป Cross Section (หน้าตัดพื้น)
# ==========================================
def draw_slab_section_with_rebar(inputs, edited_df):
    L1 = inputs.get('L1', 5.0)
    c1 = inputs.get('c1', 0.5)
    h_slab = inputs.get('h_slab_cm', 20.0) / 100.0
    has_drop = inputs.get('has_drop', False)
    h_drop = inputs.get('h_drop', 20.0) / 100.0 if has_drop else h_slab
    
    fig, ax = plt.subplots(figsize=(8, 3))
    
    # วาดเสา
    ax.add_patch(patches.Rectangle((0, -1), c1/2, 1, fill=True, color='#64748b'))
    ax.add_patch(patches.Rectangle((L1 - c1/2, -1), c1, 1, fill=True, color='#64748b'))
    
    # วาดพื้น (Slab)
    ax.add_patch(patches.Rectangle((0, 0), L1, h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155', lw=1.5))
    
    # วาด Drop Panel (ถ้ามี)
    if has_drop and h_drop > h_slab:
        drop_w = L1 / 3.0 # กะขนาด Drop Panel คร่าวๆ สำหรับแสดงผล
        ax.add_patch(patches.Rectangle((0, -(h_drop - h_slab)), drop_w/2, h_drop - h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155'))
        ax.add_patch(patches.Rectangle((L1 - drop_w/2, -(h_drop - h_slab)), drop_w, h_drop - h_slab, fill=True, facecolor='#cbd5e1', edgecolor='#334155'))
    
    # --- ดึงข้อมูลเหล็กเสริม (ดึง Column Strip เป็นหลัก) ---
    cs_top = get_rebar_text(edited_df, is_col_strip=True, is_negative=True)
    cs_bot = get_rebar_text(edited_df, is_col_strip=True, is_negative=False)
    
    cover = 0.03 # m
    
    # วาดเส้นเหล็กบน (Top Bar) เหนือเสา
    ax.plot([0, L1/3], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5)
    ax.plot([L1 - L1/3, L1], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5)
    ax.text(L1/6, h_slab + 0.05, f"Top Bar (CS): {cs_top}", color='#ef4444', ha='center', fontweight='bold', fontsize=9)
    ax.text(L1 - L1/6, h_slab + 0.05, f"Top Bar (CS): {cs_top}", color='#ef4444', ha='center', fontweight='bold', fontsize=9)
    
    # วาดเส้นเหล็กล่าง (Bottom Bar) กึ่งกลางช่วง
    ax.plot([L1/4, 3*L1/4], [cover, cover], color='#3b82f6', lw=2.5)
    ax.text(L1/2, cover - 0.15, f"Bottom Bar (CS): {cs_bot}", color='#3b82f6', ha='center', fontweight='bold', fontsize=9)
    
    # แกนอ้างอิง
    ax.annotate('', xy=(0, h_slab/2), xytext=(L1, h_slab/2), arrowprops=dict(arrowstyle='<->', color='gray', lw=1))
    ax.text(L1/2, h_slab/2 + 0.05, f"Span L1 = {L1:.2f} m", ha='center', color='gray', fontsize=9)
    
    ax.set_xlim(-0.5, L1 + 0.5)
    ax.set_ylim(-1.2, h_slab + 0.5)
    ax.axis('off')
    ax.set_title("Column Strip Elevation (Cross-Section)", pad=10, fontweight='bold')
    
    plt.tight_layout()
    return fig

# ==========================================
# 3. วาดรูป Punching Shear Perimeter
# ==========================================
def draw_punching_plan(col_loc, c1_cm, c2_cm, d_cm):
    fig, ax = plt.subplots(figsize=(5, 5))
    
    c1 = c1_cm / 100.0
    c2 = c2_cm / 100.0
    d = d_cm / 100.0
    
    # กำหนดตำแหน่งเสาและระยะวิกฤตตามประเภทของเสา
    if col_loc == "Interior":
        cx, cy = 0, 0
        b1, b2 = c1 + d, c2 + d
        ax.add_patch(patches.Rectangle((-c1/2, -c2/2), c1, c2, fill=True, color='#475569'))
        ax.add_patch(patches.Rectangle((-b1/2, -b2/2), b1, b2, fill=False, edgecolor='#ef4444', lw=2, linestyle='--'))
        
        # Labels
        ax.text(0, 0, 'Col', color='white', ha='center', va='center', fontweight='bold')
        ax.annotate('', xy=(-c1/2, c2/2+0.05), xytext=(-b1/2, c2/2+0.05), arrowprops=dict(arrowstyle='<->', color='blue'))
        ax.text(-(c1/2 + d/4), c2/2+0.1, 'd/2', color='blue', ha='center', fontsize=9)
        
        ax.set_xlim(-b1, b1)
        ax.set_ylim(-b2, b2)

    elif col_loc == "Edge":
        # เสาอยู่ขอบล่าง (y=0)
        b1, b2 = c1 + d/2, c2 + d
        ax.add_patch(patches.Rectangle((-c1/2, 0), c1, c2, fill=True, color='#475569'))
        # เส้น Perimeter รูปตัว U
        ax.plot([-b1/2, -b1/2, b1/2, b1/2], [0, b2, b2, 0], color='#ef4444', lw=2, linestyle='--')
        
        # พื้นที่ขอบพื้น
        ax.axhline(0, color='black', lw=2)
        ax.text(0, -0.1, 'Slab Edge', ha='center', fontweight='bold')
        
        ax.set_xlim(-b1, b1)
        ax.set_ylim(-0.2, b2 + 0.2)
        
    elif col_loc == "Corner":
        # เสาอยู่มุมซ้ายล่าง (0,0)
        b1, b2 = c1 + d/2, c2 + d/2
        ax.add_patch(patches.Rectangle((0, 0), c1, c2, fill=True, color='#475569'))
        # เส้น Perimeter รูปตัว L
        ax.plot([b1, b1, 0], [0, b2, b2], color='#ef4444', lw=2, linestyle='--')
        
        # พื้นที่ขอบพื้น
        ax.axvline(0, color='black', lw=2)
        ax.axhline(0, color='black', lw=2)
        ax.text(c1/2, -0.1, 'Edge', ha='center', fontweight='bold')
        ax.text(-0.1, c2/2, 'Edge', va='center', rotation=90, fontweight='bold')
        
        ax.set_xlim(-0.2, b1 + 0.2)
        ax.set_ylim(-0.2, b2 + 0.2)
    
    # Title & Legend
    ax.plot([], [], color='#ef4444', linestyle='--', lw=2, label='Critical Perimeter (bo)')
    ax.legend(loc='upper right', fontsize=8)
    
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Punching Shear Perimeter ({col_loc})", fontweight='bold')
    
    plt.tight_layout()
    return fig
