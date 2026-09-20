from highrise import BaseBot, User, Position
from highrise.__main__ import BotDefinition
from asyncio import sleep, create_task, CancelledError
import asyncio
import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==================== وب‌سرور زنده‌نگهدارنده ====================
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is Alive!")
    def log_message(self, format, *args):
        return

def run_web_server():
    try:
        port = int(os.getenv("PORT", 8080))
        server = HTTPServer(('0.0.0.0', port), PingHandler)
        print(f"✅ وب‌سرور روی پورت {port} فعال شد.")
        server.serve_forever()
    except Exception as e:
        print(f"خطا در وب‌سرور: {e}")

# ==================== ربات ====================
class MyBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.active_users = {}
        self.user_id = None
        self.dance_tasks = {}
        self.user_dances = {}
        self.bot_dance_task = None
        self.announcement_task = None
        self.save_position_task = None
        self.admin_usernames = ["max._.eror"]
        self.truth_game_active = False
        # 📍 موقعیت دقیق
        self.default_position = Position(x=16.507070541382, y=0.0, z=4.492928981781)
        self.emotes = {
            "1": "idle_zombie",
            "2": "idle_layingdown2",
            "3": "idle_layingdown",
            "4": "idle-sleep",
            "5": "idle-sad",
            "6": "idle-posh",
            "7": "idle-loop-tired",
            "8": "idle-loop-tapdance",
            "9": "idle-loop-sitfloor",
            "10": "idle-loop-shy",
            "11": "idle-loop-sad",
            "12": "idle-loop-happy",
            "13": "idle-loop-annoyed",
            "14": "idle-loop-aerobics",
            "15": "idle-lookup",
            "16": "idle-hero",
            "17": "idle-floorsleeping",
            "18": "idle-enthusiastic",
            "19": "idle-dance-swinging",
            "20": "idle-dance-headbobbing",
            "21": "emote-threadexchange-star",
            "22": "emote-ghost-idle",
        }
        self.bot_dance = self.emotes["21"]

    def is_admin(self, username: str) -> bool:
        return username.lower() in [a.lower() for a in self.admin_usernames]

    def save_position(self, position):
        pass

    async def on_start(self, session_metadata):
        print("✅ ربات وصل شد!")
        self.user_id = session_metadata.user_id
        try:
            await self.highrise.teleport(user_id=self.user_id, dest=self.default_position)
            print(f"📍 ربات به موقعیت رفت.")
        except Exception as e:
            print(f"خطا در تلپورت اولیه: {e}")
        await self.start_bot_dance(self.bot_dance)
        self.start_announcement()
        self.start_position_saver()

    def start_position_saver(self):
        if self.save_position_task:
            self.save_position_task.cancel()
        self.save_position_task = create_task(self.position_saver_loop())

    async def position_saver_loop(self):
        try:
            while True:
                await sleep(30.0)
                if not self.user_id:
                    continue
                try:
                    room_users = await self.highrise.get_room_users()
                    for u, pos in room_users.content:
                        if u.id == self.user_id:
                            self.default_position = pos
                            break
                except Exception as e:
                    print(f"خطا در ذخیره موقعیت: {e}")
        except CancelledError:
            pass
        except Exception as e:
            print(f"خطا در حلقه ذخیره موقعیت: {e}")

    def start_announcement(self):
        if self.announcement_task:
            self.announcement_task.cancel()
        self.announcement_task = create_task(self.announcement_loop())

    def stop_announcement(self):
        if self.announcement_task:
            self.announcement_task.cancel()
            self.announcement_task = None

    async def announcement_loop(self):
        try:
            while True:
                await sleep(60.0)  # ⏱️ ۶۰ ثانیه (به جای ۱۰)
                await self.highrise.chat(
                    "🤖 این ربات توسط @MAX._.EROR ساخته شده و فعلا در نسخه‌ی بتا هست.\n"
                    "🕺 برای زدن دنس، عدد ۱ تا ۲۲ را وارد کنید!"
                )
        except CancelledError:
            pass
        except Exception as e:
            print(f"خطا در حلقه تبلیغات: {e}")

    async def start_bot_dance(self, emote: str):
        if self.bot_dance_task:
            self.bot_dance_task.cancel()
            self.bot_dance_task = None
        self.bot_dance = emote
        async def bot_dance_loop():
            try:
                while True:
                    try:
                        await self.highrise.send_emote(emote, self.user_id)
                    except Exception as e:
                        print(f"خطا در دنس ربات: {e}")
                    await sleep(25.0)  # ⏱️ ۲۵ ثانیه (به جای ۱۰)
            except CancelledError:
                pass
            except Exception as e:
                print(f"خطا در دنس ربات: {e}")
        self.bot_dance_task = create_task(bot_dance_loop())

    async def start_dance(self, user: User, emote: str):
        username = user.username.lower()
        if username in self.dance_tasks:
            self.dance_tasks[username].cancel()
            self.dance_tasks.pop(username, None)
        self.user_dances[username] = emote
        async def dance_loop():
            try:
                while True:
                    try:
                        await self.highrise.send_emote(emote, user.id)
                    except Exception as e:
                        print(f"خطا در دنس {username}: {e}")
                        break
                    await sleep(25.0)  # ⏱️ ۲۵ ثانیه (به جای ۱۰)
            except CancelledError:
                pass
            except Exception as e:
                print(f"خطا در حلقه دنس {username}: {e}")
        task = create_task(dance_loop())
        self.dance_tasks[username] = task

    async def stop_dance(self, user: User):
        username = user.username.lower()
        if username in self.dance_tasks:
            self.dance_tasks[username].cancel()
            self.dance_tasks.pop(username, None)
            self.user_dances.pop(username, None)
            return True
        return False

    # ==================== ورود کاربر ====================
    async def on_user_join(self, user: User, position: Position):
        self.active_users[user.username.lower()] = user
        await self.highrise.chat(f"👋 خوش آمدی {user.username} عزیز! ❤️")

    async def on_user_leave(self, user: User, position: Position = None):
        username = user.username.lower()
        self.active_users.pop(username, None)

        if username in self.dance_tasks:
            self.dance_tasks[username].cancel()
            self.dance_tasks.pop(username, None)
            self.user_dances.pop(username, None)

        await self.highrise.chat(f"👋 {user.username} از روم خارج شد.")

    # ==================== پیوی (on_message) ====================
    async def on_message(self, user_id: str, text: str, message_id: str) -> None:
        print(f"📥 پیوی از {user_id}: {text}")
        msg = text.strip().lower()

        # 👕 دستور !rad
        if msg == "!rad":
            try:
                target_user = None
                for username, user in self.active_users.items():
                    if user.id == user_id:
                        target_user = user
                        break

                if target_user:
                    outfit_response = await self.highrise.get_user_outfit(target_user.id)
                    if hasattr(outfit_response, 'outfit') and outfit_response.outfit:
                        await self.highrise.set_outfit(outfit_response.outfit)
                        try:
                            await self.highrise.send_message(
                                user_id, 
                                f"👕 لباس @{target_user.username} رو پوشیدم!"
                            )
                        except:
                            pass
                        print(f"👕 لباس {target_user.username} پوشیده شد.")
                    else:
                        try:
                            await self.highrise.send_message(user_id, "❌ اطلاعات لباس پیدا نشد!")
                        except:
                            pass
                else:
                    try:
                        await self.highrise.send_message(user_id, "❌ شما توی روم نیستید!")
                    except:
                        pass
            except Exception as e:
                print(f"خطا در !rad: {e}")
                try:
                    await self.highrise.send_message(user_id, f"❌ خطا: {e}")
                except:
                    pass
            return

    # ==================== چت ====================
    async def on_chat(self, user: User, message: str):
        msg = message.strip().lower()

        if msg == "!pos":
            try:
                room_users = await self.highrise.get_room_users()
                found = False
                for u, pos in room_users.content:
                    if u.username.lower() == user.username.lower():
                        await self.highrise.chat(f"📍 موقعیت شما: x={pos.x}, y={pos.y}, z={pos.z}")
                        found = True
                        break
                if not found:
                    await self.highrise.chat("❌ موقعیت شما پیدا نشد!")
            except Exception as e:
                await self.highrise.chat(f"❌ خطا: {e}")
            return

        if msg == "!me":
            user_position = None
            try:
                room_users = await self.highrise.get_room_users()
                for u, pos in room_users.content:
                    if u.username.lower() == user.username.lower():
                        user_position = pos
                        break
            except Exception as e:
                print(f"خطا در گرفتن موقعیت: {e}")
            if user_position:
                try:
                    await self.highrise.teleport(user_id=self.user_id, dest=user_position)
                    await sleep(1.0)
                    self.default_position = user_position
                    await self.highrise.chat(f"✅ ربات اومد جای @{user.username}!")
                except Exception as e:
                    await self.highrise.chat(f"❌ خطا در تلپورت: {e}")
            else:
                await self.highrise.chat("❌ موقعیت شما پیدا نشد!")
            return

        if self.truth_game_active:
            if msg in ["بچرخ", "bchrkh", "spin", "بچرخون"]:
                await self.spin_bottle()
                return
            if msg == "!tr" and self.is_admin(user.username):
                await self.stop_truth_game(user)
                return
            if msg in self.emotes:
                await self.start_dance(user, self.emotes[msg])
                return

        if msg in self.emotes:
            await self.start_dance(user, self.emotes[msg])
            return

        if msg in ["سلام", "salam", "hi", "hello"]:
            await self.highrise.chat(
                f"👋 سلام {user.username}! من یه رباتم و نمی‌تونم حرف بزنم، "
                f"ولی می‌تونم برات برقصم! 🕺 عدد ۱ تا ۲۲ رو وارد کن."
            )
            return

        if msg in ["stop", "استوپ"]:
            if await self.stop_dance(user):
                await self.highrise.chat(f"🛑 دنس @{user.username} متوقف شد!")
            return

        if msg.startswith("!"):
            if not self.is_admin(user.username):
                await self.highrise.chat(f"❌ {user.username}، فقط ادمین‌ها!")
                return

            if msg == "!help":
                help_text = (
                    "📋 دستورات ربات:\n"
                    "1-22 - دنس‌ها\n"
                    "stop - توقف دنس\n"
                    "!me - ربات بیاد جای تو\n"
                    "!pos - نمایش موقعیت شما\n"
                    "📩 توی پیوی ربات: !rad (لباس تو رو بپوشه)\n"
                    "!help - راهنما\n"
                    "!adminlist - لیست ادمین‌ها\n"
                    "!addadmin @user - افزودن ادمین\n"
                    "!removeadmin @user - حذف ادمین\n"
                    "!tele @user - تلپورت\n"
                    "!dance @user - رقص برای کاربر\n"
                    "!tr - شروع/توقف بازی بچرخ\n"
                )
                await self.highrise.chat(help_text)
                return

            if msg == "!adminlist":
                admin_list = "\n".join([f"👑 @{a}" for a in self.admin_usernames])
                await self.highrise.chat(f"📋 لیست ادمین‌ها:\n{admin_list}")
                return

            if msg.startswith("!addadmin "):
                parts = msg.split()
                if len(parts) != 2 or not parts[1].startswith("@"):
                    await self.highrise.chat("❌ فرمت درست: !addadmin @username")
                    return
                target = parts[1][1:].lower()
                if target in [a.lower() for a in self.admin_usernames]:
                    await self.highrise.chat(f"❌ @{target} قبلاً ادمینه!")
                    return
                self.admin_usernames.append(target)
                await self.highrise.chat(f"✅ @{target} اضافه شد!")
                return

            if msg.startswith("!removeadmin "):
                parts = msg.split()
                if len(parts) != 2 or not parts[1].startswith("@"):
                    await self.highrise.chat("❌ فرمت درست: !removeadmin @username")
                    return
                target = parts[1][1:].lower()
                if target not in [a.lower() for a in self.admin_usernames]:
                    await self.highrise.chat(f"❌ @{target} توی لیست نیست!")
                    return
                if len(self.admin_usernames) <= 1:
                    await self.highrise.chat("❌ نمی‌تونی آخرین ادمین رو حذف کنی!")
                    return
                self.admin_usernames = [a for a in self.admin_usernames if a.lower() != target]
                await self.highrise.chat(f"✅ @{target} حذف شد!")
                return

            if msg.startswith("!tele "):
                parts = msg.split()
                if len(parts) != 2 or not parts[1].startswith("@"):
                    await self.highrise.chat("❌ فرمت درست: !tele @username")
                    return
                target_username = parts[1][1:].lower()
                target_user = self.active_users.get(target_username)
                if not target_user:
                    await self.highrise.chat(f"❌ کاربر @{target_username} آنلاین نیست!")
                    return
                try:
                    room_users = await self.highrise.get_room_users()
                    admin_pos = None
                    for u, pos in room_users.content:
                        if u.username.lower() == user.username.lower():
                            admin_pos = pos
                            break
                    if admin_pos:
                        await self.highrise.teleport(target_user.id, admin_pos)
                        await self.highrise.chat(f"✅ @{target_username} تلپورت شد!")
                    else:
                        await self.highrise.chat("❌ موقعیت شما پیدا نشد!")
                except Exception as e:
                    await self.highrise.chat(f"❌ خطا: {e}")
                return

            if msg.startswith("!dance "):
                parts = msg.split()
                if len(parts) != 2 or not parts[1].startswith("@"):
                    await self.highrise.chat("❌ فرمت درست: !dance @username")
                    return
                target_username = parts[1][1:].lower()
                target_user = self.active_users.get(target_username)
                if not target_user:
                    await self.highrise.chat(f"❌ کاربر @{target_username} آنلاین نیست!")
                    return
                await self.start_dance(target_user, self.emotes["21"])
                await self.highrise.chat(f"🕺 @{target_username} داره دنس ۲۱ می‌زنه!")
                return

            if msg == "!tr":
                await self.start_truth_game(user)
                return

    async def start_truth_game(self, user: User):
        self.truth_game_active = True
        self.stop_announcement()
        try:
            await self.highrise.chat(
                "🎮 **بازی بچرخ فعال شد!**\n"
                "🔄 کلمه «**بچرخ**» رو بزن!\n"
                "👑 ادمین با `!tr` بازی رو متوقف می‌کنه."
            )
        except Exception as e:
            print(f"خطا در ارسال پیام بازی: {e}")

    async def stop_truth_game(self, user: User):
        self.truth_game_active = False
        self.start_announcement()
        try:
            await self.highrise.chat(
                "🎮 بازی بچرخ **متوقف** شد!\n"
                "🔄 ربات به حالت عادی برگشت."
            )
        except Exception as e:
            print(f"خطا در ارسال پیام توقف: {e}")

    async def spin_bottle(self):
        if not self.active_users:
            await self.highrise.chat("❌ هیچ کاربری توی روم نیست!")
            return
        users = list(self.active_users.values())
        target_user = random.choice(users)
        try:
            await self.highrise.chat(
                f"🎯 چرخید و افتاد روی: **@{target_user.username}** 🎉"
            )
        except Exception as e:
            print(f"خطا در ارسال پیام بچرخ: {e}")

    async def cleanup_tasks(self):
        for task in [self.bot_dance_task, self.announcement_task, self.save_position_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except CancelledError:
                    pass

# ==================== main ====================
async def main():
    room_id = "69029526dc071760c84aa355"
    api_token = "d1b29fe834a9dc99541aba0f3905be0cdd5bb02af8d85a58aa3403505f9e99ad"

    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    max_reconnect = 10
    attempt = 0
    while attempt < max_reconnect:
        try:
            bot_instance = MyBot()
            bot_def = BotDefinition(room_id=room_id, api_token=api_token, bot=bot_instance)
            print(f"🔌 تلاش برای اتصال... روم: {room_id}")
            from highrise.__main__ import main as highrise_main
            await highrise_main([bot_def])
        except Exception as e:
            print(f"❌ خطای اتصال: {e}")
            try:
                await bot_instance.cleanup_tasks()
            except Exception:
                pass
            attempt += 1
            print(f"⏳ تلاش مجدد {attempt}/{max_reconnect}...")
            await asyncio.sleep(6)

if __name__ == "__main__":
    asyncio.run(main())
