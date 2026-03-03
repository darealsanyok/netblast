# NetBlast v1.2

> **⚠ Authorized use only.** NetBlast is intended exclusively for penetration testers, security researchers, and system administrators testing infrastructure they own or have explicit written permission to test. Unauthorized use is illegal under the CFAA, Computer Misuse Act, and equivalent laws worldwide.

A lightweight, single-file Python framework for network stress testing and reconnaissance. NetBlast provides seven testing modes — from TCP/UDP floods and HTTP stress to Slow Loris, port scanning, bandwidth probing, and DNS stress — all with a real-time live dashboard and a detailed results report.

---

## Features

- **7 test modes** covering the most common network stress scenarios
- **Real-time dashboard** — live req/s, Mbps, latency, success/error counts
- **Detailed results report** — duration, throughput, bandwidth, min/avg/p95/max latency, top errors
- **Multithreaded** via `ThreadPoolExecutor` for high concurrency
- **Zero dependencies** — standard library only (Python 3.9+)
- **Built-in legal confirmation prompt** before any test runs

---

## Requirements

- Python 3.9+
- No third-party packages required

---

## Installation

```bash
git clone https://github.com/darealsanyok/netblast.git
cd netblast
```

That's it. No install step needed.

---

## Usage

```
python netblast.py <mode> [options]
```

### Modes

| Mode        | Description                                              |
|-------------|----------------------------------------------------------|
| `tcp`       | TCP flood — open connections and send random payloads    |
| `udp`       | UDP flood — fire-and-forget datagrams                    |
| `http`      | HTTP/HTTPS stress — configurable method, path, keepalive |
| `slowloris` | Slow Loris — hold connections open with partial headers  |
| `portscan`  | Threaded TCP port scanner with service name hints        |
| `bandwidth` | Raw bandwidth probe — saturate a TCP port                |
| `dns`       | DNS resolver stress against a list of domains            |

### Common Options

| Flag            | Default       | Description                              |
|-----------------|---------------|------------------------------------------|
| `--host`        | `127.0.0.1`   | Target hostname or IP                    |
| `--port`        | `80`          | Target port                              |
| `--threads`     | `50`          | Number of concurrent threads             |
| `--duration`    | `30`          | Test duration in seconds                 |
| `--payload`     | `1024`        | Payload / chunk size in bytes            |
| `--timeout`     | `2.0`         | Socket connect timeout in seconds        |
| `--no-confirm`  | *(off)*       | Skip the authorization prompt            |

### HTTP-specific Options

| Flag          | Default | Description                                  |
|---------------|---------|----------------------------------------------|
| `--path`      | `/`     | URL path to request                          |
| `--method`    | `GET`   | HTTP method: `GET`, `POST`, `PUT`, `HEAD`    |
| `--ssl`       | *(off)* | Force TLS/SSL (auto-enabled on port 443)     |
| `--keepalive` | *(off)* | Use persistent HTTP keep-alive connections   |

### Port Scan Options

| Flag       | Default    | Description              |
|------------|------------|--------------------------|
| `--ports`  | `1-1024`   | Port range, e.g. `1-65535` |

### DNS Options

| Flag        | Default     | Description                                         |
|-------------|-------------|-----------------------------------------------------|
| `--domains` | *(random)*  | Comma-separated list of domains to resolve          |

---

## Examples

```bash
# TCP flood — 200 threads for 30 seconds
python netblast.py tcp --host 192.168.1.10 --port 8080 --threads 200 --duration 30

# UDP flood — 50 threads with 512-byte datagrams
python netblast.py udp --host 192.168.1.10 --port 53 --threads 50 --payload 512

# HTTP GET stress with keep-alive
python netblast.py http --host 192.168.1.10 --port 80 --threads 100 --method GET --keepalive

# HTTPS POST stress
python netblast.py http --host 192.168.1.10 --port 443 --threads 100 --method POST --ssl

# Slow Loris — hold 500 connections open for 2 minutes
python netblast.py slowloris --host 192.168.1.10 --port 80 --threads 500 --duration 120

# Full port scan
python netblast.py portscan --host 192.168.1.10 --ports 1-65535 --threads 2000

# Bandwidth saturation probe — 64 KB chunks
python netblast.py bandwidth --host 192.168.1.10 --port 9999 --threads 8 --payload 65536

# DNS resolver stress against specific domains
python netblast.py dns --threads 50 --duration 30 --domains example.com,test.com
```

---

## Output

Each run prints a live dashboard line that updates every 500 ms:

```
  HTTP Stress      [##################] 1 423 rps   48.31 Mbps   12.4 ms   42 690 ok     0 err
```

Followed by a full results summary:

```
==========================================================
  RESULTS
==========================================================
  Duration      : 30.01s
  Total Reqs    : 42,711
  Successful    : 42,690  (99.9%)
  Failed        : 21
  Throughput    : 1,423.2 req/s
  Bandwidth     : 48.31 Mbps  (181.18 MB)
  Latency       : min=1.2ms  avg=12.4ms  p95=34.1ms  max=201.7ms
==========================================================
```

---

## Legal Notice

This tool is provided for **authorized security testing and research only**. Before running any test, NetBlast will prompt you to confirm that you own the target system or hold explicit written authorization. You can suppress this prompt with `--no-confirm` only when scripting tests against your own controlled infrastructure.

The authors accept no liability for misuse. Always comply with applicable laws.

---

## License

MIT
