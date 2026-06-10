import requests
import threading
import time

MENU_URL = "https://raw.githubusercontent.com/Carpe-Omnia/showProducts/main/products.json"

# Cached menu string that gets injected into the system prompt
_menu_text = "Menu not loaded yet."
_lock = threading.Lock()


def _format_menu(products: list) -> str:
    """Convert raw JSON products into clean readable text for the prompt."""
    categories = {}
    
    for p in products:
        cat = p.get("category", "OTHER")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(
            f"  - {p['name']} | {p.get('meta', 'N/A')} | {p.get('price', 'N/A')}"
        )
    
    lines = ["CURRENT MENU (updated every 30 minutes):"]
    for cat, items in categories.items():
        lines.append(f"\n{cat}:")
        lines.extend(items)
    
    return "\n".join(lines)


def _fetch_and_update():
    """Fetch menu from GitHub and update the cache."""
    global _menu_text
    try:
        response = requests.get(MENU_URL, timeout=10)
        response.raise_for_status()
        products = response.json()
        formatted = _format_menu(products)
        with _lock:
            _menu_text = formatted
        print(f"[menu] Loaded {len(products)} products successfully.")
    except Exception as e:
        print(f"[menu] Failed to fetch menu: {e}. Using cached version.")


def _background_updater():
    """Runs in a background thread, refreshes menu every 30 minutes."""
    while True:
        _fetch_and_update()
        time.sleep(30 * 60)


def get_menu_text() -> str:
    """Get the current cached menu string."""
    with _lock:
        return _menu_text


def start(blocking=False):
    """
    Start the menu fetcher.
    blocking=True does the first fetch before returning (safe for startup).
    Background thread keeps it fresh after that.
    """
    if blocking:
        _fetch_and_update()
    
    thread = threading.Thread(target=_background_updater, daemon=True)
    thread.start()