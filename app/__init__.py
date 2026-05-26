from flask import Flask, redirect, url_for, render_template, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO()
csrf = CSRFProtect()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    cors_env = os.environ.get('CORS_ORIGINS', '').strip()
    allowed_origins = cors_env.split(',') if cors_env else '*'

    # Auto-detect async mode: gevent for production, threading for local dev
    async_mode = os.environ.get('SOCKETIO_ASYNC_MODE', '')
    if not async_mode:
        try:
            import gevent          # noqa: F401
            import geventwebsocket  # noqa: F401
            async_mode = 'gevent'
        except ImportError:
            async_mode = 'threading'

    # manage_session=False makes Flask-SocketIO share the Flask-Login session
    # so current_user works in SocketIO event handlers
    socketio.init_app(
        app,
        cors_allowed_origins=allowed_origins,
        async_mode=async_mode,
        manage_session=False,
    )
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему.'
    login_manager.login_message_category = 'warning'

    @login_manager.unauthorized_handler
    def unauthorized():
        from app.i18n import t
        current_lang = session.get('language', app.config.get('BABEL_DEFAULT_LOCALE', 'ru'))
        flash(t('auth.login_required', current_lang, 'Пожалуйста, войдите в систему.'), 'warning')
        return redirect(url_for('auth.login', next=request.full_path))

    # Locale selector for Babel
    def get_locale():
        # 1. Check session first so the auth-page selection survives login
        if 'language' in session:
            return session['language']
        # 2. Check if user is logged in and has language preference
        if current_user.is_authenticated and current_user.language:
            return current_user.language
        # 3. Check URL parameter
        if request.args.get('lang') in app.config.get('LANGUAGES', {}):
            return request.args.get('lang')
        # 4. Default
        return app.config.get('BABEL_DEFAULT_LOCALE', 'ru')

    babel.init_app(app, locale_selector=get_locale)

    # Ensure upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), exist_ok=True)

    from app.routes.auth import auth_bp
    from app.routes.admin import admin as admin_bp
    from app.routes.clinic import clinic as clinic_bp
    from app.routes.doctor import doctor as doctor_bp
    from app.routes.patient import patient_bp
    from app.routes.videocall import videocall_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(clinic_bp, url_prefix='/clinic')
    app.register_blueprint(doctor_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(videocall_bp, url_prefix='/videocall')
    app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            from app.routes.auth import ROLE_REDIRECTS
            return redirect(url_for(ROLE_REDIRECTS.get(current_user.role, 'auth.login')))
        return render_template('landing.html')

    @app.route('/landing')
    def landing():
        return render_template('landing.html')

    @app.route('/set-language/<language>')
    def set_language(language):
        if language in app.config.get('LANGUAGES', {}):
            session['language'] = language
            if current_user.is_authenticated:
                current_user.language = language
                db.session.commit()
        return redirect(request.referrer or url_for('landing'))

    @app.context_processor
    def inject_now():
        from datetime import datetime, timezone
        from app.i18n import t, get_translations, get_dom_translations
        
        # Determine current language
        current_lang = 'ru'
        if 'language' in session:
            current_lang = session['language']
        elif current_user.is_authenticated and current_user.language:
            current_lang = current_user.language
        
        from app.i18n import translate_text_from_ru, t as i18n_t

        def render_notification_field(notification, field):
            # Try structured multilingual payload first
            try:
                payload = getattr(notification, f"{field}_i18n", None)
            except Exception:
                payload = None
            if isinstance(payload, dict):
                # prefer exact language
                if current_lang in payload and payload[current_lang]:
                    return payload[current_lang]
                # fallback to ru/en order
                for fav in ('ru', 'en', 'kz'):
                    if fav in payload and payload[fav]:
                        return payload[fav]
            # Fallback: try to translate legacy Russian text
            try:
                orig = getattr(notification, field, '')
            except Exception:
                orig = ''
            return translate_text_from_ru(orig, current_lang)

        import json
        def localize_field(obj, field_name):
            """Return a localized variant for a potentially multilingual JSON field.

            If the field contains a JSON object mapping languages to strings, prefer
            the current language, then fall back to ru/en, else return the raw value.
            """
            try:
                raw = getattr(obj, field_name, None)
            except Exception:
                raw = None
            if not raw:
                return ''
            # If stored as JSON mapping (string), try to parse
            if isinstance(raw, str):
                s = raw.strip()
                if s.startswith('{') and s.endswith('}'):
                    try:
                        mapping = json.loads(raw)
                        if isinstance(mapping, dict):
                            for fav in (current_lang, 'ru', 'en'):
                                if fav in mapping and mapping[fav]:
                                    return mapping[fav]
                    except Exception:
                        pass
            # Fallback: return as-is
            return raw

        return {
            'now': datetime.now(timezone.utc).replace(tzinfo=None),
            'languages': app.config.get('LANGUAGES', {}),
            'current_language': current_lang,
            't': lambda key, default='': t(key, current_lang, default),
            'translations': get_translations(current_lang),
            'dom_translations': get_dom_translations(current_lang),
            # Helper to translate stored Russian notification text to current language
            'notif_t': lambda text: translate_text_from_ru(text, current_lang),
            # Helper to render notification fields (prefer multilingual payloads)
            'render_notification_field': render_notification_field,
            'localize_field': localize_field,
        }

    @app.before_request
    def sync_language_from_query():
        lang = request.args.get('lang')
        if lang in app.config.get('LANGUAGES', {}):
            session['language'] = lang
            if current_user.is_authenticated and current_user.language != lang:
                current_user.language = lang
                db.session.commit()

    return app
