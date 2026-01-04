import os
import json
import base64
import http.client
import ssl

# --- CONFIGURATION ---
TOKEN = os.getenv("GITHUB_TOKEN", "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")
REPO_NAME = "uce-asistan-saas"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
IGNORE_LIST = [
    ".git", ".gemini", "node_modules", ".vscode", "__pycache__", 
    ".Python", "env", "build", "dist", "uce_agent_env", ".antigravityignore"
]
# ---------------------

class GitHubAPI:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "User-Agent": "UceAsistan-Deployer",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json"
        }
        self.host = "api.github.com"
        self.context = ssl.create_default_context()

    def request(self, method, path, body=None):
        conn = http.client.HTTPSConnection(self.host, context=self.context)
        conn.request(method, path, body=json.dumps(body) if body else None, headers=self.headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        conn.close()
        return res.status, json.loads(data) if data else {}

    def get_user(self):
        status, data = self.request("GET", "/user")
        return data.get("login")

    def create_repo(self, repo_name):
        print(f"[i] Depo olusturuluyor: {repo_name}...")
        body = {
            "name": repo_name,
            "private": True,
            "description": "UceAsistan SaaS Platform - Automated Deployment"
        }
        status, data = self.request("POST", "/user/repos", body)
        if status == 201:
            print("[OK] Depo basariyla olusturuldu.")
        elif status == 422:
            print("[!] Depo zaten var, devam ediliyor.")
        else:
            print(f"[!] HATA (Repo Create): {status} {data}")

    def upload_file(self, user, repo, local_path, git_path):
        try:
            with open(local_path, "rb") as f:
                content = base64.b64encode(f.read()).decode("utf-8")
            
            # Check if file exists to get its SHA (needed for updates)
            status, data = self.request("GET", f"/repos/{user}/{repo}/contents/{git_path}")
            sha = data.get("sha") if status == 200 else None

            body = {
                "message": f"Upload {git_path}",
                "content": content
            }
            if sha:
                body["sha"] = sha

            print(f"[+] Yükleniyor: {git_path}...")
            status, data = self.request("PUT", f"/repos/{user}/{repo}/contents/{git_path}", body)
            return status in [200, 201]
        except Exception as e:
            print(f"[!] HATA (File {git_path}): {str(e)}")
            return False

def deploy():
    gh = GitHubAPI(TOKEN)
    username = gh.get_user()
    if not username:
        print("[!] GitHub yetkisi basarisiz!")
        return

    print(f"[OK] GitHub Girisi: {username}")
    gh.create_repo(REPO_NAME)

    total_uploaded = 0
    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_LIST]
        
        for file in files:
            if file.endswith((".pyc", ".log", ".tmp")): continue
            
            local_path = os.path.join(root, file)
            git_path = os.path.relpath(local_path, ROOT_DIR).replace("\\", "/")
            
            if gh.upload_file(username, REPO_NAME, local_path, git_path):
                total_uploaded += 1

    print("-" * 30)
    print(f"[Done] Toplam {total_uploaded} dosya yüklendi!")
    print(f"URL: https://github.com/{username}/{REPO_NAME}")

if __name__ == "__main__":
    deploy()
