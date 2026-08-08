import subprocess
import time
import sys
import httpx

def main():
    # Start the server and capture stdout and stderr
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
        # Now make a request to /requerimientos (GET) after logging in
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
                print(f"Response body: {r.text[:1000]}")
                # We'll still try to see if there's more info in the server logs
    finally:
        # Stop the server and get its output
        server_proc.terminate()
        stdout, stderr = server_proc.communicate(timeout=5)
        print("\n=== Server STDOUT ===")
        print(stdout)
        print("\n=== Server STDERR ===")
        print(stderr)

if __name__ == "__main__":
    main()