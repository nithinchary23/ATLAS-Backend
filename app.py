import os
from flask import Flask
from flask_cors import CORS
from routes.forecast_routes import forecast_bp
from routes.geo_routes import geo_bp
from routes.risk_routes import risk_bp

# Initialize the app directly (no function wrapper)
app = Flask(__name__)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS(app, resources={
    r"/api/*": {
        "origins": [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    }
})

# Register Blueprints
app.register_blueprint(forecast_bp, url_prefix="/api")
app.register_blueprint(geo_bp, url_prefix="/api")
app.register_blueprint(risk_bp, url_prefix="/api")

# Health Check Route
@app.route("/health")
def health():
    return {"status": "ATLAS backend running"}, 200

# Run local server
if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "true").strip().lower() == "true",
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000"))
    )