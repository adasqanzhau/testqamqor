import os
import uuid
from datetime import datetime, timedelta, timezone, date

from flask import Blueprint, render_template, redirect, url_for, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.avatar_utils import remove_user_avatar, replace_user_avatar
from app.i18n import flash_message as flash_i18n
from app.models import (
    User, Clinic, Appointment, VideoCall, ClinicSpecialization, Notification,
    Prescription, MedicalRecord, Review, ChatMessage,
)
from app.forms import ClinicForm, ProfileForm

admin = Blueprint('admin', __name__, url_prefix='/admin')


ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'svg'}


def superadmin_required(f):
    """Decorator that checks if the current user is a superadmin."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'superadmin':
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def save_logo(file):
    """Save an uploaded clinic logo and return the stored filename (without subdir prefix)."""
    if not file or not getattr(file, 'filename', ''):
        return None
    original = secure_filename(file.filename) or ''
    if '.' not in original:
        return None
    ext = original.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(
        current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'static', 'uploads'),
        'clinics',
    )
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return filename


def _wipe_user(user):
    """Remove all records that reference the given user so it can be hard-deleted.

    Ordering matters: we must expunge rows that SQLAlchemy will later try to
    cascade-delete BEFORE issuing the bulk DELETEs — otherwise the session ends up
    with stale references and raises StaleDataError / FK violations on PostgreSQL.

    Strategy:
      1. Load every Appointment the user is involved in and delete it through the
         session so SQLAlchemy's 'all, delete-orphan' cascade removes the attached
         VideoCall / Prescription / Review consistently.
      2. Flush to push those DELETEs to the database immediately.
      3. Bulk-DELETE any orphan rows that still reference the user directly
         (prescriptions/reviews/medical records where the user is mentioned outside
         an appointment, notifications, chat messages).
      4. Flush again so the session is clean before the caller deletes the user.
    """
    appts = Appointment.query.filter(
        db.or_(Appointment.patient_id == user.id, Appointment.doctor_id == user.id)
    ).all()
    for appt in appts:
        db.session.delete(appt)
    db.session.flush()

    Prescription.query.filter(
        db.or_(Prescription.patient_id == user.id, Prescription.doctor_id == user.id)
    ).delete(synchronize_session=False)
    Review.query.filter(
        db.or_(Review.patient_id == user.id, Review.doctor_id == user.id)
    ).delete(synchronize_session=False)
    MedicalRecord.query.filter(
        db.or_(MedicalRecord.patient_id == user.id, MedicalRecord.doctor_id == user.id)
    ).delete(synchronize_session=False)
    Notification.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    ChatMessage.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    db.session.flush()

@admin.route('/')
@login_required
@superadmin_required
def dashboard():
    total_clinics = Clinic.query.count()
    total_doctors = User.query.filter_by(role='doctor').count()
    total_patients = User.query.filter_by(role='patient').count()
    total_appointments = Appointment.query.count()

    recent_clinics = Clinic.query.order_by(Clinic.created_at.desc()).limit(5).all()
    recent_appointments = (
        Appointment.query
        .order_by(Appointment.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        'admin/dashboard.html',
        total_clinics=total_clinics,
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        recent_clinics=recent_clinics,
        recent_appointments=recent_appointments,
    )

@admin.route('/clinics')
@login_required
@superadmin_required
def clinics():
    page = request.args.get('page', 1, type=int)
    query = Clinic.query.order_by(Clinic.created_at.desc())

    search = request.args.get('search', '', type=str).strip()
    if search:
        safe_search = search.replace('%', r'\%').replace('_', r'\_')
        query = query.filter(Clinic.name.ilike(f'%{safe_search}%'))

    clinics = query.paginate(page=page, per_page=20, error_out=False)
    return render_template(
        'admin/clinics.html',
        clinics=clinics,
        search=search,
    )

@admin.route('/clinics/create', methods=['GET', 'POST'])
@login_required
@superadmin_required
def create_clinic():
    form = ClinicForm()

    if form.validate_on_submit():
        if not form.admin_email.data or not form.admin_password.data:
            flash_i18n('Укажите email и пароль администратора клиники.', 'danger')
            return render_template('admin/clinic_form.html', form=form, title='Создание клиники')

        if User.query.filter_by(email=form.admin_email.data).first():
            flash_i18n('Пользователь с таким email уже существует.', 'danger')
            return render_template('admin/clinic_form.html', form=form, title='Создание клиники')

        clinic = Clinic(
            name=form.name.data,
            description=form.description.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            website=form.website.data,
            primary_color=form.primary_color.data or '#0d6efd',
            secondary_color=form.secondary_color.data or '#6c757d',
            working_hours_start=form.working_hours_start.data or '09:00',
            working_hours_end=form.working_hours_end.data or '18:00',
        )

        if form.logo.data and getattr(form.logo.data, 'filename', ''):
            saved_logo = save_logo(form.logo.data)
            if saved_logo:
                clinic.logo = saved_logo

        db.session.add(clinic)
        db.session.flush()

        clinic_admin = User(
            email=form.admin_email.data,
            first_name=form.admin_first_name.data or 'Admin',
            last_name=form.admin_last_name.data or clinic.name,
            role='clinic_admin',
            clinic_id=clinic.id,
            is_active=True,
        )
        clinic_admin.set_password(form.admin_password.data)
        db.session.add(clinic_admin)

        db.session.commit()
        flash_i18n('Клиника "%(name)s" успешно создана.', 'success', name=clinic.name)
        return redirect(url_for('admin.clinics'))

    return render_template('admin/clinic_form.html', form=form, title='Создание клиники')

@admin.route('/clinics/<int:clinic_id>/edit', methods=['GET', 'POST'])
@login_required
@superadmin_required
def edit_clinic(clinic_id):
    clinic = db.session.get(Clinic, clinic_id) or abort(404)
    form = ClinicForm(obj=clinic)

    if form.validate_on_submit():
        try:
            clinic.name = form.name.data
            clinic.description = form.description.data
            clinic.address = form.address.data
            clinic.phone = form.phone.data
            clinic.email = form.email.data
            clinic.website = form.website.data
            clinic.primary_color = form.primary_color.data or clinic.primary_color
            clinic.secondary_color = form.secondary_color.data or clinic.secondary_color
            clinic.working_hours_start = form.working_hours_start.data or clinic.working_hours_start
            clinic.working_hours_end = form.working_hours_end.data or clinic.working_hours_end

            if form.logo.data and getattr(form.logo.data, 'filename', ''):
                saved_logo = save_logo(form.logo.data)
                if saved_logo:
                    clinic.logo = saved_logo

            db.session.commit()
            flash_i18n('Клиника "%(name)s" обновлена.', 'success', name=clinic.name)
            return redirect(url_for('admin.clinics'))
        except Exception as exc:
            db.session.rollback()
            current_app.logger.exception('Failed to update clinic %s', clinic_id)
            flash_i18n('Не удалось обновить клинику: %(exc)s', 'danger', exc=exc)

    return render_template('admin/clinic_form.html', form=form, title='Редактирование клиники', clinic=clinic)

@admin.route('/clinics/<int:clinic_id>/delete', methods=['POST'])
@login_required
@superadmin_required
def delete_clinic(clinic_id):
    clinic = db.session.get(Clinic, clinic_id) or abort(404)
    name = clinic.name

    try:
        members = User.query.filter(User.clinic_id == clinic.id).all()
        for member in members:
            _wipe_user(member)

        stray_appts = Appointment.query.filter_by(clinic_id=clinic.id).all()
        for appt in stray_appts:
            db.session.delete(appt)
        db.session.flush()

        db.session.delete(clinic)
        db.session.commit()
        flash_i18n('Клиника "%(name)s" удалена.', 'warning', name=name)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception('Failed to delete clinic %s', clinic_id)
        flash_i18n('Не удалось удалить клинику: %(exc)s', 'danger', exc=exc)
    return redirect(url_for('admin.clinics'))

@admin.route('/clinics/<int:clinic_id>/toggle', methods=['POST'])
@login_required
@superadmin_required
def toggle_clinic(clinic_id):
    clinic = db.session.get(Clinic, clinic_id) or abort(404)
    clinic.is_active = not clinic.is_active
    db.session.commit()
    if clinic.is_active:
        flash_i18n('Клиника "%(name)s" активирована.', 'info', name=clinic.name)
    else:
        flash_i18n('Клиника "%(name)s" деактивирована.', 'info', name=clinic.name)
    return redirect(url_for('admin.clinics'))

@admin.route('/users')
@login_required
@superadmin_required
def users():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '', type=str)
    search = request.args.get('search', '', type=str)

    query = User.query.order_by(User.created_at.desc())

    if role_filter:
        query = query.filter_by(role=role_filter)
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
            )
        )

    users = query.paginate(page=page, per_page=20, error_out=False)
    return render_template(
        'admin/users.html',
        users=users,
        role_filter=role_filter,
        search=search,
    )

@admin.route('/analytics')
@login_required
@superadmin_required
def analytics():
    total_clinics = Clinic.query.count()
    active_clinics = Clinic.query.filter_by(is_active=True).count()
    total_doctors = User.query.filter_by(role='doctor').count()
    total_patients = User.query.filter_by(role='patient').count()
    total_appointments = Appointment.query.count()
    total_videocalls = VideoCall.query.count()

    status_stats = dict(
        db.session.query(Appointment.status, db.func.count(Appointment.id))
        .group_by(Appointment.status)
        .all()
    )

    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    recent_appointments_count = Appointment.query.filter(
        Appointment.created_at >= thirty_days_ago
    ).count()

    new_users_count = User.query.filter(
        User.created_at >= thirty_days_ago
    ).count()

    top_clinics = (
        db.session.query(Clinic, db.func.count(Appointment.id).label('appointment_count'))
        .join(Appointment, Appointment.clinic_id == Clinic.id)
        .group_by(Clinic.id)
        .order_by(db.func.count(Appointment.id).desc())
        .limit(10)
        .all()
    )

    RU_MONTHS = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
    monthly_data = []
    today_d = date.today()
    for i in range(5, -1, -1):
        month = today_d.month - i
        year = today_d.year
        while month <= 0:
            month += 12
            year -= 1
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)

        apt_count = Appointment.query.filter(
            Appointment.created_at >= month_start,
            Appointment.created_at < month_end,
        ).count()
        new_pats = User.query.filter(
            User.role == 'patient',
            User.created_at >= month_start,
            User.created_at < month_end,
        ).count()
        new_docs = User.query.filter(
            User.role == 'doctor',
            User.created_at >= month_start,
            User.created_at < month_end,
        ).count()
        monthly_data.append({
            'label': f'{RU_MONTHS[month - 1]} {year}',
            'appointments': apt_count,
            'new_patients': new_pats,
            'new_doctors': new_docs,
        })

    return render_template(
        'admin/analytics.html',
        total_clinics=total_clinics,
        active_clinics=active_clinics,
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_videocalls=total_videocalls,
        status_stats=status_stats,
        recent_appointments_count=recent_appointments_count,
        new_users_count=new_users_count,
        top_clinics=top_clinics,
        monthly_data=monthly_data,
    )

@admin.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@superadmin_required
def toggle_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.role == 'superadmin':
        flash_i18n('Нельзя изменить статус суперадмина.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    if user.is_active:
        flash_i18n('Пользователь "%(name)s" активирован.', 'info', name=user.full_name)
    else:
        flash_i18n('Пользователь "%(name)s" деактивирован.', 'info', name=user.full_name)
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@superadmin_required
def delete_user(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.role == 'superadmin':
        flash_i18n('Нельзя удалить суперадмина.', 'danger')
        return redirect(url_for('admin.users'))
    name = user.full_name
    try:
        _wipe_user(user)
        db.session.delete(user)
        db.session.commit()
        flash_i18n('Пользователь "%(name)s" удалён.', 'warning', name=name)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception('Failed to delete user %s', user_id)
        flash_i18n('Не удалось удалить пользователя: %(exc)s', 'danger', exc=exc)
    return redirect(url_for('admin.users'))

@admin.route('/profile', methods=['GET', 'POST'])
@login_required
@superadmin_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data

        remove_avatar = request.form.get('remove_avatar') == '1'
        if remove_avatar and current_user.avatar:
            remove_user_avatar(current_user)
            flash_i18n('Фото профиля удалено.', 'success')

        if not remove_avatar and form.avatar.data and getattr(form.avatar.data, 'filename', ''):
            try:
                replace_user_avatar(current_user, form.avatar.data)
            except Exception as e:
                current_app.logger.error(f"Error saving admin avatar: {e}")
                flash_i18n('Ошибка при сохранении фото. Проверьте формат файла.', 'danger')

        try:
            db.session.commit()
            flash_i18n('Профиль обновлен.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating admin profile: {e}")
            flash_i18n('Ошибка при сохранении профиля. Попробуйте снова.', 'danger')
            return render_template('admin/profile.html', form=form)

        return redirect(url_for('admin.profile'))

    return render_template('admin/profile.html', form=form)

@admin.route('/notifications')
@login_required
@superadmin_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifs = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )

    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()

    return render_template('admin/notifications.html', notifications=notifs)