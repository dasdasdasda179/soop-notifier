import json
import os
import requests

STATE_FILE = "state.json"

CHANNELS = [
    {
        "id": "mintyerim07",
        "name": "mintyerim07",
        "webhook_env": "WEBHOOK_MINTYERIM07",
    },
    {
        "id": "serena06",
        "name": "serena06",
        "webhook_env": "WEBHOOK_SERENA06",
    },
]


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def is_channel_live(channel_id: str) -> tuple[bool, str]:
    url = f"https://chapi.sooplive.co.kr/api/{channel_id}/station"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            return False, ""
        data = res.json()
        broad = data.get("broad")
        if broad and broad.get("broad_no"):
            title = broad.get("broad_title", "配信中")
            return True, title
        return False, ""
    except Exception as e:
        print(f"[{channel_id}] check error: {e}")
        return False, ""


def send_discord_notification(webhook_url: str, channel_id: str, title: str) -> None:
    watch_url = f"https://play.sooplive.co.kr/{channel_id}"
    payload = {
        "content": f"🔴 **{channel_id}** が配信を開始しました！\n**タイトル:** {title}\n{watch_url}"
    }
    res = requests.post(webhook_url, json=payload, timeout=15)
    res.raise_for_status()


def main() -> None:
    state = load_state()
    changed = False

    for ch in CHANNELS:
        ch_id = ch["id"]
        webhook_url = os.environ.get(ch["webhook_env"], "").strip()

        live, title = is_channel_live(ch_id)
        prev_live = bool(state.get(ch_id, {}).get("is_live", False))
        prev_title = state.get(ch_id, {}).get("title", "")

        if live and (not prev_live or title != prev_title):
            if webhook_url:
                send_discord_notification(webhook_url, ch_id, title)
                print(f"[{ch_id}] Notification sent: {title}")
            else:
                print(f"[{ch_id}] Webhook URL is not set ({ch['webhook_env']})")

        if prev_live != live or prev_title != title:
            state[ch_id] = {"is_live": live, "title": title}
            changed = True

    if changed:
        save_state(state)


if __name__ == "__main__":
    main()
