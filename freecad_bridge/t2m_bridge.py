# Text2Model bridge: lets an external process run Python inside the FreeCAD GUI.
# Listens on 127.0.0.1:52525. Protocol: one JSON line {"code": "..."} per request,
# one JSON line {"ok": bool, "out": str, "err": str} per reply.
# Code runs on the Qt main thread (required for GUI/document calls) in a
# persistent namespace, so variables survive between requests.

import io
import json
import queue
import socket
import threading
import traceback
import contextlib

import FreeCAD
from PySide import QtCore

T2M_PORT = 52525
_t2m_jobs = queue.Queue()
_t2m_ns = {"__name__": "t2m", "FreeCAD": FreeCAD, "App": FreeCAD}


def _t2m_run(code):
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(code, "<t2m>", "exec"), _t2m_ns)
        return {"ok": True, "out": out.getvalue(), "err": ""}
    except Exception:
        return {"ok": False, "out": out.getvalue(), "err": traceback.format_exc()}


def _t2m_drain():
    while not _t2m_jobs.empty():
        code, reply = _t2m_jobs.get()
        reply["result"] = _t2m_run(code)
        reply["done"].set()


def _t2m_client(conn):
    with conn, conn.makefile("rwb") as f:
        for line in f:
            reply = {"done": threading.Event()}
            _t2m_jobs.put((json.loads(line)["code"], reply))
            reply["done"].wait()
            f.write((json.dumps(reply["result"]) + "\n").encode())
            f.flush()


def _t2m_serve():
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", T2M_PORT))
    srv.listen()
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=_t2m_client, args=(conn,), daemon=True).start()


def start():
    global _t2m_timer
    import FreeCADGui
    _t2m_ns.update(FreeCADGui=FreeCADGui, Gui=FreeCADGui)
    _t2m_timer = QtCore.QTimer()
    _t2m_timer.timeout.connect(_t2m_drain)
    _t2m_timer.start(50)
    threading.Thread(target=_t2m_serve, daemon=True).start()
    FreeCAD.Console.PrintMessage(f"Text2Model bridge listening on 127.0.0.1:{T2M_PORT}\n")
