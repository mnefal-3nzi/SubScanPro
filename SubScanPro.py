import subprocess
import shutil
import os
import datetime
import sys
import time
from concurrent.futures import ThreadPoolExecutor

TIMEOUT = 5

BANNER = r"""
 ______                            ___     
(______)                          / __)    
 _     _ ____ ____  ____  _____ _| |__     
| |   | / ___)    \|  _ \| ___ (_   __)    
| |__/ / |   | | | | | | | ____| | |       
|_____/|_|   |_|_|_|_| |_|_____) |_|       

"""

DESCRIPTION = (
    "أداة شاملة لاكتشاف النطاقات الفرعية (Sublist3r, Amass)، "
    "فحص الثغرات (sqlmap, XSStrike, nuclei)، "
    "فحص CMS (وردبريس، جوملا)، ومسح الشبكات (nmap, httpx, dirsearch) بسرعة وكفاءة."
)

# ألوان
RED = '\033[91m'
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_centered_animated(text, delay=0.01):
    columns = shutil.get_terminal_size().columns
    for line in text.split('\n'):
        line = line.strip('\n')
        padding = (columns - len(line)) // 2
        print(' ' * padding, end='')
        for char in line:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    columns = shutil.get_terminal_size().columns
    banner_lines = BANNER.strip('\n').split('\n')
    for line in banner_lines:
        padding = (columns - len(line)) // 2
        print(' ' * padding + GREEN + line + RESET)
    print()
    print_centered_animated(CYAN + DESCRIPTION + RESET, delay=0.01)
    print('\n' + YELLOW + f"{' ' * ((columns - 30) // 2)}[+] Launch Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + RESET)
    print("=" * columns)

# ... باقي الكود كما هو من السكربت الأساسي ...

def check_and_install_tool(tool_name, install_cmd, clone=False):
    path = shutil.which(tool_name)
    if path:
        print(f"{GREEN}[+] {tool_name} already installed.{RESET}")
        return True

    print(f"{YELLOW}[*] Installing {tool_name}...{RESET}")
    try:
        if clone:
            subprocess.run(install_cmd, check=True)
        else:
            subprocess.run(install_cmd, check=True)
        print(f"{GREEN}[+] {tool_name} installed successfully.{RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"{RED}[-] Failed to install {tool_name}. Please install manually.{RESET}")
        return False

def install_dependencies():
    if not os.path.exists("Sublist3r"):
        print(f"{YELLOW}[*] Installing Sublist3r...{RESET}")
        subprocess.run(['git', 'clone', 'https://github.com/aboul3la/Sublist3r.git'])
        subprocess.run(['pip', 'install', '--break-system-packages', '-r', 'Sublist3r/requirements.txt'])

    check_and_install_tool("amass", ["sudo", "snap", "install", "amass"])
    check_and_install_tool("nmap", ["sudo", "apt", "install", "-y", "nmap"])
    check_and_install_tool("go", ["sudo", "apt", "install", "-y", "golang"])
    check_and_install_tool("httpx", ["bash", "-c", "go install github.com/projectdiscovery/httpx/cmd/httpx@latest"])

    if not os.path.exists("dirsearch"):
        print(f"{YELLOW}[*] Installing dirsearch...{RESET}")
        subprocess.run(["git", "clone", "https://github.com/maurosoria/dirsearch.git"])

    if shutil.which("wpscan") is None:
        print(f"{YELLOW}[*] Installing WPScan...{RESET}")
        subprocess.run(["sudo", "gem", "install", "wpscan"], check=True)

    if not os.path.exists("joomscan"):
        print(f"{YELLOW}[*] Installing JoomScan...{RESET}")
        subprocess.run(["git", "clone", "https://github.com/rezasp/joomscan.git"])

def run_sublist3r(domain):
    subprocess.run(['python3', 'Sublist3r/sublist3r.py', '-d', domain, '-o', 'sublist3r_output.txt'])
    with open("sublist3r_output.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

def run_amass(domain):
    result = subprocess.run(['amass', 'enum', '-d', domain], capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def run_httpx(subdomains):
    with open("targets_httpx.txt", "w") as f:
        for sub in subdomains:
            f.write(f"{sub}\n")
    result = subprocess.run(["httpx", "-l", "targets_httpx.txt", "-status-code", "-title", "-tech-detect", "-server"], capture_output=True, text=True)
    return result.stdout

def run_nmap(host):
    result = subprocess.run(["nmap", "-sS", "-T4", "-Pn", "-p-", host], capture_output=True, text=True)
    return result.stdout

def run_dirsearch(url):
    try:
        subprocess.run(["python3", "dirsearch/dirsearch.py", "-u", url, "-e", "php,html,txt", "--plain-text-report=dirsearch_output.txt"], timeout=60)
        with open("dirsearch_output.txt", "r") as f:
            return f.read()
    except Exception as e:
        return f"{RED}[-] Dirsearch failed: {e}{RESET}"

def run_wpscan(url):
    print(f"{YELLOW}[*] تشغيل WPScan على {url} ...{RESET}")
    result = subprocess.run(["wpscan", "--url", url, "--no-update"], capture_output=True, text=True)
    return result.stdout

def run_joomscan(url):
    print(f"{YELLOW}[*] تشغيل JoomScan على {url} ...{RESET}")
    result = subprocess.run(["perl", "joomscan/joomscan.pl", "-u", url], capture_output=True, text=True)
    return result.stdout

def scan_cms_tools(subdomains):
    for sub in subdomains:
        url = f"http://{sub}"
        print(f"\n=== فحص CMS على {url} ===")
        print(run_wpscan(url))
        print(run_joomscan(url))

def scan_domain(domain):
    print("[1] Sublist3r\n[2] Amass")
    tool_choice = input("Select subdomain enumeration tool (1/2): ").strip()
    subdomains = run_sublist3r(domain) if tool_choice == "1" else run_amass(domain)
    print(f"{GREEN}[+] Found {len(subdomains)} subdomains{RESET}")

    print(f"{YELLOW}[*] Running httpx...{RESET}")
    httpx_results = run_httpx(subdomains)
    print(httpx_results)

    print(f"{YELLOW}[*] Running scans on live subdomains...{RESET}")
    for sub in subdomains:
        print(f"\n{GREEN}[+] Scanning {sub}{RESET}")
        print(f"{YELLOW}[*] Running nmap...{RESET}")
        print(run_nmap(sub))

        print(f"{YELLOW}[*] Running dirsearch...{RESET}")
        print(run_dirsearch(f"http://{sub}"))

    scan_cms_tools(subdomains)

def main():
    print_banner()
    install_dependencies()
    domain = input("Enter target domain: ").strip()
    scan_domain(domain)

if __name__ == "__main__":
    main()
