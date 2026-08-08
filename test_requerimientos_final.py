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
        except Exception:
            pass
        time.sleep(1)
    else:
        print("Server did not become ready in time.")
        server_proc.terminate()
        server_proc.wait()
        return

    try:
        # Step 1: Login
        login_url = f"{base_url}/login"
        with httpx.Client() as client:
            # Get the login page (optional, but we can do it to get any cookies if needed)
            resp = client.get(login_url)
            print(f"Login page status: {resp.status_code}")
            
            # Prepare login data
            login_data = {
                "email": "admin@erp.cl",
                "password": "123456",
                "remember": "false"
            }
            # Post login
            resp = client.post(login_url, data=login_data, follow_redirects=False)
            print(f"Login POST status: {resp.status_code}")
            print(f"Login headers: {resp.headers}")
            
            # Check for redirect to /
            if resp.status_code in (302, 303):
                # Get the cookie
                cookies = resp.cookies
                print(f"Cookies after login: {cookies}")
                # Create a new client with the cookie for subsequent requests
                client = httpx.Client(cookies=cookies)
            else:
                print("Login failed")
                print(resp.text)
                return

        # Step 2: Access /requerimientos (GET)
        req_url = f"{base_url}/requerimientos"
        resp = client.get(req_url)
        print(f"GET /requerimientos status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Response text: {resp.text[:500]}")
            return
        # Check that the page contains the expected title or heading
        if "Requerimientos de Cierre" in resp.text:
            print("✅ Page loaded successfully and contains expected heading.")
        else:
            print("⚠️ Page loaded but expected heading not found.")
            # Print a snippet for debugging
            print(f"Snippet: {resp.text[:1000]}")

        # Step 3: Create a new requerimiento (POST)
        create_url = f"{base_url}/requerimientos"
        new_req = {
            "producto": "Tomate cherry",
            "cantidad": "5.0",
            "precio_estimado": "1200.0",
            "prioridad": "Alta",
            "sucursal_id": "1"
        }
        resp = client.post(create_url, data=new_req, follow_redirects=False)
        print(f"POST /requerimientos status: {resp.status_code}")
        print(f"Location header: {resp.headers.get('location')}")
        if resp.status_code in (302, 303):
            # Follow the redirect
            redirect_url = resp.headers.get('location')
            if redirect_url.startswith('/'):
                redirect_url = f"{base_url}{redirect_url}"
            resp = client.get(redirect_url)
            print(f"After redirect status: {resp.status_code}")
            if "Requerimiento creado exitosamente" in resp.text:
                print("✅ Success message found after redirect.")
            else:
                print("⚠️ Success message not found after redirect.")
        else:
            print(f"Unexpected status code: {resp.status_code}")
            print(resp.text)

        # Step 4: List requerimientos again to see if the new one is there
        resp = client.get(f"{base_url}/requerimientos")
        print(f"GET /requerimientos after creation status: {resp.status_code}")
        if "Tomate cherry" in resp.text:
            print("✅ New requerimiento found in the list.")
        else:
            print("⚠️ New requerimiento NOT found in the list.")
            # Print a snippet for debugging
            print(f"Snippet: {resp.text[:2000]}")

    finally:
        # Clean up: terminate the server
        server_proc.terminate()
        server_proc.wait(timeout=5)
        print("Server terminated.")

if __name__ == "__main__":
    main()