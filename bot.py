#!/usr/bin/env python3
"""
Telegram AI Bot for Vercel
Webhook-based bot with LLM integration
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import aiohttp
from telegram import Update, ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
LLM_API_URL = os.getenv("BUILT_IN_FORGE_API_URL", "https://api.manus.im")
LLM_API_KEY = os.getenv("BUILT_IN_FORGE_API_KEY", "")

# Store conversation contexts in memory
conversation_contexts: Dict[int, List[Dict]] = {}
MAX_CONTEXT_LENGTH = 10

# Global application instance
application = None


async def get_ai_response(user_message: str, user_id: int) -> str:
    """Get AI response from LLM with conversation context"""
    try:
        # Get or create context
        if user_id not in conversation_contexts:
            conversation_contexts[user_id] = []

        context = conversation_contexts[user_id]
        context.append({"role": "user", "content": user_message})

        # Keep only last MAX_CONTEXT_LENGTH messages
        if len(context) > MAX_CONTEXT_LENGTH:
            context = context[-MAX_CONTEXT_LENGTH:]
            conversation_contexts[user_id] = context

        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant for customer support. Respond in the same language as the user. Keep responses concise and helpful.",
            }
        ]
        messages.extend(context)

        # Call LLM API
        headers = {"Authorization": f"Bearer {LLM_API_KEY}"}
        payload = {"messages": messages}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{LLM_API_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ai_response = (
                            data.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                        )

                        if ai_response:
                            context.append({"role": "assistant", "content": ai_response})
                            conversation_contexts[user_id] = context
                            return ai_response

                    logger.warning(f"LLM API error: {response.status}")
            except asyncio.TimeoutError:
                logger.error("LLM API timeout")

        return "Извините, я не смог обработать ваш запрос. Попробуйте позже."

    except Exception as e:
        logger.error(f"Error in get_ai_response: {e}")
        return "Произошла ошибка. Пожалуйста, попробуйте снова."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"User {user.id} started bot")

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я AI-ассистент и готов помочь вам с любыми вопросами.\n\n"
        f"Просто напишите ваш вопрос, и я постараюсь помочь!\n\n"
        f"Команды:\n"
        f"/start - Начать\n"
        f"/help - Помощь\n"
        f"/clear - Очистить историю"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await update.message.reply_text(
        "Я могу помочь вам с:\n\n"
        "• Ответами на вопросы\n"
        "• Информацией\n"
        "• Решением проблем\n\n"
        "Просто напишите ваш вопрос!"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear command"""
    user_id = update.effective_user.id
    if user_id in conversation_contexts:
        del conversation_contexts[user_id]
    await update.message.reply_text("✅ История очищена!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages with typing effect"""
    user = update.effective_user
    message = update.message
    user_id = user.id

    logger.info(f"Message from {user_id}: {message.text}")

    try:
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=message.chat_id, action=ChatAction.TYPING
        )

        # Get AI response
        ai_response = await get_ai_response(message.text, user_id)

        # Send response with typing effect
        sent_message = await message.reply_text("🤖 Обрабатываю...")

        # Simulate typing effect by editing message
        response_text = ""
        words = ai_response.split()

        for i, word in enumerate(words):
            response_text += word + " "

            # Update every 5 words or at end
            if (i + 1) % 5 == 0 or i == len(words) - 1:
                try:
                    await sent_message.edit_text(response_text.strip())
                    await asyncio.sleep(0.05)
                except TelegramError as e:
                    logger.warning(f"Error editing message: {e}")

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте снова."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


async def init_bot():
    """Initialize bot"""
    global application

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return False

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Add error handler
    application.add_error_handler(error_handler)

    logger.info("Bot initialized successfully")
    return True


async def handle_webhook_update(data: dict) -> dict:
    """Handle webhook update from Telegram"""
    try:
        if not application:
            await init_bot()

        update = Update.de_json(data, application.bot)
        if update:
            await application.process_update(update)

        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}


def main():
    """Start bot with polling"""
    import asyncio

    async def run():
        if await init_bot():
            logger.info("Starting bot polling...")
            await application.run_polling(allowed_updates=Update.ALL_TYPES)

    asyncio.run(run())


if __name__ == "__main__":
    main()
