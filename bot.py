ULTRA_TOXIC_MODE = False
import asyncio
import re
import os

import json
import random
import time

from datetime import datetime, timedelta


from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatPermissions
from aiogram.filters import Command





# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- DATA ----------------
DATA_FILE = "bot_data.json"


warnings_db = {}
reputation_db = {}
rep_cooldown = {}
message_tracker = {}

message_stats = {}  # теперь {chat_id: {user_id: {дата: кол-во}}}

SPAM_LIMIT = 8
SPAM_TIME = 4

# Флаг, чтобы не сохранять файл каждую секунду
stats_changed = False

rules_text = """
📜 *Правила чата*  
(читай внимательно — нарушение = последствия)

1. *Без спама* — никаких флуда, копипасты, одинаковых сообщений подряд  
2. *Без оскорблений* — ни личных, ни в сторону других участников  
3. *Без рекламы* — любые ссылки на каналы, магазины, проекты и т.д. только с разрешения админа  
4. *Уважение* — к участникам, их мнению и личным границам  
5. *Мат* — разрешён в меру и без направленности на людей (не токсичный троллинг)  
6. *Строго запрещено публиковать*:  
   • Лоли / шота / любые изображения с несовершеннолетними в сексуальном контексте  
   • Фута / любые формы порно с нечеловеческими пропорциями в явном виде  
   • Казино, ставки, крипто-скам, фишинг  
   • Любые подозрительные файлы, ссылки на вирусы/майнеры  
   • Шок-контент, gore, жестокость без контекста

Нарушение любого пункта → предупреждение → мут → бан (в зависимости от тяжести).

Приятного общения! 🔥
"""

actions = {
    "пожать": "🤝 жмет руку",
    "обнять": "🤗 обнимает",
    "поцеловать": "💋 целует",
    "рука": "🫱 подает руку помощи",
    "ударить": "👊 бьет",
    "накричать": "😡 кричит на",
    "погладить": "🥰 гладит по голове",
    "погладитьпо": "🥰 гладит по",
    "по голове": "🥰 гладит по голове",
    "по плечу": "👏 хлопает по плечу",
    "дать пять": "✋ даёт пять",
    "high five": "✋ даёт пять",
    "пнуть": "🦶 пинает",
    "пнуть в жопу": "🦶 пинает в жопу",
    "поцеловать в щёку": "😘 целует в щёчку",
    "поцеловать в щеку": "😘 целует в щёчку",
    "поцеловать в нос": "😘 целует в носик",
    "потрепать": "😄 треплет по волосам",
    "по волосам": "😄 треплет по волосам",
    "прижать": "🫂 крепко прижимает к себе",
    "прижаться": "🫂 прижимается",
    "кусь": "😈 кусь за щёчку",
    "укусить": "😈 кусает",
    "лизнуть": "👅 лижет",
    "лизнуть щеку": "👅 лижет щёчку",
    "шлёпнуть": "👋 шлёпает по попе",
    "шлепнуть": "👋 шлёпает по попе",
    "тыкнуть": "👉 тыкает пальцем",
    "ткнуть": "👉 тыкает пальцем",
    "пихнуть": "🤜 толкает",
    "толкнуть": "🤜 толкает",
    "пощекотать": "😂 щекочет",
    "за уши": "😏 тянет за уши",
    "дернуть за уши": "😏 тянет за уши",
    "похлопать": "👏 хлопает по спине",
    "по спине": "👏 хлопает по спине",
    "подмигнуть": "😏 подмигивает",
    "послать воздушный поцелуй": "😘 посылает воздушный поцелуй",
    "воздушный поцелуй": "😘 посылает воздушный поцелуй",
    "показать язык": "😝 показывает язык",
    "язык": "😝 показывает язык",
    "погладить по спине": "🥰 гладит по спине",
    "массаж": "💆 делает массаж плеч",
    "плеч": "💆 делает массаж плеч",
    "спину": "💆 делает массаж спины",
    "поцеловать в лоб": "💋 целует в лобик",
    "в лоб": "💋 целует в лобик",
    "в щёку": "💋 целует в щёчку",
    "облизать": "👅 облизывает",
    "нюхнуть": "👃 нюхает",
    "понюхать": "👃 нюхает",
    "принюхаться": "👃 принюхивается",
    "схватить за сиськи": "😏 хватает за грудь",
    "схватить за грудь": "😏 хватает за грудь",
    "за сиськи": "😏 хватает за сиськи",
    "сжать попку": "🍑 сжимает попку",
    "шлёпнуть по жопе": "👋 шлёпает по жопе",
    "по попе": "👋 шлёпает по попе",
    "ущипнуть за сосок": "😈 ущипывает за сосок",
    "лизнуть шею": "👅 лижет шею",
    "куснуть за ухо": "😈 кусает за ушко",
    "прижать к стене": "🫦 прижимает к стене",
    "зажать между ног": "😏 зажимает между ног",
    "погладить по бедру": "🥵 гладит по бедру",
    "схватить за волосы": "💦 хватает за волосы",
    "дернуть за волосы": "💦 тянет за волосы",
    "поцеловать в шею": "😘 целует в шею",
    "лизнуть грудь": "👅 лижет грудь",
    "пососать сосок": "😈 посасывает сосок",
    "поглаживать попу": "🍑 гладит попку",
    "сунуть руку под юбку": "😏 лезет рукой под юбку",
    "пощупать между ног": "🥵 трогает между ног",
    "выебать": "😈 выебывает жёстко",
    "трахнуть": "🥵 трахает без остановки",
    "оттрахать": "💦 оттрахивает до крика",
    "отыметь": "🔥 отымел как следует",
    "ебать": "😏 ебёт без пощады",
    "вставить": "🍆 вставляет глубоко",
    "засадить": "🍆 засадил по самые яйца",
    "отшпилить": "🔥 отшпиливает как следует",
    "отпиздить": "🍑 отпиздил по полной",
    "отъебать": "😈 отъебал до потери пульса",
    "выебать в жопу": "🍑 выебал в жопу",
    "трахнуть в рот": "👄 трахает в рот",
    "отсосать": "👅 отсасывает как профи",
    "пососать": "👅 посасывает член",
    "лизать пизду": "👅 лижет пизду",
    "вылизать": "👅 вылизывает до дрожи",
    "кончить в рот": "💦 кончает в рот",
    "кончить на лицо": "💦 кончает на лицо",
    "залить спермой": "💦 заливает спермой",
    "оттрахать в анал": "🍑 трахает в анал",
    "разъебать жопу": "🍑 разъебал жопу",
    "отшлёпать и выебать": "👋 шлёпает и выебывает",
    "заставить сосать": "😈 заставляет сосать",
    "отдать в ротик": "👄 отдаёт в ротик",
    "насадить на хуй": "🍆 насаживает на хуй",
    "отъебать до слёз": "😭 отъебал до слёз",
    "выебать до крика": "😩 выебал до крика",
    "трахнуть раком": "🐶 трахает раком",
    "оттрахать догги": "🐶 оттрахал догги-стайл",
    "уебать": "🪓 уебал(а) сковородой по башке",
    "уебать сковородой": "🪓 уебал(а) сковородой по башке",
    "спиздить": "🕵️‍♂️ спиздил(а) всё, что плохо лежит",
    "вскрыть": "🔪 вскрыл(а) грудную клетку",
    "вскрыть позвоночник": "🪚 вскрыл(а) позвоночник",
    "чай": "☕ налил(а) кипяток в глаза",
    "растрелить": "🔫 расстрелял(а) в упор",
    "респритировать": "💀 респритировал(а) в мясо",
    "толкнуть": "🤜 толкнул(а) с 9-го этажа",
    "ракетная бомбардировка": "🚀 устроил(а) ракетную бомбардировку",
    "взятка": "💰 сунул(а) взятку в жопу",
    "подстрелил": "🔫 подстрелил(а) в колено",
    "кастрировать": "✂️ кастрировал(а) без наркоза",
    "общий сбор мужити": "🗣️ объявил(а) общий сбор мужити на разборки",
    "продать на органы": "🫀 продал(а) на органы",
    "продать в рабство": "⛓️ продал(а) в сексуальное рабство",
    "сделать куни": "👅 сделал(а) куни до потери сознания",
    "отрезать яйца": "✂️ отрезал(а) яйца и скормил(а) собаке",
    "вырвать кишки": "🪚 вырвал(а) кишки через рот",
    "размозжить череп": "🔨 размозжил(а) череп кувалдой",
    "зарезать": "🔪 зарезал(а) как свинью",
    "сжечь заживо": "🔥 сжёг(ла) заживо",
    "утопить в сортире": "🚽 утопил(а) головой в сортире",
    "отрубить голову": "🪓 отрубил(а) голову топором",
    "раздавить катком": "🚜 раздавил(а) катком",
    "задушить проводом": "🔌 задушил(а) сетевым кабелем",
    "взорвать в жопе": "💣 взорвал(а) динамит в жопе",
    "отравить ртутью": "☠️ отравил(а) ртутью в кофе",
    "распилить бензопилой": "⛓️ распилил(а) бензопилой пополам",
    "засунуть в микроволновку": "📡 засунул(а) в микроволновку",
    "сварить в кислоте": "🧪 сварил(а) в серной кислоте",
    "отдать на опыты": "🧪 отдал(а) на опыты вивисекторам",
    "сделать минет под дулом": "🔫 заставил(а) сосать под дулом пистолета",
    "изнасиловать битой": "⚾ изнасиловал(а) битой",
    "выколоть глаза": "👁️ выколол(а) глаза ложкой",
    "отрезать уши": "✂️ отрезал(а) уши и надел(а) на шею",
    "содрать кожу": "🪚 содрал(а) кожу заживо",
    "распять на кресте": "✝️ распял(а) на кресте",
    "сжечь на костре": "🔥 сжёг(ла) на инквизиторском костре",
    "закопать живьём": "⚰️ закопал(а) живьём",
    "скормить свиньям": "🐷 скормил(а) свиньям",
    "вырвать сердце": "❤️ вырвал(а) сердце голыми руками",
    "расприссировать": "🔪 расприссировал(а) на куски как свинью",
    "расприссировал": "🩸 расприссировал(а) и разложил(а) по пакетам",
    "автоматом получил пизды": "🔫 автоматом получил(а) пизды в упор",
    "получить пизды": "👊 автоматом влупил(а) пизды очередью",
    "влупить пизды": "💥 влупил(а) пизды из АК-47",
    "расстрелять очередью": "🔥 расстрелял(а) длинной очередью",
    "получить свинец": "🩸 получил(а) свинец в ебало",
    "набить ебало": "👊 набил(а) ебало до каши",
    "размазать по стенке": "🧱 размазал(а) по стенке как таракана",
    "выбить мозги": "🧠 выбил(а) мозги прикладом",
    "отрезать хуй": "✂️ отрезал(а) хуй и скормил(а) хозяину",
    "вырвать яйца": "🥚 вырвал(а) яйца с корнем",
    "засунуть гранату": "💣 засунул(а) гранату в жопу и дернул(а) чеку",
    "поджечь яйца": "🔥 поджёг(ла) яйца бензином",
    "раздавить голову": "🪨 раздавил(а) голову прессом",
    "отрубить ноги": "🪚 отрубил(а) ноги циркуляркой",
    "выколоть глаза": "👁️ выколол(а) глаза вилкой",
    "засадить лом в жопу": "🔧 засадил(а) лом в жопу по самые гланды",
    "отрезать пальцы": "✂️ отрезал(а) пальцы один за одним",
    "вырвать язык": "👅 вырвал(а) язык плоскогубцами",
    "залить глаза кислотой": "🧪 залил(а) глаза серной кислотой",
    "распороть живот": "🔪 распорот(а) живот и выпустил(а) кишки",
    "разбить череп об стену": "🧱 разбил(а) череп об стену до хруста",
    "задушить кишками": "🪢 задушил(а) собственными кишками",
    "скормить живьём": "🐊 скормил(а) живьём крокодилам",
    "разорвать на части": "🩸 разорвал(а) на части голыми руками",
    "взорвать голову": "💥 взорвал(а) голову динамитом",
    "отпилить ноги": "🪚 отпилил(а) ноги ржавой пилой",
    "выжечь глаза": "🔥 выжег(ла) глаза паяльником",
    "засунуть в блендер": "🥤 засунул(а) в блендер и включил(а)",
    "раздавить яйца молотком": "🔨 раздавил(а) яйца молотком",
    "вырвать сердце": "❤️ вырвал(а) сердце и съел(а) на глазах",
    "распять на заборе": "✝️ распял(а) на заборе колючей проволокой",

}

ultra_toxic = [
    
    # "уебать", "уебать сковородой",
    # "вскрыть", "вскрыть позвоночник",
    # "растрелить", "расстрелять очередью",
    # "расприссировать", "расприссировал",
    # "кастрировать", "отрезать яйца", "вырвать яйца", "раздавить яйца молотком",
    # "отрезать хуй",
    # "вырвать кишки", "распороть живот",
    # "размозжить череп", "выбить мозги", "разбить череп об стену", "взорвать голову",
    # "зарезать", "сжечь заживо", "сжечь на костре", "поджечь яйца",
    # "утопить в сортире", "закопать живьём", "скормить свиньям", "скормить живьём",
    # "отрубить голову", "отрубить ноги", "отпилить ноги", "распилить бензопилой",
    # "выколоть глаза", "залить глаза кислотой", "выжечь глаза",
    # "содрать кожу", "вырвать язык", "отрезать уши", "отрезать пальцы",
    # "вырвать сердце", "задушить кишками", "задушить проводом",
    # "взорвать в жопе", "засунуть гранату", "засадить лом в жопу",
    # "сварить в кислоте", "засунуть в микроволновку", "засунуть в блендер",
    # "раздавить голову", "раздавить катком", "разорвать на части",
    # "распять на кресте", "распять на заборе",
    # "отдать на опыты", "продать на органы", "продать в рабство",
    # "изнасиловать битой", "сделать минет под дулом",
    # "выебать", "трахнуть", "оттрахать", "отъебать", "ебать", "засадить", "отшпилить",
    # "выебать в жопу", "оттрахать в анал", "разъебать жопу", "трахнуть раком", "оттрахать догги",
    # "кончить в рот", "кончить на лицо", "залить спермой",
    # "отъебать до слёз", "выебать до крика", "отъебал до потери пульса",

]

welcome_list = [
    "🔥 Добро пожаловать, {name}!",
    "👋 {name} залетел!",
    "🎉 Новый участник — {name}",
    "⚡ {name} теперь с нами!",
    "🌟 Встречаем {name}",
    "💎 {name} в чате!",
    "🚀 {name} врывается в чат!",
    "😎 {name} присоединился к тусовке!",
    "👀 Все смотрят на {name}!",
    "🎊 {name} только что заспавнился!",
    "🫡 {name} на связи, салют!",
    "💥 {name} — бум, и он уже здесь!",
    "🗿 {name} пришёл молча и серьёзно",
    "🍿 {name} зашёл посмотреть на этот цирк",
    "📡 {name} поймал сигнал и подключился",
    "🐸 {name} запрыгнул в чат как лягушка",
    "🤡 {name} пришёл потроллить (шутка, или нет?)",
    "💀 {name} воскрес ради этого чата",
    "🥰 {name} такой милый, добро пожаловать~",
    "🫂 Обнимашки для {name} при входе!",
    "🌸 {name} принёс с собой хорошее настроение!",
    "☀️ {name} осветил чат своим появлением",
    "❤️ {name} — наш новый любимчик!",
    "🔥 {name} зажёг чат своим приходом!",
    "🏆 {name} — новый король/королева чата!",
    "⚔️ {name} вступил в битву (за внимание)",
    "🦁 {name} рычит: «Я здесь!»",
    "🚨 Внимание! {name} в здании!",
    "Yo, {name}!",
    "{name} online 🔥",
    "{name} has joined the party 🎈",
    "Привет, {name} 👀",
    "О, {name} зашёл, держите пиво 🍺",

]

bye_list = [
    "😢 {name} ушел...",
    "👋 {name} покинул чат",
    "🚪 {name} вышел",
    "💨 {name} исчез",
    "🥺 {name} нас покинул... возвращайся скорее",
    "💔 {name} ушёл, чат опустел",
    "😭 {name} сказал пока... грустно",
    "🕯️ {name} ушёл в закат",
    "🌧️ {name} ушёл под дождём",
    "💀 {name} сдох (в чате)",
    "🏃‍♂️ {name} побежал от проблем",
    "🗿 {name} ушёл как босс",
    "🍿 {name} вышел посмотреть сериал",
    "🚪💨 {name} слился по-английски",
    "😶‍🌫️ {name} растворился в тумане",
    "🪦 {name} RIP в чате",
    "🤡 {name} ушёл за хлебом (и не вернётся)",
    "⚰️ {name} покинул этот бренный мир (чат)",
    "🌌 {name} ушёл в другую галактику",
    "🔥 {name} сгорел и вышел",
    "🌀 {name} исчез в портале",
    "🪓 {name} был изгнан (шутка, сам ушёл)",
    "👋 Пока, {name}! Ждём обратно",
    "✌️ {name} отвалился",
    "🫡 {name} ушёл по службе",
    "📴 {name} оффнулся",
    "🚶‍♂️ {name} пошёл дальше",
    "😴 {name} пошёл спать",
    "🍔 {name} ушёл жрать",
    "🎮 {name} побежал в катку",
    "🥺 {name} уходишь? Будем скучать~",
    "🫂 Обнимаем на дорожку, {name}",
    "❤️ {name}, возвращайся скорее!",
    "🌙 Спокойной ночи, {name}",
]

# ---------------- ФАКТЫ ARKNIGHTS: ENDFIELD (все на русском, много новых) ----------------
endfield_facts = [
    "Arknights: Endfield происходит на луне Talos-II газового гиганта.",
    "Главный герой — Эндминистратор, пропавший 10 лет назад.",
    "В игре есть полноценная механика строительства фабрик, похожая на Factorio.",
    "Можно погладить Burdenbeast раз в день — получишь Burdo-muck.",
    "Некоторые операторы реагируют, если слишком долго смотреть на их хвост.",
    "Обезвоженный слизняк благодарит за воду и дарит подарок.",
    "Yvon делает бомбы Tweety в честь своего агрессивного питомца.",
    "Есть башенный режим, как в оригинальном Arknights.",
    "Laevatain — один из первых 6-звёздочных персонажей типа Striker.",
    "Endfield Industries — главная фракция в сюжете.",
    "Talos-II колонизировали терране 152 года назад через Этергейт.",
    "Аггелой — враждебные 'истинные ангелы' с Talos-II.",
    "Байт — альтернативное измерение, которое распространяется как чума.",
    "Ориджинум на Talos-II стабилизирует орипатію, и её можно вылечить.",
    "Перлика — помощница Эндминистратора, похожа на Амию из оригинала.",
    "Варфарин руководит филиалом Rhodes Island на Talos-II.",
    "У некоторых операторов есть уникальные анимации двойного рывка.",
    "Ксиранит — новый материал, который противостоит Байту.",
    "Чэнь Цяньюй — отдельный персонаж, не та Чэнь из Arknights.",
    "Игра вышла 22 января 2026 года по всему миру.",
    "Гилберта управляет гравитацией с помощью искусств Ориджинума.",
    "Авроральный Барьер разделяет север и юг Talos-II.",
    "Ландбрейкеры — варвары, большая угроза для колонистов.",
    "Дидзян — корабль Endfield Industries с возможностью кастомизации.",
    "Музыка Endfield выходит под лейблом Metal Scar Radio.",
    "Эндминистратор может быть мужчиной или женщиной — на выбор.",
    "Этерсайд — измерение, связанное с Коллапсалами из оригинального Arknights.",
    "Пограничник, Лифэн и Гилберта — обладатели уникальных дашей.",
    "Симуляции можно мгновенно завершить и получить полную награду.",
    "Сокровища и секреты спрятаны повсюду — как охота за сундуками в AK.",
    "Тата — Tranquil Automatic Cart, прототип от Yvon.",
    "Северные Врата и Rhodes Island упоминаются в лоре.",
    "Экономика в игре динамическая — цены меняются по регионам.",
    "Есть система исследования руин древней цивилизации.",
    "Некоторые персонажи имеют скрытые концовки в личных историях.",
    "Байт может заражать технику и превращать её в монстров.",
    "Эндфилд — это 'последний оплот' терран, а не просто колония.",
    "В игре есть секретный босс — 'Коллапсальный Страж'.",
    "Операторы Rhodes Island иногда вспоминают события оригинальной игры.",
    "Система крафта позволяет создавать оружие и броню из Ксиранита.",
    "Есть ежедневные задания на добычу Burdo-muck.",
    "В игре можно строить целые города и защищать их от Байта.",
    "Некоторые руины содержат записи о Коллапсе с Земли.",
    "Персонажи могут иметь уникальные взаимодействия с окружающей средой.",
    "Есть режим 'Выживание' с ограниченными ресурсами.",
    "Эндминистратор может выбирать путь: исследователь или воин."
]

# ---------------- HELPERS ----------------
def is_admin(message: types.Message):
    return message.from_user and message.from_user.id in [OWNER_ID]

async def is_bot_or_group_admin(message: types.Message) -> bool:
    # OWNER всегда может
    if is_admin(message):
        return True
    
    # Админы группы тоже могут
    if message.chat.type in ["group", "supergroup"]:
        try:
            admins = await bot.get_chat_administrators(message.chat.id)
            admin_ids = [admin.user.id for admin in admins]
            if message.from_user.id in admin_ids:
                return True
        except Exception as e:
            print(f"Ошибка проверки админов группы: {e}")
    
    return False

def parse_time(time_str):
    match = re.match(r"(\d+)([smhd])", time_str)
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    return {
        "s": timedelta(seconds=val),
        "m": timedelta(minutes=val),
        "h": timedelta(hours=val),
        "d": timedelta(days=val)
    }.get(unit)

def load_data():
    global warnings_db, reputation_db, message_stats, stats_changed
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                warnings_db, reputation_db, message_stats = {}, {}, {}
                stats_changed = False
                return

            data = json.loads(content)

            warnings_db = {int(k): v for k, v in data.get("warnings", {}).items()}
            reputation_db = {int(k): v for k, v in data.get("reputation", {}).items()}


            raw = data.get("messages", {})
            message_stats = {}
            for chat_str, users in raw.items():
                try:
                    chat_id = int(chat_str)
                    message_stats[chat_id] = {}
                    for uid_str, days in users.items():
                        message_stats[chat_id][int(uid_str)] = days
                except:
                    continue

            stats_changed = False

    except FileNotFoundError:
        warnings_db, reputation_db, message_stats = {}, {}, {}
        stats_changed = False

def save_data():
    global stats_changed
    if not stats_changed:
        return  # ничего не изменилось — не пишем файл

    serial_stats = {}
    for chat_id, users in message_stats.items():
        chat_str = str(chat_id)
        serial_stats[chat_str] = {}
        for uid, days in users.items():
            serial_stats[chat_str][str(uid)] = days

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "warnings": warnings_db,
            "reputation": reputation_db,
            "messages": serial_stats
        }, f, ensure_ascii=False, indent=2)

    stats_changed = False  # сброс флага

def get_display_name(user: types.User) -> str:
    if user.username:
        return f"@{user.username} ({user.first_name})"
    return user.first_name

# ---------------- ФОНОВАЯ СОХРАНКА СТАТИСТИКИ ----------------
async def auto_save_stats():
    global stats_changed
    while True:
        await asyncio.sleep(30)  # каждые 30 секунд
        if stats_changed:
            save_data()

# ---------------- MODERATION ----------------
@dp.message(Command(commands=["mute"]))
@dp.message(Command(commands=["unmute"]))
@dp.message(Command(commands=["warn"]))
@dp.message(Command(commands=["ban"]))
@dp.message(Command(commands=["permaban"]))
async def moderation(message: types.Message):

    if not await is_bot_or_group_admin(message) or not message.reply_to_message:
        return await message.answer("Ответь на сообщение пользователя или будь админом группы.")

    user_id = message.reply_to_message.from_user.id
    cmd = message.text.split()[0].replace("/", "")


    if cmd == "mute":
        args = message.text.split()
        if len(args) < 2:
            return await message.answer("Пример: /mute 10m")

        delta = parse_time(args[1])

        if not delta:
            return await message.answer("Формат: 10s / 10m / 1h / 2d")

        await bot.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(can_send_messages=False),
            until_date=datetime.now() + delta
        )

        await message.answer(f"🔇 Мут на {args[1]}")

    elif cmd == "unmute":

        await bot.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(can_send_messages=True)
        )

        await message.answer("✅ Мут снят")

    elif cmd == "warn":

        warnings_db[user_id] = warnings_db.get(user_id, 0) + 1
        count = warnings_db[user_id]

        await message.answer(f"⚠ Варн. Всего: {count}")

        if count >= 3:

            await bot.restrict_chat_member(
                message.chat.id,
                user_id,
                ChatPermissions(can_send_messages=False),
                until_date=datetime.now() + timedelta(minutes=30)
            )

            warnings_db[user_id] = 0

            await message.answer("🚫 3 варна → мут 30 минут")

        save_data()

    elif cmd == "ban":

        args = message.text.split()

        if len(args) < 2:
            return await message.answer("Пример: /ban 1d")

        delta = parse_time(args[1])

        if not delta:
            return await message.answer("Формат: 10m / 3h / 2d")

        await bot.ban_chat_member(
            message.chat.id,
            user_id,
            until_date=datetime.now() + delta
        )

        await message.answer(f"🚫 Бан на {args[1]}")

    elif cmd == "permaban":

        await bot.ban_chat_member(message.chat.id, user_id)

        await message.answer("⛔ Перманентный бан")





# ---------------- KICK RANGE ----------------
@dp.message(Command("kickrange"))
async def kickrange(message: types.Message):

    if not await is_bot_or_group_admin(message):
        return

    members = await bot.get_chat_administrators(message.chat.id)

    admins = [m.user.id for m in members]

    kicked = 0

    async for member in bot.get_chat_members(message.chat.id):

        if member.user.id not in admins and not member.user.is_bot:

            try:
                await bot.ban_chat_member(message.chat.id, member.user.id)
                await bot.unban_chat_member(message.chat.id, member.user.id)
                kicked += 1
            except:
                pass

    await message.answer(f"⚡ Кикнуто пользователей: {kicked}")


# ---------------- RULES / HELP ----------------
@dp.message(Command("rules"))
async def rules_cmd(message: types.Message):
    await message.answer(rules_text)


@dp.message(Command("help"))
async def help_cmd(message: types.Message):

    await message.answer(
        "📜 Команды бота\n\n"

        "Основное:\n"
        "/rules — правила\n"
        "/rep — твоя репутация\n"
        "/userinfo — информация о пользователе\n"
        "/fakt_endfield — случайный факт Arknights: Endfield\n\n"

        "Топы:\n"
        "/toprep — топ репутации\n"
        "/toplist — топ активности\n"
        "/toplist day\n"
        "/toplist week\n"
        "/toplist month\n"
        "/toplist year\n\n"

        "Интерактив:\n"
        "обнять\n"
        "пожать\n"
        "поцеловать\n"
        "рука\n"
        "ударить\n"
        "накричать\n\n"

        "Модерация:\n"
        "/mute\n"
        "/unmute\n"
        "/warn\n"
        "/ban\n"
        "/permaban\n"
        "/kickrange"
    )


# ---------------- REP ----------------
@dp.message(Command("rep"))
async def rep(message: types.Message):

    user_id = message.from_user.id
    now = datetime.now()

    if user_id in rep_cooldown:
        if now - rep_cooldown[user_id] < timedelta(seconds=10):
            return await message.answer("⏳ КД 10 секунд.")

    rep_cooldown[user_id] = now

    rep = reputation_db.get(user_id, 0)

    await message.answer(
        f"⭐ Репутация {get_display_name(message.from_user)}: {rep}"
    )


# ---------------- USER INFO ----------------
@dp.message(Command("userinfo"))
async def userinfo(message: types.Message):

    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = message.from_user

    uid = user.id
    chat_id = message.chat.id

    rep = reputation_db.get(uid, 0)
    warns = warnings_db.get(uid, 0)

    messages = 0

    if chat_id in message_stats and uid in message_stats[chat_id]:
        messages = sum(message_stats[chat_id][uid].values())

    text = (
        f"👤 {get_display_name(user)}\n"
        f"🆔 ID: {uid}\n\n"
        f"⭐ Репутация: {rep}\n"
        f"⚠ Варны: {warns}\n"
        f"💬 Сообщений в этом чате: {messages}"
    )

    await message.answer(text)


# ---------------- TOP REP ----------------
@dp.message(Command("toprep"))
async def toprep(message: types.Message):

    chat_id = message.chat.id

    if not reputation_db:
        return await message.answer("Нет данных.")

    active_users = []
    if chat_id in message_stats:
        active_users = [uid for uid in reputation_db if uid in message_stats[chat_id]]

    if not active_users:
        return await message.answer("Нет активных пользователей с репутацией в этом чате.")

    top = sorted(
        [(uid, reputation_db[uid]) for uid in active_users],
        key=lambda x: x[1],
        reverse=True
    )[:10]

    text = "🏆 Топ репутации (только этот чат)\n\n"

    for i, (uid, rep) in enumerate(top, 1):

        try:
            member = await bot.get_chat_member(chat_id, uid)
            name = get_display_name(member.user)
        except:
            name = f"ID {uid}"

        text += f"{i}. {name} — {rep}\n"

    await message.answer(text)


# ---------------- TOP LIST ----------------
@dp.message(Command("toplist"))
async def toplist(message: types.Message):

    chat_id = message.chat.id
    args = message.text.split()
    period = "all"

    if len(args) > 1:
        period = args[1]

    now = datetime.now()

    if chat_id not in message_stats:
        return await message.answer("В этом чате ещё нет статистики.")

    stats = {}

    for uid, days in message_stats[chat_id].items():

        total = 0

        for day, count in days.items():

            day_dt = datetime.strptime(day, "%Y-%m-%d")

            if period == "day":
                if day_dt.date() == now.date():
                    total += count

            elif period == "week":
                if (now - day_dt).days <= 7:
                    total += count

            elif period == "month":
                if (now - day_dt).days <= 30:
                    total += count

            elif period == "year":
                if (now - day_dt).days <= 365:
                    total += count

            else:
                total += count

        if total > 0:
            stats[uid] = total

    if not stats:
        return await message.answer("Нет данных за этот период в этом чате.")

    top = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]

    text = f"🏆 Топ активности ({period}) — только этот чат\n\n"

    for i, (uid, msgs) in enumerate(top, 1):

        try:
            member = await bot.get_chat_member(chat_id, uid)
            name = get_display_name(member.user)
        except:
            name = f"ID {uid}"

        text += f"{i}. {name} — {msgs}\n"

    await message.answer(text)


# ---------------- ФАКТ ENDFIELD ----------------
@dp.message(Command("fakt_endfield"))
async def fakt_endfield(message: types.Message):
    fact = random.choice(endfield_facts)
    await message.answer(f"🎲 Факт по Arknights: Endfield:\n\n{fact}")





# ---------------- UNIVERSAL HANDLER ----------------
@dp.message()
async def universal(message: types.Message):

    global stats_changed

    if not message.from_user or not message.chat:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text or ""

    # --- MESSAGE TRACKER ---
    today = datetime.now().strftime("%Y-%m-%d")

    if chat_id not in message_stats:
        message_stats[chat_id] = {}

    if user_id not in message_stats[chat_id]:
        message_stats[chat_id][user_id] = {}

    if today not in message_stats[chat_id][user_id]:
        message_stats[chat_id][user_id][today] = 0

    message_stats[chat_id][user_id][today] += 1
    stats_changed = True  # флаг — данные изменились, надо сохранить

    # --- ANTI-SPAM ---
    if user_id != OWNER_ID:

        now = time.time()

        message_tracker[user_id] = [
            t for t in message_tracker.get(user_id, [])
            if now - t < SPAM_TIME
        ]

        message_tracker[user_id].append(now)

        if len(message_tracker[user_id]) >= SPAM_LIMIT:

            await bot.restrict_chat_member(
                message.chat.id,
                user_id,
                ChatPermissions(can_send_messages=False),
                until_date=datetime.now() + timedelta(minutes=5)
            )

            message_tracker[user_id].clear()

            return await message.answer("🚫 Спам → мут 5 минут")

    # --- REP CHANGE ---
    if message.reply_to_message:

        target_id = message.reply_to_message.from_user.id

        if target_id != user_id:

            if text == "+":
                reputation_db[target_id] = reputation_db.get(target_id, 0) + 1
                await message.answer(
                    f"👍 +1 реп {message.reply_to_message.from_user.first_name}"
                )

            elif text == "-":
                reputation_db[target_id] = reputation_db.get(target_id, 0) - 1
                await message.answer(
                    f"👎 -1 реп {message.reply_to_message.from_user.first_name}"
                )

            elif re.match(r"^[+-]\d+$", text) and await is_bot_or_group_admin(message):

                val = int(text)

                reputation_db[target_id] = reputation_db.get(target_id, 0) + val

                await message.answer(
                    f"⭐ Репутация {message.reply_to_message.from_user.first_name} изменена на {val}"
                )

            save_data()

            # --- INTERACTIVE ---
            if text.lower() in actions and any(word in text.lower() for word in ultra_toxic):
                if not ULTRA_TOXIC_MODE:
                   return await message.answer("Это слишком жёстко. Включи /toxicon если админ разрешит.")
            if text.lower() in actions:

                await message.answer(
                    f"{message.from_user.first_name} {actions[text.lower()]} {message.reply_to_message.from_user.first_name}"
                )

    # --- WELCOME / BYE ---
    if message.new_chat_members:

        for u in message.new_chat_members:
            await message.answer(
                f"{random.choice(welcome_list).format(name=u.first_name)}{rules_text}"
            )

    if message.left_chat_member:

        u = message.left_chat_member

        await message.answer(
            f"{random.choice(bye_list).format(name=u.first_name)}"
        )


# ---------------- START ----------------
async def main():

    load_data()

    # Запускаем фоновую задачу сохранения статистики каждые 30 сек
    asyncio.create_task(auto_save_stats())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


bot.delete_webhook(drop_pending_updates=True)
dp.run_polling(bot)