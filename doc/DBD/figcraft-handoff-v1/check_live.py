"""Read-only live FigCraft connection probe; never edits the document."""
import json
import queue
import subprocess
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
process = subprocess.Popen(
    [r"C:\Program Files\ArtCraft\FigCraft\figcraft-cli.exe", "mcp", "--attach", "7979", "--timeout", "15"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding="utf-8",
)
responses = queue.Queue()
def read_responses():
    for line in process.stdout:
        try:
            responses.put(json.loads(line))
        except ValueError:
            pass
threading.Thread(target=read_responses, daemon=True).start()
def request(number, method, params):
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": number, "method": method, "params": params}) + "\n")
    process.stdin.flush()
    while True:
        response = responses.get(timeout=20)
        if response.get("id") == number:
            if "error" in response:
                raise RuntimeError(response["error"])
            return response["result"]
report = {}
try:
    report["initialize"] = request(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "POS readiness probe", "version": "1"}})
    process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
    process.stdin.flush()
    report["document"] = request(2, "tools/call", {"name": "inspect_document", "arguments": {"depth": 0, "outline": True, "maxBytes": 60000}})
    report["liveDocumentRead"] = not report["document"].get("isError", False)
except Exception as error:
    report["liveDocumentRead"] = False
    report["error"] = type(error).__name__ + ": " + str(error)
finally:
    process.terminate()
    process.wait(timeout=10)
    report["stderr"] = process.stderr.read()
    (ROOT / "live-document-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
