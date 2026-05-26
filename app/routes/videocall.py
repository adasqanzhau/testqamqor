import logging
import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from app import db, socketio, csrf
from app.models import User, Appointment, VideoCall, Notification, MedicalRecord
from app import db as _db
import app.i18n as i18n

logger = logging.getLogger(__name__)

videocall_bp = Blueprint('videocall', __name__)


@videocall_bp.route('/room/<room_id>')
@login_required
def room(room_id):
    videocall = VideoCall.query.filter_by(room_id=room_id).first()
    if not videocall:
        abort(404)
    appointment = videocall.appointment

    if current_user.id not in (appointment.doctor_id, appointment.patient_id):
        abort(403)

    if videocall.status == 'ended' and (videocall.transcription or videocall.summary):
        return render_template('videocall/summary.html', videocall=videocall, appointment=appointment)

    call = {
        'room_id': videocall.room_id,
        'appointment_id': videocall.appointment_id,
        'doctor_name': appointment.doctor.full_name if appointment.doctor else '',
        'patient_name': appointment.patient.full_name if appointment.patient else '',
    }
    return render_template('videocall/room.html', videocall=videocall, appointment=appointment, call=call)


@videocall_bp.route('/start/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def start(appointment_id):
    appointment = db.session.get(Appointment, appointment_id) or abort(404)

    if current_user.id not in (appointment.doctor_id, appointment.patient_id):
        abort(403)

    if appointment.videocall:
        return redirect(url_for('videocall.room', room_id=appointment.videocall.room_id))

    if appointment.status in ('completed', 'cancelled'):
        flash('Нельзя начать звонок для завершённого или отменённого приёма.', 'danger')
        return redirect(url_for('patient.index') if current_user.role == 'patient' else url_for('doctor.dashboard'))

    room_id = str(uuid.uuid4())

    videocall = VideoCall(
        appointment_id=appointment.id,
        room_id=room_id,
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
        status='active',
    )

    if appointment.status == 'scheduled':
        appointment.status = 'in_progress'

    db.session.add(videocall)
    db.session.commit()

    return redirect(url_for('videocall.room', room_id=room_id))


@videocall_bp.route('/end/<room_id>', methods=['POST'])
@login_required
@csrf.exempt
def end(room_id):
    videocall = VideoCall.query.filter_by(room_id=room_id).first() or abort(404)
    appointment = videocall.appointment

    if current_user.id not in (appointment.doctor_id, appointment.patient_id):
        abort(403)

    was_active = videocall.status != 'ended'

    videocall.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if videocall.started_at:
        videocall.duration_seconds = int((videocall.ended_at - videocall.started_at).total_seconds())
    videocall.status = 'ended'

    if appointment.status in ('scheduled', 'in_progress', 'awaiting_report'):
        appointment.status = 'completed'

    db.session.commit()

    if was_active:
        try:
            patient_name = appointment.patient.full_name if appointment.patient else 'Пациент'
            doctor_name = appointment.doctor.full_name if appointment.doctor else 'Врач'
            room_link = url_for('videocall.room', room_id=room_id)

            # create notification texts in recipient's language
            doctor = db.session.get(User, appointment.doctor_id)
            doc_lang = (doctor.language if doctor and doctor.language else current_app.config.get('BABEL_DEFAULT_LOCALE', 'ru'))
            title_doc = i18n.t('videocall.completed', doc_lang, 'Видеоконсультация завершена')
            msg_doc = i18n.t('videocall.with_patient', doc_lang, 'Видеоконсультация с пациентом %(name)s') % {'name': patient_name}
            db.session.add(Notification(
                user_id=appointment.doctor_id,
                title=title_doc,
                message=msg_doc,
                title_i18n={
                    lang: i18n.t('videocall.completed', lang, 'Видеоконсультация завершена')
                    for lang in current_app.config.get('LANGUAGES', {}).keys()
                },
                message_i18n={
                    lang: i18n.t('videocall.with_patient', lang, 'Видеоконсультация с пациентом %(name)s') % {'name': patient_name}
                    for lang in current_app.config.get('LANGUAGES', {}).keys()
                },
                type='success',
                link=room_link,
            ))
            patient = db.session.get(User, appointment.patient_id)
            pat_lang = (patient.language if patient and patient.language else current_app.config.get('BABEL_DEFAULT_LOCALE', 'ru'))
            title_pat = i18n.t('videocall.completed', pat_lang, 'Видеоконсультация завершена')
            msg_pat = i18n.t('videocall.with_doctor', pat_lang, 'Видеоконсультация с доктором %(name)s') % {'name': doctor_name}
            db.session.add(Notification(
                user_id=appointment.patient_id,
                title=title_pat,
                message=msg_pat,
                title_i18n={
                    lang: i18n.t('videocall.completed', lang, 'Видеоконсультация завершена')
                    for lang in current_app.config.get('LANGUAGES', {}).keys()
                },
                message_i18n={
                    lang: i18n.t('videocall.with_doctor', lang, 'Видеоконсультация с доктором %(name)s') % {'name': doctor_name}
                    for lang in current_app.config.get('LANGUAGES', {}).keys()
                },
                type='success',
                link=room_link,
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('Failed to create end-of-call notifications')

    flash('Видеозвонок завершён.', 'success')
    if current_user.role == 'patient':
        return redirect(url_for('patient.index'))
    return redirect(url_for('doctor.patient_detail', patient_id=appointment.patient_id))


@videocall_bp.route('/transcribe/<room_id>', methods=['POST'])
@login_required
@csrf.exempt
def transcribe(room_id):
    videocall = VideoCall.query.filter_by(room_id=room_id).first() or abort(404)
    appointment = videocall.appointment

    if current_user.id not in (appointment.doctor_id, appointment.patient_id):
        abort(403)

    if videocall.transcription:
        return jsonify({'status': 'already_saved', 'summary': videocall.summary})

    data = request.get_json(silent=True) or {}
    raw_text = (data.get('transcription') or '').strip()
    transcription_text = raw_text[:50000]  # limit length

    patient_name = appointment.patient.full_name if appointment.patient else 'Пациент'
    doctor_name = appointment.doctor.full_name if appointment.doctor else 'Врач'
    appointment_date = (
        appointment.scheduled_time.strftime('%d.%m.%Y %H:%M')
        if appointment.scheduled_time else ''
    )

    # Store the raw transcription text so downstream consumers can use it directly.
    videocall.transcription = transcription_text or 'Транскрипция не велась во время звонка.'

    summary = None
    if transcription_text:
        from app.ai import chat_completion
        summary_messages = [
            {
                'role': 'system',
                'content': (
                    'Вы — медицинский ассистент. Создайте краткое резюме телемедицинской консультации '
                    'на основе транскрипции разговора врача и пациента. Укажите основные жалобы, '
                    'рекомендации врача и ключевые моменты. Отвечайте на русском языке.'
                ),
            },
            {
                'role': 'user',
                'content': f'<transcription>\n{transcription_text}\n</transcription>\n\nСоздайте краткое резюме.',
            },
        ]
        ai_summary, error = chat_completion(summary_messages, max_tokens=1000, temperature=0.3)
        if ai_summary:
            summary = ai_summary
        elif error:
            logger.warning('Transcription summary failed: %s', error)

    if not summary:
        import json

        ru_summary = (
            f'Видеоконсультация между врачом {doctor_name} и пациентом {patient_name} '
            f'состоялась {appointment_date}. '
            + ('Подробная транскрипция недоступна.' if not transcription_text
               else 'AI-резюме не удалось сформировать.')
        )
        en_summary = (
            f'The video consultation between doctor {doctor_name} and patient {patient_name} took place on {appointment_date}. '
            + ('A detailed transcription is not available.' if not transcription_text else 'AI summary could not be generated.')
        )
        kz_summary = (
            f'Дәрігер {doctor_name} пен пациент {patient_name} арасындағы бейнеқызмет {appointment_date} өтті. '
            + ('Толық транскрипция қолжетімсіз.' if not transcription_text else 'AI-резюме құру мүмкін болмады.')
        )
        summary = ru_summary
        try:
            import json
            videocall.summary = json.dumps({'ru': ru_summary, 'kz': kz_summary, 'en': en_summary}, ensure_ascii=False)
        except Exception:
            videocall.summary = ru_summary
    else:
        videocall.summary = summary

    try:
        med_content = summary or videocall.summary or ''
        if transcription_text:
            med_content += '\n\n--- Транскрипция ---\n' + transcription_text
        med_record = MedicalRecord(
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            record_type='consultation',
            title=f'Видеоконсультация — {appointment_date or "без даты"}',
            content=med_content,
        )
        db.session.add(med_record)
    except Exception:
        logger.exception('Failed to build medical record from transcription')

    db.session.commit()

    room_link = url_for('videocall.room', room_id=room_id)
    # Localize transcription-ready notifications per recipient language
    doctor = db.session.get(User, appointment.doctor_id)
    doc_lang = (doctor.language if doctor and doctor.language else current_app.config.get('BABEL_DEFAULT_LOCALE', 'ru'))
    title_doc = 'Транскрипция консультации готова'
    msg_doc = f'Транскрипция видеоконсультации с пациентом {patient_name} сохранена.'
    langs = current_app.config.get('LANGUAGES', {}).keys()
    title_map_doc = {lang: i18n.t('videocall.transcription', lang, 'Транскрипция консультации готова') for lang in langs}
    msg_map_doc = {lang: i18n.t('videocall.transcription_saved_patient', lang, 'Транскрипция видеоконсультации с пациентом %(name)s') % {'name': patient_name} for lang in langs}
    db.session.add(Notification(
        user_id=appointment.doctor_id,
        title=title_doc,
        message=msg_doc,
        title_i18n=title_map_doc,
        message_i18n=msg_map_doc,
        type='info',
        link=room_link,
    ))

    patient = db.session.get(User, appointment.patient_id)
    pat_lang = (patient.language if patient and patient.language else current_app.config.get('BABEL_DEFAULT_LOCALE', 'ru'))
    title_pat = 'Транскрипция консультации готова'
    msg_pat = f'Транскрипция видеоконсультации с доктором {doctor_name} сохранена.'
    title_map_pat = {lang: i18n.t('videocall.transcription', lang, 'Транскрипция консультации готова') for lang in langs}
    msg_map_pat = {lang: i18n.t('videocall.transcription_saved_doctor', lang, 'Транскрипция видеоконсультации с доктором %(name)s сохранена.') % {'name': doctor_name} for lang in langs}
    db.session.add(Notification(
        user_id=appointment.patient_id,
        title=title_pat,
        message=msg_pat,
        title_i18n=title_map_pat,
        message_i18n=msg_map_pat,
        type='info',
        link=room_link,
    ))
    db.session.commit()

    return jsonify({
        'status': 'success',
        'summary': summary,
    })



_room_participants = {}


def _is_room_participant(room_id):
    """Check if current_user is authenticated and is a participant of the given room."""
    if not current_user.is_authenticated:
        return False
    if not room_id:
        return False
    videocall = VideoCall.query.filter_by(room_id=room_id).first()
    if not videocall:
        return False
    appointment = videocall.appointment
    return current_user.id in (appointment.doctor_id, appointment.patient_id)


@socketio.on('join_room')
def handle_join_room(data):
    room_id = data.get('room_id')
    if not _is_room_participant(room_id):
        emit('error', {'message': 'Доступ запрещён'})
        return

    from flask import request as flask_request
    sid = flask_request.sid

    participants = _room_participants.setdefault(room_id, set())
    is_first = len(participants) == 0
    participants.add(sid)

    join_room(room_id)
    logger.info('User %s joined room %s (sid=%s, first=%s, total=%d)',
                current_user.id, room_id, sid, is_first, len(participants))

    emit('joined', {
        'user_id': current_user.id,
        'is_initiator': is_first,
        'participants_count': len(participants),
    })

    if not is_first:
        emit('peer_joined', {'user_id': current_user.id}, to=room_id, include_self=False)


@socketio.on('offer')
def handle_offer(data):
    room_id = data.get('room_id')
    if not _is_room_participant(room_id):
        return
    logger.info('Relaying offer in room %s', room_id)
    emit('offer', data, to=room_id, include_self=False)


@socketio.on('answer')
def handle_answer(data):
    room_id = data.get('room_id')
    if not _is_room_participant(room_id):
        return
    logger.info('Relaying answer in room %s', room_id)
    emit('answer', data, to=room_id, include_self=False)


@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    room_id = data.get('room_id')
    if not _is_room_participant(room_id):
        return
    emit('ice_candidate', data, to=room_id, include_self=False)


@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data.get('room_id')
    if not room_id:
        return

    from flask import request as flask_request
    sid = flask_request.sid
    if room_id in _room_participants:
        _room_participants[room_id].discard(sid)
        if not _room_participants[room_id]:
            del _room_participants[room_id]

    leave_room(room_id)
    uid = current_user.id if current_user.is_authenticated else None
    emit('user_left', {'user_id': uid}, to=room_id, include_self=False)


@socketio.on('disconnect')
def handle_disconnect():
    """Clean up room participants on disconnect."""
    from flask import request as flask_request
    sid = flask_request.sid
    for room_id in list(_room_participants.keys()):
        if sid in _room_participants[room_id]:
            _room_participants[room_id].discard(sid)
            if not _room_participants[room_id]:
                del _room_participants[room_id]
            emit('user_left', {}, to=room_id)