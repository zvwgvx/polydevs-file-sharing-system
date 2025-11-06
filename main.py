#!/usr/bin/env python3
"""
Modern Flask File Sharing App
- Password-protected file listing
- Beautiful, responsive UI
- View and download files from the same directory
- Access control via allowed_files.txt
"""

import os
import mimetypes
from flask import Flask, request, session, redirect, url_for, send_from_directory, abort, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------- Configuration ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASSWORD = os.environ.get("SHARE_PW", "changeme")
PASSWORD_HASH = generate_password_hash(PASSWORD)
SECRET_KEY = os.environ.get("FLASK_SECRET") or os.urandom(24)
ALLOWED_FILES_CONFIG = os.path.join(BASE_DIR, "allowed_files.txt")
# ------------------------------------------------

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Minimalist Router-Style CSS
COMMON_STYLE = """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: Arial, sans-serif;
        background: #ffffff;
        color: #000000;
        line-height: 1.4;
        padding: 0;
        margin: 0;
    }

    .header-bar {
        background: #000000;
        color: #ffffff;
        padding: 12px 20px;
        border-bottom: 2px solid #000000;
    }

    .header-bar h1 {
        font-size: 16px;
        font-weight: normal;
        display: inline-block;
    }

    .header-bar .logout {
        float: right;
        color: #ffffff;
        text-decoration: none;
        font-size: 13px;
        border: 1px solid #ffffff;
        padding: 4px 12px;
    }

    .header-bar .logout:hover {
        background: #ffffff;
        color: #000000;
    }

    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }

    .section {
        border: 1px solid #000000;
        margin-bottom: 20px;
        background: #ffffff;
    }

    .section-header {
        background: #f5f5f5;
        padding: 10px 15px;
        border-bottom: 1px solid #000000;
        font-weight: bold;
        font-size: 14px;
    }

    .section-content {
        padding: 15px;
    }

    input[type="password"] {
        width: 100%;
        padding: 8px;
        border: 1px solid #000000;
        font-size: 14px;
        font-family: Arial, sans-serif;
    }

    input[type="password"]:focus {
        outline: 2px solid #000000;
    }

    button, .btn {
        background: #ffffff;
        color: #000000;
        padding: 8px 20px;
        border: 1px solid #000000;
        font-size: 13px;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
        font-family: Arial, sans-serif;
    }

    button:hover, .btn:hover {
        background: #000000;
        color: #ffffff;
    }

    button:active, .btn:active {
        background: #333333;
    }

    .error {
        background: #000000;
        color: #ffffff;
        padding: 10px 15px;
        margin-bottom: 15px;
        font-size: 13px;
    }

    .path {
        background: #f5f5f5;
        padding: 8px 12px;
        border: 1px solid #000000;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        margin-bottom: 15px;
    }

    .back-link {
        display: inline-block;
        color: #000000;
        text-decoration: none;
        margin-bottom: 15px;
        font-size: 13px;
        border-bottom: 1px solid #000000;
    }

    .back-link:hover {
        border-bottom: 2px solid #000000;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #000000;
    }

    thead {
        background: #f5f5f5;
    }

    th {
        padding: 10px;
        text-align: left;
        font-weight: bold;
        font-size: 13px;
        border: 1px solid #000000;
    }

    td {
        padding: 10px;
        border: 1px solid #000000;
        font-size: 13px;
    }

    tbody tr:hover {
        background: #f5f5f5;
    }

    .action-link {
        color: #000000;
        text-decoration: underline;
        margin: 0 8px 0 0;
        font-size: 13px;
    }

    .action-link:hover {
        text-decoration: none;
    }

    .empty-state {
        text-align: center;
        padding: 40px 20px;
        border: 1px dashed #000000;
        font-size: 13px;
    }

    .content-viewer {
        background: #ffffff;
        border: 1px solid #000000;
        padding: 15px;
        overflow-x: auto;
        margin-top: 15px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.6;
        max-height: 500px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    .no-preview {
        text-align: center;
        padding: 40px 20px;
        border: 1px dashed #000000;
    }

    .no-preview-icon {
        font-size: 32px;
        margin-bottom: 15px;
    }

    .form-group {
        margin-bottom: 15px;
    }

    label {
        display: block;
        margin-bottom: 5px;
        font-size: 13px;
        font-weight: bold;
    }

    .warning-banner {
        background: #fff3cd;
        border: 1px solid #000000;
        padding: 10px 15px;
        margin-bottom: 15px;
        font-size: 13px;
        color: #856404;
    }

    @media (max-width: 768px) {
        .container {
            padding: 10px;
        }

        .header-bar h1 {
            font-size: 14px;
        }

        table {
            font-size: 12px;
        }

        th, td {
            padding: 8px 5px;
        }
    }
</style>
"""

LOGIN_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - File Share</title>
    """ + COMMON_STYLE + """
</head>
<body>
    <div class="header-bar">
        <h1>Polydevs File Sharing System - PFSS</h1>
    </div>
    <div class="container">
        <div class="section">
            <div class="section-header">Authentication Required</div>
            <div class="section-content">
                {% if error %}
                <div class="error">{{ error }}</div>
                {% endif %}
                <form method="post">
                    <div class="form-group">
                        <label>Password:</label>
                        <input type="password" name="pw" required autofocus>
                    </div>
                    <button type="submit">Login</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

LIST_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Polydevs File Sharing System - PFSS</title>
    """ + COMMON_STYLE + """
</head>
<body>
    <div class="header-bar">
        <h1>Polydevs File Sharing System - PFSS</h1>
        <a href="{{ url_for('logout') }}" class="logout">Logout</a>
    </div>
    <div class="container">
        {% if not config_exists %}
        <div class="warning-banner">
            ⚠️ Cảnh báo: File cấu hình allowed_files.txt không tồn tại. Tất cả files đều bị chặn truy cập.
        </div>
        {% endif %}

        <div class="section">
            <div class="section-header">Directory Listing</div>
            <div class="section-content">
                <div class="path">{{ base_dir }}</div>

                {% if items %}
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for it in items %}
                        <tr>
                            <td>{{ it.name }}</td>
                            <td>{{ it.type }}</td>
                            <td>
                                {% if it.type == 'File' %}
                                    <a href="{{ url_for('view_file', filename=it.name) }}" class="action-link">View</a>
                                    <a href="{{ url_for('download_file', filename=it.name) }}" class="action-link">Download</a>
                                {% elif it.type == 'Folder' %}
                                    <a href="{{ url_for('list_sub', name=it.name) }}" class="action-link">Open</a>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty-state">No files found</div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

DIR_LIST_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ dirname }} - Polydevs File Sharing System - PFSS</title>
    """ + COMMON_STYLE + """
</head>
<body>
    <div class="header-bar">
        <h1>Polydevs File Sharing System - PFSS - {{ dirname }}</h1>
        <a href="{{ url_for('logout') }}" class="logout">Logout</a>
    </div>
    <div class="container">
        <a href="{{ url_for('list_root') }}" class="back-link">&laquo; Back to root directory</a>

        <div class="section">
            <div class="section-header">Folder Contents</div>
            <div class="section-content">
                {% if items %}
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for it in items %}
                        <tr>
                            <td>{{ it.name }}</td>
                            <td>{{ it.type }}</td>
                            <td>
                                {% if it.type == 'File' %}
                                    <a href="{{ url_for('view_sub_file', folder=dirname, filename=it.name) }}" class="action-link">View</a>
                                    <a href="{{ url_for('download_sub_file', folder=dirname, filename=it.name) }}" class="action-link">Download</a>
                                {% else %}
                                    <span style="color: #999;">Subfolder</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty-state">No files found</div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

TEXT_VIEW_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ filename }} - File Viewer</title>
    """ + COMMON_STYLE + """
</head>
<body>
    <div class="header-bar">
        <h1>File Viewer - {{ filename }}</h1>
        <a href="{{ url_for('logout') }}" class="logout">Logout</a>
    </div>
    <div class="container">
        <a href="{{ url_for('list_root') }}" class="back-link">&laquo; Back to file list</a>

        <div class="section">
            <div class="section-header">File Contents</div>
            <div class="section-content">
                <div class="content-viewer">{{ content }}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

NO_PREVIEW_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ filename }} - Preview Unavailable</title>
    """ + COMMON_STYLE + """
</head>
<body>
    <div class="header-bar">
        <h1>File Viewer - {{ filename }}</h1>
        <a href="{{ url_for('logout') }}" class="logout">Logout</a>
    </div>
    <div class="container">
        <a href="{{ url_for('list_root') }}" class="back-link">&laquo; Back to file list</a>

        <div class="section">
            <div class="section-header">Preview Not Available</div>
            <div class="section-content">
                <div class="no-preview">
                    <p>This file type cannot be previewed in the browser.</p>
                    <br>
                    <a href="{{ download_url }}" class="btn">Download File</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


# ---------------- Access Control ----------------
def load_allowed_items():
    """
    Đọc file allowed_files.txt và trả về set các đường dẫn được phép.
    Format trong file:
    - file.txt (file ở root)
    - folder/ (folder ở root - cho phép truy cập folder)
    - folder/file.txt (file trong folder)
    """
    allowed = set()
    if not os.path.exists(ALLOWED_FILES_CONFIG):
        print(f"WARNING: {ALLOWED_FILES_CONFIG} không tồn tại!")
        return allowed

    try:
        with open(ALLOWED_FILES_CONFIG, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Bỏ qua dòng trống và comment
                if line and not line.startswith('#'):
                    # Chuẩn hóa đường dẫn
                    line = line.replace('\\', '/')
                    allowed.add(line)
        print(f"Loaded {len(allowed)} allowed items from {ALLOWED_FILES_CONFIG}")
    except Exception as e:
        print(f"ERROR reading {ALLOWED_FILES_CONFIG}: {e}")

    return allowed


def is_allowed(path):
    """
    Kiểm tra xem một đường dẫn có được phép truy cập không.
    path: đường dẫn tương đối, ví dụ: "file.txt" hoặc "folder/file.txt"
    """
    allowed_items = load_allowed_items()

    # Nếu file config không tồn tại hoặc rỗng, chặn tất cả
    if not allowed_items:
        return False

    # Chuẩn hóa path
    path = path.replace('\\', '/')

    # Kiểm tra chính xác
    if path in allowed_items:
        return True

    # Nếu là folder, kiểm tra có trailing slash
    if path + '/' in allowed_items:
        return True

    # Kiểm tra xem folder cha có được phép không (cho phép list folder)
    parts = path.split('/')
    if len(parts) > 1:
        folder = parts[0]
        if folder + '/' in allowed_items:
            return True

    return False


def filter_allowed_items(entries, parent_path=""):
    """
    Lọc danh sách entries chỉ giữ lại những items được phép.
    entries: list các dict {'name': ..., 'type': ...}
    parent_path: đường dẫn folder cha (nếu có)
    """
    filtered = []
    for entry in entries:
        if parent_path:
            path = f"{parent_path}/{entry['name']}"
        else:
            path = entry['name']

        # Nếu là folder, thêm trailing slash để check
        if entry['type'] == 'Folder':
            if is_allowed(path) or is_allowed(path + '/'):
                filtered.append(entry)
        else:
            if is_allowed(path):
                filtered.append(entry)

    return filtered


# ------------------------------------------------

# ---------------- Helpers ----------------
def require_login():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return None


def is_direct_child(path):
    """Ensure path is a direct child of BASE_DIR."""
    real = os.path.realpath(path)
    if not real.startswith(BASE_DIR + os.sep) and real != BASE_DIR:
        return False
    return os.path.dirname(real) == BASE_DIR


def is_child_under(folder, name):
    """Ensure folder is direct child of BASE_DIR, and name is direct child of that folder."""
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.isdir(folder_path):
        return False
    real_folder = os.path.realpath(folder_path)
    if os.path.dirname(real_folder) != BASE_DIR:
        return False
    candidate = os.path.join(real_folder, name)
    real_candidate = os.path.realpath(candidate)
    return os.path.dirname(real_candidate) == real_folder


# -----------------------------------------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("pw", "")
        if check_password_hash(PASSWORD_HASH, pw):
            session["logged_in"] = True
            return redirect(url_for("list_root"))
        else:
            return render_template_string(LOGIN_HTML, error="Incorrect password. Please try again.")

    if session.get("logged_in"):
        return redirect(url_for("list_root"))
    return render_template_string(LOGIN_HTML, error=None)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/list")
def list_root():
    if (r := require_login()) is not None:
        return r
    entries = []
    for name in sorted(os.listdir(BASE_DIR)):
        # Bỏ qua file cấu hình
        if name == "allowed_files.txt":
            continue
        path = os.path.join(BASE_DIR, name)
        entries.append({
            "name": name,
            "type": "File" if os.path.isfile(path) else "Folder" if os.path.isdir(path) else "Other"
        })

    # Lọc chỉ hiển thị items được phép
    entries = filter_allowed_items(entries)

    config_exists = os.path.exists(ALLOWED_FILES_CONFIG)
    return render_template_string(LIST_HTML, items=entries, base_dir=BASE_DIR, config_exists=config_exists)


@app.route("/list/<name>")
def list_sub(name):
    if (r := require_login()) is not None:
        return r
    if "/" in name or "\\" in name:
        abort(400)

    # Kiểm tra quyền truy cập folder
    if not is_allowed(name) and not is_allowed(name + '/'):
        abort(403)

    folder_path = os.path.join(BASE_DIR, name)
    if not is_direct_child(folder_path) or not os.path.isdir(folder_path):
        abort(404)

    entries = []
    for child in sorted(os.listdir(folder_path)):
        child_path = os.path.join(folder_path, child)
        entries.append({
            "name": child,
            "type": "File" if os.path.isfile(child_path) else "Folder" if os.path.isdir(child_path) else "Other"
        })

    # Lọc chỉ hiển thị items được phép
    entries = filter_allowed_items(entries, parent_path=name)

    return render_template_string(DIR_LIST_HTML, items=entries, dirname=name)


@app.route("/view/<filename>")
def view_file(filename):
    if (r := require_login()) is not None:
        return r
    if "/" in filename or "\\" in filename:
        abort(400)

    # Kiểm tra quyền truy cập
    if not is_allowed(filename):
        abort(403)

    file_path = os.path.join(BASE_DIR, filename)
    if not is_direct_child(file_path) or not os.path.isfile(file_path):
        abort(404)
    mime, _ = mimetypes.guess_type(file_path)

    if mime and mime.startswith("text"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            content = f"Unable to read file: {e}"
        return render_template_string(TEXT_VIEW_HTML, filename=filename, content=content)
    elif mime and mime.startswith("image"):
        return send_from_directory(BASE_DIR, filename, as_attachment=False)
    else:
        return render_template_string(NO_PREVIEW_HTML,
                                      filename=filename,
                                      download_url=url_for('download_file', filename=filename))


@app.route("/download/<filename>")
def download_file(filename):
    if (r := require_login()) is not None:
        return r
    if "/" in filename or "\\" in filename:
        abort(400)

    # Kiểm tra quyền truy cập
    if not is_allowed(filename):
        abort(403)

    file_path = os.path.join(BASE_DIR, filename)
    if not is_direct_child(file_path) or not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(BASE_DIR, filename, as_attachment=True)


@app.route("/view/<folder>/<filename>")
def view_sub_file(folder, filename):
    if (r := require_login()) is not None:
        return r
    if "/" in folder or "\\" in folder or "/" in filename or "\\" in filename:
        abort(400)

    # Kiểm tra quyền truy cập
    file_path_relative = f"{folder}/{filename}"
    if not is_allowed(file_path_relative):
        abort(403)

    if not is_child_under(folder, filename):
        abort(404)
    folder_path = os.path.join(BASE_DIR, folder)
    file_path = os.path.join(folder_path, filename)
    mime, _ = mimetypes.guess_type(file_path)

    if mime and mime.startswith("text"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            content = f"Unable to read file: {e}"
        return render_template_string(TEXT_VIEW_HTML, filename=f"{folder}/{filename}", content=content)
    elif mime and mime.startswith("image"):
        return send_from_directory(folder_path, filename, as_attachment=False)
    else:
        return render_template_string(NO_PREVIEW_HTML,
                                      filename=f"{folder}/{filename}",
                                      download_url=url_for('download_sub_file', folder=folder, filename=filename))


@app.route("/download/<folder>/<filename>")
def download_sub_file(folder, filename):
    if (r := require_login()) is not None:
        return r
    if "/" in folder or "\\" in folder or "/" in filename or "\\" in filename:
        abort(400)

    # Kiểm tra quyền truy cập
    file_path_relative = f"{folder}/{filename}"
    if not is_allowed(file_path_relative):
        abort(403)

    if not is_child_under(folder, filename):
        abort(404)
    folder_path = os.path.join(BASE_DIR, folder)
    return send_from_directory(folder_path, filename, as_attachment=True)


if __name__ == "__main__":
    print("Polydevs File Sharing System")
    print(f"Directory: {BASE_DIR}")
    print(f"Password: {PASSWORD}")
    print(f"Access Control: {ALLOWED_FILES_CONFIG}")
    print("Address: http://0.0.0.0:80")
    print("Note: Port 80 requires root/admin")
    app.run(host="0.0.0.0", port=80, debug=False)