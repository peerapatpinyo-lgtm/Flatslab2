# draw_rebar.py
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_drafting_details(L1_l, L1_r, L2, c1_cm, c2_cm, h_cm, 
                          top_col_sz, top_col_sp, bot_col_sz, bot_col_sp,
                          top_mid_sz, top_mid_sp, bot_mid_sz, bot_mid_sp):
    
    st.subheader("🏗️ Final Engineering Shop Drawing")
    
    # 1. การเตรียมข้อมูลสัดส่วน (Logic-Driven Scaling)
    x_left_full = L1_l * 100 / 2
    x_right_full = L1_r * 100 / 2
    y_span = L2 * 100 / 2
    cs_w = (min(max(L1_l, L1_r), L2) / 2.0) * 100 # Column Strip Width
    
    # ==========================================
    # PLAN VIEW: เน้นการแบ่งโซน CS/MS ที่ชัดเจนที่สุด
    # ==========================================
    fig_plan, ax = plt.subplots(figsize=(11, 7))
    
    # วาดพื้นคอนกรีตแยกตามแถบ (Strip Shading)
    # Column Strip (Light Gray)
    ax.add_patch(patches.Rectangle((-x_left_full, -cs_w/2), x_left_full+x_right_full, cs_w, 
                                   facecolor='#F8F9FA', edgecolor='#ADB5BD', lw=1, zorder=1))
    # Middle Strips (Slightly Darker)
    ax.add_patch(patches.Rectangle((-x_left_full, cs_w/2), x_left_full+x_right_full, y_span-cs_w/2, 
                                   facecolor='#E9ECEF', edgecolor='#ADB5BD', lw=1, zorder=1))
    ax.add_patch(patches.Rectangle((-x_left_full, -y_span), x_left_full+x_right_full, y_span-cs_w/2, 
                                   facecolor='#E9ECEF', edgecolor='#ADB5BD', lw=1, zorder=1))

    # วาดเสา (Strong Contrast)
    ax.add_patch(patches.Rectangle((-c1_cm/2, -c2_cm/2), c1_cm, c2_cm, 
                                   facecolor='#212529', edgecolor='black', zorder=10))

    # เส้น Grid Centerlines
    ax.axhline(0, color='red', linestyle='-.', lw=0.7, alpha=0.6, zorder=2)
    ax.axvline(0, color='red', linestyle='-.', lw=0.7, alpha=0.6, zorder=2)

    # --- การจัดวางเหล็กเสริม (Reinforcement Layout) ---
    # ใช้สีแยกความสำคัญ: แดง=บน (Top), น้ำเงิน=ล่าง (Bottom)
    
    # 1. Column Strip Rebars
    t_cs_l, t_cs_r = -0.3 * (L1_l * 100), 0.3 * (L1_r * 100)
    ax.plot([t_cs_l, t_cs_r], [c2_cm/2 + 15, c2_cm/2 + 15], color='#D00000', lw=2.5, label='Top CS', zorder=11)
    ax.plot([-x_left_full+10, x_right_full-10], [-c2_cm/2 - 15, -c2_cm/2 - 15], color='#003566', lw=2.5, ls='--', zorder=11)

    # 2. Middle Strip Rebars
    t_ms_l, t_ms_r = -0.22 * (L1_l * 100), 0.22 * (L1_r * 100)
    y_ms_pos = cs_w/2 + (y_span - cs_w/2)/2
    ax.plot([t_ms_l, t_ms_r], [y_ms_pos, y_ms_pos], color='#D00000', lw=2, zorder=11)
    ax.plot([-x_left_full+10, x_right_full-10], [-y_ms_pos, -y_ms_pos], color='#003566', lw=2, ls='--', zorder=11)

    # --- Callouts (Leader Lines) เพื่อกันข้อความซ้อนรูป ---
    # ใช้แกน X ฝั่งขวาสุดสำหรับ Label Column Strip และฝั่งซ้ายสำหรับ Middle Strip
    label_x_r = x_right_full + 30
    label_x_l = -x_left_full - 30

    # Column Strip Labels
    ax.annotate(f"TOP CS: {top_col_sz}@{top_col_sp}", xy=(t_cs_r, c2_cm/2 + 15), xytext=(label_x_r, c2_cm/2 + 50),
                arrowprops=dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=90"), fontsize=9, weight='bold')
    ax.annotate(f"BOT CS: {bot_col_sz}@{bot_col_sp}", xy=(x_right_full-50, -c2_cm/2 - 15), xytext=(label_x_r, -c2_cm/2 - 50),
                arrowprops=dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=90"), fontsize=9)

    # Middle Strip Labels
    ax.annotate(f"TOP MS: {top_mid_sz}@{top_mid_sp}", xy=(t_ms_l, y_ms_pos), xytext=(label_x_l, y_ms_pos + 30),
                ha='right', arrowprops=dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=90"), fontsize=9, weight='bold')
    ax.annotate(f"BOT MS: {bot_mid_sz}@{bot_mid_sp}", xy=(-x_left_full+50, -y_ms_pos), xytext=(label_x_l, -y_ms_pos - 30),
                ha='right', arrowprops=dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=90"), fontsize=9)

    # ตั้งค่าแกนและชื่อรูป
    ax.set_title("PLAN VIEW: REINFORCEMENT ARRANGEMENT", fontsize=12, pad=20, weight='bold')
    ax.set_xlim(label_x_l - 100, label_x_r + 100)
    ax.set_ylim(-y_span - 50, y_span + 50)
    ax.set_aspect('equal')
    ax.axis('off')
    st.pyplot(fig_plan)

    st.divider()

    # ==========================================
    # SECTION VIEW: ใช้ "Split Scale" เพื่อให้เห็นความหนาพื้นชัดเจน
    # ==========================================
    fig_sec, ax_sec = plt.subplots(figsize=(11, 4))
    
    # พื้นและเสา
    ax_sec.add_patch(patches.Rectangle((-x_left_full, 0), x_left_full+x_right_full, h_cm, 
                                       facecolor='#F1F3F5', edgecolor='black', lw=1.5))
    ax_sec.add_patch(patches.Rectangle((-c1_cm/2, -h_cm*2), c1_cm, h_cm*2, 
                                       facecolor='#DEE2E6', edgecolor='black', hatch='///', lw=1))
    
    # เส้นบอก Grid
    ax_sec.axvline(0, color='red', linestyle='-.', lw=0.8, alpha=0.5)

    # วาดเหล็กเสริมในรูปตัด (เน้นระยะ Covering 3cm)
    cov = 3.0
    # Top Bar with Hook
    ax_sec.plot([t_cs_l, t_cs_r], [h_cm-cov, h_cm-cov], color='#D00000', lw=3, zorder=5)
    ax_sec.plot([t_cs_l, t_cs_l], [h_cm-cov, h_cm-cov-10], color='#D00000', lw=3, zorder=5)
    ax_sec.plot([t_cs_r, t_cs_r], [h_cm-cov, h_cm-cov-10], color='#D00000', lw=3, zorder=5)
    
    # Bottom Bar
    ax_sec.plot([-x_left_full+5, x_right_full-5], [cov, cov], color='#003566', lw=3, zorder=5)

    # มิติความหนา (h)
    ax_sec.annotate('', xy=(x_right_full + 20, 0), xytext=(x_right_full + 20, h_cm),
                    arrowprops=dict(arrowstyle='<->', color='black'))
    ax_sec.text(x_right_full + 30, h_cm/2, f"h = {h_cm} cm", va='center', weight='bold')

    # มิติระยะหยุดเหล็กบน (0.3L)
    ax_sec.annotate('', xy=(t_cs_l, h_cm + 10), xytext=(0, h_cm + 10), arrowprops=dict(arrowstyle='<->', color='gray'))
    ax_sec.text(t_cs_l/2, h_cm + 20, "0.3 L1", ha='center', fontsize=8)

    ax_sec.set_title("CROSS SECTION A-A (AT COLUMN STRIP)", fontsize=12, weight='bold')
    ax_sec.set_xlim(-x_left_full - 50, x_right_full + 100)
    # หัวใจสำคัญ: ปรับ ylim ให้แคบเพื่อให้พื้นดูหนา (Non-equal aspect ratio สำหรับ Section)
    ax_sec.set_ylim(-h_cm*3, h_cm*5)
    ax_sec.axis('off')
    
    st.pyplot(fig_sec)
