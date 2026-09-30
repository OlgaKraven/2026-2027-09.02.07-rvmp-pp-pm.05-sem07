import json
import os
import secrets
from pathlib import Path
import pymysql
from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from db import database, rows
from rules import DomainPolicy, validate_registration

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  SESSION_COOKIE_NAME='pm05_flask')
domain = json.loads((Path(__file__).parent.parent / 'domain.json').read_text())
policy = DomainPolicy(domain)


@app.before_request
def protect():
    session.setdefault('csrf', secrets.token_hex(24))
    if request.method == 'POST' and not secrets.compare_digest(
        session['csrf'], request.form.get('csrf', '')
    ):
        abort(400, 'Недействительный токен формы. Обновите страницу.')


def current_user():
    found = rows('SELECT id,login,full_name,role FROM users WHERE id=%s',
                 (session.get('user_id', 0),))
    return found[0] if found else None


def require_user(admin=False):
    user = current_user()
    if not user or (admin and user['role'] != 'admin'):
        abort(403)
    return user


def show(page, **context):
    return render_template('page.html', page=page, domain=domain,
                           user=current_user(), values=request.form,
                           errors=context.pop('errors', []), **context)


@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = []
    if request.method == 'POST':
        errors = validate_registration(request.form)
        if not errors:
            try:
                with database() as connection, connection.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO users(login,password_hash,full_name,phone,email) '
                        'VALUES(%s,%s,%s,%s,%s)',
                        (request.form['login'], generate_password_hash(request.form['password']),
                         request.form['full_name'], request.form['phone'], request.form['email']))
                return redirect(url_for('login'))
            except pymysql.err.IntegrityError:
                errors = ['Этот логин уже занят.']
    return show('register', errors=errors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == 'POST':
        found = rows('SELECT * FROM users WHERE login=%s', (request.form.get('login',''),))
        if found and check_password_hash(found[0]['password_hash'], request.form.get('password','')):
            session.clear()
            session.update(user_id=found[0]['id'], csrf=secrets.token_hex(24))
            return redirect(url_for('index'))
        errors = ['Неверный логин или пароль.']
    return show('login', errors=errors)


@app.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.get('/')
def index():
    if not current_user():
        return redirect(url_for('login'))
    user = require_user()
    condition = '1=1' if user['role'] == 'admin' else 't.user_id=%s'
    args = [] if user['role'] == 'admin' else [user['id']]
    status = request.args.get('status', '')
    if status in ('Новая','В работе','Завершена'):
        condition += ' AND t.status=%s'
        args.append(status)
    tickets = rows('SELECT t.*,u.full_name,s.name AS service,n.name AS technician '
                   'FROM tickets t JOIN users u ON u.id=t.user_id '
                   'JOIN services s ON s.id=t.service_id '
                   'LEFT JOIN technicians n ON n.id=t.technician_id '
                   f'WHERE {condition} ORDER BY t.id DESC', args)
    return show('list', tickets=tickets, status=status)


@app.route('/new', methods=['GET','POST'])
def new():
    user = require_user()
    services = rows('SELECT * FROM services WHERE active=TRUE ORDER BY id')
    errors = []
    if request.method == 'POST':
        service = next((s for s in services if str(s['id']) == request.form.get('service_id')), None)
        if not service:
            errors.append('Выберите действующую услугу.')
        if not 3 <= len(request.form.get('equipment','').strip()) <= 120:
            errors.append('Оборудование: от 3 до 120 символов.')
        if not 5 <= len(request.form.get('symptom','').strip()) <= 2000:
            errors.append('Описание неисправности: от 5 до 2000 символов.')
        details = {f['name']:request.form.get(f['name'],'') for f in domain['fields']}
        errors += policy.validate({**details, 'service':service['name'] if service else ''})
        if not errors:
            with database() as connection, connection.cursor() as cursor:
                cursor.execute('INSERT INTO tickets(user_id,service_id,equipment,symptom,parameters,result) '
                               'VALUES(%s,%s,%s,%s,%s,%s)',
                               (user['id'],service['id'],request.form['equipment'],request.form['symptom'],
                                json.dumps(details,ensure_ascii=False),''))
                ticket_id = cursor.lastrowid
                cursor.execute('INSERT INTO ticket_history(ticket_id,actor_id,new_status,comment) '
                               'VALUES(%s,%s,%s,%s)',(ticket_id,user['id'],'Новая','Заявка создана'))
            return redirect(url_for('detail',ticket_id=ticket_id))
    return show('new',services=services,errors=errors)


@app.route('/ticket/<int:ticket_id>', methods=['GET','POST'])
def detail(ticket_id):
    user = require_user()
    errors = []
    if request.method == 'POST':
        require_user(admin=True)
        with database() as connection, connection.cursor() as cursor:
            cursor.execute('SELECT * FROM tickets WHERE id=%s FOR UPDATE',(ticket_id,))
            ticket = cursor.fetchone()
            if not ticket:
                abort(404)
            target = request.form.get('status','')
            expected = {'Новая':'В работе','В работе':'Завершена'}.get(ticket['status'])
            try:
                technician = int(request.form.get('technician_id',''))
            except ValueError:
                technician = 0
            cursor.execute('SELECT id FROM technicians WHERE id=%s AND active=TRUE',(technician or 0,))
            if not cursor.fetchone():
                errors.append('Назначьте действующего исполнителя.')
            result = request.form.get('result','').strip()
            if target != expected:
                errors.append('Недопустимый переход статуса.')
            if target == 'Завершена' and not 5 <= len(result) <= 2000:
                errors.append('Для завершения опишите результат: от 5 до 2000 символов.')
            if len(result) > 2000:
                errors.append('Результат слишком длинный.')
            if not errors:
                cursor.execute('UPDATE tickets SET status=%s,technician_id=%s,result=%s WHERE id=%s',
                               (target,technician,result,ticket_id))
                cursor.execute('INSERT INTO ticket_history(ticket_id,actor_id,old_status,new_status,comment) '
                               'VALUES(%s,%s,%s,%s,%s)',(ticket_id,user['id'],ticket['status'],target,result))
    found = rows('SELECT t.*,s.name AS service,n.name AS technician FROM tickets t '
                 'JOIN services s ON s.id=t.service_id LEFT JOIN technicians n ON n.id=t.technician_id '
                 'WHERE t.id=%s AND (%s=\'admin\' OR t.user_id=%s)',(ticket_id,user['role'],user['id']))
    if not found:
        abort(404)
    history = rows('SELECT h.*,u.full_name FROM ticket_history h JOIN users u ON u.id=h.actor_id '
                   'WHERE ticket_id=%s ORDER BY h.id',(ticket_id,))
    return show('detail',ticket=found[0],details=json.loads(found[0]['parameters']),history=history,
                technicians=rows('SELECT * FROM technicians WHERE active=TRUE'),errors=errors)


@app.cli.command('create-admin')
def create_admin():
    import getpass
    login = input('Логин администратора: ')
    password = getpass.getpass('Пароль администратора: ')
    with database() as connection, connection.cursor() as cursor:
        cursor.execute('INSERT INTO users(login,password_hash,full_name,phone,email,role) '
                       'VALUES(%s,%s,%s,%s,%s,%s)',
                       (login,generate_password_hash(password),'Учебный Администратор',
                        '8(999)123-45-67','admin@example.test','admin'))
    print('Администратор создан в выбранной учебной базе.')
