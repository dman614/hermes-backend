from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
import os
import sys

app = FastAPI()

# Log everything to stdout so we can see it
print("✅ App starting up...", file=sys.stderr, flush=True)

@app.get("/health")
def health():
    print("✅ Health check called", file=sys.stderr, flush=True)
    return {"status": "ok"}

@app.get("/test")
def test():
    print("✅ Test endpoint called", file=sys.stderr, flush=True)
    return {"message": "Test OK"}

@app.post("/webhook/call")
async def webhook_call(request: Request):
    print("✅ POST /webhook/call called", file=sys.stderr, flush=True)
    try:
        body = await request.body()
        print(f"Request body: {body}", file=sys.stderr, flush=True)
    except:
        pass
    
    xml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Hello</Say><Hangup/></Response>'
    print(f"Returning TwiML: {xml}", file=sys.stderr, flush=True)
    return Response(content=xml, media_type="application/xml")

@app.api_route("/webhook/call", methods=["GET", "POST"])
async def webhook_call_any(request: Request):
    print(f"✅ Webhook called via {request.method}", file=sys.stderr, flush=True)
    xml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Hello from Hermes</Say><Hangup/></Response>'
    return Response(content=xml, media_type="application/xml")

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    print(f"❌ Exception: {exc}", file=sys.stderr, flush=True)
    xml = '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error occurred</Say><Hangup/></Response>'
    return Response(content=xml, media_type="application/xml", status_code=200)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting on port {port}", file=sys.stderr, flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)
