from flask import Flask, jsonify, request, render_template_string
import requests
import random
import string
import re
import time

app = Flask(__name__)

BASE = "https://api.mail.tm"

# ─── Regex patterns để bắt mã xác nhận ───────────────────────────────────────
# Thêm / bớt pattern tuỳ theo site bạn dùng
CODE_PATTERNS = [
    r'\b[A-Z0-9]{3}-[A-Z0-9]{3}\b',   # ABC-123
    r'\b\d{6}\b',                        # 123456
    r'\b\d{4}\b',                        # 1234
    r'\b[A-Z0-9]{8}\b',                 # AB12CD34
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def random_username(length=12):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def create_account():
    domain_res = requests.get(f"{BASE}/domains", timeout=10)
    domain_res.raise_for_status()
    domain = domain_res.json()["hydra:member"][0]["domain"]

    address = f"{random_username()}@{domain}"
    password = "Pass1234!"

    acc_res = requests.post(f"{BASE}/accounts", json={
        "address": address,
        "password": password
    }, timeout=10)

    if acc_res.status_code not in (200, 201):
        raise Exception(f"Tạo tài khoản thất bại ({acc_res.status_code}): {acc_res.text}")

    return address, password


def get_token(address, password):
    res = requests.post(f"{BASE}/token", json={
        "address": address,
        "password": password
    }, timeout=10)
    res.raise_for_status()
    token = res.json().get("token")
    if not token:
        raise Exception("Không lấy được token")
    return token


# ─── Routes ───────────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Temp Mail API</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:#0f0f1a;color:#e0e0f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
    .wrap{width:100%;max-width:680px}
    h1{font-size:1.8rem;color:#a78bfa;text-align:center;margin-bottom:6px}
    .sub{text-align:center;color:#6b7280;margin-bottom:36px;font-size:.95rem}
    .card{background:#1a1a2e;border:1px solid #2d2d5e;border-radius:14px;padding:28px;margin-bottom:20px}
    h2{font-size:1rem;color:#a78bfa;margin-bottom:16px;display:flex;align-items:center;gap:8px}
    .endpoint{background:#0f0f1a;border:1px solid #2d2d5e;border-radius:8px;padding:14px 16px;font-family:monospace;font-size:.9rem;color:#7dd3fc;margin-bottom:12px}
    .badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.75rem;font-weight:700;margin-right:8px}
    .get{background:#065f46;color:#6ee7b7}
    .post{background:#1e3a5f;color:#7dd3fc}
    table{width:100%;border-collapse:collapse;font-size:.88rem}
    th{text-align:left;color:#6b7280;padding:6px 8px;border-bottom:1px solid #2d2d5e}
    td{padding:8px;border-bottom:1px solid #1e1e3a;vertical-align:top}
    td:first-child{font-family:monospace;color:#f9a8d4;white-space:nowrap}
    .demo{margin-top:24px}
    .demo label{font-size:.8rem;color:#6b7280;display:block;margin-bottom:6px}
    .row{display:flex;gap:10px;margin-bottom:12px}
    input{flex:1;background:#0f0f1a;border:1px solid #2d2d5e;color:#e0e0f0;border-radius:8px;padding:10px 14px;font-size:.9rem;outline:none}
    input:focus{border-color:#7c3aed}
    button{padding:10px 20px;background:linear-gradient(135deg,#7c3aed,#4f46e5);color:#fff;border:none;border-radius:8px;font-size:.9rem;cursor:pointer;font-weight:600;transition:opacity .2s;white-space:nowrap}
    button:hover{opacity:.85}
    button:disabled{opacity:.45;cursor:not-allowed}
    pre{background:#0f0f1a;border:1px solid #2d2d5e;border-radius:8px;padding:16px;font-size:.83rem;overflow-x:auto;color:#d1d5db;white-space:pre-wrap;word-break:break-all;min-height:60px}
    .tag{font-size:.72rem;color:#9ca3af;background:#1e1e3a;padding:2px 8px;border-radius:4px;margin-left:6px}
    .spin{display:inline-block;animation:spin 1s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
  </style>
</head>
<body>
<div class="wrap">
  <h1>📬 Temp Mail API</h1>
  <p class="sub">Một endpoint duy nhất — tự tạo mail, tự chờ, tự đọc, trả về mã xác nhận</p>

  <div class="card">
    <h2>🔌 Endpoint</h2>
    <div class="endpoint">
      <span class="badge get">GET</span>/api/get-code
      &nbsp;|&nbsp;
      <span class="badge post">POST</span>/api/get-code
    </div>
    <table>
      <tr><th>Tham số</th><th>Nơi truyền</th><th>Mặc định</th><th>Mô tả</th></tr>
      <tr><td>timeout</td><td>query / body</td><td>120</td><td>Thời gian tối đa chờ mail (giây)</td></tr>
      <tr><td>interval</td><td>query / body</td><td>5</td><td>Khoảng cách giữa các lần check (giây)</td></tr>
      <tr><td>pattern</td><td>query / body</td><td>—</td><td>Regex tuỳ chỉnh để bắt mã (tuỳ chọn)</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>📤 Response</h2>
    <table>
      <tr><th>Field</th><th>Kiểu</th><th>Mô tả</th></tr>
      <tr><td>success</td><td>bool</td><td>true nếu tìm được mã</td></tr>
      <tr><td>code</td><td>string</td><td>Mã xác nhận tìm được</td></tr>
      <tr><td>email</td><td>string</td><td>Địa chỉ email tạm đã dùng</td></tr>
      <tr><td>from</td><td>string</td><td>Người gửi mail</td></tr>
      <tr><td>subject</td><td>string</td><td>Tiêu đề mail</td></tr>
      <tr><td>elapsed</td><td>float</td><td>Thời gian xử lý (giây)</td></tr>
      <tr><td>error</td><td>string</td><td>Thông báo lỗi (nếu có)</td></tr>
    </table>
  </div>

  <div class="card demo">
    <h2>🧪 Thử ngay <span class="tag">live demo</span></h2>
    <div class="row">
      <input id="timeout" type="number" placeholder="timeout (s)" value="120" style="max-width:150px"/>
      <input id="pattern" type="text" placeholder="regex tuỳ chỉnh (tuỳ chọn)"/>
      <button id="runBtn" onclick="runDemo()">▶ Gọi API</button>
    </div>
    <label id="statusLbl"></label>
    <pre id="out">// Kết quả sẽ hiển thị ở đây...</pre>
  </div>

  <div class="card">
    <h2>💡 Ví dụ gọi API</h2>
    <pre># cURL
curl "https://your-app.vercel.app/api/get-code?timeout=60"

# Python
import requests
r = requests.get("https://your-app.vercel.app/api/get-code", params={"timeout": 60})
print(r.json())

# JavaScript / fetch
const res = await fetch("/api/get-code?timeout=60");
const data = await res.json();
console.log(data.code);</pre>
  </div>
</div>

<script>
  async function runDemo() {
    const btn = document.getElementById('runBtn');
    const out = document.getElementById('out');
    const lbl = document.getElementById('statusLbl');
    const timeout = document.getElementById('timeout').value || 120;
    const pattern = document.getElementById('pattern').value;

    btn.disabled = true;
    out.textContent = '// Đang xử lý...';
    const startTime = Date.now();

    const timer = setInterval(() => {
      const s = ((Date.now() - startTime) / 1000).toFixed(1);
      lbl.innerHTML = '<span class="spin">⏳</span> Đang chờ mail... ' + s + 's';
    }, 200);

    let params = 'timeout=' + timeout;
    if (pattern) params += '&pattern=' + encodeURIComponent(pattern);

    try {
      const res = await fetch('/api/get-code?' + params);
      const data = await res.json();
      clearInterval(timer);
      lbl.textContent = data.success ? '✅ Thành công sau ' + data.elapsed + 's' : '❌ Thất bại sau ' + data.elapsed + 's';
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
    return render_template_string(HTML)


@app.route('/api/get-code', methods=['GET', 'POST'])
def get_code():
    """
    All-in-one endpoint:
      1. Tạo email tạm thời trên mail.tm
      2. Đăng nhập lấy JWT token
      3. Poll hộp thư đến khi nhận được mail
      4. Dùng regex trích xuất mã xác nhận
      5. Trả về JSON

    Params (query string cho GET, JSON body cho POST):
      timeout  : int  — giây chờ tối đa, mặc định 120, tối đa 300
      interval : int  — giây giữa mỗi lần check, mặc định 5
      pattern  : str  — regex tuỳ chỉnh (override CODE_PATTERNS)
    """
    t0 = time.time()

    if request.method == 'POST':
        body = request.get_json(silent=True) or {}
        timeout        = int(body.get('timeout', 120))
        interval       = int(body.get('interval', 5))
        custom_pattern = body.get('pattern', None)
    else:
        timeout        = int(request.args.get('timeout', 120))
        interval       = int(request.args.get('interval', 5))
        custom_pattern = request.args.get('pattern', None)

    timeout  = max(10, min(timeout, 300))
    interval = max(2,  min(interval, 30))
    patterns = [custom_pattern] if custom_pattern else CODE_PATTERNS

    try:
        # 1. Tạo tài khoản
        address, password = create_account()

        # 2. Lấy token
        token = get_token(address, password)

        # 3 & 4. Poll + trích mã
        headers  = {"Authorization": f"Bearer {token}"}
        deadline = time.time() + timeout
        code = subject = sender = None

        while time.time() < deadline:
            msg_res = requests.get(f"{BASE}/messages", headers=headers, timeout=10)
            msg_res.raise_for_status()
            members = msg_res.json().get("hydra:member", [])

            for msg in members:
                detail = requests.get(f"{BASE}/messages/{msg['id']}", headers=headers, timeout=10)
                detail.raise_for_status()
                mail = detail.json()

                text     = mail.get("text", "") or ""
                html_raw = " ".join(mail.get("html", []) or [])
                combined = text + " " + html_raw

                for pat in patterns:
                    m = re.search(pat, combined)
                    if m:
                        code    = m.group(0)
                        subject = mail.get("subject", "")
                        sender  = mail.get("from", {}).get("address", "")
                        break
                if code:
                    break
            if code:
                break

            time.sleep(interval)

        elapsed = round(time.time() - t0, 2)

        if code:
            return jsonify({
                "success": True,
                "code":    code,
                "email":   address,
                "from":    sender,
                "subject": subject,
                "elapsed": elapsed
            })
        else:
            return jsonify({
                "success": False,
                "code":    None,
                "email":   address,
                "error":   f"Không tìm thấy mã sau {timeout}s",
                "elapsed": elapsed
            }), 408

    except Exception as e:
        return jsonify({
            "success": False,
            "code":    None,
            "email":   None,
            "error":   str(e),
            "elapsed": round(time.time() - t0, 2)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
