import os
import subprocess
import platform
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time

# 🧠 Chemin vers gcloud selon OS
if platform.system() == "Windows":
    GCLOUD_PATH = r"C:\Users\Adm\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
else:
    GCLOUD_PATH = "gcloud"  # macOS/Linux si installé via brew ou path

# 🧪 Vérifie si gcloud est dispo
if not os.path.exists(GCLOUD_PATH) and platform.system() == "Windows":
    tk.Tk().withdraw()
    messagebox.showerror("Erreur", f"gcloud introuvable à l'emplacement :\n{GCLOUD_PATH}\n\nVérifie l'installation du SDK GCP.")
    exit(1)

# Liste des VMs
VM_LIST = [
    {"name": "ci-cd-vm-projet-master", "zone": "europe-west1-b"},
    {"name": "ci-cd-vm-projet-master-dev", "zone": "europe-west1-b"},
]

# Interface graphique
root = tk.Tk()
root.title("Gestion des ressources GCP")
root.geometry("500x400")
root.resizable(False, False)

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
            output = subprocess.check_output([
                GCLOUD_PATH, "compute", "instances", "describe",
                vm["name"], f"--zone={vm['zone']}", "--format=value(status)"
            ], stderr=subprocess.DEVNULL).decode().strip()

            lines.append(f"{vm['name']} : {'Allumée' if output == 'RUNNING' else 'Éteinte' if output == 'TERMINATED' else output}")
        except Exception as e:
            lines.append(f"{vm['name']} : Erreur")
    status_output.delete("1.0", tk.END)
    status_output.insert(tk.END, "\n".join(lines))

def threaded(action):
    threading.Thread(target=action, daemon=True).start()

def start_vms():
    for vm in VM_LIST:
        log(f"Démarrage de {vm['name']}...")
        result = subprocess.run([GCLOUD_PATH, "compute", "instances", "start", vm["name"], f"--zone={vm['zone']}"], capture_output=True, text=True)
        log(result.stdout or result.stderr)
    get_vm_status()
    log("Toutes les VMs sont démarrées.")

def stop_vms():
    for vm in VM_LIST:
        log(f"Arrêt de {vm['name']}...")
        result = subprocess.run([GCLOUD_PATH, "compute", "instances", "stop", vm["name"], f"--zone={vm['zone']}"], capture_output=True, text=True)
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
