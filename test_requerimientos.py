import time
import subprocess
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
    time.sleep(3)
    # Check if process is still alive
    if server_proc.poll() is not None:
        stdout, stderr = server_proc.communicate()
        print("Server failed to start:")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        return

    try:
        base_url = "http://127.0.0.1:8000"
        # Step 1: Get login page to get CSRF? Actually our login uses form, no CSRF.
        # We'll just post to /login
        login_data = {
            "email": "admin@erp.cl",
            "password": "123456",
            "remember": "false"
        }
        with httpx.Client() as client:
            # First, get the login page to maybe get any cookies (though we don't need)
            r = client.get(f"{base_url}/login")
            print(f"Login page status: {r.status_code}")
            # Post login
            r = client.post(f"{base_url}/login", data=login_data, follow_redirects=False)
            print(f"Login POST status: {r.status_code}")
            print(f"Login headers: {r.headers}")
            # Extract cookie
            cookies = r.cookies
            print(f"Cookies: {cookies}")
            # Now access protected endpoint with cookies
            client.cookies = cookies
            # Get the requerimientos page (should redirect to login if not authenticated)
            r = client.get(f"{base_url}/requerimientos")
            print(f"Access /requerimientos status: {r.status_code}")
            if r.status_code != 200:
                print(f"Response text: {r.text[:500]}")
            # Now create a requerimiento
            new_req = {
                "producto": "Tomate cherry",
                "cantidad": "5.0",
                "precio_estimado": "1200.0",
                "prioridad": "Alta",
                "sucursal_id": "1"
            }
            r = client.post(f"{base_url}/requerimientos", data=new_req, follow_redirects=False)
            print(f"Create requerimiento status: {r.status_code}")
            print(f"Location header: {r.headers.get('location')}")
            # Follow redirect to see success message
            if r.status_code in (302, 303):
                redirect_url = r.headers.get("location")
                r = client.get(f"{base_url}{redirect_url}")
                print(f"After redirect status: {r.status_code}")
                # Check if success message appears
                if "Requerimiento creado exitosamente" in r.text:
                    print("✅ Success message found in response")
                else:
                    print("⚠️ Success message not found")
            # Now list requerimientos to see if it's there
            r = client.get(f"{base_url}/requerimientos")
            print(f"List requerimientos status: {r.status_code}")
            if "Tomate cherry" in r.text:
                print("✅ New requerimiento found in list")
            else:
                print("⚠️ New requerimiento NOT found in list")
                # Print a snippet for debugging
                print(f"Snippet: {r.text[:1000]}")
    finally:
        # Kill the server
        server_proc.terminate()
        server_proc.wait(timeout=5)
        print("Server terminated")

if __name__ == "__main__":
    main()