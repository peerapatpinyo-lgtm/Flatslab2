import math

def calculate_efm(calc_obj):
    """
    Equivalent Frame Method (EFM) - Stiffness Calculation
    อ้างอิงมาตรฐาน ACI 318 และหลักการของ Wight/MacGregor
    """
    
    # 1. ดึงข้อมูลเบื้องต้นจาก calc_obj
    col = calc_obj.get('col_size', {'c1': 50, 'c2': 50})   # ขนาดเสา (cm)
    geom = calc_obj.get('geom', {})                       # ขนาดทางกายภาพ
    bc = calc_obj.get('bc', {'h_up': 3.0, 'h_lo': 3.0})   # ความสูงชั้น (m)
    mat = calc_obj.get('mat', {'fc': 240})                # คุณสมบัติวัสดุ
    
    # แปลงหน่วย Dimensions เป็นเมตร (m)
    c1 = col['c1'] / 100.0      # ขนาดเสาในทิศทางที่พิจารณา
    c2 = col['c2'] / 100.0      # ขนาดเสาในทิศทางตั้งฉาก
    L1 = geom.get('L1_r', 6.0)  # ความยาวช่วง (Span length)
    L2 = geom.get('L2', 6.0)    # ความกว้างแผ่นพื้น (Transverse width)
    h_s = geom.get('h_slab', 0.20) # ความหนาพื้น
    
    # 2. คุณสมบัติของวัสดุ (Material Properties)
    # E_c = 15100 * sqrt(fc') ksc -> แปลงเป็น kPa (kN/m²)
    # 1 ksc ≈ 98.0665 kPa
    fc_prime = mat['fc']
    Ec_ksc = 15100 * (fc_prime**0.5)
    Ec_kPa = Ec_ksc * 98.0665 
    
    # 3. Slab Stiffness (Ks)
    # คำนวณ Inertia ของพื้น (Gross Section)
    Is_gross = (L2 * (h_s**3)) / 12
    # Ks = 4EI/L (กรณีปลายอีกด้านถูกยึดแน่น/สมมาตร)
    Ks = (4 * Ec_kPa * Is_gross) / L1
    
    # 4. Column Stiffness (Kc)
    # Inertia ของเสา Ic = (width * depth^3) / 12
    Ic = (c2 * (c1**3)) / 12 
    
    h_up = bc.get('h_up', 3.0)
    h_lo = bc.get('h_lo', 3.0)
    
    # ค่า Factor k สำหรับเสา (Fixed far end = 4.0)
    k_col = 4.0 
    
    # Stiffness ของเสาบนและเสาล่าง
    Kc_up = (k_col * Ec_kPa * Ic) / h_up if h_up > 0 else 0
    Kc_lo = (k_col * Ec_kPa * Ic) / h_lo if h_lo > 0 else 0
    Sum_Kc = Kc_up + Kc_lo
    
    # 5. Torsional Member Stiffness (Kt) - ACI R8.11.5
    # คำนวณหาค่าคงที่การบิด (Torsion Constant, C)
    # x = ด้านสั้น (ความหนาพื้น), y = ด้านยาว (ความลึกเสา c1)
    x = min(h_s, c1)
    y = max(h_s, c1)
    
    # สูตรคำนวณค่า C สำหรับหน้าตัดสี่เหลี่ยมผืนผ้า
    C = (1 - 0.63 * (x/y)) * (x**3) * y / 3
    
    # คำนวณ Kt (Stiffness ของส่วนรับแรงบิด)
    term1 = 9 * Ec_kPa * C
    term2 = L2 * ((1 - (c2/L2))**3)
    
    if term2 <= 0: 
        term2 = 0.0001 # ป้องกัน Division by zero
    
    # สำหรับเสาภายใน (Interior Column) คิดแรงบิดทั้งสองข้าง
    Kt = (term1 / term2) * 2 
    
    # 6. Equivalent Column Stiffness (Kec)
    # สูตรความสัมพันธ์แบบสปริงต่ออนุกรม: 1/Kec = 1/ΣKc + 1/Kt
    if Sum_Kc > 0 and Kt > 0:
        Kec = 1 / ((1/Sum_Kc) + (1/Kt))
    else:
        Kec = Sum_Kc # ถ้าไม่มีแรงบิด ให้ใช้ค่า Kc โดยตรง
        
    # 7. Distribution Factors (DF) ที่จุดต่อ (Joint)
    # ใช้สำหรับกระจาย Unbalanced Moment เข้าสู่พื้นและเสาเสมือน
    Sum_K_Joint = Ks + Kec
    if Sum_K_Joint > 0:
        df_slab = Ks / Sum_K_Joint
        df_col = Kec / Sum_K_Joint
    else:
        df_slab, df_col = 0, 0
        
    # ส่งค่าผลลัพธ์กลับในรูปแบบ Dictionary
    return {
        'Ic': Ic,
        'Is': Is_gross,
        'Ec_kPa': Ec_kPa,
        'Kc_up': Kc_up,
        'Kc_lo': Kc_lo,
        'Sum_Kc': Sum_Kc,
        'C': C,
        'Kt': Kt,
        'Kec': Kec,
        'Ks': Ks,
        'df_slab': df_slab,
        'df_col': df_col
    }
