import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uvicorn
import config.settings as settings

if __name__ == "__main__":
    print(f"\n🚀 API: http://localhost:{settings.API_PORT}\n   Docs: http://localhost:{settings.API_PORT}/docs\n")
    uvicorn.run("api.app:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)