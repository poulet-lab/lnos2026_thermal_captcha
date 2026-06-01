"""Tkinter participant display on the second monitor."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from tkinter import font as tkfont

from PIL import Image, ImageTk

from .config import Settings, load_settings
from .globals import CHOICE_COUNT, STIMULUS_TRACES_DIR, TRIALS_PER_PERSON


class _Command(Enum):
    TITLE = auto()
    INSTRUCTIONS = auto()
    ATTENTION = auto()
    CHOICES = auto()
    RESULTS = auto()
    BLANK = auto()
    STOP = auto()


@dataclass
class _Payload:
    command: _Command
    data: dict | None = None


class ParticipantDisplay:
    """Thread-safe fullscreen display on the second monitor."""

    def __init__(self, settings: Settings | None = None, traces_dir: Path | None = None):
        self.settings = settings or load_settings()
        self.traces_dir = traces_dir or STIMULUS_TRACES_DIR
        self._queue: queue.Queue[_Payload] = queue.Queue()
        self._choice_event = threading.Event()
        self._chosen: str | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._photo_refs: list[ImageTk.PhotoImage] = []

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, name="participant-display", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=10):
            raise RuntimeError("Participant display failed to start")

    def stop(self) -> None:
        self._queue.put(_Payload(_Command.STOP))
        if self._thread is not None:
            self._thread.join(timeout=5)

    def show_title(self) -> None:
        self._put(_Command.TITLE)

    def show_instructions(self) -> None:
        self._put(_Command.INSTRUCTIONS)

    def show_attention(self, on: bool) -> None:
        self._put(_Command.ATTENTION, {"on": on})

    def show_choices(self, options: list[str]) -> str:
        if len(options) != CHOICE_COUNT:
            raise ValueError(f"Expected {CHOICE_COUNT} options, got {len(options)}")
        self._chosen = None
        self._choice_event.clear()
        self._put(_Command.CHOICES, {"options": options})
        self._choice_event.wait()
        assert self._chosen is not None
        return self._chosen

    def show_results(self, score: int, above: int, same: int, below: int) -> None:
        self._put(
            _Command.RESULTS,
            {"score": score, "above": above, "same": same, "below": below},
        )

    def _put(self, command: _Command, data: dict | None = None) -> None:
        self._queue.put(_Payload(command, data))

    def _run(self) -> None:
        root = tk.Tk()
        root.title("Thermal Captcha")
        root.configure(bg="white")
        self._place_on_second_monitor(root)

        container = tk.Frame(root, bg="white")
        container.pack(fill=tk.BOTH, expand=True)

        title_font = tkfont.Font(family="Helvetica", size=48, weight="bold")
        body_font = tkfont.Font(family="Helvetica", size=22)
        small_font = tkfont.Font(family="Helvetica", size=18)

        title_label = tk.Label(container, text="", font=title_font, bg="white", fg="black")
        body_label = tk.Label(
            container, text="", font=body_font, bg="white", fg="black", wraplength=900, justify=tk.CENTER
        )
        dot_canvas = tk.Canvas(container, width=120, height=120, bg="white", highlightthickness=0)
        choices_frame = tk.Frame(container, bg="white")
        results_label = tk.Label(
            container, text="", font=body_font, bg="white", fg="black", wraplength=1000, justify=tk.CENTER
        )

        def hide_all() -> None:
            for w in (title_label, body_label, dot_canvas, choices_frame, results_label):
                w.pack_forget()
            for child in choices_frame.winfo_children():
                child.destroy()
            self._photo_refs.clear()

        def show_title_view() -> None:
            hide_all()
            title_label.config(text="Thermal Captcha")
            body_label.config(
                text="Press Enter to start",
                font=body_font,
            )
            title_label.pack(pady=(120, 20))
            body_label.pack(pady=20)

        def show_instructions_view() -> None:
            hide_all()
            title_label.config(text="Instructions")
            body_label.config(
                text=(
                    "When you see the green dot, pay attention to what you feel "
                    "on your skin through the thermal stimulator.\n\n"
                    "You will then see six drawings — click the one that looks most "
                    "like what you just felt."
                ),
                font=body_font,
            )
            title_label.pack(pady=(80, 20))
            body_label.pack(pady=20, padx=40)

        def show_attention_view(on: bool) -> None:
            hide_all()
            dot_canvas.delete("all")
            if on:
                dot_canvas.create_oval(10, 10, 110, 110, fill="#22c55e", outline="")
            dot_canvas.pack(expand=True)

        def show_results_view(score: int, above: int, same: int, below: int) -> None:
            hide_all()
            if score < TRIALS_PER_PERSON:
                above_line = f"{above} people got {score + 1} or more correct"
            else:
                above_line = f"{above} people scored higher than you"
            same_line = f"{same} people got the same as you ({score})"
            if score > 0:
                below_line = f"{below} people got {score - 1} or less"
            else:
                below_line = f"{below} people scored lower than you"
            results_label.config(
                text=(
                    f"You got {score} out of {TRIALS_PER_PERSON} correct!\n\n"
                    f"{above_line}\n"
                    f"{same_line}\n"
                    f"{below_line}"
                ),
                font=body_font,
            )
            results_label.pack(expand=True, pady=80)

        def show_choices_view(options: list[str]) -> None:
            hide_all()
            self._photo_refs.clear()
            for i, name in enumerate(options):
                path = self.traces_dir / f"{name}.png"
                img = Image.open(path)
                img = img.resize((280, 140), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._photo_refs.append(photo)

                def on_click(_event=None, stim=name) -> None:
                    self._chosen = stim
                    self._choice_event.set()

                btn = tk.Button(
                    choices_frame,
                    image=photo,
                    command=on_click,
                    bd=2,
                    relief=tk.RAISED,
                    bg="white",
                )
                btn.grid(row=i // 3, column=i % 3, padx=16, pady=16)
            choices_frame.pack(expand=True, pady=40)

        def poll_queue() -> None:
            try:
                while True:
                    payload = self._queue.get_nowait()
                    if payload.command is _Command.STOP:
                        root.quit()
                        return
                    if payload.command is _Command.TITLE:
                        show_title_view()
                    elif payload.command is _Command.INSTRUCTIONS:
                        show_instructions_view()
                    elif payload.command is _Command.ATTENTION:
                        show_attention_view(bool(payload.data and payload.data.get("on")))
                    elif payload.command is _Command.CHOICES:
                        show_choices_view(payload.data["options"])
                    elif payload.command is _Command.RESULTS:
                        d = payload.data
                        show_results_view(d["score"], d["above"], d["same"], d["below"])
                    elif payload.command is _Command.BLANK:
                        hide_all()
            except queue.Empty:
                pass
            root.after(50, poll_queue)

        ready.set()
        self._ready.set()
        poll_queue()
        root.mainloop()

    def _place_on_second_monitor(self, root: tk.Tk) -> None:
        root.update_idletasks()
        offset = self.settings.second_monitor_offset
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        if offset > 0:
            root.geometry(f"{width}x{height}+{offset}+0")
        else:
            root.geometry(f"{width}x{height}+0+0")
        root.attributes("-fullscreen", True)
