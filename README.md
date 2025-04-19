# Real Estate Dashboard Project (King County Focus)

This project aims to create a dashboard for visualizing local real estate market factors, their impact on home values, and potential future outlooks, initially focusing on King County, WA.

## Project Objectives

(Copy/paste from the original description if desired, or summarize)
* Visualize market factors affecting home values.
* Provide future outlooks using PCA and AI insights.
* Target users: Developers, investors, brokers, consumers.

## Tech Stack (Initial)

* Python
* Flask (Web Framework)
* HTML/CSS/JavaScript
* Leaflet.js (Mapping Library)
* (Potentially: Pandas, Scikit-learn, GeoPandas, AI APIs)

## Setup Instructions

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <your-repo-url>
    cd your-project-name
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows (cmd):
    # .\venv\Scripts\activate
    # On Windows (PowerShell):
    # .\venv\Scripts\Activate.ps1
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables (if needed):**
    * Flask needs to know where your app is. Set the `FLASK_APP` environment variable.
    ```bash
    # On macOS/Linux:
    export FLASK_APP=app
    export FLASK_ENV=development # Optional: enables debug mode
    # On Windows (cmd):
    # set FLASK_APP=app
    # set FLASK_ENV=development
    # On Windows (PowerShell):
    # $env:FLASK_APP = "app"
    # $env:FLASK_ENV = "development"
    ```
    *(Note: Setting FLASK_ENV=development enables helpful debugging features)*

5.  **Run the application:**
    ```bash
    flask run
    ```

6.  Open your web browser and navigate to `http://127.0.0.1:5000` (or the address provided by Flask).

## Project Structure