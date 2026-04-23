# เพิ่มฟังก์ชันนี้ต่อท้ายในไฟล์ viz_ddm.py

def draw_rebar_plan_view(inputs, edited_df):
    """วาดรูปแปลน (Top View) แสดง Column Strip, Middle Strip และแนวการจัดเหล็ก"""
    # 1. ดึงข้อมูล Geometry
    L1 = inputs.get('l1', 5.0) * 100 # แปลงเป็น cm
    L2 = inputs.get('l2', 5.0) * 100
    c1 = inputs.get('c1', 0.5) * 100
    c2 = inputs.get('c2', 0.5) * 100
    
    # 2. คำนวณความกว้าง Strip
    cs_width = min(L1, L2) / 2.0
    ms_width_1 = L1 - cs_width
    ms_width_2 = L2 - cs_width
    
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
    # พื้นที่ทับซ้อนคือ Column Strip Intersection
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
