import openai
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import sys
import asyncio

# Replace these values with your actual bot token and OpenAI API key
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
OPENAI_API_KEY = 'YOUR_OPENAI_API_KEY'

# Set your OpenAI API key
openai.api_key = OPENAI_API_KEY

# Set up logging to track what is happening during execution
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# List to store recent messages
recent_messages = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Received /start command")
    await update.message.reply_text('Hello! Use /summarize <number> to summarize recent messages. (Max 500 messages)')

async def store_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        # Store the message text in the recent_messages list
        recent_messages.append(update.message.text)
        # Keep only the last 500 messages
        if len(recent_messages) > 500:
            recent_messages.pop(0)

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        n = int(context.args[0]) if context.args else 5
        if n > 500:
            await update.message.reply_text("Sorry, you can only summarize up to 500 messages.")
            return
        logger.info(f"Received /summarize command with n={n}")
    except ValueError:
        await update.message.reply_text("Please provide a valid number of messages to summarize.")
        return

    # Fetch recent messages from the cache
    messages_to_summarize = recent_messages[-n:]
    combined_text = " ".join(messages_to_summarize)
    logger.info(f"Combined text length for summarization: {len(combined_text)} characters")

    # Send the text to OpenAI for summarization
    try:
        logger.info("Sending messages to OpenAI for summarization...")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Alternatively use another available model if needed
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes messages."},
                {"role": "user", "content": f"Please summarize the following messages: {combined_text}"},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        summary = response.choices[0].message.content.strip()
        await update.message.reply_text(f"Summary: {summary}")
        logger.info("Successfully returned summary to user.")
    except Exception as e:
        error_message = f"Error summarizing messages: {e}"
        logger.error(error_message)
        await update.message.reply_text(error_message)

def main() -> None:
    logger.info("Starting the bot...")

    # Create the application using the ApplicationBuilder
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command handlers to the application
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, store_message))

    # Fix loop policy issue for Windows
    if sys.platform == 'win32' and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the bot with polling (blocking)
    logger.info("Running bot with polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
