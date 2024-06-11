import logging
import requests
import concurrent.futures
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
from PIL import Image
from io import BytesIO

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

api_url = "https://free-ff-api.onrender.com/api/v1/account?region=ME&uid={}"
number_of_requests = 50
allowed_chats = [1211529050,-1002138953526]
from PIL import Image, ImageDraw, ImageFont
def send_images(uid, update, sticker_size=(110, 200), 
                headPic_size=(60, 60), bannerId_size=(140, 200),
                headPic_location=(0, 70), bannerId_location=(60, 3),
                id_location=(2, 100), name_location=(2, 79), level_location=(95, 112),
                default_banner_path='/storage/emulated/0/2009/1717413659443.jpg'):
    try:
        response = requests.get(api_url.format(uid))
        logger.info(f"Response Code: {response.status_code}, Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            headPic_id = data['basicInfo'].get('headPic')
            
            if 'bannerId' in data['basicInfo']:
                bannerId_id = data['basicInfo']['bannerId']
                bannerId_url = f"https://raw.githubusercontent.com/jinix6/ff-profile-webp/main/webp/{bannerId_id}.webp"
                bannerId_response = requests.get(bannerId_url)
                try:
                    bannerId_image = Image.open(BytesIO(bannerId_response.content))
                except Exception as e:
                    logger.error(f"Error loading banner image: {e}, Content: {bannerId_response.content}")
                    bannerId_image = Image.open(default_banner_path)
            else:
                bannerId_image = Image.open(default_banner_path)
            
            if headPic_id:
                headPic_url = f"https://raw.githubusercontent.com/jinix6/ff-profile-webp/main/webp/{headPic_id}.webp"
                headPic_response = requests.get(headPic_url)
                try:
                    headPic_image = Image.open(BytesIO(headPic_response.content))
                except Exception as e:
                    logger.error(f"Error loading headPic image: {e}, Content: {headPic_response.content}")
                    return  # خروج من الدالة إذا فشل تحميل صورة الرأس
                
                # Resize each image to the specified size
                headPic_image = headPic_image.resize(headPic_size, Image.LANCZOS)
                bannerId_image = bannerId_image.resize(bannerId_size, Image.LANCZOS)

                # Create a new image with a transparent background
                combined_image = Image.new('RGBA', (sticker_size[0] * 2, sticker_size[1]))
                combined_image.paste(headPic_image, headPic_location)
                combined_image.paste(bannerId_image, bannerId_location)

                # Write player info on combined image
                draw = ImageDraw.Draw(combined_image)
                font = ImageFont.truetype("arial.ttf", 15)

                # Write player ID
                player_id_text = f"ID: {data['basicInfo']['accountId']}"
                draw.text((id_location[0] + bannerId_location[0], id_location[1] + bannerId_location[1]), player_id_text, fill=(255, 255, 255), font=font)

                # Write player name
                player_name_text = f" {data['basicInfo']['nickname']}"
                draw.text((name_location[0] + bannerId_location[0], name_location[1] + bannerId_location[1]), player_name_text, fill=(255, 255, 255), font=font)

                # Write player level
                player_level_text = f"Lvl {data['basicInfo']['level']}"
                draw.text((level_location[0] + bannerId_location[0], level_location[1] + bannerId_location[1]), player_level_text, fill=(255, 255, 255), font=font)

                # Save combined image to send
                combined_image_path = f"combined_{uid}.webp"
                combined_image.save(combined_image_path)

                update.message.reply_sticker(sticker=open(combined_image_path, 'rb'))
                os.remove(combined_image_path)
            else:
                bannerId_image = bannerId_image.resize(bannerId_size, Image.LANCZOS)
                bannerId_path = f"bannerId_{uid}.webp"
                bannerId_image.save(bannerId_path)
                update.message.reply_sticker(sticker=open(bannerId_path, 'rb'))
                os.remove(bannerId_path)
        else:
            logger.error(f"Failed to retrieve data for UID {uid}: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending images: {e}", exc_info=True)

def is_allowed_chat(chat_id):
    return chat_id in allowed_chats

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('مرحب بك في بوت C4 TEAM \nاوامر :\n جلب معلومات اكتب /C4 id \nمثل:\n /C4 12345678\n لإرسال الزيارات اكتب /VU4 id')

def send_visits(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    if is_allowed_chat(chat_id):
        if context.args:
            uid = context.args[0]
            update.message.reply_text(f'جاري إرسال {number_of_requests} طلبات باستخدام UID: {uid}')
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(send_request, uid, update) for _ in range(number_of_requests)]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
            
            update.message.reply_text("تم إرسال جميع الطلبات.")
        else:
            update.message.reply_text('يرجى توفير UID بعد الأمر /VU4.')
    else:
        update.message.reply_text('هذه المجموعة غير مسموح لها باستخدام هذا الأمر.')

def get_player_info(uid):
    response = requests.get(api_url.format(uid))
    if response.status_code == 200:
        return response.json()
    else:
        return None

def player_info(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    if is_allowed_chat(chat_id):
        if context.args:
            uid = context.args[0]
            data = get_player_info(uid)
            if data:
                basic_info = data.get('basicInfo', {})
                clan_info = data.get('clanBasicInfo', {})
                captain_info = data.get('captainBasicInfo', {})
                credit_info = data.get('creditScoreInfo', {})
                pet_info = data.get('petInfo', {})
                profile_info = data.get('profileInfo', {})
                social_info = data.get('socialInfo', {})
                diamond_cost_res = data.get('diamondCostRes', {})
                equipped_ach = data.get('equippedAch', [])
                info = (
                    f"┌ 📋 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗵𝗶𝘀𝘁𝗼𝗿𝘆  [×] \n"
                    f"├─ Last Login : {basic_info.get('lastLoginAt', 'N/A')}\n"
                    f"└─ Created At : {basic_info.get('createAt', 'N/A')}\n\n"

                    f"┌ 👤 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗶𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻 \n"
                    f"├─ Account ID : {basic_info.get('accountId', 'N/A')}\n"
                    f"├─ Nickname : {basic_info.get('nickname', 'N/A')}\n"
                    f"├─ Region : {basic_info.get('region', 'N/A')}\n"
                    f"├─ Level : {basic_info.get('level', 'N/A')}\n"
                    f"├─ Experience : {basic_info.get('exp', 'N/A')}\n"
                    f"├─ Banner  : {basic_info.get('bannerId', 'N/A')}\n"
                    f"├─ avatar : {basic_info.get('headPic', 'N/A')}\n"
                    f"├─ Rank : {basic_info.get('rank', 'N/A')}\n"
                    f"├─ Ranking Points : {basic_info.get('rankingPoints', 'N/A')}\n"
                    f"├─ Badge ID : {basic_info.get('badgeId', 'N/A')}\n"
                    f"├─ Season ID : {basic_info.get('seasonId', 'N/A')}\n"
                    f"├─ Liked : {basic_info.get('liked', 'N/A')}\n"
                    f"├─ Last Login : {basic_info.get('lastLoginAt', 'N/A')}\n"
                    f"├─ CS Rank : {basic_info.get('csRank', 'N/A')}\n"
                    f"├─ Weapon Skin Shows : {basic_info.get('weaponSkinShows', 'N/A')}\n"
                    f"├─ Max Rank : {basic_info.get('maxRank', 'N/A')}\n"
                    f"├─ CS Max Rank : {basic_info.get('csMaxRank','N/A')}\n"
                    f"├─ Account Prefers : {basic_info.get('accountPrefers', 'N/A')}\n"
                    f"├─ Created At : {basic_info.get('createAt', 'N/A')}\n"
                    f"├─ External Icon Info : {basic_info.get('externalIconInfo', 'N/A')}\n"
                    f"└─ Release Version : {basic_info.get('releaseVersion', 'N/A')}\n\n"

                    f"┌ 🛡️ 𝗚𝗨𝗜𝗟𝗗 𝗜𝗡𝗙𝗢 \n"
                    f"├─ Clan ID : {clan_info.get('clanId', 'N/A')}\n"
                    f"├─ Clan Name : {clan_info.get('clanName', 'N/A')}\n"
                    f"├─ Captain ID : {clan_info.get('captainId', 'N/A')}\n"
                    f"├─ Clan Level : {clan_info.get('clanLevel', 'N/A')}\n"
                    f"├─ Capacity : {clan_info.get('capacity', 'N/A')}\n"
                    f"└─ Member Num : {clan_info.get('memberNum', 'N/A')}\n\n"

                    f"┌ ♻️ 𝗚𝗨𝗜𝗟𝗗 𝗟𝗘𝗔𝗗𝗘𝗥 𝗜𝗡𝗙𝗢 \n"
                    f"├─ Nickname : {captain_info.get('nickname', 'N/A')}\n"
                    f"├─ Level : {captain_info.get('level', 'N/A')}\n"
                    f"├─ Exp : {captain_info.get('exp', 'N/A')}\n"
                    f"├─ Rank : {captain_info.get('rank', 'N/A')}\n"
                    f"├─ Ranking Points : {captain_info.get('rankingPoints', 'N/A')}\n"
                    f"├─ Badge Count : {captain_info.get('badgeId', 'N/A')}\n"
                    f"├─ Likes : {captain_info.get('liked', 'N/A')}\n"
                    f"├─ CS Rank : {captain_info.get('csRank', 'N/A')}\n"
                    f"├─ CS Ranking Points : {captain_info.get('csRankingPoints', 'N/A')}\n"
                    f"├─ Last Login At : {captain_info.get('lastLoginAt', 'N/A')}\n"
                    f"└─ Created At : {captain_info.get('createAt','N/A')}\n\n"

                    f"┌ 🐾 𝗣𝗘𝗧 𝗜𝗡𝗙𝗢 \n"
                    f"├─ Pet ID : {pet_info.get('id', 'N/A')}\n"
                    f"├─ Pet Name : {pet_info.get('name', 'N/A')}\n"
                    f"├─ Pet Level : {pet_info.get('level', 'N/A')}\n"
                    f"├─ Pet Experience : {pet_info.get('exp', 'N/A')}\n"
                    f"└─ Selected Skill : {pet_info.get('selectedSkillId', 'N/A')}\n\n"

                    f"┌ ⚙️ 𝗖𝗥𝗘𝗗𝗜𝗧 𝗦𝗖𝗢𝗥𝗘 𝗜𝗡𝗙𝗢 \n"
                    f"├─ Credit Score : {credit_info.get('creditScore', 'N/A')}\n"
                    f"├─ Reward State : {credit_info.get('rewardState', 'N/A')}\n"
                    f"├─ Periodic Summary Likes : {credit_info.get('periodicSummaryLikeCnt', 'N/A')}\n"
                    f"├─ Periodic Summary Illegal Actions : {credit_info.get('periodicSummaryIllegalCnt', 'N/A')}\n"
                    f"└─ Periodic Summary End Time : {credit_info.get('periodicSummaryEndTime', 'N/A')}\n\n"

                    f"𝑭 𝑹 𝑬 𝑬  𝑷 𝑨 𝑳 𝑨 𝑺 𝑻 𝑰 𝑵 𝑬\n"
                    f"┌ 📜 𝗣𝗥𝗢𝗙𝗜𝗟𝗘 𝗜𝗡𝗙𝗢 \n"
                    f"├─ Avatar ID : {profile_info.get('avatarId', 'N/A')}\n"
                    f"├─ Clothes : {profile_info.get('clothes', 'N/A')}\n"
                    f"├─ Equipped Skills : {profile_info.get('equipedSkills', 'N/A')}\n"
                    f"├─ PVE Primary Weapon : {profile_info.get('pvePrimaryWeapon', 'N/A')}\n"
                    f"├─ End Time :{profile_info.get('endTime', 'N/A')}\n"
                    f"└─ Is Marked Star : {profile_info.get('isMarkedStar', 'N/A')}\n\n"

                    f"┌ 🔗 𝗦𝗢𝗖𝗜𝗔𝗟 𝗜𝗡𝗙𝗢 \n"
                    f"├─ Facebook : Yes\n"
                    f"├─ Google : no\n"
                    f"└─ VK : no\n\n"

                    f"┌ 💎 𝗗𝗜𝗔𝗠𝗢𝗡𝗗 𝗖𝗢𝗦𝗧 𝗥𝗘𝗦𝗢𝗨𝗥𝗖𝗘𝗦 \n"
                    f"└─ Diamond Cost : {diamond_cost_res.get('diamondCost', 'N/A')}\n\n"

                    f"┌ 🎖️ 𝗘𝗤𝗨𝗜𝗣𝗣𝗘𝗗 𝗔𝗖𝗛𝗜𝗘𝗩𝗘𝗠𝗘𝗡𝗧𝗦 \n"
                    f"└─ Equipped Achievements : {equipped_ach}\n\n"
                 f"┌  🚧 𝗠𝗬 𝗔𝗖𝗖𝗢𝗨𝗡𝗧𝗦 \n"
            f"├─ Telegram : \n"
            f"├─ Group : \n"
            f"├─ TikTok : \n"                f"└─" )
                
                update.message.reply_text(info)
                
                # Send avatar and banner images
                send_images(uid, update)
            else:
                update.message.reply_text("لا توجد معلومات متاحة لهذا UID.")
        else:
            update.message.reply_text('يرجى توفير UID بعد الأمر /C4.')
    else:
        update.message.reply_text('لتفعيل بوت في مجموعة خاصتك توصل مع مطور \n@rizakyi او @black_modzz')

def send_request(uid, update):
    try:
        response = requests.get(api_url.format(uid))
        logger.info(f"طلب أرسل باستخدام UID: {uid}, Response Code: {response.status_code}")
    except Exception as e:
        logger.error(f"خطأ أثناء إرسال الطلب: {e}", exc_info=True)

def main():
    updater = Updater("5163932685:AAFE1jIYnrFztPt2FteYi7-_ubKEtLm1qC0", use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("VU4", send_visits, pass_args=True))
    dispatcher.add_handler(CommandHandler("C4", player_info, pass_args=True))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
# Sent by User ID: .
