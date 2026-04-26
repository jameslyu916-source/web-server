# Comp 2322 Multi-threaded Web Server
This is my submission for the Comp 2322 Computer Networking project. It's a basic multi-threaded web server written from scratch in Python using socket programming.

---

## What You Need First
Just **Python 3.x** installed on your computer. That's it. No extra libraries required.

---

## How to Run This Thing
1.  **Open your terminal/command prompt** and navigate into the main `web-server` folder (the one with `server.py` in it).
2.  **Double-check your files**:
    *   Make sure there's a `test_files` folder here.
    *   Inside `test_files`, you should have at least `index.html`, `style.css`, and `script.js`.
3.  **Start the server**:
    ```bash
    python server.py
    ```
    *(If that doesn't work, try `python3 server.py` instead.)*
4.  **Test it in your browser**:
    Go to `http://127.0.0.1:6789`

---

## Stopping the Server
Go back to the terminal window where the server is running and press **Ctrl + C**.

---

## Quick Test Checklist (For TA)
*   ✅ Accessing `/` loads `index.html`
*   ✅ CSS and JS files load correctly (background is light blue, alert pops up)
*   ✅ Accessing a non-existent file returns `404 Not Found`
*   ✅ Accessing a hidden file (like `/.test`) returns `403 Forbidden`
*   ✅ `server.log` file is created and logs all requests
*   ✅ Multiple browser tabs can load pages at the same time (multi-threading works)
