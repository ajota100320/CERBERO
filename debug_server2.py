import subprocess
import time
import sys
import threading
import queue

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line.decode('utf-8', errors='replace'))
    out.close()

def main():
    # Start the server
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=r"C:\Users\hola\Documents\Mi segundo Cerebro\Nuevo proyecto ERP",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False  # We'll handle decoding in our threads
    )
    print(f"Server started with PID {server_proc.pid}")
    
    # Set up queues to capture output
    stdout_q = queue.Queue()
    stderr_q = queue.Queue()
    
    stdout_thread = threading.Thread(target=enqueue_output, args=(server_proc.stdout, stdout_q))
    stderr_thread = threading.Thread(target=enqueue_output, args=(server_proc.stderr, stderr_q))
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    # Wait for server to be ready
    base_url = "http://127.0.0.1:8000"
    max_wait = 30
    start = time.time()
    while time.time() - start < max_wait:
        try:
            import httpx
            resp = httpx.get(f"{base_url}/health", timeout=5.0)
            if resp.status_code == 200:
                print("Server is ready.")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        print("Server did not become ready in time.")
        # Print whatever we've captured so far
        print("=== STDOUT ===")
        while not stdout_q.empty():
            print(stdout_q.get_nowait(), end='')
        print("=== STDERR ===")
        while not stderr_q.empty():
            print(stderr_q.get_nowait(), end='')
        server_proc.terminate()
        server_proc.wait()
        return

    try:
        # Now run the tests
        import httpx
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
                # We'll still try to see if we can get more info from server logs
                return
            
            # Now test POST to create a requerimiento
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
                # Follow the redirect to see the success message
                redirect_url = r.headers.get("location")
                if redirect_url:
                    if redirect_url not in [None, ""]:
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
            
            # Finally, list requerimientos again to see if the new one appears
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
        # Stop capturing and terminate the server
        server_proc.terminate()
        server_proc.wait(timeout=5)
        # Print any remaining output
        print("\n=== Final STDOUT ===")
        while not stdout_q.empty():
            print(stdout_q.get_nowait(), end='')
        print("\n=== Final STDERR ===")
        while not stderr_q.empty():
            print(stderr_q.get_nowait(), end='')

if __name__ == "__main__":
    main()