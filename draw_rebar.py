# draw_rebar.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_drafting_details(L1_l, L1_r, L2, c1_cm, c2_cm, h_cm, top_col_sz, top_col_sp, bot_col_sz, bot_col_sp):
    st.subheader("📐 Standard Detailing (Plan & Section)")
    st.markdown("แสดงผังการเสริมเหล็กบริเวณจุดต่อ (Joint) แบบจำลองตามสัดส่วนจริง (Schematic CAD Style)")
    
    # ตัวแปรสำหรับวาดรูป (หน่วย ซม.)
    x_left = -L1_l * 100 / 2    # แสดงครึ่งช่วงซ้าย
    x_right = L1_r * 100 / 2    # แสดงครึ่งช่วงขวา
    y_top = L2 * 100 / 2
    y_bot = -L2 * 100 / 2
    
    col_strip_w = (min(max(L1_l, L1_r), L2) / 2.0) * 100 # ความกว้าง Column Strip
    
    st.divider()

    # ==========================================
    # 1. วาด PLAN VIEW
    # ==========================================
    fig_plan, ax_plan = plt.subplots(figsize=(10, 6))
    
    # พื้นหลัง Slab
    ax_plan.add_patch(patches.Rectangle((x_left, y_bot), x_right - x_left, y_top - y_bot, 
                                        facecolor='#F8F9FA', edgecolor='#CED4DA', lw=2))
    
    # แรเงา Column Strip
    ax_plan.add_patch(patches.Rectangle((x_left, -col_strip_w/2), x_right - x_left, col_strip_w, 
                                        facecolor='#E9ECEF', edgecolor='none', alpha=0.7, label='Column Strip'))
    
    # เสา (Column) ตรงกลาง Joint
    ax_plan.add_patch(patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, 
                                        facecolor='#343A40', edgecolor='black', zorder=5))
    
    # Centerlines
    ax_plan.axhline(0, color='black', linestyle='-.', lw=1, alpha=0.5)
    ax_plan.axvline(0, color='black', linestyle='-.', lw=1, alpha=0.5)

    # วาดเหล็กบน (Top Bar) - สีแดง (พาดผ่านหัวเสา)
    top_ext_l = -0.3 * (L1_l * 100) # ยื่นซ้าย 0.3L
    top_ext_r = 0.3 * (L1_r * 100)  # ยื่นขวา 0.3L
    y_top_bar = c2_cm/2 + 20
    ax_plan.plot([top_ext_l, top_ext_r], [y_top_bar, y_top_bar], color='#D90429', lw=2.5, zorder=4)
    # ขีดจบเหล็ก (Hook/Cut)
    ax_plan.plot([top_ext_l, top_ext_l], [y_top_bar-5, y_top_bar+5], color='#D90429', lw=2)
    ax_plan.plot([top_ext_r, top_ext_r], [y_top_bar-5, y_top_bar+5], color='#D90429', lw=2)
    
    # วาดเหล็กล่าง (Bottom Bar) - สีน้ำเงิน (ล้วงเข้าเสาหรือทาบ)
    y_bot_bar = -c2_cm/2 - 20
    ax_plan.plot([x_left+15, x_right-15], [y_bot_bar, y_bot_bar], color='#2B2D42', lw=2, linestyle='--', zorder=4)

    # Labels ชี้เหล็ก
    ax_plan.annotate(f"Top Bar: {top_col_sz} @ {top_col_sp} cm", xy=(0, y_top_bar), xytext=(0, y_top_bar + 40),
                     ha='center', color='#D90429', weight='bold',
                     arrowprops=dict(arrowstyle="->", color='#D90429'))
                     
    ax_plan.annotate(f"Bottom Bar: {bot_col_sz} @ {bot_col_sp} cm", xy=(0, y_bot_bar), xytext=(0, y_bot_bar - 40),
                     ha='center', va='top', color='#2B2D42', weight='bold',
                     arrowprops=dict(arrowstyle="->", color='#2B2D42'))

    # Dimensions
    ax_plan.annotate('', xy=(x_left, y_bot-30), xytext=(0, y_bot-30), arrowprops=dict(arrowstyle='<->', color='black'))
    ax_plan.text(x_left/2, y_bot-50, f"L1 (Left) = {L1_l} m", ha='center', va='top')
    
    ax_plan.annotate('', xy=(0, y_bot-30), xytext=(x_right, y_bot-30), arrowprops=dict(arrowstyle='<->', color='black'))
    ax_plan.text(x_right/2, y_bot-50, f"L1 (Right) = {L1_r} m", ha='center', va='top')

    ax_plan.set_title("PLAN VIEW (Column Strip Highlighted)", fontsize=12, weight='bold', pad=15)
    ax_plan.set_xlim(x_left - 50, x_right + 50)
    ax_plan.set_ylim(y_bot - 100, y_top + 50)
    ax_plan.set_aspect('equal')
    ax_plan.axis('off')
    
    st.pyplot(fig_plan)

    st.divider()

    # ==========================================
    # 2. วาด SECTION VIEW (ปรับสัดส่วนแกน Y ให้เห็นความหนา)
    # ==========================================
    fig_sec, ax_sec = plt.subplots(figsize=(10, 3.5))
    
    # พื้น Slab
    ax_sec.add_patch(patches.Rectangle((x_left, 0), x_right - x_left, h_cm, 
                                       facecolor='#E9ECEF', edgecolor='black', hatch='//', lw=1.5))
    
    # เสา (Column) ล่างและบน
    ax_sec.add_patch(patches.Rectangle((-c1_cm/2, -h_cm*1.5), c1_cm, h_cm*1.5, facecolor='#ADB5BD', edgecolor='black', lw=1.5))
    
    # Centerline เสา
    ax_sec.axvline(0, color='black', linestyle='-.', lw=1)

    # ระยะ Covering สมมติ 3 ซม.
    cov = 3
    
    # เหล็กบน (Top Bar) สีแดง
    ax_sec.plot([top_ext_l, top_ext_r], [h_cm - cov, h_cm - cov], color='#D90429', lw=2.5)
    ax_sec.plot([top_ext_l, top_ext_l], [h_cm - cov, h_cm - cov - h_cm/3], color='#D90429', lw=2.5) # งอขอ
    ax_sec.plot([top_ext_r, top_ext_r], [h_cm - cov, h_cm - cov - h_cm/3], color='#D90429', lw=2.5) # งอขอ

    # เหล็กล่าง (Bottom Bar) สีเข้ม
    ax_sec.plot([x_left+15, x_right-15], [cov, cov], color='#2B2D42', lw=2.5)

    # Labels สำหรับ Section
    ax_sec.annotate(f"Top: {top_col_sz}@{top_col_sp}", xy=(top_ext_l/2, h_cm-cov), xytext=(top_ext_l/2, h_cm + 15),
                    ha='center', color='#D90429', weight='bold', arrowprops=dict(arrowstyle="->", color='#D90429'))
    
    ax_sec.annotate(f"Bot: {bot_col_sz}@{bot_col_sp}", xy=(x_right/2, cov), xytext=(x_right/2, -h_cm/1.5),
                    ha='center', color='#2B2D42', weight='bold', arrowprops=dict(arrowstyle="->", color='#2B2D42'))

    # Dimension ความหนาพื้น (h) ด้านขวา
    dim_x = x_right + 20
    ax_sec.annotate('', xy=(dim_x, 0), xytext=(dim_x, h_cm), arrowprops=dict(arrowstyle='<->', color='black'))
    ax_sec.text(dim_x + 10, h_cm/2, f"h = {h_cm:.0f} cm", va='center', weight='bold')

    ax_sec.set_title("CROSS-SECTION AT COLUMN", fontsize=12, weight='bold', pad=15)
    
    # ปิดแกนและจัดขอบเขต (ไม่ใช้ aspect='equal' เพื่อให้แกน Y ยืดออก เห็นความหนาพื้นชัดเจน)
    ax_sec.set_xlim(x_left - 50, x_right + 100)
    ax_sec.set_ylim(-h_cm*2, h_cm*2.5)
    ax_sec.axis('off')

    st.pyplot(fig_sec)
