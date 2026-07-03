import json
import os
import numpy as np
import matplotlib.pyplot as plt


def calculate_bjt_ic(v_be, v_ce, I_s=1e-14, V_T=0.026, V_A=100):
    v_be_clipped = np.clip(v_be, -np.inf, 1)
    v_ce_effect = 1 + (v_ce / V_A)
    saturation_factor = np.clip(1 - np.exp(-v_ce / 0.1), 0, 1) # nay de mo phong
    return I_s * (np.exp(v_be_clipped / V_T) - 1) * v_ce_effect * saturation_factor


def load_config(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f).get('functions', {})


def small_signal_at_Q(v_be_q, v_ce_q, I_s, V_T, V_A):
    """Tính Ic_Q, gm (=dIc/dVbe) và go=1/ro (=dIc/dVce) tại điểm phân cực Q."""
    I_c_q = calculate_bjt_ic(v_be_q, v_ce_q, I_s, V_T, V_A)
    g_m = I_c_q / V_T
    g_o = I_c_q / V_A          # go = 1/ro
    return I_c_q, g_m, g_o


def compute_smallsignal_results(config_file):
    """Tính Ic_Q, gm, ro cho tung diem trong JSON, tra ve danh sach ket qua."""
    cfg = load_config(config_file)
    I_s, V_T, V_A = cfg.get('I_s', 1e-14), cfg.get('V_T', 0.026), cfg.get('V_A', 80)
    points = cfg.get('points', [{'name': 'Q1', 'v_be': 0.7, 'v_ce': 5}])

    results = []
    for pt in points:
        name, v_be_q, v_ce_q = pt.get('name', 'Q'), pt['v_be'], pt['v_ce']
        I_c_q, g_m, g_o = small_signal_at_Q(v_be_q, v_ce_q, I_s, V_T, V_A)
        results.append({
            'name': name, 'v_be': v_be_q, 'v_ce': v_ce_q,
            'I_c': float(I_c_q), 'g_m': float(g_m),
            'r_o': float(1 / g_o), 'g_o': float(g_o)
        })
    return results


def save_results_to_json(results, output_file):
    """Ghi ket qua small-signal (Ic, gm, ro) ra file JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'results': results}, f, indent=2, ensure_ascii=False)
    print(f"Đã lưu kết quả vào file: {output_file}")


# ==========================================
# 2. PHẦN HIỂN THỊ
# ==========================================
def plot_smallsignal_tangents(config_file=None):
    config_file = config_file or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bjt.json')
    cfg = load_config(config_file)
    I_s, V_T, V_A = cfg.get('I_s', 1e-14), cfg.get('V_T', 0.026), cfg.get('V_A', 80)
    points = cfg.get('points', [{'name': 'Q1', 'v_be': 0.7, 'v_ce': 5}])

    v_be_range = np.linspace(0.4, 1, 200)
    v_ce_range = np.linspace(0, 15, 300)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for pt in points:
        name, v_be_q, v_ce_q = pt.get('name', 'Q'), pt['v_be'], pt['v_ce']
        I_c_q, g_m, g_o = small_signal_at_Q(v_be_q, v_ce_q, I_s, V_T, V_A)

        # --- Ic - Vbe: dac tuyen lon + tiep tuyen small-signal (slope = gm) ---
        i_c_vbe = calculate_bjt_ic(v_be_range, v_ce_q, I_s, V_T, V_A)
        ax1.plot(v_be_range, i_c_vbe * 1000, label=name + ': Vce=' + str(v_ce_q) + 'V')

        # Tiep tuyen CHI hop le trong mien tin hieu nho quanh Q (vd +-30mV)
        d_vbe = 0.03
        v_be_local = np.linspace(v_be_q - d_vbe, v_be_q + d_vbe, 20)
        tangent_vbe = (I_c_q + g_m * (v_be_local - v_be_q)) * 1000
        ax1.plot(v_be_local, tangent_vbe, '--', linewidth=2, alpha=0.9,
                  label=name + ' tiep tuyen (gm=' + f'{g_m*1e3:.2f}' + ' mA/V)')
        ax1.scatter([v_be_q], [I_c_q * 1000], color='black', zorder=5)

        # --- Ic - Vce: dac tuyen lon + tiep tuyen small-signal (slope = go = 1/ro) ---
        i_c_vce = calculate_bjt_ic(v_be_q, v_ce_range, I_s, V_T, V_A)
        ax2.plot(v_ce_range, i_c_vce * 1000, label=name + ': Vbe=' + str(v_be_q) + 'V')

        # Tiep tuyen CHI hop le trong mien tin hieu nho quanh Q (vd +-1V, ro tuyen tinh hon gm)
        d_vce = 1.0
        v_ce_local = np.linspace(max(v_ce_q - d_vce, 0), v_ce_q + d_vce, 20)
        tangent_vce = (I_c_q + g_o * (v_ce_local - v_ce_q)) * 1000
        ax2.plot(v_ce_local, tangent_vce, '--', linewidth=2, alpha=0.9,
                  label=name + ' tiep tuyen (ro=' + f'{1/g_o:.1f}' + ' Ω)')
        ax2.scatter([v_ce_q], [I_c_q * 1000], color='black', zorder=5)

    ax1.set_title('Ic - Vbe: dac tuyen lon va xap xi small-signal (gm)')
    ax1.set_xlabel('Vbe (V)'); ax1.set_ylabel('Ic (mA)')
    ax1.grid(True); ax1.legend(fontsize=8)

    ax2.set_title('Ic - Vce: dac tuyen lon va xap xi small-signal (ro)')
    ax2.set_xlabel('Vce (V)'); ax2.set_ylabel('Ic (mA)')
    ax2.set_ylim(bottom=0)
    ax2.grid(True); ax2.legend(fontsize=8)

    plt.tight_layout()
    plt.show()


# ==========================================
# 3. MAIN
# ==========================================
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'bjt_input.json')
    plot_smallsignal_tangents(config_path)
    save_results_to_json(compute_smallsignal_results(config_path),
                          os.path.join(script_dir, 'bjt_output.json'))