# PHT logo usage

The supplied logo is included as two pre-sized transparent PNG assets:
- `assets/pht_logo_login.png` for the spacious welcome screen (300 x 200).
- `assets/pht_logo_sidebar.png` for compact navigation sidebars (170 x 114).

Both assets preserve the original aspect ratio and are rendered without runtime resizing or stretching. The Python GUI uses Tkinter's built-in `PhotoImage`, so no additional image library is required. The logo is retained on each view instance to prevent Tkinter from garbage-collecting the image.
