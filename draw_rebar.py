# draw_rebar.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_dim_line(ax, x1, x2, y, text, text_offset=15):
    ax.plot([x1, x2], [y, y], color='#555555', lw=0.8)
    ax.plot([x1, x1], [y-15, y+15], color='#555555', lw=0.5)
    ax.plot([x2, x2], [y-15, y+15], color='#555555', lw=0.5)
    
    tick = 10
    ax.plot([x1-tick, x1+tick], [y-tick, y+tick], color='black', lw=1.2)
    ax.plot([x2-tick, x2+tick], [y-tick, y+tick], color='black', lw=1.2)
    ax.text((x1+x2)/2, y + text_offset, text, ha='center', va='center', fontsize=9, color='black', weight='bold')

# ✅ อัปเดตฟังก์ชันรับพารามิเตอร์ Middle Strip เข้ามาด้วย
def draw_drafting_details(L1_l, L1_r, L2, c1_cm, c2_cm, h_cm, 
                          top_col_sz, top_col_sp, bot_col_sz, bot_col_sp,
                          top_mid_sz, top_mid_sp, bot_mid_sz, bot_mid_sp):
    
    st.subheader("📐 Standard Detailing: Column & Middle Strips")
    
    x_l = -L1_l * 100 / 2
    x_r = L1_r * 100 / 2
    y_t = L2 * 100 / 2
    y_b = -L2 * 100 / 2
    
    # คำนวณความกว้างแถบ
    col_strip_w = (min(max(L1_l, L1_r), L2) / 2.0) * 100
    cs_half = col_strip_w / 2
    
    st.divider()

    # ==========================================
    # 1. PLAN VIEW (Full Panel Reinforcement)
    # ==========================================
    fig_plan, ax_plan = plt.subplots(figsize=(10, 6.5))
    
    # ขอบแผ่นพื้น
    ax_plan.plot([x_l, x_r], [y_t, y_t], color='black', lw=1.5)
    ax_plan.plot([x_l, x_r], [y_b, y_b], color='black', lw=1.5)
    
    # ขอบเขต Column Strip / Middle Strip (เส้นประ)
    ax_plan.axhline(cs_half, color='#888888', linestyle='--', lw=1.2)
    ax_plan.axhline(-cs_half, color='#888888', linestyle='--', lw=1.2)
    
    # Labels บอกโซน
    ax_plan.text(x_l + 20, 10, "COLUMN STRIP", color='#777777', fontsize=8, weight='bold')
    ax_plan.text(x_l + 20, cs_half + 10, "MIDDLE STRIP", color='#777777', fontsize=8, weight='bold')
    ax_plan.text(x_l + 20, -cs_half - 20, "MIDDLE STRIP", color='#777777', fontsize=8, weight='bold')

    # กริดและเสา
    ax_plan.axhline(0, color='#AAAAAA', linestyle='-.', lw=0.8) 
    ax_plan.axvline(0, color='#AAAAAA', linestyle='-.', lw=0.8) 
    ax_plan.add_patch(patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, facecolor='#333333', edgecolor='black', zorder=5))

    # --- 🟥 เหล็กบน (Top Bars - Red) ---
    top_ext_l, top_ext_r = -0.3 * (L1_l * 100), 0.3 * (L1_r * 100)
    
    # Top Bar (Column Strip)
    y_top_cs = 30
    ax_plan.plot([top_ext_l, top_ext_r], [y_top_cs, y_top_cs], color='#E63946', lw=3, zorder=6)
    ax_plan.plot([top_ext_l, top_ext_l], [y_top_cs-10, y_top_cs+10], color='#E63946', lw=2)
    ax_plan.plot([top_ext_r, top_ext_r], [y_top_cs-10, y_top_cs+10], color='#E63946', lw=2)
    ax_plan.text(top_ext_r + 10, y_top_cs, f"TOP (CS): {top_col_sz}@{top_col_sp}", color='#E63946', va='center', weight='bold', fontsize=9)

    # Top Bar (Middle Strip) - ระยะยื่นตาม ACI มักจะเป็น 0.22L แต่เพื่อให้รูปเคลียร์จะวาดสั้นกว่า Column Strip เล็กน้อย
    top_ext_mid_l, top_ext_mid_r = -0.22 * (L1_l * 100), 0.22 * (L1_r * 100)
    y_top_ms = cs_half + (y_t - cs_half)/2
    ax_plan.plot([top_ext_mid_l, top_ext_mid_r], [y_top_ms, y_top_ms], color='#E63946', lw=2.5, zorder=6)
    ax_plan.plot([top_ext_mid_l, top_ext_mid_l], [y_top_ms-8, y_top_ms+8], color='#E63946', lw=1.5)
    ax_plan.plot([top_ext_mid_r, top_ext_mid_r], [y_top_ms-8, y_top_ms+8], color='#E63946', lw=1.5)
    ax_plan.text(top_ext_mid_r + 10, y_top_ms, f"TOP (MS): {top_mid_sz}@{top_mid_sp}", color='#E63946', va='center', weight='bold', fontsize=9)

    # --- 🟦 เหล็กล่าง (Bottom Bars - Navy) ---
    # Bottom Bar (Column Strip)
    y_bot_cs = -30
    ax_plan.plot([x_l+25, x_r-25], [y_bot_cs, y_bot_cs], color='#1D3557', lw=3, linestyle='--', zorder=6)
    ax_plan.text(x_l + 35, y_bot_cs + 15, f"BOT (CS): {bot_col_sz}@{bot_col_sp}", color='#1D3557', va='bottom', weight='bold', fontsize=9)

    # Bottom Bar (Middle Strip)
    y_bot_ms = -cs_half - (abs(y_b) - cs_half)/2
    ax_plan.plot([x_l+25, x_r-25], [y_bot_ms, y_bot_ms], color='#1D3557', lw=2.5, linestyle='--', zorder=6)
    ax_plan.text(x_l + 35, y_bot_ms + 15, f"BOT (MS): {bot_mid_sz}@{bot_mid_sp}", color='#1D3557', va='bottom', weight='bold', fontsize=9)

    # Dimensions
    draw_dim_line(ax_plan, x_l, 0, y_b - 40, f"L1 = {L1_l} m")
    draw_dim_line(ax_plan, 0, x_r, y_b - 40, f"L1 = {L1_r} m")

    ax_plan.set_title("PLAN VIEW (Full Panel Detailing)", fontsize=11, weight='bold', loc='left')
    ax_plan.set_xlim(x_l - 50, x_r + 150) # เผื่อที่ให้ Text ด้านขวา
    ax_plan.set_ylim(y_b - 90, y_t + 30)
    ax_plan.set_aspect('equal')
    ax_plan.axis('off')
    
    st.pyplot(fig_plan)
    st.divider()

    # ==========================================
    # 2. SECTION VIEW (ตัดผ่าน Column Strip)
    # ==========================================
    fig_sec, ax_sec = plt.subplots(figsize=(10, 3.5))
    
    ax_sec.add_patch(patches.Rectangle((x_l, 0), x_r - x_l, h_cm, facecolor='#F1F3F5', edgecolor='black', lw=1.5))
    ax_sec.add_patch(patches.Rectangle((-c1_cm/2, -h_cm*1.5), c1_cm, h_cm*1.5, facecolor='#DEE2E6', edgecolor='black', lw=1.5))
    ax_sec.axvline(0, color='#888888', linestyle='-.', lw=0.8)

    cov = 3.0 
    
    # เหล็กเฉพาะ Column Strip (เพราะตัดผ่านเสา)
    ax_sec.plot([top_ext_l, top_ext_r], [h_cm - cov, h_cm - cov], color='#E63946', lw=3, zorder=4)
    ax_sec.plot([top_ext_l, top_ext_l], [h_cm - cov, h_cm - cov - 10], color='#E63946', lw=3)
    ax_sec.plot([top_ext_r, top_ext_r], [h_cm - cov, h_cm - cov - 10], color='#E63946', lw=3)
    ax_sec.plot([x_l+10, x_r-10], [cov, cov], color='#1D3557', lw=3, zorder=4)

    ax_sec.annotate(f"TOP (CS): {top_col_sz}@{top_col_sp}", 
                    xy=(top_ext_l/2, h_cm - cov), xytext=(top_ext_l/2, h_cm + 30),
                    ha='center', fontsize=9, weight='bold', color='#E63946',
                    arrowprops=dict(arrowstyle="-|>", color='#E63946', lw=1.2))
    
    ax_sec.annotate(f"BOT (CS): {bot_col_sz}@{bot_col_sp}", 
                    xy=(x_r/2, cov), xytext=(x_r/2, -h_cm),
                    ha='center', fontsize=9, weight='bold', color='#1D3557',
                    arrowprops=dict(arrowstyle="-|>", color='#1D3557', lw=1.2))

    draw_dim_line(ax_sec, top_ext_l, 0, h_cm + 60, "0.3 L1")
    draw_dim_line(ax_sec, 0, top_ext_r, h_cm + 60, "0.3 L1")
    
    dim_x = x_r + 30
    ax_sec.plot([dim_x, dim_x], [0, h_cm], color='#555555', lw=0.8)
    ax_sec.plot([dim_x-8, dim_x+8], [0, 0], color='black', lw=1.2)
    ax_sec.plot([dim_x-8, dim_x+8], [h_cm, h_cm], color='black', lw=1.2)
    ax_sec.text(dim_x + 15, h_cm/2, f"h={h_cm:.0f}cm", va='center', fontsize=9, weight='bold')

    ax_sec.set_title("SECTION AT SUPPORT (Showing Column Strip Rebar)", fontsize=11, weight='bold', loc='left')
    ax_sec.set_xlim(x_l - 50, x_r + 120)
    ax_sec.set_ylim(-h_cm*2, h_cm*4) 
    ax_sec.axis('off')

    st.pyplot(fig_sec)
