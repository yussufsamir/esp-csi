import serial
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import re
import time

# --- CONFIGURATION ---
PORT = "COM5"
BAUD = 921600
MAX_POINTS = 400
SUBCARRIER_INDEX = 150
USE_AVERAGE = True

# --- INITIALIZE SERIAL PORT ---
ser = serial.Serial(PORT, BAUD, timeout=1)
pattern = re.compile(r'\[(.*?)\]')

amplitude_buffer = deque(maxlen=MAX_POINTS)
time_buffer = deque(maxlen=MAX_POINTS)
std_buffer = deque(maxlen=MAX_POINTS)
start_time = time.time()

plt.ion()
fig, ax = plt.subplots(figsize=(10, 5))
(line_mean,) = ax.plot([], [], color="blue", linewidth=2, label="Mean Amplitude")
(line_std,) = ax.plot([], [], color="red", linewidth=1.5, linestyle="--", label="Std Deviation")
threshold_line = ax.axhline(y=0, color="green", linestyle="--", label="Dynamic Threshold")

ax.set_title("Real-Time CSI Amplitude & Standard Deviation (ESP32)")
ax.set_xlabel("Time (s)")
ax.set_ylabel("CSI Amplitude (a.u.)")
ax.legend()
plt.grid(True)

print("Listening for CSI_DATA...")

while True:
    try:
        raw = ser.readline().decode('utf-8', errors='ignore').strip()
        if "CSI_DATA" in raw:
            match = pattern.search(raw)
            if match:
                csi_str = match.group(1)
                csi_values = np.fromstring(csi_str, dtype=int, sep=',')

                if len(csi_values) == 0:
                    continue

                # Compute amplitude
                if USE_AVERAGE:
                    amplitude = float(np.mean(np.abs(csi_values)))
                else:
                    if SUBCARRIER_INDEX < len(csi_values):
                        amplitude = float(np.abs(csi_values[SUBCARRIER_INDEX]))
                    else:
                        continue

                # Append new data
                elapsed = time.time() - start_time
                amplitude_buffer.append(amplitude)
                time_buffer.append(elapsed)

                if len(amplitude_buffer) < 3:
                    continue  # wait for enough data points before plotting

                # Compute stats
                current_mean = np.mean(amplitude_buffer)
                current_std = np.std(amplitude_buffer)
                std_buffer.append(current_std)

                # Ensure all buffers have same length before plotting
                min_len = min(len(time_buffer), len(amplitude_buffer), len(std_buffer))
                times = list(time_buffer)[-min_len:]
                amplitudes = list(amplitude_buffer)[-min_len:]
                stds = list(std_buffer)[-min_len:]

                # Dynamic threshold (optional)
                threshold = current_mean + current_std
                threshold_line.set_ydata([threshold])

                # Update plots safely
                line_mean.set_data(times, amplitudes)
                line_std.set_data(times, stds)
                ax.relim()
                ax.autoscale_view()
                plt.pause(0.001)

                print(f"Mean: {current_mean:.2f} | Std: {current_std:.4f}")

    except KeyboardInterrupt:
        print("\nStopped by user.")
        break
    except Exception as e:
        print("Error:", e)
        continue

ser.close()
