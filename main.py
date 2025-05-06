from app import app

# This makes 'flask run' and 'gunicorn' commands work
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)