#!/usr/bin/env python3
import os
import sys
import subprocess
import urllib.request
import zipfile
import json

VENV_DIR = os.path.join(os.path.dirname(__file__), 'flaskenv')

ASCII_ART = r'''

   ____  ___   __  __________  __   ____       ____               __            
  / __ \/   | / / / /_  __/ / / /  / __ \___  / __/_______  _____/ /_           
 / / / / /| |/ / / / / / / /_/ /  / /_/ / _ \/ /_/ ___/ _ \/ ___/ __ \          
/ /_/ / ___ / /_/ / / / / __  /  / _, _/  __/ __/ /  /  __(__  ) / / /          
\____/_/  |_\____/ /_/ /_/ /_/  /_/_|_|\___/_/ /_/   \___/____/_/ /_/           
 /_  __/___  / /_____  ____     / ____/__  ____  ___  _________ _/ /_____  _____
  / / / __ \/ //_/ _ \/ __ \   / / __/ _ \/ __ \/ _ \/ ___/ __ `/ __/ __ \/ ___/
 / / / /_/ / ,< /  __/ / / /  / /_/ /  __/ / / /  __/ /  / /_/ / /_/ /_/ / /    
/_/  \____/_/|_|\___/_/ /_/   \____/\___/_/ /_/\___/_/   \__,_/\__/\____/_/     

                                                            By XBEAST
'''

print(ASCII_ART)

def in_venv():
    return hasattr(sys, 'real_prefix') or sys.prefix != getattr(sys, 'base_prefix', sys.prefix)

def create_and_activate_venv():
    print("→ Creating virtual environment…")
    if not os.path.isdir(VENV_DIR):
        subprocess.run([sys.executable, '-m', 'venv', VENV_DIR], check=True)
        
    if os.name == 'nt':
        pip = os.path.join(VENV_DIR, 'Scripts', 'pip.exe')
        python = os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    else:
        subprocess.run([sys.executable, '-m', 'venv', VENV_DIR], check=True)
        pip = os.path.join(VENV_DIR, 'bin', 'pip')

    print("→ Installing Flask into venv…")
    if os.name == 'nt':
        subprocess.run([python, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([pip, 'install', 'Flask', 'requests'], check=True)
    else:
        subprocess.run([pip, 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([pip, 'install', 'Flask', 'requests'], check=True)

    print("✅ Virtualenv ready.")
    if os.name == 'nt':
        python = os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    else:
        python = os.path.join(VENV_DIR, 'bin', 'python')

    script_path = os.path.abspath(__file__)
    if os.name == 'nt':
        subprocess.run([python, script_path] + sys.argv[1:], check=True)
        sys.exit(0)
    else:
        os.execv(python, [python] + sys.argv)

if not in_venv():
    create_and_activate_venv()

import webbrowser
import requests
from flask import Flask, request

def is_curl_installed():
    try:
        return subprocess.run(['curl', '--version'], capture_output=True).returncode == 0
    except:
        return False

def install_curl():
    if os.name == 'nt':
        print("→ Downloading and installing the latest curl for Windows...")
        curl_api_url = "https://api.github.com/repos/curl/curl/releases/latest"
        response = urllib.request.urlopen(curl_api_url)
        release_data = json.loads(response.read())

        for asset in release_data["assets"]:
            if "win64" in asset["name"].lower() and "zip" in asset["name"]:
                curl_url = asset["browser_download_url"]
                break

        download_path = os.path.join(os.getenv('TEMP'), 'curl.zip')
        urllib.request.urlretrieve(curl_url, download_path)
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(os.getenv('TEMP'))
        print("✅ curl installed successfully.")
    else:
        print("→ Installing curl on Linux…")
        if subprocess.run(["which", "pacman"], capture_output=True).returncode == 0:
            subprocess.run(["sudo", "pacman", "-S", "curl", "--noconfirm"], check=True)
        elif subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
            subprocess.run(["sudo", "apt", "install", "curl", "-y"], check=True)
        elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
            subprocess.run(["sudo", "dnf", "install", "curl", "-y"], check=True)


def generate_refresh_token(client_id, client_secret, scope):
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri=http://localhost:5000&response_type=code"
        f"&scope={scope}&access_type=offline&prompt=consent"
    )
    print("Opening authorization URL in browser…")
    webbrowser.open(auth_url)

    app = Flask(__name__)

    @app.route('/')
    def handle_redirect():
        auth_code = request.args.get('code')
        if not auth_code:
            return "Error: No authorization code found.", 400

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': auth_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': 'http://localhost:5000',
            'grant_type': 'authorization_code'
        }
        resp = requests.post(token_url, data=data)
        tokens = resp.json()

        print("\n=== OAuth2 Tokens ===\n")
        if 'refresh_token' in tokens:
            print(f"🔑 Refresh Token: {tokens['refresh_token']}\n")
        else:
            print("⚠️ No refresh token received. Try deleting and recreating the OAuth client.")

        print(f"Access Token: {tokens.get('access_token')}")
        print(f"Expires In: {tokens.get('expires_in')} seconds")
        print(f"Scope: {tokens.get('scope')}")
        print(f"Token Type: {tokens.get('token_type')}")
        print("\n======================\n")

        if 'refresh_token' in tokens:
            print("→ Testing refresh token with curl...\n")
            curl_cmd = (
                f"curl --request POST --data 'client_id={client_id}&client_secret={client_secret}"
                f"&refresh_token={tokens['refresh_token']}&grant_type=refresh_token' "
                "https://oauth2.googleapis.com/token"
            )
            print("Running command:\n" + curl_cmd)
            curl_result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True)
            print("\nCurl response:\n", curl_result.stdout)
            print("✅ Refresh token is valid!\n")
        return "<h3>Authorization successful! You can close this window.</h3>"

    app.run(port=5000)

if __name__ == '__main__':
    if not is_curl_installed():
        print("Curl is missing; please install it (e.g. pacman -S curl) and retry.")
        sys.exit(1)

    cid = input("Enter your Client ID: ").strip()
    secret = input("Enter your Client Secret: ").strip()
    scope = input("Enter scope (default https://mail.google.com/): ").strip() or "https://mail.google.com/"
    generate_refresh_token(cid, secret, scope)
