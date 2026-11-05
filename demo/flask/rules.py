import math
import re


def validate_details(domain, values):
    errors = []
    for field in domain['fields']:
        value = values.get(field['name'], '').strip()
        if not value:
            if field.get('required'):
                errors.append(f"Заполните поле «{field['label']}».")
            continue
        if len(value) > 120:
            errors.append(f"Поле «{field['label']}» слишком длинное.")
        if field['type'] == 'select' and value not in field['choices']:
            errors.append(f"Выберите допустимое значение «{field['label']}».")
        if field.get('pattern') and not re.fullmatch(field['pattern'], value):
            errors.append(f"Проверьте формат «{field['label']}».")
        if field['type'] in ('number', 'integer'):
            try:
                number = float(value)
                valid = math.isfinite(number)
                valid &= field['type'] != 'integer' or number.is_integer()
                valid &= number >= field.get('min', 0)
                valid &= number <= field.get('max', 100000)
                if not valid:
                    raise ValueError()
            except ValueError:
                errors.append(f"Проверьте число «{field['label']}».")
    for rule in domain.get('rules', []):
        condition = rule['when']
        if values.get(condition['field']) == condition['equals']:
            if rule.get('require') and not values.get(rule['require'], '').strip():
                errors.append(rule['message'])
            if rule.get('expect'):
                expected = rule['expect']
                if values.get(expected['field']) != expected['equals']:
                    errors.append(rule['message'])
    return errors


def validate_registration(values):
    errors = []
    if not re.fullmatch(r'[A-Za-z0-9]{6,40}', values.get('login', '')):
        errors.append('Логин: от 6 до 40 латинских букв и цифр.')
    if not 8 <= len(values.get('password', '')) or len(values.get('password', '').encode('utf-8')) > 64:
        errors.append('Пароль: от 8 символов, не более 64 байт UTF-8.')
    if not re.fullmatch(r'[А-Яа-яЁё ]{3,120}', values.get('full_name', '').strip()):
        errors.append('ФИО: кириллица и пробелы.')
    if not re.fullmatch(r'8\(\d{3}\)\d{3}-\d{2}-\d{2}', values.get('phone', '')):
        errors.append('Телефон: 8(999)123-45-67.')
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', values.get('email', '')) or len(values.get('email','')) > 120:
        errors.append('Введите корректную электронную почту.')
    return errors


class DomainPolicy:
    def __init__(self, domain):
        self.domain = domain

    def validate(self, values):
        return validate_details(self.domain, values)
