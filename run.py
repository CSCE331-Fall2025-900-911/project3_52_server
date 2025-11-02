# server_flask/run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True means the server will auto-reload when you save the file
    app.run(debug=True, port=5000)