import json
import os
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

##### JSON #########

json_filename = "mos_re.json"

if not os.path.exists(json_filename):
    print(f"LỖI: Không tìm thấy file {json_filename}!")
    print("Vui lòng tạo file JSON này cùng thư mục với file code Python.")
    exit()

with open(json_filename, "r") as file:
    data = json.load(file)

mosfet_name = data["transistor"]["name"]
gm = data["transistor"]["gm"]
ro = data["transistor"]["ro"]
Cgs = data["transistor"]["Cgs"]
Cgd = data["transistor"]["Cgd"]
#Cds = data["transistor"]["Cds"]

R_sig = data["circuit"]["R_sig"]
R_D = data["circuit"]["R_D"]

f_start = data["simulation"]["f_start"]
f_end = data["simulation"]["f_end"]
points = data["simulation"]["points"]



###################


R_L_eff = (R_D * ro) / (R_D + ro)
Av0 = -gm * R_L_eff
C_in = Cgs + Cgd * (1 - Av0)
omega_H = 1 / (R_sig * C_in)
f_H = omega_H / (2 * np.pi)


num = [Av0]
den = [1/omega_H, 1]
sys = signal.TransferFunction(num, den)


f_start, f_end = 10, 1e10
w = np.logspace(np.log10(f_start), np.log10(f_end), 1000) * 2 * np.pi 


w, mag, phase = signal.bode(sys, w)
f_vector = w / (2 * np.pi)


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

ax1.semilogx(f_vector, mag, 'b-', linewidth=2, label='Gain Av (dB)')
ax1.axvline(f_H, color='r', linestyle='--', label=f'Tần số cắt = {f_H/1e6:.2f} MHz')
ax1.axhline(mag[0] - 3, color='g', linestyle=':', label='Điểm -3 dB')

ax1.set_ylabel('Biên độ', fontsize=12)
ax1.set_title('FREQ RESPONSE MILLER CỰC TRỘI', fontsize=14, fontweight='bold')
ax1.grid(True, which="both", linestyle=':', alpha=0.6)
ax1.legend(loc='lower left')
ax2.semilogx(f_vector, phase, 'm-', linewidth=2, label='lệch pha')
ax2.axvline(f_H, color='r', linestyle='--')

ax2.set_xlabel('Tần số (Hz) theo log', fontsize=12)
ax2.set_ylabel('Pha (Độ $^\circ$)', fontsize=12)
ax2.grid(True, which="both", linestyle=':', alpha=0.6)
ax2.legend(loc='lower left')

plt.tight_layout()
plt.show()