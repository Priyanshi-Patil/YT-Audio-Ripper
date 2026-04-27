#!/usr/bin/env python3
"""
YT Audio Ripper — landscape layout, auto YT thumbnail if no cover chosen
Requirements: pip install yt-dlp mutagen Pillow requests
              + ffmpeg installed and in PATH
"""

import os, sys, threading, io
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import subprocess

# ─── Auto-install deps ───────────────────────────────────────────────────────
def _install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

for _dep, _mod in [("yt-dlp","yt_dlp"),("mutagen","mutagen"),("Pillow","PIL"),("requests","requests")]:
    try: __import__(_mod)
    except ImportError:
        print(f"Installing {_dep}…"); _install(_dep)

import yt_dlp, requests
from mutagen.id3 import ID3, APIC, TIT2, TPE1, ID3NoHeaderError
from PIL import Image, ImageTk

# ─── Theme ───────────────────────────────────────────────────────────────────
BG      = "#0d0d0d"
SURFACE = "#161616"
CARD    = "#1e1e1e"
BORDER  = "#2a2a2a"
ACCENT  = "#ff3c3c"
ACCENT2 = "#ff7c3c"
TEXT    = "#f0f0f0"
SUB     = "#777777"
OK      = "#3cff8f"
WARN    = "#ffcc3c"

FT  = ("Georgia",   18, "bold")
FL  = ("Consolas",   9)
FI  = ("Consolas",  10)
FB  = ("Consolas",  10, "bold")

# ─── Downloader logic ────────────────────────────────────────────────────────
class Downloader:
    def __init__(self):
        self.video_info = None
        self.cover_path = None
        self.output_dir = str(Path.home() / "Downloads")

    def fetch_info(self, url):
        with yt_dlp.YoutubeDL({"quiet":True,"no_warnings":True,"skip_download":True}) as ydl:
            self.video_info = ydl.extract_info(url, download=False)
        return self.video_info

    def download_audio(self, url, filename, outdir, on_progress=None, on_done=None, on_error=None):
        safe = "".join(c for c in filename if c not in r'\/:*?"<>|').strip()
        tmpl = os.path.join(outdir, f"{safe}.%(ext)s")

        def hook(d):
            if d["status"] == "downloading" and on_progress:
                try: on_progress(float(d.get("_percent_str","0%").strip().rstrip("%")))
                except: pass
            elif d["status"] == "finished" and on_progress:
                on_progress(99)

        opts = {
            "format": "bestaudio/best",
            "outtmpl": tmpl,
            "postprocessors": [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}],
            "progress_hooks": [hook],
            "quiet": True, "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            mp3 = os.path.join(outdir, f"{safe}.mp3")

            # Cover priority: custom file > YT thumbnail > nothing
            if self.cover_path and os.path.exists(self.cover_path):
                self._embed_file(mp3, self.cover_path, filename)
            elif self.video_info:
                thumb = self.video_info.get("thumbnail")
                if thumb:
                    self._embed_url(mp3, thumb, filename)

            if on_done: on_done(mp3)
        except Exception as e:
            if on_error: on_error(str(e))

    def _embed_file(self, mp3, path, title):
        try:
            img = Image.open(path).convert("RGB")
            buf = io.BytesIO(); img.save(buf, "JPEG", quality=90)
            self._write(mp3, buf.getvalue(), title)
        except Exception as e: print("Cover error:", e)

    def _embed_url(self, mp3, url, title):
        try:
            r = requests.get(url, timeout=10)
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            buf = io.BytesIO(); img.save(buf, "JPEG", quality=90)
            self._write(mp3, buf.getvalue(), title)
        except Exception as e: print("Thumb error:", e)

    def _write(self, mp3, img_bytes, title):
        try: audio = ID3(mp3)
        except ID3NoHeaderError: audio = ID3()
        audio["APIC"] = APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img_bytes)
        if title: audio["TIT2"] = TIT2(encoding=3, text=title)
        if self.video_info:
            ch = self.video_info.get("uploader","")
            if ch: audio["TPE1"] = TPE1(encoding=3, text=ch)
        audio.save(mp3)


# ─── GUI ─────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.dl = Downloader()
        self.cover_img_ref = self.thumb_img_ref = None

        self.title("YT Audio Ripper")
        self.configure(bg=BG)
        self.geometry("860x540")
        self.resizable(False, False)
        self._build()

    # ── layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(18,0))
        tk.Label(hdr, text="◈ YT AUDIO RIPPER", font=FT, bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(hdr, text="mp3 + cover art", font=FL, bg=BG, fg=SUB).pack(side="left", padx=(10,0), pady=(6,0))
        tk.Button(hdr, text="▶ DOWNLOAD MP3", font=FB, bg=ACCENT, fg="#fff",
                  activebackground=ACCENT2, activeforeground="#fff",
                  relief="flat", cursor="hand2", command=self._on_download
                  ).pack(side="right", ipady=6, ipadx=14)
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x", padx=24, pady=(8,12))

        # ── Two-column body ──────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24)

        left  = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0,10))

        right = tk.Frame(body, bg=BG, width=220)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # ── LEFT column ──────────────────────────────────────────────────────

        # URL row
        self._lbl(left, "① YOUTUBE URL")
        url_row = self._card(left)
        self.url_var = tk.StringVar()
        tk.Entry(url_row, textvariable=self.url_var, font=FI, bg=SURFACE, fg=TEXT,
                 insertbackground=ACCENT, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT).pack(side="left", fill="x", expand=True, ipady=6, padx=(0,8))
        self._btn(url_row, "FETCH", self._on_fetch, side="right")

        # Info card
        self._lbl(left, "② VIDEO INFO")
        info_c = self._card(left, height=80)
        self.thumb_lbl = tk.Label(info_c, bg=CARD, width=9)
        self.thumb_lbl.pack(side="left", padx=(0,10))
        ir = tk.Frame(info_c, bg=CARD); ir.pack(side="left", fill="both", expand=True)
        self.title_var = tk.StringVar(value="—")
        self.chan_var  = tk.StringVar(value="—")
        self.dur_var   = tk.StringVar(value="—")
        for lbl, var in [("Title", self.title_var),("Channel", self.chan_var),("Duration", self.dur_var)]:
            row = tk.Frame(ir, bg=CARD); row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{lbl}:", font=FL, bg=CARD, fg=SUB, width=7, anchor="w").pack(side="left")
            tk.Label(row, textvariable=var, font=FL, bg=CARD, fg=TEXT, anchor="w").pack(side="left")

        # Filename
        self._lbl(left, "③ FILENAME  (editable)")
        fn_c = self._card(left)
        self.fname_var = tk.StringVar()
        tk.Entry(fn_c, textvariable=self.fname_var, font=FI, bg=SURFACE, fg=TEXT,
                 insertbackground=ACCENT, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT).pack(fill="x", expand=True, ipady=6)

        # Output folder
        self._lbl(left, "④ SAVE TO FOLDER")
        dir_c = self._card(left)
        self.dir_var = tk.StringVar(value=self.dl.output_dir)
        tk.Label(dir_c, textvariable=self.dir_var, font=FL, bg=CARD, fg=TEXT, anchor="w").pack(
            side="left", fill="x", expand=True)
        self._btn(dir_c, "BROWSE", self._on_browse, side="right")

        # Progress + download
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=(12,8))
        self.status_var = tk.StringVar(value="ready.")
        self.status_lbl = tk.Label(left, textvariable=self.status_var, font=FL, bg=BG, fg=SUB, anchor="w")
        self.status_lbl.pack(fill="x")

        prog_bg = tk.Frame(left, bg=SURFACE, height=5)
        prog_bg.pack(fill="x", pady=(4,0)); prog_bg.pack_propagate(False)
        self.prog_fill = tk.Frame(prog_bg, bg=ACCENT, height=5)
        self.prog_fill.place(x=0, y=0, relheight=1, width=0)
        self._prog_bg = prog_bg

        # ── RIGHT column — cover art ──────────────────────────────────────────
        self._lbl(right, "⑤ CUSTOM COVER")
        cov_frame = tk.Frame(right, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        cov_frame.pack(fill="x", pady=(0,6))

        self.cover_preview = tk.Label(cov_frame, bg=SURFACE,
                                      text="auto\nYT thumb", font=FL, fg=SUB,
                                      width=20, height=8)
        self.cover_preview.pack(padx=10, pady=10)

        btn_f = tk.Frame(cov_frame, bg=CARD); btn_f.pack(fill="x", padx=10, pady=(0,8))
        self._btn(btn_f, "CHOOSE IMAGE", self._on_choose_cover)
        self._btn(btn_f, "CLEAR", self._on_clear_cover, color=BORDER, fg=SUB)

        self.cover_path_var = tk.StringVar(value="using YT thumbnail")
        tk.Label(cov_frame, textvariable=self.cover_path_var, font=FL, bg=CARD,
                 fg=SUB, wraplength=190, justify="left").pack(padx=10, pady=(0,10))

        tk.Label(right, text="ffmpeg required\nyt-dlp · mutagen · Pillow",
                 font=FL, bg=BG, fg=BORDER, justify="center").pack(pady=(10,0))



    # ── helpers ──────────────────────────────────────────────────────────────
    def _lbl(self, parent, text):
        tk.Label(parent, text=text, font=FL, bg=BG, fg=SUB).pack(anchor="w", pady=(8,3))

    def _card(self, parent, height=None):
        kw = {"height": height} if height else {}
        f = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER, **kw)
        f.pack(fill="x", pady=(0,2))
        if height: f.pack_propagate(False)
        inner = tk.Frame(f, bg=CARD)
        inner.pack(fill="both", expand=True, padx=10, pady=8)
        return inner

    def _btn(self, parent, text, cmd, side="left", color=ACCENT, fg="#fff"):
        tk.Button(parent, text=text, font=FB, bg=color, fg=fg,
                  activebackground=ACCENT2, activeforeground="#fff",
                  relief="flat", cursor="hand2", command=cmd
                  ).pack(side=side, padx=(0,4) if side=="left" else (4,0), ipady=5, ipadx=8)

    def _set_progress(self, pct):
        self.update_idletasks()
        w = int(self._prog_bg.winfo_width() * pct / 100)
        self.prog_fill.place(x=0, y=0, relheight=1, width=w)

    def _set_status(self, msg, color=SUB):
        self.status_var.set(msg)
        self.status_lbl.configure(fg=color)

    # ── actions ──────────────────────────────────────────────────────────────
    def _on_fetch(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Paste a YouTube URL first."); return
        self._set_status("fetching…", WARN); self._set_progress(0)
        def go():
            try:
                info = self.dl.fetch_info(url)
                self.after(0, lambda: self._fill_info(info))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"error: {e}", ACCENT))
        threading.Thread(target=go, daemon=True).start()

    def _fill_info(self, info):
        title = info.get("title","Unknown")
        secs  = info.get("duration", 0)
        self.title_var.set(title[:55]+("…" if len(title)>55 else ""))
        self.chan_var.set(info.get("uploader","Unknown"))
        self.dur_var.set(f"{secs//60}:{secs%60:02d}" if secs else "?")
        self.fname_var.set(title)
        self._set_status("ready — edit filename or cover, then download.", OK)
        self._set_progress(10)
        thumb = info.get("thumbnail")
        if thumb:
            threading.Thread(target=self._load_thumb, args=(thumb,), daemon=True).start()

    def _load_thumb(self, url):
        try:
            r = requests.get(url, timeout=8)
            img = Image.open(io.BytesIO(r.content)).resize((72,50), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.thumb_img_ref = tk_img
            self.after(0, lambda: self.thumb_lbl.configure(image=tk_img, text=""))
        except: pass

    def _on_choose_cover(self):
        path = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Images","*.jpg *.jpeg *.png *.webp *.bmp"),("All","*.*")])
        if not path: return
        self.dl.cover_path = path
        self.cover_path_var.set(os.path.basename(path))
        try:
            img = Image.open(path).resize((160,160), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self.cover_img_ref = tk_img
            self.cover_preview.configure(image=tk_img, text="")
        except: pass

    def _on_clear_cover(self):
        self.dl.cover_path = None
        self.cover_path_var.set("using YT thumbnail")
        self.cover_preview.configure(image="", text="auto\nYT thumb")
        self.cover_img_ref = None

    def _on_browse(self):
        p = filedialog.askdirectory(title="Select Output Folder")
        if p: self.dl.output_dir = p; self.dir_var.set(p)

    def _on_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Paste a YouTube URL first."); return
        if not self.dl.video_info:
            messagebox.showwarning("Fetch First", "Click FETCH before downloading."); return
        fname  = self.fname_var.get().strip() or self.dl.video_info.get("title","audio")
        outdir = self.dl.output_dir
        self._set_status("downloading…", WARN); self._set_progress(0)

        def prog(p): self.after(0, lambda v=p: (self._set_progress(v), self._set_status(f"downloading… {v:.0f}%", WARN)))
        def done(p): self.after(0, lambda: (self._set_progress(100), self._set_status(f"saved → {os.path.basename(p)}", OK), messagebox.showinfo("Done!", f"Saved to:\n{p}")))
        def err(e):  self.after(0, lambda: (self._set_status(f"error: {e}", ACCENT), messagebox.showerror("Error", e)))

        threading.Thread(target=self.dl.download_audio,
                         args=(url, fname, outdir, prog, done, err), daemon=True).start()


if __name__ == "__main__":
    App().mainloop()