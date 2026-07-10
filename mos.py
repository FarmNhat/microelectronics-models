import json
import os
import numpy as np
import matplotlib.pyplot as plt


def calculate_mosfet_id(v_gs, v_ds, Vth=0.7, k_n=200e-6, lambda_=0.02):
    v_ov = np.clip(v_gs - Vth, 0, np.inf)  # qua ap (overdrive), <=0 la cutoff -> Id=0

    id_triode = k_n * (v_ov * v_ds - (v_ds ** 2) / 2)
    id_sat = 0.5 * k_n * (v_ov ** 2) * (1 + lambda_ * v_ds)

    is_triode = v_ds < v_ov  # bien gioi triode/saturation: Vds < Vov
    id_out = np.where(is_triode, id_triode, id_sat)

    return np.where(v_ov <= 0, 0.0, id_out)  # cutoff


def load_config(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f).get('functions', {})


def small_signal_at_Q(v_gs_q, v_ds_q, Vth, k_n, lambda_):

    I_d_q = calculate_mosfet_id(v_gs_q, v_ds_q, Vth, k_n, lambda_)

    v_ov_q = max(v_gs_q - Vth, 0.0)
    g_m = k_n * v_ov_q * (1 + lambda_ * v_ds_q)
    g_ds = 0.5 * k_n * (v_ov_q ** 2) * lambda_   # ~ I_d_q * lambda_, go = 1/ro

    return I_d_q, g_m, g_ds


def compute_smallsignal_results(config_file):

    cfg = load_config(config_file)
    Vth = cfg.get('Vth', 0.7)
    k_n = cfg.get('k_n', 200e-6)
    lambda_ = cfg.get('lambda_', 0.02)
    points = cfg.get('points', [{'name': 'Q1', 'v_gs': 1.2, 'v_ds': 1.8}])

    results = []
    for pt in points:
        name, v_gs_q, v_ds_q = pt.get('name', 'Q'), pt['v_gs'], pt['v_ds']
        I_d_q, g_m, g_ds = small_signal_at_Q(v_gs_q, v_ds_q, Vth, k_n, lambda_)
        results.append({
            'name': name, 'v_gs': v_gs_q, 'v_ds': v_ds_q,
            'I_d': float(I_d_q), 'g_m': float(g_m),
            'r_o': float(1 / g_ds) if g_ds != 0 else float('inf'), 'g_ds': float(g_ds)
        })

    return results


def save_results_to_json(results, output_file):
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'results': results}, f, indent=2, ensure_ascii=False)
    print(f"saved: {output_file}")


# ==========================================
# 2. PHẦN HIỂN THỊ
# ==========================================
def plot_smallsignal_tangents(config_file=None):
    config_file = config_file or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mos_input.json')
    cfg = load_config(config_file)
    Vth = cfg.get('Vth', 0.7)
    k_n = cfg.get('k_n', 200e-6)
    lambda_ = cfg.get('lambda_', 0.02)
    points = cfg.get('points', [{'name': 'Q1', 'v_gs': 1.2, 'v_ds': 1.8}])

    v_gs_range = np.linspace(Vth, Vth + 1.5, 200)
    v_ds_range = np.linspace(0, 3, 300)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for pt in points:
        name, v_gs_q, v_ds_q = pt.get('name', 'Q'), pt['v_gs'], pt['v_ds']
        I_d_q, g_m, g_ds = small_signal_at_Q(v_gs_q, v_ds_q, Vth, k_n, lambda_)

        # --- Id - Vgs: dac tuyen lon + tiep tuyen small-signal (slope = gm) ---
        i_d_vgs = calculate_mosfet_id(v_gs_range, v_ds_q, Vth, k_n, lambda_)
        ax1.plot(v_gs_range, i_d_vgs * 1000, label=name + ': Vds=' + str(v_ds_q) + 'V')

        # Tiep tuyen CHI hop le trong mien tin hieu nho quanh Q (vd +-30mV)
        d_vgs = 0.03
        v_gs_local = np.linspace(v_gs_q - d_vgs, v_gs_q + d_vgs, 20)
        tangent_vgs = (I_d_q + g_m * (v_gs_local - v_gs_q)) * 1000
        ax1.plot(v_gs_local, tangent_vgs, '--', linewidth=2, alpha=0.9,
                  label=name + ' gm=' + f'{g_m*1e3:.2f}' + ' mA/V')
        ax1.scatter([v_gs_q], [I_d_q * 1000], color='black', zorder=5)

        # --- Id - Vds: dac tuyen lon + tiep tuyen small-signal (slope = gds = 1/ro) ---
        i_d_vds = calculate_mosfet_id(v_gs_q, v_ds_range, Vth, k_n, lambda_)
        ax2.plot(v_ds_range, i_d_vds * 1000, label=name + ': Vgs=' + str(v_gs_q) + 'V')

        # Tiep tuyen CHI hop le trong mien tin hieu nho quanh Q (vd +-0.2V, ro tuyen tinh hon gm)
        d_vds = 0.2
        v_ds_local = np.linspace(max(v_ds_q - d_vds, 0), v_ds_q + d_vds, 20)
        tangent_vds = (I_d_q + g_ds * (v_ds_local - v_ds_q)) * 1000
        ax2.plot(v_ds_local, tangent_vds, '--', linewidth=2, alpha=0.9,
                  label=name + ' ro=' + f'{1/g_ds:.1f}' + ' Ω')
        ax2.scatter([v_ds_q], [I_d_q * 1000], color='black', zorder=5)

    ax1.set_title('Id - Vgs small-signal (gm)')
    ax1.set_xlabel('Vgs (V)'); ax1.set_ylabel('Id (mA)')
    ax1.grid(True); ax1.legend(fontsize=8)

    ax2.set_title('Id - Vds small-signal (ro)')
    ax2.set_xlabel('Vds (V)'); ax2.set_ylabel('Id (mA)')
    ax2.set_ylim(bottom=0)
    ax2.grid(True); ax2.legend(fontsize=8)

    plt.tight_layout()
    plt.show()


# ==========================================
# 3. MAIN
# ==========================================
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'mos_input.json')
    plot_smallsignal_tangents(config_path)
    save_results_to_json(compute_smallsignal_results(config_path),
                          os.path.join(script_dir, 'mos_output.json'))