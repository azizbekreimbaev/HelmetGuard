# HelmetGuard

Warehouse helmet monitoring prototype. Open this folder in VS Code.

## Dashboard

Run `streamlit run dashboard.py` and open http://localhost:8501.
The dashboard starts in dark mode; use **Dark mode** in the sidebar to
switch to light mode. Image, video, and camera workspaces share the same
responsive layout. Source controls sit above the result, with a two-column
metric grid, detection status, and legend beside the image or video on desktop.
On smaller screens the overview stacks below the result. Expand **Inspection
workflow** for guidance.

Browser review (with the dashboard already running):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe ui_review.py
```

The review saves screenshots and a result report under `ui-review/`.
It checks both themes at desktop, tablet, and phone widths, confidence
settings, sample inference, uploads, result tabs, image downloads,
video playback and stop, and camera connection controls. Physical camera
hardware and a valid remote stream require manual verification.

## Windows / Git Bash

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python main.py
```

PowerShell activation: `.venv\Scripts\Activate.ps1`.

## Required model

The model is NOT included. Put an Ultralytics-compatible object detection
checkpoint at `models/helmet.pt`. It must be trained for helmets AND explicit
bare heads/no-helmet detections. Generic COCO weights are insufficient.
The program prints model class names and accepts no-helmet labels such as
`NO-Hardhat`, `no_helmet`, or `without helmet`. Adjust the set in main.py
if your verified model uses another label. Review the model license before use.
Do not infer a violation simply because a helmet was not detected.

Camera index defaults to 0. Press Q to exit.

This prototype has not been validated on a warehouse camera. Occlusion,
small heads, lighting, and motion can cause missed or false detections.
Validate using labeled helmet/no-helmet footage and report precision, recall,
and FPS before making performance claims. It is not a certified safety system.
