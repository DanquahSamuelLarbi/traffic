# SmartLight MVP — Adaptive Traffic Light Optimization System

A real-time adaptive traffic signal control system built with **SUMO**, **TraCI**, **YOLOv8**, and **OpenCV**. The system replaces fixed-timer traffic lights with a demand-weighted queue algorithm that dynamically switches green phases based on actual vehicle density.

## Results

Benchmarked against a standard fixed-timer controller using identical traffic demand:

| Metric | Fixed-Timer | SmartLight | Change |
|---|---|---|---|
| Vehicles Completed | 402 | 463 | **+15.2%** |
| Avg. Travel Time | 87.45s | 56.73s | **−35.1%** |
| Avg. Waiting Time | 42.56s | 12.32s | **−71.1%** |
| Total Waiting Time | 17,109s | 5,703s | **−66.7%** |

![Benchmark Results](benchmark_results.png)

---

## Project Structure

```
traffic/
├── cv_detector.py              # YOLOv8 + OpenCV lane vehicle counter
├── smart_light_control.py      # TraCI adaptive traffic light controller
├── benchmark.py                # Static vs SmartLight KPI comparison
├── requirements.txt            # Python dependencies
├── benchmark_results.png       # Performance comparison chart
├── benchmark_report.md         # Auto-generated KPI report
└── simulation/
    ├── intersection.nod.xml    # SUMO node definitions
    ├── intersection.edg.xml    # SUMO edge definitions
    ├── intersection.con.xml    # SUMO connection rules
    ├── intersection.net.xml    # Compiled SUMO road network
    ├── intersection.rou.xml    # Vehicle routes & traffic flows
    ├── intersection.sumocfg    # SUMO master config
    ├── tripinfo_static.xml     # Simulation output (fixed-timer)
    └── tripinfo_smart.xml      # Simulation output (SmartLight)
```

---

## Prerequisites

### 1. Install SUMO
Download and install from: https://sumo.dlr.de/docs/Downloads.php  
Default install path: `C:\Program Files (x86)\Eclipse\Sumo`

### 2. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Download YOLOv8 Model
The model weights (`yolov8n.pt`) are downloaded automatically on first run of `cv_detector.py`.  
Or manually:
```python
from ultralytics import YOLO
YOLO("yolov8n.pt")
```

---

## Usage

### CV Vehicle Detection (on a recorded video)
```powershell
# With live preview window
python cv_detector.py --input your_traffic_video.mp4

# Headless (faster — saves to processed_traffic.mp4)
python cv_detector.py --input your_traffic_video.mp4 --no-display
```

### Run the Full Benchmark (Static vs SmartLight)
```powershell
python benchmark.py
```
Outputs: `benchmark_results.png` + `benchmark_report.md`

### Run SmartLight Simulation Alone
```powershell
# Headless
python smart_light_control.py --sumocfg simulation/intersection.sumocfg

# With SUMO GUI
python smart_light_control.py --sumocfg simulation/intersection.sumocfg --gui
```

---

## Algorithm — How It Works

Every simulation second, the controller:

1. **Computes a weighted queue score** for each direction (NS and EW):
   - Bus / Truck = **2.0** weight (high priority)
   - Car = **1.0** weight
   - Motorcycle = **0.5** weight
   - Only counts vehicles with speed < 1.0 m/s (queued)

2. **Decides whether to switch** the green phase:
   - Minimum green guard: **15 seconds** (prevents rapid flickering)
   - If opposing direction weight exceeds current by **> 3.0** → switch
   - Maximum green cap: **60 seconds** (fairness guarantee)

3. **Executes a 4-second yellow** transition before switching green phase

---

## Technologies

- **SUMO** — Traffic simulation engine
- **TraCI** — Python API for real-time SUMO control
- **YOLOv8 (Ultralytics)** — Pre-trained object detection model
- **OpenCV** — Video processing and ROI polygon testing
- **Python 3** — All logic, control, and analysis
- **Matplotlib / NumPy** — Benchmarking charts and statistics
