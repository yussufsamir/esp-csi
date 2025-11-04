import re
import numpy as np
import matplotlib.pyplot as plt

# === CONFIG ===
CSI_FILE = "csi_data_log.txt"

# === PARSE FUNCTION ===
def parse_csi_line(line):
    if not line.startswith("CSI_DATA"):
        return None
    match = re.search(r'\[(.*?)\]', line)
    if not match:
        return None
    try:
        arr = [int(x.strip()) for x in match.group(1).split(",") if x.strip().lstrip("-").isdigit()]
        if arr:
            return np.mean(np.abs(arr))
    except Exception:
        return None
    return None

# === LOAD FILE ===
signal_values = []
with open(CSI_FILE, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        val = parse_csi_line(line)
        if val is not None:
            signal_values.append(val)

signal_values = np.array(signal_values)
print(f"Parsed {len(signal_values)} CSI samples.")

# === NORMALIZE ===
norm_signal = (signal_values - np.min(signal_values)) / (np.max(signal_values) - np.min(signal_values) + 1e-6)
smooth_signal = np.convolve(norm_signal, np.ones(5)/5, mode='same')

# === VISUALIZE ===
plt.figure(figsize=(10, 5))
plt.plot(smooth_signal * 8, 'b', label="WiFi Signal")
threshold = np.mean(smooth_signal) * 1.5
plt.axhline(threshold * 8, color='g', label="Threshold")
plt.fill_between(range(len(smooth_signal)), threshold*8, smooth_signal*8,
                 where=smooth_signal>threshold, color='orange', alpha=0.3, label="Activity")

plt.title("Human Activity Detection from CSI Data (Recorded)")
plt.xlabel("Time (samples)")
plt.ylabel("Normalized WiFi Signal Amplitude")
plt.legend(loc="upper right")
plt.grid(True)
plt.show()
