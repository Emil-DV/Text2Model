"""Send Python to the FreeCAD GUI via the Text2Model bridge.

CLI:  python3 -m t2m.client path/to/script.py     (or '-' for stdin)

Each run puts the repo on FreeCAD's sys.path and drops cached t2m modules,
so edits to t2m/*.py take effect without restarting FreeCAD.

Every step sent is appended to journal/<date>.py. Successful steps are kept
as code, failed ones are commented out, so a journal file is itself a
replayable script:  python3 -m t2m.client journal/2026-11-16.py
(running a file from journal/ is not journaled again).
"""
import datetime
import json
import os
import socket
import sys

PORT = 52525
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL = os.path.join(REPO, "journal")
PREAMBLE = f"""
import sys
if {REPO!r} not in sys.path:
    sys.path.insert(0, {REPO!r})
for _m in [m for m in sys.modules if m == "t2m" or m.startswith("t2m.")]:
    del sys.modules[_m]
"""


def journal(code, result, source):
    now = datetime.datetime.now()
    os.makedirs(JOURNAL, exist_ok=True)
    status = "ok" if result["ok"] else "FAILED"
    body = code.rstrip() + "\n"
    if not result["ok"]:
        err = result["err"].strip().splitlines()[-1]
        body = f"# error: {err}\n" + "".join("# " + l + "\n" for l in body.splitlines())
    with open(os.path.join(JOURNAL, f"{now:%Y-%m-%d}.py"), "a") as f:
        f.write(f"\n# ===== step {now:%H:%M:%S} {status}  (source: {source}) =====\n{body}")


def run(code, timeout=300, source="inline", log=True):
    with socket.create_connection(("127.0.0.1", PORT), timeout=timeout) as s:
        f = s.makefile("rwb")
        f.write((json.dumps({"code": PREAMBLE + code}) + "\n").encode())
        f.flush()
        result = json.loads(f.readline())
    if log:
        journal(code, result, source)
    return result


if __name__ == "__main__":
    path = sys.argv[1]
    src = sys.stdin.read() if path == "-" else open(path).read()
    replaying = path != "-" and os.path.abspath(path).startswith(JOURNAL + os.sep)
    source = "stdin" if path == "-" else os.path.relpath(os.path.abspath(path), REPO)
    r = run(src, source=source, log=not replaying)
    sys.stdout.write(r["out"])
    sys.stderr.write(r["err"])
    sys.exit(0 if r["ok"] else 1)
