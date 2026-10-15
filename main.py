from flask import Flask, Response

app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'ok'}

@app.route('/webhook/call', methods=['POST', 'GET'])
def webhook_call():
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Say>Hello from Hermes</Say>
<Hangup/>
</Response>'''
    return Response(xml, mimetype='application/xml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
