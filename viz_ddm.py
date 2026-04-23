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
    """วาดรูปแปลน (Top View) แสดง Column Strip, Middle Strip และแนวการจัดเหล็ก"""
    # 1. ดึงข้อมูล Geometry
    L1 = inputs.get('l1', 5.0) * 100 # แปลงเป็น cm
    L2 = inputs.get('l2', 5.0) * 100
    c1 = inputs.get('c1', 0.5) * 100
    c2 = inputs.get('c2', 0.5) * 100
    
    # 2. คำนวณความกว้าง Strip
    cs_width = min(L1, L2) / 2.0
    
    # 3. ดึงข้อมูลเหล็กจากการออกแบบแบบปลอดภัย (ดักจับ Error)
    def get_rebar_text(loc_keyword):
        try:
            row = edited_df[edited_df['Location'].str.contains(loc_keyword, case=False, na=False)].iloc[0]
            return f"DB{int(row['Bar Size (mm)'])} @ {row['Spacing (cm)']:.1f}"
        except:
            return "N/A"
            
    cs_top = get_rebar_text("Col.*Neg")
    cs_bot = get_rebar_text("Col.*Pos")
    ms_top = get_rebar_text("Mid.*Neg")
    ms_bot = get_rebar_text("Mid.*Pos")

    fig, ax = plt.subplots(figsize=(9, 8))
    
    # วาดขอบเขตพื้น (พิจารณา 1 ช่วงเสา โดยให้เสาอยู่ตรงกลาง)
    ax.add_patch(patches.Rectangle((-L1/2, -L2/2), L1, L2, facecolor='#f8f9fa', edgecolor='black', linewidth=1.5))
    
    # วาดแถบ Column Strip (แกน Y และ X)
    ax.add_patch(patches.Rectangle((-cs_width/2, -L2/2), cs_width, L2, facecolor='#e9ecef', alpha=0.5))
    ax.add_patch(patches.Rectangle((-L1/2, -cs_width/2), L1, cs_width, facecolor='#e9ecef', alpha=0.5))
    
    # เส้นประแบ่ง Strip
    ax.axhline(cs_width/2, color='gray', linestyle='-.', linewidth=1)
    ax.axhline(-cs_width/2, color='gray', linestyle='-.', linewidth=1)
    ax.axvline(cs_width/2, color='gray', linestyle='-.', linewidth=1)
    ax.axvline(-cs_width/2, color='gray', linestyle='-.', linewidth=1)

    # วาดเสาตรงกลาง
    ax.add_patch(patches.Rectangle((-c1/2, -c2/2), c1, c2, color='#495057', zorder=3))

    # ==========================================
    # วาดสัญลักษณ์เหล็กเสริม (Schematic Rebars)
    # ==========================================
    # 1. เหล็กบน (Top Bar - สีแดง) มักจะพาดผ่านหัวเสาระยะ L/3 หรือ 0.3Ln
    top_len = L1 * 0.33
    # Column Strip Top Bar
    ax.plot([-top_len, top_len], [c2/2 + 20, c2/2 + 20], color='red', linewidth=2.5, zorder=4)
    ax.text(0, c2/2 + 25, f"Top CS:\n{cs_top}", color='darkred', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Middle Strip Top Bar (อยู่ขอบๆ ของ Middle Strip)
    ax.plot([-top_len, top_len], [L2/2 - 30, L2/2 - 30], color='red', linewidth=2.5, zorder=4)
    ax.text(0, L2/2 - 35, f"Top MS:\n{ms_top}", color='darkred', ha='center', va='top', fontsize=9, fontweight='bold')

    # 2. เหล็กล่าง (Bottom Bar - สีน้ำเงิน) ลากยาวตลอดช่วง
    bot_len = L1/2 - 20
    # Column Strip Bottom Bar
    ax.plot([-bot_len, bot_len], [-c2/2 - 20, -c2/2 - 20], color='blue', linewidth=1.5, linestyle='--', zorder=4)
    ax.text(0, -c2/2 - 25, f"Bot CS:\n{cs_bot}", color='darkblue', ha='center', va='top', fontsize=9, fontweight='bold')
    
    # Middle Strip Bottom Bar
    ax.plot([-bot_len, bot_len], [-L2/2 + 30, -L2/2 + 30], color='blue', linewidth=1.5, linestyle='--', zorder=4)
    ax.text(0, -L2/2 + 35, f"Bot MS:\n{ms_bot}", color='darkblue', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # ใส่ Text บอก Zone
    ax.text(-L1/2 + 20, 0, "Middle\nStrip", rotation=90, va='center', ha='left', color='gray', fontsize=10)
    ax.text(L1/2 - 20, 0, "Middle\nStrip", rotation=270, va='center', ha='right', color='gray', fontsize=10)
    ax.text(0, -cs_width/2 + 10, "Column Strip Width", color='black', ha='center', va='bottom', fontsize=10, alpha=0.7)

    # ตกแต่งกราฟ
    ax.set_xlim(-L1/2 - 40, L1/2 + 40)
    ax.set_ylim(-L2/2 - 40, L2/2 + 40)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("REBAR PLAN VIEW: Column Strip & Middle Strip Zones", fontsize=12, fontweight='bold')
    
    return fig
