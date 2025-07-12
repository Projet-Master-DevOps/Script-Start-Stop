import subprocess
import tkinter as tk
from tkinter import scrolledtext
import threading
import os
import time

# Configuration des VMs
VM_LIST = [
    {"name": "ci-cd-vm-projet-master", "zone": "europe-west1-b"},
    {"name": "ci-cd-vm-projet-master-dev", "zone": "europe-west1-b"},
]

# Variables d'environnement
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.getenv("TEMP") or "/tmp", "gcp-service-account.json"
)
subprocess.run(["gcloud", "config", "set", "project", "projet-pipeline"], stdout=subprocess.DEVNULL)

def get_vm_status():
    result_lines = []
    for vm in VM_LIST:
        try:
            output = subprocess.check_output(
                ["gcloud", "compute", "instances", "describe", vm["name"],
                 f"--zone={vm['zone']}", "--format=value(status)"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            
            if output == "RUNNING":
                status = "Allumée"
            elif output == "TERMINATED":
                status = "Éteinte"
            else:
                status = output

            result_lines.append(f"{vm['name']} : {status}")
        except subprocess.SubprocessError:
            result_lines.append(f"{vm['name']} : Erreur")

    return "\n".join(result_lines)

def log(message):
    timestamp = time.strftime("[%H:%M:%S]")
    log_output.insert(tk.END, f"{timestamp} {message}\n")
    log_output.see(tk.END)

def update_status():
    status_output.delete("1.0", tk.END)
    status_output.insert(tk.END, get_vm_status())

def start_vms():
    for vm in VM_LIST:
        log(f"Démarrage de la VM {vm['name']}...")
        result = subprocess.run(["gcloud", "compute", "instances", "start", vm["name"], f"--zone={vm['zone']}"], capture_output=True, text=True)
        log(result.stdout or result.stderr)
    update_status()
    log("Toutes les ressources sont démarrées.")

def stop_vms():
    for vm in VM_LIST:
        log(f"Arrêt de la VM {vm['name']}...")
        result = subprocess.run(["gcloud", "compute", "instances", "stop", vm["name"], f"--zone={vm['zone']}"], capture_output=True, text=True)
        log(result.stdout or result.stderr)
    update_status()
    log("Toutes les ressources sont arrêtées.")

def threaded(action):
    threading.Thread(target=action, daemon=True).start()

# Interface
root = tk.Tk()
root.title("Gestion des ressources GCP")
root.geometry("500x400")
root.resizable(False, False)

status_output = scrolledtext.ScrolledText(root, height=5, state='normal', font=("Segoe UI", 10))
status_output.pack(padx=10, pady=(10, 5), fill="x")

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

start_button = tk.Button(button_frame, text="Allumer les ressources", width=25, font=("Segoe UI", 10), command=lambda: threaded(start_vms))
start_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(button_frame, text="Éteindre les ressources", width=25, font=("Segoe UI", 10), command=lambda: threaded(stop_vms))
stop_button.grid(row=0, column=1, padx=10)

log_output = scrolledtext.ScrolledText(root, height=10, state='normal', font=("Segoe UI", 10))
log_output.pack(padx=10, pady=(5, 10), fill="both", expand=True)

def auto_refresh():
    update_status()
    root.after(10000, auto_refresh)

auto_refresh()
root.mainloop()
