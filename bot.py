import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - Read from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

# Pollinations API (free, no key required for basic use)
POLLINATIONS_API_KEY = os.environ.get("POLLINATIONS_API_KEY", "")
API_URL = "https://image.pollinations.ai/prompt/"

# Store user preferences (in-memory - resets on bot restart)
user_preferences = {}

# Default settings
DEFAULT_SIZE = "1024x1024"
DEFAULT_STYLE = "cinematic"

# Available options for users
SIZES = ["512x512", "768x768", "1024x1024"]
STYLES = ["cinematic", "anime", "photorealistic", "abstract", "sketch", "vintage", "3d", "watercolor"]

# ==================== Helper Functions ====================

async def generate_image(prompt: str, size: str = DEFAULT_SIZE, style: str = DEFAULT_STYLE) -> str:
    """
    Generate an image using Pollinations.ai API.
    Returns the image URL.
    """
    # Enhanced prompt with style
    enhanced_prompt = f"{prompt}, {style} style, high quality, detailed, masterpiece"
    
    # Parse dimensions
    width, height = size.split('x')
    
    # Build URL
    url = f"{API_URL}{enhanced_prompt}?width={width}&height={height}&nologo=true"
    
    # Add API key if available (for higher rate limits)
    if POLLINATIONS_API_KEY:
        url += f"&api_key={POLLINATIONS_API_KEY}"
    
    logger.info(f"Generating image for prompt: {enhanced_prompt[:50]}...")
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return url
        else:
            logger.error(f"API error: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None

# ==================== Command Handlers ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    welcome_text = (
        f"🎨 **Hello {user.first_name}!**\n\n"
        "I'm your **AI Image Prompt Generator**.\n"
        "I create stunning images from your text descriptions!\n\n"
        "✨ **How to use me:**\n"
        "• Send me any text description\n"
        "• Use /settings to customize size and style\n"
        "• Use /help to see all commands\n\n"
        "🚀 **Example prompts:**\n"
        "• 'A beautiful sunset over a mountain lake'\n"
        "• 'A futuristic cyberpunk city with neon lights'\n"
        "• 'A cute cat wearing a wizard hat'\n\n"
        "Let's create something amazing! 🎨"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎯 Try an Example", callback_data="example")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("💡 Tips", callback_data="tips")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = (
        "📖 **Help & Commands**\n\n"
        "• /start - Restart the bot\n"
        "• /help - Show this help message\n"
        "• /settings - Customize size and style\n"
        "• /examples - See example prompts\n"
        "• /reset - Reset to default settings\n\n"
        "💡 **Tips for great prompts:**\n"
        "• Be specific and descriptive\n"
        "• Include style, mood, and details\n"
        "• Use adjectives like 'majestic', 'serene'\n"
        "• Mention lighting, colors, perspective\n\n"
        "🖼️ **Just send any text description** and I'll generate an image!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show settings menu."""
    user_id = update.effective_user.id
    prefs = user_preferences.get(user_id, {})
    current_size = prefs.get("size", DEFAULT_SIZE)
    current_style = prefs.get("style", DEFAULT_STYLE)
    
    settings_text = (
        f"⚙️ **Your Current Settings**\n\n"
        f"📐 Size: `{current_size}`\n"
        f"🎨 Style: `{current_style}`\n\n"
        "Choose an option to customize:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📐 Change Size", callback_data="change_size")],
        [InlineKeyboardButton("🎨 Change Style", callback_data="change_style")],
        [InlineKeyboardButton("🔄 Reset to Default", callback_data="reset_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        settings_text, 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def examples(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show example prompts."""
    examples_text = (
        "🎯 **Example Prompts to Try**\n\n"
        "1️⃣ *Nature*: 'A serene mountain lake at sunrise with mist and pine trees, photorealistic'\n"
        "2️⃣ *Fantasy*: 'A majestic dragon flying over a medieval castle, cinematic lighting'\n"
        "3️⃣ *Sci-Fi*: 'A cyberpunk city with neon lights and flying cars, futuristic style'\n"
        "4️⃣ *Portrait*: 'A beautiful woman with flowing hair in a sunflower field, golden hour'\n"
        "5️⃣ *Abstract*: 'A colorful abstract painting with swirling patterns and vibrant colors'\n"
        "6️⃣ *Animals*: 'A cute fluffy cat sitting in a teacup, anime style'\n"
        "7️⃣ *Food*: 'A delicious chocolate cake with strawberries, food photography'\n"
        "8️⃣ *Space*: 'A spectacular nebula with stars and galaxies, cosmic style'\n\n"
        "💡 **Copy any of these** and send them to me!"
    )
    await update.message.reply_text(examples_text, parse_mode="Markdown")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset user preferences to default."""
    user_id = update.effective_user.id
    if user_id in user_preferences:
        del user_preferences[user_id]
    
    await update.message.reply_text(
        "🔄 Settings have been reset to default!\n"
        f"📐 Size: {DEFAULT_SIZE}\n"
        f"🎨 Style: {DEFAULT_STYLE}"
    )

# ==================== Callback Query Handlers ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "example":
        # Send random example
        examples_list = [
            "A beautiful sunset over a mountain lake with pine trees, cinematic style",
            "A futuristic cyberpunk city with neon lights and flying cars",
            "A majestic dragon flying over a medieval castle, fantasy art",
            "A cute fluffy cat sitting in a teacup, anime style",
            "A delicious chocolate cake with strawberries, food photography"
        ]
        import random
        example = random.choice(examples_list)
        await query.message.reply_text(
            f"🎯 **Try this example:**\n\n`{example}`\n\nSend me this prompt or modify it!",
            parse_mode="Markdown"
        )
    
    elif data == "settings":
        await settings_command(update, context)
    
    elif data == "tips":
        tips_text = (
            "💡 **Pro Tips for Better Images**\n\n"
            "1. **Be Specific**: 'A red Ferrari driving down a coastal road' > 'A car'\n"
            "2. **Use Style Words**: 'oil painting', '3D render', 'watercolor'\n"
            "3. **Add Lighting**: 'golden hour', 'neon lighting', 'studio lighting'\n"
            "4. **Describe Mood**: 'serene', 'dramatic', 'dreamy', 'mysterious'\n"
            "5. **Include Perspective**: 'wide shot', 'close-up', 'aerial view'\n"
            "6. **Mention Colors**: 'vibrant colors', 'monochrome', 'pastel tones'\n"
            "7. **Use Quality Keywords**: 'highly detailed', 'intricate', 'masterpiece'\n"
            "8. **Add Environment**: 'in a forest', 'on a beach', 'in space'\n\n"
            "🎨 **Combine these elements for amazing results!**"
        )
        await query.message.reply_text(tips_text, parse_mode="Markdown")
    
    elif data == "change_size":
        keyboard = []
        for size in SIZES:
            keyboard.append([InlineKeyboardButton(size, callback_data=f"size_{size}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="settings_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "📐 **Select Image Size:**", 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )
    
    elif data == "change_style":
        keyboard = []
        row = []
        for style in STYLES:
            row.append(InlineKeyboardButton(style.capitalize(), callback_data=f"style_{style}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="settings_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "🎨 **Select Image Style:**", 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )
    
    elif data == "reset_settings":
        if user_id in user_preferences:
            del user_preferences[user_id]
        await query.message.edit_text(
            "🔄 Settings have been reset to default!\n"
            f"📐 Size: {DEFAULT_SIZE}\n"
            f"🎨 Style: {DEFAULT_STYLE}\n\n"
            "Use /settings to customize again."
        )
    
    elif data == "settings_back":
        await settings_command(update, context)
    
    elif data.startswith("size_"):
        size = data.replace("size_", "")
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]["size"] = size
        
        await query.message.edit_text(
            f"✅ Size set to: `{size}`\n\n"
            "Use /settings to customize more options.",
            parse_mode="Markdown"
        )
    
    elif data.startswith("style_"):
        style = data.replace("style_", "")
        if user_id not in user_preferences:
            user_preferences[user_id] = {}
        user_preferences[user_id]["style"] = style
        
        await query.message.edit_text(
            f"✅ Style set to: `{style}`\n\n"
            "Use /settings to customize more options.",
            parse_mode="Markdown"
        )

# ==================== Message Handler ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages (prompts)."""
    user_id = update.effective_user.id
    prompt = update.message.text
    
    # Get user preferences
    prefs = user_preferences.get(user_id, {})
    size = prefs.get("size", DEFAULT_SIZE)
    style = prefs.get("style", DEFAULT_STYLE)
    
    # Send typing indicator
    await update.message.chat.send_action(action="typing")
    
    # Send initial message
    processing_msg = await update.message.reply_text(
        f"🎨 **Generating your image...**\n\n"
        f"📐 Size: `{size}`\n"
        f"🎨 Style: `{style}`\n\n"
        f"⏳ Please wait a few seconds...",
        parse_mode="Markdown"
    )
    
    # Generate image
    image_url = await generate_image(prompt, size, style)
    
    if image_url:
        try:
            # Send the image
            await update.message.reply_photo(
                photo=image_url,
                caption=f"🖼️ **Generated Image**\n\n"
                       f"📝 **Prompt:** `{prompt}`\n"
                       f"📐 **Size:** `{size}`\n"
                       f"🎨 **Style:** `{style}`\n\n"
                       f"💡 Modify your prompt for different results!",
                parse_mode="Markdown"
            )
            await processing_msg.delete()
        except Exception as e:
            logger.error(f"Error sending image: {e}")
            await processing_msg.edit_text(
                "❌ Sorry, I couldn't send the image. Please try again with a different prompt."
            )
    else:
        await processing_msg.edit_text(
            "❌ Sorry, I couldn't generate the image. Please try again with a different prompt."
        )

# ==================== Error Handler ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Please try again or use /help for assistance."
            )
    except:
        pass

# ==================== Main Function ====================

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("examples", examples))
    application.add_handler(CommandHandler("reset", reset))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("🤖 Bot is starting...")
    logger.info(f"Bot @{application.bot.username} is running!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
