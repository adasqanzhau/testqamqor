"""Tests for multilingual videocall text helpers."""
import json
from unittest.mock import patch

from app.localized_text import (
    empty_transcription_messages,
    fallback_summary_messages,
    generate_consultation_i18n,
    pick_localized,
    strip_embedded_transcription,
    to_multilingual_json,
    translate_transcription_only,
)


class TestStripEmbeddedTranscription:
    def test_removes_transcription_section(self):
        content = (
            'Видеоконсультация между врачом и пациентом.\n\n'
            '--- Транскрипция ---\n'
            'Добрый день у меня болит голова'
        )
        assert strip_embedded_transcription(content) == 'Видеоконсультация между врачом и пациентом.'

    def test_keeps_content_without_marker(self):
        assert strip_embedded_transcription('Только резюме') == 'Только резюме'


class TestPickLocalized:
    def test_plain_text_passthrough(self):
        assert pick_localized('Привет', 'en') == 'Привет'

    def test_json_prefers_requested_language(self):
        raw = to_multilingual_json({
            'ru': 'Русский',
            'en': 'English',
            'kz': 'Қазақша',
        })
        assert pick_localized(raw, 'en') == 'English'
        assert pick_localized(raw, 'kz') == 'Қазақша'

    def test_json_fallback_order(self):
        raw = json.dumps({'ru': 'Русский', 'en': 'English'}, ensure_ascii=False)
        assert pick_localized(raw, 'kz') == 'Русский'


class TestFallbackMessages:
    def test_empty_transcription_messages_cover_all_langs(self):
        messages = empty_transcription_messages()
        assert set(messages) == {'ru', 'en', 'kz'}

    def test_fallback_summary_without_transcription(self):
        messages = fallback_summary_messages(
            doctor_name='Dr A',
            patient_name='Patient B',
            appointment_date='01.01.2026 10:00',
            has_transcription=False,
        )
        assert 'Dr A' in messages['en']
        assert 'Patient B' in messages['ru']
        assert '01.01.2026 10:00' in messages['kz']


class TestGenerateConsultationI18n:
    @patch('app.ai.chat_completion')
    def test_parses_multilingual_payload(self, mock_chat):
        mock_chat.return_value = (
            json.dumps({
                'summary': {
                    'ru': 'Краткое резюме',
                    'en': 'Brief summary',
                    'kz': 'Қысқаша мазмұн',
                },
                'transcription': {
                    'ru': 'Пациент жалуется на боль',
                    'en': 'Patient complains of pain',
                    'kz': 'Пациент ауыруға шағымданады',
                },
            }, ensure_ascii=False),
            None,
        )
        summary, transcription = generate_consultation_i18n('Пациент жалуется на боль')
        assert summary['en'] == 'Brief summary'
        assert transcription['ru'] == 'Пациент жалуется на боль'

    @patch('app.ai.chat_completion')
    def test_returns_none_on_invalid_json(self, mock_chat):
        mock_chat.return_value = ('not json', None)
        assert generate_consultation_i18n('текст') is None


class TestTranslateTranscriptionOnly:
    @patch('app.ai.chat_completion')
    def test_keeps_russian_source(self, mock_chat):
        mock_chat.return_value = (
            json.dumps({
                'ru': 'ignored',
                'en': 'Patient complains',
                'kz': 'Пациент шағымданады',
            }, ensure_ascii=False),
            None,
        )
        result = translate_transcription_only('Пациент жалуется')
        assert result['ru'] == 'Пациент жалуется'
        assert result['en'] == 'Patient complains'

    @patch('app.ai.chat_completion')
    def test_falls_back_to_russian_only(self, mock_chat):
        mock_chat.return_value = (None, 'AI unavailable')
        result = translate_transcription_only('Только русский')
        assert result == {'ru': 'Только русский'}
