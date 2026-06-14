import io
import uuid
from pathlib import Path

from app import create_app, db
from app.avatar_utils import avatar_url, replace_user_avatar
from app.models import User
from config import Config


class TestAvatarUtils:
    def test_avatar_url_includes_cache_buster(self, app, patient_user):
        with app.app_context():
            user = db.session.get(User, patient_user)
            user.avatar = 'sample.png'
            db.session.commit()
            url = avatar_url(user)
            assert 'sample.png' in url
            assert '?v=' in url

    def test_replace_user_avatar_deletes_previous_file(self, app, patient_user):
        with app.app_context():
            user = db.session.get(User, patient_user)
            upload_dir = Path(app.config['UPLOAD_FOLDER']) / 'avatars'
            upload_dir.mkdir(parents=True, exist_ok=True)

            first_name = f'{uuid.uuid4().hex}.png'
            second_name = f'{uuid.uuid4().hex}.png'
            (upload_dir / first_name).write_bytes(b'first')
            user.avatar = first_name
            db.session.commit()

            replace_user_avatar(
                user,
                type('File', (), {
                    'filename': second_name,
                    'save': lambda self, path: Path(path).write_bytes(b'second'),
                })(),
            )
            db.session.commit()

            assert user.avatar != first_name
            assert not (upload_dir / first_name).exists()
            assert (upload_dir / user.avatar).exists()
            (upload_dir / user.avatar).unlink(missing_ok=True)
