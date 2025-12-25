import os, requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def store_secret(username, notes, password):
    url = f"{SUPABASE_URL}/rest/v1/vault"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    r = requests.post(url, headers=headers, json={
        "username": username,
        "notes": notes,
        "password": password
    })

    if r.status_code == 409:
        return False
    return True


