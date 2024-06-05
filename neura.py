import logging
from telegram import Update, ParseMode, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import pyshorteners
from urllib.parse import urlparse
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
VERSION = '2.0.8'
CREATOR = '@Suprafreak'

BANNER = '''<b>Welcome to Neura: Mask The Phish</b> 🎉

<b>Version:</b> {version}
<b>Creator:</b> {creator}


https://mallucampaign.in/images/img_1717572103.jpg
'''.format(version=VERSION, creator=CREATOR)

# URL Shorteners initialization
s = pyshorteners.Shortener()
shorteners = [
    s.tinyurl,
    s.dagd,
    s.clckru,
    s.osdb,
]

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    context.user_data.clear()  # clear any stored data
    
    # Send the image
    # update.message.reply_photo(photo=IMAGE_URL)
    
    # Send the banner text
    update.message.reply_html(
        BANNER,
        reply_markup=None
    )
    update.message.reply_text(
        f"Hi {user.mention_html()}! 👋\n"
        "Please enter the original link:",
        parse_mode=ParseMode.HTML
    )
    return 'URL'

def validate_web_url(url):
    url_pattern = re.compile(
        r'^(https?://)'  # starts with 'https://'
        r'([a-zA-Z0-9-]+\.)*'  # optional subdomains
        r'([a-zA-Z]{2,})'  # domain
        r'(:\d{1,5})?'  # optional port
        r'(/.*)?$')

    if not url_pattern.match(url):
        return False
    return True

def validate_custom_domain(domain):
    domain_pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not domain_pattern.match(domain):
        return False
    return True

def format_phish_keywords(keywords):
    max_length = 15
    if " " in keywords:
        return False
    if len(keywords) > max_length:
        return False
    return "-".join(keywords.split())

def handle_url(update: Update, context: CallbackContext) -> None:
    web_url = update.message.text.strip()
    if validate_web_url(web_url):
        context.user_data['web_url'] = web_url
        update.message.reply_text(
            "Please enter your custom domain (ex: gmail.com):"
        )
        return 'DOMAIN'
    else:
        update.message.reply_text(
            "Invalid URL format. Please enter a valid web URL (ex: https://www.ngrok.com):"
        )
        return 'URL'

def handle_domain(update: Update, context: CallbackContext) -> None:
    custom_domain = update.message.text.strip()
    if validate_custom_domain(custom_domain):
        context.user_data['custom_domain'] = custom_domain
        update.message.reply_text(
            "Please enter phishing keywords (ex: free-stuff, login):"
        )
        return 'PHISH'
    else:
        update.message.reply_text(
            "Invalid custom domain. Please enter a valid domain name (ex: gmail.com):"
        )
        return 'DOMAIN'

def handle_phish(update: Update, context: CallbackContext) -> None:
    phish = update.message.text.strip()
    formatted_phish = format_phish_keywords(phish)
    if formatted_phish:
        context.user_data['phish'] = formatted_phish
        web_url = context.user_data['web_url']
        custom_domain = context.user_data['custom_domain']
        phish = context.user_data['phish']
        # Shorten the original URL with multiple URL shorteners
        short_urls = []
        for shortener in shorteners:
            try:
                short_url = shortener.short(web_url)
                short_urls.append(short_url)
            except pyshorteners.exceptions.ShorteningErrorException as e:
                short_urls.append(f"Error: {str(e)}")
                continue
            except Exception as e:
                short_urls.append(f"Unexpected error: {str(e)}")
                continue

        def mask_url(domain, keyword, url):
            parsed_url = urlparse(url)
            return f"{parsed_url.scheme}://{domain}-{keyword}@{parsed_url.netloc}{parsed_url.path}"

        response = f"<b>Original URL:</b> {web_url}\n\n"
        response += f"<b>Masked URL (using multiple shorteners):</b>\n"
        for i, short_url in enumerate(short_urls):
            masked_url = mask_url(custom_domain, formatted_phish, short_url)
            response += f"Shortener {i + 1}: {masked_url}\n"
        
        response += f"\nDeveloped by {CREATOR} 🚀"

        update.message.reply_html(response)
        return 'END'
    else:
        update.message.reply_text(
            "Invalid phishing keywords. Please enter valid keywords without spaces (use '-' to separate them):"
        )
        return 'PHISH'

def main() -> None:
    updater = Updater("6386798657:AAF4tCpPCU4c5r4u2sxtyOxS0MBXfUu_nkA")

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'URL': [MessageHandler(Filters.text & ~Filters.command, handle_url)],
            'DOMAIN': [MessageHandler(Filters.text & ~Filters.command, handle_domain)],
            'PHISH': [MessageHandler(Filters.text & ~Filters.command, handle_phish)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
