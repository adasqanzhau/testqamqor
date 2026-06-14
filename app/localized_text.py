"""Helpers for storing and reading multilingual text fields (ru / en / kz)."""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

LANGS = ('ru', 'en', 'kz')
LANG_FALLBACK_ORDER = ('ru', 'en', 'kz')
TRANSCRIPTION_SECTION_MARKERS = (
    '--- Транскрипция ---',
    '--- Transcription ---',
    '--- Әңгіме транскрипциясы ---',
)


def strip_embedded_transcription(content: Optional[str]) -> str:
    """Remove videocall transcription appended to a medical record body."""
    if not content:
        return ''
    for marker in TRANSCRIPTION_SECTION_MARKERS:
        if marker in content:
            return content.split(marker, 1)[0].rstrip()
    return content


def to_multilingual_json(mapping: dict) -> str:
    payload = {lang: mapping[lang] for lang in LANGS if mapping.get(lang)}
    return json.dumps(payload, ensure_ascii=False)


def pick_localized(raw: Optional[str], lang: str) -> str:
    """Return the best matching string for *lang* from plain text or JSON mapping."""
    if not raw:
        return ''
    if isinstance(raw, str):
        stripped = raw.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                mapping = json.loads(raw)
                if isinstance(mapping, dict):
                    for fav in (lang, *LANG_FALLBACK_ORDER):
                        if fav in mapping and mapping[fav]:
                            return mapping[fav]
            except (json.JSONDecodeError, TypeError):
                pass
    return str(raw)


def parse_ai_json(text: str) -> Optional[dict]:
    """Parse JSON returned by the AI, tolerating optional markdown fences."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning('Failed to parse AI JSON response')
        return None
    return data if isinstance(data, dict) else None


def _normalize_lang_map(data: Optional[dict], *, required_lang: str = 'ru') -> Optional[dict]:
    if not isinstance(data, dict):
        return None
    result = {}
    for lang in LANGS:
        value = data.get(lang)
        if isinstance(value, str) and value.strip():
            result[lang] = value.strip()
    if required_lang not in result:
        return None
    return result


def fallback_summary_messages(
    *,
    doctor_name: str,
    patient_name: str,
    appointment_date: str,
    has_transcription: bool,
) -> dict:
    if has_transcription:
        ru_tail = 'AI-резюме не удалось сформировать.'
        en_tail = 'AI summary could not be generated.'
        kz_tail = 'AI-резюме құру мүмкін болмады.'
    else:
        ru_tail = 'Подробная транскрипция недоступна.'
        en_tail = 'A detailed transcription is not available.'
        kz_tail = 'Толық транскрипция қолжетімсіз.'

    return {
        'ru': (
            f'Видеоконсультация между врачом {doctor_name} и пациентом {patient_name} '
            f'состоялась {appointment_date}. {ru_tail}'
        ),
        'en': (
            f'The video consultation between doctor {doctor_name} and patient {patient_name} '
            f'took place on {appointment_date}. {en_tail}'
        ),
        'kz': (
            f'Дәрігер {doctor_name} пен пациент {patient_name} арасындағы бейнеқызмет '
            f'{appointment_date} өтті. {kz_tail}'
        ),
    }


def empty_transcription_messages() -> dict:
    return {
        'ru': 'Транскрипция не велась во время звонка.',
        'en': 'Transcription was not recorded during the call.',
        'kz': 'Қоңырау кезінде транскрипция жүргізілмеді.',
    }


def generate_consultation_i18n(transcription_text: str) -> Optional[tuple[dict, dict]]:
    """Use AI to build multilingual summary and transcription. Returns None on failure."""
    from app.ai import chat_completion

    messages = [
        {
            'role': 'system',
            'content': (
                'Вы — медицинский ассистент. На основе транскрипции телемедицинской консультации '
                'врача и пациента:\n'
                '1. Создайте краткое резюме (жалобы, рекомендации врача, ключевые моменты) '
                'на русском, английском и казахском языках.\n'
                '2. Сохраните исходную транскрипцию в поле ru и переведите её на английский (en) '
                'и казахский (kz).\n\n'
                'Ответьте ТОЛЬКО валидным JSON без markdown:\n'
                '{"summary":{"ru":"...","en":"...","kz":"..."},'
                '"transcription":{"ru":"...","en":"...","kz":"..."}}'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'<transcription>\n{transcription_text}\n</transcription>\n\n'
                'Сформируйте JSON с резюме и переводами транскрипции.'
            ),
        },
    ]
    response, error = chat_completion(messages, max_tokens=2000, temperature=0.3)
    if error or not response:
        if error:
            logger.warning('Multilingual consultation AI failed: %s', error)
        return None

    payload = parse_ai_json(response)
    if not payload:
        return None

    summary = _normalize_lang_map(payload.get('summary'))
    transcription = _normalize_lang_map(payload.get('transcription'))
    if not summary or not transcription:
        return None
    transcription['ru'] = transcription_text
    return summary, transcription


def build_consultation_texts(
    *,
    transcription_text: str,
    doctor_name: str,
    patient_name: str,
    appointment_date: str,
) -> tuple[dict, dict]:
    """Build multilingual summary and transcription payloads for a videocall."""
    if transcription_text:
        generated = generate_consultation_i18n(transcription_text)
        if generated:
            return generated
        return (
            fallback_summary_messages(
                doctor_name=doctor_name,
                patient_name=patient_name,
                appointment_date=appointment_date,
                has_transcription=True,
            ),
            translate_transcription_only(transcription_text),
        )
    return (
        fallback_summary_messages(
            doctor_name=doctor_name,
            patient_name=patient_name,
            appointment_date=appointment_date,
            has_transcription=False,
        ),
        empty_transcription_messages(),
    )


def _is_full_json(raw: Optional[str]) -> bool:
    if not raw:
        return False
    try:
        mapping = json.loads(raw.strip())
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(mapping, dict) and all(mapping.get(lang) for lang in LANGS)


def _recover_summary_from_medical_records(videocall) -> str:
    """Best-effort recovery of a legacy Russian summary from linked medical records."""
    from app.models import MedicalRecord

    appointment = videocall.appointment
    if not appointment:
        return ''

    appointment_date = (
        appointment.scheduled_time.strftime('%d.%m.%Y %H:%M')
        if appointment.scheduled_time else ''
    )
    records = MedicalRecord.query.filter_by(
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        record_type='consultation',
    ).order_by(MedicalRecord.id.desc()).all()

    for record in records:
        content = (record.content or '').strip()
        if not content:
            continue
        if appointment_date and appointment_date not in (record.title or '') and appointment_date not in content:
            continue
        summary_part = content.split('--- Транскрипция ---', 1)[0].strip()
        if summary_part and not _is_generated_fallback_summary(summary_part):
            return summary_part
    return ''


def relocalize_videocall(videocall) -> bool:
    """Upgrade legacy or partially localized videocall fields to multilingual JSON."""
    needs_transcription = not _is_full_json(videocall.transcription)

    appointment = videocall.appointment
    doctor_name = appointment.doctor.full_name if appointment and appointment.doctor else 'Врач'
    patient_name = appointment.patient.full_name if appointment and appointment.patient else 'Пациент'
    appointment_date = (
        appointment.scheduled_time.strftime('%d.%m.%Y %H:%M')
        if appointment and appointment.scheduled_time else ''
    )

    stored_summary_ru = pick_localized(videocall.summary, 'ru')
    legacy_summary_ru = stored_summary_ru
    if _is_generated_fallback_summary(legacy_summary_ru):
        recovered = _recover_summary_from_medical_records(videocall)
        if recovered:
            legacy_summary_ru = recovered

    needs_summary = not _is_full_json(videocall.summary) or (
        legacy_summary_ru
        and not _is_generated_fallback_summary(legacy_summary_ru)
        and _is_generated_fallback_summary(stored_summary_ru)
    )
    if not needs_summary and not needs_transcription:
        return False

    ru_transcription = pick_localized(videocall.transcription, 'ru')
    empty_ru = empty_transcription_messages()['ru']
    transcription_text = ''
    if ru_transcription and ru_transcription != empty_ru:
        transcription_text = ru_transcription

    if needs_summary:
        summary_map, transcription_map = build_consultation_texts(
            transcription_text=transcription_text,
            doctor_name=doctor_name,
            patient_name=patient_name,
            appointment_date=appointment_date,
        )
        if (
            legacy_summary_ru
            and not _is_generated_fallback_summary(legacy_summary_ru)
            and _is_generated_fallback_summary(summary_map.get('ru', ''))
        ):
            summary_map = translate_ru_multilingual(legacy_summary_ru, content_kind='резюме консультации')
        videocall.summary = to_multilingual_json(summary_map)
    else:
        transcription_map = {}

    if needs_transcription:
        if transcription_text:
            transcription_map = translate_ru_multilingual(
                transcription_text,
                content_kind='транскрипция консультации',
            )
        else:
            transcription_map = empty_transcription_messages()
        videocall.transcription = to_multilingual_json(transcription_map)

    return True


def _is_generated_fallback_summary(text: str) -> bool:
    markers = (
        'AI-резюме не удалось сформировать.',
        'Подробная транскрипция недоступна.',
        'AI summary could not be generated.',
        'A detailed transcription is not available.',
        'AI-резюме құру мүмкін болмады.',
        'Толық транскрипция қолжетімсіз.',
    )
    return any(marker in text for marker in markers)


def translate_ru_multilingual(ru_text: str, *, content_kind: str) -> dict:
    """Translate Russian medical text to en/kz; always keep the original Russian text."""
    from app.ai import chat_completion

    if not ru_text.strip():
        return {'ru': ru_text}

    messages = [
        {
            'role': 'system',
            'content': (
                f'Переведите следующий текст ({content_kind}) на английский и казахский языки. '
                'Русский вариант оставьте без изменений. '
                'Ответьте ТОЛЬКО JSON: {"ru":"...","en":"...","kz":"..."}'
            ),
        },
        {'role': 'user', 'content': ru_text},
    ]
    response, error = chat_completion(messages, max_tokens=1500, temperature=0.2)
    if not error and response:
        mapping = _normalize_lang_map(parse_ai_json(response))
        if mapping:
            mapping['ru'] = ru_text
            return mapping
    return {'ru': ru_text}


def translate_transcription_only(transcription_text: str) -> dict:
    """Translate transcription to en/kz; always keep the original Russian text."""
    return translate_ru_multilingual(transcription_text, content_kind='транскрипция консультации')
