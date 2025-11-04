import re
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
from matplotlib.animation import FuncAnimation
import threading
import time
import os

# ==============================
# CONFIGURATION
# ==============================
FILE_PATH = "D:\\ESP32\\esp-csi\\examples\\get-started\\csi_recv\\csi_stream.txt"        # Path to your recorded CSI log
WINDOW_SIZE = 300                # Number of samples visible in window
THRESHOLD_SCALE = 1.5            # Sensitivity multiplier (higher = less sensitive)
REFRESH_INTERVAL = 100           # ms between plot updates
READ_DELAY = 0.02                # seconds between reading lines (simulated real time)

# ==============================
# SHARED DATA
# ==============================
signal_window = deque(maxlen=WINDOW_SIZE)
data_lock = threading.Lock()
running = True


# ==============================
# PARSER FUNCTION
# ==============================
def parse_csi_line(line):
    """Extract average CSI amplitude from a CSI_DATA line"""
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


# ==============================
# FILE READER THREAD
# ==============================
def file_reader():
    global running
    if not os.path.exists(FILE_PATH):
        print(f"❌ File not found: {FILE_PATH}")
        running = False
        return

    print(f"📄 Replaying CSI data from {FILE_PATH}")
    with open(FILE_PATH, "r") as f:
        for line in f:
            if not running:
                break
            value = parse_csi_line(line)
            if value is not None:
                with data_lock:
                    signal_window.append(value)
            time.sleep(READ_DELAY)  # simulate real-time feed


# ==============================
# PLOT SETUP
# ==============================
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 5))
line_signal, = ax.plot([], [], 'b', label='WiFi Signal')
line_threshold, = ax.plot([], [], 'g', label='Threshold')
fill_activity = None
ax.set_xlabel("Time (samples)")
ax.set_ylabel("Normalized WiFi Signal Amplitude")
ax.set_title("Human Activity Detection from CSI (File Replay)")
ax.legend(loc='upper right')
ax.set_xlim(0, WINDOW_SIZE)
ax.set_ylim(0, 10)


# ==============================
# UPDATE FUNCTION (ANIMATION)
# ==============================
def update(frame):
    global fill_activity
    with data_lock:
        if len(signal_window) == 0:
            return line_signal, line_threshold

        signal = np.array(signal_window)
        signal = (signal - np.min(signal)) / (np.max(signal) - np.min(signal) + 1e-6)
        smoothed = np.convolve(signal, np.ones(5)/5, mode='same')
        threshold = np.mean(smoothed) * THRESHOLD_SCALE

        # Remove old fill
        if fill_activity:
            fill_activity.remove()

        # Highlight motion regions
        motion_mask = smoothed > threshold
        fill_activity = ax.fill_between(
            range(len(smoothed)),
            0, smoothed * 8,
            where=motion_mask,
            color='orange', alpha=0.3, label='Activity'
        )

        line_signal.set_data(range(len(smoothed)), smoothed * 8)
        line_threshold.set_data(range(len(smoothed)), np.ones_like(smoothed) * threshold * 8)

    return line_signal, line_threshold, fill_activity


# ==============================
# START THREAD & RUN ANIMATION
# ==============================
reader_thread = threading.Thread(target=file_reader, daemon=True)
reader_thread.start()

ani = FuncAnimation(fig, update, interval=REFRESH_INTERVAL, blit=False, cache_frame_data=False)

try:
    plt.tight_layout()
    plt.show()
finally:
    running = False
    reader_thread.join(timeout=1)
    print("🛑 Visualization stopped.")
