import os
import json
import urllib.request
import urllib.parse
import subprocess

BUNDLE_ID = 201
CHAT_ID = "6920969559"

ROBLOX_URL = f"https://catalog.roblox.com/v1/bundles/{BUNDLE_ID}/details"

TOKEN = os.environ["TELEGRAM_TOKEN"]
STATE_FILE = "state.json"


def get_roblox_data():
    request = urllib.request.Request(
        ROBLOX_URL,
        headers={"User-Agent": "RobloxHeadlessMonitor/1.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "on_sale": False,
            "price": None
        }

    with open(STATE_FILE, "r") as file:
        return json.load(file)


def save_state(state):
    with open(STATE_FILE, "w") as file:
        json.dump(state, file)


def commit_state():
    subprocess.run(["git", "config", "user.name", "Headless Monitor"])
    subprocess.run(["git", "config", "user.email", "headless@github.com"])
    subprocess.run(["git", "add", STATE_FILE])
    subprocess.run(
        ["git", "commit", "-m", "Update Headless state"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    subprocess.run(["git", "push"])


def main():
    data = get_roblox_data()

    product = data.get("product", {})
    collectible = data.get("collectibleItemDetail", {})

    name = data.get("name", "Headless Horseman")

    is_for_sale = product.get("isForSale", False)
    sale_status = collectible.get("saleStatus")

    on_sale = is_for_sale or sale_status == "OnSale"

    price = (
        product.get("priceInRobux")
        or collectible.get("price")
    )

    state = load_state()

    was_on_sale = state.get("on_sale", False)
    old_price = state.get("price")

    # Avisar cuando pasa de fuera de venta a disponible
    if on_sale and not was_on_sale:
        message = (
            "🎃 <b>HEADLESS HORSEMAN DISPONIBLE</b>\n\n"
            f"🐎 {name}\n"
            f"💰 Precio: <b>{price:,} Robux</b>\n"
            "🟢 Estado: <b>EN VENTA</b>\n\n"
            "🛒 https://www.roblox.com/bundles/201/Headless-Horseman"
        )

        send_telegram(message)

    # Si ya estaba disponible y cambia el precio, avisar también
    elif on_sale and was_on_sale and price != old_price:
        message = (
            "💰 <b>CAMBIO DE PRECIO - HEADLESS HORSEMAN</b>\n\n"
            f"🐎 {name}\n"
            f"💰 Nuevo precio: <b>{price:,} Robux</b>\n\n"
            "🛒 https://www.roblox.com/bundles/201/Headless-Horseman"
        )

        send_telegram(message)

    state["on_sale"] = on_sale
    state["price"] = price

    save_state(state)

    if os.environ.get("GITHUB_ACTIONS") == "true":
        commit_state()


if __name__ == "__main__":
    main()