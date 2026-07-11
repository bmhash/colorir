# Security Audit Report

**Project:** colorir  
**Date:** 2026-07-11  
**Methodology:** Red/Blue team comprehensive review  
**Scope:** Full codebase, git history, Docker configuration, dependency supply chain

---

## Executive Summary

The codebase demonstrates **solid security fundamentals** (no eval/exec/pickle, no shell=True, no hardcoded secrets, good input sanitization via slugify). However, there are **actionable findings** across 4 severity levels that should be addressed, particularly around Docker hardening, SSRF protection, dependency pinning, and the file opener's command injection surface.

| Severity | Count | Key Issues |
|----------|-------|-----------|
| CRITICAL | 1 | No dependency lock file |
| HIGH     | 3 | Docker runs as root, SSRF in web downloads, broad version pinning |
| MEDIUM   | 5 | Command injection in opener.py, decompression bombs, symlink attacks, Docker capabilities, apt not pinned |
| LOW      | 4 | Prompt injection, path traversal (mitigated), query injection, no explicit image dimension limit |
| INFO     | 3 | No unsafe deserialization, integer bounds properly handled, hatchling secure |

---

## Findings

### CRITICAL-1: No Dependency Lock File

**Location:** Project root (missing file)  
**CVSS Equivalent:** 9.0

**Description:** The project has no lock file (`requirements.txt` with hashes, `uv.lock`, `poetry.lock`, or `pylock.toml`). All deps use unbounded `>=` specifiers.

**Attack Scenario:**
1. Attacker compromises a PyPI maintainer account (common - happened to LiteLLM March 2026)
2. Publishes malicious patch version (e.g. `pillow==10.2.1`)
3. Next `pip install` on any machine silently installs backdoored version
4. No way to detect the change; different environments get different versions

**Impact:** Full compromise of any machine running `pip install` for this project.

**Fix:**
```bash
uv lock                    # Generate lock file
uv sync --frozen           # Install from lock only
```

---

### HIGH-1: Docker Container Runs as Root

**Location:** `Dockerfile` (no USER instruction)

**Description:** The container runs all processes as `root`. If an attacker exploits a vulnerability in any dependency (Pillow, OpenCV, lxml), they have root privileges inside the container, making container escape significantly easier.

**Fix:** Add non-root user:
```dockerfile
RUN groupadd -r colorir && useradd -r -g colorir -d /app colorir
RUN mkdir -p /app/output && chown -R colorir:colorir /app
USER colorir
```

---

### HIGH-2: SSRF via Unvalidated Image URLs

**Location:** `coloured_drawings/sources/web_search.py:68-74`

**Description:** URLs from DuckDuckGo search results are fetched directly via `requests.get()` without validating the resolved IP address. An attacker could poison search results to make the tool request internal/cloud metadata endpoints.

**Attack Scenario:**
- DDG returns URL pointing to `http://169.254.169.254/latest/meta-data/` (AWS)
- Or `http://127.0.0.1:6379/` (local Redis)
- The tool blindly fetches it, potentially leaking credentials or scanning internal networks

**Mitigating factors:** This is a CLI tool (not a web service), so the attacker must control DDG results for the user's query. Risk is higher when run in cloud environments.

**Fix:** Add SSRF guard before `requests.get()`:
```python
import ipaddress, socket
from urllib.parse import urlparse

def _is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        for info in socket.getaddrinfo(hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        return True
    except Exception:
        return False
```

---

### HIGH-3: Overly Broad Dependency Version Pins

**Location:** `pyproject.toml:10-19`

**Description:** All deps use `>=` with no upper bound:
```toml
"pillow>=10.2",        # allows any future version
"requests>=2.31",      # includes versions with CVEs (< 2.32.4)
"opencv-python-headless>=4.9",
```

**Known CVEs in current allowed ranges:**
- `pillow < 10.3.0` — CVE-2024-28219 (buffer overflow)
- `requests < 2.32.4` — CVE-2024-47081 (.netrc credential leak)
- `lxml < 6.1.0` (transitive) — CVE-2026-41066 (XXE)

**Fix:**
```toml
"pillow>=10.3,<13",
"requests>=2.32.4,<3",
"opencv-python-headless>=4.9,<6",
```

---

### MEDIUM-1: Command Injection in opener.py

**Location:** `coloured_drawings/opener.py:54`

**Description:** The `cmd.exe /c start "" <path>` pattern is passed as a list to `subprocess.Popen`, which on Windows gets reassembled into a command string. If the Windows path contains `&`, `|`, or `>`, cmd.exe interprets them as shell metacharacters.

**Mitigating factors:** The path originates from `slugify()` output (only `[a-z0-9-]`) for `gerar`, but `converter` accepts arbitrary filenames. The `wslpath -w` output is a UNC path (`\\wsl$\...`) which is safe by structure.

**Fix:** Validate the path or use PowerShell:
```python
# Reject paths with shell metacharacters
SHELL_META = set('&|<>^%"')
if SHELL_META & set(win_path):
    return False
```

---

### MEDIUM-2: Decompression Bomb (Pillow)

**Location:** `web_search.py:74`, `ai_generator.py:47`, `pipeline.py:48`

**Description:** `Image.open()` relies on Pillow's default `MAX_IMAGE_PIXELS` (89M pixels). While this prevents catastrophic bombs, it still allows ~340 MB allocations (89M pixels * 4 bytes). No explicit dimension check is applied for the A4 use case (max needed: ~3508px at 300 DPI).

**Fix:**
```python
from PIL import Image
Image.MAX_IMAGE_PIXELS = 25_000_000  # ~100 MB, more than enough for A4

# After opening:
if max(image.size) > 8000:
    raise ValueError("Image dimensions exceed safe limit")
```

---

### MEDIUM-3: Symlink Attacks on Output

**Location:** `pipeline.py:63-64`

**Description:** Files are saved with `image.save(out_dir / "original.png")` without checking if the target is a symlink. In a shared/multi-user environment, an attacker could pre-create symlinks to redirect writes to arbitrary locations.

**Mitigating factors:** The output directory is created with `mkdir(parents=True)` which would fail if a non-directory already exists at that path. Timestamp suffix makes prediction difficult.

**Fix:**
```python
path = out_dir / "original.png"
if path.is_symlink() or path.exists():
    raise IOError(f"Output path already exists: {path}")
image.save(path)
```

---

### MEDIUM-4: Docker — No Capability Drop

**Location:** `docker-compose.yml`

**Description:** The container retains all default Linux capabilities. Best practice is to drop all and add back only what's needed.

**Fix in docker-compose.yml:**
```yaml
services:
  colorir:
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
```

---

### MEDIUM-5: Docker — Apt Packages Not Pinned

**Location:** `Dockerfile:25-28`

**Description:** `libglib2.0-0` and `fonts-dejavu-core` are installed without version pins. A supply chain attack on Debian mirrors could inject malicious packages.

**Fix:** Pin major versions or use content-addressable base image digests (already using `@sha256:...` for Python image, which helps).

---

### LOW-1: Prompt Injection (OpenAI)

**Location:** `ai_generator.py:36`

**Description:** User prompt is interpolated into `PROMPT_TEMPLATE` via `.format()`. A crafted prompt could attempt to manipulate the AI's behavior.

**Impact:** Limited — output is only used to generate an image. OpenAI's safety filters provide additional protection. The worst case is generating an off-topic image.

---

### LOW-2: Path Traversal (Already Mitigated)

**Location:** `utils.py:9-13`

**Description:** `slugify()` strips everything except `[a-zA-Z0-9-]`. Verified safe against `../../etc/passwd`, null bytes, and 200-char inputs. No action needed, but explicit tests would improve confidence.

---

### LOW-3: Search Query Injection

**Location:** `web_search.py:30`

**Description:** User prompt is concatenated into DDG query. Impact is limited to getting unexpected search results.

---

### LOW-4: No Response Size Limit on Downloads

**Location:** `web_search.py:68`

**Description:** `requests.get(url)` downloads the entire response body into memory. A malicious URL could serve a multi-GB response.

**Fix:** Add `stream=True` with size limit:
```python
resp = requests.get(url, timeout=TIMEOUT, headers=headers, stream=True)
if int(resp.headers.get('content-length', 0)) > 50_000_000:  # 50MB
    return None
```

---

## Items Verified CLEAN

| Check | Result |
|-------|--------|
| Secrets in git history | CLEAN — no API keys, tokens, or private keys in any commit |
| Secrets in code | CLEAN — API key read from env var only |
| `eval()` / `exec()` / `pickle` | CLEAN — none used |
| `shell=True` in subprocess | CLEAN — all calls use list args |
| Unsafe YAML/XML loading | CLEAN — not used |
| Integer overflow (detail param) | CLEAN — bounded at CLI + runtime levels |
| Path traversal via slugify | CLEAN — regex strips all special chars |
| Hardcoded credentials | CLEAN — none found |
| .env files committed | CLEAN — in .gitignore |
| Docker socket mount | CLEAN — not exposed |

---

## Supply Chain Risk Summary

| Dependency | Risk | Concern |
|-----------|------|---------|
| `primp` (transitive via ddgs) | HIGH | Single maintainer, 111 removal incidents, custom forked Rust crates |
| `ddgs` | MEDIUM-HIGH | Single maintainer (same as primp), network access |
| `lxml` (transitive via ddgs) | MEDIUM | Historical CVEs, XML parsing complexity |
| `pillow` | MEDIUM | Many historical CVEs (image parsing) but well-maintained team |
| `openai` | LOW | Corporate backing, active security team |
| `requests` / `numpy` / `typer` | LOW | Widely audited, multi-maintainer |

---

## Recommended Remediation Priority

### Immediate (do now)
1. Generate `uv.lock` with hash pinning
2. Tighten version bounds in `pyproject.toml`
3. Add non-root user to Dockerfile

### Short-term (this sprint)
4. Add SSRF guard to `web_search.py`
5. Add image dimension limit (8000px max)
6. Harden `opener.py` with metacharacter check
7. Add `cap_drop: ALL` + `read_only: true` to docker-compose.yml

### Medium-term (next sprint)
8. Add `pip-audit` to CI
9. Add symlink check before file writes
10. Add response size limit to HTTP downloads
11. Add security-focused tests (path traversal, oversized images)

---

## Conclusion

The project has **no critical data leaks or active vulnerabilities** that could be exploited remotely today. The highest real-world risk is the **supply chain** (no lock file + broad version pins) — this is the one thing that could lead to silent compromise without any user interaction. The SSRF and Docker-as-root issues are important to fix but have lower practical exploitability for a local CLI tool.

Overall security posture: **Good fundamentals, needs hardening for production distribution.**
