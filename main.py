"""FarmSense — student-built smart farm monitoring prototype.

Run locally with: streamlit run main.py

Important: sensor values in this prototype are simulated. NOAA forecast data is
fetched live when the NOAA weather API is reachable. Risk thresholds are demo
heuristics only, not validated agricultural or veterinary safety limits.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# -----------------------------------------------------------------------------
# App setup and styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="FarmSense | Smart Farm Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { --forest: #183f32; --leaf: #3b7959; --cream: #f5f6ef; }
      .stApp { background: #f7f8f3; color: #203b2e; }
      /* Explicit text colors prevent white-on-pale text if the viewer's
         Streamlit/browser theme is set to dark mode. */
      [data-testid="stAppViewContainer"],
      [data-testid="stAppViewContainer"] .stMarkdown,
      [data-testid="stAppViewContainer"] .stMarkdown p,
      [data-testid="stAppViewContainer"] label,
      [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
      [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] p,
      [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] p,
      [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] li {
        color: #203b2e;
      }
      [data-testid="stSidebar"] { background: #edf2e8; border-right: 1px solid #dbe3d5; color: #203b2e; }
      [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3,
      [data-testid="stSidebar"] p,
      [data-testid="stSidebar"] label,
      [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
      [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #183f32 !important;
      }
      [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #f7f8f3 !important;
      }
      [data-testid="stSidebar"] button p { color: #f7f8f3 !important; }
      .hero {
        padding: 1.35rem 1.55rem; border-radius: 18px;
        background: linear-gradient(120deg, #173f32 0%, #2d6849 68%, #6f965e 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 { color: white; margin: 0; font-size: 2.25rem; letter-spacing: -0.04em; }
      .hero p { color: #e7f0e5; margin: .45rem 0 0 0; font-size: 1rem; }
      .eyebrow { text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; font-weight: 700; opacity: .85; }
      .metric-card { padding: 1rem 1.05rem; background: white; border: 1px solid #e4e8de; border-radius: 15px; min-height: 130px; }
      .metric-label { color: #59685d; font-size: .86rem; margin-bottom: .35rem; }
      .metric-value { color: #183f32; font-size: 1.8rem; line-height: 1.2; font-weight: 750; }
      .metric-foot { color: #657269; font-size: .8rem; margin-top: .45rem; }
      .status { display: inline-block; padding: .28rem .65rem; border-radius: 999px; font-size: .76rem; font-weight: 750; }
      .green { color: #17633b; background: #e3f4e8; }
      .yellow { color: #855a00; background: #fff1c7; }
      .red { color: #9d2828; background: #fde6e3; }
      .gray { color: #4f5b54; background: #e8ece8; }
      .risk-card { border: 1px solid #e3e8df; background: white; padding: 1rem; border-radius: 14px; height: 100%; }
      .risk-title { font-size: 1.04rem; font-weight: 750; color: #183f32; margin-bottom: .45rem; }
      .small-muted { color: #68756b; font-size: .82rem; }
      .section-heading { color: #183f32; font-weight: 750; letter-spacing: -.015em; }
      div[data-testid="stAlert"] { border-radius: 12px; }
      .stButton button { border-radius: 10px; }
      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Farm / sensor simulation. These are not measurements from physical sensors.
# -----------------------------------------------------------------------------
LOCATION_OPTIONS = {
    "West Tennessee · Memphis area": (35.1495, -90.0490),
    "West Tennessee · Jackson area": (35.6145, -88.8139),
    "Middle Tennessee · Nashville area": (36.1627, -86.7816),
    "East Tennessee · Knoxville area": (35.9606, -83.9207),
}

SCENARIOS = [
    "Dry soil warning",
    "Balanced conditions",
    "Frost watch",
    "Barn heat stress indicator",
    "Barn air-quality alert",
]


def simulated_readings(scenario: str, field: str) -> dict[str, dict[str, Any]]:
    """Return illustrative readings for the selected training/demo scenario."""
    # Values are deliberately fixed for a repeatable video demonstration.
    field_values = {
        "field-north": {"soil_moisture": 38.0, "temperature_c": 19.0, "humidity": 62.0},
        "field-south": {"soil_moisture": 31.0, "temperature_c": 20.0, "humidity": 60.0},
    }
    barn = {"temperature_c": 24.0, "humidity": 67.0, "ammonia_ppm": 5.0}

    if scenario == "Dry soil warning":
        field_values["field-north"].update(soil_moisture=16.0, temperature_c=25.0, humidity=48.0)
        field_values["field-south"].update(soil_moisture=23.0, temperature_c=25.0, humidity=47.0)
    elif scenario == "Frost watch":
        field_values["field-north"].update(soil_moisture=29.0, temperature_c=1.5, humidity=78.0)
        field_values["field-south"].update(soil_moisture=33.0, temperature_c=2.0, humidity=79.0)
    elif scenario == "Barn heat stress indicator":
        barn.update(temperature_c=33.0, humidity=86.0, ammonia_ppm=7.0)
    elif scenario == "Barn air-quality alert":
        barn.update(temperature_c=25.0, humidity=73.0, ammonia_ppm=22.0)

    # Small visual variations make the historical demo chart look realistic,
    # while keeping the selected scenario itself stable and repeatable.
    rng = random.Random(f"{scenario}-{field}-farmsense")
    out = {}
    for sensor_id, values in field_values.items():
        out[sensor_id] = {
            "sensor_id": sensor_id,
            "kind": "soil",
            **values,
            "reading_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    out["barn-1"] = {
        "sensor_id": "barn-1",
        "kind": "barn",
        **barn,
        "reading_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    # Keep rng referenced to make the deterministic variation seed explicit;
    # it is used for the history chart further below.
    _ = rng
    return out


def assess_soil(reading: dict[str, Any]) -> dict[str, str]:
    """Demo-only soil rules. Replace with locally validated crop guidance."""
    moisture = reading.get("soil_moisture")
    temp_c = reading.get("temperature_c")
    if moisture is None or temp_c is None:
        return {"level": "gray", "label": "NO DATA", "message": "A sensor value is missing. Check the sensor connection before making a decision."}
    if temp_c <= 0:
        return {"level": "red", "label": "HIGH RISK", "message": "Air/soil temperature is at or below 0°C in this demo. Check a local forecast and protect frost-sensitive crops as appropriate."}
    if temp_c <= 3:
        return {"level": "yellow", "label": "WATCH", "message": "Temperature is close to freezing in this demo. Review crop-specific frost guidance and the local forecast."}
    if moisture <= 20:
        return {"level": "red", "label": "HIGH RISK", "message": "Demo rule: soil moisture is low. Check the field and irrigation system before deciding whether to water."}
    if moisture <= 30:
        return {"level": "yellow", "label": "WATCH", "message": "Demo rule: soil moisture is trending low. Recheck the sensor and consider crop stage, soil type, and recent rain."}
    return {"level": "green", "label": "LOW RISK", "message": "No demo rule was triggered. Continue monitoring and compare the reading with crop-specific targets."}


def assess_barn(reading: dict[str, Any]) -> dict[str, str]:
    """Demo-only barn screening rules, not veterinary safety standards."""
    temp_c = reading.get("temperature_c")
    humidity = reading.get("humidity")
    ammonia = reading.get("ammonia_ppm")
    if temp_c is None or humidity is None or ammonia is None:
        return {"level": "gray", "label": "NO DATA", "message": "A barn sensor value is missing. Check the sensor and confirm conditions in person."}
    if ammonia >= 20:
        return {"level": "red", "label": "HIGH RISK", "message": "Demo rule: ammonia reading is elevated. Verify the reading promptly, increase appropriate ventilation if safe, and consult species-specific guidance."}
    if temp_c >= 32 and humidity >= 80:
        return {"level": "red", "label": "HIGH RISK", "message": "Demo rule: temperature and humidity are both elevated. Check animals and the barn environment promptly; use a veterinarian's guidance."}
    if temp_c >= 29 or humidity >= 80 or ammonia >= 10:
        return {"level": "yellow", "label": "WATCH", "message": "Demo rule: one or more barn readings are elevated. Recheck sensors, airflow, water access, and species-specific recommendations."}
    return {"level": "green", "label": "LOW RISK", "message": "No demo rule was triggered. Continue routine observation and compare conditions with veterinary guidance for the species."}


def severity_class(level: str) -> str:
    return {"green": "green", "yellow": "yellow", "red": "red"}.get(level, "gray")


def show_risk_badge(risk: dict[str, str]) -> str:
    return f'<span class="status {severity_class(risk["level"])}">{risk["label"]}</span>'


# -----------------------------------------------------------------------------
# NOAA forecast lookup. If the API is unavailable, the app will still work.
# -----------------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)
def get_noaa_weather(lat: float, lon: float) -> dict[str, Any]:
    """Fetch a public NOAA forecast and active alerts for US coordinates."""
    headers = {
        "User-Agent": "FarmSense-Student-CAC-Demo/1.0",
        "Accept": "application/geo+json",
    }
    response = requests.get(
        f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}",
        headers=headers,
        timeout=12,
    )
    response.raise_for_status()
    properties = response.json().get("properties", {})
    forecast_url = properties.get("forecast")
    if not forecast_url:
        raise ValueError("NOAA did not return a forecast endpoint for this location.")

    forecast_response = requests.get(forecast_url, headers=headers, timeout=12)
    forecast_response.raise_for_status()
    periods = forecast_response.json().get("properties", {}).get("periods", [])

    alerts: list[dict[str, str]] = []
    try:
        alert_response = requests.get(
            f"https://api.weather.gov/alerts/active?point={lat:.4f},{lon:.4f}",
            headers=headers,
            timeout=12,
        )
        alert_response.raise_for_status()
        for feature in alert_response.json().get("features", [])[:5]:
            p = feature.get("properties", {})
            alerts.append({
                "event": str(p.get("event") or "Weather alert"),
                "severity": str(p.get("severity") or "Unknown"),
                "headline": str(p.get("headline") or p.get("description") or "See official NOAA details")[:260],
            })
    except (requests.RequestException, ValueError, TypeError):
        # Forecast display should still be usable if the separate alerts endpoint fails.
        alerts = []

    return {"periods": periods[:8], "alerts": alerts, "source": "NOAA / National Weather Service"}


def build_history(sensor_id: str, current: dict[str, Any], scenario: str) -> pd.DataFrame:
    """Make illustrative 24-hour values that lead toward the current demo reading."""
    rng = random.Random(f"history-{sensor_id}-{scenario}")
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    rows: list[dict[str, Any]] = []
    if sensor_id.startswith("field"):
        target = float(current["soil_moisture"])
        start = min(75.0, max(35.0, target + (18.0 if scenario == "Dry soil warning" else 3.0)))
        for i in range(24):
            progress = i / 23
            value = start + (target - start) * progress + rng.uniform(-1.8, 1.8)
            rows.append({"Time": now - timedelta(hours=23 - i), "Soil moisture (%)": round(max(0, min(100, value)), 1)})
        return pd.DataFrame(rows)

    target = float(current["ammonia_ppm"])
    start = min(16.0, max(3.0, target - 5.0)) if scenario != "Barn air-quality alert" else 8.0
    for i in range(24):
        progress = i / 23
        value = start + (target - start) * progress + rng.uniform(-0.45, 0.45)
        rows.append({"Time": now - timedelta(hours=23 - i), "Ammonia (ppm) · demo": round(max(0, value), 1)})
    return pd.DataFrame(rows)


def metric_card(label: str, value: str, foot: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-foot">{foot}</div></div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Sidebar controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("# 🌱 FarmSense")
    st.caption("Practical monitoring for small and mid-sized farms")
    st.divider()
    st.markdown("### Demo controls")
    location_label = st.selectbox("Weather location", list(LOCATION_OPTIONS.keys()), index=0)
    scenario = st.selectbox("Sensor demo scenario", SCENARIOS, index=0)
    field = st.selectbox("Field to inspect", ["field-north", "field-south"], format_func=lambda x: "North field" if x == "field-north" else "South field")
    st.button("Refresh dashboard", use_container_width=True, on_click=lambda: st.cache_data.clear())
    st.divider()
    st.markdown("### Data source")
    st.markdown("**Sensors:** simulated demo readings")
    st.markdown("**Weather:** NOAA live forecast when available")
    st.caption("This prototype is for demonstration, not automated farm control or emergency decision-making.")


readings = simulated_readings(scenario, field)
soil_reading = readings[field]
barn_reading = readings["barn-1"]
soil_risk = assess_soil(soil_reading)
barn_risk = assess_barn(barn_reading)
lat, lon = LOCATION_OPTIONS[location_label]

# Header
st.markdown(
    f"""
    <div class="hero">
      <div class="eyebrow">Farm intelligence · Tennessee prototype</div>
      <h1>FarmSense Dashboard</h1>
      <p>Know what is happening across your fields and barns before small changes become bigger problems.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

head_left, head_right = st.columns([3, 1])
with head_left:
    st.markdown(f"**Weather area:** {location_label}")
with head_right:
    st.markdown(f"<div style='text-align:right' class='small-muted'>Demo updated {datetime.now().strftime('%I:%M %p')}</div>", unsafe_allow_html=True)

# Metric row
moisture = soil_reading["soil_moisture"]
soil_temp = soil_reading["temperature_c"]
barn_temp = barn_reading["temperature_c"]
ammonia = barn_reading["ammonia_ppm"]

cols = st.columns(4, gap="medium")
with cols[0]:
    metric_card("Soil moisture", f"{moisture:.1f}%", "Simulated · selected field")
with cols[1]:
    metric_card("Field temperature", f"{soil_temp:.1f}°C", "Simulated sensor reading")
with cols[2]:
    metric_card("Barn temperature", f"{barn_temp:.1f}°C", "Simulated sensor reading")
with cols[3]:
    metric_card("Barn ammonia", f"{ammonia:.1f} ppm", "Simulated sensor reading")

st.markdown("## Farm status")
status_cols = st.columns(3, gap="medium")
with status_cols[0]:
    st.markdown(
        f'<div class="risk-card"><div class="risk-title">🌿 Soil health · {"North field" if field == "field-north" else "South field"}</div>'
        f'{show_risk_badge(soil_risk)}<p>{soil_risk["message"]}</p>'
        '<div class="small-muted">Based on demo-only soil moisture and temperature rules.</div></div>',
        unsafe_allow_html=True,
    )
with status_cols[1]:
    st.markdown(
        f'<div class="risk-card"><div class="risk-title">🐄 Livestock environment</div>'
        f'{show_risk_badge(barn_risk)}<p>{barn_risk["message"]}</p>'
        '<div class="small-muted">Demo screening only; it does not determine whether a barn is safe.</div></div>',
        unsafe_allow_html=True,
    )
with status_cols[2]:
    st.markdown(
        '<div class="risk-card"><div class="risk-title">🌦️ Weather & risk</div>'
        '<span class="status gray">FORECAST CHECK</span>'
        '<p>Check the local forecast and official alerts for possible frost, storms, and heavy rain. Crop-specific drought prediction is not implemented in this prototype.</p>'
        '<div class="small-muted">NOAA forecast where available.</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("## Trends across the farm")
chart_col, guide_col = st.columns([1.6, 1], gap="large")
with chart_col:
    tab_soil, tab_barn = st.tabs(["Soil moisture · 24 hours", "Barn air quality · 24 hours"])
    with tab_soil:
        soil_history = build_history(field, soil_reading, scenario)
        fig_soil = px.line(soil_history, x="Time", y="Soil moisture (%)", markers=True)
        fig_soil.update_layout(height=315, margin=dict(l=8, r=8, t=18, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="Moisture (%)", showlegend=False)
        fig_soil.update_traces(line=dict(color="#367954", width=3), marker=dict(size=4))
        st.plotly_chart(fig_soil, use_container_width=True)
        st.caption("Illustrative 24-hour trend generated for the selected scenario, not recorded field history.")
    with tab_barn:
        barn_history = build_history("barn-1", barn_reading, scenario)
        y_col = "Ammonia (ppm) · demo"
        fig_barn = px.line(barn_history, x="Time", y=y_col, markers=True)
        fig_barn.update_layout(height=315, margin=dict(l=8, r=8, t=18, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="Ammonia (ppm)", showlegend=False)
        fig_barn.update_traces(line=dict(color="#b47a2d", width=3), marker=dict(size=4))
        st.plotly_chart(fig_barn, use_container_width=True)
        st.caption("Illustrative trend generated for the selected scenario, not recorded barn history.")

with guide_col:
    st.markdown("### FarmSense recommendations")
    if soil_risk["level"] == "red":
        st.error("**Soil check:** Verify the moisture/temperature reading and inspect the field. Follow local crop and weather guidance before irrigation or frost protection.")
    elif soil_risk["level"] == "yellow":
        st.warning("**Soil check:** Recheck the sensor, review recent rain, and compare the reading with requirements for the crop and soil type.")
    else:
        st.success("**Soil check:** Continue monitoring and compare readings with crop-specific targets.")

    if barn_risk["level"] == "red":
        st.error("**Barn check:** Confirm readings promptly, check ventilation and animals in person, and contact a veterinarian or appropriate farm professional when needed.")
    elif barn_risk["level"] == "yellow":
        st.warning("**Barn check:** Recheck sensors, airflow, water availability, and species-specific recommendations.")
    else:
        st.success("**Barn check:** Continue routine animal observation and monitoring.")

    st.info("**Important:** Recommendations are explanatory demo messages. This version does not operate irrigation, vents, or other farm equipment.")

st.markdown("## Local weather outlook")
st.write("FarmSense checks the National Weather Service forecast for the selected Tennessee area. Forecast data is not a substitute for on-farm sensors or official emergency instructions.")
with st.spinner("Checking NOAA forecast…"):
    try:
        weather = get_noaa_weather(lat, lon)
        periods = weather.get("periods", [])
        if periods:
            weather_cols = st.columns(min(4, len(periods)), gap="medium")
            for idx, period in enumerate(periods[:4]):
                with weather_cols[idx]:
                    temp = period.get("temperature", "—")
                    unit = period.get("temperatureUnit", "F")
                    pop = period.get("probabilityOfPrecipitation", {}).get("value")
                    pop_text = f"{pop}% chance of precipitation" if pop is not None else "Precipitation chance unavailable"
                    detail = str(period.get("detailedForecast") or period.get("shortForecast") or "Forecast details unavailable")
                    st.markdown(
                        f'<div class="risk-card"><div class="risk-title">{period.get("name", "Forecast period")}</div>'
                        f'<div class="metric-value">{temp}°{unit}</div><p>{period.get("shortForecast", "Forecast")}</p>'
                        f'<div class="small-muted">{pop_text}</div></div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander("Forecast details"):
                        st.write(detail)
        else:
            st.warning("NOAA did not return forecast periods for this point. Use the official forecast link below.")
        alerts = weather.get("alerts", [])
        if alerts:
            st.markdown("### Active weather alerts for this area")
            for alert in alerts:
                st.warning(f"**{alert['event']} · {alert['severity']}**\n\n{alert['headline']}")
        else:
            st.success("No active alerts were returned by the NOAA alerts endpoint for the selected point, or that endpoint was temporarily unavailable. Check the official source before making decisions.")
        st.markdown("Source: [National Weather Service / NOAA](https://www.weather.gov/)")
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        st.warning("Live NOAA data could not be loaded right now. The rest of the demo still works. Check your internet connection and try again.")
        st.caption(f"Technical detail for debugging: {type(exc).__name__}")
        st.markdown("Official forecast: [weather.gov](https://www.weather.gov/)")

with st.expander("About this prototype, thresholds, and limitations"):
    st.markdown(
        """
        - **Simulated readings:** Every soil and barn sensor number and its history chart is generated for this demonstration. No physical sensors are connected.
        - **Weather data:** The app attempts to fetch forecast periods and active alerts from the public National Weather Service API. If it cannot connect, the dashboard remains usable.
        - **Rule-based risk flags:** The green/yellow/red logic uses illustrative thresholds so a judge can see how alerts respond to conditions. These are **not validated crop, livestock, or occupational exposure limits**.
        - **No autonomous controls:** This version does not activate irrigation, fans, vents, or SMS notifications.
        - **Before real farm use:** Work with local agricultural extension specialists and veterinarians to select thresholds for crop type, growth stage, animal species, sensors, and local conditions. Validate sensor calibration and false alarms.
        """
    )

st.divider()
st.caption("FarmSense · Congressional App Challenge prototype · Built with Python and Streamlit · Sensor data shown here is simulated")
