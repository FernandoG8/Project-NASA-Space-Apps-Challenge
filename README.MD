# 🌦️ Climate Analysis API (NASA POWER / MERRA-2)

## 📘 Overview

This project provides a **FastAPI-based climate analysis API** that retrieves and analyzes historical environmental data (temperature, precipitation, humidity, and windspeed) from NASA POWER.  
It estimates **empirical probabilities** for specific climate conditions (e.g., *very wet*, *very hot*) based on long-term historical distributions — not deterministic weather forecasts.

---

## ⚙️ Features

- Query any geographic coordinate (lat/lon)
- Analyze a specific day or a short time window across multiple years
- Retrieve CSV datasets or PNG trend plots
- Compute percentile-based probability classifications
- Validate user inputs (lat/lon, dates, leap years, etc.)
- Designed with modular architecture: routers, schemas, services, datasources, utils

---

## 🧩 Requirements

- **Python 3.12+**
- **pip** (latest version)
- (optional) **virtualenv** or **venv**
- **Git** (to clone the repository)

---

## 🛠️ Installation

### 1. Clone the repository

```bash
cd campeche_weather
https://github.com/FernandoG8/Project-NASA-Space-Apps-Challenge.git
```

## 2. Create environment 
---

###  On Linux / macOS / WSL

```bash
# Create a virtual environment inside the project folder
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

## 3. Install Project Dependencies

Once your virtual environment is active (`(.venv)` appears in your terminal), install all project dependencies from the `requirements.txt` file.

---

### Upgrade `pip` and install requirements.txt

It’s good practice to upgrade `pip` first to avoid compatibility issues.

```bash
pip install --upgrade pip
after:
pip install -r requirements.txt
```


## Run the API Server

Once dependencies are installed and your virtual environment is active, you can start the API using **Uvicorn**, the ASGI server used by FastAPI.

---

### Run in Development Mode

Use the `--reload` flag to automatically restart the server whenever you modify code.

```bash
uvicorn app.main:app --reload --port 8000
