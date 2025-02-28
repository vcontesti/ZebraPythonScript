from flask import Flask, request, Response
import requests
from pyngrok import ngrok
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/<path:path>', methods=['GET', 'POST'])
def proxy(path):
    # Get the target printer IP from headers or query params
    printer_ip = request.headers.get('X-Printer-IP') or request.args.get('printer_ip')
    if not printer_ip:
        return 'Printer IP not specified', 400

    # Construct the target URL
    target_url = f'http://{printer_ip}/{path}'
    logger.info(f'Proxying request to: {target_url}')

    try:
        # Forward the request to the printer
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10
        )

        # Return the printer's response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                  if name.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, headers)

    except requests.RequestException as e:
        logger.error(f'Error proxying request: {str(e)}')
        return f'Error connecting to printer: {str(e)}', 502

def start_ngrok():
    # Start ngrok tunnel
    public_url = ngrok.connect(5000)
    logger.info(f'Ngrok tunnel established at: {public_url}')
    return public_url

if __name__ == '__main__':
    # Install pyngrok if not already installed
    try:
        import pyngrok
    except ImportError:
        import subprocess
        subprocess.check_call(['pip', 'install', 'pyngrok'])
        from pyngrok import ngrok

    # Start ngrok tunnel
    public_url = start_ngrok()
    print(f'\nProxy server is running at: {public_url}')
    print('Use this URL in your render.com application')
    print('Press Ctrl+C to stop the server\n')
    
    # Run Flask app
    app.run(port=5000)
