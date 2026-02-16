# app_config.py
import matplotlib.pyplot as plt

# ==============================================================================
# 1. VISUALIZATION STYLES & COLORS
# ==============================================================================

# Professional Color Palette
COLORS = {
    'concrete_plan': '#F0F2F5',
    'concrete_cut': '#BDC3C7',
    'column': '#34495E',
    'drop_panel_plan': '#F39C12', 
    'drop_panel_cut': '#9BA4B0', 
    'dim_line': '#566573',
    'strip_line': '#3498DB', 
    'hatch_color': '#7F8C8D',
    'cs_bg': '#D6EAF8',
    'cs_text': '#154360',
    'ms_bg': '#FDFEFE',
    'ms_text': '#566573',
    'cantilever_bg': '#E8DAEF', # Purple tint for cantilever
    'support_symbol': '#2C3E50'
}

def setup_matplotlib_style():
    """Applies professional styling to matplotlib"""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
        'font.size': 9,
        'axes.titlesize': 11,
        'axes.labelsize': 9,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 9,
        'figure.titlesize': 13,
        'axes.grid': False,
        'axes.facecolor': 'white',
        'figure.facecolor': 'white'
    })

# ==============================================================================
# 2. UNIT CONVERSION & CONSTANTS
# ==============================================================================
class Units:
    G = 9.80665  # m/s^2
    CM_TO_M = 0.01
    KG_TO_N = G  # 1 kgf = 9.80665 N
    KSC_TO_PA = 98066.5 
    KSC_TO_MPA = 0.0980665
