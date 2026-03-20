from flask import Flask, Response, request
import requests
import re
import time
from html.parser import HTMLParser

app = Flask(__name__)

BASE = "https://api.mail.tm"

# ── Pattern mặc định ──────────────────────────────────────────────────────────
CODE_PATTERNS = [
    r'\b[A-Z0-9]{3,8}-[A-Z0-9]{3,8}\b',   # XXX-XXX  (ưu tiên — theo yêu cầu)
    r'\b[A-Z0-9]{3}-[A-Z0-9]{3}\b',         # ABC-123  (3-3)
    r'\b\d{6}\b',                            # 123456
    r'\b\d{4}\b',                            # 1234
    r'\b[A-Z0-9]{8}\b',                      # AB12CD34
]


# ── Strip HTML đơn giản ───────────────────────────────────────────────────────
class _MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return " ".join(self.fed)


def strip_html(html: str) -> str:
    s = _MLStripper()
    s.feed(html)
    return re.sub(r"\s{2,}", " ", s.get_data()).strip()


# ── Helpers ───────────────────────────────────────────────────────────────────
def download_txt(content: str, filename: str = "result.txt"):
    return Response(
        response=content,
        status=200,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


def get_token(email: str, password: str) -> str:
    res = requests.post(f"{BASE}/token", json={
        "address": email,
        "password": password
    }, timeout=10)
    res.raise_for_status()
    token = res.json().get("token")
    if not token:
        raise Exception("Không lấy được token — kiểm tra lại email/password")
    return token


def extract_code(text: str, patterns: list):
    """Trả về code đầu tiên khớp, ưu tiên theo thứ tự patterns."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0).upper()
    return None


def format_mail_result(mail: dict, patterns: list) -> str:
    """
    Trả về chuỗi đầy đủ:
      - Metadata: from, subject, date
      - Nội dung mail
      - Code nếu tìm được, ngược lại: 'không đọc được code'
    """
    divider  = "=" * 60
    thin     = "-" * 60

    # Metadata
    from_    = mail.get("from", {}).get("address", "(không rõ)")
    subject  = mail.get("subject", "(không có tiêu đề)")
    date_raw = mail.get("createdAt", "")

    # Body: ưu tiên text, fallback HTML
    body_text = mail.get("text", "").strip()
    html_parts = mail.get("html", []) or []
    html_text  = strip_html(" ".join(html_parts)).strip() if html_parts else ""
    body       = body_text if body_text else html_text or "(email không có nội dung)"

    # Tìm code
    combined = body_text + " " + html_text
    code     = extract_code(combined, patterns)

    lines = [
        divider,
        f"📅 Ngày   : {date_raw}",
        f"👤 Từ     : {from_}",
        f"📌 Tiêu đề: {subject}",
        thin,
        "📄 Nội dung:",
        body,
        thin,
    ]

    if code:
        lines.append(f"🔑 Code   : {code}")
    else:
        lines.append("⚠️  Không đọc được code (không tìm thấy định dạng XXX-XXX)")

    lines.append(divider)
    return "\n".join(lines)


# ── HTML giao diện (giữ nguyên style, chỉ cập nhật mô tả) ────────────────────
HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Get Code API</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:#0f0f1a;color:#e0e0f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
    .wrap{width:100%;max-width:680px}
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
    pre{background:#0f0f1a;border:1px solid #2d2d5e;border-radius:8px;padding:14px;font-size:.83rem;color:#d1d5db;white-space:pre-wrap;min-height:54px;margin-top:12px}
    .lbl{font-size:.8rem;color:#6b7280;margin:8px 0 6px;display:block}
    .spin{display:inline-block;animation:spin 1s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
    .dl-btn{display:none;width:100%;margin-top:10px;padding:10px;background:linear-gradient(135deg,#1e3a5f,#1e40af);color:#fff;border:none;border-radius:9px;font-size:.9rem;cursor:pointer;font-weight:600}
    .dl-btn:hover{opacity:.85}
  </style>
</head>
<body>
<div class="wrap">
  <h1>🔍 Get Code API</h1>
  <p class="sub">Nhận <code>email + password</code> → chờ mail → download <code>get-code.txt</code> chứa nội dung mail + mã xác nhận</p>

  <div class="card">
    <h2>🔌 Endpoint</h2>
    <div class="ep">
      <span class="badge-get">GET</span>/api/get-code?email=...&amp;password=...<br/>
      <span class="badge-post" style="margin-top:8px;display:inline-block">POST</span>/api/get-code &nbsp;→ body JSON: <code>{"email","password","timeout","pattern"}</code>
    </div>
    <table>
      <tr><th>Tham số</th><th>Nơi truyền</th><th>Mặc định</th><th>Mô tả</th></tr>
      <tr><td>email <span class="req">*</span></td><td>query / body</td><td>—</td><td>Địa chỉ email tạm</td></tr>
      <tr><td>password <span class="req">*</span></td><td>query / body</td><td>—</td><td>Mật khẩu tài khoản</td></tr>
      <tr><td>timeout</td><td>query / body</td><td>120</td><td>Thời gian chờ tối đa (giây)</td></tr>
      <tr><td>interval</td><td>query / body</td><td>5</td><td>Khoảng cách giữa mỗi lần check (giây)</td></tr>
      <tr><td>pattern</td><td>query / body</td><td>—</td><td>Regex tuỳ chỉnh để bắt mã</td></tr>
    </table>
  </div>

  <div class="card">
    <h2>📤 Nội dung file <code>get-code.txt</code></h2>
    <table>
      <tr><th>Trường hợp</th><th>Nội dung</th></tr>
      <tr><td>Tìm được code</td><td>Nội dung mail đầy đủ + <code>🔑 Code: ABC-123</code></td></tr>
      <tr><td>Không có code</td><td>Nội dung mail đầy đủ + <code>⚠️ Không đọc được code</code></td></tr>
      <tr><td>Timeout / lỗi</td><td><code>error|Không tìm thấy mail sau 120s</code></td></tr>
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
    <button id="btn" onclick="run()">🔍 Chờ & Download TXT</button>
    <span class="lbl" id="lbl"></span>
    <pre id="out">// Nội dung file sẽ hiển thị ở đây...</pre>
    <a id="dlLink" style="display:none"><button class="dl-btn" id="dlBtn">⬇️ Download get-code.txt</button></a>
  </div>

  <div class="card">
    <h2>💡 Ví dụ gọi API</h2>
    <pre># cURL GET — tự download file
curl -OJ "https://read-otp.vercel.app/api/get-code?email=abc@mail.tm&password=Pass1234!&timeout=60"

# cURL POST
curl -X POST "https://read-otp.vercel.app/api/get-code" \\
  -H "Content-Type: application/json" \\
  -d '{"email":"abc@mail.tm","password":"Pass1234!","timeout":60}' \\
  -OJ

# Python
import requests
r = requests.post("https://read-otp.vercel.app/api/get-code", json={
    "email": "abc@mail.tm",
    "password": "Pass1234!",
    "timeout": 60
})
print(r.text)
# ============================================================
# 📅 Ngày   : 2025-01-01T12:00:00+00:00
# 👤 Từ     : noreply@example.com
# 📌 Tiêu đề: Your verification code
# ------------------------------------------------------------
# 📄 Nội dung:
# Your code is ABC-123. It expires in 10 minutes.
# ------------------------------------------------------------
# 🔑 Code   : ABC-123
# ============================================================</pre>
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

    if (!email || !password) { lbl.textContent = '⚠️ Vui lòng nhập email và password'; return; }

    btn.disabled = true;
    document.getElementById('dlLink').style.display = 'none';
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
      const blob = await res.blob();
      const text = (await blob.text()).trim();
      clearInterval(timer);

      const isError = text.startsWith('error|');
      lbl.textContent = isError
        ? '❌ ' + text.replace('error|', '')
        : text.includes('🔑') ? '✅ Tìm được code!' : '⚠️ Nhận mail nhưng không có code XXX-XXX';
      out.textContent = text;

      if (!isError) {
        const url = URL.createObjectURL(blob);
        const link = document.getElementById('dlLink');
        link.href = url; link.download = 'get-code.txt'; link.style.display = 'block';
        document.getElementById('dlBtn').style.display = 'block';
      }
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


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return HTML


@app.route('/api/get-code', methods=['GET', 'POST'])
def get_code():
    """
    Poll inbox → trả về nội dung mail + code (nếu có) dưới dạng file TXT.

    Response: file get-code.txt
      Thành công  : nội dung mail đầy đủ + "🔑 Code: XXX-XXX"
      Không code  : nội dung mail đầy đủ + "⚠️ Không đọc được code"
      Timeout/lỗi : "error|<message>"
    """
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

    if not email or not password:
        return download_txt("error|Thiếu tham số bắt buộc: email và password")

    timeout  = max(10, min(timeout, 300))
    interval = max(2,  min(interval, 30))
    patterns = [custom_pattern] if custom_pattern else CODE_PATTERNS

    try:
        token   = get_token(email, password)
        headers = {"Authorization": f"Bearer {token}"}
        seen    = set()          # tránh xử lý lại mail cũ
        results = []             # tập hợp kết quả từng mail mới
        deadline = time.time() + timeout

        while time.time() < deadline:
            msg_res = requests.get(f"{BASE}/messages", headers=headers, timeout=10)
            msg_res.raise_for_status()
            members = msg_res.json().get("hydra:member", [])

            new_found = False
            for msg in members:
                mid = msg["id"]
                if mid in seen:
                    continue
                seen.add(mid)
                new_found = True

                detail = requests.get(f"{BASE}/messages/{mid}", headers=headers, timeout=10)
                detail.raise_for_status()
                mail = detail.json()

                results.append(format_mail_result(mail, patterns))

            # Ngay khi có mail mới → trả về luôn, không chờ timeout
            if new_found and results:
                break

            time.sleep(interval)

        if results:
            content = "\n\n".join(results)
            return download_txt(content, "get-code.txt")
        else:
            return download_txt(
                f"error|Không tìm thấy mail nào sau {timeout}s",
                "get-code.txt"
            )

    except Exception as e:
        return download_txt(f"error|{str(e)}", "get-code.txt")


if __name__ == '__main__':
    app.run(debug=True)
