import uvicorn
from fastapi.responses import HTMLResponse
import os

# Import your existing API application
try:
    from api_server import app
except ImportError:
    print("Error: Could not find 'app' in api_server.py.")
    exit()

# Add a route to serve your mobile app
@app.get("/mobile", response_class=HTMLResponse)
async def serve_mobile_pm():
    file_path = os.path.join(os.getcwd(), "mobile_pm.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Error</h1><p>mobile_pm.html not found.</p>", status_code=404)

# Start the server
if __name__ == "__main__":
    print("Starting server...")
    print("On your phone, visit: https://designing-saturday-internship-geological.trycloudflare.com/mobile")
    uvicorn.run(app, host="0.0.0.0", port=8000)