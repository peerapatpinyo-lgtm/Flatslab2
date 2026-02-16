import matplotlib.pyplot as plt

# ==============================================================================
# 1. COLOR PALETTE (Engineering Style)
# ==============================================================================
COLORS = {
    'bg_canvas': '#FFFFFF',       # พื้นหลังขาว
    'concrete': '#EAECEE',        # สีคอนกรีตเทาอ่อน (ที่ Error ถามหา)
    'concrete_outline': '#2C3E50',# เส้นขอบคอนกรีต (ที่ Error ถามหา)
    'rebar': '#C0392B',           # สีเหล็กเสริม/Drop Panel (แดงเข้ม)
    'dim_line': '#2E4053',        # สีเส้นบอกระยะ
    'dim_text_bg': '#FFFFFF',     # พื้นหลังตัวเลข
    'center_line': '#E74C3C',     # เส้น Center Line (แดงจาง)
    'cantilever': '#D7BDE2',      # สีไฮไลท์ส่วนยื่น (ม่วงอ่อน)
    'support': '#212F3C',         # สีจุดรองรับ
    'text_main': '#17202A'        # สีตัวหนังสือหลัก
}

# ==============================================================================
# 2. UNIT CONVERSION & CONSTANTS
# ==============================================================================
class Units:
    G = 9.80665
    CM_TO_M = 0.01
    KG_TO_N = G
    KSC_TO_PA = 98066.5 
    
def setup_matplotlib_style():
    """Configures global matplotlib settings for clean technical drawings."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 9,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'lines.linewidth': 1.0,
        'patch.linewidth': 1.0,
        'figure.autolayout': True
    })
