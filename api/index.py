from flask import Flask, jsonify, render_template_string
import requests
import random
import string
import time
import re

app = Flask(__name__)

BASE = "https://api.mail.tm"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Temp Mail Tool</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', sans-serif;
      background: #0f0f1a;
      color: #e0e0f0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card {
      background: #1a1a2e;
      border: 1px solid #2d2d5e;
      border-radius: 16px;
      padding: 40px;
      width: 100%;
      max-width: 520px;
      box-shadow: 0 0 40px rgba(100,80,255,0.15);
    }
    h1 {
      font-size: 1.6rem;
      color: #a78bfa;
      margin-bottom: 8px;
      text-align: center;
    }
    p.sub {
      text-align: center;
      color: #6b7280;
      font-size: 0.9rem;
      margin-bottom: 30px;
    }
    button {
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #7c3aed, #4f46e5);
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 1rem;
      cursor: pointer;
      transition: opacity 0.2s;
      font-weight: 600;
    }
    button:hover { opacity: 0.85; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .result {
      margin-top: 24px;
      display: none;
    }
    .field {
      background: #0f0f1a;
      border: 1px solid #2d2d5e;
      border-radius: 10px;
      padding: 14px 16px;
      margin-bottom: 12px;
    }
    .field label {
      font-size: 0.75rem;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      display: block;
      margin-bottom: 4px;
    }
    .field span {
      font-size: 1rem;
      color: #e0e0f0;
      word-break: break-all;
    }
    .code-box {
      background: linear-gradient(135deg, #1e1b4b, #1a1a2e);
      border: 1px solid #7c3aed;
      border-radius: 10px;
      padding: 20px;
      text-align: center;
      margin-top: 8px;
    }
    .code-box label {
      font-size: 0.75rem;
      color: #a78bfa;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      display: block;
      margin-bottom: 8px;
    }
    .code-box .code {
      font-size: 2rem;
      font-weight: 700;
      color: #a78bfa;
      letter-spacing: 0.15em;
    }
    .status {
      text-align: center;
      color: #6b7280;
      font-size: 0.9rem;
      margin-top: 16px;
      min-height: 22px;
    }
    .dot { animation: blink 1s infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }
    .copy-btn {
      margin-top: 8px;
      padding: 6px 14px;
      background: #2d2d5e;
      color: #a78bfa;
      border: none;
      border-radius: 6px;
      font-size: 0.8rem;
      cursor: pointer;
      width: auto;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>📬 Temp Mail Tool</h1>
    <p class="sub">Tạo email tạm thời và nhận mã xác nhận tự động</p>
    <button id="startBtn" onclick="start()">⚡ Tạo Email & Chờ Code</button>
    <div class="result" id="result">
      <div class="field">
        <label>Email</label>
        <span id="emailVal">—</span>
      </div>
      <div class="field">
        <label>Password</label>
        <span id="passVal">—</span>
      </div>
      <div class="code-box">
        <label>Mã xác nhận</label>
        <div class="code" id="codeVal">...</div>
        <button class="copy-btn" onclick="copyCode()">📋 Copy</button>
      </div>
    </div>
    <div class="status" id="status"></div>
  </div>

  <script>
    let polling = false;
    let pollData = null;

    async function start() {
      const btn = document.getElementById('startBtn');
      btn.disabled = true;
      document.getElementById('status').innerHTML = 'Đang tạo email<span class="dot">...</span>';
      document.getElementById('result').style.display = 'none';

      try {
        const res = await fetch('/api/create');
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        pollData = data;
        document.getElementById('emailVal').textContent = data.email;
        document.getElementById('passVal').textContent = data.password;
        document.getElementById('codeVal').textContent = '...';
        document.getElementById('result').style.display = 'block';

        pollCode(data.token);
      } catch (e) {
        document.getElementById('status').textContent = '❌ Lỗi: ' + e.message;
        btn.disabled = false;
      }
    }

    async function pollCode(token) {
      document.getElementById('status').innerHTML = 'Đang chờ email đến<span class="dot">...</span>';
      let attempts = 0;
      while (attempts < 60) {
        await sleep(5000);
        attempts++;
        try {
          const res = await fetch('/api/check?token=' + encodeURIComponent(token));
          const data = await res.json();
          if (data.code) {
            document.getElementById('codeVal').textContent = data.code;
            document.getElementById('status').textContent = '✅ Đã nhận được mã!';
            document.getElementById('startBtn').disabled = false;
            return;
          }
          document.getElementById('status').innerHTML = `Đang chờ... (${attempts * 5}s)<span class="dot">.</span>`;
        } catch(e) {}
      }
      document.getElementById('status').textContent = '⏱ Hết thời gian chờ.';
      document.getElementById('startBtn').disabled = false;
    }

    function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

    function copyCode() {
      const code = document.getElementById('codeVal').textContent;
      navigator.clipboard.writeText(code).then(() => alert('Đã copy: ' + code));
    }
  </script>
</body>
</html>
"""


def random_username(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/create')
def create_mail():
    try:
        # Get domain
        domain_res = requests.get(f"{BASE}/domains", timeout=10)
        domain = domain_res.json()["hydra:member"][0]["domain"]

        username = random_username()
        address = f"{username}@{domain}"
        password = "Pass1234!"

        # Create account
        acc_res = requests.post(f"{BASE}/accounts", json={
            "address": address,
            "password": password
        }, timeout=10)

        if acc_res.status_code not in (200, 201):
            return jsonify({"error": f"Tạo tài khoản thất bại: {acc_res.text}"}), 400

        # Get token
        token_res = requests.post(f"{BASE}/token", json={
            "address": address,
            "password": password
        }, timeout=10)
        token = token_res.json().get("token")

        return jsonify({
            "email": address,
            "password": password,
            "token": token
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/check')
def check_mail():
    from flask import request
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "Thiếu token"}), 400
    try:
        headers = {"Authorization": f"Bearer {token}"}
        msg_res = requests.get(f"{BASE}/messages", headers=headers, timeout=10)
        members = msg_res.json().get("hydra:member", [])

        if not members:
            return jsonify({"code": None})

        msg_id = members[0]["id"]
        mail_res = requests.get(f"{BASE}/messages/{msg_id}", headers=headers, timeout=10)
        mail = mail_res.json()

        text = mail.get("text", "") or ""
        html_body = mail.get("html", [""])[0] if mail.get("html") else ""
        combined = text + " " + html_body

        # Regex patterns phổ biến
        patterns = [
            r'\b[A-Z0-9]{3}-[A-Z0-9]{3}\b',
            r'\b\d{6}\b',
            r'\b[A-Z0-9]{8}\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, combined)
            if match:
                return jsonify({"code": match.group(0)})

        return jsonify({"code": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
