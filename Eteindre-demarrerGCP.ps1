Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$cheminFichierJSON = "$env:TEMP\gcp-service-account.json"
$env:GOOGLE_APPLICATION_CREDENTIALS = $cheminFichierJSON
gcloud config set project projet-pipeline *> $null

#Liste des VM à suivre
$vmListe = @(
    @{ Name = "ci-cd-vm-projet-master"; Zone = "europe-west1-b" },
    @{ Name = "ci-cd-vm-projet-master-dev"; Zone = "europe-west1-b" }
)

$form = New-Object System.Windows.Forms.Form
$form.Text = "Gestion des ressources GCP"
$form.Size = New-Object System.Drawing.Size(500, 400)
$form.StartPosition = "CenterScreen"

$txtEtat = New-Object System.Windows.Forms.TextBox
$txtEtat.Location = New-Object System.Drawing.Point(20, 10)
$txtEtat.Size = New-Object System.Drawing.Size(440, 80)
$txtEtat.Multiline = $true
$txtEtat.ReadOnly = $true
$txtEtat.ScrollBars = "Vertical"
$txtEtat.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.Controls.Add($txtEtat)

$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Multiline = $true
$txtLog.ReadOnly = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.Location = New-Object System.Drawing.Point(20, 190)
$txtLog.Size = New-Object System.Drawing.Size(440, 160)
$form.Controls.Add($txtLog)

function Log($message) {
    $txtLog.AppendText("[$(Get-Date -Format 'HH:mm:ss')] $message`r`n")
    $txtLog.SelectionStart = $txtLog.Text.Length
    $txtLog.ScrollToCaret()
}

function ObtenirEtatVMs {
    $resultats = @()
    foreach ($vm in $vmListe) {
        try {
            $zone = $vm["Zone"]
            $name = $vm["Name"]
            $etat = & gcloud compute instances describe $name --zone=$zone --format="value(status)" 2>$null

            switch ($etat) {
                "RUNNING" { $etatFR = "Allumée" }
                "TERMINATED" { $etatFR = "Éteinte" }
                default { $etatFR = $etat }
            }
            $resultats += "$name : $etatFR"
        } catch {
            $resultats += "$name : Erreur"
        }
    }
    return ($resultats -join "`r`n")
}

$btnAllumer = New-Object System.Windows.Forms.Button
$btnAllumer.Location = New-Object System.Drawing.Point(20, 100)
$btnAllumer.Size = New-Object System.Drawing.Size(200, 60)
$btnAllumer.Text = "Allumer les ressources"
$btnAllumer.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$btnAllumer.Add_Click({
    foreach ($vm in $vmListe) {
        Log("Démarrage de la VM $($vm.Name)...")
        $output = & gcloud compute instances start $vm.Name --zone=$($vm.Zone) 2>&1
        Log($output)
    }
    $txtEtat.Text = ObtenirEtatVMs
    Log("Toutes les ressources sont démarrées.")
})
$form.Controls.Add($btnAllumer)

$btnEteindre = New-Object System.Windows.Forms.Button
$btnEteindre.Location = New-Object System.Drawing.Point(260, 100)
$btnEteindre.Size = New-Object System.Drawing.Size(200, 60)
$btnEteindre.Text = "Éteindre les ressources"
$btnEteindre.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$btnEteindre.Add_Click({
    foreach ($vm in $vmListe) {
        Log("Arrêt de la VM $($vm.Name)...")
        $output = & gcloud compute instances stop $vm.Name --zone=$($vm.Zone) 2>&1
        Log($output)
    }
    $txtEtat.Text = ObtenirEtatVMs
    Log("Toutes les ressources sont arrêtées.")
})
$form.Controls.Add($btnEteindre)

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 10000
$timer.Add_Tick({ $txtEtat.Text = ObtenirEtatVMs })
$timer.Start()

$txtEtat.Text = ObtenirEtatVMs
$txtEtat.ForeColor = [System.Drawing.Color]::DarkBlue
$form.Topmost = $true
$form.Add_Shown({ $form.Activate() })
[void] $form.ShowDialog()
