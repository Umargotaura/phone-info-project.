from flask import Flask, request, render_template_string
from datetime import datetime, timezone
from collections import deque
import os
import secrets

app = Flask(__name__)

# Temporary storage for recent submissions.
visits = deque(maxlen=500)

# 1. Set your secret token here or in environment variables
DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "default_secret_token")

# 2. Set a secret URL path so people don't know where the dashboard is
SECRET_URL_PATH = os.environ.get("SECRET_URL_PATH", "/admin-panel")

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Browser Information Demo</title>
  <style>
    body { font-family: sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }
    #status { margin-top: 10px; color: green; font-weight: bold; }
    .info-box { background: #f4f4f4; padding: 10px; border-radius: 5px; margin-top: 20px; }
  </style>
</head>
<body>
  <h2>Browser Info Demo</h2>
  <p>This page collects basic info automatically.</p>
  
  <div class="info-box">
    <p id="status">Submitting...</p>
    <p><small>Platform: <span id="plat"></span></small></p>
    <p><small>Screen: <span id="scr"></span></small></p>
  </div>
  
  <script>
    const info = {
      platform: navigator.userAgentData?.platform || navigator.platform || "Unknown",
      screen_width: screen.width,
      screen_height: screen.height,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };

    // Update UI immediately for user feedback
    document.getElementById('plat').textContent = info.platform;
    document.getElementById('scr').textContent = `${info.screen_width}x${info.screen_height}`;

    fetch("/submit", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(info)
    })
    .then(response => {
      document.getElementById("status").textContent = 
        response.ok ? "✅ Data sent successfully." : "❌ Submission failed.";
    })
    .catch(() => {
      document.getElementById("status").textContent = "⚠️ Unable to submit.";
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
    
    allowed = ("platform", "screen_width", "screen_height", "timezone")
    clean = {
        key: str(data.get(key, "Unknown"))[:100]
        for key in allowed
    }
    clean["visited_at"] = datetime.now(timezone.utc).isoformat()
    
    visits.append(clean)
    return {"ok": True}

@app.get(SECRET_URL_PATH)
def dashboard():
    # Check for the token
    supplied_token = request.headers.get("X-Dashboard-Token", "")
    
    if not secrets.compare_digest(supplied_token, DASHBOARD_TOKEN):
        # Return 404 instead of 401 to make it even harder to find
        # It looks like the page doesn't exist rather than "wrong password"
        return "Not Found", 404
        
    return {"visits": list(visits)}

if __name__ == "__main__":
    app.run(debug=False) # Debug mode off for production feel
