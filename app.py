from flask import Flask, request, render_template_string
from datetime import datetime, timezone
from collections import deque
import os
import secrets

app = Flask(__name__)

# Temporary storage for recent submissions.
# Data resets when the server restarts.
visits = deque(maxlen=500)

# Set this environment variable to secure your dashboard.
# Example: DASHBOARD_TOKEN="my_secret_key" python app.py
DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "")

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Browser Information Demo</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    #status { margin-top: 10px; color: green; }
  </style>
</head>
<body>
  <h2>Browser Information Demo</h2>
  <p>
    This demo automatically submits basic browser information
    when you open this page. It collects your browser's reported
    platform, screen dimensions, and visit time.
  </p>
  <p id="status">Submitting browser information...</p>
  
  <script>
    const info = {
      platform: navigator.userAgentData?.platform || navigator.platform || "Unknown",
      screen_width: screen.width,
      screen_height: screen.height,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };

    fetch("/submit", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(info)
    })
    .then(response => {
      document.getElementById("status").textContent = 
        response.ok ? "Submission complete." : "Submission failed.";
    })
    .catch(() => {
      document.getElementById("status").textContent = "Unable to submit information.";
    });
  </script>
</body>
</html>"""

@app.get("/")
def home():
    return render_template_string(PAGE)

@app.post("/submit")
def submit():
    data = request.get_json(silent=True) or {}
    
    # Accept only the specific fields used by this demo.
    allowed = ("platform", "screen_width", "screen_height", "timezone")
    clean = {
        key: str(data.get(key, "Unknown"))[:100]
        for key in allowed
    }
    clean["visited_at"] = datetime.now(timezone.utc).isoformat()
    
    visits.append(clean)
    return {"ok": True}

@app.get("/dashboard")
def dashboard():
    if not DASHBOARD_TOKEN:
        return "Dashboard is not configured.", 503
    
    supplied = request.headers.get("X-Dashboard-Token", "")
    
    # Secure comparison to prevent timing attacks
    if not secrets.compare_digest(supplied, DASHBOARD_TOKEN):
        return "Unauthorized", 401
        
    return {"visits": list(visits)}

if __name__ == "__main__":
    app.run(debug=True)
