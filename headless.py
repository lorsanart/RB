import os
import json
import base64
import urllib.request
import urllib.parse
import urllib.error

BUNDLE_ID = 201
CHAT_ID = "6920969559"

ROBLOX_URL = f"https://catalog.roblox.com/v1/bundles/{BUNDLE_ID}/details"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

OWNER = "lorsanart"
REPO = "RB"
STATE_PATH = "state.json"


def request_json(url, method="GET", data=None, headers=None):
    headers = headers or {}
    headers["User-Agent"] = "HeadlessMonitor/1.0"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode())


def get_roblox_data():
    return request_json(
        ROBLOX_URL,
        headers={"User-Agent": "HeadlessMonitor/1.0"}
    )


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }).encode()

    result = request_json(
        url,
        method="POST",
        data=data
    )

    print("Telegram:", "OK" if result.get("ok") else "ERROR")

    if not result.get("ok"):
        raise RuntimeError(f"Telegram rechazó el mensaje: {result}")


def get_state():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{STATE_PATH}"

    try:
        result = request_json(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "X-GitHub-Api-Version": "2026-03-10"
            }
        )

        content = base64.b64decode(
            result["content"].replace("\n", "")
        ).decode()

        return json.loads(content), result["sha"]

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        raise


def save_state(state, sha=None):
    content = json.dumps(state, indent=2).encode()
    encoded = base64.b64encode(content).decode()

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{STATE_PATH}"

    body = {
        "message": "Update Headless state",
        "content": encoded,
        "branch": "main"
    }

    if sha:
        body["sha"] = sha

    data = json.dumps(body).encode()

    result = request_json(
        url,
        method="PUT",
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2026-03-10",
            "Content-Type": "application/json"
        }
    )

    print("Estado guardado en GitHub: OK")


def main():

    print("Comprobando Headless Horseman...")

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

    print(f"Estado: {'EN VENTA' if on_sale else 'NO ESTÁ EN VENTA'}")
    print(f"Precio: {price}")

    old_state, sha = get_state()

    # Primera ejecución
    if old_state is None:

        if on_sale:
            message = (
                "🎃 <b>HEADLESS HORSEMAN</b>\n\n"
                "🟢 <b>¡ESTÁ A LA VENTA!</b>\n"
                f"💰 Precio: <b>{price:,} Robux</b>\n\n"
                "🛒 https://www.roblox.com/bundles/201/Headless-Horseman"
            )
        else:
            message = (
                "🎃 <b>HEADLESS HORSEMAN</b>\n\n"
                "🔴 <b>NO ESTÁ A LA VENTA</b>"
            )

        send_telegram(message)

    else:

        old_on_sale = old_state.get("on_sale", False)

        # NO VENTA → VENTA
        if on_sale and not old_on_sale:

            message = (
                "🚨🎃 <b>HEADLESS HORSEMAN</b> 🎃🚨\n\n"
                "🟢 <b>¡ESTÁ A LA VENTA!</b>\n"
                f"💰 Precio: <b>{price:,} Robux</b>\n\n"
                "🛒 https://www.roblox.com/bundles/201/Headless-Horseman"
            )

            send_telegram(message)

        # VENTA → NO VENTA
        elif not on_sale and old_on_sale:

            message = (
                "🔴 <b>HEADLESS HORSEMAN</b>\n\n"
                "❌ <b>YA NO ESTÁ A LA VENTA</b>"
            )

            send_telegram(message)

    save_state({
        "on_sale": on_sale,
        "price": price
    }, sha)


if __name__ == "__main__":
    main()
