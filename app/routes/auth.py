from urllib.parse import urlparse

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Clinic
from app.forms import LoginForm, PatientRegistrationForm
from app.i18n import t


def _is_safe_url(target):
    """Ensure redirect target is a relative path on the same host."""
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.scheme == '' and parsed.netloc == ''

auth_bp = Blueprint('auth', __name__)

ROLE_REDIRECTS = {
    'superadmin': 'admin.dashboard',
    'clinic_admin': 'clinic.dashboard',
    'doctor': 'doctor.dashboard',
    'patient': 'patient.index',
}


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    force_auth_page = request.args.get('force_auth') == '1' or request.args.get('force_login') == '1'
    if current_user.is_authenticated and not force_auth_page:
        return redirect(url_for(ROLE_REDIRECTS.get(current_user.role, 'auth.login')))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user is None or not user.check_password(form.password.data):
            flash(t('auth.invalid_credentials', session.get('language', 'ru'), 'Неверный email или пароль.'), 'danger')
            return render_template('auth/login.html', form=form)

        if not user.is_active:
            flash('Ваш аккаунт деактивирован. Обратитесь к администратору.', 'warning')
            return render_template('auth/login.html', form=form)

        selected_language = session.get('language')
        if selected_language and user.language != selected_language:
            user.language = selected_language
            db.session.commit()

        login_user(user, remember=True)
        welcome_text = t('auth.welcome_user', session.get('language', 'ru'), 'Добро пожаловать, %(name)s!')
        flash(welcome_text % {'name': user.first_name}, 'success')

        next_page = request.args.get('next')
        if next_page and _is_safe_url(next_page):
            return redirect(next_page)

        return redirect(url_for(ROLE_REDIRECTS.get(user.role, 'auth.login')))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    force_auth_page = request.args.get('force_auth') == '1'
    if current_user.is_authenticated and not force_auth_page:
        return redirect(url_for(ROLE_REDIRECTS.get(current_user.role, 'auth.login')))

    form = PatientRegistrationForm()
    clinics = Clinic.query.filter_by(is_active=True).order_by(Clinic.name).all()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing_user:
            flash('Пользователь с таким email уже зарегистрирован.', 'danger')
            return render_template('auth/register.html', form=form, clinics=clinics)

        clinic_id = request.form.get('clinic_id', type=int)
        if clinic_id:
            clinic = db.session.get(Clinic, clinic_id)
            if not clinic or not clinic.is_active:
                flash('Выбранная клиника недоступна.', 'danger')
                return render_template('auth/register.html', form=form, clinics=clinics)

        user = User(
            email=form.email.data.lower().strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            birth_date=form.birth_date.data,
            gender=form.gender.data if form.gender.data else None,
            role='patient',
            clinic_id=clinic_id,
            language=session.get('language', 'ru'),
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Регистрация прошла успешно! Войдите в систему.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, clinics=clinics)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash(t('auth.logged_out', session.get('language', 'ru'), 'Вы вышли из системы.'), 'success')
    return redirect(url_for('auth.login'))
