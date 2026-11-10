"""
CloudByte Optimizer - Standalone Python HTTP Web Server
Zero external web frameworks required (Pure Python http.server + native compression suite).
Supports:
- Web dashboard serving (exact matching dark UI)
- Multipart file upload & streaming benchmarking
- Live JSON telemetry endpoints
- Direct download of compressed binary artifacts (.zst, .br, .lz4, .sz, .gz)
- Built-in test presets (JSON, CSV, Log telemetry)
"""

import os
import io
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import engine

PORT = 8080
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# In-memory storage for active session compressed payloads for instant downloads
LATEST_PAYLOAD_CACHE = {
    "filename": "prod_telemetry_2.4GB.log",
    "raw_data": b"",
    "compressed_map": {}  # key -> bytes
}

def generate_preset_data(name: str):
    if name == "sample_json":
        items = []
        for i in range(12000):
            items.append({
                "id": i,
                "uuid": f"usr-{i:06d}-us-east-1",
                "status": "HEALTHY" if i % 7 != 0 else "DEGRADED",
                "request_count": i * 14 + 7,
                "latency_p99": round(12.4 + (i % 15) * 1.8, 2),
                "region": "us-east-1" if i % 2 == 0 else "eu-west-1",
                "meta": {
                    "tags": ["prod", "edge-router", "v2-gateway"],
                    "timestamp": "2026-10-06T00:15:30Z"
                }
            })
        raw = json.dumps(items, indent=2).encode("utf-8")
        return raw, "cloud_api_dump.json"

    elif name == "sample_csv":
        lines = ["timestamp,node_id,cpu_usage_pct,ram_mb_used,disk_io_iops,net_egress_kbps,status_code\n"]
        for i in range(15000):
            line = f"2026-10-06T01:{i%60:02d}:{i%60:02d}Z,node-{(i%24):03d},{20.0 + (i%70)},{4096 + (i%2048)},{1200 + (i%500)},{45000 + (i%15000)},200\n"
            lines.append(line)
        raw = "".join(lines).encode("utf-8")
        return raw, "cluster_metrics_stream.csv"

    else: # sample_log default
        lines = []
        services = ["auth-service", "billing-gateway", "telemetry-collector", "k8s-ingress", "sql-replicator"]
        levels = ["INFO", "INFO", "WARN", "DEBUG", "ERROR"]
        for i in range(16000):
            svc = services[i % len(services)]
            lvl = levels[i % len(levels)]
            lines.append(f"2026-10-06 01:22:{i%60:02d}.{i%1000:03d} [{lvl}] [{svc}] req_id=tx-{i:08x} client_ip=192.168.1.{i%254} latency={(i%120)+5}ms handled successfully with payload_size=4096\n")
        raw = "".join(lines).encode("utf-8")
        return raw, "prod_telemetry_2.4GB.log"

# Initialize with default sample
default_raw, default_name = generate_preset_data("sample_log")
LATEST_PAYLOAD_CACHE["filename"] = default_name
LATEST_PAYLOAD_CACHE["raw_data"] = default_raw

class CloudByteRequestHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ["/", "/index.html"]:
            self.serve_index()
        elif path == "/api/preset":
            self.serve_preset(query)
        elif path == "/api/download":
            self.serve_download(query)
        elif path == "/api/benchmark_current":
            self.serve_current_benchmark()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/benchmark":
            self.handle_upload_benchmark()
        else:
            self.send_error(404, "Not Found")

    def serve_index(self):
        index_file = os.path.join(TEMPLATES_DIR, "index.html")
        if not os.path.exists(index_file):
            self.send_error(500, "Template missing")
            return
        with open(index_file, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_preset(self, query):
        name = query.get("name", ["sample_log"])[0]
        if name == "current" and LATEST_PAYLOAD_CACHE["raw_data"]:
            raw = LATEST_PAYLOAD_CACHE["raw_data"]
            fname = LATEST_PAYLOAD_CACHE["filename"]
        else:
            raw, fname = generate_preset_data(name)
            LATEST_PAYLOAD_CACHE["filename"] = fname
            LATEST_PAYLOAD_CACHE["raw_data"] = raw

        bench_data = self.run_and_cache_benchmark(raw, fname)
        self.send_json_response(bench_data)

    def serve_current_benchmark(self):
        raw = LATEST_PAYLOAD_CACHE["raw_data"]
        fname = LATEST_PAYLOAD_CACHE["filename"]
        bench_data = self.run_and_cache_benchmark(raw, fname)
        self.send_json_response(bench_data)

    def serve_download(self, query):
        key = query.get("key", [""])[0]
        if not key or key not in LATEST_PAYLOAD_CACHE["compressed_map"]:
            self.send_error(404, f"Compressed artifact for '{key}' not found or session expired.")
            return

        payload = LATEST_PAYLOAD_CACHE["compressed_map"][key]
        ext_map = {
            "zstd-9": ".zst",
            "zstd-3": ".zst",
            "brotli-11": ".br",
            "brotli-5": ".br",
            "lzma-6": ".xz",
            "bzip2-9": ".bz2",
            "lz4": ".lz4",
            "lz4-hc": ".lz4",
            "snappy": ".sz",
            "gzip-9": ".gz",
            "zlib-9": ".zz"
        }
        ext = ext_map.get(key, ".bin")
        base_name = os.path.splitext(LATEST_PAYLOAD_CACHE["filename"])[0]
        out_filename = f"{base_name}{ext}"

        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{out_filename}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_upload_benchmark(self):
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))

        if not content_type.startswith("multipart/form-data"):
            # Raw binary upload fallback
            body = self.rfile.read(content_length)
            filename = "uploaded_payload.bin"
        else:
            boundary_str = content_type.split("boundary=")[-1].split(";")[0].strip().strip('"\'')
            boundary = boundary_str.encode("latin1")
            raw_body = self.rfile.read(content_length)
            
            # Robust multipart parser
            parts = raw_body.split(b"--" + boundary)
            body = b""
            filename = "uploaded_file.bin"
            
            for part in parts:
                if b"Content-Disposition:" in part and b'filename=' in part:
                    header_end = part.find(b"\r\n\r\n")
                    if header_end != -1:
                        headers = part[:header_end].decode("latin1")
                        for line in headers.split("\r\n"):
                            if "filename=" in line:
                                fname_part = line.split("filename=")[-1].strip().strip('"\'')
                                if fname_part:
                                    filename = os.path.basename(fname_part)
                        file_data = part[header_end + 4:]
                        if file_data.endswith(b"\r\n"):
                            file_data = file_data[:-2]
                        body = file_data
                        break

            # Secondary fallback if boundary split didn't find filename
            if not body and b"\r\n\r\n" in raw_body:
                first_sep = raw_body.find(b"\r\n\r\n")
                body = raw_body[first_sep + 4:]
                if body.endswith(b"--\r\n"):
                    body = body[:-4]

        if not body:
            self.send_json_response({"error": "No file payload received"})
            return

        LATEST_PAYLOAD_CACHE["filename"] = filename
        LATEST_PAYLOAD_CACHE["raw_data"] = body

        bench_data = self.run_and_cache_benchmark(body, filename)
        self.send_json_response(bench_data)

    def run_and_cache_benchmark(self, data: bytes, filename: str):
        # Hot-reload engine to guarantee newly configured algorithms are live
        import importlib
        importlib.reload(engine)
        
        # We benchmark payload directly across all 11 engines
        raw_results = engine.benchmark_payload(data, filename)
        
        # Save compressed bytes in cache for direct artifact download
        LATEST_PAYLOAD_CACHE["compressed_map"] = raw_results.pop("_artifacts", {})

        return raw_results

    def send_json_response(self, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Clean logging
        print(f"[CloudByte HTTP] {self.address_string()} - {format%args}")

def run_server(host="127.0.0.1", port=PORT):
    server = HTTPServer((host, port), CloudByteRequestHandler)
    print(f"=================================================================")
    print(f">> CloudByte Optimizer Server running at: http://{host}:{port}")
    print(f"=================================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()

if __name__ == "__main__":
    run_server()
