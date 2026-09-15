import os, sys, subprocess, traceback, threading, multiprocessing
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def ensure_pymupdf():
    try:
        import pymupdf
        return pymupdf
    except Exception:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "PyMuPDF"])
        import pymupdf
        return pymupdf

def unique_output_paths(output_dir, base_name, need_pdf=True, need_jpg=False):
    """Choose a conflict-safe matched name without overwriting existing output."""
    n = 0
    while True:
        suffix = "" if n == 0 else f" ({n})"
        candidate_name = base_name + suffix
        pdf_path = os.path.join(output_dir, candidate_name + ".pdf")
        jpg_dir = os.path.join(output_dir, candidate_name)

        pdf_conflict = need_pdf and os.path.exists(pdf_path)
        jpg_conflict = need_jpg and os.path.exists(jpg_dir)

        if not pdf_conflict and not jpg_conflict:
            return pdf_path, jpg_dir
        n += 1

def merge_pdf(input_path, output_path, keep_front):
    pm = ensure_pymupdf()
    src = pm.open(input_path)
    total = src.page_count
    if total == 0:
        src.close()
        raise ValueError("PDF has no pages.")

    out = pm.open()

    for i in range(min(keep_front, total)):
        r = src.load_page(i).rect
        p = out.new_page(width=r.width, height=r.height)
        p.show_pdf_page(p.rect, src, i)

    i = keep_front
    while i < total:
        if i + 1 < total:
            r1 = src.load_page(i).rect
            r2 = src.load_page(i + 1).rect
            p = out.new_page(width=r1.width + r2.width, height=max(r1.height, r2.height))
            p.show_pdf_page(pm.Rect(0, 0, r1.width, r1.height), src, i)
            p.show_pdf_page(pm.Rect(r1.width, 0, r1.width + r2.width, r2.height), src, i + 1)
            i += 2
        else:
            r = src.load_page(i).rect
            p = out.new_page(width=r.width, height=r.height)
            p.show_pdf_page(p.rect, src, i)
            i += 1

    out.save(output_path, garbage=4, deflate=True)
    out.close()
    src.close()

def _render_one_jpg_process(pdf_path, page_no, out_path, dpi, quality):
    # Top-level worker so Windows multiprocessing / PyInstaller can spawn it safely.
    import pymupdf as pm
    doc = pm.open(pdf_path)
    try:
        page = doc.load_page(page_no)
        scale = float(dpi) / 72.0
        pix = page.get_pixmap(matrix=pm.Matrix(scale, scale), alpha=False)
        try:
            data = pix.tobytes("jpeg", jpg_quality=int(quality))
            with open(out_path, "wb") as f:
                f.write(data)
        except TypeError:
            pix.save(out_path)
    finally:
        doc.close()
    return page_no


def export_pdf_to_jpg(pdf_path, jpg_dir, dpi=150, quality=90, pause_event=None,
                      progress_callback=None, workers=None):
    if pause_event is None:
        pause_event = threading.Event()
        pause_event.set()

    # Ensure the dependency exists before child processes are spawned.
    pm = ensure_pymupdf()
    doc = pm.open(pdf_path)
    page_count = doc.page_count
    doc.close()

    os.makedirs(jpg_dir, exist_ok=True)
    digits = max(3, len(str(page_count)))

    cpu = os.cpu_count() or 2
    if workers is None:
        workers = max(1, cpu - 1)
    workers = max(1, min(int(workers), cpu, max(1, page_count)))

    done_count = 0
    next_page = 0
    pending = set()

    # Keep only about one batch in flight. This makes Pause responsive: already
    # running pages finish, but no new pages are dispatched while paused.
    with ProcessPoolExecutor(max_workers=workers) as pool:
        while done_count < page_count:
            while pause_event.is_set() and next_page < page_count and len(pending) < workers:
                out_path = os.path.join(jpg_dir, f"{next_page+1:0{digits}d}.jpg")
                pending.add(pool.submit(
                    _render_one_jpg_process,
                    pdf_path, next_page, out_path, dpi, quality
                ))
                next_page += 1

            if not pending:
                pause_event.wait()
                continue

            finished, pending = wait(pending, timeout=0.15, return_when=FIRST_COMPLETED)
            for job in finished:
                job.result()
                done_count += 1
                if progress_callback:
                    progress_callback(done_count, page_count)


def get_root_base():
    try:
        from tkinterdnd2 import TkinterDnD
        return TkinterDnD.Tk, True
    except Exception:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--user", "tkinterdnd2"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            from tkinterdnd2 import TkinterDnD
            return TkinterDnD.Tk, True
        except Exception:
            return tk.Tk, False

RootBase, DND_AVAILABLE = get_root_base()

class App(RootBase):
    def __init__(self, initial_files=None):
        super().__init__()
        self.title("PDF Spread Batch Tool v16")
        self.geometry("850x680")
        self.minsize(700, 620)
        self.files = []
        self.keep_var = tk.IntVar(value=0)
        self.output_dir = tk.StringVar(value="")
        self.output_mode_var = tk.StringVar(value="merge_pdf")
        self.jpg_dpi_var = tk.StringVar(value="150")
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.processing = False

        top = tk.Frame(self)
        top.pack(fill="x", padx=14, pady=(14,8))

        tk.Button(top, text="Add PDFs...", command=self.add_files, width=13).pack(side="left")
        tk.Button(top, text="Remove selected", command=self.remove_selected, width=15).pack(side="left", padx=8)
        tk.Button(top, text="Clear", command=self.clear_files, width=9).pack(side="left")

        self.drop_label = tk.Label(
            self,
            text="Drop PDF files here",
            relief="groove",
            bd=2,
            height=3,
            font=("Segoe UI", 11)
        )
        self.drop_label.pack(fill="x", padx=14, pady=(0,8))

        if DND_AVAILABLE:
            try:
                from tkinterdnd2 import DND_FILES
                self.drop_label.drop_target_register(DND_FILES)
                self.drop_label.dnd_bind("<<Drop>>", self.on_drop)
            except Exception:
                self.drop_label.config(text="Drop unavailable - use Add PDFs")
        else:
            self.drop_label.config(text="Drop unavailable - use Add PDFs")

        opt = tk.LabelFrame(self, text="Cover setting (applies to ALL files)")
        opt.pack(fill="x", padx=14, pady=8)
        tk.Radiobutton(opt, text="0  No cover: 1+2, 3+4, 5+6...", variable=self.keep_var, value=0).pack(anchor="w", padx=12, pady=(8,3))
        tk.Radiobutton(opt, text="1  Keep page 1 as cover: 2+3, 4+5, 6+7...", variable=self.keep_var, value=1).pack(anchor="w", padx=12, pady=(3,8))

        out_frame = tk.LabelFrame(self, text="Output folder")
        out_frame.pack(fill="x", padx=14, pady=8)
        out_frame.columnconfigure(0, weight=1)
        tk.Entry(out_frame, textvariable=self.output_dir).grid(row=0, column=0, sticky="ew", padx=(10,8), pady=10)
        tk.Button(out_frame, text="Browse...", command=self.choose_output_folder, width=12).grid(row=0, column=1, padx=(0,10), pady=10)

        mode_frame = tk.LabelFrame(self, text="Output mode")
        mode_frame.pack(fill="x", padx=14, pady=8)

        tk.Radiobutton(
            mode_frame,
            text="Merge PDF only",
            variable=self.output_mode_var,
            value="merge_pdf"
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8,3))

        tk.Radiobutton(
            mode_frame,
            text="Merge PDF + export merged pages as JPG",
            variable=self.output_mode_var,
            value="merge_jpg"
        ).grid(row=1, column=0, sticky="w", padx=12, pady=3)

        tk.Radiobutton(
            mode_frame,
            text="Original pages to JPG only (no merge, no PDF output)",
            variable=self.output_mode_var,
            value="original_jpg"
        ).grid(row=2, column=0, sticky="w", padx=12, pady=(3,8))

        tk.Label(mode_frame, text="DPI:").grid(row=0, column=1, rowspan=3, sticky="e", padx=(24,4), pady=8)
        dpi_box = ttk.Combobox(
            mode_frame,
            textvariable=self.jpg_dpi_var,
            values=("150", "200", "300"),
            width=7,
            state="readonly"
        )
        dpi_box.grid(row=0, column=2, rowspan=3, sticky="w", padx=(2,12), pady=8)

        # Reserve the bottom controls before giving the file list the remaining space.
        # This keeps Start / Pause visible even on shorter displays or with Windows
        # display scaling enabled.
        info_label = tk.Label(
            self,
            text="JPG export automatically uses all but one logical CPU core. Pause stops dispatching new pages.",
            fg="#666"
        )
        info_label.pack(side="bottom", pady=(0,8))

        bottom = tk.Frame(self)
        bottom.pack(side="bottom", fill="x", padx=14, pady=(5,10))
        self.count_label = tk.Label(bottom, text="0 files")
        self.count_label.pack(side="left")

        self.pause_button = tk.Button(
            bottom,
            text="Pause",
            command=self.toggle_pause,
            width=12,
            height=2,
            state="disabled"
        )
        self.pause_button.pack(side="right", padx=(8,0))

        self.merge_button = tk.Button(
            bottom,
            text="Start",
            command=self.merge_all,
            width=20,
            height=2
        )
        self.merge_button.pack(side="right")

        # The file list is the only vertically flexible area. It shrinks first
        # when the window is short, rather than pushing the controls off-screen.
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True, padx=14, pady=8)

        self.tree = ttk.Treeview(frame, columns=("file","status"), show="headings", selectmode="extended")
        self.tree.heading("file", text="PDF")
        self.tree.heading("status", text="Status")
        self.tree.column("file", width=650, anchor="w")
        self.tree.column("status", width=130, anchor="center")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        if initial_files:
            self.add_paths(initial_files)

    def add_paths(self, paths):
        for p in paths:
            p = os.path.abspath(p)
            if os.path.isfile(p) and p.lower().endswith(".pdf") and p not in self.files:
                self.files.append(p)
                self.tree.insert("", "end", iid=str(len(self.files)-1), values=(p, "Ready"))
        self.refresh_tree_ids()

    def refresh_tree_ids(self):
        # Rebuild to keep IDs simple after removals.
        current = list(self.files)
        for x in self.tree.get_children():
            self.tree.delete(x)
        for idx, p in enumerate(current):
            self.tree.insert("", "end", iid=str(idx), values=(p, "Ready"))
        self.count_label.config(text=f"{len(self.files)} files")

    def on_drop(self, event):
        try:
            paths = list(self.tk.splitlist(event.data))
            self.add_paths(paths)
        except Exception as e:
            messagebox.showerror("Drop error", str(e))

    def choose_output_folder(self):
        initial = self.output_dir.get().strip()
        folder = filedialog.askdirectory(
            title="Choose output folder",
            initialdir=initial if os.path.isdir(initial) else None
        )
        if folder:
            self.output_dir.set(folder)

    def add_files(self):
        paths = filedialog.askopenfilenames(title="Choose PDFs", filetypes=[("PDF files","*.pdf")])
        self.add_paths(paths)

    def remove_selected(self):
        indices = sorted([int(i) for i in self.tree.selection()], reverse=True)
        for i in indices:
            if 0 <= i < len(self.files):
                self.files.pop(i)
        self.refresh_tree_ids()

    def clear_files(self):
        self.files.clear()
        self.refresh_tree_ids()

    def toggle_pause(self):
        if not self.processing:
            return

        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.config(text="Resume")
        else:
            self.pause_event.set()
            self.pause_button.config(text="Pause")

    def ui_set_status(self, idx, text):
        self.after(0, lambda: self.tree.set(str(idx), "status", text))

    def ui_finish(self, ok, total, errors):
        def finish():
            self.processing = False
            self.pause_event.set()
            self.pause_button.config(text="Pause", state="disabled")
            self.merge_button.config(state="normal")
            self.config(cursor="")

            if errors:
                messagebox.showwarning(
                    "Finished",
                    f"Done: {ok}/{total}\\n\\nErrors:\\n" + "\\n".join(errors[:10])
                )
            else:
                messagebox.showinfo("Finished", f"All {ok} PDFs finished.")
        self.after(0, finish)

    def merge_all(self):
        if self.processing:
            return

        if not self.files:
            messagebox.showwarning("No files", "Please add one or more PDF files.")
            return

        output_dir = self.output_dir.get().strip()
        if not output_dir:
            messagebox.showwarning("Output folder", "Please choose an output folder.")
            return
        if not os.path.isdir(output_dir):
            messagebox.showwarning("Output folder", "The selected output folder does not exist.")
            return

        keep = self.keep_var.get()
        mode = self.output_mode_var.get()
        dpi = int(self.jpg_dpi_var.get())
        process_workers = None  # automatic: logical CPU count - 1

        self.processing = True
        self.pause_event.set()
        self.pause_button.config(text="Pause", state="normal")
        self.merge_button.config(state="disabled")
        self.config(cursor="wait")

        files_snapshot = list(self.files)

        def worker():
            ok = 0
            errors = []

            for idx, src in enumerate(files_snapshot):
                try:
                    # Pause before starting each file.
                    self.pause_event.wait()

                    base_name = os.path.splitext(os.path.basename(src))[0]
                    need_pdf = mode in ("merge_pdf", "merge_jpg")
                    need_jpg = mode in ("merge_jpg", "original_jpg")
                    out, jpg_dir = unique_output_paths(
                        output_dir, base_name, need_pdf=need_pdf, need_jpg=need_jpg
                    )

                    def jpg_progress(done, total, _idx=idx):
                        self.ui_set_status(_idx, f"JPG {done}/{total}")

                    if mode == "original_jpg":
                        self.ui_set_status(idx, "Exporting original JPG...")
                        export_pdf_to_jpg(
                            src,
                            jpg_dir,
                            dpi=dpi,
                            quality=90,
                            pause_event=self.pause_event,
                            progress_callback=jpg_progress,
                            workers=process_workers
                        )
                    else:
                        self.ui_set_status(idx, "Merging PDF...")
                        merge_pdf(src, out, keep)

                        if mode == "merge_jpg":
                            self.pause_event.wait()
                            self.ui_set_status(idx, "Exporting merged JPG...")
                            export_pdf_to_jpg(
                                out,
                                jpg_dir,
                                dpi=dpi,
                                quality=90,
                                pause_event=self.pause_event,
                                progress_callback=jpg_progress,
                                workers=process_workers
                            )

                    self.ui_set_status(idx, "Done")
                    ok += 1

                except Exception as e:
                    self.ui_set_status(idx, "Error")
                    errors.append(f"{os.path.basename(src)}: {e}")

            self.ui_finish(ok, len(files_snapshot), errors)

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        dropped = [p for p in sys.argv[1:] if os.path.isfile(p) and p.lower().endswith(".pdf")]
        App(dropped).mainloop()
    except Exception:
        log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_log.txt")
        with open(log, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())