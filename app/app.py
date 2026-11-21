"""
Tiny web app that displays the name of the Kubernetes pod serving the request.

The pod name, pod IP, node name and app name are injected by Kubernetes as
environment variables using the Downward API (see k8s/*-deployment.yaml).
When run outside Kubernetes it falls back to the container hostname, which
Docker/Kubernetes set to the container/pod name anyway.

Uses only the Python standard library -> no dependencies to install.
"""
import json
import os
import socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.getenv("PORT", "8080"))


def pod_info():
    return {
        "app": os.getenv("APP_NAME", "pod-name-app"),
        "pod_name": os.getenv("POD_NAME", socket.gethostname()),
        "pod_ip": os.getenv("POD_IP", "unknown"),
        "node_name": os.getenv("NODE_NAME", "unknown"),
        "service_type": os.getenv("SERVICE_TYPE", "unknown"),
        "time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }


HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>{app}</title>
<style>
 body{{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;
      display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
 .card{{background:#1e293b;padding:2rem 3rem;border-radius:12px;text-align:center}}
 h1{{color:#38bdf8;margin:0 0 .5rem}} .pod{{font-size:1.6rem;color:#facc15}}
 td{{padding:.2rem .8rem;text-align:left}}
</style></head>
<body><div class="card">
 <h1>Hello from Kubernetes!</h1>
 <p>This request was served by pod:</p>
 <p class="pod"><b>{pod_name}</b></p>
 <table>
  <tr><td>App / Deployment</td><td>{app}</td></tr>
  <tr><td>Exposed via</td><td>{service_type}</td></tr>
  <tr><td>Pod IP</td><td>{pod_ip}</td></tr>
  <tr><td>Node</td><td>{node_name}</td></tr>
  <tr><td>Time (UTC)</td><td>{time_utc}</td></tr>
 </table>
</div></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        info = pod_info()
        if self.path == "/healthz":
            self._send(200, "ok\n", "text/plain")
        elif self.path == "/api":
            self._send(200, json.dumps(info) + "\n", "application/json")
        elif self.path == "/":
            # curl / wget get plain text, browsers get HTML
            agent = self.headers.get("User-Agent", "")
            if agent.startswith(("curl", "Wget")):
                self._send(200, f"Hello from pod: {info['pod_name']} "
                                f"(app={info['app']}, service={info['service_type']})\n",
                           "text/plain")
            else:
                self._send(200, HTML.format(**info), "text/html")
        else:
            self._send(404, "not found\n", "text/plain")

    def log_message(self, fmt, *args):
        print(f"[{os.getenv('POD_NAME', socket.gethostname())}] "
              f"{self.address_string()} - {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"Listening on 0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
