import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Discord Notifier API")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

class MessagePayload(BaseModel):
    content: str
    username: str = "FastAPI Bot"  # Optional: Overrides the webhook's default name

@app.post("/api/notify")
async def send_discord_message(payload: MessagePayload):
    if not DISCORD_WEBHOOK_URL:
        raise HTTPException(status_code=500, detail="Discord webhook URL not configured.")

    # Use httpx for asynchronous requests so we don't block the FastAPI event loop
    async with httpx.AsyncClient() as client:
        response = await client.post(
            DISCORD_WEBHOOK_URL,
            json={"content": payload.content, "username": payload.username}
        )
        
        # Discord webhooks return 204 No Content on success
        if response.status_code not in (200, 204):
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Failed to send message: {response.text}"
            )

    return {"status": "success", "message": "Message dispatched to Discord"}