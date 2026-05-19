from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Kunci rahasia untuk mengamankan data session Flask
    app.secret_key = 'medilife_apotek'
    
    # Daftarkan jalur URL (routes)
    from .routes.views import views
    app.register_blueprint(views, url_prefix='/')

    return app