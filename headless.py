import os
import json
import urllib.request
import urllib.parse

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
        return None

    with open(STATE_FILE, "r") as file:
        return json.load(file)


def save_state(on_sale, price):
    with open(STATE_FILE, "w") as file:
        json.dump({
            "on_sale": on_sale,
            "price": price
        }, file)


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

    old_state = load_state()

    # Primera comprobación
    if old_state is None:

        save_state(on_sale, price)

        if on_sale:
            message = (
                "🎃 <b>HEADLESS HORSEMAN</b>\n\n"
                "🟢 <b>ESTÁ A LA VENTA</b>\n"
                f"💰 Precio: <b>{price:,} Robux</b>\n\n"
                "🛒 https://www.roblox.com/bundles/201/Headless-Horseman"
            )
        else:
            message = (
                "🎃 <b>HEADLESS HORSEMAN</b>\n\n"
                "🔴 <b>NO ESTÁ A LA VENTA</b>"
            )

        send_telegram(message)
        return

    old_on_sale = old_state.get("on_sale", False)

    # Ha pasado de NO estar a la venta → A LA VENTA
    if on_sale and not old_on_sale:

        message = (
            "🚨🎃 <b>HEADLESS HORSEMAN</b> 🎃🚨\n\n"
            "🟢 <b>¡ESTÁ A LA VENTA!</b>\n"
            f"💰 Precio: <b>{price:,} Robux</b>\n\n"
            "🛒 https://www.roblox.com/bundles/201/Headless-Horseman"
        )

        send_telegram(message)

    # Ha pasado de estar a la venta → NO A LA VENTA
    elif not on_sale and old_on_sale:

        message = (
            "🔴 <b>HEADLESS HORSEMAN</b>\n\n"
            "❌ <b>YA NO ESTÁ A LA VENTA</b>"
        )

        send_telegram(message)

    save_state(on_sale, price)


if __name__ == "__main__":
    main()
