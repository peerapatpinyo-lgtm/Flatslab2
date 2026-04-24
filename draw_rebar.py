# draw_rebar.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_drafting_details(L1_l, L1_r, L2, c1_cm, c2_cm, h_cm, top_col_sz, top_col_sp, bot_col_sz, bot_col_sp):
    st.subheader("Typical Reinforcement Detailing (Analyzed Direction)")
    st.markdown("รูปด้านล่างนี้จำลองการเสริมเหล็กในทิศทาง L1 โดยอ้างอิงจากขนาดและระยะแอด (Spacing) ที่คุณเลือกใน **Tab 3**")
    
    # ตัวแปรสำหรับวาดรูป
    draw_L1 = max(L1_l, L1_r) * 100 # แปลงเป็น cm
    draw_L2 = L2 * 100 # แปลงเป็น cm
    
    # ---------------------------------
    # 1. วาด Plan View
    # ---------------------------------
    fig_plan, ax_plan = plt.subplots(figsize=(10, 6))
    
    # Slab Background (จำลองการวาด 1 ช่วงเสาหลัก)
    ax_plan.add_patch(patches.Rectangle((0, 0), draw_L1*1.5, draw_L2, facecolor='#f0f2f6', edgecolor='black', lw=1.5))
    
    # Column
    col_x, col_y = draw_L1*0.75, draw_L2/2
    ax_plan.add_patch(patches.Rectangle((col_x - c1_cm/2, col_y - c2_cm/2), c1_cm, c2_cm, facecolor='#31333F'))
    
    # Top Bar (สีแดง) - บริเวณหัวเสา Column Strip
    top_ext = draw_L1 * 0.3 # ระยะยื่นเหล็กบนตามมาตรฐาน (0.3L)
    ax_plan.plot([col_x - top_ext, col_x + top_ext], [col_y + c2_cm, col_y + c2_cm], color='#ff4b4b', lw=3, solid_capstyle='round')
    ax_plan.text(col_x, col_y + c2_cm + 15, f"Top Bar (Col Strip): {top_col_sz} @ {top_col_sp} cm", color='#ff4b4b', ha='center', weight='bold')

    # Bottom Bar (สีน้ำเงิน) - บริเวณกลางช่วง
    ax_plan.plot([draw_L1*0.1, draw_L1*1.4], [col_y - c2_cm - 30, col_y - c2_cm - 30], color='#1f77b4', lw=2, linestyle='--')
    ax_plan.text(col_x, col_y - c2_cm - 20, f"Bottom Bar (Col Strip): {bot_col_sz} @ {bot_col_sp} cm", color='#1f77b4', ha='center', weight='bold')

    ax_plan.set_title("PLAN VIEW: FLAT SLAB REINFORCEMENT", fontsize=14, weight='bold')
    ax_plan.set_aspect('equal')
    ax_plan.axis('off')
    
    st.pyplot(fig_plan)

    st.divider()

    # ---------------------------------
    # 2. วาด Section View
    # ---------------------------------
    fig_sec, ax_sec = plt.subplots(figsize=(10, 4))
    
    # Slab Cross Section
    ax_sec.fill_between([0, draw_L1*1.5], [0, 0], [h_cm, h_cm], facecolor='#e9ecef', edgecolor='black', hatch='//')
    
    # Column Section (หัวเสา)
    ax_sec.fill_between([col_x - c1_cm/2, col_x + c1_cm/2], [-h_cm, -h_cm], [0, 0], facecolor='#adb5bd', edgecolor='black')
    
    # Top Bar (สีแดง) ใน Section
    d_top = h_cm - 3 # ระยะหุ้ม (Covering) สมมติ 3 cm
    ax_sec.plot([col_x - top_ext, col_x + top_ext], [d_top, d_top], color='#ff4b4b', lw=3)
    # งอขอเหล็กบน
    ax_sec.plot([col_x - top_ext, col_x - top_ext], [d_top, d_top - h_cm/3], color='#ff4b4b', lw=3)
    ax_sec.plot([col_x + top_ext, col_x + top_ext], [d_top, d_top - h_cm/3], color='#ff4b4b', lw=3)
    ax_sec.text(col_x, d_top + 3, f"Top: {top_col_sz} @ {top_col_sp} cm", color='#ff4b4b', ha='center', weight='bold')

    # Bottom Bar (สีน้ำเงิน) ใน Section
    d_bot = 3 # ระยะหุ้ม
    ax_sec.plot([draw_L1*0.1, draw_L1*1.4], [d_bot, d_bot], color='#1f77b4', lw=3)
    ax_sec.text(col_x, d_bot - 5, f"Bottom: {bot_col_sz} @ {bot_col_sp} cm", color='#1f77b4', ha='center', weight='bold')

    # Dimension ความหนาพื้น
    ax_sec.annotate('', xy=(draw_L1*1.45, 0), xytext=(draw_L1*1.45, h_cm), arrowprops=dict(arrowstyle='<->', color='black'))
    ax_sec.text(draw_L1*1.47, h_cm/2, f"h = {h_cm:.0f} cm", va='center')

    ax_sec.set_title("CROSS-SECTION VIEW AT COLUMN", fontsize=14, weight='bold')
    ax_sec.set_aspect('equal')
    ax_sec.axis('off')

    st.pyplot(fig_sec)
