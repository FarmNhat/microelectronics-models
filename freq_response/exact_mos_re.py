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
Cdb = data["transistor"]["Cdb"]   # tu Mang - Than (thay cho Cds truoc day)
Csb = data["transistor"]["Csb"]   # tu Nguon - Than (chi de tham khao, xem ghi chu ben duoi)

R_sig = data["circuit"]["R_sig"]
R_D = data["circuit"]["R_D"]

f_start = data["simulation"]["f_start"]
f_end = data["simulation"]["f_end"]
points = data["simulation"]["points"]

print(f"--- Đã nạp cấu hình thành công cho Transistor: {mosfet_name} ---")

###################

# 
# Mo hinh gom Cgs, Cgd, gm*vgs, ro, va hai tu ky sinh do than (body): Cdb (D-B) va Csb (S-B).
# Trong cau hinh khuech dai CS chuan, cuc Nguon S duoc noi truc tiep xuong AC-ground
# (dong thoi than B thuong cung noi GND), nen Csb bi ngan mach ca hai dau xuong dat
# -> Csb KHONG xuat hien trong phuong trinh ham truyen (khong tao thanh nut tin hieu nao ca).
# Cdb thi tuong duong voi tu "Cds" (Mang - noi dat) trong mo hinh rut gon truoc day,
# vi noi dat va cuc Nguon la mot node AC. Do do chi can doi ten Cds -> Cdb, cau truc
# phuong trinh giu nguyen.


# 2. TÍNH TOÁN THEO MÔ HÌNH ĐẦY ĐỦ (EXACT POLYNOMIAL)
R_L_eff = (R_D * ro) / (R_D + ro)
Av0 = -gm * R_L_eff

#hệ số của den = as^2 + bs + 1
a = R_sig * R_L_eff * (Cgs * Cgd + Cgs * Cdb + Cgd * Cdb)
b = R_sig * (Cgs + Cgd * (1 + gm * R_L_eff)) + R_L_eff * (Cdb + Cgd)

# Tử số = c*s + d (Chứa điểm Zero)
c = -R_L_eff * Cgd
d = -gm * R_L_eff

# Tạo hàm truyền chính xác bậc 2
num_exact = [c, d]
den_exact = [a, b, 1]
sys_exact = signal.TransferFunction(num_exact, den_exact)


# 2b. TÍNH CÁC CỰC (POLES) CHÍNH XÁC TỪ ĐA THỨC BẬC 2

roots_s = np.roots([a, b, 1])          # nghiem cua a*s^2 + b*s + 1
f_poles_exact = np.sort(np.abs(roots_s.real) / (2 * np.pi))  # sap xep tang dan
f_H1_exact, f_H2_exact = f_poles_exact[0], f_poles_exact[1]


#   wP1 ~= 1/b            (cuc troi )
#   wP2 ~= b/a             (cuc phu )
f_H1_approx = 1 / (2 * np.pi * b)
f_H2_approx = b / (2 * np.pi * a)

print("\n--- CAC CUC (POLES) CUA MO HINH DAY DU ---")
print(f"Nghiem chinh xac (giai da thuc bac 2):")
print(f"  f_H1 (cuc troi) = {f_H1_exact/1e6:.4f} MHz")
print(f"  f_H2 (cuc phu)  = {f_H2_exact/1e6:.4f} MHz")
print(f"Xap xi tach cuc (giong cach lam cua Miller, 1/b va b/a):")
print(f"  f_H1_approx = {f_H1_approx/1e6:.4f} MHz")
print(f"  f_H2_approx = {f_H2_approx/1e6:.4f} MHz")
print(f"Sai so xap xi f_H1: {abs(f_H1_approx - f_H1_exact)/f_H1_exact*100:.2f} %")
print(f"Sai so xap xi f_H2: {abs(f_H2_approx - f_H2_exact)/f_H2_exact*100:.2f} %\n")


#AC swep
w = np.logspace(np.log10(f_start), np.log10(f_end), points) * 2 * np.pi
w, mag_exact, phase_exact = signal.bode(sys_exact, w)
f_vector = w / (2 * np.pi)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
ax1.semilogx(f_vector, mag_exact, 'r-', linewidth=2, label='complete Bậc 2')
ax1.axvline(f_H1_exact, color='b', linestyle='--', label=f'$f_{{H1}}$  = {f_H1_exact/1e6:.2f} MHz')
ax1.axvline(f_H2_exact, color='orange', linestyle='--', label=f'$f_{{H2}}$  = {f_H2_exact/1e6:.2f} MHz')
ax1.set_ylabel('Biên độ Av (dB)')
ax1.set_title('FREQ-RESPONSE MOSFET', fontsize=13, fontweight='bold')
ax1.grid(True, which="both", linestyle=':')
ax1.legend(fontsize=9)

ax2.semilogx(f_vector, phase_exact, 'g-', linewidth=2, label='complete Bậc 2')
ax2.axvline(f_H1_exact, color='b', linestyle='--')
ax2.axvline(f_H2_exact, color='orange', linestyle='--')
ax2.set_xlabel('Tần số (Hz) theo log')
ax2.set_ylabel('Pha (Độ)')
ax2.grid(True, which="both", linestyle=':')
ax2.legend(fontsize=9)

plt.tight_layout()
plt.show()