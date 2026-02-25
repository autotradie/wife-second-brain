import requests, os
url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage"
r = requests.post(url, json={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": "test"})
print(r.text)