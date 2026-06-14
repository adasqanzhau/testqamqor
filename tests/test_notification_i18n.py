"""Tests for multilingual notification rendering."""
import json

from app.i18n import resolve_notification_field, t, translate_text_from_ru
from app.models import Notification


class TestNotificationTranslations:
    def test_videocall_keys_exist_in_all_languages(self):
        keys = [
            'videocall.consultation_completed',
            'videocall.consultation_with_doctor',
            'videocall.consultation_with_patient',
            'videocall.transcription_ready',
            'videocall.transcription_saved_doctor',
            'videocall.transcription_saved_patient',
            'notifications.new_appointment',
            'notifications.appointment_booked',
            'notifications.new_review',
            'notifications.review_left',
        ]
        for key in keys:
            for lang in ('ru', 'en', 'kz'):
                value = t(key, lang)
                assert value, f'Missing translation for {key} in {lang}'

    def test_resolve_notification_field_uses_i18n_payload(self):
        n = Notification(
            user_id=1,
            title='Транскрипция консультации готова',
            message='Транскрипция видеоконсультации с доктором Иван Иванов сохранена.',
            title_i18n={
                'ru': 'Транскрипция консультации готова',
                'en': 'Consultation transcription ready',
                'kz': 'Консультация транскрипциясы дайын',
            },
            message_i18n={
                'ru': 'Транскрипция видеоконсультации с доктором Иван Иванов сохранена.',
                'en': 'Video consultation transcription with doctor Ivan Ivanov has been saved.',
                'kz': 'Дәрігер Иван Иванов-мен бейнеконсультация транскрипциясы сақталды.',
            },
        )
        assert resolve_notification_field(n, 'title', 'en') == 'Consultation transcription ready'
        assert 'Ivan Ivanov' in resolve_notification_field(n, 'message', 'en')

    def test_resolve_notification_field_translates_legacy_russian_payload(self):
        n = Notification(
            user_id=1,
            title='Транскрипция консультации готова',
            message='Транскрипция видеоконсультации с доктором Арман Сериков сохранена.',
            title_i18n={
                'ru': 'Транскрипция консультации готова',
                'en': 'Conversation transcription',
                'kz': 'Әңгіме транскрипциясы',
            },
            message_i18n={
                'ru': 'Транскрипция видеоконсультации с доктором Арман Сериков сохранена.',
                'en': 'Транскрипция видеоконсультации с доктором Арман Сериков сохранена.',
                'kz': 'Транскрипция видеоконсультации с доктором Арман Сериков сохранена.',
            },
        )
        en_message = resolve_notification_field(n, 'message', 'en')
        assert 'Арман Сериков' in en_message
        assert 'Video consultation transcription' in en_message

    def test_resolve_notification_field_fixes_legacy_completed_title(self):
        n = Notification(
            user_id=1,
            title='Видеоконсультация завершена',
            message='Видеоконсультация с доктором Арман Сериков',
            title_i18n={'ru': 'Видеоконсультация завершена', 'en': 'Completed', 'kz': 'Аяқталды'},
            message_i18n={
                'ru': 'Видеоконсультация с доктором Арман Сериков',
                'en': 'with doctor Арман Сериков',
                'kz': 'дәрігермен Арман Сериков',
            },
        )
        assert resolve_notification_field(n, 'title', 'en') == 'Video consultation completed'
        assert 'Арман Сериков' in resolve_notification_field(n, 'message', 'en')
        assert 'Video consultation with doctor' in resolve_notification_field(n, 'message', 'en')

    def test_translate_text_from_ru_notification_patterns(self):
        msg = 'Транскрипция видеоконсультации с доктором Арман Сериков сохранена.'
        assert 'Арман Сериков' in translate_text_from_ru(msg, 'en')
        assert 'Video consultation transcription' in translate_text_from_ru(msg, 'en')

    def test_api_notifications_localized(self, client, app, patient_user):
        with app.app_context():
            from app import db

            n = Notification(
                user_id=patient_user,
                title='Транскрипция консультации готова',
                message='Транскрипция видеоконсультации с доктором Test Doctor сохранена.',
                title_i18n={
                    'ru': 'Транскрипция консультации готова',
                    'en': 'Consultation transcription ready',
                    'kz': 'Консультация транскрипциясы дайын',
                },
                message_i18n={
                    'ru': 'Транскрипция видеоконсультации с доктором Test Doctor сохранена.',
                    'en': 'Video consultation transcription with doctor Test Doctor has been saved.',
                    'kz': 'Дәрігер Test Doctor-мен бейнеконсультация транскрипциясы сақталды.',
                },
                is_read=False,
            )
            db.session.add(n)
            db.session.commit()

        from tests.conftest import login

        login(client, 'patient@test.kz')
        with client.session_transaction() as sess:
            sess['language'] = 'en'

        resp = client.get('/api/notifications')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['notifications'][0]['title'] == 'Consultation transcription ready'
        assert 'Test Doctor' in data['notifications'][0]['message']
