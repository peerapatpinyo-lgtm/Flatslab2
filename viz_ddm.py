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
