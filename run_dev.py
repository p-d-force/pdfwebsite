import subprocess, sys, os, signal, time
os.chdir(r"C:\Users\LokiF\Desktop\PDFWEBSITE")
proc = subprocess.Popen(
    [sys.executable, "-u", "dev_server.py"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
# Wait for startup banner
for line in proc.stdout:
    print(line, end="", flush=True)
    if "Server: http" in line:
        break
# Write PID for management
with open("dev_server.pid", "w") as f:
    f.write(str(proc.pid))
print(f"\nSERVER_READY pid={proc.pid}", flush=True)
# Keep reading output
for line in proc.stdout:
    print(line, end="", flush=True)
