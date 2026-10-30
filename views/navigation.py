"""Shared host for authenticated pages to keep the Tk root window stable."""
import tkinter as tk


def get_page_container(window, background="#F3F9FA"):
    """Return a persistent frame used by authenticated pages.

    The top-level window is never cleared during page navigation. Only the
    contents of this frame are replaced, preventing window resize/flash effects.
    """
    container = getattr(window, "_pht_page_container", None)
    if container is None or not container.winfo_exists():
        container = tk.Frame(window, bg=background, bd=0, highlightthickness=0)
        container.pack(fill="both", expand=True)
        window._pht_page_container = container
    else:
        container.configure(bg=background)
    return container


def clear_page(container):
    for widget in container.winfo_children():
        widget.destroy()
