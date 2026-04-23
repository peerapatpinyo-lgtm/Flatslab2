# viz_ddm.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

def draw_slab_section_with_rebar(inputs, edited_df):
    """วาดรูปหน้าตัดพื้น (Cross Section) แบบ Scaled แสดงเหล็กเสริมที่ออกแบบจริง"""
    # 1. ดึงข้อมูล Geometry จาก inputs (MKS units)
    L1 = inputs.get('l1', 5.0)
    L2 = inputs.get('l2', 5.0)
    h_slab_m = inputs.get('h_slab', 20) / 100.0
    has_drop = inputs.get('has_drop', False)
    h_drop_m = inputs.get('h_drop', 25) / 100.0 if has_drop else h_slab_m
    drop_w_m = inputs.get('eb_width', inputs.get('l1', 5.0) / 3.0) # แปลงค่า Drop Width ให้เหมาะสม
    c1_m = inputs.get('c1', 0.50)
    cc_m = inputs.get('cc_cm', 3.0) / 100.0
    
    # 2. แปลงค่าเป็น cm เพื่อการวาดที่ง่ายขึ้น
    h_s, h_d, c1, cc = h_slab_m*100, h_drop_m*100, c1_m*100, cc_m*100
    w_d = drop_w_m * 100
    
    # 3. เตรียมข้อมูลเหล็กเสริมจาก edited_df (ดึงค่าเฉลี่ยหรือค่าที่วิกฤตที่สุด)
    try:
        # เหล็กบน (Negative Moment) - Column Strip
        col_neg_row = edited_df[edited_df['Location'].str.contains("Col", case=False) & edited_df['Location'].str.contains("Neg", case=False)].iloc[0]
        rebar_top = f"DB{int(col_neg_row['Bar Size (mm)'])} @ {col_neg_row['Spacing (cm)']:.1f} cm"
        # เหล็กล่าง (Positive Moment) - Middle Strip
        mid_pos_row = edited_df[edited_df['Location'].str.contains("Mid", case=False) & edited_df['Location'].str.contains("Pos", case=False)].iloc[0]
        rebar_bot = f"DB{int(mid_pos_row['Bar Size (mm)'])} @ {mid_pos_row['Spacing (cm)']:.1f} cm"
    except:
        rebar_top = "Designed Rebar"
        rebar_bot = "Designed Rebar"

    fig, ax = plt.subplots(figsize=(12, 5))
    
    # วาดพื้นและหัวเสา
    w_slab = max(w_d * 1.5, c1 * 4)
    # Slab
    ax.add_patch(patches.Rectangle((-w_slab/2, 0), w_slab, h_s, color='#e0e0e0', label='Slab'))
    # Drop Panel
    if has_drop:
        ax.add_patch(patches.Rectangle((-w_d/2, - (h_d - h_s)), w_d, h_d - h_s, color='#c0c0c0', label='Drop Panel'))
    # Column
    ax.add_patch(patches.Rectangle((-c1/2, -100), c1, 100, color='#909090', label='Column'))

    # วาดเหล็กเสริม
    # เหล็กบน (Top Rebar) - สีแดง
    ax.plot([-w_slab/2 + 10, w_slab/2 - 10], [h_s - cc, h_s - cc], color='red', linewidth=2.5, label=f'Top Negative: {rebar_top}')
    # เหล็กล่าง (Bottom Rebar) - สีน้ำเงิน
    ax.plot([-w_slab/2 + 10, w_slab/2 - 10], [cc, cc], color='blue', linewidth=1.5, linestyle='--', label=f'Bottom Positive: {rebar_bot}')

    # ตกแต่ง
    limit_w = w_slab/2 + 20
    limit_h_bot = - (h_d - h_s) - 20
    limit_h_top = h_s + 20
    ax.set_xlim(-limit_w, limit_w)
    ax.set_ylim(limit_h_bot, limit_h_top)
    ax.set_aspect('equal')
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize='small')
    ax.axis('off')
    ax.set_title(f"SCALED DETAILED SECTION: L1={L1:.1f}m, L2={L2:.1f}m", fontsize=13, fontweight='bold')
    
    return fig

def draw_punching_plan(col_loc, c1, c2, d):
    """วาดรูปแปลนหน้าตัดวิกฤต (Punching Shear Critical Section)"""
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # วาดเสา
    ax.add_patch(patches.Rectangle((-c1/2, -c2/2), c1, c2, color='#808080', label='Column'))
    
    # วาดหน้าตัดวิกฤต (bo) ตามตำแหน่งเสา
    if col_loc == "Interior":
        bo_w, bo_h = c1 + d, c2 + d
        rect = patches.Rectangle((-bo_w/2, -bo_h/2), bo_w, bo_h, linewidth=2, edgecolor='red', facecolor='none', linestyle='--', label='Critical Section ($b_o$)')
    elif col_loc == "Edge":
        bo_w, bo_h = c1 + d/2, c2 + d
        rect = patches.Rectangle((-c1/2, -bo_h/2), bo_w, bo_h, linewidth=2, edgecolor='red', facecolor='none', linestyle='--', label='Critical Section ($b_o$)')
    else: # Corner
        bo_w, bo_h = c1 + d/2, c2 + d/2
        rect = patches.Rectangle((-c1/2, -c2/2), bo_w, bo_h, linewidth=2, edgecolor='red', facecolor='none', linestyle='--', label='Critical Section ($b_o$)')

    ax.add_patch(rect)
    
    # ตกแต่ง
    limit = max(c1, c2) * 1.5
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_aspect('equal')
    ax.legend(loc='upper right', fontsize='small')
    ax.set_title(f"Punching Shear Perimeter: {col_loc} Column")
    
    return fig


def draw_rebar_plan_view(inputs, edited_df):
    """วาดรูปแปลน (Top View) แสดงเหล็กเสริมทั้งแกน X (L1) และแกน Y (L2)"""
    L1 = inputs.get('l1', 5.0) * 100 
    L2 = inputs.get('l2', 5.0) * 100
    c1 = inputs.get('c1', 0.5) * 100
    c2 = inputs.get('c2', 0.5) * 100
    
    cs_width_x = min(L1, L2) / 2.0
    cs_width_y = min(L1, L2) / 2.0
    
    # ดึงข้อมูลเหล็ก (ในอนาคตถ้าตาราง edited_df แยกแกน X, Y ให้มาแก้ Filter ตรงนี้ให้ดึงแยกแกนได้ครับ)
    # ตอนนี้จะดึงค่าจากตารางมาโชว์เป็นตัวแทนไปก่อน
    def get_rebar_text(loc_keyword):
        try:
            row = edited_df[edited_df['Location'].str.contains(loc_keyword, case=False, na=False)].iloc[0]
            return f"DB{int(row['Bar Size (mm)'])}@{row['Spacing (cm)']:.1f}"
        except:
            return "N/A"
            
    cs_top = get_rebar_text("Col.*Neg")
    cs_bot = get_rebar_text("Col.*Pos")
    ms_top = get_rebar_text("Mid.*Neg")
    ms_bot = get_rebar_text("Mid.*Pos")

    fig, ax = plt.subplots(figsize=(10, 10))
    
    # 1. วาดขอบเขตพื้น
    ax.add_patch(patches.Rectangle((-L1/2, -L2/2), L1, L2, facecolor='#f8f9fa', edgecolor='black', linewidth=2))
    
    # 2. แรเงา Column Strip จุดตัดตรงกลาง
    ax.add_patch(patches.Rectangle((-cs_width_x/2, -cs_width_y/2), cs_width_x, cs_width_y, facecolor='#dee2e6', alpha=0.8))
    
    # เส้นประแบ่ง Strip
    ax.axhline(cs_width_y/2, color='gray', linestyle='-.', linewidth=1)
    ax.axhline(-cs_width_y/2, color='gray', linestyle='-.', linewidth=1)
    ax.axvline(cs_width_x/2, color='gray', linestyle='-.', linewidth=1)
    ax.axvline(-cs_width_x/2, color='gray', linestyle='-.', linewidth=1)

    # 3. วาดเสาตรงกลาง
    ax.add_patch(patches.Rectangle((-c1/2, -c2/2), c1, c2, color='#495057', zorder=5))

    # ==========================================
    # 🔴 4. วาดเหล็ก แกน X (แนวนอน - ขนาน L1)
    # ==========================================
    top_len_x = L1 * 0.33
    bot_len_x = L1/2 - 20
    
    # แกน X: เหล็กบน CS (พาดผ่านเสา)
    ax.plot([-top_len_x, top_len_x], [c2/2 + 15, c2/2 + 15], color='red', linewidth=2.5, zorder=6)
    ax.text(0, c2/2 + 20, f"X-Top CS: {cs_top}", color='darkred', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # แกน X: เหล็กล่าง CS (ตลอดช่วง)
    ax.plot([-bot_len_x, bot_len_x], [-c2/2 - 15, -c2/2 - 15], color='blue', linewidth=1.5, linestyle='--', zorder=6)
    ax.text(0, -c2/2 - 20, f"X-Bot CS: {cs_bot}", color='darkblue', ha='center', va='top', fontsize=9, fontweight='bold')

    # แกน X: เหล็กบน MS (ขอบบน-ล่าง)
    ax.plot([-top_len_x, top_len_x], [L2/2 - 30, L2/2 - 30], color='red', linewidth=2.5, zorder=6)
    ax.text(0, L2/2 - 35, f"X-Top MS: {ms_top}", color='darkred', ha='center', va='top', fontsize=9)
    
    # แกน X: เหล็กล่าง MS
    ax.plot([-bot_len_x, bot_len_x], [-L2/2 + 30, -L2/2 + 30], color='blue', linewidth=1.5, linestyle='--', zorder=6)
    ax.text(0, -L2/2 + 35, f"X-Bot MS: {ms_bot}", color='darkblue', ha='center', va='bottom', fontsize=9)

    # ==========================================
    # 🟢 5. วาดเหล็ก แกน Y (แนวตั้ง - ขนาน L2)
    # ==========================================
    top_len_y = L2 * 0.33
    bot_len_y = L2/2 - 20
    
    # แกน Y: เหล็กบน CS (พาดผ่านเสา)
    ax.plot([-c1/2 - 15, -c1/2 - 15], [-top_len_y, top_len_y], color='#d9534f', linewidth=2.5, zorder=6)
    ax.text(-c1/2 - 20, 0, f"Y-Top CS: {cs_top}", color='#d9534f', ha='right', va='center', rotation=90, fontsize=9, fontweight='bold')
    
    # แกน Y: เหล็กล่าง CS (ตลอดช่วง)
    ax.plot([c1/2 + 15, c1/2 + 15], [-bot_len_y, bot_len_y], color='#5bc0de', linewidth=1.5, linestyle='--', zorder=6)
    ax.text(c1/2 + 20, 0, f"Y-Bot CS: {cs_bot}", color='#31708f', ha='left', va='center', rotation=90, fontsize=9, fontweight='bold')

    # แกน Y: เหล็กบน MS (ขอบซ้าย-ขวา)
    ax.plot([-L1/2 + 30, -L1/2 + 30], [-top_len_y, top_len_y], color='#d9534f', linewidth=2.5, zorder=6)
    ax.text(-L1/2 + 35, 0, f"Y-Top MS: {ms_top}", color='#d9534f', ha='left', va='center', rotation=90, fontsize=9)
    
    # แกน Y: เหล็กล่าง MS
    ax.plot([L1/2 - 30, L1/2 - 30], [-bot_len_y, bot_len_y], color='#5bc0de', linewidth=1.5, linestyle='--', zorder=6)
    ax.text(L1/2 - 35, 0, f"Y-Bot MS: {ms_bot}", color='#31708f', ha='right', va='center', rotation=90, fontsize=9)

    # ตกแต่งกราฟ
    ax.set_xlim(-L1/2 - 60, L1/2 + 60)
    ax.set_ylim(-L2/2 - 60, L2/2 + 60)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("2-WAY REBAR PLAN: X-Axis (L1) & Y-Axis (L2)", fontsize=13, fontweight='bold')
    
    return fig
