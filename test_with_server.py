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
        # Get the server's output to see what went wrong
        stdout, stderr = server_proc.communicate(timeout=5)
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        server_proc.terminate()
        server_proc.wait()
        return

    try:
        # Now run the tests
        with httpx.Client() as client:
            # Login
            r = client.get(f"{base_url}/login")
            print(f"Login page: {r.status_code}")
            
            login_data = {
                "email": "admin@erp.cl",
                "password": "123456",
                "remember": "false"
            }
            r = client.post(f"{base_url}/login", data=login_data, follow_redirects=False)
            print(f"Login POST: {r.status_code}")
            if r.status_code not in (302, 303):
                print("Login failed")
                print(r.text[:500])
                return
            
            # Access /requerimientos (GET)
            r = client.get(f"{base_url}/requerimientos")
            print(f"GET /requerimientos: {r.status_code}")
            if r.status_code == 200:
                if "Requerimientos de Cierre" in r.text:
                    print("✓ GET /requerimientos successful and page contains expected heading")
                else:
                    print("⚠ GET /requerimientos returned 200 but heading not found")
                    print(f"Snippet: {r.text[:500]}")
            else:
                print(f"✗ GET /requerimientos failed with status {r.status_code}")
                print(r.text[:500])
                return
            
            # POST to create a requerimiento
            new_req = {
                "producto": "Tomate cherry",
                "cantidad": "5.0",
                "precio_estimado": "1200.0",
                "prioridad": "Alta",
                "sucursal_id": "1"
            }
            r = client.post(f"{base_url}/requerimientos", data=new_req, follow_redirects=False)
            print(f"POST /requerimientos: {r.status_code}")
            if r.status_code in (302, 303):
                print("✓ POST /requerimientos returned redirect (as expected)")
                redirect_url = r.headers.get("location")
                if redirect_url:
                    if redirect_url.startswith("/"):
                        redirect_url = base_url + redirect_url
                    r2 = client.get(redirect_url)
                    print(f"Followed redirect to {redirect_url}: {r2.status_code}")
                    if "Requerimiento creado exitosamente" in r2.text:
                        print("✓ Success message found after redirect")
                    else:
                        print("⚠ Success message not found in redirected page")
                        print(r2.text[:500])
            else:
                print(f"✗ POST /requerimientos unexpected status: {r.status_code}")
                print(r.text[:500])
            
            # List requerimientos again
            r = client.get(f"{base_url}/requerimientos")
            print(f"GET /requerimientos after creation: {r.status_code}")
            if r.status_code == 200:
                if "Tomate cherry" in r.text:
                    print("✓ New requerimiento found in the list")
                else:
                    print("⚠ New requerimiento NOT found in the list")
                    print(f"Snippet: {r.text[:1000]}")
            else:
                print(f"✗ GET /requerimientos failed after creation: {r.status_code}")
    finally:
        # Stop the server
        server_proc.terminate()
        server_proc.wait(timeout=5)
        print("Server terminated.")

if __name__ == "__main__":
    main()