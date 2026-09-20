"""Chunked, resumable downloader for a flaky link.

Both `pip` and `huggingface_hub` stream a whole file over one HTTP connection.
On this network the connection establishes fine but stalls mid-transfer, and a
stall late in a 2-10 GB file throws away everything already transferred.

This fetches a fixed-size window at a time (`Range: bytes=a-b`) with a short
per-chunk timeout, appending to the destination. A stall costs one chunk, not
the whole file, and the destination is always a valid prefix so re-running
resumes exactly where it stopped.

Usage:
    python scripts/robust_download.py <url> <dest> [--sha256 HEX] [--chunk-mb 16]
    python scripts/robust_download.py --manifest lisa      # all LISA-7B-v1 files
    python scripts/robust_download.py --manifest wheels    # torch + torchvision
"""

import argparse
import hashlib
import os
import sys
import time

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HF = "https://huggingface.co"
TORCH_IDX = "https://download.pytorch.org/whl/cu121"

MANIFESTS = {
    # cp311, not cp312. transformers 4.31.0 requires tokenizers<0.14, and
    # tokenizers published no cp312 wheel below 0.14 - while 0.13.3 cannot be
    # built from source on 3.12 either, since it pins PyO3 0.18 (3.12 support
    # arrived in PyO3 0.20). Python 3.11 is therefore a hard requirement for
    # this stack, and PyPI has no CUDA torch build for Windows at all, so
    # download.pytorch.org is the only source for these two files.
    "wheels": [
        (f"{TORCH_IDX}/torch-2.4.1%2Bcu121-cp311-cp311-win_amd64.whl",
         "wheels/torch-2.4.1+cu121-cp311-cp311-win_amd64.whl", None),
        (f"{TORCH_IDX}/torchvision-0.19.1%2Bcu121-cp311-cp311-win_amd64.whl",
         "wheels/torchvision-0.19.1+cu121-cp311-cp311-win_amd64.whl", None),
    ],
    # CLIP ViT-L/14 vision tower. Only the three files LLaVA actually touches
    # plus the tokenizer assets; the tf/flax/onnx and safetensors duplicates of
    # the same weights are skipped. No sha256: the HF API reports these as plain
    # git blobs, not LFS objects, so there is no published oid to check against.
    "clip": [
        (f"{HF}/openai/clip-vit-large-patch14/resolve/main/pytorch_model.bin",
         "weights/clip-vit-large-patch14/pytorch_model.bin", None),
        (f"{HF}/openai/clip-vit-large-patch14/resolve/main/config.json",
         "weights/clip-vit-large-patch14/config.json", None),
        (f"{HF}/openai/clip-vit-large-patch14/resolve/main/preprocessor_config.json",
         "weights/clip-vit-large-patch14/preprocessor_config.json", None),
        (f"{HF}/openai/clip-vit-large-patch14/resolve/main/tokenizer_config.json",
         "weights/clip-vit-large-patch14/tokenizer_config.json", None),
        (f"{HF}/openai/clip-vit-large-patch14/resolve/main/special_tokens_map.json",
         "weights/clip-vit-large-patch14/special_tokens_map.json", None),
        (f"{HF}/openai/clip-vit-large-patch14/resolve/main/vocab.json",
         "weights/clip-vit-large-patch14/vocab.json", None),
        (f"{HF}/openai/clip-vit-large-patch14/resolve/main/merges.txt",
         "weights/clip-vit-large-patch14/merges.txt", None),
    ],
    # sha256 values are the LFS object ids reported by the HF API.
    "lisa": [
        (f"{HF}/xinlai/LISA-7B-v1/resolve/main/pytorch_model-00001-of-00002.bin",
         "weights/LISA-7B-v1/pytorch_model-00001-of-00002.bin",
         "86c2b94e29646fc7949ca4957da54983fe91a53f5ffa7c4a80509377562af447"),
        (f"{HF}/xinlai/LISA-7B-v1/resolve/main/pytorch_model-00002-of-00002.bin",
         "weights/LISA-7B-v1/pytorch_model-00002-of-00002.bin",
         "9290b230d2a80c782a21b508eff2da04ed373188f31e023302d73c18e55c28b6"),
    ],
}


def remote_size(url, session):
    """Total size of `url`, or None when the server does not advertise one.

    HF serves small non-LFS blobs (config.json, vocab.json, ...) with chunked
    transfer encoding, which carries no Content-Length. That is not an error -
    it just means the ranged-window strategy has no target to aim at.
    """
    r = session.head(url, allow_redirects=True, timeout=30)
    r.raise_for_status()
    size = r.headers.get("Content-Length")
    return int(size) if size is not None else None


def download_whole(url, dest, session, timeout=60):
    """Fetch a small file in one shot, atomically via a .part sibling."""
    r = session.get(url, stream=True, timeout=timeout)
    r.raise_for_status()
    tmp = dest + ".part"
    with open(tmp, "wb") as f:
        for block in r.iter_content(256 * 1024):
            if block:
                f.write(block)
    os.replace(tmp, dest)
    return os.path.getsize(dest)


def download(url, dest, sha256=None, chunk_mb=16, timeout=30, max_stalls=10000):
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    session = requests.Session()
    total = remote_size(url, session)
    chunk = chunk_mb * 1024 * 1024

    if total is None:
        # No advertised length: nothing to resume against, so re-fetch whole.
        n = download_whole(url, dest, session)
        print(f"[dl] COMPLETE {os.path.basename(dest)} ({n / 1e3:.0f} kB, unsized)",
              flush=True)
        return

    have = os.path.getsize(dest) if os.path.exists(dest) else 0
    if have > total:  # corrupt/oversized leftover - start clean
        os.remove(dest)
        have = 0
    print(f"[dl] {os.path.basename(dest)}  {have / 1e9:.2f}/{total / 1e9:.2f} GB", flush=True)

    stalls = 0
    t_last = time.time()
    bytes_since = 0
    while have < total:
        end = min(have + chunk, total) - 1
        try:
            r = session.get(
                url,
                headers={"Range": f"bytes={have}-{end}"},
                stream=True,
                timeout=timeout,
            )
            if r.status_code not in (200, 206):
                raise RuntimeError(f"HTTP {r.status_code}")
            written = 0
            with open(dest, "ab") as f:
                for block in r.iter_content(1024 * 1024):
                    if block:
                        f.write(block)
                        written += len(block)
            have += written
            bytes_since += written
            if written == 0:
                stalls += 1
                time.sleep(2)
            else:
                stalls = 0
        except Exception as exc:  # noqa: BLE001
            stalls += 1
            if stalls > max_stalls:
                raise
            print(f"[dl] retry {stalls} at {have / 1e9:.2f} GB: {exc}", flush=True)
            time.sleep(min(2 + stalls, 15))
            # a partial chunk may have landed; re-read the real size
            have = os.path.getsize(dest) if os.path.exists(dest) else 0

        now = time.time()
        if now - t_last >= 30:
            rate = bytes_since / (now - t_last) / 1e6
            pct = 100 * have / total
            eta = (total - have) / max(bytes_since / (now - t_last), 1) / 60
            print(f"[dl] {pct:5.1f}%  {have / 1e9:.2f}/{total / 1e9:.2f} GB  "
                  f"{rate:.2f} MB/s  eta {eta:.0f} min", flush=True)
            t_last, bytes_since = now, 0

    if sha256:
        print(f"[dl] verifying sha256 of {os.path.basename(dest)}...", flush=True)
        h = hashlib.sha256()
        with open(dest, "rb") as f:
            for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
                h.update(block)
        if h.hexdigest() != sha256:
            raise SystemExit(
                f"CHECKSUM MISMATCH for {dest}\n  expected {sha256}\n  got      {h.hexdigest()}"
            )
        print("[dl] checksum OK", flush=True)
    print(f"[dl] COMPLETE {os.path.basename(dest)}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("dest", nargs="?")
    ap.add_argument("--sha256")
    ap.add_argument("--chunk-mb", type=int, default=16)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--manifest", choices=sorted(MANIFESTS))
    args = ap.parse_args()

    if args.manifest:
        failed = []
        for url, rel, sha in MANIFESTS[args.manifest]:
            try:
                download(
                    url, os.path.join(REPO_ROOT, rel), sha, args.chunk_mb, args.timeout
                )
            except Exception as exc:  # noqa: BLE001
                # One unreachable file must not abandon the rest of the batch;
                # re-running the manifest skips whatever already completed.
                print(f"[dl] FAILED {rel}: {type(exc).__name__}: {exc}", flush=True)
                failed.append(rel)
        if failed:
            raise SystemExit("incomplete: " + ", ".join(failed))
    elif args.url and args.dest:
        download(args.url, args.dest, args.sha256, args.chunk_mb, args.timeout)
    else:
        ap.error("give <url> <dest> or --manifest")
    print("ALL DOWNLOADS COMPLETE", flush=True)


if __name__ == "__main__":
    sys.exit(main())
