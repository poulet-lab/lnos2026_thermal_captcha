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

from .globals import (
    CHOICE_COUNT,
    CHOICE_FEEDBACK_PAUSE_S,
    ROUND_PROGRESS_PAUSE_S,
    SECOND_MONITOR_HEIGHT,
    SECOND_MONITOR_OFFSET,
    SECOND_MONITOR_WIDTH,
    STIMULUS_TRACES_DIR,
    TRIALS_PER_PERSON,
)
from .monitors import force_window_to_monitor, get_participant_monitor
from .ui_strings import (
    comparison_results_sections,
    first_player_results_sections,
    instructions_screen_sections,
    ready_screen_parts,
    round_progress_parts,
    thanks_screen_parts,
    title_screen_parts,
)

# Dark theme
BG = "#000000"
FG = "#FFFFFF"
BTN_BG = "#111111"
BTN_ACTIVE = "#222222"
TRACE_PAD = "#1a1a1a"
FEEDBACK_GREEN = "#22c55e"
FEEDBACK_RED = "#ef4444"
FEEDBACK_BORDER = 5


class _Command(Enum):
    TITLE = auto()
    INSTRUCTIONS = auto()
    READY = auto()
    ATTENTION = auto()
    ROUND_PROGRESS = auto()
    CHOICES = auto()
    RESULTS = auto()
    THANKS = auto()
    BLANK = auto()
    STOP = auto()


@dataclass
class _Payload:
    command: _Command
    data: dict | None = None


class ParticipantDisplay:
    """Thread-safe fullscreen display on the second monitor."""

    def __init__(self, traces_dir: Path | None = None):
        self.traces_dir = traces_dir or STIMULUS_TRACES_DIR
        self._queue: queue.Queue[_Payload] = queue.Queue()
        self._choice_event = threading.Event()
        self._enter_event = threading.Event()
        self._round_progress_event = threading.Event()
        self._round_progress_ready = threading.Event()
        self._chosen: str | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._photo_refs: list[ImageTk.PhotoImage] = []
        self._advance_enabled = False
        self._queue_wake = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = None
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, name="participant-display", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=10):
            raise RuntimeError("Participant display failed to start")

    def stop(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._thread = None
            return
        self._put(_Command.STOP)
        self._thread.join(timeout=5)
        self._thread = None

    def show_title(self) -> None:
        self._put(_Command.TITLE)

    def show_instructions(self) -> None:
        self._put(_Command.INSTRUCTIONS)

    def show_ready(self) -> None:
        self._put(_Command.READY)

    def show_attention(self, on: bool) -> None:
        self._put(_Command.ATTENTION, {"on": on})

    def show_round_progress(self, trial: int, total: int = TRIALS_PER_PERSON) -> None:
        self._round_progress_event.clear()
        self._round_progress_ready.clear()
        self._put(_Command.ROUND_PROGRESS, {"trial": trial, "total": total})
        self._round_progress_ready.wait()
        self._round_progress_event.wait()

    def show_blank(self) -> None:
        self._put(_Command.BLANK)

    def is_continue_signaled(self) -> bool:
        return self._enter_event.is_set()

    def clear_continue(self) -> None:
        self._enter_event.clear()

    def enable_continue(self) -> None:
        self._advance_enabled = True

    def disable_continue(self) -> None:
        self._advance_enabled = False

    def signal_continue(self) -> None:
        self._enter_event.set()

    def wait_for_continue(self) -> None:
        self._enter_event.clear()
        self._enter_event.wait()

    def wait_for_continue_signal(self) -> None:
        self._enter_event.wait()

    def wait_for_enter(self) -> None:
        """Backward-compatible alias for wait_for_continue()."""
        self.wait_for_continue()

    def show_choices(self, options: list[str], correct_name: str) -> str:
        if len(options) != CHOICE_COUNT:
            raise ValueError(f"Expected {CHOICE_COUNT} options, got {len(options)}")
        if correct_name not in options:
            raise ValueError(f"Correct stimulus {correct_name!r} not in options")
        self._chosen = None
        self._choice_event.clear()
        self._put(_Command.CHOICES, {"options": options, "correct": correct_name})
        self._choice_event.wait()
        assert self._chosen is not None
        return self._chosen

    def show_results(
        self,
        score: int,
        *,
        is_first_player: bool = False,
        above: int = 0,
        same: int = 0,
        below: int = 0,
    ) -> None:
        self._put(
            _Command.RESULTS,
            {
                "score": score,
                "is_first_player": is_first_player,
                "above": above,
                "same": same,
                "below": below,
            },
        )

    def show_thanks(self) -> None:
        self._put(_Command.THANKS)

    def _put(self, command: _Command, data: dict | None = None) -> None:
        self._queue.put(_Payload(command, data))
        wake = self._queue_wake
        if wake is not None:
            try:
                wake()
            except (RuntimeError, tk.TclError):
                pass

    def _run(self) -> None:
        root = tk.Tk()
        self._root = root
        root.title("Thermal Captcha")
        root.configure(bg=BG)
        monitor = self._place_on_second_monitor(root)

        def on_advance(_event=None) -> None:
            if self._advance_enabled:
                root.focus_force()
                self._enter_event.set()

        root.bind("<Return>", on_advance)
        root.bind("<KP_Enter>", on_advance)
        root.bind("<Button-1>", on_advance)

        container = tk.Frame(root, bg=BG)
        container.pack(fill=tk.BOTH, expand=True)

        center_frame = tk.Frame(container, bg=BG)

        title_font = tkfont.Font(root=root, family="Helvetica", size=48, weight="bold")
        score_font = tkfont.Font(root=root, family="Helvetica", size=28, weight="bold")
        body_font = tkfont.Font(root=root, family="Helvetica", size=22)

        title_label = tk.Label(center_frame, text="", font=title_font, bg=BG, fg=FG)
        text_stack = tk.Frame(center_frame, bg=BG)
        dot_canvas = tk.Canvas(center_frame, width=120, height=120, bg=BG, highlightthickness=0)
        choices_frame = tk.Frame(center_frame, bg=BG)
        round_progress_frames: dict[tuple[int, int], tk.Frame] = {}

        def clear_text_stack() -> None:
            for child in text_stack.winfo_children():
                child.destroy()

        def add_bilingual_blocks(
            parent: tk.Frame,
            blocks: list[tuple[str, str]],
            *,
            font=body_font,
        ) -> None:
            for index, (de, en) in enumerate(blocks):
                if index > 0:
                    tk.Frame(parent, height=24, bg=BG).pack()
                tk.Label(
                    parent,
                    text=de,
                    font=font,
                    bg=BG,
                    fg=FG,
                    wraplength=1200,
                    justify=tk.CENTER,
                ).pack(pady=(0, 12))
                tk.Frame(parent, height=2, bg=FG, width=480).pack(
                    fill=tk.X, padx=40, pady=12
                )
                tk.Label(
                    parent,
                    text=en,
                    font=font,
                    bg=BG,
                    fg=FG,
                    wraplength=1200,
                    justify=tk.CENTER,
                ).pack(pady=(12, 0))

        def show_bilingual_blocks(blocks: list[tuple[str, str]], *, font=body_font) -> None:
            clear_text_stack()
            add_bilingual_blocks(text_stack, blocks, font=font)

        def get_round_progress_frame(trial: int, total: int) -> tk.Frame:
            key = (trial, total)
            frame = round_progress_frames.get(key)
            if frame is None:
                frame = tk.Frame(center_frame, bg=BG)
                add_bilingual_blocks(
                    frame,
                    [round_progress_parts(trial, total)],
                    font=score_font,
                )
                round_progress_frames[key] = frame
                frame.update_idletasks()
            return frame

        def show_titled_bilingual_section(
            de_title: str,
            de_body: str,
            en_title: str,
            en_body: str,
        ) -> None:
            clear_text_stack()
            tk.Label(
                text_stack,
                text=de_title,
                font=title_font,
                bg=BG,
                fg=FG,
                wraplength=1200,
                justify=tk.CENTER,
            ).pack(pady=(0, 16))
            tk.Label(
                text_stack,
                text=de_body,
                font=body_font,
                bg=BG,
                fg=FG,
                wraplength=1200,
                justify=tk.CENTER,
            ).pack(pady=(0, 12))
            tk.Frame(text_stack, height=2, bg=FG, width=480).pack(fill=tk.X, padx=40, pady=12)
            tk.Label(
                text_stack,
                text=en_title,
                font=title_font,
                bg=BG,
                fg=FG,
                wraplength=1200,
                justify=tk.CENTER,
            ).pack(pady=(12, 16))
            tk.Label(
                text_stack,
                text=en_body,
                font=body_font,
                bg=BG,
                fg=FG,
                wraplength=1200,
                justify=tk.CENTER,
            ).pack(pady=(0, 0))

        def show_results_section(
            de_headline: str,
            de_body: str,
            en_headline: str,
            en_body: str,
        ) -> None:
            clear_text_stack()
            tk.Label(
                text_stack,
                text=de_headline,
                font=score_font,
                bg=BG,
                fg=FG,
                wraplength=1200,
                justify=tk.CENTER,
            ).pack(pady=(0, 16))
            tk.Label(
                text_stack,
                text=de_body,
                font=body_font,
                bg=BG,
                fg=FG,
                wraplength=1200,
                justify=tk.CENTER,
            ).pack(pady=(0, 12))
            tk.Frame(text_stack, height=2, bg=FG, width=480).pack(fill=tk.X, padx=40, pady=12)
            tk.Label(
                text_stack,
                text=en_headline,
                font=score_font,
                bg=BG,
                fg=FG,
                wraplength=1200,
                justify=tk.CENTER,
            ).pack(pady=(12, 16))
            tk.Label(
                text_stack,
                text=en_body,
                font=body_font,
                bg=BG,
                fg=FG,
                wraplength=1200,
                justify=tk.CENTER,
            ).pack(pady=(0, 0))

        def hide_all() -> None:
            center_frame.place_forget()
            for w in (title_label, text_stack, dot_canvas, choices_frame):
                w.pack_forget()
            for w in round_progress_frames.values():
                w.pack_forget()
            clear_text_stack()
            for child in choices_frame.winfo_children():
                child.destroy()
            self._photo_refs.clear()

        def show_centered() -> None:
            center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        def show_title_view() -> None:
            hide_all()
            title_text, body_block = title_screen_parts()
            title_label.config(text=title_text)
            show_bilingual_blocks([body_block])
            show_centered()
            title_label.pack(pady=(0, 20))
            text_stack.pack()
            root.focus_force()

        def show_instructions_view() -> None:
            hide_all()
            (de_title, de_body), (en_title, en_body) = instructions_screen_sections()
            show_titled_bilingual_section(de_title, de_body, en_title, en_body)
            show_centered()
            text_stack.pack()
            root.focus_force()

        def show_ready_view() -> None:
            hide_all()
            show_bilingual_blocks([ready_screen_parts()])
            show_centered()
            text_stack.pack()
            root.focus_force()

        def show_thanks_view() -> None:
            hide_all()
            show_bilingual_blocks([thanks_screen_parts()])
            show_centered()
            text_stack.pack()
            root.focus_force()

        def show_attention_view(on: bool) -> None:
            hide_all()
            dot_canvas.delete("all")
            if on:
                dot_canvas.create_oval(10, 10, 110, 110, fill="#22c55e", outline="")
            show_centered()
            dot_canvas.pack()

        def show_round_progress_view(trial: int, total: int) -> None:
            round_progress_frame = get_round_progress_frame(trial, total)
            hide_all()
            show_centered()
            round_progress_frame.pack()
            root.update_idletasks()
            root.focus_force()
            if round_progress_after_id[0] is not None:
                root.after_cancel(round_progress_after_id[0])
            self._round_progress_ready.set()
            pause_ms = int(ROUND_PROGRESS_PAUSE_S * 1000)
            round_progress_after_id[0] = root.after(pause_ms, finish_round_progress)

        round_progress_after_id: list[str | None] = [None]

        def finish_round_progress() -> None:
            round_progress_after_id[0] = None
            hide_all()
            root.update_idletasks()
            self._round_progress_event.set()

        for trial in range(1, TRIALS_PER_PERSON + 1):
            get_round_progress_frame(trial, TRIALS_PER_PERSON)

        def show_results_view(
            score: int,
            is_first_player: bool,
            above: int,
            same: int,
            below: int,
        ) -> None:
            hide_all()
            if is_first_player:
                (de_headline, de_body), (en_headline, en_body) = first_player_results_sections(
                    score
                )
            else:
                (de_headline, de_body), (en_headline, en_body) = comparison_results_sections(
                    score, above, same, below
                )
            show_results_section(de_headline, de_body, en_headline, en_body)
            show_centered()
            text_stack.pack()
            root.focus_force()

        def show_choices_view(options: list[str], correct_name: str) -> None:
            hide_all()
            self._photo_refs.clear()
            if choice_feedback_after_id[0] is not None:
                root.after_cancel(choice_feedback_after_id[0])
                choice_feedback_after_id[0] = None

            choice_frames: dict[str, tk.Frame] = {}
            choice_locked = [False]

            def finish_choice() -> None:
                choice_feedback_after_id[0] = None
                self._choice_event.set()

            def on_click(stim: str) -> None:
                if choice_locked[0]:
                    return
                choice_locked[0] = True
                self._chosen = stim
                for btn in choice_frames.values():
                    for child in btn.winfo_children():
                        if isinstance(child, tk.Button):
                            child.config(state=tk.DISABLED)
                if stim == correct_name:
                    choice_frames[stim].config(highlightbackground=FEEDBACK_GREEN)
                else:
                    choice_frames[stim].config(highlightbackground=FEEDBACK_RED)
                    choice_frames[correct_name].config(highlightbackground=FEEDBACK_GREEN)
                root.update_idletasks()
                pause_ms = int(CHOICE_FEEDBACK_PAUSE_S * 1000)
                choice_feedback_after_id[0] = root.after(pause_ms, finish_choice)

            for i, name in enumerate(options):
                path = self.traces_dir / f"{name}.png"
                img = Image.open(path)
                img = img.resize((280, 140), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._photo_refs.append(photo)

                border = tk.Frame(
                    choices_frame,
                    bg=BG,
                    highlightthickness=FEEDBACK_BORDER,
                    highlightbackground=TRACE_PAD,
                )
                btn = tk.Button(
                    border,
                    image=photo,
                    command=lambda stim=name: on_click(stim),
                    bd=2,
                    relief=tk.RAISED,
                    bg=TRACE_PAD,
                    activebackground=BTN_ACTIVE,
                    highlightbackground=BTN_BG,
                )
                btn.pack()
                border.grid(row=i // 3, column=i % 3, padx=16, pady=16)
                choice_frames[name] = border

            show_centered()
            choices_frame.pack()
            root.focus_force()

        choice_feedback_after_id: list[str | None] = [None]

        queue_wake_pending = [False]

        def poll_queue(*, schedule_next: bool = True) -> None:
            queue_wake_pending[0] = False
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
                    elif payload.command is _Command.READY:
                        show_ready_view()
                    elif payload.command is _Command.ATTENTION:
                        show_attention_view(bool(payload.data and payload.data.get("on")))
                    elif payload.command is _Command.ROUND_PROGRESS:
                        d = payload.data
                        show_round_progress_view(d["trial"], d["total"])
                    elif payload.command is _Command.CHOICES:
                        d = payload.data
                        show_choices_view(d["options"], d["correct"])
                    elif payload.command is _Command.RESULTS:
                        d = payload.data
                        show_results_view(
                            d["score"],
                            d["is_first_player"],
                            d["above"],
                            d["same"],
                            d["below"],
                        )
                    elif payload.command is _Command.THANKS:
                        show_thanks_view()
                    elif payload.command is _Command.BLANK:
                        hide_all()
            except queue.Empty:
                pass
            if schedule_next:
                root.after(50, poll_queue)

        def wake_queue() -> None:
            if queue_wake_pending[0]:
                return
            queue_wake_pending[0] = True
            root.after(0, lambda: poll_queue(schedule_next=False))

        self._queue_wake = wake_queue

        self._ready.set()
        poll_queue()
        root.mainloop()
        try:
            root.destroy()
        except tk.TclError:
            pass
        self._queue_wake = None
        self._root = None

    def _place_on_second_monitor(self, root: tk.Tk):
        monitor = get_participant_monitor(
            fallback_offset=SECOND_MONITOR_OFFSET,
            fallback_width=SECOND_MONITOR_WIDTH,
            fallback_height=SECOND_MONITOR_HEIGHT,
        )
        root.overrideredirect(True)
        root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        root.update_idletasks()
        force_window_to_monitor(root.winfo_id(), monitor)
        root.lift()
        root.focus_force()
        return monitor
