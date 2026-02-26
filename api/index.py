from flask import Flask, jsonify, request
import requests
import re
import time

app = Flask(__name__)

BASE = "https://api.mail.tm"

# ─── Regex patterns để bắt mã xác nhận ──────────────────────────────────────
# Thêm / bớt tuỳ định dạng mã của site bạn cần
CODE_PATTERNS = [
    r'\b[A-Z0-9]{3}-[A-Z0-9]{3}\b',   # ABC-123
    r'\b\d{6}\b',                        # 123456
    r'\b\d{4}\b',                        # 1234
    r'\b[A-Z0-9]{8}\b',                 # AB12CD34
]


def get_token(email: str, password: str) -> str:
    res = requests.post(f"{BASE}/token", json={
        "address":  email,
        "password": password
    }, timeout=10)
    res.raise_for_status()
    token = res.json().get("token")
    if not token:
        raise Exception("Không lấy được token — kiểm tra lại email/password")
    return token


def extract_code(text: str, patterns: list) -> str | None:
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    return None


HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Get Code API</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:#0f0f1a;color:#e0e0f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
    .wrap{width:100%;max-width:640px}
    h1{font-size:1.7rem;color:#34d399;text-align:center;margin-bottom:6px}
    .sub{text-align:center;color:#6b7280;margin-bottom:32px;font-size:.93rem}
    .card{background:#1a1a2e;border:1px solid #2d2d5e;border-radius:14px;padding:26px;margin-bottom:18px}
    h2{font-size:.95rem;color:#34d399;margin-bottom:14px}
    .ep{background:#0f0f1a;border:1px solid #2d2d5e;border-radius:8px;padding:12px 16px;font-family:monospace;font-size:.88rem;color:#7dd3fc;margin-bottom:14px}
    .badge-get{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700;margin-right:6px;background:#065f46;color:#6ee7b7}
    .badge-post{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700;margin-right:6px;background:#1e3a5f;color:#7dd3fc}
    table{width:100%;border-collapse:collapse;font-size:.87rem}
    th{text-align:left;color:#6b7280;padding:5px 8px;border-bottom:1px solid #2d2d5e}
    td{padding:8px;border-bottom:1px solid #1e1e3a;vertical-align:top}
    td:first-child{font-family:monospace;color:#f9a8d4;white-space:nowrap}
    .req{color:#fca5a5;font-size:.72rem;margin-left:4px}
    input{width:100%;background:#0f0f1a;border:1px solid #2d2d5e;color:#e0e0f0;border-radius:8px;padding:10px 14px;font-size:.9rem;outline:none;margin-bottom:10px}
    input:focus{border-color:#34d399}
    .row{display:flex;gap:10px}
    .row input{flex:1}
    button{width:100%;padding:13px;background:linear-gradient(135deg,#059669,#0d9488);color:#fff;border:none;border-radius:9px;font-size:.95rem;cursor:pointer;font-weight:600;transition:opacity .2s}
    button:hover{opacity:.85}
    button:disabled{opacity:.45;cursor:not-allowed}
    pre{background:#0f0f1a;border:1px solid #2d2d5e;border-radius:8px;padding:14px;font-size:.83rem;color:#d1d5db;white-space:pre-wrap;word-break:break-all;min-height:54px;margin-top:12px}
    .lbl{font-size:.8rem;color:#6b7280;margin:8px 0 6px;display:block}
    .spin{display:inline-block;animation:spin 1s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
  </style>
</head>
<body>
<div class="wrap">
  <h1>🔍 Get Code API</h1>
  <p class="sub">Nhận <code>email + password</code> → chờ mail → trả về mã xác nhận</p>

  <div class="card">
    <h2>🔌 Endpoint</h2>
    <div class="ep">
      <span class="badge-get">GET</span>/api/get-code?email=...&amp;password=...<br/>
      <span class="badge-post" style="margin-top:8px;display:inline-block">POST</span>/api/get-code &nbsp;→ body: <code>{"email","password","timeout","pattern"}</code>
    </div>
    <table>
      <tr><th>Tham số</th><th>Nơi truyền</th><th>Mặc định</th><th>Mô tả</th></tr>
      <tr><td>email <span class="req">*bắt buộc</span></td><td>query / body</td><td>—</td><td>Địa chỉ email tạm</td></tr>
      <tr><td>password <span class="req">*bắt buộc</span></td><td>query / body</td><td>—</td><td>Mật khẩu tài khoản</td></tr>
      <tr><td>timeout</td><td>query / body</td><td>120</td><td>Thời gian chờ tối đa (giây)</td></tr>
      <tr><td>interval</td><td>query / body</td><td>5</td><td>Khoảng cách giữa mỗi lần check (giây)</td></tr>
      <tr><td>pattern</td><td>query / body</td><td>—</td><td>Regex tuỳ chỉnh để bắt mã</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>📤 Response</h2>
    <table>
      <tr><th>Field</th><th>Kiểu</th><th>Mô tả</th></tr>
      <tr><td>success</td><td>bool</td><td>true nếu tìm được mã</td></tr>
      <tr><td>code</td><td>string</td><td>Mã xác nhận trích xuất được</td></tr>
      <tr><td>from</td><td>string</td><td>Địa chỉ người gửi</td></tr>
      <tr><td>subject</td><td>string</td><td>Tiêu đề email</td></tr>
      <tr><td>elapsed</td><td>float</td><td>Thời gian xử lý (giây)</td></tr>
      <tr><td>error</td><td>string</td><td>Thông báo lỗi (nếu có)</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>🧪 Thử ngay</h2>
    <input id="email" type="text" placeholder="email *" />
    <input id="password" type="text" placeholder="password *" />
    <div class="row">
      <input id="timeout" type="number" placeholder="timeout (s)" value="120"/>
      <input id="pattern" type="text" placeholder="regex (tuỳ chọn)"/>
    </div>
    <button id="btn" onclick="run()">🔍 Chờ & Lấy Code</button>
    <span class="lbl" id="lbl"></span>
    <pre id="out">// Kết quả hiển thị ở đây...</pre>
  </div>

  <div class="card">
    <h2>💡 Ví dụ gọi API</h2>
    <pre># cURL (GET)
curl "https://your-get-code-app.vercel.app/api/get-code?email=abc@mail.tm&password=Pass1234!&timeout=60"

# cURL (POST)
curl -X POST "https://your-get-code-app.vercel.app/api/get-code" \\
  -H "Content-Type: application/json" \\
  -d '{"email":"abc@mail.tm","password":"Pass1234!","timeout":60}'

# Python
import requests
r = requests.post("https://your-get-code-app.vercel.app/api/get-code", json={
    "email": "abc@mail.tm",
    "password": "Pass1234!",
    "timeout": 60
})
print(r.json()["code"])

# JavaScript
const res = await fetch("/api/get-code", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password, timeout: 60 })
});
const data = await res.json();</pre>
  </div>
</div>
<script>
  async function run() {
    const btn = document.getElementById('btn');
    const out = document.getElementById('out');
    const lbl = document.getElementById('lbl');
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const timeout  = document.getElementById('timeout').value || 120;
    const pattern  = document.getElementById('pattern').value.trim();

    if (!email || !password) {
      lbl.textContent = '⚠️ Vui lòng nhập email và password';
      return;
    }

    btn.disabled = true;
    const startTime = Date.now();
    const timer = setInterval(() => {
      const s = ((Date.now() - startTime) / 1000).toFixed(1);
      lbl.innerHTML = '<span class="spin">⏳</span> Đang chờ mail... ' + s + 's';
    }, 200);

    try {
      const body = { email, password, timeout: parseInt(timeout) };
      if (pattern) body.pattern = pattern;
      const res = await fetch('/api/get-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      clearInterval(timer);
      lbl.textContent = data.success ? '✅ Tìm được mã sau ' + data.elapsed + 's' : '❌ Thất bại: ' + (data.error || '');
      out.textContent = JSON.stringify(data, null, 2);
    } catch(e) {
      clearInterval(timer);
      lbl.textContent = '❌ Lỗi kết nối';
      out.textContent = e.message;
    }
    btn.disabled = false;
  }
</script>
</body>
</html>"""


@app.route('/')
def index():
    return HTML


@app.route('/api/get-code', methods=['GET', 'POST'])
def get_code():
    """
    Nhận email + password → đăng nhập → poll inbox → trích mã → trả JSON.

    Params (query string cho GET, JSON body cho POST):
      email    * : string — địa chỉ email
      password * : string — mật khẩu
      timeout    : int    — giây chờ tối đa, mặc định 120
      interval   : int    — giây giữa mỗi lần poll, mặc định 5
      pattern    : string — regex tuỳ chỉnh (ghi đè CODE_PATTERNS)
    """
    t0 = time.time()

    if request.method == 'POST':
        body           = request.get_json(silent=True) or {}
        email          = body.get('email', '').strip()
        password       = body.get('password', '').strip()
        timeout        = int(body.get('timeout', 120))
        interval       = int(body.get('interval', 5))
        custom_pattern = body.get('pattern', None)
    else:
        email          = request.args.get('email', '').strip()
        password       = request.args.get('password', '').strip()
        timeout        = int(request.args.get('timeout', 120))
        interval       = int(request.args.get('interval', 5))
        custom_pattern = request.args.get('pattern', None)

    # Validate
    if not email or not password:
        return jsonify({
            "success": False,
            "error":   "Thiếu tham số bắt buộc: email và password"
        }), 400

    timeout  = max(10, min(timeout, 300))
    interval = max(2,  min(interval, 30))
    patterns = [custom_pattern] if custom_pattern else CODE_PATTERNS

    try:
        # 1. Lấy JWT token
        token = get_token(email, password)

        # 2. Poll inbox và trích mã
        headers  = {"Authorization": f"Bearer {token}"}
        deadline = time.time() + timeout
        code = subject = sender = None

        while time.time() < deadline:
            msg_res = requests.get(f"{BASE}/messages", headers=headers, timeout=10)
            msg_res.raise_for_status()
            members = msg_res.json().get("hydra:member", [])

            for msg in members:
                detail = requests.get(
                    f"{BASE}/messages/{msg['id']}", headers=headers, timeout=10
                )
                detail.raise_for_status()
                mail = detail.json()

                text     = mail.get("text", "") or ""
                html_raw = " ".join(mail.get("html", []) or [])
                combined = text + " " + html_raw

                code = extract_code(combined, patterns)
                if code:
                    subject = mail.get("subject", "")
                    sender  = mail.get("from", {}).get("address", "")
                    break

            if code:
                break

            time.sleep(interval)

        elapsed = round(time.time() - t0, 2)

        if code:
            return jsonify({
                "success": True,
                "code":    code,
                "from":    sender,
                "subject": subject,
                "elapsed": elapsed
            })
        else:
            return jsonify({
                "success": False,
                "code":    None,
                "error":   f"Không tìm thấy mã sau {timeout}s",
                "elapsed": elapsed
            }), 408

    except Exception as e:
        return jsonify({
            "success": False,
            "code":    None,
            "error":   str(e),
            "elapsed": round(time.time() - t0, 2)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
