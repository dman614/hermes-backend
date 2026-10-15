from fastapi import FastAPI
from fastapi.responses import Response
import os

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhook/call")
def webhook_call():
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Say>Hello. Thank you for calling.</Say>
<Hangup/>
</Response>'''
    return Response(content=xml, media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
