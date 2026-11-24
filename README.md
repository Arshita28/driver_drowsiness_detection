# Driver Drowsiness Detection

This team project includes the original Python desktop detector and a browser-based DriveAware dashboard.

## Run the website

1. Clone or download this repository and open it in VS Code.
2. Install Node.js LTS from https://nodejs.org/.
3. Open a terminal and run:

```sh
cd website
node server.cjs
```

4. Open http://localhost:8000 in Chrome or Edge.
5. Click **Start webcam** and allow camera access.

No npm install or Python packages are required for the website. Internet is needed to load MediaPipe and its model. Camera frames are processed in the browser and are not uploaded.

Alternatively, with Python installed, run `python -m http.server 8000 --directory website` from the repository root.

The dark dashboard includes live eye and mouth ratios, adjustable thresholds, and a loud repeating alarm. The alarm triggers after 50 consecutive frames below the eye threshold or 15 above the mouth threshold. It stops when the triggering conditions clear, monitoring stops, or sound is disabled. Sound is enabled by default and device volume controls actual loudness.

## Run the original Python detector

The Python scripts, model, audio, images, and cascades remain in the repository root. Run from the root so relative paths resolve. The desktop application uses OpenCV and dlib; the browser adaptation uses MediaPipe. The website does not execute the Python application.

## Deploy to Render

Create a **Static Site** connected to this repository:

- Build command: `echo "Static site ready"`
- Publish directory: `website`

Or use the included `render.yaml` Blueprint. Render provides an HTTPS address needed for webcam access on a public website. Uploading files to GitHub alone does not publish a running website.

## Limitations

This is a college project prototype, not a certified driving safety system. Lighting, glasses, head angle, camera frame rate, and individual facial differences can affect detection. Thresholds may require adjustment.
