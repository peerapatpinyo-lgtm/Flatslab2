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
    # สมมติเราดึงข้อมูลจาก Column Strip Interior Negative และ Middle Strip Interior Positive มาโชว์
    try:
        # เหล็กบน (Negative Moment) - Column Strip
        col_neg_row = edited_df[edited_df['Location'].str.contains("Col", case=False) & edited_df['Location'].str.contains("Neg", case=False)].iloc[0]
        rebar_top = f"DB{col_neg_row['Bar Size (mm)']} @ {col_neg_row['Spacing (cm)']:.1f} cm"
        # เหล็กล่าง (Positive Moment) - Middle Strip
        mid_pos_row = edited_df[edited_df['Location'].str.contains("Mid", case=False) & edited_df['Location'].str.contains("Pos", case=False)].iloc[0]
        rebar_bot = f"DB{mid_pos_row['Bar Size (mm)']} @ {mid_pos_row['Spacing (cm)']:.1f} cm"
    except (IndexError, KeyError):
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

# ส่วน draw_punching_plan คงเดิม
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
