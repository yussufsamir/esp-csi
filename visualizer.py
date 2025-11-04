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
start_time = time.time()

plt.ion()
fig, ax = plt.subplots(figsize=(10, 5))
(line,) = ax.plot([], [], color="blue", linewidth=2)
threshold_line = ax.axhline(y=0, color="green", linestyle="--")
ax.set_title("Real-Time CSI Amplitude (ESP32)")
ax.set_xlabel("Time (s)")
ax.set_ylabel("CSI Amplitude (a.u.)")
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
                    continue  # skip empty frames

                # Compute amplitude
                if USE_AVERAGE:
                    amplitude = float(np.mean(np.abs(csi_values)))
                else:
                    if SUBCARRIER_INDEX < len(csi_values):
                        amplitude = float(np.abs(csi_values[SUBCARRIER_INDEX]))
                    else:
                        continue

                # Append time and amplitude
                elapsed = time.time() - start_time
                amplitude_buffer.append(amplitude)
                time_buffer.append(elapsed)

                if len(amplitude_buffer) < 2:
                    continue  # wait until we have enough data

                # Compute dynamic threshold
                threshold = np.mean(amplitude_buffer) + np.std(amplitude_buffer)
                threshold_line.set_ydata([threshold])

                # Update line data
                line.set_data(list(time_buffer), list(amplitude_buffer))
                ax.relim()
                ax.autoscale_view()
                plt.pause(0.001)

    except KeyboardInterrupt:
        print("\nStopped by user.")
        break
    except Exception as e:
        print("Error:", e)
        continue

ser.close()
