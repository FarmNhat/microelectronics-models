import json
import numpy as np
import matplotlib.pyplot as plt



def load_two_points_from_json(file_path):
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    voltages = np.sort(np.array(data["voltages"]))
    
    # Lấy ra v_A (VD1) và v_B (VD2)
    v_A = voltages[0]
    v_B = voltages[1]
    return v_A, v_B

def diode_equation(v_in, I_s=1e-14, V_T=0.02585, n=1):
    
    v_in_clipped = np.clip(v_in, -np.inf, 1.0)
    return I_s * (np.exp(v_in_clipped / (n * V_T)) - 1)

def calculate_all_data(v_A, v_B):
    
    
    v_min_plot = v_A - 0.15
    v_max_plot = v_B + 0.15
    v_smooth = np.linspace(v_min_plot, v_max_plot, 500)
    
    
    i_smooth_curve = diode_equation(v_smooth)
    
    
    i_A = diode_equation(v_A)
    i_B = diode_equation(v_B)
    
    
    g_m = (i_B - i_A) / (v_B - v_A)  
    i_small_ext = i_A + g_m * (v_smooth - v_A)
    
    
    points_data = {'v_A': v_A, 'i_A': i_A, 'v_B': v_B, 'i_B': i_B}
    return v_smooth, i_smooth_curve, i_small_ext, points_data


# ==========================================
# 2. PHẦN HIỂN THỊ (Visualization / Plotting)
# ==========================================
def plot_secant_model(v_smooth, i_smooth, i_small_ext, points):
    plt.figure(figsize=(10, 6.5))
    
    # Chuyển đổi đơn vị dòng điện sang mA để hiển thị trực quan
    i_smooth_mA = i_smooth * 1000
    i_small_ext_mA = i_small_ext * 1000
    i_A_mA = points['i_A'] * 1000
    i_B_mA = points['i_B'] * 1000
    
    # 1. Vẽ đường cong phi tuyến (Tín hiệu lớn) và đường tuyến tính (Tín hiệu nhỏ)
    plt.plot(v_smooth, i_smooth_mA, 'b-', label='Large', linewidth=2.5)
    plt.plot(v_smooth, i_small_ext_mA, 'r--', label='Small A B)', linewidth=1.5)
    
    # 2. Đánh dấu chấm tròn tại hai điểm A và B
    plt.plot(points['v_A'], i_A_mA, 'ko', markersize=6)
    plt.plot(points['v_B'], i_B_mA, 'ko', markersize=6)
    plt.text(points['v_A'] - 0.01, i_A_mA + 0.8, 'A', fontsize=12, fontweight='bold')
    plt.text(points['v_B'] - 0.01, i_B_mA + 0.8, 'B', fontsize=12, fontweight='bold')
    
    # 3. Vẽ các đường nét đứt gióng tọa độ y hệt như image_db9fa5.png
    plt.vlines([points['v_A'], points['v_B']], ymin=-5, ymax=[i_A_mA, i_B_mA], colors='gray', linestyles=':')
    plt.hlines([i_A_mA, i_B_mA], xmin=v_smooth[0], xmax=[points['v_A'], points['v_B']], colors='gray', linestyles=':')
    
    # 4. Ghi đè chữ VD1, VD2, ID1, ID2 lên các trục tọa độ
    plt.xticks(list(plt.xticks()[0]) + [points['v_A'], points['v_B']], 
               labels=list(plt.xticks()[0]) + [f"$V_{{D1}}$\n({points['v_A']}V)", f"$V_{{D2}}$\n({points['v_B']}V)"])
    plt.yticks(list(plt.yticks()[0]) + [i_A_mA, i_B_mA], 
               labels=list(plt.yticks()[0]) + [f"$I_{{D1}}$", f"$I_{{D2}}$"])
    
    # Khung nhìn đồ thị tập trung sát vào 2 điểm để thấy rõ khoảng hở cát tuyến như hình mẫu
    plt.xlim(v_smooth[0], v_smooth[-1])
    plt.ylim(-1, i_B_mA * 1.4)
    
    
    plt.xlabel('$V_D$ (V)', fontsize=11)
    plt.ylabel('$I_D$ (mA)', fontsize=11)
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.legend(fontsize=10, loc='upper left')
    
    plt.show()



if __name__ == "__main__":
    json_file = "diode.json"
    
    voltage_A, voltage_B = load_two_points_from_json(json_file)
    v_smooth, i_large, i_small, pts = calculate_all_data(voltage_A, voltage_B)
    plot_secant_model(v_smooth, i_large, i_small, pts)