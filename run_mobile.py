import uvicorn
from fastapi.responses import HTMLResponse

# Import your existing API application
# (Assuming your FastAPI app is defined in api_server.py as `app = FastAPI()`)
try:
    from api_server import app
except ImportError:
    print("Error: Could not find 'app' in api_server.py.")
    print("If your FastAPI app is in another file (like api/main.py), please change the import line in this script.")
    exit(1)

# Add the /mobile route to serve your HTML file
@app.get("/mobile", response_class=HTMLResponse)
async def serve_mobile_app():
    try:
        with open("mobile_pm.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error</h1><p>mobile_pm.html not found in the folder.</p>", status_code=404)

# Start the server
if __name__ == "__main__":
    print("Starting server...")
    print("Mobile App URL: http://localhost:8000/mobile")
    print("Press CTRL+C to stop.")
    uvicorn.run(app, host="0.0.0.0", port=8000)