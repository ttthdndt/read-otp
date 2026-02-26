from flask import Flask, jsonify
import requests
import random
import string

app = Flask(__name__)

BASE = "https://api.mail.tm"


def random_username(length=12):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Create Mail API</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:#0f0f1a;color:#e0e0f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
    .wrap{width:100%;max-width:620px}
    h1{font-size:1.7rem;color:#a78bfa;text-align:center;margin-bottom:6px}
    .sub{text-align:center;color:#6b7280;margin-bottom:32px;font-size:.93rem}
    .card{background:#1a1a2e;border:1px solid #2d2d5e;border-radius:14px;padding:26px;margin-bottom:18px}
    h2{font-size:.95rem;color:#a78bfa;margin-bottom:14px}
    .ep{background:#0f0f1a;border:1px solid #2d2d5e;border-radius:8px;padding:12px 16px;font-family:monospace;font-size:.9rem;color:#7dd3fc;margin-bottom:14px}
    .badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700;margin-right:6px;background:#065f46;color:#6ee7b7}
    table{width:100%;border-collapse:collapse;font-size:.87rem}
    th{text-align:left;color:#6b7280;padding:5px 8px;border-bottom:1px solid #2d2d5e}
    td{padding:8px;border-bottom:1px solid #1e1e3a;vertical-align:top}
    td:first-child{font-family:monospace;color:#f9a8d4;white-space:nowrap}
    button{width:100%;padding:13px;background:linear-gradient(135deg,#7c3aed,#4f46e5);color:#fff;border:none;border-radius:9px;font-size:.95rem;cursor:pointer;font-weight:600;transition:opacity .2s}
    button:hover{opacity:.85}
    button:disabled{opacity:.45;cursor:not-allowed}
    pre{background:#0f0f1a;border:1px solid #2d2d5e;border-radius:8px;padding:14px;font-size:.83rem;color:#d1d5db;white-space:pre-wrap;word-break:break-all;min-height:54px;margin-top:12px}
    .lbl{font-size:.8rem;color:#6b7280;margin-bottom:6px;display:block}
  </style>
</head>
<body>
<div class="wrap">
  <h1>✉️ Create Mail API</h1>
  <p class="sub">Tạo email tạm thời — trả về <code>email</code> và <code>password</code></p>

  <div class="card">
    <h2>🔌 Endpoint</h2>
    <div class="ep"><span class="badge">GET</span>/api/create-mail</div>
    <table>
      <tr><th>Field</th><th>Kiểu</th><th>Mô tả</th></tr>
      <tr><td>success</td><td>bool</td><td>true nếu tạo thành công</td></tr>
      <tr><td>email</td><td>string</td><td>Địa chỉ email vừa tạo</td></tr>
      <tr><td>password</td><td>string</td><td>Mật khẩu tài khoản</td></tr>
      <tr><td>error</td><td>string</td><td>Thông báo lỗi (nếu có)</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>🧪 Thử ngay</h2>
    <button id="btn" onclick="run()">⚡ Tạo Email mới</button>
    <span class="lbl" id="lbl" style="margin-top:10px"></span>
    <pre id="out">// Kết quả hiển thị ở đây...</pre>
  </div>

  <div class="card">
    <h2>💡 Ví dụ gọi API</h2>
    <pre># cURL
curl "https://your-create-mail-app.vercel.app/api/create-mail"

# Python
import requests
r = requests.get("https://your-create-mail-app.vercel.app/api/create-mail")
data = r.json()
print(data["email"], data["password"])

# JavaScript
const res = await fetch("/api/create-mail");
const { email, password } = await res.json();</pre>
  </div>
</div>
<script>
  async function run() {
    const btn = document.getElementById('btn');
    const out = document.getElementById('out');
    const lbl = document.getElementById('lbl');
    btn.disabled = true;
    lbl.textContent = '⏳ Đang tạo...';
    try {
      const res = await fetch('/api/create-mail');
      const data = await res.json();
      lbl.textContent = data.success ? '✅ Tạo thành công!' : '❌ Thất bại';
      out.textContent = JSON.stringify(data, null, 2);
    } catch(e) {
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


@app.route('/api/create-mail', methods=['GET'])
def create_mail():
    """
    Tạo một tài khoản email tạm thời trên mail.tm.

    Response JSON:
      success  : bool
      email    : string — địa chỉ email
      password : string — mật khẩu
      error    : string — chỉ có khi thất bại
    """
    try:
        # 1. Lấy domain khả dụng
        domain_res = requests.get(f"{BASE}/domains", timeout=10)
        domain_res.raise_for_status()
        domain = domain_res.json()["hydra:member"][0]["domain"]

        # 2. Tạo thông tin tài khoản
        address  = f"{random_username()}@{domain}"
        password = "Pass1234!"

        # 3. Đăng ký tài khoản
        acc_res = requests.post(f"{BASE}/accounts", json={
            "address":  address,
            "password": password
        }, timeout=10)

        if acc_res.status_code not in (200, 201):
            return jsonify({
                "success": False,
                "error": f"Tạo tài khoản thất bại ({acc_res.status_code}): {acc_res.text}"
            }), 400

        return jsonify({
            "success":  True,
            "email":    address,
            "password": password
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error":   str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
