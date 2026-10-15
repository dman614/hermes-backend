"""
Hermes - Home Services AI Platform
Twilio Integration for incoming calls
"""

from fastapi import FastAPI, Request
from fastapi.responses import Response
import os

app = FastAPI(title="Hermes Backend")

@app.get("/")
async def root():
    return {"message": "Hermes is running!"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "hermes-backend"
    }

@app.post("/webhook/call")
async def handle_call(request: Request):
    """
    Twilio webhook for incoming calls.
    Returns TwiML instructions to answer the call.
    """
    # TwiML response telling Twilio to say hello and record
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! Thank you for calling. This is Hermes, your AI assistant. Please describe what you need.</Say>
    <Record maxLength="120" action="/webhook/recording" method="POST"/>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/webhook/recording")
async def handle_recording(request: Request):
    """
    Twilio webhook for recording callback.
    """
    # Get the recording URL from Twilio
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl", "")
    caller_phone = form_data.get("From", "Unknown")
    
    print(f"✅ Received call from: {caller_phone}")
    print(f"Recording URL: {recording_url}")
    
    # Return TwiML to thank them
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you! Your request has been received. We will get back to you shortly.</Say>
    <Hangup/>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
