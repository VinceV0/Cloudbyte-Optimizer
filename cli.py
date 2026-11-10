"""
Command-line Interface (CLI) Benchmark Runner for CloudByte Optimizer.
Usage:
    python cli.py <file_path> [--sort balance|ratio|speed] [--export-dir ./out]
"""

import sys
import os
import argparse
import engine

def format_bytes(num_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"

def main():
    parser = argparse.ArgumentParser(description="CloudByte Optimizer Multi-Engine Benchmark CLI")
    parser.add_argument("file", help="Path to input file to compress and benchmark")
    parser.add_argument("--sort", choices=["balance", "ratio", "speed"], default="balance", help="Sort results by metric")
    parser.add_argument("--export-dir", default=None, help="Directory to save compressed artifacts")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"  CLOUDBYTE OPTIMIZER - MULTI-ALGORITHM BENCHMARK")
    print(f"=======================================================")
    print(f"Target: {args.file}")
    
    with open(args.file, "rb") as f:
        data = f.read()

    print(f"Raw Size: {format_bytes(len(data))} ({len(data):,} bytes)")
    
    report = engine.benchmark_payload(data, os.path.basename(args.file))
    if "error" in report:
        print(f"Benchmark error: {report['error']}")
        sys.exit(1)

    results = report["results"]
    if args.sort == "ratio":
        results.sort(key=lambda x: x["saved_percent"], reverse=True)
    elif args.sort == "speed":
        results.sort(key=lambda x: x["encode_time_ms"])
    else:
        results.sort(key=lambda x: x["balance_score"], reverse=True)

    print(f"Entropy: {report['entropy']} bits/byte\n")
    print(f"{'ENGINE':<18} | {'OUTPUT SIZE':<12} | {'SAVED %':<9} | {'ENC TIME':<10} | {'DEC TIME':<10} | {'ENC THRUPUT':<12} | {'SCORE':<6}")
    print("-" * 94)

    for r in results:
        winner_mark = " *" if r.get("is_winner") else "  "
        print(f"{r['name'] + winner_mark:<18} | {format_bytes(r['compressed_size']):<12} | {r['saved_percent']:>6.1f} % | {r['encode_time_ms']:>7.1f} ms | {r['decode_time_ms']:>7.1f} ms | {r['encode_throughput_mb_s']:>7.1f} MB/s | {r['balance_score']:>5.1f}")

    winner = report["winner"]
    print("-" * 94)
    print(f">> [PARETO WINNER]: {winner['name']} ({winner['variant']}) - {winner['saved_percent']}% reduction in {winner['encode_time_ms']}ms")

    if args.export_dir:
        os.makedirs(args.export_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(args.file))[0]
        # Generate files
        print(f"\nExporting compressed artifacts to: {args.export_dir}")
        artifacts = report.get("_artifacts", {})
        ext_map = {r["key"]: r["extension"] for r in results}
        for key, c_data in artifacts.items():
            ext = ext_map.get(key, ".bin")
            out_p = os.path.join(args.export_dir, f"{base}_{key}{ext}")
            with open(out_p, "wb") as out_f:
                out_f.write(c_data)
            print(f" -> Exported: {out_p} ({format_bytes(len(c_data))})")

if __name__ == "__main__":
    main()
