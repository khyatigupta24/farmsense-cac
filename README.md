# FarmSense — Python prototype for the Congressional App Challenge

FarmSense is a student-built prototype for small and mid-sized farms. It brings simulated soil and barn sensor readings, simple rule-based alerts, trends, and a live NOAA/National Weather Service forecast into one dashboard.

## What currently works

- Three dashboard modules: Soil Health, Livestock Environment, and Weather & Risk.
- Repeatable demo scenarios (dry soil, balanced conditions, frost watch, barn heat indicator, and barn air-quality alert).
- Color-coded risk flags and explanatory recommendations.
- Illustrative 24-hour soil moisture and barn ammonia charts.
- NOAA forecast periods and active weather alerts when the public API is available.
- A fallback message if the live forecast cannot be reached.

## Important limitations

- Soil and barn sensor values are simulated; the app is not connected to real hardware.
- Historical sensor charts are illustrative, not actual recorded farm history.
- Green/yellow/red thresholds are demonstration heuristics, not validated agronomic, veterinary, or occupational safety standards.
- No hardware is controlled and no SMS messages are sent.
- The prototype is not for emergency or real-world safety decisions.

## Run locally (Mac / VS Code)

1. Install a current, stable Python version that the packages support. Python 3.12 is a conservative choice for a new project.
2. Download and unzip this project folder.
3. Open VS Code. Choose **File → Open Folder…** and select the unzipped `farmsense_fresh` folder.
4. Open **Terminal → New Terminal** in VS Code.
5. Create a virtual environment:

   ```bash
   python3.12 -m venv .venv
   ```

6. Activate it:

   ```bash
   source .venv/bin/activate
   ```

7. Install the packages:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

8. Start the app:

   ```bash
   python -m streamlit run main.py
   ```

9. Streamlit should open a browser tab. If it does not, copy the local address printed in Terminal (usually `http://localhost:8501`) into your browser.
10. Use **Demo controls → Sensor demo scenario** to show different conditions. Use **Refresh dashboard** to retry NOAA data and refresh the page.

### If `python3.12` is not found

That means Python 3.12 may not be installed or your terminal uses a different command. Check with `python3 --version`. Install Python 3.12 from python.org, then close/reopen VS Code and retry. Do not delete another working Python installation.

### If a command fails

Copy the full error from Terminal and share it. Do not share passwords, private access tokens, or secret API keys.

## Publish a demo website for the video

The simplest beginner-friendly route is GitHub + Streamlit Community Cloud:

1. Sign in to GitHub and create a new repository named `farmsense-cac`. For the simplest first deployment, choose **Public** (the source code will be visible to others, so do not put secrets or personal information in it).
2. Upload the contents of this folder to the repository root. Upload `main.py`, `requirements.txt`, `README.md`, `.gitignore`, and the `.streamlit` folder. Do not upload `.venv` or `__pycache__`.
3. Open `https://share.streamlit.io/` and sign in using GitHub.
4. Select **Create app**, select your repository and branch (`main`), and set **Main file path** to `main.py`.
5. In advanced settings, choose Python 3.12 if offered, then deploy.
6. When it finishes, copy the `https://....streamlit.app` URL. Open that URL in a private/incognito window to make sure the public demo loads before recording.

Official instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Suggested video demo sequence (about 90 seconds)

1. **0–10 sec:** Introduce FarmSense and the problem small farms face when field or barn conditions change unexpectedly.
2. **10–25 sec:** Show the overview cards and point out that this version uses simulated sensor readings for the prototype.
3. **25–40 sec:** Select **Dry soil warning** and explain how the soil status changes and why the recommendation appears.
4. **40–55 sec:** Select **Frost watch**, then show the temperature and risk message.
5. **55–70 sec:** Select **Barn air-quality alert** and show the barn risk response.
6. **70–82 sec:** Scroll to the NOAA outlook and show the forecast / active-alert display if available.
7. **82–90 sec:** Explain next steps: connect hardware, validate thresholds with agricultural and veterinary experts, add SMS, and only then consider safe, supervised automation.

## Suggested project explanation

- `main.py`: the dashboard, demo sensor data, risk rules, charts, and NOAA requests.
- `requirements.txt`: the external Python packages to install.
- `.streamlit/config.toml`: colors and server settings for the Streamlit app.
- `.gitignore`: keeps generated Python cache, local environments, and secrets out of GitHub.
