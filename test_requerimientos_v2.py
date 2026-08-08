import subprocess
import time
import sys
import httpx

def main():
    # Start the server
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=r"C:\Users\hola\Documents\Mi segundo Cerebro\Nuevo proyecto ERP",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print(f"Server started with PID {server_proc.pid}")
    
    # Wait for server to be ready
    base_url = "http://127.0.0.1:8000"
    max_wait = 30
    start = time.time()
    while time.time() - start < max_wait:
        try:
            resp = httpx.get(f"{base_url}/health", timeout=5.0)
            if resp.status_code == 200:
                print("Server is ready.")
                break
        except Exception as e:
            pass
        time.sleep(1)
    else:
        print("Server did not become ready in time.")
        server_proc.terminate()
        server_proc.wait()
        return

    try:
        # Use a single client with reasonable timeout
        with httpx.Client(timeout=15.0) as client:
            # Step 1: Login
            login_url = f"{base_url}/login"
            print("Fetching login page...")
            resp = client.get(login_url)
            print(f"Login page status: {resp.status_code}")
            
            login_data = {
                "email": "admin@erp.cl",
                "password": "123456",
                "remember": "false"
            }
            print("Posting login...")
            resp = client.post(login_url, data=login_data, follow_redirects=False)
            print(f"Login POST status: {resp.status_code}")
            print(f"Login headers: {resp.headers}")
            
            if resp.status_code not in (302, 303):
                print("Login failed")
                print(resp.text[:500])
                return
            
            # The client already has the cookie from the response (since we didn't follow redirect)
            # But we need to make sure we keep the cookie for subsequent requests.
            # The client cookie jar should have been updated automatically.
            # Let's proceed to /requerimientos
            
            # Step 2: Access /requerimientos
            req_url = f"{base_url}/requerimientos"
            print(f"GET {req_url}...")
            resp = client.get(req_url)
            print(f"GET /requerimientos status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"Response text (first 500 chars): {resp.text[:500]}")
                return
            # Check for expected content
            if "Requerimientos de Cierre" in resp.text:
                print("✅ Page loaded successfully and contains expected heading.")
            else:
                print("⚠️ Page loaded but expected heading not found.")
                # Save a snippet for debugging
                print(f"Response snippet (first 1000 chars): {resp.text[:1000]}")
            
            # Step 3: Create a new requerimiento
            create_url = f"{base_url}/requerimientos"
            new_req = {
                "producto": "Tomate cherry",
                "cantidad": "5.0",
                "precio_estimado": "1200.0",
                "prioridad": "Alta",
                "sucursal_id": "1"
            }
            print(f"POST {create_url}...")
            resp = client.post(create_url, data=new_req, follow_redirects=False)
            print(f"POST /requerimientos status: {resp.status_code}")
            print(f"Location header: {resp.headers.get('location')}")
            if resp.status_code in (302, 303):
                # Follow redirect
                redirect_url = resp.headers.get('location')
                if redirect_url.startswith('/'):
                    redirect_url = f"{base_url}{redirect_url}"
                print(f"Following redirect to {redirect_url}")
                resp = client.get(redirect_url)
                print(f"After redirect status: {resp.status_code}")
                if "Requerimiento creado exitosamente" in resp.text:
                    print("✅ Success message found after redirect.")
                else:
                    print("⚠️ Success message not found after redirect.")
                    print(f"Response snippet: {resp.text[:500]}")
            else:
                print(f"Unexpected status code: {resp.status_code}")
                print(resp.text[:500])
            
            # Step 4: List requerimientos again
            print(f"GET {req_url} after creation...")
            resp = client.get(req_url)
            print(f"GET /requerimientos after creation status: {resp.status_code}")
            if "Tomate cherry" in resp.text:
                print("✅ New requerimiento found in the list.")
            else:
                print("⚠️ New requerimiento NOT found in the list.")
                print(f"Response snippet (first 2000 chars): {resp.text[:2000]}")
                
    finally:
        # Clean up: terminate the server
        server_proc.terminate()
        server_proc.wait(timeout=5)
        print("Server terminated.")

if __name__ == "__main__":
    main()