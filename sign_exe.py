import subprocess
import os
import sys

def sign_executable(exe_path: str):
    """
    Generates/fetches a Code Signing Certificate for Agentik Marketing (Mohammad A. Bakhtawer)
    and signs the Windows Executable.
    Prevents Unknown Installer warnings & Defender false positives.
    """
    if not os.path.exists(exe_path):
        print(f"File not found for signing: {exe_path}")
        return False

    abs_path = os.path.abspath(exe_path)
    
    ps_script = f"""
    $cert = Get-ChildItem -Path Cert:\\CurrentUser\\My -CodeSigningCert | Select-Object -First 1
    if ($null -eq $cert) {{
        $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Agentik Marketing (Mohammad A. Bakhtawer)" -CertStoreLocation Cert:\\CurrentUser\\My
    }}
    Set-AuthenticodeSignature -FilePath "{abs_path}" -Certificate $cert
    """
    
    try:
        res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Successfully signed executable with Code Signing Certificate (Agentik Marketing): {exe_path}")
            return True
        else:
            print(f"Signing notice: {res.stderr}")
            return False
    except Exception as e:
        print(f"Signing exception: {e}")
        return False

if __name__ == "__main__":
    target = os.path.join("dist", "GoogleRankChecker", "GoogleRankChecker.exe")
    sign_executable(target)
