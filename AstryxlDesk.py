import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import threading, time, json, os, random, datetime, copy, math
import ctypes

try:
    from pynput import mouse, keyboard
    from pynput.mouse import Button, Controller as MouseCtrl
    from pynput.keyboard import Key, Controller as KeyCtrl
    PYNPUT_OK = True
except ImportError:
    PYNPUT_OK = False

try:
    import pyautogui
    import PIL.ImageGrab as ImageGrab
    VISION_OK = True
except ImportError:
    VISION_OK = False

# ══════════════════════════════════════════════════════════════════════════════
#  THEME SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
_DARK = dict(
    BG="#0a0a10", PANEL="#13131c", CARD="#1a1a26", BORDER="#252535",
    ACCENT="#39ff8f", ACC2="#ff3f6c", ACC3="#ffcf40", ACC4="#3fa8ff", ACC5="#bf7fff",
    TEXT="#dde2f0", MUTED="#525270", SEL="#2a2a3a",
)
_LIGHT = dict(
    BG="#f0f2f8", PANEL="#e0e4f0", CARD="#ffffff", BORDER="#c0c8e0",
    ACCENT="#0a7c3e", ACC2="#cc1040", ACC3="#c07000", ACC4="#0055c0", ACC5="#7030b0",
    TEXT="#1a1a2e", MUTED="#7080a0", SEL="#d0d8f0",
)
TH = dict(_DARK)   # active theme dict — mutated on switch

def _c(k): return TH[k]   # color lookup

FONT   = ("Consolas", 9)
FONT_B = ("Consolas", 9, "bold")
FONT_H = ("Consolas", 14, "bold")
FONT_T = ("Consolas", 18, "bold")

# shortcuts for frequently used colors (re-fetched at call time via _c)
def BG():     return TH["BG"]
def PANEL():  return TH["PANEL"]
def CARD():   return TH["CARD"]
def BORDER(): return TH["BORDER"]
def ACCENT(): return TH["ACCENT"]
def ACC2():   return TH["ACC2"]
def ACC3():   return TH["ACC3"]
def ACC4():   return TH["ACC4"]
def ACC5():   return TH["ACC5"]
def TEXT():   return TH["TEXT"]
def MUTED():  return TH["MUTED"]

def cbutton(parent, text, cmd, fg_key="ACCENT", bg_key="CARD", pad=(10,4), **kw):
    return tk.Button(parent, text=text, command=cmd,
                     bg=_c(bg_key), fg=_c(fg_key),
                     activebackground=_c("BORDER"), activeforeground=_c(fg_key),
                     font=FONT_B, relief="flat", cursor="hand2",
                     highlightbackground=_c(fg_key), highlightthickness=1,
                     padx=pad[0], pady=pad[1], **kw)

def centry(parent, var, width=8):
    return tk.Entry(parent, textvariable=var, width=width,
                    bg=_c("CARD"), fg=_c("ACCENT"), font=FONT,
                    insertbackground=_c("ACCENT"), relief="flat",
                    highlightbackground=_c("BORDER"), highlightthickness=1)

def sep(parent):
    tk.Frame(parent, bg=_c("BORDER"), height=1).pack(fill="x", pady=3)


# ══════════════════════════════════════════════════════════════════════════════
#  HUMANIZED ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class HumanMover:
    @staticmethod
    def _bezier(p0, p1, p2, p3, t):
        u = 1 - t
        return (u**3*p0[0]+3*u**2*t*p1[0]+3*u*t**2*p2[0]+t**3*p3[0],
                u**3*p0[1]+3*u**2*t*p1[1]+3*u*t**2*p2[1]+t**3*p3[1])

    @staticmethod
    def move(mc, x2, y2, duration=None, speed_mult=1.0):
        x1, y1 = mc.position
        dist = math.hypot(x2-x1, y2-y1)
        if dist < 2:
            mc.position = (int(x2), int(y2)); return
        if duration is None:
            base = 0.04 + dist / 4000
            duration = base * random.uniform(0.7, 1.4) / max(speed_mult, 0.1)
        steps = max(8, int(dist / 10))
        cp1 = (x1+(x2-x1)*random.uniform(0.2,0.4)+random.uniform(-dist*0.12,dist*0.12),
               y1+(y2-y1)*random.uniform(0.2,0.4)+random.uniform(-dist*0.12,dist*0.12))
        cp2 = (x1+(x2-x1)*random.uniform(0.6,0.8)+random.uniform(-dist*0.08,dist*0.08),
               y1+(y2-y1)*random.uniform(0.6,0.8)+random.uniform(-dist*0.08,dist*0.08))
        sleep_per = duration / steps
        for i in range(steps+1):
            if i == steps:
                px, py = x2, y2
            else:
                t = i/steps; t_e = t*t*(3-2*t)
                px, py = HumanMover._bezier((x1,y1),cp1,cp2,(x2,y2),t_e)
                px += random.gauss(0, 0.35); py += random.gauss(0, 0.35)
            mc.position = (int(px), int(py))
            time.sleep(sleep_per)

class HumanClick:
    @staticmethod
    def click(mc, btn=None, double=False, right=False, middle=False):
        if btn is None:
            if right:   btn = Button.right
            elif middle: btn = Button.middle
            else:        btn = Button.left
        time.sleep(random.uniform(0.008, 0.035))
        mc.press(btn); time.sleep(random.uniform(0.04, 0.13)); mc.release(btn)
        if double:
            time.sleep(random.uniform(0.05, 0.11))
            mc.press(btn); time.sleep(random.uniform(0.03, 0.09)); mc.release(btn)


# ══════════════════════════════════════════════════════════════════════════════
#  DRAGGABLE TARGET OVERLAY
# ══════════════════════════════════════════════════════════════════════════════
class TargetOverlay(tk.Toplevel):
    RADIUS = 18
    COLORS = [ACC2, "ACC3", "ACC4", "ACC5", "ACCENT", "#ff9f40", "#40ffdf", "#ff6ef7"]

    def __init__(self, master, targets, on_update):
        super().__init__(master)
        self.targets   = targets
        self.on_update = on_update
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "#010101")
        self.configure(bg="#010101")
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.canvas = tk.Canvas(self, bg="#010101", highlightthickness=0, cursor="hand2")
        self.canvas.pack(fill="both", expand=True)
        self._drag_idx = None; self._drag_offx = self._drag_offy = 0
        self.canvas.bind("<ButtonPress-1>",   self._press)
        self.canvas.bind("<B1-Motion>",       self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<ButtonPress-3>",   self._rclick)
        self._visible = True
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        R = self.RADIUS
        for i, t in enumerate(self.targets):
            x, y = t["x"], t["y"]
            col = self.COLORS[i % len(self.COLORS)]
            self.canvas.create_oval(x-R-3,y-R-3,x+R+3,y+R+3, fill="",outline=col,width=2)
            self.canvas.create_oval(x-R,y-R,x+R,y+R, fill=col,outline="white",width=1.5)
            self.canvas.create_text(x, y, text=str(i+1), fill="black",
                                    font=("Consolas",10,"bold"))
            badge = f"{t.get('delay_ms',300)}ms"
            bw = len(badge)*7
            self.canvas.create_rectangle(x+R,y-10,x+R+bw,y+10, fill="#000000",outline=col)
            self.canvas.create_text(x+R+bw//2, y, text=badge, fill=col,
                                    font=("Consolas",7,"bold"))

    def _hit(self, cx, cy):
        R = self.RADIUS+6
        for i,t in enumerate(self.targets):
            if abs(t["x"]-cx)<=R and abs(t["y"]-cy)<=R: return i
        return None

    def _press(self, e):
        self._drag_idx = self._hit(e.x, e.y)
        if self._drag_idx is not None:
            t = self.targets[self._drag_idx]
            self._drag_offx = t["x"]-e.x; self._drag_offy = t["y"]-e.y

    def _drag(self, e):
        if self._drag_idx is None: return
        self.targets[self._drag_idx]["x"] = e.x+self._drag_offx
        self.targets[self._drag_idx]["y"] = e.y+self._drag_offy
        self.redraw()

    def _release(self, e):
        if self._drag_idx is not None: self.on_update()
        self._drag_idx = None

    def _rclick(self, e):
        idx = self._hit(e.x, e.y)
        if idx is None: return
        m = tk.Menu(self, tearoff=0, bg=_c("CARD"), fg=_c("TEXT"),
                    activebackground=BORDER, activeforeground=_c("ACCENT"), font=FONT)
        t = self.targets[idx]
        m.add_command(label=f"#{idx+1}  ({t['x']}, {t['y']})", state="disabled")
        m.add_separator()
        m.add_command(label="🗑 Hapus", command=lambda i=idx: self._del(i))
        m.tk_popup(e.x_root, e.y_root)

    def _del(self, idx):
        if 0 <= idx < len(self.targets):
            self.targets.pop(idx); self.on_update(); self.redraw()

    def toggle(self):
        if self._visible: self.withdraw(); self._visible = False
        else:             self.deiconify(); self._visible = True; self.redraw()

    def refresh(self): self.redraw()


# ══════════════════════════════════════════════════════════════════════════════
#  STATE  (core logic)
# ══════════════════════════════════════════════════════════════════════════════
class State:
    # Mouse move throttle: only record a move event every N ms to keep file small
    MOVE_THROTTLE_MS = 16   # ~60fps

    def __init__(self):
        self.recorded_actions = []
        self.is_recording = False
        self.is_playing   = False
        self.record_start = None
        self.last_event_t = None
        self.last_move_t  = None      # for move throttle
        self.play_thread  = None
        self.targets  = []
        self.chains   = []
        self.profiles = {}
        self.humanized      = False
        self.human_move_spd = 1.0
        self.human_key_var  = 60
        # move recording toggle (can disable to save events)
        self.record_moves = True

        self.on_record_toggle = None
        self.on_play_toggle   = None
        self.on_status_update = None
        self.on_action_logged = None

        self._mouse_l    = None
        self._keyboard_l = None
        if PYNPUT_OK:
            self._start_listeners()

    def _start_listeners(self):
        self._mouse_l = mouse.Listener(
            on_move=self._on_move,          # ← NOW RECORDING MOVES
            on_click=self._on_click,
            on_scroll=self._on_scroll)
        self._mouse_l.daemon = True
        self._mouse_l.start()

        self._keyboard_l = keyboard.Listener(
            on_press=self._on_kpress, on_release=self._on_krelease)
        self._keyboard_l.daemon = True
        self._keyboard_l.start()

        self._hotkeys = {
            "<f5>": keyboard.HotKey(keyboard.HotKey.parse("<f5>"), self._hk_play),
            "<f6>": keyboard.HotKey(keyboard.HotKey.parse("<f6>"), self._hk_record),
            "<f7>": keyboard.HotKey(keyboard.HotKey.parse("<f7>"), self._hk_stop),
        }

    def _canonical(self, key):
        try: return self._keyboard_l.canonical(key)
        except: return key

    def _fwd_hk(self, key, pressed):
        for hk in self._hotkeys.values():
            try: (hk.press if pressed else hk.release)(self._canonical(key))
            except: pass

    # ── event handlers ──────────────────────────────────────────────────
    def _on_move(self, x, y):
        if not self.is_recording or not self.record_moves: return
        now = time.time()
        # throttle: only record if enough time passed since last move
        if self.last_move_t and (now - self.last_move_t)*1000 < self.MOVE_THROTTLE_MS:
            return
        self.last_move_t = now
        self._record({"type": "mouse_move", "x": x, "y": y})

    def _on_click(self, x, y, btn, pressed):
        if not self.is_recording: return
        self._record({"type":"mouse_click","x":x,"y":y,
                      "button":btn.name,"pressed":pressed})

    def _on_scroll(self, x, y, dx, dy):
        if not self.is_recording: return
        self._record({"type":"scroll","x":x,"y":y,"dx":dx,"dy":dy})

    def _on_kpress(self, key):
        self._fwd_hk(key, True)
        if not self.is_recording: return
        try:
            if self._canonical(key) in [Key.f5,Key.f6,Key.f7]: return
        except: pass
        self._record({"type":"key_press","key":self._kstr(key)})

    def _on_krelease(self, key):
        self._fwd_hk(key, False)
        if not self.is_recording: return
        try:
            if self._canonical(key) in [Key.f5,Key.f6,Key.f7]: return
        except: pass
        self._record({"type":"key_release","key":self._kstr(key)})

    def _kstr(self, key):
        try: return key.char or str(key)
        except: return str(key)

    def _record(self, d):
        now = time.time()
        d["delay_ms"] = round((now - self.last_event_t)*1000) if self.last_event_t else 0
        self.last_event_t = now
        d.setdefault("speed_mult", 1.0)   # per-action speed, editable later
        self.recorded_actions.append(d)
        if self.on_action_logged: self.on_action_logged(d)

    def _hk_record(self):
        if self.on_record_toggle: self.on_record_toggle()
    def _hk_play(self):
        if self.on_play_toggle:   self.on_play_toggle()
    def _hk_stop(self):
        self.is_recording = False; self.is_playing = False
        if self.on_status_update: self.on_status_update()

    def start_recording(self):
        self.recorded_actions = []
        self.is_recording = True
        self.record_start = time.time()
        self.last_event_t = time.time()
        self.last_move_t  = None

    def stop_recording(self):
        self.is_recording = False

    # ── execute one action ───────────────────────────────────────────────
    def _resolve_btn(self, btn_str):
        """Convert string to pynput Button."""
        m = {"left":Button.left, "right":Button.right, "middle":Button.middle}
        return m.get(btn_str, Button.left)

    def _execute(self, action, mc, kc, rel_origin=None, hold_ms=0,
                 jitter_ms=0, speed=1.0):
        t = action["type"]
        per_spd = action.get("speed_mult", 1.0)
        eff_spd = max(speed * per_spd, 0.05)
        delay = action.get("delay_ms", 0) / 1000.0 / eff_spd
        if jitter_ms:
            delay += random.uniform(-jitter_ms/2000, jitter_ms/2000)
        if self.humanized and delay > 0:
            time.sleep(max(0, delay * random.uniform(0.85, 1.20)))
        else:
            time.sleep(max(0, delay))

        def _xy():
            x = action.get("x",0); y = action.get("y",0)
            if rel_origin: x += rel_origin[0]; y += rel_origin[1]
            return int(x), int(y)

        if t == "mouse_move":
            # ── REPLAY MOUSE MOVEMENT ──
            tx, ty = _xy()
            if self.humanized:
                # humanized mode: smooth Bezier to destination
                HumanMover.move(mc, tx, ty, speed_mult=self.human_move_spd)
            else:
                # faithful replay: move directly to recorded position
                mc.position = (tx, ty)

        elif t == "mouse_click":
            btn = self._resolve_btn(action["button"])
            tx, ty = _xy()
            if self.humanized:
                HumanMover.move(mc, tx, ty, speed_mult=self.human_move_spd)
                if action["pressed"]:
                    HumanClick.click(mc, btn)
            else:
                mc.position = (tx, ty)
                if action["pressed"]:
                    mc.press(btn)
                    if hold_ms: time.sleep(hold_ms/1000)
                else:
                    mc.release(btn)

        elif t == "scroll":
            mc.position = _xy()
            mc.scroll(action["dx"], action["dy"])

        elif t == "key_press":
            try:
                k = self._parse_key(action["key"])
                if self.humanized:
                    time.sleep(random.uniform(0, self.human_key_var/1000))
                    kc.press(k)
                    time.sleep(random.uniform(0.03, 0.10))
                else:
                    kc.press(k)
                    if hold_ms: time.sleep(hold_ms/1000)
            except: pass

        elif t == "key_release":
            try:
                k = self._parse_key(action["key"])
                if self.humanized:
                    time.sleep(random.uniform(0.02, 0.06))
                kc.release(k)
            except: pass

    def _parse_key(self, s):
        if s and len(s) == 1: return s
        try: return getattr(Key, s.replace("Key.",""))
        except: return s

    # ── multi-target execute (supports button field + keyboard action) ──
    def _execute_target(self, t, mc, kc, rel_origin=None, jitter=0, speed=1.0):
        delay = t.get("delay_ms", 300) / 1000 / max(speed, 0.1)
        if jitter: delay += random.uniform(-jitter/2000, jitter/2000)
        if self.humanized: delay *= random.uniform(0.85, 1.20)
        time.sleep(max(0, delay))

        action_type = t.get("action", "click")   # "click" or "key"

        if action_type == "key":
            # keyboard shortcut target
            key_str = t.get("key", "")
            if key_str:
                try:
                    k = self._parse_key(key_str)
                    if self.humanized:
                        time.sleep(random.uniform(0, self.human_key_var/1000))
                    kc.press(k)
                    time.sleep(random.uniform(0.04, 0.10) if self.humanized else 0.05)
                    kc.release(k)
                except: pass
        else:
            # mouse click target
            x, y = t["x"], t["y"]
            if rel_origin: x += rel_origin[0]; y += rel_origin[1]
            btn_name = t.get("button", "left")
            btn      = self._resolve_btn(btn_name)
            click_type = t.get("type", "click")

            if self.humanized:
                HumanMover.move(mc, x, y, speed_mult=self.human_move_spd)
                HumanClick.click(mc, btn, double=(click_type=="dblclick"))
            else:
                mc.position = (x, y)
                if click_type == "dblclick":
                    mc.click(btn, 2)
                else:
                    mc.click(btn, 1)

    # ── playback engine ──────────────────────────────────────────────────
    def start_playback(self, mode, speed=1.0, repeat=1, until_stop=False,
                       jitter=0, hold=0, rel_origin=None, scheduled_at=None,
                       actions_override=None):
        self.is_playing = True
        mc = MouseCtrl()
        kc = KeyCtrl()

        def _run():
            if scheduled_at:
                now = datetime.datetime.now()
                tgt = datetime.datetime.combine(now.date(), scheduled_at)
                if tgt < now: tgt += datetime.timedelta(days=1)
                wait = (tgt - datetime.datetime.now()).total_seconds()
                if wait > 0: time.sleep(wait)

            count = 0
            while self.is_playing:
                if mode == "recorded":
                    acts = actions_override or list(self.recorded_actions)
                    for a in acts:
                        if not self.is_playing: break
                        self._execute(a, mc, kc, rel_origin, hold, jitter, speed)

                elif mode == "multi":
                    for t in list(self.targets):
                        if not self.is_playing: break
                        self._execute_target(t, mc, kc, rel_origin, jitter, speed)

                elif mode == "interval":
                    x   = (actions_override or [{"x":0}])[0]["x"]
                    y   = (actions_override or [{"y":0}])[0]["y"]
                    iv  = (actions_override or [{"delay_ms":1000}])[0].get("delay_ms",1000)
                    btn = self._resolve_btn((actions_override or [{"button":"left"}])[0].get("button","left"))
                    d   = iv / 1000 / max(speed, 0.1)
                    if jitter: d += random.uniform(-jitter/2000, jitter/2000)
                    if self.humanized: d *= random.uniform(0.85, 1.20)
                    if self.humanized:
                        HumanMover.move(mc, x, y, speed_mult=self.human_move_spd)
                        HumanClick.click(mc, btn)
                    else:
                        mc.position = (x, y); mc.click(btn)
                    time.sleep(max(0, d))

                count += 1
                if not until_stop and count >= max(repeat, 1): break

            self.is_playing = False
            if self.on_status_update: self.on_status_update()

        self.play_thread = threading.Thread(target=_run, daemon=True)
        self.play_thread.start()

    def stop_playback(self): self.is_playing = False

    def save(self, path):
        with open(path,"w") as f:
            json.dump({"version":"astryxl-1.0","actions":self.recorded_actions,
                       "targets":self.targets,"chains":self.chains},f,indent=2)

    def load(self, path):
        with open(path) as f: d = json.load(f)
        self.recorded_actions = d.get("actions",[])
        self.targets          = d.get("targets",[])
        self.chains           = d.get("chains", [])

    def save_profile(self, name):
        self.profiles[name] = {"actions":copy.deepcopy(self.recorded_actions),
                               "targets":copy.deepcopy(self.targets),
                               "chains": copy.deepcopy(self.chains)}

    def load_profile(self, name):
        p = self.profiles.get(name,{})
        self.recorded_actions = copy.deepcopy(p.get("actions",[]))
        self.targets          = copy.deepcopy(p.get("targets",[]))
        self.chains           = copy.deepcopy(p.get("chains", []))


# ══════════════════════════════════════════════════════════════════════════════
#  HUD OVERLAY
# ══════════════════════════════════════════════════════════════════════════════
class HudOverlay(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.82)
        self.configure(bg="#000010")
        self.geometry("200x52+20+20")
        self.resizable(False,False)
        self._dx = self._dy = 0; self._visible = True
        self.sv = tk.StringVar(value="■ IDLE")
        self.lbl = tk.Label(self, textvariable=self.sv,
                            font=("Consolas",11,"bold"),
                            bg="#000010",fg=_c("ACCENT"),padx=8,pady=6)
        self.lbl.pack(fill="both",expand=True)
        for w in (self,self.lbl):
            w.bind("<ButtonPress-1>",self._ds); w.bind("<B1-Motion>",self._dm)

    def set(self, text, color=None):
        if color is None: color = _c("ACCENT")
        self.sv.set(text); self.lbl.configure(fg=color)

    def toggle(self):
        if self._visible: self.withdraw(); self._visible=False
        else:             self.deiconify(); self._visible=True

    def _ds(self,e): self._dx=e.x; self._dy=e.y
    def _dm(self,e): self.geometry(f"+{self.winfo_x()+e.x-self._dx}+{self.winfo_y()+e.y-self._dy}")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Clicker by Astryxl")
        self.geometry("980x740")
        self.configure(bg=_c("BG"))
        self.resizable(True,True)
        self.minsize(800,600)
        self._is_dark = True
        self.state = State()
        self.state.on_record_toggle = self._toggle_record
        self.state.on_play_toggle   = self._toggle_play
        self.state.on_status_update = self._refresh_ui
        self.state.on_action_logged = self._append_log
        self.hud = HudOverlay(self)
        self.tov = None
        self._vision_running = False
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.state.is_playing=False; self.state.is_recording=False; self.destroy()

    # ══════════════════════════════════════════════════════════════════
    #  THEME SWITCH
    # ══════════════════════════════════════════════════════════════════
    def _switch_theme(self):
        self._is_dark = not self._is_dark
        TH.update(_DARK if self._is_dark else _LIGHT)
        self._apply_ttk_styles()
        # rebuild all widgets with new colors
        for w in self.winfo_children():
            try: w.destroy()
            except: pass
        self._build_ui()
        self._refresh_ui()

    def _apply_ttk_styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook",     background=_c("BG"),   borderwidth=0)
        s.configure("TNotebook.Tab", background=_c("PANEL"),foreground=_c("MUTED"),
                    font=FONT_B,padding=[10,5])
        s.map("TNotebook.Tab",background=[("selected",_c("CARD"))],
              foreground=[("selected",_c("ACCENT"))])
        s.configure("Treeview",background=_c("CARD"),foreground=_c("TEXT"),
                    fieldbackground=_c("CARD"),font=FONT)
        s.configure("Treeview.Heading",background=_c("PANEL"),
                    foreground=_c("ACCENT"),font=FONT_B)
        s.map("Treeview",background=[("selected",_c("BORDER"))])

    # ══════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════
    def _build_ui(self):
        self.configure(bg=_c("BG"))
        self._apply_ttk_styles()
        # header
        hdr = tk.Frame(self,bg=_c("BG")); hdr.pack(fill="x",padx=16,pady=(10,0))
        # title stack: "Auto Clicker" besar di atas, "by Astryxl" kecil di bawah
        title_frame = tk.Frame(hdr, bg=_c("BG"))
        title_frame.pack(side="left")
        tk.Label(title_frame, text="Auto Clicker",
                 font=("Consolas", 20, "bold"),
                 bg=_c("BG"), fg=_c("ACCENT")).pack(anchor="w")
        tk.Label(title_frame, text="by Astryxl",
                 font=("Consolas", 9),
                 bg=_c("BG"), fg=_c("MUTED")).pack(anchor="w")
        tk.Label(hdr,text="   F5=Play  F6=Rec  F7=Stop",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left",padx=12,pady=(4,0))
        _tl = "☀ LIGHT" if self._is_dark else "🌙 DARK"
        cbutton(hdr,_tl,       self._switch_theme,"ACC3").pack(side="right",padx=3)
        cbutton(hdr,"HUD",     self.hud.toggle,   "ACC4").pack(side="right",padx=3)
        cbutton(hdr,"TARGETS", self._toggle_tov,  "ACC2").pack(side="right",padx=3)
        self._human_var = tk.BooleanVar(value=self.state.humanized)
        tk.Checkbutton(hdr,text="🧠 HUMANIZED",variable=self._human_var,
                       command=self._toggle_human,
                       bg=_c("BG"),fg=_c("ACC5"),selectcolor=_c("CARD"),
                       activebackground=_c("BG"),activeforeground=_c("ACC5"),font=FONT_B).pack(side="right",padx=8)

        # status bar
        self.status_var = tk.StringVar(value="■  IDLE")
        sf = tk.Frame(self,bg=_c("PANEL"),pady=3); sf.pack(fill="x",padx=16,pady=(5,0))
        self.status_lbl = tk.Label(sf,textvariable=self.status_var,
                                   font=FONT_B,bg=_c("PANEL"),fg=_c("MUTED"),padx=12)
        self.status_lbl.pack(side="left")
        self.human_ind = tk.Label(sf,text="",font=FONT_B,bg=_c("PANEL"),fg=_c("ACC5"),padx=6)
        self.human_ind.pack(side="left")
        if self.state.humanized: self.human_ind.configure(text="🧠 ON")

        # notebook
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook",     background=_c("BG"),   borderwidth=0)
        s.configure("TNotebook.Tab", background=_c("PANEL"),foreground=_c("MUTED"),font=FONT_B,padding=[10,5])
        s.map("TNotebook.Tab",background=[("selected", "CARD")],foreground=[("selected", "ACCENT")])
        s.configure("Treeview",background=_c("CARD"),foreground=_c("TEXT"),fieldbackground=_c("CARD"),font=FONT)
        s.configure("Treeview.Heading",background=_c("PANEL"),foreground=_c("ACCENT"),font=FONT_B)
        s.map("Treeview",background=[("selected", "BORDER")])

        nb = ttk.Notebook(self); nb.pack(fill="both",expand=True,padx=16,pady=6)
        self._tabs = {k: tk.Frame(nb,bg=_c("BG")) for k in
                      ["RECORD","MULTI-TARGET","INTERVAL","IMAGE/COLOR","CHAINS","PROFILES","SETTINGS"]}
        for name,f in self._tabs.items(): nb.add(f,text=f"  {name}  ")

        self._build_record_tab(self._tabs["RECORD"])
        self._build_multi_tab(self._tabs["MULTI-TARGET"])
        self._build_interval_tab(self._tabs["INTERVAL"])
        self._build_vision_tab(self._tabs["IMAGE/COLOR"])
        self._build_chains_tab(self._tabs["CHAINS"])
        self._build_profiles_tab(self._tabs["PROFILES"])
        self._build_settings_tab(self._tabs["SETTINGS"])

    # ── shared playback opts ────────────────────────────────────────────
    def _popts(self, parent):
        f = tk.Frame(parent,bg=_c("BG")); f.pack(fill="x",pady=3)
        until_v=tk.BooleanVar(value=False)
        rv=tk.StringVar(value="1"); sv=tk.StringVar(value="1.0")
        jv=tk.StringVar(value="0"); hv=tk.StringVar(value="0")
        relv=tk.BooleanVar(value=False); schedv=tk.StringVar(value="")

        # Until Stop toggle
        utcb = tk.Checkbutton(f,text="🔁 UNTIL STOP",variable=until_v,
                              bg=_c("BG"),fg=_c("ACC2"),selectcolor=_c("CARD"),
                              activebackground=_c("BG"),activeforeground=_c("ACC2"),
                              font=FONT_B)
        utcb.pack(side="left",padx=(0,10))

        rep_lbl = tk.Label(f,text="REPEAT",font=FONT,bg=_c("BG"),fg=_c("MUTED"))
        rep_lbl.pack(side="left")
        rep_e = centry(f,rv,5); rep_e.pack(side="left",padx=(2,8))

        # grey out REPEAT when Until Stop active
        def _tog(*_):
            state_ = "disabled" if until_v.get() else "normal"
            rep_e.configure(state=state_)
            rep_lbl.configure(fg=_c("BORDER") if until_v.get() else _c("MUTED"))
        until_v.trace_add("write",_tog)

        for lbl,var in [("SPEED×",sv),("JITTER ms",jv),("HOLD ms",hv)]:
            tk.Label(f,text=lbl,font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left")
            centry(f,var,5).pack(side="left",padx=(2,7))
        tk.Checkbutton(f,text="REL.POS",variable=relv,bg=_c("BG"),fg=_c("ACC3"),
                       selectcolor=_c("CARD"),activebackground=_c("BG"),activeforeground=_c("ACC3"),
                       font=FONT).pack(side="left",padx=(0,7))
        tk.Label(f,text="SCHED HH:MM",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left")
        centry(f,schedv,6).pack(side="left",padx=2)
        return until_v,rv,sv,jv,hv,relv,schedv

    def _parse_popts(self, opts):
        until_v,rv,sv,jv,hv,relv,schedv = opts
        def _i(v,d):
            try: return int(v.get())
            except: return d
        def _f(v,d):
            try: return float(v.get())
            except: return d
        until_stop=until_v.get()
        repeat=_i(rv,1); speed=_f(sv,1.0); jitter=_i(jv,0); hold=_i(hv,0)
        rel_origin=None
        if relv.get() and PYNPUT_OK:
            mc=MouseCtrl(); rel_origin=mc.position
        sched=None
        s=schedv.get().strip()
        if s:
            try: h,m=s.split(":"); sched=datetime.time(int(h),int(m))
            except: pass
        return until_stop,repeat,speed,jitter,hold,rel_origin,sched

    # ─────────────────────────────────────────────────────────────────
    #  TAB: RECORD
    # ─────────────────────────────────────────────────────────────────
    def _build_record_tab(self, p):
        # top buttons
        br = tk.Frame(p,bg=_c("BG")); br.pack(fill="x",pady=5)
        self.rec_btn  = cbutton(br,"⏺ START REC (F6)",self._toggle_record, "ACC2")
        self.play_btn = cbutton(br,"▶ PLAY (F5)",      self._toggle_play)
        self.stop_btn = cbutton(br,"■ STOP (F7)",       self._stop_all, "MUTED")
        for b in [self.rec_btn,self.play_btn,self.stop_btn]: b.pack(side="left",padx=(0,5))

        # io row
        io = tk.Frame(p,bg=_c("BG")); io.pack(fill="x",pady=2)
        cbutton(io,"💾 SAVE", self._save).pack(side="left",padx=(0,5))
        cbutton(io,"📂 LOAD", self._load).pack(side="left",padx=(0,5))
        cbutton(io,"🗑 CLEAR",self._clear_rec, "ACC2").pack(side="left",padx=(0,12))

        # move recording toggle
        self._rec_move_var = tk.BooleanVar(value=True)
        tk.Checkbutton(io,text="Rekam gerakan mouse",variable=self._rec_move_var,
                       command=lambda: setattr(self.state,"record_moves",self._rec_move_var.get()),
                       bg=_c("BG"),fg=_c("ACC3"),selectcolor=_c("CARD"),
                       activebackground=_c("BG"),activeforeground=_c("ACC3"),font=FONT).pack(side="left")

        # move throttle
        tk.Label(io,text="  Throttle ms:",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left")
        self._throttle_var = tk.StringVar(value="16")
        centry(io,self._throttle_var,4).pack(side="left",padx=2)
        tk.Button(io,text="OK",command=self._apply_throttle,
                  bg=_c("CARD"),fg=_c("ACCENT"),font=FONT,relief="flat",padx=4,pady=1).pack(side="left",padx=2)

        sep(p)
        self._rec_opts = self._popts(p)
        sep(p)

        # ── action editor toolbar ──
        ae = tk.Frame(p,bg=_c("BG")); ae.pack(fill="x",pady=2)
        tk.Label(ae,text="ACTION EDITOR:",font=FONT_B,bg=_c("BG"),fg=_c("ACCENT")).pack(side="left",padx=(0,8))
        cbutton(ae,"✏ EDIT",    self._edit_action,   "ACC3").pack(side="left",padx=(0,4))
        cbutton(ae,"⇅ MOVE TO", self._move_action_to,"ACC4").pack(side="left",padx=(0,4))
        cbutton(ae,"🗑 DELETE",  self._delete_action, "ACC2").pack(side="left",padx=(0,4))
        cbutton(ae,"⬆",         self._action_up,     "MUTED",pad=(6,4)).pack(side="left",padx=(0,2))
        cbutton(ae,"⬇",         self._action_down,   "MUTED",pad=(6,4)).pack(side="left",padx=(0,8))
        tk.Label(ae,text="Double-click = edit",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left")

        # ── action treeview ──
        lf = tk.Frame(p,bg=_c("BORDER"),padx=1,pady=1); lf.pack(fill="both",expand=True)
        li = tk.Frame(lf,bg=_c("CARD"));                 li.pack(fill="both",expand=True)
        acols = ("#","Type","Delay ms","Speed×","X","Y","Button/Key","Detail")
        self.action_tree = ttk.Treeview(li,columns=acols,show="headings",height=12)
        for c,w in zip(acols,[30,90,80,60,70,70,90,200]):
            self.action_tree.heading(c,text=c); self.action_tree.column(c,width=w,anchor="center")
        asy = tk.Scrollbar(li,orient="vertical",  command=self.action_tree.yview)
        asx = tk.Scrollbar(li,orient="horizontal",command=self.action_tree.xview)
        self.action_tree.configure(yscrollcommand=asy.set,xscrollcommand=asx.set)
        asy.pack(side="right",fill="y"); asx.pack(side="bottom",fill="x")
        self.action_tree.pack(fill="both",expand=True)
        self.action_tree.bind("<Double-1>",lambda e:self._edit_action())

        bot = tk.Frame(p,bg=_c("BG")); bot.pack(fill="x",pady=2)
        self.count_var = tk.StringVar(value="0 actions")
        tk.Label(bot,textvariable=self.count_var,font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left")

    def _apply_throttle(self):
        try:
            v = int(self._throttle_var.get())
            self.state.MOVE_THROTTLE_MS = max(8, v)
        except: pass

    # ─────────────────────────────────────────────────────────────────
    #  TAB: MULTI-TARGET  (with button + keyboard action + reorder)
    # ─────────────────────────────────────────────────────────────────
    def _build_multi_tab(self, p):
        top = tk.Frame(p,bg=_c("BG")); top.pack(fill="x",pady=5)
        cbutton(top,"+ ADD",         self._add_target_dlg).pack(side="left",padx=(0,4))
        cbutton(top,"🎯 PICK(3s)",   self._pick_target).pack(side="left",padx=(0,4))
        cbutton(top,"✏ EDIT",        self._edit_target).pack(side="left",padx=(0,4))
        cbutton(top,"⇅ REORDER",     self._reorder_dlg,"ACC3").pack(side="left",padx=(0,4))
        cbutton(top,"🗑 HAPUS",      self._remove_target, "ACC2").pack(side="left",padx=(0,4))
        cbutton(top,"🗑 SEMUA",      self._clear_targets, "ACC2").pack(side="left",padx=(0,10))
        cbutton(top,"🟣 OVERLAY",    self._toggle_tov, "ACC5").pack(side="left")

        # treeview — columns now include Button column
        tf = tk.Frame(p,bg=_c("BORDER"),padx=1,pady=1); tf.pack(fill="both",expand=True,pady=3)
        ti = tk.Frame(tf,bg=_c("CARD"));                 ti.pack(fill="both",expand=True)
        cols = ("#","X","Y","Delay ms","Action","Button/Key","Type","Label")
        self.ttree = ttk.Treeview(ti,columns=cols,show="headings",height=11)
        widths = [30,60,60,80,70,90,80,120]
        for c,w in zip(cols,widths):
            self.ttree.heading(c,text=c); self.ttree.column(c,width=w,anchor="center")
        tsv = tk.Scrollbar(ti,orient="vertical",command=self.ttree.yview)
        tsx = tk.Scrollbar(ti,orient="horizontal",command=self.ttree.xview)
        self.ttree.configure(yscrollcommand=tsv.set,xscrollcommand=tsx.set)
        tsv.pack(side="right",fill="y"); tsx.pack(side="bottom",fill="x")
        self.ttree.pack(fill="both",expand=True)
        self.ttree.bind("<Double-1>", lambda e: self._edit_target())

        sep(p)
        pr = tk.Frame(p,bg=_c("BG")); pr.pack(fill="x",pady=3)
        self.multi_play_btn = cbutton(pr,"▶ PLAY MULTI (F5)",self._play_multi)
        self.multi_play_btn.pack(side="left",padx=(0,5))
        cbutton(pr,"■ STOP",self._stop_all, "MUTED").pack(side="left")
        self._mt_opts = self._popts(p)

        tk.Label(p,text="TIP: Double-click row untuk edit • OVERLAY → drag lingkaran langsung ke posisi",
                 font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(anchor="w")

    # ─────────────────────────────────────────────────────────────────
    #  TAB: INTERVAL
    # ─────────────────────────────────────────────────────────────────
    def _build_interval_tab(self, p):
        tk.Label(p,text="INTERVAL CLICKER — Klik satu titik berulang",
                 font=FONT_B,bg=_c("BG"),fg=_c("ACC3")).pack(anchor="w",pady=(8,4))
        sep(p)
        f = tk.Frame(p,bg=_c("BG")); f.pack(fill="x",pady=6)
        self._iv_x  = tk.StringVar(value="0")
        self._iv_y  = tk.StringVar(value="0")
        self._iv_iv = tk.StringVar(value="500")
        self._iv_btn = tk.StringVar(value="left")
        for lt,var in [("X",self._iv_x),("Y",self._iv_y),("Interval ms",self._iv_iv)]:
            tk.Label(f,text=lt,font=FONT,bg=_c("BG"),fg=_c("TEXT"),width=12,anchor="w").pack(side="left")
            centry(f,var,7).pack(side="left",padx=(0,14))
        tk.Label(f,text="Button:",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        ttk.Combobox(f,textvariable=self._iv_btn,
                     values=["left","right","middle"],width=7,state="readonly").pack(side="left",padx=4)

        bf = tk.Frame(p,bg=_c("BG")); bf.pack(fill="x",pady=4)
        cbutton(bf,"🎯 PICK POS(3s)",self._pick_interval_pos).pack(side="left",padx=(0,6))
        self.iv_play_btn = cbutton(bf,"▶ START",self._play_interval)
        self.iv_play_btn.pack(side="left",padx=(0,6))
        cbutton(bf,"■ STOP",self._stop_all, "MUTED").pack(side="left")
        sep(p)
        self._iv_opts = self._popts(p)

    # ─────────────────────────────────────────────────────────────────
    #  TAB: IMAGE/COLOR
    # ─────────────────────────────────────────────────────────────────
    def _build_vision_tab(self, p):
        if not VISION_OK:
            tk.Label(p,text="⚠ pip install pyautogui pillow",
                     font=FONT_B,bg=_c("BG"),fg=_c("ACC2")).pack(expand=True); return
        nb2 = ttk.Notebook(p); nb2.pack(fill="both",expand=True)
        ti=tk.Frame(nb2,bg=_c("BG")); tc=tk.Frame(nb2,bg=_c("BG"))
        nb2.add(ti,text="  IMAGE  "); nb2.add(tc,text="  COLOR TRIGGER  ")

        # image tab
        tk.Label(ti,text="Auto klik saat gambar muncul di layar",font=FONT_B,bg=_c("BG"),fg=_c("ACC3")).pack(anchor="w",pady=8,padx=8)
        sep(ti)
        r1=tk.Frame(ti,bg=_c("BG")); r1.pack(fill="x",padx=8,pady=4)
        self._img_path=tk.StringVar(value="(belum dipilih)")
        tk.Label(r1,textvariable=self._img_path,font=FONT,bg=_c("BG"),fg=_c("TEXT"),width=40,anchor="w").pack(side="left")
        cbutton(r1,"📁",self._pick_image_file,pad=(6,4)).pack(side="left",padx=4)
        cbutton(r1,"📷 SNIP",self._snip_image,pad=(6,4)).pack(side="left")
        r2=tk.Frame(ti,bg=_c("BG")); r2.pack(fill="x",padx=8,pady=4)
        tk.Label(r2,text="Confidence:",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left")
        self._img_conf=tk.StringVar(value="0.85"); centry(r2,self._img_conf,5).pack(side="left",padx=5)
        tk.Label(r2,text="Type:",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left",padx=(10,0))
        self._img_ctype=ttk.Combobox(r2,values=["click","dblclick","right"],width=8,state="readonly")
        self._img_ctype.set("click"); self._img_ctype.pack(side="left",padx=4)
        self.img_watch_btn=cbutton(ti,"👁 START WATCHING",self._start_img_watch)
        self.img_watch_btn.pack(anchor="w",padx=8,pady=8)
        self._img_log=tk.StringVar(value="idle")
        tk.Label(ti,textvariable=self._img_log,font=FONT,bg=_c("BG"),fg=_c("ACC4")).pack(anchor="w",padx=8)

        # color tab
        tk.Label(tc,text="Auto klik saat pixel berubah warna",font=FONT_B,bg=_c("BG"),fg=_c("ACC3")).pack(anchor="w",pady=8,padx=8)
        sep(tc)
        clf=tk.Frame(tc,bg=_c("BG")); clf.pack(fill="x",padx=8,pady=4)
        self._col_x=tk.StringVar(value="0"); self._col_y=tk.StringVar(value="0")
        self._col_tgt=tk.StringVar(value="#ff0000"); self._col_tol=tk.StringVar(value="20")
        self._col_cx=tk.StringVar(value="0"); self._col_cy=tk.StringVar(value="0")
        for lt,var in [("WX",self._col_x),("WY",self._col_y),("COLOR",self._col_tgt),("TOL",self._col_tol)]:
            tk.Label(clf,text=lt,font=FONT,bg=_c("BG"),fg=_c("MUTED"),width=6).pack(side="left")
            centry(clf,var,7).pack(side="left",padx=(0,8))
        clf2=tk.Frame(tc,bg=_c("BG")); clf2.pack(fill="x",padx=8,pady=4)
        cbutton(clf2,"🎨 PICK",self._pick_color).pack(side="left",padx=(0,6))
        cbutton(clf2,"🎯 WATCH POS(3s)",self._pick_col_pos).pack(side="left",padx=(0,6))
        clf3=tk.Frame(tc,bg=_c("BG")); clf3.pack(fill="x",padx=8,pady=4)
        tk.Label(clf3,text="CLICK X:",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left")
        centry(clf3,self._col_cx,6).pack(side="left",padx=4)
        tk.Label(clf3,text="Y:",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left")
        centry(clf3,self._col_cy,6).pack(side="left",padx=4)
        cbutton(clf3,"🎯 CLICK POS(3s)",self._pick_col_click_pos).pack(side="left",padx=6)
        self.col_watch_btn=cbutton(tc,"👁 START WATCHING",self._start_col_watch)
        self.col_watch_btn.pack(anchor="w",padx=8,pady=8)
        self._col_log=tk.StringVar(value="idle")
        tk.Label(tc,textvariable=self._col_log,font=FONT,bg=_c("BG"),fg=_c("ACC4")).pack(anchor="w",padx=8)

    # ─────────────────────────────────────────────────────────────────
    #  TAB: CHAINS
    # ─────────────────────────────────────────────────────────────────
    def _build_chains_tab(self, p):
        tk.Label(p,text="MACRO CHAINS — Gabungin beberapa recording",font=FONT_B,bg=_c("BG"),fg=_c("ACC3")).pack(anchor="w",pady=(8,4))
        sep(p)
        top=tk.Frame(p,bg=_c("BG")); top.pack(fill="x",pady=4)
        cbutton(top,"+ TAMBAH",self._add_chain).pack(side="left",padx=(0,5))
        cbutton(top,"▶ RUN",   self._run_chain).pack(side="left",padx=(0,5))
        cbutton(top,"🗑 HAPUS",self._del_chain, "ACC2").pack(side="left")
        lf=tk.Frame(p,bg=_c("BORDER"),padx=1,pady=1); lf.pack(fill="both",expand=True,pady=4)
        li=tk.Frame(lf,bg=_c("CARD")); li.pack(fill="both",expand=True)
        cols2=("Nama","Actions","Repeat","Notes")
        self.chain_tree=ttk.Treeview(li,columns=cols2,show="headings",height=14)
        for c in cols2:
            self.chain_tree.heading(c,text=c); self.chain_tree.column(c,anchor="center",width=180)
        csv2=tk.Scrollbar(li,orient="vertical",command=self.chain_tree.yview)
        self.chain_tree.configure(yscrollcommand=csv2.set)
        csv2.pack(side="right",fill="y"); self.chain_tree.pack(fill="both",expand=True)

    # ─────────────────────────────────────────────────────────────────
    #  TAB: PROFILES
    # ─────────────────────────────────────────────────────────────────
    def _build_profiles_tab(self, p):
        tk.Label(p,text="PROFILE MANAGER",font=FONT_B,bg=_c("BG"),fg=_c("ACC3")).pack(anchor="w",pady=(8,4))
        sep(p)
        nf=tk.Frame(p,bg=_c("BG")); nf.pack(fill="x",pady=5)
        self._prof_var=tk.StringVar(value="")
        tk.Label(nf,text="Nama:",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        centry(nf,self._prof_var,20).pack(side="left",padx=6)
        cbutton(nf,"💾 SAVE", self._save_profile).pack(side="left",padx=(0,5))
        cbutton(nf,"📂 LOAD", self._load_profile_sel).pack(side="left",padx=(0,5))
        cbutton(nf,"🗑 HAPUS",self._del_profile, "ACC2").pack(side="left")
        lf=tk.Frame(p,bg=_c("BORDER"),padx=1,pady=1); lf.pack(fill="both",expand=True,pady=6)
        li=tk.Frame(lf,bg=_c("CARD")); li.pack(fill="both",expand=True)
        cols3=("Nama","Actions","Targets","Chains")
        self.prof_tree=ttk.Treeview(li,columns=cols3,show="headings",height=16)
        for c in cols3:
            self.prof_tree.heading(c,text=c); self.prof_tree.column(c,anchor="center",width=200)
        psv=tk.Scrollbar(li,orient="vertical",command=self.prof_tree.yview)
        self.prof_tree.configure(yscrollcommand=psv.set)
        psv.pack(side="right",fill="y"); self.prof_tree.pack(fill="both",expand=True)

    # ─────────────────────────────────────────────────────────────────
    #  TAB: SETTINGS
    # ─────────────────────────────────────────────────────────────────
    def _build_settings_tab(self, p):
        tk.Label(p,text="HOTKEYS",font=FONT_H,bg=_c("BG"),fg=_c("ACCENT")).pack(anchor="w",padx=14,pady=(10,4))
        for key,desc in [("F5","Play/Stop"),("F6","Record/Stop"),("F7","Emergency Stop")]:
            r=tk.Frame(p,bg=_c("BG")); r.pack(fill="x",padx=14,pady=2)
            tk.Label(r,text=f"[{key}]",font=FONT_B,bg=_c("BG"),fg=_c("ACCENT"),width=6).pack(side="left")
            tk.Label(r,text=desc,font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        sep(p)
        tk.Label(p,text="🧠 HUMANIZED SETTINGS",font=FONT_H,bg=_c("BG"),fg=_c("ACC5")).pack(anchor="w",padx=14,pady=(8,4))
        hf=tk.Frame(p,bg=_c("CARD"),padx=14,pady=10); hf.pack(fill="x",padx=14,pady=4)
        spd_v=tk.DoubleVar(value=self.state.human_move_spd); kv_v=tk.IntVar(value=self.state.human_key_var)
        def _us(v): self.state.human_move_spd=float(v)
        def _uk(v): self.state.human_key_var=int(float(v))
        for label,var,fr,to,res,cmd,tip in [
            ("Mouse Speed",spd_v,0.3,3.0,0.1,_us,"kecil=lambat"),
            ("Key Variance ms",kv_v,10,200,5,_uk,"variasi timing")]:
            r=tk.Frame(hf,bg=_c("CARD")); r.pack(fill="x",pady=4)
            tk.Label(r,text=label,font=FONT,bg=_c("CARD"),fg=_c("TEXT"),width=18,anchor="w").pack(side="left")
            tk.Scale(r,from_=fr,to=to,resolution=res,orient="horizontal",variable=var,command=cmd,
                     bg=_c("CARD"),fg=_c("ACCENT"),troughcolor=_c("BORDER"),highlightthickness=0,
                     length=180,showvalue=True).pack(side="left")
            tk.Label(r,text=tip,font=FONT,bg=_c("CARD"),fg=_c("MUTED")).pack(side="left",padx=8)
        sep(p)
        tk.Label(p,text="THEME",font=FONT_H,bg=_c("BG"),fg=_c("ACC3")).pack(anchor="w",padx=14,pady=(8,4))
        _mode = "Dark Mode" if self._is_dark else "Light Mode"
        tk.Label(p,text=f"Aktif: {_mode}  —  klik tombol di bawah atau di header untuk switch",
                 font=FONT,bg=_c("BG"),fg=_c("TEXT"),padx=14).pack(anchor="w")
        cbutton(p,"🔄 SWITCH THEME",self._switch_theme,"ACC3").pack(anchor="w",padx=14,pady=6)
        sep(p)
        tk.Label(p,
                 text="Auto Clicker by Astryxl  —  Advanced Automation Tool\n\n"
                      "● Record tab: mouse moves + klik + keyboard direkam\n"
                      "● Action Editor: edit tiap action satu-satu (type, delay, speed×, posisi)\n"
                      "● Repeat UNTIL STOP: loop sampai F7 ditekan\n"
                      "● Multi-Target: left/right/middle click + keyboard shortcut\n"
                      "● Dark/Light theme switch\n"
                      "● Humanized: Bezier mouse + variable key timing\n"
                      "● Overlay: drag target circles langsung di layar",
                 font=FONT,bg=_c("BG"),fg=_c("TEXT"),justify="left",padx=14).pack(anchor="w",pady=6)

    # ══════════════════════════════════════════════════════════════════
    #  RECORD ACTIONS
    # ══════════════════════════════════════════════════════════════════
    # ── action editor helpers ─────────────────────────────────────────
    def _arow(self, n, a):
        t=a["type"]; d=a.get("delay_ms",0); sp=a.get("speed_mult",1.0)
        x=a.get("x",""); y=a.get("y","")
        if t=="mouse_move":   return (n,"MOVE",  d,sp,x,y,"","")
        if t=="mouse_click":  return (n,"CLICK", d,sp,x,y,a.get("button",""),"↓" if a.get("pressed") else "↑")
        if t=="mouse_drag":   return (n,"DRAG",  d,sp,x,y,a.get("button",""),f"→({a.get('x2',0)},{a.get('y2',0)})")
        if t=="scroll":       return (n,"SCROLL",d,sp,x,y,"",f"dy={a.get('dy',0)}")
        if t=="key_press":    return (n,"KEY↓",  d,sp,"","",a.get("key",""),"")
        if t=="key_release":  return (n,"KEY↑",  d,sp,"","",a.get("key",""),"")
        return (n,t,d,sp,x,y,"","")

    def _reload_action_tree(self):
        for i in self.action_tree.get_children(): self.action_tree.delete(i)
        for i,a in enumerate(self.state.recorded_actions):
            self.action_tree.insert("","end",values=self._arow(i+1,a))
        self.count_var.set(f"{len(self.state.recorded_actions)} actions")

    def _sel_action_idx(self):
        sel=self.action_tree.selection()
        return self.action_tree.index(sel[0]) if sel else None

    def _edit_action(self):
        idx=self._sel_action_idx()
        if idx is None: return
        a=self.state.recorded_actions[idx]
        d=tk.Toplevel(self); d.title(f"Edit Action #{idx+1}"); d.configure(bg=_c("BG")); d.grab_set()
        type_v=tk.StringVar(value=a["type"])
        r0=tk.Frame(d,bg=_c("BG")); r0.pack(fill="x",padx=14,pady=4)
        tk.Label(r0,text="Type",width=12,anchor="w",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        ttk.Combobox(r0,textvariable=type_v,
                     values=["mouse_move","mouse_click","mouse_drag","scroll","key_press","key_release"],
                     width=14,state="readonly").pack(side="left",padx=4)
        fields={}
        for lbl,key,default in [("Delay ms","delay_ms",0),("Speed×","speed_mult",1.0),
                                  ("X","x",""),("Y","y",""),("X2 (drag)","x2",""),("Y2 (drag)","y2",""),
                                  ("Button","button","left"),("Key","key","")]:
            r2=tk.Frame(d,bg=_c("BG")); r2.pack(fill="x",padx=14,pady=3)
            tk.Label(r2,text=lbl,width=12,anchor="w",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
            v=tk.StringVar(value=str(a.get(key,default)))
            e=tk.Entry(r2,textvariable=v,bg=_c("CARD"),fg=_c("ACCENT"),font=FONT,relief="flat",
                       insertbackground=_c("ACCENT"),highlightbackground=_c("BORDER"),
                       highlightthickness=1,width=16)
            e.pack(side="left",padx=4); fields[key]=v
        def _ok():
            try:
                a["type"]=type_v.get()
                a["delay_ms"]=int(float(fields["delay_ms"].get() or 0))
                a["speed_mult"]=float(fields["speed_mult"].get() or 1.0)
                for k in ["x","y","x2","y2"]:
                    v=fields[k].get().strip()
                    if v: a[k]=int(float(v))
                    elif k in a: del a[k]
                a["button"]=fields["button"].get().strip() or "left"
                a["key"]   =fields["key"].get().strip()
                item=self.action_tree.selection()[0]
                self.action_tree.item(item,values=self._arow(idx+1,a))
                d.destroy()
            except Exception as ex: messagebox.showerror("Error",str(ex),parent=d)
        br=tk.Frame(d,bg=_c("BG")); br.pack(pady=8)
        cbutton(br,"SAVE",_ok).pack(side="left",padx=6)
        cbutton(br,"CANCEL",d.destroy,"ACC2").pack(side="left",padx=6)

    def _move_action_to(self):
        idx=self._sel_action_idx()
        if idx is None: return
        n=len(self.state.recorded_actions)
        d=tk.Toplevel(self); d.title("Move Action"); d.configure(bg=_c("BG")); d.grab_set()
        tk.Label(d,text=f"Pindah action #{idx+1} ke posisi:",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(padx=14,pady=8)
        to_v=tk.StringVar(value=str(idx+1)); centry(d,to_v,6).pack(padx=14)
        def _ok():
            try: to=int(to_v.get())-1
            except: return
            if not 0<=to<n: return
            acts=self.state.recorded_actions
            item=acts.pop(idx); acts.insert(to,item)
            self._reload_action_tree(); d.destroy()
        br=tk.Frame(d,bg=_c("BG")); br.pack(pady=8)
        cbutton(br,"OK",_ok).pack(side="left",padx=6)
        cbutton(br,"CANCEL",d.destroy,"ACC2").pack(side="left",padx=6)

    def _delete_action(self):
        idx=self._sel_action_idx()
        if idx is None: return
        sel=self.action_tree.selection()[0]
        self.state.recorded_actions.pop(idx)
        self.action_tree.delete(sel)
        self._renumber(self.action_tree)
        self.count_var.set(f"{len(self.state.recorded_actions)} actions")

    def _action_up(self):
        idx=self._sel_action_idx()
        if idx is None or idx==0: return
        a=self.state.recorded_actions; a[idx-1],a[idx]=a[idx],a[idx-1]
        self._reload_action_tree()

    def _action_down(self):
        idx=self._sel_action_idx()
        if idx is None or idx>=len(self.state.recorded_actions)-1: return
        a=self.state.recorded_actions; a[idx],a[idx+1]=a[idx+1],a[idx]
        self._reload_action_tree()

    def _toggle_record(self):
        if self.state.is_recording:
            self.state.stop_recording(); self._refresh_ui()
        else:
            if self.state.is_playing: return
            self.state.start_recording(); self._refresh_ui()

    def _toggle_play(self):
        if self.state.is_playing:
            self.state.stop_playback(); self._refresh_ui(); return
        if not self.state.recorded_actions:
            messagebox.showwarning("Empty","Belum ada recording!"); return
        if self.state.is_recording: self.state.stop_recording()
        us,r,s,j,h,rel,sched = self._parse_popts(self._rec_opts)
        self.state.start_playback("recorded",s,r,us,j,h,rel,sched)
        self._refresh_ui()

    def _stop_all(self):
        self.state.stop_recording(); self.state.stop_playback()
        self._vision_running=False; self._refresh_ui()

    def _clear_rec(self):
        self.state.recorded_actions=[]
        for i in self.action_tree.get_children(): self.action_tree.delete(i)
        self.count_var.set("0 actions")

    def _save(self):
        path=filedialog.asksaveasfilename(defaultextension=".axd",
            filetypes=[("Astryxl Desk","*.axd"),("JSON","*.json")])
        if path: self.state.save(path); messagebox.showinfo("Saved",os.path.basename(path))

    def _load(self):
        path=filedialog.askopenfilename(filetypes=[("Astryxl Desk","*.axd"),("JSON","*.json"),("NandaClick","*.nclick")])
        if path:
            try:
                self.state.load(path); self._reload_action_tree(); self._reload_ttree()
                if self.tov: self.tov.refresh()
                messagebox.showinfo("Loaded",
                    f"{len(self.state.recorded_actions)} actions, {len(self.state.targets)} targets")
            except Exception as e: messagebox.showerror("Error",str(e))

    # ══════════════════════════════════════════════════════════════════
    #  HUMANIZED
    # ══════════════════════════════════════════════════════════════════
    def _toggle_human(self):
        self.state.humanized=self._human_var.get()
        self.human_ind.configure(text="🧠 ON" if self.state.humanized else "")

    # ══════════════════════════════════════════════════════════════════
    #  TARGET OVERLAY
    # ══════════════════════════════════════════════════════════════════
    def _toggle_tov(self):
        if self.tov is None:
            self.tov=TargetOverlay(self,self.state.targets,self._on_target_drag)
        else: self.tov.toggle()

    def _on_target_drag(self): self._reload_ttree()

    # ══════════════════════════════════════════════════════════════════
    #  MULTI-TARGET ACTIONS
    # ══════════════════════════════════════════════════════════════════
    def _target_dialog(self, title, prefill=None):
        """Shared dialog for add/edit target. Returns dict or None."""
        result = {}
        d = tk.Toplevel(self); d.title(title); d.configure(bg=_c("BG")); d.resizable(False,False)
        d.grab_set()

        fields = {}
        defaults = {"X":"100","Y":"100","Delay ms":"300","Label":""}
        for lbl_t, key in [("X","X"),("Y","Y"),("Delay ms","Delay ms"),("Label","Label")]:
            r=tk.Frame(d,bg=_c("BG")); r.pack(fill="x",padx=14,pady=3)
            tk.Label(r,text=lbl_t,width=10,anchor="w",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
            e=tk.Entry(r,bg=_c("CARD"),fg=_c("ACCENT"),font=FONT,relief="flat",
                       insertbackground=_c("ACCENT"),highlightbackground=_c("BORDER"),
                       highlightthickness=1,width=14)
            val = str(prefill.get(key,"")) if prefill else defaults.get(key,"")
            e.insert(0,val); e.pack(side="left"); fields[key]=e

        # Action type selector
        r2=tk.Frame(d,bg=_c("BG")); r2.pack(fill="x",padx=14,pady=3)
        tk.Label(r2,text="Action",width=10,anchor="w",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        action_var=tk.StringVar(value=prefill.get("action","click") if prefill else "click")
        combo_action=ttk.Combobox(r2,textvariable=action_var,
                                  values=["click","key"],width=8,state="readonly")
        combo_action.pack(side="left",padx=4)

        # Button selector (shown when action=click)
        r3=tk.Frame(d,bg=_c("BG")); r3.pack(fill="x",padx=14,pady=3)
        tk.Label(r3,text="Button",width=10,anchor="w",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        btn_var=tk.StringVar(value=prefill.get("button","left") if prefill else "left")
        combo_btn=ttk.Combobox(r3,textvariable=btn_var,
                               values=["left","right","middle"],width=8,state="readonly")
        combo_btn.pack(side="left",padx=4)

        # Click type (click/dblclick) — for mouse
        r4=tk.Frame(d,bg=_c("BG")); r4.pack(fill="x",padx=14,pady=3)
        tk.Label(r4,text="Click Type",width=10,anchor="w",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        ctype_var=tk.StringVar(value=prefill.get("type","click") if prefill else "click")
        ttk.Combobox(r4,textvariable=ctype_var,
                     values=["click","dblclick"],width=8,state="readonly").pack(side="left",padx=4)

        # Key entry (shown when action=key)
        r5=tk.Frame(d,bg=_c("BG")); r5.pack(fill="x",padx=14,pady=3)
        tk.Label(r5,text="Key",width=10,anchor="w",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        key_e=tk.Entry(r5,bg=_c("CARD"),fg=_c("ACCENT"),font=FONT,relief="flat",
                       insertbackground=_c("ACCENT"),highlightbackground=_c("BORDER"),
                       highlightthickness=1,width=14)
        key_e.insert(0,prefill.get("key","") if prefill else "")
        key_e.pack(side="left",padx=4)
        tk.Label(r5,text="contoh: a, space, ctrl, f1",font=FONT,bg=_c("BG"),fg=_c("MUTED")).pack(side="left",padx=4)

        def _ok():
            try:
                result["X"]=int(fields["X"].get()); result["Y"]=int(fields["Y"].get())
                result["delay_ms"]=int(fields["Delay ms"].get())
                result["label"]=fields["Label"].get()
                result["action"]=action_var.get()
                result["button"]=btn_var.get()
                result["type"]=ctype_var.get()
                result["key"]=key_e.get().strip()
                d.destroy()
            except ValueError: messagebox.showerror("Error","X/Y/Delay harus angka",parent=d)

        def _cancel(): d.destroy()
        br=tk.Frame(d,bg=_c("BG")); br.pack(pady=8)
        cbutton(br,"OK",_ok).pack(side="left",padx=6)
        cbutton(br,"CANCEL",_cancel, "ACC2").pack(side="left",padx=6)
        d.wait_window()
        return result if result else None

    def _add_target_dlg(self):
        res=self._target_dialog("Add Target")
        if not res: return
        t={"x":res["X"],"y":res["Y"],"delay_ms":res["delay_ms"],
           "label":res["label"],"action":res["action"],
           "button":res["button"],"type":res["type"],"key":res["key"]}
        self.state.targets.append(t)
        n=len(self.state.targets)
        self.ttree.insert("","end",values=self._trow(n,t))
        if self.tov: self.tov.refresh()

    def _edit_target(self):
        sel=self.ttree.selection()
        if not sel: return
        item=sel[0]; idx=self.ttree.index(item)
        if idx>=len(self.state.targets): return
        t=self.state.targets[idx]
        prefill={"X":t["x"],"Y":t["y"],"Delay ms":t.get("delay_ms",300),
                 "Label":t.get("label",""),"action":t.get("action","click"),
                 "button":t.get("button","left"),"type":t.get("type","click"),
                 "key":t.get("key","")}
        res=self._target_dialog("Edit Target",prefill)
        if not res: return
        t.update({"x":res["X"],"y":res["Y"],"delay_ms":res["delay_ms"],
                  "label":res["label"],"action":res["action"],
                  "button":res["button"],"type":res["type"],"key":res["key"]})
        self.ttree.item(item,values=self._trow(idx+1,t))
        if self.tov: self.tov.refresh()

    def _trow(self, n, t):
        """Build treeview row tuple for a target."""
        if t.get("action","click")=="key":
            return (n, "-", "-", t.get("delay_ms",300), "KEY",
                    t.get("key",""), "-", t.get("label",""))
        return (n, t["x"], t["y"], t.get("delay_ms",300),
                "CLICK", t.get("button","left"),
                t.get("type","click"), t.get("label",""))

    def _reorder_dlg(self):
        """Dialog: move target from position A to position B."""
        n = len(self.state.targets)
        if n < 2: messagebox.showinfo("Info","Minimal 2 target untuk reorder."); return
        d = tk.Toplevel(self); d.title("Reorder Target"); d.configure(bg=_c("BG")); d.resizable(False,False)
        d.grab_set()
        tk.Label(d,text=f"Total target: {n}",font=FONT_B,bg=_c("BG"),fg=_c("ACCENT"),pady=6).pack()
        f=tk.Frame(d,bg=_c("BG")); f.pack(padx=14,pady=6)
        tk.Label(f,text="Pindah dari nomor:",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        from_v=tk.StringVar(); fe=centry(f,from_v,4); fe.pack(side="left",padx=6)
        tk.Label(f,text="ke nomor:",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
        to_v=tk.StringVar(); te=centry(f,to_v,4); te.pack(side="left",padx=6)

        def _ok():
            try:
                fr=int(from_v.get())-1; to=int(to_v.get())-1
            except: messagebox.showerror("Error","Masukkan angka!",parent=d); return
            if not (0<=fr<n and 0<=to<n):
                messagebox.showerror("Error",f"Nomor harus antara 1 dan {n}",parent=d); return
            t=self.state.targets
            item=t.pop(fr); t.insert(to,item)
            self._reload_ttree()
            if self.tov: self.tov.refresh()
            d.destroy()

        br=tk.Frame(d,bg=_c("BG")); br.pack(pady=8)
        cbutton(br,"PINDAH",_ok).pack(side="left",padx=6)
        cbutton(br,"TUTUP",d.destroy, "MUTED").pack(side="left",padx=6)

    def _pick_target(self):
        self.iconify()
        def _cap():
            time.sleep(3)
            x,y=(MouseCtrl().position if PYNPUT_OK else (0,0))
            t={"x":x,"y":y,"delay_ms":300,"label":"","action":"click",
               "button":"left","type":"click","key":""}
            self.state.targets.append(t)
            n=len(self.state.targets)
            self.after(0,lambda: (
                self.ttree.insert("","end",values=self._trow(n,t)),
                self.tov.refresh() if self.tov else None,
                self.deiconify()
            ))
        threading.Thread(target=_cap,daemon=True).start()
        messagebox.showinfo("Pick","Pindah cursor ke target. 3 detik.")

    def _remove_target(self):
        for item in self.ttree.selection():
            idx=self.ttree.index(item); self.ttree.delete(item)
            if 0<=idx<len(self.state.targets): self.state.targets.pop(idx)
        self._renumber(self.ttree)
        if self.tov: self.tov.refresh()

    def _clear_targets(self):
        self.state.targets=[]
        for i in self.ttree.get_children(): self.ttree.delete(i)
        if self.tov: self.tov.refresh()

    def _play_multi(self):
        if self.state.is_playing:
            self.state.stop_playback(); self._refresh_ui(); return
        if not self.state.targets:
            messagebox.showwarning("Empty","Tambah target dulu!"); return
        us,r,s,j,h,rel,sched=self._parse_popts(self._mt_opts)
        self.state.start_playback("multi",s,r,us,j,h,rel,sched)
        self._refresh_ui()

    # ══════════════════════════════════════════════════════════════════
    #  INTERVAL
    # ══════════════════════════════════════════════════════════════════
    def _pick_interval_pos(self):
        self.iconify()
        def _c():
            time.sleep(3); x,y=(MouseCtrl().position if PYNPUT_OK else (0,0))
            self._iv_x.set(str(x)); self._iv_y.set(str(y)); self.after(0,self.deiconify)
        threading.Thread(target=_c,daemon=True).start()
        messagebox.showinfo("Pick","Pindah ke posisi. 3 detik.")

    def _play_interval(self):
        if self.state.is_playing:
            self.state.stop_playback(); self._refresh_ui(); return
        try: x=int(self._iv_x.get()); y=int(self._iv_y.get()); iv=int(self._iv_iv.get())
        except: messagebox.showerror("Error","X/Y/Interval harus angka."); return
        us,r,s,j,h,rel,sched=self._parse_popts(self._iv_opts)
        self.state.start_playback("interval",s,r,us,j,h,rel,sched,
                                  actions_override=[{"x":x,"y":y,"delay_ms":iv,
                                                     "button":self._iv_btn.get()}])
        self._refresh_ui()

    # ══════════════════════════════════════════════════════════════════
    #  VISION
    # ══════════════════════════════════════════════════════════════════
    def _pick_image_file(self):
        path=filedialog.askopenfilename(filetypes=[("Image","*.png *.jpg *.bmp")])
        if path: self._img_path.set(path)

    def _snip_image(self):
        if not VISION_OK: return
        self.withdraw(); time.sleep(0.4)
        snip=tk.Toplevel(); snip.attributes("-fullscreen",True)
        snip.attributes("-alpha",0.3); snip.configure(bg="black")
        snip.attributes("-topmost",True)
        c=tk.Canvas(snip,cursor="cross",bg="black",highlightthickness=0)
        c.pack(fill="both",expand=True)
        co={}
        def _s(e): co["x1"]=e.x; co["y1"]=e.y
        def _d(e):
            c.delete("s"); c.create_rectangle(co["x1"],co["y1"],e.x,e.y,outline=_c("ACCENT"),width=2,tag="s")
        def _e(e):
            co["x2"]=e.x; co["y2"]=e.y; snip.destroy()
            x1=min(co["x1"],co["x2"]); y1=min(co["y1"],co["y2"])
            x2=max(co["x1"],co["x2"]); y2=max(co["y1"],co["y2"])
            img=ImageGrab.grab(bbox=(x1,y1,x2,y2))
            path=filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("PNG","*.png")])
            if path: img.save(path); self._img_path.set(path)
            self.deiconify()
        c.bind("<ButtonPress-1>",_s); c.bind("<B1-Motion>",_d); c.bind("<ButtonRelease-1>",_e)

    def _start_img_watch(self):
        if self._vision_running:
            self._vision_running=False
            self.img_watch_btn.configure(text="👁 START WATCHING")
            self._img_log.set("stopped"); return
        path=self._img_path.get()
        if not os.path.exists(path): messagebox.showwarning("No Image","Pilih gambar dulu!"); return
        try: conf=float(self._img_conf.get())
        except: conf=0.85
        ctype=self._img_ctype.get()
        self._vision_running=True
        self.img_watch_btn.configure(text="■ STOP WATCHING")
        def _w():
            mc=MouseCtrl()
            while self._vision_running:
                try:
                    loc=pyautogui.locateOnScreen(path,confidence=conf)
                    if loc:
                        cx,cy=pyautogui.center(loc)
                        if self.state.humanized:
                            HumanMover.move(mc,cx,cy)
                            HumanClick.click(mc,Button.left,double=(ctype=="dblclick"),
                                             right=(ctype=="right"))
                        else:
                            mc.position=(cx,cy)
                            if ctype=="dblclick": mc.click(Button.left,2)
                            elif ctype=="right":  mc.click(Button.right)
                            else:                 mc.click(Button.left)
                        self._img_log.set(f"✅ @ ({cx},{cy})"); time.sleep(1.0)
                    else: self._img_log.set("👁 Mencari...")
                except Exception as ex: self._img_log.set(f"⚠ {str(ex)[:60]}")
                time.sleep(0.5)
        threading.Thread(target=_w,daemon=True).start()

    def _pick_color(self):
        c=colorchooser.askcolor()
        if c and c[1]: self._col_tgt.set(c[1])

    def _pick_col_pos(self):
        self.iconify()
        def _c():
            time.sleep(3); x,y=(MouseCtrl().position if PYNPUT_OK else (0,0))
            self._col_x.set(str(x)); self._col_y.set(str(y)); self.after(0,self.deiconify)
        threading.Thread(target=_c,daemon=True).start()
        messagebox.showinfo("Pick","Pindah ke posisi watch. 3 detik.")

    def _pick_col_click_pos(self):
        self.iconify()
        def _c():
            time.sleep(3); x,y=(MouseCtrl().position if PYNPUT_OK else (0,0))
            self._col_cx.set(str(x)); self._col_cy.set(str(y)); self.after(0,self.deiconify)
        threading.Thread(target=_c,daemon=True).start()
        messagebox.showinfo("Pick","Pindah ke posisi klik. 3 detik.")

    def _start_col_watch(self):
        if self._vision_running:
            self._vision_running=False
            self.col_watch_btn.configure(text="👁 START WATCHING")
            self._col_log.set("stopped"); return
        if not VISION_OK: return
        try:
            wx=int(self._col_x.get()); wy=int(self._col_y.get())
            tol=int(self._col_tol.get())
            cx_=int(self._col_cx.get()); cy_=int(self._col_cy.get())
        except: messagebox.showerror("Error","Semua nilai harus angka."); return
        tc2=self._col_tgt.get().lstrip("#")
        try: tr,tg,tb=int(tc2[0:2],16),int(tc2[2:4],16),int(tc2[4:6],16)
        except: tr,tg,tb=255,0,0
        self._vision_running=True
        self.col_watch_btn.configure(text="■ STOP WATCHING")
        def _w():
            mc=MouseCtrl()
            while self._vision_running:
                try:
                    img=ImageGrab.grab(bbox=(wx,wy,wx+1,wy+1))
                    pr,pg,pb=img.getpixel((0,0))[:3]
                    if abs(pr-tr)<=tol and abs(pg-tg)<=tol and abs(pb-tb)<=tol:
                        if self.state.humanized:
                            HumanMover.move(mc,cx_,cy_); HumanClick.click(mc)
                        else:
                            mc.position=(cx_,cy_); mc.click(Button.left)
                        self._col_log.set(f"✅ klik @ ({cx_},{cy_})"); time.sleep(0.8)
                    else:
                        self._col_log.set(f"👁 ({pr},{pg},{pb}) ≠ ({tr},{tg},{tb})±{tol}")
                except Exception as ex: self._col_log.set(f"⚠ {str(ex)[:60]}")
                time.sleep(0.3)
        threading.Thread(target=_w,daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    #  CHAINS
    # ══════════════════════════════════════════════════════════════════
    def _add_chain(self):
        if not self.state.recorded_actions:
            messagebox.showwarning("Empty","Record dulu!"); return
        d=tk.Toplevel(self); d.title("New Chain"); d.configure(bg=_c("BG")); d.resizable(False,False)
        nv=tk.StringVar(value="Chain "+str(len(self.state.chains)+1))
        rv=tk.StringVar(value="1"); notev=tk.StringVar(value="")
        for lt,var in [("Nama:",nv),("Repeat:",rv),("Notes:",notev)]:
            r=tk.Frame(d,bg=_c("BG")); r.pack(fill="x",padx=14,pady=4)
            tk.Label(r,text=lt,width=8,anchor="w",font=FONT,bg=_c("BG"),fg=_c("TEXT")).pack(side="left")
            centry(r,var,24).pack(side="left")
        def _ok():
            chain={"name":nv.get(),"repeat":rv.get(),"notes":notev.get(),
                   "actions":copy.deepcopy(self.state.recorded_actions)}
            self.state.chains.append(chain)
            self.chain_tree.insert("","end",values=(chain["name"],len(chain["actions"]),chain["repeat"],chain["notes"]))
            d.destroy()
        cbutton(d,"ADD",_ok).pack(pady=10)

    def _run_chain(self):
        sel=self.chain_tree.selection()
        if not sel: messagebox.showwarning("Pilih","Pilih chain!"); return
        if self.state.is_playing: return
        idx=self.chain_tree.index(sel[0])
        if idx>=len(self.state.chains): return
        chain=self.state.chains[idx]
        try: rep=int(chain["repeat"])
        except: rep=1
        self.state.start_playback("recorded",1.0,rep,0,0,None,None,
                                  actions_override=chain["actions"])
        self._refresh_ui()

    def _del_chain(self):
        for item in self.chain_tree.selection():
            idx=self.chain_tree.index(item); self.chain_tree.delete(item)
            if 0<=idx<len(self.state.chains): self.state.chains.pop(idx)

    # ══════════════════════════════════════════════════════════════════
    #  PROFILES
    # ══════════════════════════════════════════════════════════════════
    def _save_profile(self):
        name=self._prof_var.get().strip()
        if not name: messagebox.showwarning("Nama","Isi nama profil!"); return
        self.state.save_profile(name)
        p=self.state.profiles[name]
        for item in self.prof_tree.get_children():
            if self.prof_tree.item(item,"values")[0]==name:
                self.prof_tree.item(item,values=(name,len(p["actions"]),len(p["targets"]),len(p["chains"]))); return
        self.prof_tree.insert("","end",values=(name,len(p["actions"]),len(p["targets"]),len(p["chains"])))

    def _load_profile_sel(self):
        sel=self.prof_tree.selection()
        if not sel: return
        name=self.prof_tree.item(sel[0],"values")[0]
        self.state.load_profile(name); self._reload_action_tree(); self._reload_ttree()
        if self.tov: self.tov.refresh()
        messagebox.showinfo("Loaded",f"'{name}' dimuat.")

    def _del_profile(self):
        for item in self.prof_tree.selection():
            name=self.prof_tree.item(item,"values")[0]
            self.state.profiles.pop(name,None); self.prof_tree.delete(item)

    # ══════════════════════════════════════════════════════════════════
    #  UI REFRESH
    # ══════════════════════════════════════════════════════════════════
    def _refresh_ui(self):
        if self.state.is_recording:
            self.status_var.set("● RECORDING"); self.status_lbl.configure(fg=_c("ACC2"))
            self.rec_btn.configure(text="⏹ STOP REC (F6)")
            self.hud.set("● REC", "ACC2")
        elif self.state.is_playing:
            self.status_var.set("▶ PLAYING"); self.status_lbl.configure(fg=_c("ACCENT"))
            self.play_btn.configure(text="■ STOP (F5)")
            self.multi_play_btn.configure(text="■ STOP (F5)")
            self.hud.set("▶ PLAY", "ACCENT")
        else:
            self.status_var.set("■ IDLE"); self.status_lbl.configure(fg=_c("MUTED"))
            self.rec_btn.configure(text="⏺ START REC (F6)")
            self.play_btn.configure(text="▶ PLAY (F5)")
            self.multi_play_btn.configure(text="▶ PLAY MULTI (F5)")
            self.hud.set("■ IDLE", "MUTED")

    def _append_log(self, a):
        n=len(self.state.recorded_actions)
        self.action_tree.insert("","end",values=self._arow(n,a))
        self.action_tree.yview_moveto(1)
        self.count_var.set(f"{n} actions")


    def _reload_ttree(self):
        for i in self.ttree.get_children(): self.ttree.delete(i)
        for i,t in enumerate(self.state.targets):
            self.ttree.insert("","end",values=self._trow(i+1,t))

    def _renumber(self, tree):
        for i,item in enumerate(tree.get_children()):
            v=list(tree.item(item,"values")); v[0]=i+1; tree.item(item,values=v)



if __name__ == "__main__":
    app = App()
    app.mainloop()

