"""
Vercel Serverless Function for Telegram Webhook
This handles incoming Telegram updates
"""

import os
import json
import logging
import asyncio
from typing import Dict
import aiohttp

logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
LLM_API_URL = os.getenv("BUILT_IN_FORGE_API_URL", "https://api.manus.im")
LLM_API_KEY = os.getenv("BUILT_IN_FORGE_API_KEY", "")

# Store contexts
conversation_contexts: Dict[int, list] = {}
MAX_CONTEXT_LENGTH = 10


async def get_ai_response(user_message: str, user_id: int) -> str:
    """Get AI response from LLM"""
    try:
        if user_id not in conversation_contexts:
            conversation_contexts[user_id] = []

        context = conversation_contexts[user_id]
        context.append({"role": "user", "content": user_message})

        if len(context) > MAX_CONTEXT_LENGTH:
            context = context[-MAX_CONTEXT_LENGTH:]
            conversation_contexts[user_id] = context

        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Respond in the same language as the user.",
            }
        ]
        messages.extend(context)

        headers = {"Authorization": f"Bearer {LLM_API_KEY}"}
        payload = {"messages": messages}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LLM_API_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=25),
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

        return "Извините, я не смог обработать ваш запрос."

    except Exception as e:
        logger.error(f"Error: {e}")
        return "Произошла ошибка. Попробуйте позже."


async def send_telegram_message(chat_id: int, text: str) -> bool:
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False


async def edit_telegram_message(chat_id: int, message_id: int, text: str) -> bool:
    """Edit Telegram message"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": message_id, "text": text}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return False


async def handle_update(update_data: dict) -> dict:
    """Handle incoming Telegram update"""
    try:
        if "message" not in update_data:
            return {"ok": True}

        message = update_data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        user_id = message["from"]["id"]

        if text.startswith("/start"):
            await send_telegram_message(
                chat_id,
                "👋 Привет! Я AI-ассистент. Напишите ваш вопрос!",
            )
        elif text.startswith("/help"):
            await send_telegram_message(
                chat_id, "Я помогу вам с любыми вопросами. Просто напишите!"
            )
        elif text.startswith("/clear"):
            if user_id in conversation_contexts:
                del conversation_contexts[user_id]
            await send_telegram_message(chat_id, "✅ История очищена!")
        elif text:
            # Send "typing" message
            response_msg = await send_telegram_message(chat_id, "🤖 Обрабатываю...")

            # Get AI response
            ai_response = await get_ai_response(text, user_id)

            # Edit message with response
            if response_msg:
                # Parse message ID from response if needed
                # For now, just send as new message
                await send_telegram_message(chat_id, ai_response)

        return {"ok": True}

    except Exception as e:
        logger.error(f"Error handling update: {e}")
        return {"ok": False, "error": str(e)}


async def handler(request):
    """Vercel serverless handler"""
    if request.method == "POST":
        try:
            data = await request.json()
            result = await handle_update(data)
            return result
        except Exception as e:
            logger.error(f"Handler error: {e}")
            return {"ok": False, "error": str(e)}

    return {"ok": True, "message": "Telegram webhook is running"}
