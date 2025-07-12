import os
import sys
import subprocess
import platform
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import shutil
import urllib.request
import tempfile
from PIL import Image, ImageTk

# 🌐 Fonction utilitaire pour retrouver les fichiers embarqués avec PyInstaller
def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)

# 💡 Installer automatiquement le SDK GCP si absent
def install_gcloud_windows():
    install_url = "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe"
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "GoogleCloudSDKInstaller.exe")

    try:
        tk.Tk().withdraw()
        messagebox.showinfo("Installation requise", "Google Cloud SDK va être téléchargé et installé automatiquement.")
        urllib.request.urlretrieve(install_url, installer_path)
        subprocess.run([installer_path, "/S"], check=True)
        messagebox.showinfo("Succès", "Google Cloud SDK a été installé. Veuillez redémarrer l'application.")
        exit(0)
    except Exception as e:
        messagebox.showerror("Erreur d'installation", f"Échec de l'installation de Google Cloud SDK :\n{str(e)}")
        exit(1)

def install_gcloud_mac():
    try:
        tk.Tk().withdraw()
        response = messagebox.askyesno("Installation requise", "Le SDK Google Cloud n'est pas installé. Voulez-vous l'installer via Homebrew ?")
        if response:
            subprocess.run(["brew", "install", "google-cloud-sdk"], check=True)
            messagebox.showinfo("Succès", "Google Cloud SDK installé. Veuillez redémarrer l'application.")
        else:
            messagebox.showwarning("Installation annulée", "L'application va se fermer.")
        exit(0)
    except Exception as e:
        messagebox.showerror("Erreur", f"Échec de l'installation : {str(e)}")
        exit(1)

# 🔍 Détection multiplateforme de gcloud
if platform.system() == "Windows":
    GCLOUD_PATH = shutil.which("gcloud") or r"C:\\Users\\Adm\\AppData\\Local\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd"
    if not os.path.exists(GCLOUD_PATH):
        install_gcloud_windows()
else:
    GCLOUD_PATH = shutil.which("gcloud") or "gcloud"
    if shutil.which("gcloud") is None:
        install_gcloud_mac()

# 🔧 Fonction pour exécuter une commande gcloud sans fenêtre cmd
def run_gcloud_command(args, capture_output=True):
    kwargs = {
        "text": True,
        "capture_output": capture_output
    }
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run([GCLOUD_PATH] + args, **kwargs)

# Liste des VMs
VM_LIST = [
    {"name": "ci-cd-vm-projet-master", "zone": "europe-west1-b"},
    {"name": "ci-cd-vm-projet-master-dev", "zone": "europe-west1-b"},
]

# Interface graphique
root = tk.Tk()
root.title("Gestion des ressources GCP")
root.geometry("500x450")
root.resizable(False, False)

# 🌟 Logo affiché en haut de l'application (facultatif)
try:
    logo_path = resource_path("F1stream_logo.png")
    logo_image = Image.open(logo_path)
    logo_image = logo_image.resize((100, 100), Image.ANTIALIAS)
    logo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(root, image=logo)
    logo_label.image = logo  # pour que tkinter le garde en mémoire
    logo_label.pack(pady=(5, 0))
except Exception as e:
    print(f"[!] Impossible de charger le logo : {e}")

status_output = scrolledtext.ScrolledText(root, height=5, font=("Segoe UI", 10))
status_output.pack(padx=10, pady=(10, 5), fill="x")

log_output = scrolledtext.ScrolledText(root, height=10, font=("Segoe UI", 10))
log_output.pack(padx=10, pady=(5, 10), fill="both", expand=True)

def log(message):
    timestamp = time.strftime("[%H:%M:%S]")
    log_output.insert(tk.END, f"{timestamp} {message}\n")
    log_output.see(tk.END)

def get_vm_status():
    lines = []
    for vm in VM_LIST:
        try:
            result = run_gcloud_command([
                "compute", "instances", "describe",
                vm["name"], f"--zone={vm['zone']}", "--format=value(status)"
            ])
            output = result.stdout.strip()
            lines.append(f"{vm['name']} : {'Allumée' if output == 'RUNNING' else 'Éteinte' if output == 'TERMINATED' else output}")
        except Exception:
            lines.append(f"{vm['name']} : Erreur")
    status_output.delete("1.0", tk.END)
    status_output.insert(tk.END, "\n".join(lines))

def threaded(action):
    threading.Thread(target=action, daemon=True).start()

def start_vms():
    for vm in VM_LIST:
        log(f"Démarrage de {vm['name']}...")
        result = run_gcloud_command([
            "compute", "instances", "start", vm["name"], f"--zone={vm['zone']}"
        ])
        log(result.stdout or result.stderr)
    get_vm_status()
    log("Toutes les VMs sont démarrées.")

def stop_vms():
    for vm in VM_LIST:
        log(f"Arrêt de {vm['name']}...")
        result = run_gcloud_command([
            "compute", "instances", "stop", vm["name"], f"--zone={vm['zone']}"
        ])
        log(result.stdout or result.stderr)
    get_vm_status()
    log("Toutes les VMs sont arrêtées.")

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

tk.Button(button_frame, text="Allumer les ressources", font=("Segoe UI", 10),
          command=lambda: threaded(start_vms), width=25).grid(row=0, column=0, padx=10)

tk.Button(button_frame, text="Éteindre les ressources", font=("Segoe UI", 10),
          command=lambda: threaded(stop_vms), width=25).grid(row=0, column=1, padx=10)

def auto_refresh():
    get_vm_status()
    root.after(10000, auto_refresh)

auto_refresh()
root.mainloop()
