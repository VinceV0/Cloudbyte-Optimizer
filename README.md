# CloudByte Optimizer ⚡

A high-performance Python application and developer testbench designed to benchmark, evaluate, and compress files across 11 industry-standard algorithms:

- **Zstandard Balanced (Zstd -9)**: Balanced execution speed and high compression density (RFC 8878).
- **Zstandard Fast (Zstd -3)**: Ultra-fast streaming compression for real-time telemetry and message queues.
- **Brotli Max (br -11)**: Maximum compression ratio for high-density static assets (RFC 7932).
- **Brotli Web (br -5)**: Dynamic on-the-fly HTTP asset compression.
- **XZ / LZMA2 (xz -6)**: Extreme density archival compression using LZMA2 (POSIX standard tar.xz).
- **Bzip2 (bz2 -9)**: Classic Unix Burrows-Wheeler block sorting compression.
- **LZ4 Fast (lz4-fast)**: High-throughput, ultra-fast streaming compression for real-time I/O.
- **LZ4 High Compression (lz4 -12)**: Elevated compression ratio while preserving multi-GB/s decompression throughput.
- **Snappy (framed)**: Low-latency database byte streamer (Google Snappy / BigTable).
- **Gzip (gz -9)**: Universal HTTP and legacy compatibility (RFC 1952).
- **Zlib (zlib -9)**: Raw Deflate system standard (RFC 1950) powering Git packs and PNGs.

---

## 🚀 Key Features

1. **Pixel-Perfect Web Dashboard**:
   - Built to match the exact dark UI specification.
   - Live drag-and-drop intake pipe for `.json`, `.csv`, `.log`, `.bin`, `.tar`, and `.parquet` payloads.
   - In-memory processing ensuring local execution without sending data to remote servers.
   - Built-in live datasets (Telemetry Logs, JSON APIs, CSV Matrices) for instant benchmarking.

2. **Real-Time Telemetry & Performance Metrics**:
   - Raw vs. compressed file size comparisons.
   - Total space saved (%) and elimination ratio.
   - Compression (encode) and decompression (decode) time in milliseconds.
   - Sustained throughput in MB/s for both encoding and decoding.
   - Shannon entropy estimation (bits/byte).
   - Automated **Pareto Frontier Winner** scoring based on balanced speed-to-ratio curves.

3. **Dynamic Filtering & Ranking**:
   - Sort by **Best Balance** (Pareto index score).
   - Sort by **Most Space Saved** (compression ratio).
   - Sort by **Fastest Compression** (pure low-latency throughput).

4. **Direct Artifact Export**:
   - Download compressed binaries (`.zst`, `.br`, `.xz`, `.bz2`, `.lz4`, `.sz`, `.gz`, `.zz`) directly from the web interface or CLI.
   - Auto-generated CLI deployment pipelines ready to copy.

---

## 📦 Installation

Ensure Python 3.10+ is installed. Install the compression engines via pip:

```bash
pip install zstandard brotli lz4 python-snappy
```

---

## 🖥️ Running the Web Application

Launch the local server:

```bash
python app.py
```

Then open your browser to:
**[http://127.0.0.1:8080](http://127.0.0.1:8080)**

Drag and drop any file or select one of the test presets to view live multi-algorithm compression benchmarks and download compressed artifacts.
