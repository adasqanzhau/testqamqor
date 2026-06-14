import json
import os
import re

from flask import flash as flask_flash, session

def get_translations(language='ru'):
    """Load translations for the given language."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    trans_file = os.path.join(base_path, 'translations', f'{language}.json')
    
    if not os.path.exists(trans_file):
        # Fallback to Russian if language file doesn't exist
        trans_file = os.path.join(base_path, 'translations', 'ru.json')
    
    try:
        with open(trans_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def t(key, language='ru', default=''):
    """
    Get translation by key.
    Usage: t('common.language', 'ru') or t('nav.dashboard', current_language)
    """
    translations = get_translations(language)

    def resolve(candidate_key):
        value = translations
        for part in candidate_key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value

    value = resolve(key)
    if value is not None:
        return value

    if key.startswith('admin.'):
        value = resolve('patient.admin.' + key[len('admin.'):])
        if value is not None:
            return value

    if key.startswith('doctor.'):
        value = resolve('patient.doctor.' + key[len('doctor.'):])
        if value is not None:
            return value

    if key.startswith('clinic.'):
        value = resolve('patient.clinic.' + key[len('clinic.'):])
        if value is not None:
            return value

    if key.startswith('patient.'):
        value = resolve(key[len('patient.'):])
        if value is not None:
            return value

    return default


SOURCE_TEXT_TRANSLATIONS = {
    'Панель управления': {'ru': 'Панель управления', 'kz': 'Басқару панелі', 'en': 'Dashboard'},
    'Клиники': {'ru': 'Клиники', 'kz': 'Клиникалар', 'en': 'Clinics'},
    'Пользователи': {'ru': 'Пользователи', 'kz': 'Пайдаланушылар', 'en': 'Users'},
    'Аналитика': {'ru': 'Аналитика', 'kz': 'Аналитика', 'en': 'Analytics'},
    'Врачи': {'ru': 'Врачи', 'kz': 'Дәрігерлер', 'en': 'Doctors'},
    'Пациенты': {'ru': 'Пациенты', 'kz': 'Пациенттер', 'en': 'Patients'},
    'Записи': {'ru': 'Записи', 'kz': 'Тіркелулер', 'en': 'Appointments'},
    'Настройки': {'ru': 'Настройки', 'kz': 'Параметрлер', 'en': 'Settings'},
    'Расписание': {'ru': 'Расписание', 'kz': 'Кесте', 'en': 'Schedule'},
    'Отзывы': {'ru': 'Отзывы', 'kz': 'Пікірлер', 'en': 'Reviews'},
    'Профиль': {'ru': 'Профиль', 'kz': 'Профиль', 'en': 'Profile'},
    'Войти': {'ru': 'Войти', 'kz': 'Кіру', 'en': 'Login'},
    'Регистрация': {'ru': 'Регистрация', 'kz': 'Тіркелу', 'en': 'Register'},
    'Зарегистрироваться': {'ru': 'Зарегистрироваться', 'kz': 'Тіркелу', 'en': 'Sign up'},
    'Выход': {'ru': 'Выход', 'kz': 'Шығу', 'en': 'Logout'},
    'Уведомления': {'ru': 'Уведомления', 'kz': 'Хабарламалар', 'en': 'Notifications'},
    'Все уведомления': {'ru': 'Все уведомления', 'kz': 'Барлық хабарламалар', 'en': 'All notifications'},
    'Прочитать все': {'ru': 'Прочитать все', 'kz': 'Барлығын оқу', 'en': 'Mark all read'},
    'Нет новых уведомлений': {'ru': 'Нет новых уведомлений', 'kz': 'Жаңа хабарламалар жоқ', 'en': 'No new notifications'},
    'Мои записи': {'ru': 'Мои записи', 'kz': 'Менің тіркелулерім', 'en': 'My appointments'},
    'Мед. карта': {'ru': 'Мед. карта', 'kz': 'Мед. карта', 'en': 'Medical record'},
    'AI Ассистент': {'ru': 'AI Ассистент', 'kz': 'AI Көмекші', 'en': 'AI Assistant'},
    'Сохранить': {'ru': 'Сохранить', 'kz': 'Сақтау', 'en': 'Save'},
    'Отмена': {'ru': 'Отмена', 'kz': 'Бас тарту', 'en': 'Cancel'},
    'Удалить': {'ru': 'Удалить', 'kz': 'Өшіру', 'en': 'Delete'},
    'Редактировать': {'ru': 'Редактировать', 'kz': 'Өңдеу', 'en': 'Edit'},
    'Добавить': {'ru': 'Добавить', 'kz': 'Қосу', 'en': 'Add'},
    'Назад': {'ru': 'Назад', 'kz': 'Артқа', 'en': 'Back'},
    'Далее': {'ru': 'Далее', 'kz': 'Келесі', 'en': 'Next'},
    'Отправить': {'ru': 'Отправить', 'kz': 'Жіберу', 'en': 'Submit'},
    'Поиск': {'ru': 'Поиск', 'kz': 'Іздеу', 'en': 'Search'},
    'Запомнить меня': {'ru': 'Запомнить меня', 'kz': 'Мені есте сақтау', 'en': 'Remember me'},
    'Забыли пароль?': {'ru': 'Забыли пароль?', 'kz': 'Құпия сөзді ұмыттыңыз ба?', 'en': 'Forgot password?'},
    'Нет аккаунта?': {'ru': 'Нет аккаунта?', 'kz': 'Аккаунтыңыз жоқ па?', 'en': "Don't have an account?"},
    'Уже есть аккаунт?': {'ru': 'Уже есть аккаунт?', 'kz': 'Аккаунтыңыз бар ма?', 'en': 'Already have an account?'},
    'Email': {'ru': 'Email', 'kz': 'Email', 'en': 'Email'},
    'Пароль': {'ru': 'Пароль', 'kz': 'Құпия сөз', 'en': 'Password'},
    'Подтвердить пароль': {'ru': 'Подтвердить пароль', 'kz': 'Құпия сөзді растау', 'en': 'Confirm password'},
    'Телефон': {'ru': 'Телефон', 'kz': 'Телефон', 'en': 'Phone'},
    'Имя': {'ru': 'Имя', 'kz': 'Аты', 'en': 'First name'},
    'Фамилия': {'ru': 'Фамилия', 'kz': 'Тегі', 'en': 'Last name'},
    'Дата рождения': {'ru': 'Дата рождения', 'kz': 'Туған күні', 'en': 'Date of birth'},
    'Пол': {'ru': 'Пол', 'kz': 'Жыныс', 'en': 'Gender'},
    'Адрес': {'ru': 'Адрес', 'kz': 'Мекенжай', 'en': 'Address'},
    'Специализация': {'ru': 'Специализация', 'kz': 'Мамандану', 'en': 'Specialization'},
    'Опыт': {'ru': 'Опыт', 'kz': 'Тәжірибе', 'en': 'Experience'},
    'Клиника': {'ru': 'Клиника', 'kz': 'Клиника', 'en': 'Clinic'},
    'Удаление': {'ru': 'Удаление', 'kz': 'Жою', 'en': 'Delete'},
    'Закрыть': {'ru': 'Закрыть', 'kz': 'Жабу', 'en': 'Close'},
    'Выберите': {'ru': 'Выберите', 'kz': 'Таңдаңыз', 'en': 'Choose'},
    'Выберите клинику': {'ru': 'Выберите клинику', 'kz': 'Клиниканы таңдаңыз', 'en': 'Choose clinic'},
    'Имя': {'ru': 'Имя', 'kz': 'Аты', 'en': 'First name'},
    'Фамилия': {'ru': 'Фамилия', 'kz': 'Тегі', 'en': 'Last name'},
    'Телефон': {'ru': 'Телефон', 'kz': 'Телефон', 'en': 'Phone'},
    'Дата рождения': {'ru': 'Дата рождения', 'kz': 'Туған күні', 'en': 'Date of birth'},
    'Пол': {'ru': 'Пол', 'kz': 'Жыныс', 'en': 'Gender'},
    'Главная': {'ru': 'Главная', 'kz': 'Басты бет', 'en': 'Home'},
    'В кабинет': {'ru': 'В кабинет', 'kz': 'Кабинетке', 'en': 'Dashboard'},
    'Телемедицина Казахстана': {'ru': 'Телемедицина Казахстана', 'kz': 'Қазақстан телемедицинасы', 'en': 'Telemedicine of Kazakhstan'},
    'Возможности': {'ru': 'Возможности', 'kz': 'Мүмкіндіктер', 'en': 'Features'},
    'Как это работает': {'ru': 'Как это работает', 'kz': 'Бұл қалай жұмыс істейді', 'en': 'How it works'},
    'Для клиник': {'ru': 'Для клиник', 'kz': 'Клиникалар үшін', 'en': 'For clinics'},
    'Современная': {'ru': 'Современная', 'kz': 'Заманауи', 'en': 'Modern'},
    'телемедицина': {'ru': 'телемедицина', 'kz': 'телемедицина', 'en': 'telemedicine'},
    'Казахстана': {'ru': 'Казахстана', 'kz': 'Қазақстанның', 'en': 'of Kazakhstan'},
    'Консультации с лучшими врачами онлайн, запись на прием, электронные рецепты и AI-помощник — все в одной платформе.': {
        'ru': 'Консультации с лучшими врачами онлайн, запись на прием, электронные рецепты и AI-помощник — все в одной платформе.',
        'kz': 'Үздік дәрігерлерден онлайн кеңес, қабылдауға жазылу, электронды рецепттер және AI-көмекші — барлығы бір платформада.',
        'en': 'Online consultations with top doctors, appointments, electronic prescriptions and an AI assistant - all in one platform.'
    },
    'Ваше здоровье онлайн': {'ru': 'Ваше здоровье онлайн', 'kz': 'Сіздің денсаулығыңыз онлайн', 'en': 'Your health online'},
    'Видеоконсультации 24/7': {'ru': 'Видеоконсультации 24/7', 'kz': '24/7 бейне кеңестер', 'en': 'Video consultations 24/7'},
    'AI-чатбот для первичной помощи': {'ru': 'AI-чатбот для первичной помощи', 'kz': 'Алғашқы көмекке арналған AI чатбот', 'en': 'AI chatbot for first aid'},
    'Электронные рецепты': {'ru': 'Электронные рецепты', 'kz': 'Электронды рецепттер', 'en': 'Electronic prescriptions'},
    'Медицинская карта онлайн': {'ru': 'Медицинская карта онлайн', 'kz': 'Онлайн медициналық карта', 'en': 'Online medical record'},
    'Все для вашего здоровья': {'ru': 'Все для вашего здоровья', 'kz': 'Денсаулығыңыз үшін бәрі', 'en': 'Everything for your health'},
    'Начните заботиться о здоровье за три простых шага.': {'ru': 'Начните заботиться о здоровье за три простых шага.', 'kz': 'Денсаулыққа үш қарапайым қадаммен қамқорлық жасауды бастаңыз.', 'en': 'Start caring for your health in three simple steps.'},
    'Qamqor объединяет передовые технологии и квалифицированных врачей для заботы о вашем здоровье.': {
        'ru': 'Qamqor объединяет передовые технологии и квалифицированных врачей для заботы о вашем здоровье.',
        'kz': 'Qamqor озық технологиялар мен білікті дәрігерлерді денсаулығыңыз үшін біріктіреді.',
        'en': 'Qamqor combines advanced technology and qualified doctors to care for your health.'
    },
    'Общайтесь с врачом лицом к лицу через защищенный видеочат. Без очередей и поездок в клинику.': {
        'ru': 'Общайтесь с врачом лицом к лицу через защищенный видеочат. Без очередей и поездок в клинику.',
        'kz': 'Дәрігермен қорғалған бейнечат арқылы бетпе-бет сөйлесіңіз. Кезек те, емханаға бару да жоқ.',
        'en': 'Talk to a doctor face to face through a secure video chat. No queues or trips to the clinic.'
    },
    'Интеллектуальный помощник проведет первичный опрос симптомов и поможет определить нужного специалиста.': {
        'ru': 'Интеллектуальный помощник проведет первичный опрос симптомов и поможет определить нужного специалиста.',
        'kz': 'Ақылды көмекші симптомдар бойынша алғашқы сауалнама жүргізіп, қажетті маманды анықтауға көмектеседі.',
        'en': 'An intelligent assistant will conduct an initial symptom assessment and help identify the right specialist.'
    },
    'Получайте рецепты от врачей в электронном формате. Быстро и удобно — прямо в вашем личном кабинете.': {
        'ru': 'Получайте рецепты от врачей в электронном формате. Быстро и удобно — прямо в вашем личном кабинете.',
        'kz': 'Дәрігерлерден рецепттерді электронды түрде алыңыз. Жылдам әрі ыңғайлы — тікелей жеке кабинетіңізде.',
        'en': 'Receive prescriptions from doctors in electronic form. Fast and convenient - right in your personal account.'
    },
    'Записывайтесь к врачу онлайн в удобное время. Выбирайте специалиста и клинику за пару кликов.': {
        'ru': 'Записывайтесь к врачу онлайн в удобное время. Выбирайте специалиста и клинику за пару кликов.',
        'kz': 'Өзіңізге ыңғайлы уақытта дәрігерге онлайн жазылыңыз. Маманды және клиниканы бірнеше басумен таңдаңыз.',
        'en': 'Book a doctor online at a convenient time. Choose a specialist and clinic in a few clicks.'
    },
    'Оценивайте приёмы и читайте отзывы других пациентов — выбирайте лучших специалистов.': {
        'ru': 'Оценивайте приёмы и читайте отзывы других пациентов — выбирайте лучших специалистов.',
        'kz': 'Қабылдауларды бағалап, басқа пациенттердің пікірлерін оқыңыз — ең жақсы мамандарды таңдаңыз.',
        'en': 'Rate appointments and read other patients reviews - choose the best specialists.'
    },
    'Вся история обращений, диагнозы и результаты анализов — в одном защищенном месте с доступом 24/7.': {
        'ru': 'Вся история обращений, диагнозы и результаты анализов — в одном защищенном месте с доступом 24/7.',
        'kz': 'Жүгінулер тарихы, диагноздар және талдау нәтижелері — 24/7 қолжетімді бір қорғалған жерде.',
        'en': 'All visit history, diagnoses and test results in one secure place with 24/7 access.'
    },
    'Создайте аккаунт за минуту, заполнив основные данные и выбрав клинику.': {
        'ru': 'Создайте аккаунт за минуту, заполнив основные данные и выбрав клинику.',
        'kz': 'Негізгі деректерді толтырып, клиниканы таңдау арқылы бір минутта аккаунт жасаңыз.',
        'en': 'Create an account in a minute by filling in the basics and choosing a clinic.'
    },
    'Найдите подходящего специалиста или задайте вопрос AI-помощнику для рекомендации.': {
        'ru': 'Найдите подходящего специалиста или задайте вопрос AI-помощнику для рекомендации.',
        'kz': 'Қажетті маманды табыңыз немесе ұсыныс алу үшін AI-көмекшіге сұрақ қойыңыз.',
        'en': 'Find the right specialist or ask the AI assistant for a recommendation.'
    },
    'Проведите видеоконсультацию, получите рецепт и рекомендации — не выходя из дома.': {
        'ru': 'Проведите видеоконсультацию, получите рецепт и рекомендации — не выходя из дома.',
        'kz': 'Бейне кеңес өткізіп, рецепт пен ұсыныстарды үйден шықпай алыңыз.',
        'en': 'Have a video consultation, get a prescription and recommendations - without leaving home.'
    },
    'Онлайн-расписание и управление записями пациентов': {'ru': 'Онлайн-расписание и управление записями пациентов', 'kz': 'Онлайн-кесте және пациент жазбаларын басқару', 'en': 'Online schedule and patient appointment management'},
    'Встроенная видеосвязь для телеконсультаций': {'ru': 'Встроенная видеосвязь для телеконсультаций', 'kz': 'Телеконсультацияға арналған кіріктірілген бейнебайланыс', 'en': 'Built-in video calls for teleconsultations'},
    'Электронный документооборот и рецепты': {'ru': 'Электронный документооборот и рецепты', 'kz': 'Электронды құжат айналымы және рецепттер', 'en': 'Electronic document flow and prescriptions'},
    'Аналитика и отчеты для руководства': {'ru': 'Аналитика и отчеты для руководства', 'kz': 'Басшылыққа арналған аналитика мен есептер', 'en': 'Analytics and reports for management'},
    'Техническая поддержка и обучение персонала': {'ru': 'Техническая поддержка и обучение персонала', 'kz': 'Техникалық қолдау және қызметкерлерді оқыту', 'en': 'Technical support and staff training'},
    'Начните заботиться о здоровье за три простых шага.': {'ru': 'Начните заботиться о здоровье за три простых шага.', 'kz': 'Денсаулыққа үш қарапайым қадаммен қамқорлық жасауды бастаңыз.', 'en': 'Start caring for your health in three simple steps.'},
    'Все права защищены.': {'ru': 'Все права защищены.', 'kz': 'Барлық құқықтар қорғалған.', 'en': 'All rights reserved.'},
    'Пациентов': {'ru': 'Пациентов', 'kz': 'Пациент', 'en': 'Patients'},
    'Врачей': {'ru': 'Врачей', 'kz': 'Дәрігер', 'en': 'Doctors'},
    'Клиник': {'ru': 'Клиник', 'kz': 'Клиника', 'en': 'Clinics'},
    'Поддержка': {'ru': 'Поддержка', 'kz': 'Қолдау', 'en': 'Support'},
    'Подключите вашу клинику': {'ru': 'Подключите вашу клинику', 'kz': 'Клиникаңызды қосыңыз', 'en': 'Connect your clinic'},
    'Присоединяйтесь к Qamqor': {'ru': 'Присоединяйтесь к Qamqor', 'kz': 'Qamqor-ға қосылыңыз', 'en': 'Join Qamqor'},
    'Платформа': {'ru': 'Платформа', 'kz': 'Платформа', 'en': 'Platform'},
    'Поддержка': {'ru': 'Поддержка', 'kz': 'Қолдау', 'en': 'Support'},
    'Контакты': {'ru': 'Контакты', 'kz': 'Байланыс', 'en': 'Contacts'},
    'Помощь': {'ru': 'Помощь', 'kz': 'Көмек', 'en': 'Help'},
    'FAQ': {'ru': 'FAQ', 'kz': 'FAQ', 'en': 'FAQ'},
    'Ваше здоровье онлайн': {'ru': 'Ваше здоровье онлайн', 'kz': 'Сіздің денсаулығыңыз онлайн', 'en': 'Your health online'},
    'Зарегистрируйтесь': {'ru': 'Зарегистрируйтесь', 'kz': 'Тіркеліңіз', 'en': 'Register now'},
    'Выберите врача': {'ru': 'Выберите врача', 'kz': 'Дәрігерді таңдаңыз', 'en': 'Choose a doctor'},
    'Получите помощь': {'ru': 'Получите помощь', 'kz': 'Көмек алыңыз', 'en': 'Get help'},
    'Все для вашего здоровья': {'ru': 'Все для вашего здоровья', 'kz': 'Денсаулығыңыз үшін бәрі', 'en': 'Everything for your health'},
    'Современная телемедицинская платформа для пациентов и клиник Казахстана.': {
        'ru': 'Современная телемедицинская платформа для пациентов и клиник Казахстана.',
        'kz': 'Қазақстандағы пациенттер мен клиникаларға арналған заманауи телемедициналық платформа.',
        'en': 'A modern telemedicine platform for patients and clinics in Kazakhstan.'
    },
    'Связаться с нами': {'ru': 'Связаться с нами', 'kz': 'Бізбен байланысу', 'en': 'Contact us'},
    'Платформа': {'ru': 'Платформа', 'kz': 'Платформа', 'en': 'Platform'},
    'Qamqor помогает клиникам расширить охват пациентов и оптимизировать рабочие процессы с помощью современных цифровых инструментов.': {
        'ru': 'Qamqor помогает клиникам расширить охват пациентов и оптимизировать рабочие процессы с помощью современных цифровых инструментов.',
        'kz': 'Qamqor клиникаларға пациенттер ауқымын кеңейтуге және заманауи цифрлық құралдардың көмегімен жұмыс үдерістерін оңтайландыруға көмектеседі.',
        'en': 'Qamqor helps clinics expand patient reach and optimize workflows with modern digital tools.'
    },
    'Зарегистрируйте вашу клинику и получите доступ ко всем инструментам телемедицинской платформы. Мы поможем с настройкой и интеграцией.': {
        'ru': 'Зарегистрируйте вашу клинику и получите доступ ко всем инструментам телемедицинской платформы. Мы поможем с настройкой и интеграцией.',
        'kz': 'Клиникаңызды тіркеп, телемедициналық платформаның барлық құралдарына қол жеткізіңіз. Орнату мен интеграцияға көмектесеміз.',
        'en': 'Register your clinic and get access to all telemedicine platform tools. We will help with setup and integration.'
    },
    'Современная телемедицинская платформа для пациентов и клиник Казахстана.': {'ru': 'Современная телемедицинская платформа для пациентов и клиник Казахстана.', 'kz': 'Қазақстандағы пациенттер мен клиникаларға арналған заманауи телемедициналық платформа.', 'en': 'A modern telemedicine platform for patients and clinics in Kazakhstan.'},
    'Платформа': {'ru': 'Платформа', 'kz': 'Платформа', 'en': 'Platform'},
    'Современная телемедицинская платформа для пациентов и клиник Казахстана.': {'ru': 'Современная телемедицинская платформа для пациентов и клиник Казахстана.', 'kz': 'Қазақстандағы пациенттер мен клиникаларға арналған заманауи телемедициналық платформа.', 'en': 'A modern telemedicine platform for patients and clinics in Kazakhstan.'},
    'Вы уверены? Это действие нельзя отменить.': {
        'ru': 'Вы уверены? Это действие нельзя отменить.',
        'kz': 'Сіз сенімдісіз бе? Бұл әрекетті қайтару мүмкін емес.',
        'en': 'Are you sure? This action cannot be undone.'
    },
    'Политика конфиденциальности': {'ru': 'Политика конфиденциальности', 'kz': 'Құпиялылық саясаты', 'en': 'Privacy policy'},
    'Условия использования': {'ru': 'Условия использования', 'kz': 'Пайдалану шарттары', 'en': 'Terms of use'},
}


def get_dom_translations(language='ru'):
    return {
        source: translations.get(language, translations['ru'])
        for source, translations in SOURCE_TEXT_TRANSLATIONS.items()
    }


FLASH_TRANSLATIONS = {
    'Укажите email и пароль администратора клиники.': {
        'ru': 'Укажите email и пароль администратора клиники.',
        'kz': 'Клиника әкімшісінің email мен құпия сөзін көрсетіңіз.',
        'en': "Specify the clinic administrator's email and password.",
    },
    'Пользователь с таким email уже существует.': {
        'ru': 'Пользователь с таким email уже существует.',
        'kz': 'Мұндай email мекенжайы бар пайдаланушы бұрыннан бар.',
        'en': 'A user with this email already exists.',
    },
    'Клиника "%(name)s" успешно создана.': {
        'ru': 'Клиника "%(name)s" успешно создана.',
        'kz': '"%(name)s" клиникасы сәтті құрылды.',
        'en': 'Clinic "%(name)s" was created successfully.',
    },
    'Клиника "%(name)s" обновлена.': {
        'ru': 'Клиника "%(name)s" обновлена.',
        'kz': '"%(name)s" клиникасы жаңартылды.',
        'en': 'Clinic "%(name)s" has been updated.',
    },
    'Не удалось обновить клинику: %(exc)s': {
        'ru': 'Не удалось обновить клинику: %(exc)s',
        'kz': 'Клиниканы жаңарту мүмкін болмады: %(exc)s',
        'en': 'Failed to update clinic: %(exc)s',
    },
    'Клиника "%(name)s" удалена.': {
        'ru': 'Клиника "%(name)s" удалена.',
        'kz': '"%(name)s" клиникасы жойылды.',
        'en': 'Clinic "%(name)s" has been deleted.',
    },
    'Не удалось удалить клинику: %(exc)s': {
        'ru': 'Не удалось удалить клинику: %(exc)s',
        'kz': 'Клиниканы жою мүмкін болмады: %(exc)s',
        'en': 'Failed to delete clinic: %(exc)s',
    },
    'Клиника "%(name)s" активирована.': {
        'ru': 'Клиника "%(name)s" активирована.',
        'kz': '"%(name)s" клиникасы белсендірілді.',
        'en': 'Clinic "%(name)s" has been activated.',
    },
    'Клиника "%(name)s" деактивирована.': {
        'ru': 'Клиника "%(name)s" деактивирована.',
        'kz': '"%(name)s" клиникасы өшірілді.',
        'en': 'Clinic "%(name)s" has been deactivated.',
    },
    'Нельзя изменить статус суперадмина.': {
        'ru': 'Нельзя изменить статус суперадмина.',
        'kz': 'Суперадминнің статусын өзгертуге болмайды.',
        'en': 'Cannot change the superadmin status.',
    },
    'Пользователь "%(name)s" активирован.': {
        'ru': 'Пользователь "%(name)s" активирован.',
        'kz': '"%(name)s" пайдаланушысы белсендірілді.',
        'en': 'User "%(name)s" has been activated.',
    },
    'Пользователь "%(name)s" деактивирован.': {
        'ru': 'Пользователь "%(name)s" деактивирован.',
        'kz': '"%(name)s" пайдаланушысы өшірілді.',
        'en': 'User "%(name)s" has been deactivated.',
    },
    'Нельзя удалить суперадмина.': {
        'ru': 'Нельзя удалить суперадмина.',
        'kz': 'Суперадминді жоюға болмайды.',
        'en': 'Cannot delete the superadmin.',
    },
    'Пользователь "%(name)s" удалён.': {
        'ru': 'Пользователь "%(name)s" удалён.',
        'kz': '"%(name)s" пайдаланушысы жойылды.',
        'en': 'User "%(name)s" has been deleted.',
    },
    'Не удалось удалить пользователя: %(exc)s': {
        'ru': 'Не удалось удалить пользователя: %(exc)s',
        'kz': 'Пайдаланушыны жою мүмкін болмады: %(exc)s',
        'en': 'Failed to delete user: %(exc)s',
    },
    'Ошибка при сохранении фото. Проверьте формат файла.': {
        'ru': 'Ошибка при сохранении фото. Проверьте формат файла.',
        'kz': 'Фотоны сақтау қатесі. Файл пішімін тексеріңіз.',
        'en': 'Error saving photo. Check the file format.',
    },
    'Профиль обновлен.': {
        'ru': 'Профиль обновлен.',
        'kz': 'Профиль жаңартылды.',
        'en': 'Profile updated.',
    },
    'Ошибка при сохранении профиля. Попробуйте снова.': {
        'ru': 'Ошибка при сохранении профиля. Попробуйте снова.',
        'kz': 'Профильді сақтау қатесі. Қайта көріңіз.',
        'en': 'Error saving profile. Please try again.',
    },
    'Врач успешно добавлен.': {
        'ru': 'Врач успешно добавлен.',
        'kz': 'Дәрігер сәтті қосылды.',
        'en': 'Doctor added successfully.',
    },
    'Ошибка при добавлении врача. Попробуйте снова.': {
        'ru': 'Ошибка при добавлении врача. Попробуйте снова.',
        'kz': 'Дәрігерді қосу қатесі. Қайта көріңіз.',
        'en': 'Error adding doctor. Please try again.',
    },
    'Данные врача обновлены.': {
        'ru': 'Данные врача обновлены.',
        'kz': 'Дәрігер деректері жаңартылды.',
        'en': 'Doctor data updated.',
    },
    'Ошибка при обновлении врача. Попробуйте снова.': {
        'ru': 'Ошибка при обновлении врача. Попробуйте снова.',
        'kz': 'Дәрігерді жаңарту қатесі. Қайта көріңіз.',
        'en': 'Error updating doctor. Please try again.',
    },
    'Врач удалён.': {
        'ru': 'Врач удалён.',
        'kz': 'Дәрігер жойылды.',
        'en': 'Doctor deleted.',
    },
    'Настройки клиники обновлены.': {
        'ru': 'Настройки клиники обновлены.',
        'kz': 'Клиника баптаулары жаңартылды.',
        'en': 'Clinic settings updated.',
    },
    'Не удалось обновить настройки: %(exc)s': {
        'ru': 'Не удалось обновить настройки: %(exc)s',
        'kz': 'Баптауларды жаңарту мүмкін болмады: %(exc)s',
        'en': 'Failed to update settings: %(exc)s',
    },
    'Профиль обновлён.': {
        'ru': 'Профиль обновлён.',
        'kz': 'Профиль жаңартылды.',
        'en': 'Profile updated.',
    },
    'Фото профиля удалено.': {
        'ru': 'Фото профиля удалено.',
        'kz': 'Профиль фотосы өшірілді.',
        'en': 'Profile photo deleted.',
    },
    'Пожалуйста, выберите время приёма.': {
        'ru': 'Пожалуйста, выберите время приёма.',
        'kz': 'Қабылдау уақытын таңдаңыз.',
        'en': 'Please choose an appointment time.',
    },
    'Это время уже занято. Выберите другое.': {
        'ru': 'Это время уже занято. Выберите другое.',
        'kz': 'Бұл уақыт бос емес. Басқасын таңдаңыз.',
        'en': 'This time is already booked. Choose another.',
    },
    'Врач не найден.': {
        'ru': 'Врач не найден.',
        'kz': 'Дәрігер табылмады.',
        'en': 'Doctor not found.',
    },
    'Этот врач не принадлежит вашей клинике.': {
        'ru': 'Этот врач не принадлежит вашей клинике.',
        'kz': 'Бұл дәрігер сіздің клиникаңызға тиесілі емес.',
        'en': 'This doctor does not belong to your clinic.',
    },
    'Вы успешно записались на приём!': {
        'ru': 'Вы успешно записались на приём!',
        'kz': 'Сіз қабылдауға сәтті жазылдыңыз!',
        'en': 'Your appointment has been booked successfully!',
    },
    'Можно отменить только запланированный приём.': {
        'ru': 'Можно отменить только запланированный приём.',
        'kz': 'Тек жоспарланған қабылдауды ғана болдыруға болады.',
        'en': 'Only scheduled appointments can be canceled.',
    },
    'Запись отменена.': {
        'ru': 'Запись отменена.',
        'kz': 'Қабылдау тоқтатылды.',
        'en': 'Appointment canceled.',
    },
    'Допустимы только изображения (jpg, png).': {
        'ru': 'Допустимы только изображения (jpg, png).',
        'kz': 'Тек кескіндерге рұқсат етіледі (jpg, png).',
        'en': 'Only images are allowed (jpg, png).',
    },
    'Профиль успешно обновлён.': {
        'ru': 'Профиль успешно обновлён.',
        'kz': 'Профиль сәтті жаңартылды.',
        'en': 'Profile updated successfully.',
    },
    'Отзыв можно оставить только после завершённого приёма.': {
        'ru': 'Отзыв можно оставить только после завершённого приёма.',
        'kz': 'Пікірді тек аяқталған қабылдаудан кейін ғана қалдыруға болады.',
        'en': 'You can leave a review only after a completed appointment.',
    },
    'Вы уже оставили отзыв на этот приём.': {
        'ru': 'Вы уже оставили отзыв на этот приём.',
        'kz': 'Сіз бұл қабылдауға пікір қалдырғансыз.',
        'en': 'You have already left a review for this appointment.',
    },
    'Спасибо за ваш отзыв!': {
        'ru': 'Спасибо за ваш отзыв!',
        'kz': 'Пікіріңіз үшін рақмет!',
        'en': 'Thank you for your review!',
    },
    'Уведомление отмечено как прочитанное.': {
        'ru': 'Уведомление отмечено как прочитанное.',
        'kz': 'Хабарлама оқылған деп белгіленді.',
        'en': 'Notification marked as read.',
    },
    'Все уведомления отмечены как прочитанные.': {
        'ru': 'Все уведомления отмечены как прочитанные.',
        'kz': 'Барлық хабарламалар оқылған деп белгіленді.',
        'en': 'All notifications marked as read.',
    },
    'Введите описание симптома.': {
        'ru': 'Введите описание симптома.',
        'kz': 'Симптом сипаттамасын енгізіңіз.',
        'en': 'Enter a symptom description.',
    },
    'Симптом записан.': {
        'ru': 'Симптом записан.',
        'kz': 'Симптом жазылды.',
        'en': 'Symptom recorded.',
    },
    'Чат-бот доступен только для пациентов.': {
        'ru': 'Чат-бот доступен только для пациентов.',
        'kz': 'Чат-бот тек пациенттерге қолжетімді.',
        'en': 'Chatbot is available only for patients.',
    },
    'Нельзя начать звонок для завершённого или отменённого приёма.': {
        'ru': 'Нельзя начать звонок для завершённого или отменённого приёма.',
        'kz': 'Аяқталған немесе тоқтатылған қабылдау үшін қоңырау бастауға болмайды.',
        'en': 'Cannot start a call for a completed or canceled appointment.',
    },
    'Видеозвонок завершён.': {
        'ru': 'Видеозвонок завершён.',
        'kz': 'Бейнеқоңырау аяқталды.',
        'en': 'Video call ended.',
    },
    'Ошибка при сохранении фото. Проверьте формат файла (jpg, png, heic).': {
        'ru': 'Ошибка при сохранении фото. Проверьте формат файла (jpg, png, heic).',
        'kz': 'Фотоны сақтау қатесі. Файл пішімін тексеріңіз (jpg, png, heic).',
        'en': 'Error saving photo. Check the file format (jpg, png, heic).',
    },
}


def translate_flash_text(message, target_language='ru'):
    if not message or not isinstance(message, str):
        return message
    translations = FLASH_TRANSLATIONS.get(message)
    if isinstance(translations, dict):
        return translations.get(target_language) or translations.get('ru') or message
    return message


def flash_message(message, category='message', language=None, **params):
    lang = language or session.get('language', 'ru')
    translated = translate_flash_text(message, lang)
    if params:
        translated = translated % params
    flask_flash(translated, category)
    return translated


_CYRILLIC_RE = re.compile(r'[А-Яа-яЁё]')


def _looks_cyrillic(text):
    return bool(text and _CYRILLIC_RE.search(text))


_LEGACY_NOTIFICATION_TITLES = {
    'en': {
        'Completed': 'videocall.consultation_completed',
    },
    'kz': {
        'Аяқталды': 'videocall.consultation_completed',
    },
}

_LEGACY_NOTIFICATION_MESSAGE_PATTERNS = {
    'en': (
        (re.compile(r'^with doctor (.+)$'), 'videocall.consultation_with_doctor'),
        (re.compile(r'^with patient (.+)$'), 'videocall.consultation_with_patient'),
    ),
}


def resolve_notification_field(notification, field, language='ru'):
    """Return a localized notification title or message for the given language."""
    payload = None
    try:
        payload = getattr(notification, f'{field}_i18n', None)
    except Exception:
        payload = None

    if isinstance(payload, dict):
        if language in payload and payload[language]:
            text = payload[language]
            if field == 'title':
                legacy_key = _LEGACY_NOTIFICATION_TITLES.get(language, {}).get(text.strip())
                if legacy_key:
                    return t(legacy_key, language, text)
            if field == 'message':
                for pattern, legacy_key in _LEGACY_NOTIFICATION_MESSAGE_PATTERNS.get(language, ()):
                    m = pattern.match(text.strip())
                    if m:
                        return t(legacy_key, language, text) % {'name': m.group(1)}
            if language != 'ru' and _looks_cyrillic(text):
                translated = translate_text_from_ru(text, language)
                if translated != text:
                    return translated
            return text
        for fav in ('ru', 'en', 'kz'):
            if fav in payload and payload[fav]:
                text = payload[fav]
                if language == fav:
                    return text
                return translate_text_from_ru(text, language)

    try:
        orig = getattr(notification, field, '')
    except Exception:
        orig = ''
    if language == 'ru':
        return orig
    return translate_text_from_ru(orig, language)


def translate_text_from_ru(value, target_language='ru'):
    """
    Try to translate an arbitrary text that was stored in Russian by finding
    a matching value in the Russian translations and returning the equivalent
    string in `target_language`. If not found, return the original value.
    This is a best-effort helper for legacy notifications stored as Russian
    sentences.
    """
    if not value or not isinstance(value, str):
        return value

    # Load Russian translations
    ru = get_translations('ru') or {}

    # Walk ru dict to find a key whose value equals `value`.
    # If found, use t(key, target_language) to get translated variant.
    def walk(d, path=''):
        if isinstance(d, dict):
            for k, v in d.items():
                new_path = f"{path}.{k}" if path else k
                if isinstance(v, dict):
                    res = walk(v, new_path)
                    if res:
                        return res
                else:
                    # Normalize and compare
                    if isinstance(v, str) and v.strip() == value.strip():
                        return new_path
        return None

    key = walk(ru)
    if key:
        # Use t to fetch in target language; fall back to original value
        return t(key, target_language, value)

    # Best-effort translation for legacy dynamic medical-record texts with
    # dates/names where exact key lookup is impossible.
    if target_language in ('en', 'kz'):
        line_prefixes = {
            'en': {
                'Заключение врача — приём ': "Doctor's conclusion — appointment ",
                'Видеоконсультация — ': 'Video consultation — ',
                'Диагноз:': 'Diagnosis:',
                'Рекомендации:': 'Recommendations:',
            },
            'kz': {
                'Заключение врача — приём ': 'Дәрігер қорытындысы — қабылдау ',
                'Видеоконсультация — ': 'Бейнеконсультация — ',
                'Диагноз:': 'Диагноз:',
                'Рекомендации:': 'Ұсыныстар:',
            },
        }

        sentence_patterns = [
            (
                re.compile(
                    r'^Видеоконсультация между врачом\s+(.+?)\s+и пациентом\s+(.+?)\s+состоялась\s+(.+?)\.\s+Подробная транскрипция недоступна\.$'
                ),
                {
                    'en': 'Video consultation between doctor {0} and patient {1} took place on {2}. Detailed transcript is unavailable.',
                    'kz': 'Дәрігер {0} мен пациент {1} арасындағы бейнеконсультация {2} күні өтті. Толық транскрипция қолжетімсіз.',
                },
            ),
            (
                re.compile(r'^Транскрипция видеоконсультации с доктором (.+?) сохранена\.$'),
                {
                    'en': 'Video consultation transcription with doctor {0} has been saved.',
                    'kz': 'Дәрігер {0}-мен бейнеконсультация транскрипциясы сақталды.',
                },
            ),
            (
                re.compile(r'^Транскрипция видеоконсультации с пациентом (.+?) сохранена\.$'),
                {
                    'en': 'Video consultation transcription with patient {0} has been saved.',
                    'kz': 'Пациент {0}-пен бейнеконсультация транскрипциясы сақталды.',
                },
            ),
            (
                re.compile(r'^Видеоконсультация с доктором (.+?) завершена\.$'),
                {
                    'en': 'Video consultation with doctor {0} has been completed.',
                    'kz': 'Дәрігер {0}-мен бейнеконсультация аяқталды.',
                },
            ),
            (
                re.compile(r'^Видеоконсультация с доктором (.+)$'),
                {
                    'en': 'Video consultation with doctor {0}',
                    'kz': 'Дәрігер {0}-пен бейнеконсультация',
                },
            ),
            (
                re.compile(r'^Видеоконсультация с пациентом (.+)$'),
                {
                    'en': 'Video consultation with patient {0}',
                    'kz': 'Пациент {0}-пен бейнеконсультация',
                },
            ),
            (
                re.compile(r'^Пациент (.+?) записался на (.+)$'),
                {
                    'en': 'Patient {0} booked an appointment for {1}',
                    'kz': 'Пациент {0} {1} уақытына жазылды',
                },
            ),
            (
                re.compile(r'^Пациент (.+?) оставил отзыв \((\d+)/5\)\.$'),
                {
                    'en': 'Patient {0} left a review ({1}/5).',
                    'kz': 'Пациент {0} пікір қалдырды ({1}/5).',
                },
            ),
        ]

        stripped = value.strip()
        for pattern, templates in sentence_patterns:
            m = pattern.match(stripped)
            if m and target_language in templates:
                return templates[target_language].format(*m.groups())

        # Translate line-by-line while preserving unknown lines as-is.
        prefixes = line_prefixes[target_language]
        translated_lines = []
        changed = False
        for line in value.split('\n'):
            translated_line = line
            for ru_prefix, tr_prefix in prefixes.items():
                if line.startswith(ru_prefix):
                    translated_line = tr_prefix + line[len(ru_prefix):]
                    changed = True
                    break
            translated_lines.append(translated_line)
        if changed:
            return '\n'.join(translated_lines)

    return value
