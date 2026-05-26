import json
import os
import re

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

        sentence_patterns = {
            'en': (
                re.compile(
                    r'^Видеоконсультация между врачом\s+(.+?)\s+и пациентом\s+(.+?)\s+состоялась\s+(.+?)\.\s+Подробная транскрипция недоступна\.$'
                ),
                'Video consultation between doctor {doctor} and patient {patient} took place on {dt}. Detailed transcript is unavailable.'
            ),
            'kz': (
                re.compile(
                    r'^Видеоконсультация между врачом\s+(.+?)\s+и пациентом\s+(.+?)\s+состоялась\s+(.+?)\.\s+Подробная транскрипция недоступна\.$'
                ),
                'Дәрігер {doctor} мен пациент {patient} арасындағы бейнеконсультация {dt} күні өтті. Толық транскрипция қолжетімсіз.'
            ),
        }

        # Replace known standalone sentence pattern first.
        pattern, template = sentence_patterns[target_language]
        m = pattern.match(value.strip())
        if m:
            return template.format(doctor=m.group(1), patient=m.group(2), dt=m.group(3))

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
