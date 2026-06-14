import os
import uuid

from flask import current_app, session, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.i18n import t

ALLOWED_AVATAR_EXTENSIONS = {'jpg', 'jpeg', 'png', 'img'}


def current_language():
    lang = session.get('language')
    if lang in current_app.config.get('LANGUAGES', {}):
        return lang
    if current_user.is_authenticated and current_user.language in current_app.config.get('LANGUAGES', {}):
        return current_user.language
    return current_app.config.get('BABEL_DEFAULT_LOCALE', 'ru')


def avatar_validation_error():
    return t(
        'messages.invalid_avatar_format',
        current_language(),
        'Допустимы только изображения (jpg, jpeg, png, img).',
    )


def save_avatar_file(file_storage, upload_subdir='avatars'):
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return None

    filename = secure_filename(file_storage.filename) or ''
    if '.' not in filename:
        return None

    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        return None

    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_subdir)
    os.makedirs(upload_dir, exist_ok=True)

    unique_name = f'{uuid.uuid4().hex}.{ext}'
    file_storage.save(os.path.join(upload_dir, unique_name))
    return unique_name


def delete_avatar_file(filename, upload_subdir='avatars'):
    if not filename:
        return False

    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_subdir)
    file_path = os.path.join(upload_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def remove_user_avatar(user, upload_subdir='avatars'):
    if getattr(user, 'avatar', None):
        delete_avatar_file(user.avatar, upload_subdir=upload_subdir)
        user.avatar = None


def replace_user_avatar(user, file_storage, upload_subdir='avatars'):
    """Save a new avatar file and remove the previous one."""
    new_name = save_avatar_file(file_storage, upload_subdir)
    if not new_name:
        return None
    if getattr(user, 'avatar', None):
        delete_avatar_file(user.avatar, upload_subdir=upload_subdir)
    user.avatar = new_name
    return new_name


def avatar_url(user):
    """Return a cache-busted static URL for a user's avatar, or None."""
    filename = getattr(user, 'avatar', None) if user else None
    if not filename:
        return None

    static_url = url_for('static', filename=f'uploads/avatars/{filename}')
    version = getattr(user, 'updated_at', None) or getattr(user, 'created_at', None)
    if version:
        return f'{static_url}?v={int(version.timestamp())}'
    return static_url