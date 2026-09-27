from flask import Flask, render_template

from config import Config
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.technician import technician_bp
from routes.panel import panel_bp
from routes.maintenance import maintenance_bp
from routes.ai import ai_bp

app = Flask(__name__)

app.config.from_object(Config)

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(
    technician_bp,
    url_prefix="/technician"
)
app.register_blueprint(panel_bp)
app.register_blueprint(maintenance_bp)
app.register_blueprint(ai_bp)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)