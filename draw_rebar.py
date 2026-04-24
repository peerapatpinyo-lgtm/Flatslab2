# draw_rebar.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- ฟังก์ชันช่วยวาดเส้นบอกมิติ (CAD Style Dimension) ---
def draw_cad_dim(ax, x1, x2, y, text, text_y_offset=15):
    # เส้นหลัก
    ax.plot([x1, x2], [y, y], color='black', lw=0.8)
    # เส้น Extension (ตั้งฉาก)
    ax.plot([x1, x1], [y-10, y+10], color='black', lw=0.8)
    ax.plot([x2, x2], [y-10, y+10], color='black', lw=0.8)
    # Architectural Ticks (ขีดเฉียง 45 องศา)
    tick_len = 8
    ax.plot([x1-tick_len, x1+tick_len], [y-tick_len, y+tick_len], color='black', lw=1.2)
    ax.plot([x2-tick_len, x2+tick_len], [y-tick_len, y+tick_len], color='black', lw=1.2)
    # ตัวหนังสือ
    ax.text((x1+x2)/2, y + text_y_offset, text, ha='center', va='center', fontsize=9, family='monospace')

# --- ฟังก์ชันช่วยวาด Break Line (รอยตัดต่อเนื่อง) ---
def draw_break_line(ax, x, y_bottom, y_top, is_vertical=True):
    # สร้างเส้นหยักๆ แบบ CAD
    if is_vertical:
        y_mid = (y_bottom + y_top) / 2
        ax.plot([x, x, x+15, x-15, x, x], 
                [y_bottom, y_mid-20, y_mid-10, y_mid+10, y_mid+20, y_top], 
                color='black', lw=1.2)

def draw_drafting_details(L1_l, L1_r, L2, c1_cm, c2_cm, h_cm, top_col_sz, top_col_sp, bot_col_sz, bot_col_sp):
    st.subheader("📐 Structural Detailing (CAD Generation)")
    
    # แปลงระยะเป็น ซม.
    x_left = -L1_l * 100 / 2
    x_right = L1_r * 100 / 2
    y_top = L2 * 100 / 2
    y_bot = -L2 * 100 / 2
    col_strip_w = (min(max(L1_l, L1_r), L2) / 2.0) * 100
    
    st.divider()

    # ==========================================
    # 1. วาด PLAN VIEW (Structural Framing Plan)
    # ==========================================
    fig_plan, ax_plan = plt.subplots(figsize=(10, 6))
    
    # วาดขอบพื้นด้านบนและล่าง
    ax_plan.plot([x_left, x_right], [y_top, y_top], color='black', lw=1.5)
    ax_plan.plot([x_left, x_right], [y_bot, y_bot], color='black', lw=1.5)
    
    # วาด Break lines ด้านซ้ายและขวา
    draw_break_line(ax_plan, x_left, y_bot, y_top, is_vertical=True)
    draw_break_line(ax_plan, x_right, y_bot, y_top, is_vertical=True)
    
    # ขอบเขต Column Strip (เส้นประ)
    cs_y_top = col_strip_w / 2
    cs_y_bot = -col_strip_w / 2
    ax_plan.plot([x_left, x_right], [cs_y_top, cs_y_top], color='gray', linestyle='--', lw=1)
    ax_plan.plot([x_left, x_right], [cs_y_bot, cs_y_bot], color='gray', linestyle='--', lw=1)
    ax_plan.text(x_left + 50, cs_y_top - 20, "COLUMN STRIP BOUNDARY", color='gray', fontsize=8, family='monospace')

    # Grid Lines (Centerlines)
    ax_plan.plot([x_left-50, x_right+50], [0, 0], color='black', linestyle='-.', lw=0.8) # X-axis
    ax_plan.plot([0, 0], [y_bot-50, y_top+50], color='black', linestyle='-.', lw=0.8) # Y-axis
    
    # Grid Bubbles
    ax_plan.add_patch(patches.Circle((0, y_top + 60), 20, facecolor='white', edgecolor='black', lw=1, zorder=10))
    ax_plan.text(0, y_top + 60, "1", ha='center', va='center', fontsize=10, weight='bold')
    ax_plan.add_patch(patches.Circle((x_left - 60, 0), 20, facecolor='white', edgecolor='black', lw=1, zorder=10))
    ax_plan.text(x_left - 60, 0, "A", ha='center', va='center', fontsize=10, weight='bold')

    # หน้าตัดเสา (Hatching กากบาท)
    ax_plan.add_patch(patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, 
                                        facecolor='white', edgecolor='black', hatch='X', lw=1.5, zorder=5))

    # ---- การวาดเหล็กเสริม (Reinforcement) ----
    # 1. Top Bar (สีแดง)
    top_ext_l = -0.3 * (L1_l * 100)
    top_ext_r = 0.3 * (L1_r * 100)
    y_top_bar = c2_cm/2 + 30
    ax_plan.plot([top_ext_l, top_ext_r], [y_top_bar, y_top_bar], color='#D90429', lw=2)
    ax_plan.plot([top_ext_l, top_ext_l], [y_top_bar-8, y_top_bar+8], color='#D90429', lw=2) # Cut
    ax_plan.plot([top_ext_r, top_ext_r], [y_top_bar-8, y_top_bar+8], color='#D90429', lw=2) # Cut
    
    # 2. Bottom Bar (สีน้ำเงิน)
    y_bot_bar = -c2_cm/2 - 30
    ax_plan.plot([x_left+20, x_right-20], [y_bot_bar, y_bot_bar], color='#003049', lw=2, linestyle='dashed')
    ax_plan.plot([x_left+20, x_left+20], [y_bot_bar-5, y_bot_bar+5], color='#003049', lw=2)
    ax_plan.plot([x_right-20, x_right-20], [y_bot_bar-5, y_bot_bar+5], color='#003049', lw=2)

    # CAD Multi-leaders (เส้นชี้บอกรายละเอียด)
    ax_plan.annotate(f"TOP REBAR:\n{top_col_sz} @ {top_col_sp} cm\n(L=0.3L1)", 
                     xy=(top_ext_r - 20, y_top_bar), xytext=(top_ext_r + 40, y_top_bar + 50),
                     fontsize=9, family='monospace', color='#D90429',
                     arrowprops=dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=90,rad=0", color='#D90429'))

    ax_plan.annotate(f"BOT REBAR:\n{bot_col_sz} @ {bot_col_sp} cm", 
                     xy=(x_left + 40, y_bot_bar), xytext=(x_left - 20, y_bot_bar - 80),
                     fontsize=9, family='monospace', color='#003049',
                     arrowprops=dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=90,rad=0", color='#003049'))

    # Dimensions
    draw_cad_dim(ax_plan, x_left, 0, y_bot - 80, f"L1 (LEFT) = {L1_l} m")
    draw_cad_dim(ax_plan, 0, x_right, y_bot - 80, f"L1 (RIGHT) = {L1_r} m")

    ax_plan.set_title("PLAN VIEW - REINFORCEMENT AT JOINT", fontsize=11, weight='bold', pad=20, family='monospace')
    ax_plan.set_xlim(x_left - 100, x_right + 150)
    ax_plan.set_ylim(y_bot - 150, y_top + 100)
    ax_plan.set_aspect('equal')
    ax_plan.axis('off')
    
    st.pyplot(fig_plan)

    st.divider()

    # ==========================================
    # 2. วาด SECTION VIEW (Cross-Section Profile)
    # ==========================================
    fig_sec, ax_sec = plt.subplots(figsize=(10, 4))
    
    # พื้น Slab (Hatching จุดคอนกรีต)
    slab = patches.Rectangle((x_left, 0), x_right - x_left, h_cm, 
                             facecolor='#F8F9FA', edgecolor='black', hatch='...', lw=1.5)
    ax_sec.add_patch(slab)
    draw_break_line(ax_sec, x_left, 0, h_cm, is_vertical=True)
    draw_break_line(ax_sec, x_right, 0, h_cm, is_vertical=True)
    
    # เสา (Column) ล่างและบน (Hatching ลายอิฐ/คอนกรีต)
    ax_sec.add_patch(patches.Rectangle((-c1_cm/2, -h_cm*1.5), c1_cm, h_cm*1.5, facecolor='white', edgecolor='black', hatch='//', lw=1.2))
    ax_sec.plot([-c1_cm/2 - 10, c1_cm/2 + 10], [-h_cm*1.5, -h_cm*1.5], color='black', lw=1.5) # รอยตัดเสาล่าง
    
    # Centerline เสา
    ax_sec.plot([0, 0], [-h_cm*2, h_cm*2], color='black', linestyle='-.', lw=0.8)
    ax_sec.add_patch(patches.Circle((0, h_cm*2 + 15), 12, facecolor='white', edgecolor='black', lw=1, zorder=10))
    ax_sec.text(0, h_cm*2 + 15, "1", ha='center', va='center', fontsize=8, weight='bold')

    # Covering
    cov = 3 
    
    # Top Bar (มี Hook หรืองอฉาก)
    ax_sec.plot([top_ext_l, top_ext_r], [h_cm - cov, h_cm - cov], color='#D90429', lw=2.5)
    ax_sec.plot([top_ext_l, top_ext_l], [h_cm - cov, h_cm - cov - 8], color='#D90429', lw=2.5) # Hook
    ax_sec.plot([top_ext_r, top_ext_r], [h_cm - cov, h_cm - cov - 8], color='#D90429', lw=2.5) # Hook

    # Bottom Bar
    ax_sec.plot([x_left+10, x_right-10], [cov, cov], color='#003049', lw=2.5)

    # CAD Multi-leaders สำหรับ Section
    ax_sec.annotate(f"{top_col_sz} @ {top_col_sp} cm", 
                    xy=(top_ext_l/2, h_cm - cov), xytext=(top_ext_l/2 - 20, h_cm + 25),
                    fontsize=9, family='monospace', color='#D90429',
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color='#D90429'))
    
    ax_sec.annotate(f"{bot_col_sz} @ {bot_col_sp} cm", 
                    xy=(x_right/2, cov), xytext=(x_right/2 + 20, -h_cm),
                    fontsize=9, family='monospace', color='#003049',
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color='#003049'))

    # Dimensions
    draw_cad_dim(ax_sec, top_ext_l, 0, h_cm + 45, f"0.3 L1")
    draw_cad_dim(ax_sec, 0, top_ext_r, h_cm + 45, f"0.3 L1")
    
    # Dimension ความหนาพื้นด้านขวา (ใช้ Vertical tick)
    dim_x = x_right + 30
    ax_sec.plot([dim_x, dim_x], [0, h_cm], color='black', lw=0.8)
    ax_sec.plot([dim_x-10, dim_x+10], [0, 0], color='black', lw=0.8) # Ext line
    ax_sec.plot([dim_x-10, dim_x+10], [h_cm, h_cm], color='black', lw=0.8) # Ext line
    ax_sec.text(dim_x + 10, h_cm/2, f"THK. = {h_cm:.0f} cm", va='center', fontsize=9, family='monospace')

    ax_sec.set_title("SECTION A-A (CROSS-SECTION AT SUPPORT)", fontsize=11, weight='bold', pad=25, family='monospace')
    ax_sec.set_xlim(x_left - 50, x_right + 100)
    ax_sec.set_ylim(-h_cm*2, h_cm*3)
    ax_sec.axis('off')

    st.pyplot(fig_sec)
