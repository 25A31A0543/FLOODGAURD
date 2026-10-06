"""
FloodGuard — Step 1: Data Ingestion Engine Server Launcher.
Run with: python run_server.py
Access interactive dashboard at: http://127.0.0.1:8000/dashboard
Access API documentation at: http://127.0.0.1:8000/docs
"""
import uvicorn

if __name__ == "__main__":
    print("Starting FloodGuard Step 1: Data Ingestion Engine...")
    print("Dashboard: http://127.0.0.1:8000/dashboard")
    print("Swagger Docs: http://127.0.0.1:8000/docs")
    uvicorn.run("floodguard.main:app", host="127.0.0.1", port=8000, reload=True)
