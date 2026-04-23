# viz_ddm.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_slab_section(geom_data, rebar_data):
    """วาดรูปหน้าตัดพื้น (Cross Section) แสดง Rebar และ Drop Panel"""
    h_slab = geom_data.get('h_slab_cm', 20)
    has_drop = geom_data.get('has_drop', False)
    h_drop = geom_data.get('h_drop_cm', h_slab + 5) if has_drop else h_slab
    drop_w = geom_data.get('drop_w1', 2.0) * 100 # แปลงเป็น cm
    c1 = geom_data.get('c1_cm', 50)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # 1. วาดพื้น (Slab)
    slab_width = max(drop_w * 1.5, c1 * 4)
    ax.add_patch(patches.Rectangle((-slab_width/2, 0), slab_width, h_slab, color='#d3d3d3', label='Slab'))
    
    # 2. วาด Drop Panel (ถ้ามี)
    if has_drop:
        ax.add_patch(patches.Rectangle((-drop_w/2, - (h_drop - h_slab)), drop_w, h_drop - h_slab, color='#b0b0b0', label='Drop Panel'))
    
    # 3. วาดหัวเสา (Column)
    ax.add_patch(patches.Rectangle((-c1/2, -100), c1, 100, color='#808080', label='Column'))

    # 4. วาดเหล็กเสริม (Rebar Line) - วาดเป็นเส้นประสีแดง
    cover = 3.0
    ax.plot([-slab_width/2 + 5, slab_width/2 - 5], [h_slab - cover, h_slab - cover], color='red', linewidth=2, label='Top Reinforcement')
    ax.plot([-slab_width/2 + 5, slab_width/2 - 5], [cover, cover], color='blue', linewidth=1.5, linestyle='--', label='Bottom Reinforcement')

    # ตั้งค่ากราฟ
    ax.set_xlim(-slab_width/2 - 20, slab_width/2 + 20)
    ax.set_ylim(- (h_drop - h_slab) - 20, h_slab + 20)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Slab-Column Connection Section", fontsize=12, fontweight='bold')
    
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
