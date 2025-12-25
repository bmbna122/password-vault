from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import secrets, string
from supabase_store import store_secret

app = FastAPI()

def generate_password(length=20):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+"
    return ''.join(secrets.choice(chars) for _ in range(length))

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h2>Cloud Password Vault</h2>
    <form action="/generate" method="post">
      Username:<br><input name="username" required><br>
      Notes:<br><textarea name="notes" required></textarea><br>
      Password Length:<br><input name="length" value="20"><br><br>
      <button type="submit">Generate & Save</button>
    </form>
    """
@app.post("/generate", response_class=HTMLResponse)
def generate(username: str = Form(...), notes: str = Form(...), length: int = Form(20)):
    password = generate_password(length)

    ok =  store_secret(username, notes, password)

    if not ok:
        return f"""
        <h3 style="color:red;"> Duplicate Entry</h3>
        <p>This username + note already exists.</p>
        """

    return f"""
    <h3>Password Generated & Saved</h3>
    <pre>

Username: {username}
Notes: {notes}
Password: {password}
    </pre>
    <a href="/">Generate another</a>
    """
