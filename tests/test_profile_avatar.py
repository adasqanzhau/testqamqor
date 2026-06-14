import io
import uuid
from pathlib import Path

import pytest

from app import db
from app.models import User
from tests.conftest import login


PROFILE_UPLOAD_CASES = [
    ('/admin/profile', 'admin@test.kz', 'superadmin'),
    ('/clinic/profile', 'clinicadmin@test.kz', 'clinic_admin_user'),
    ('/doctor/profile', 'doctor@test.kz', 'doctor_user'),
    ('/patient/profile', 'patient@test.kz', 'patient_user'),
]


@pytest.mark.parametrize('route,email,user_fixture', PROFILE_UPLOAD_CASES)
def test_profile_avatar_upload_commits(client, app, request, route, email, user_fixture):
    user_id = request.getfixturevalue(user_fixture)
    login(client, email)

    filename = f'{uuid.uuid4().hex}.png'
    response = client.post(
        route,
        data={
            'first_name': 'Avatar',
            'last_name': 'Tester',
            'avatar': (io.BytesIO(b'not-a-real-image-but-valid-extension'), filename),
        },
        content_type='multipart/form-data',
        follow_redirects=True,
    )

    assert response.status_code == 200
    body = response.data.decode()
    assert 'Error saving profile. Please try again.' not in body
    assert 'Ошибка при сохранении профиля. Попробуйте снова.' not in body

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.avatar
        assert user.avatar.endswith('.png')

        avatar_path = Path(app.config['UPLOAD_FOLDER']) / 'avatars' / user.avatar
        assert avatar_path.exists()
        avatar_path.unlink()