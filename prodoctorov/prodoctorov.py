import urllib.request
import json
import datetime
import diskcache
import platformdirs
import telegram
import os
import asyncio

# import user_cache_dir

doctor_id = 803551
lpu_id = 73456

def parse_answer(answer):
	for doctor in answer['result']:
		if doctor['doctor_id'] != doctor_id:
			continue
		if doctor['lpu_id'] != lpu_id:
			continue
		for date, day in doctor['slots'].items():
			if not day:
				continue
			for slot in day:
				if slot['duration'] != 3600:
					continue
				if not slot['free']:
					continue
				if slot['time'] in ('18:00', '19:00', '20:00'):
					yield date, slot['time']

def get_slots(date):
	headers = {
		"accept": "application/json",
		"accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
		"cache-control": "no-cache",
		"content-type": "application/json",
		"origin": "https://prodoctorov.ru",
		"pragma": "no-cache",
		"priority": "u=1, i",
		"referer": f"https://prodoctorov.ru/moskva/vrach/{doctor_id}-pancov/",
		"sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
		"sec-ch-ua-mobile": "?0",
		"sec-ch-ua-platform": '"Linux"',
		"sec-fetch-dest": "empty",
		"sec-fetch-mode": "cors",
		"sec-fetch-site": "same-origin",
		"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
	}

	request_body = {
		"days": 14,
		"dt_start": date.strftime("%Y-%m-%d"),
		"doctors_lpus": [{
			"doctor_id": doctor_id,
			"lpu_id": lpu_id,
			"lpu_timedelta": 3,
			"has_slots": True}],
		"town_timedelta": 3}

	req = urllib.request.Request(
		"https://prodoctorov.ru/ajax/schedule/slots_bulk/",
		json.dumps(request_body).encode('UTF-8'),
		headers)
	
	with urllib.request.urlopen(req) as response:
		for date, time in parse_answer(json.loads(response.read().decode("utf-8"))):
			yield date, time

def main():
	found=[]
	cachedir = platformdirs.user_cache_dir("prodoctorov", "legeyda")
	with diskcache.Cache(cachedir) as cache:
		for date, time in get_slots(datetime.date.today()):
			key = date + '_' + time
			if key in cache:
				continue
			cache[key] = True
			print(date + ' ' + time)
			found.append(date + ' ' + time)
	
	if found:
		bot = telegram.Bot(os.environ['TELEGRAM_API_KEY'])
		if len(found) == 1:
			text = "Найден слот: " + found[0]
		elif len(found) > 1:
			text = "Найдены слоты: " + ', '.join(found)
		asyncio.run(bot.send_message(text = text, chat_id=os.environ['TELEGRAM_CHAT_ID']))

		




if __name__ == "__main__":
	main()

