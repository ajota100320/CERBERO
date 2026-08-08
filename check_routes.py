import sys
sys.path.insert(0, r'C:\Users\hola\Documents\Mi segundo Cerebro\Nuevo proyecto ERP')

from app.main import app
from fastapi.routing import APIRoute

# List all routes
routes = []
for route in app.routes:
    if isinstance(route, APIRoute):
        routes.append(f"{','.join(route.methods)} {route.path}")
    else:
        # For other types like Mount, etc.
        routes.append(f"{route.path}")

print("Registered routes:")
for r in sorted(routes):
    print(r)

# Check if our required routes are present
required = [
    "GET /requerimientos",
    "POST /requerimientos"
]
for req in required:
    if req in [r for r in routes]:
        print(f"✓ Found: {req}")
    else:
        print(f"✗ Missing: {req}")