from flask import Flask
from flask_jwt_extended import JWTManager

from app.utils.database import db
from .models.revoked_tokens import RevokedToken

from .models.user import User
from .routes.api.metasploit import metasploit
from .routes.api.nmap import nmap
from .routes.api.zap import zap
from .utils.connection_pool import ConnectionPool

from .utils.mail import mail

from .routes.api.auth import auth
from .routes.api.missions import missions
from .routes.api.users import users
from .routes.api.pocs import pocs




app = Flask(__name__, template_folder='templates')

# Load config based on environment
if app.config['ENV'] == "production":
    app.config.from_object("config.ProductionConfig")
elif app.config['ENV'] == "testing":
    app.config.from_object("config.TestingConfig")
elif app.config['ENV'] == "development":
    app.config.from_object("config.DevelopmentConfig")
else:
    app.config.from_object("config.Config")

# Initializations
db.init_app(app)
mail.init_app(app)
jwt = JWTManager(app)




# Registering blueprints
app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(users, url_prefix='/api/users')
app.register_blueprint(missions, url_prefix='/api/missions')
app.register_blueprint(pocs, url_prefix='/api/pocs')
#Tools routes
app.register_blueprint(nmap, url_prefix='/api/nmap')
app.register_blueprint(metasploit, url_prefix='/api/metasploit')
app.register_blueprint(zap, url_prefix='/api/zap')




###### Middleware #######
'''
@app.before_request
@jwt_required(optional=True)  # Use optional=True to allow non-authenticated routes
def check_revoked_token():
    """
    This middleware function will run befor execution any endpoint route to make sure the token is not revoked before
    :return: None if token not revoked ELSE 401 if token revoked or 500 error
    """
    try:
        jwt_data = get_jwt()
        jti = jwt_data["jti"]
        if RevokedToken.is_token_revoked(jti):
            return jsonify({"message": "Token revoked"}), 401
        return None  # Continue with the request
    except Exception as e:
        return jsonify({"message": "An error occurred"}), 500

'''