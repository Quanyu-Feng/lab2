import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from src.models.user import db
from src.routes.user import user_bp
from src.routes.note import note_bp
from src.models.note import Note

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

# register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')

# Configure database - Supabase PostgreSQL
# Get Supabase credentials from environment variables
SUPABASE_DB_URL = os.getenv('SUPABASE_DB_URL')

# Setup local SQLite as fallback
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(ROOT_DIR, 'database', 'app.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
SQLITE_URI = f"sqlite:///{DB_PATH}"

if SUPABASE_DB_URL:
    try:
        # Try to use Supabase PostgreSQL database
        app.config['SQLALCHEMY_DATABASE_URI'] = SUPABASE_DB_URL
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        
        # Test the connection
        with app.app_context():
            db.create_all()
        print("✅ Successfully connected to Supabase PostgreSQL database")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")
        print("⚠️  Falling back to local SQLite database")
        print("💡 Tip: Make sure you're using the 'Connection pooling' URI from Supabase (port 6543)")
        
        # Fallback to SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLITE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        with app.app_context():
            db.create_all()
else:
    # Use local SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLITE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
    print("⚠️  Using local SQLite database (SUPABASE_DB_URL not set in .env)")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
