import csv
import serial
import matplotlib.pyplot as plt

PORT = "COM6"
BAUD_RATE = 115200
LOG_FILE = "sensor_log.csv"
MAX_POINTS = 100

times = []
temperatures = []
setpoints = []
lights = []
start_timestamp_ms = None
previous_timestamp_ms = None

plt.ion()

fig, (ax_temp, ax_light) = plt.subplots(2, 1, sharex=True)

temperature_line, = ax_temp.plot([], [], color="red", label="Filtered temperature")
setpoint_line, = ax_temp.plot([], [], color="blue", label="Filtered setpoint")
light_line, = ax_light.plot([], [], color="orange", label="Filtered light")

ax_temp.set_title("Live Sensor Dashboard")
ax_temp.set_ylabel("Temperature (C)")
ax_temp.grid(True)
ax_temp.legend()

stats_text = ax_temp.text(
    0.02,
    0.98,
    "",
    transform=ax_temp.transAxes,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
)

ax_light.set_xlabel("Time since start (s)")
ax_light.set_ylabel("Light level (0-4095)")
ax_light.grid(True)
ax_light.legend()

fig.tight_layout()

plt.show(block=False)

try:
    with open(LOG_FILE, "w", newline="") as log_file:
        writer = csv.writer(log_file)

        writer.writerow([
            "timestamp_ms",
            "temp_raw_c",
            "temp_filtered_c",
            "light_raw",
            "light_filtered",
            "setpoint_raw_c",
            "setpoint_filtered_c"
        ])

        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print("Connected to", PORT)
            print("Logging data to", LOG_FILE)

            while True:
                line = ser.readline().decode("utf-8", errors="replace").strip()

                if not line:
                    continue

                if line.startswith("timestamp_ms"):
                    continue

                parts = line.split(",")

                if len(parts) != 7:
                    print("Skipped bad row:", line)
                    continue

                try:
                    timestamp_ms = int(parts[0])
                    temperature_c = float(parts[1])
                    temperature_filtered_c = float(parts[2])
                    light_raw = int(parts[3])
                    light_filtered = int(parts[4])
                    setpoint_c = float(parts[5])
                    setpoint_filtered_c = float(parts[6])
                except ValueError:
                    print("Skipped bad row:", line)
                    continue

                writer.writerow([
                    timestamp_ms,
                    temperature_c,
                    temperature_filtered_c,
                    light_raw,
                    light_filtered,
                    setpoint_c,
                    setpoint_filtered_c
                ])

                log_file.flush()

                if start_timestamp_ms is None:
                    start_timestamp_ms = timestamp_ms

                time_s = (timestamp_ms - start_timestamp_ms) / 1000.0

                times.append(time_s)
                temperatures.append(temperature_filtered_c)
                setpoints.append(setpoint_filtered_c)
                lights.append(light_filtered)

                if len(times) > MAX_POINTS:
                    times.pop(0)
                    temperatures.pop(0)
                    setpoints.pop(0)
                    lights.pop(0)

                min_temp = min(temperatures)
                max_temp = max(temperatures)
                average_temp = sum(temperatures) / len(temperatures)

                if previous_timestamp_ms is None:
                    rate_text = "Rate: waiting..."
                else:
                    interval_ms = timestamp_ms - previous_timestamp_ms

                    if interval_ms <= 500:
                        rate_text = "Rate: Fast (250 ms)"
                    elif interval_ms <= 1500:
                        rate_text = "Rate: Medium (1000 ms)"
                    else:
                        rate_text = "Rate: Slow (2000 ms)"

                previous_timestamp_ms = timestamp_ms

                stats_text.set_text(
                    f"Current: {temperature_filtered_c:.1f} C\n"
                    f"Min: {min_temp:.1f} C\n"
                    f"Max: {max_temp:.1f} C\n"
                    f"Average: {average_temp:.1f} C\n"
                    f"{rate_text}"
                )

                temperature_line.set_data(times, temperatures)
                setpoint_line.set_data(times, setpoints)
                light_line.set_data(times, lights)

                ax_temp.relim()
                ax_temp.autoscale_view()

                ax_light.relim()
                ax_light.autoscale_view()

                plt.pause(0.01)

except serial.SerialException as error:
    print("Could not open serial port:", error)

except KeyboardInterrupt:
    print("\nStopped by user")