import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_rebar_plan_view(*args, **kwargs):
    """
    Generates a Reinforcement Plan View.
    Bulletproof version: Searches through all arguments for direction and DataFrame.
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import numpy as np
    import pandas as pd

    fig, ax = plt.subplots(figsize=(8, 6))
    
    # --- 1. ค่าเริ่มต้น (Fallback) ---
    L1, L2, c1, c2 = 8.0, 6.0, 0.4, 0.4
    analysis_dir = 'x-axis'
    df_design = None

    # --- 2. ระบบค้นหาตัวแปรอัจฉริยะแบบกวาดหมด (Scan All Arguments) ---
    all_args = list(args) + list(kwargs.values())
    
    for arg in all_args:
        if isinstance(arg, dict):
            # ถ้ามี Dictionary ส่งมา ให้ดึงค่าขนาดพื้น
            L1 = arg.get('L1', L1)
            L2 = arg.get('L2', L2)
            c1 = arg.get('c1', c1)
            c2 = arg.get('c2', c2)
            if 'analysis_dir' in arg:
                analysis_dir = str(arg['analysis_dir']).lower()
                
        elif isinstance(arg, pd.DataFrame):
            # ถ้าพบว่ามีการส่ง DataFrame เข้ามา ให้เก็บไว้ดึงค่าเหล็ก
            df_design = arg
            
        elif isinstance(arg, str):
            # ถ้ามีข้อความส่งมาลอยๆ ให้เช็คว่าเป็นตัวบอกทิศทาง X/Y หรือไม่
            arg_lower = arg.lower()
            if 'x' in arg_lower or 'y' in arg_lower or 'l1' in arg_lower or 'l2' in arg_lower:
                analysis_dir = arg_lower

    # --- 3. ดึงข้อมูลปริมาณเหล็กจากตาราง (df_design) ---
    top_bar_text = "Top Rebar (Support)"
    bot_bar_text = "Bottom Rebar (Midspan)"
    
    if df_design is not None and not df_design.empty:
        try:
            df_str = df_design.astype(str)
            
            # เล็งคอลัมน์สุดท้ายไว้ก่อน (มักจะเป็นคอลัมน์สรุปผลเหล็กเสริม)
            target_col = df_design.columns[-1] 
            
            # หรือค้นหาชื่อคอลัมน์ที่น่าจะใช่
            for col in df_design.columns:
                col_name_lower = str(col).lower()
                if any(kw in col_name_lower for kw in ['rebar', 'เหล็ก', 'เสริม', 'prov', 'as']):
                    target_col = col
                    break
            
            # ดึงข้อมูลจากคอลัมน์นั้น (ตัดค่าว่าง หรือขีดทิ้ง)
            rebar_list = [val for val in df_str[target_col].tolist() if val.strip() and val.lower() != 'nan' and val.strip() != '-']
            
            if len(rebar_list) >= 2:
                top_bar_text = f"Top: {rebar_list[0]}"  # แถวบนๆ มักเป็นเหล็ก Support
                bot_bar_text = f"Bot: {rebar_list[-1]}" # แถวท้ายๆ มักเป็นเหล็ก Midspan
            elif len(rebar_list) == 1:
                top_bar_text = f"Rebar: {rebar_list[0]}"
                bot_bar_text = f"Rebar: {rebar_list[0]}"
        except Exception:
            # ถ้าดึงพลาด จะแสดงข้อความนี้เพื่อให้รู้ว่ามีตารางส่งมา แต่โครงสร้างอ่านไม่ได้
            top_bar_text = "Top (Format Error)"
            bot_bar_text = "Bot (Format Error)"

    # --- 4. วาดเส้นขอบพื้นและเสา ---
    ax.add_patch(patches.Rectangle((0, 0), L1, L2, fill=False, edgecolor='black', linewidth=2.5, zorder=3))
    col_coords = [(0,0), (L1,0), (0,L2), (L1,L2)]
    for (cx, cy) in col_coords:
        col = patches.Rectangle((cx - c1/2, cy - c2/2), c1, c2, fill=True, color='dimgray', zorder=4)
        ax.add_patch(col)
        
    # --- 5. เช็คทิศทางและวาดเหล็ก ---
    is_x_dir = 'x' in analysis_dir or 'l1' in analysis_dir or 'long' in analysis_dir
    
    if is_x_dir:
        # ➡️ วาดเหล็กแนวนอน (X-Axis)
        ax.set_title(f"Reinforcement Plan View - X-Axis Frame\n[ {top_bar_text} / {bot_bar_text} ]", fontsize=12, fontweight='bold', pad=15)
        
        ax.hlines(y=[L2*0.85, L2*0.90, L2*0.95], xmin=0, xmax=L1*0.3, color='#ef4444', lw=1.5, label='Top Rebar (Support)')
        ax.hlines(y=[L2*0.85, L2*0.90, L2*0.95], xmin=L1*0.7, xmax=L1, color='#ef4444', lw=1.5)
        ax.text(L1*0.15, L2*0.97, top_bar_text, color='#ef4444', ha='center', fontweight='bold', fontsize=9)
        ax.text(L1*0.85, L2*0.97, top_bar_text, color='#ef4444', ha='center', fontweight='bold', fontsize=9)
        
        y_bottoms = np.linspace(L2*0.25, L2*0.75, 7)
        ax.hlines(y=y_bottoms, xmin=0.05*L1, xmax=0.95*L1, color='#3b82f6', lw=1.2, linestyle='--', label='Bottom Rebar (Midspan)')
        ax.text(L1*0.5, L2*0.78, bot_bar_text, color='#3b82f6', ha='center', fontweight='bold', fontsize=9)
        
    else:
        # ⬆️ วาดเหล็กแนวตั้ง (Y-Axis)
        ax.set_title(f"Reinforcement Plan View - Y-Axis Frame\n[ {top_bar_text} / {bot_bar_text} ]", fontsize=12, fontweight='bold', pad=15)
        
        ax.vlines(x=[L1*0.85, L1*0.90, L1*0.95], ymin=0, ymax=L2*0.3, color='#ef4444', lw=1.5, label='Top Rebar (Support)')
        ax.vlines(x=[L1*0.85, L1*0.90, L1*0.95], ymin=L2*0.7, ymax=L2, color='#ef4444', lw=1.5)
        ax.text(L1*0.97, L2*0.15, top_bar_text, color='#ef4444', va='center', rotation=-90, fontweight='bold', fontsize=9)
        ax.text(L1*0.97, L2*0.85, top_bar_text, color='#ef4444', va='center', rotation=-90, fontweight='bold', fontsize=9)
        
        x_bottoms = np.linspace(L1*0.25, L1*0.75, 7)
        ax.vlines(x=x_bottoms, ymin=0.05*L2, ymax=0.95*L2, color='#3b82f6', lw=1.2, linestyle='--', label='Bottom Rebar (Midspan)')
        ax.text(L1*0.78, L2*0.5, bot_bar_text, color='#3b82f6', va='center', rotation=-90, fontweight='bold', fontsize=9)

    # --- 6. การตกแต่งและปิดงาน ---
    ax.set_aspect('equal')
    ax.set_xlim(-c1, L1 + c1)
    ax.set_ylim(-c2, L2 + c2)
    ax.set_xlabel("X - Dimension (m)", fontsize=10, fontweight='bold')
    ax.set_ylabel("Y - Dimension (m)", fontsize=10, fontweight='bold')
    
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper right", bbox_to_anchor=(1.25, 1.05), frameon=False)
    
    ax.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()
    return fig

def draw_slab_section_with_rebar(inputs, df_design=None):
    """
    Generates a Cross-Section View of the slab showing top and bottom reinforcement.
    """
    fig, ax = plt.subplots(figsize=(10, 3.5))
    
    # Extract Geometry from inputs
    L1 = inputs.get('L1', 8.0)
    h_slab = inputs.get('h_slab_cm', 20.0) / 100.0  # Convert to meters
    c1 = inputs.get('c1', 0.5)
    has_drop = inputs.get('has_drop', False)
    h_drop = inputs.get('h_drop', h_slab * 100) / 100.0
    
    # Visual limits
    plot_width = L1 + 2 * c1
    
    # 1. Draw Columns (Supports)
    # Left Column
    ax.add_patch(patches.Rectangle((-c1/2, -1.0), c1, 1.0, fill=True, color='#64748b', zorder=2))
    # Right Column
    ax.add_patch(patches.Rectangle((L1 - c1/2, -1.0), c1, 1.0, fill=True, color='#64748b', zorder=2))
    
    # 2. Draw Drop Panels (if any)
    if has_drop and h_drop > h_slab:
        drop_w = L1 / 3.0  # Approximate drop panel width for visual
        drop_depth = h_drop - h_slab
        ax.add_patch(patches.Rectangle((-drop_w/2, -drop_depth), drop_w, drop_depth, fill=True, color='#e2e8f0', edgecolor='#0f172a', zorder=3))
        ax.add_patch(patches.Rectangle((L1 - drop_w/2, -drop_depth), drop_w, drop_depth, fill=True, color='#e2e8f0', edgecolor='#0f172a', zorder=3))

    # 3. Draw Slab
    ax.add_patch(patches.Rectangle((-c1, 0), plot_width, h_slab, fill=True, facecolor='#e2e8f0', edgecolor='#0f172a', lw=1.5, zorder=4))
    
    # 4. Draw Rebars
    cover = 0.03  # 3 cm concrete cover
    
    # Top Rebars (over supports - Negative Moment)
    ax.plot([-c1*0.8, L1*0.3], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5, zorder=5, label='Top Rebar (Support)')
    ax.plot([L1*0.7, L1 + c1*0.8], [h_slab - cover, h_slab - cover], color='#ef4444', lw=2.5, zorder=5)
    
    # Bottom Rebars (midspan - Positive Moment)
    ax.plot([L1*0.1, L1*0.9], [cover, cover], color='#3b82f6', lw=2.5, zorder=5, label='Bottom Rebar (Midspan)')
    
    # 5. Annotations & Dimension Lines
    # Slab thickness dimension
    ax.annotate('', xy=(L1/2, 0), xytext=(L1/2, h_slab), arrowprops=dict(arrowstyle='<->', color='#0f172a', lw=1.5), zorder=6)
    ax.text(L1/2 + 0.1, h_slab/2, f'h = {h_slab*100:.1f} cm', va='center', fontweight='bold', fontsize=10)
    
    # Span dimension
    ax.annotate('', xy=(0, -0.5), xytext=(L1, -0.5), arrowprops=dict(arrowstyle='<->', color='#475569', lw=1.5), zorder=6)
    ax.text(L1/2, -0.4, f'Span L = {L1:.2f} m', ha='center', va='bottom', color='#334155', fontweight='bold', fontsize=10)

    # Styling
    ax.set_title("Slab Cross-Section Details", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlim(-c1*1.5, L1 + c1*1.5)
    ax.set_ylim(-0.8, h_slab + 0.2)
    ax.axis('off')
    
    # Add legend at top right
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.15), frameon=False, ncol=2)
    
    plt.tight_layout()
    return fig
def draw_punching_plan(*args, **kwargs):
    """
    Generates a Plan View of the Punching Shear Critical Section.
    Bulletproof version: Extracts parameters whether they are passed as a dict, 
    or as individual positional arguments (e.g., str, float, float, float).
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # --- 1. ระบบแยกแยะและดึงข้อมูลอัจฉริยะแบบกัน Error ---
    c1 = 50.0      # ค่าเริ่มต้น (cm)
    c2 = 50.0      # ค่าเริ่มต้น (cm)
    col_loc = 'Interior' # ค่าเริ่มต้น
    h_slab = 20.0  # ค่าเริ่มต้น (cm)
    
    # เช็คว่ามีการส่ง Dictionary (เช่น inputs) มาหรือไม่
    dict_arg = next((arg for arg in args if isinstance(arg, dict)), None)
    
    if dict_arg:
        # กรณีส่ง inputs มาเป็น Dictionary ตามปกติ
        c1 = dict_arg.get('c1', 0.5) * 100.0
        c2 = dict_arg.get('c2', 0.5) * 100.0
        col_loc = dict_arg.get('col_loc', 'Interior')
        h_slab = dict_arg.get('h_slab_cm', 20.0)
    else:
        # กรณีส่งตัวแปรแยกมา 4 ตัว (ข้อความ 1, ตัวเลข 3)
        strings = [arg for arg in args if isinstance(arg, str)]
        numbers = [arg for arg in args if isinstance(arg, (int, float))]
        
        if strings:
            col_loc = strings[0] # ดึงประเภทเสา (Interior, Edge, Corner)
            
        if len(numbers) >= 3:
            # ดึงค่า c1, c2, h_slab (ถ้าค่าน้อยกว่า 10 แสดงว่าเป็นหน่วยเมตร ให้คูณ 100)
            c1 = numbers[0] * 100.0 if numbers[0] < 10 else numbers[0]
            c2 = numbers[1] * 100.0 if numbers[1] < 10 else numbers[1]
            h_slab = numbers[2] * 100.0 if numbers[2] < 10 else numbers[2]
            
    # --- 2. คำนวณและวาดรูป ---
    d = h_slab - 3.0 - 0.6  # ประมาณค่า Effective depth (cm)
    col_color = '#334155'
    crit_color = '#ef4444'
    
    if col_loc.lower() == 'corner':
        # เสามุม
        ax.add_patch(patches.Rectangle((0, 0), c1, c2, fill=True, color=col_color))
        b1, b2 = c1 + d/2.0, c2 + d/2.0
        ax.plot([b1, b1], [0, b2], color=crit_color, ls='--', lw=2.5)
        ax.plot([0, b1], [b2, b2], color=crit_color, ls='--', lw=2.5)
        ax.set_xlim(-20, b1 + 50)
        ax.set_ylim(-20, b2 + 50)
        
    elif col_loc.lower() == 'edge':
        # เสาขอบ
        ax.add_patch(patches.Rectangle((0, -c2/2.0), c1, c2, fill=True, color=col_color))
        b1, b2 = c1 + d/2.0, c2 + d
        ax.plot([b1, b1], [-b2/2.0, b2/2.0], color=crit_color, ls='--', lw=2.5)
        ax.plot([0, b1], [b2/2.0, b2/2.0], color=crit_color, ls='--', lw=2.5)
        ax.plot([0, b1], [-b2/2.0, -b2/2.0], color=crit_color, ls='--', lw=2.5)
        ax.set_xlim(-20, b1 + 50)
        ax.set_ylim(-b2/2.0 - 50, b2/2.0 + 50)
        
    else: 
        # เสากลาง (Interior)
        ax.add_patch(patches.Rectangle((-c1/2.0, -c2/2.0), c1, c2, fill=True, color=col_color))
        b1, b2 = c1 + d, c2 + d
        ax.add_patch(patches.Rectangle((-b1/2.0, -b2/2.0), b1, b2, fill=False, edgecolor=crit_color, ls='--', lw=2.5))
        ax.set_xlim(-b1/2.0 - 50, b1/2.0 + 50)
        ax.set_ylim(-b2/2.0 - 50, b2/2.0 + 50)
        
        # ลากเส้นบอกระยะบวกข้อความ (เฉพาะเสากลาง)
        ax.annotate('', xy=(-c1/2, 0), xytext=(c1/2, 0), arrowprops=dict(arrowstyle='<->', color='white'))
        ax.text(0, 0, f'c1', color='white', ha='center', va='center', fontweight='bold')
        ax.text(-b1/2, b2/2 + 5, f'b1 = {b1:.1f} cm', color=crit_color, fontweight='bold')
        ax.text(b1/2 + 5, 0, f'b2\n=\n{b2:.1f}\ncm', color=crit_color, fontweight='bold', va='center')

    # --- 3. ตกแต่งกราฟ ---
    ax.set_title(f"Punching Shear Critical Section - {col_loc.capitalize()} Column", fontsize=13, fontweight='bold', pad=15)
    ax.set_aspect('equal')
    ax.axis('off')
    
    ax.plot([], [], color=col_color, lw=5, label='Column Dimension (c1 x c2)')
    ax.plot([], [], color=crit_color, ls='--', lw=2.5, label='Critical Perimeter (bo) at d/2')
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=1)
    
    fig.tight_layout()
    return fig
