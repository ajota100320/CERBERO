import httpx
import time

BASE_URL = "http://127.0.0.1:8000"

def test_endpoints():
    # First, login to get a session
    with httpx.Client() as client:
        # Get login page (optional)
        r = client.get(f"{BASE_URL}/login")
        print(f"Login page: {r.status_code}")
        
        # Login
        login_data = {
            "email": "admin@erp.cl",
            "password": "123456",
            "remember": "false"
        }
        r = client.post(f"{BASE_URL}/login", data=login_data, follow_redirects=False)
        print(f"Login POST: {r.status_code}")
        if r.status_code not in (302, 303):
            print("Login failed")
            print(r.text[:500])
            return
        
        # The client now has the cookie from the response (Set-Cookie)
        # Let's access a protected endpoint: /requerimientos (GET)
        r = client.get(f"{BASE_URL}/requerimientos")
        print(f"GET /requerimientos: {r.status_code}")
        if r.status_code == 200:
            if "Requerimientos de Cierre" in r.text:
                print("✓ GET /requerimientos successful and page contains expected heading")
            else:
                print("⚠ GET /requerimientos returned 200 but heading not found")
                # Print a snippet for debugging
                print(f"Snippet: {r.text[:500]}")
        else:
            print(f"✗ GET /requerimientos failed with status {r.status_code}")
            print(r.text[:500])
            return
        
        # Now test POST to create a requerimiento
        new_req = {
            "producto": "Tomate cherry",
            "cantidad": "5.0",
            "precio_estimado": "1200.0",
            "prioridad": "Alta",
            "sucursal_id": "1"
        }
        r = client.post(f"{BASE_URL}/requerimientos", data=new_req, follow_redirects=False)
        print(f"POST /requerimientos: {r.status_code}")
        if r.status_code in (302, 303):
            print("✓ POST /requerimientos returned redirect (as expected)")
            # Follow the redirect to see the success message
            redirect_url = r.headers.get("location")
            if redirect_url:
                if redirect_url not in [None, ""]:
                    if redirect_url.startswith("/"):
                        redirect_url = BASE_URL + redirect_url
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
        r = client.get(f"{BASE_URL}/requerimientos")
        print(f"GET /requerimientos after creation: {r.status_code}")
        if r.status_code == 200:
            if "Tomate cherry" in r.text:
                print("✓ New requerimiento found in the list")
            else:
                print("⚠ New requerimiento NOT found in the list")
                # Maybe it's there but not in the text we checked? Let's see a snippet
                print(f"Snippet: {r.text[:1000]}")
        else:
            print(f"✗ GET /requerimientos failed after creation: {r.status_code}")

if __name__ == "__main__":
    # Give the server a moment to start (if it hasn't already)
    time.sleep(2)
    test_endpoints()