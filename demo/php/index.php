<?php
declare(strict_types=1);
require __DIR__.'/lib.php';
session_name('pm05_php');
session_start(['cookie_httponly'=>true, 'cookie_samesite'=>'Lax']);
$_SESSION['csrf'] ??= bin2hex(random_bytes(24));
$post = $_SERVER['REQUEST_METHOD'] === 'POST';
if ($post && !hash_equals($_SESSION['csrf'], (string)($_POST['csrf'] ?? ''))) fail(400);
$domain = json_decode(file_get_contents(__DIR__.'/../domain.json'), true, flags: JSON_THROW_ON_ERROR);
$policy = new DomainPolicy($domain);
$page = $_GET['page'] ?? 'list';
$errors = [];
$user = current_user();

if ($page === 'register' && $post) {
    $errors = registration_errors($_POST);
    if (!$errors) {
        try {
            query('INSERT INTO users(login,password_hash,full_name,phone,email) VALUES(?,?,?,?,?)',
                [$_POST['login'],password_hash($_POST['password'],PASSWORD_DEFAULT),
                 $_POST['full_name'],$_POST['phone'],$_POST['email']]);
            go('login');
        } catch (PDOException $ex) {
            if ($ex->getCode() !== '23000') throw $ex;
            $errors[] = 'Этот логин уже занят.';
        }
    }
}
if ($page === 'login' && $post) {
    $found = query('SELECT * FROM users WHERE login=?', [$_POST['login'] ?? ''])->fetch();
    if ($found && password_verify($_POST['password'] ?? '', $found['password_hash'])) {
        session_regenerate_id(true);
        $_SESSION = ['user_id'=>$found['id'],'csrf'=>bin2hex(random_bytes(24))];
        go('list');
    }
    $errors[] = 'Неверный логин или пароль.';
}
if ($page === 'logout') {
    if (!$post) fail(405);
    $_SESSION = [];
    session_destroy();
    go('login');
}
if (!in_array($page, ['login','register'], true)) {
    if (!$user) go('login');
    $user = require_user();
}

if ($page === 'new') {
    $services = query('SELECT * FROM services WHERE active=TRUE ORDER BY id')->fetchAll();
    if ($post) {
        $service = null;
        foreach ($services as $s) if ((string)$s['id'] === ($_POST['service_id'] ?? '')) $service = $s;
        if (!$service) $errors[] = 'Выберите действующую услугу.';
        $length = mb_strlen(trim($_POST['equipment'] ?? ''));
        if ($length < 3 || $length > 120) $errors[] = 'Оборудование: от 3 до 120 символов.';
        $length = mb_strlen(trim($_POST['symptom'] ?? ''));
        if ($length < 5 || $length > 2000) $errors[] = 'Описание неисправности: от 5 до 2000 символов.';
        $details = [];
        foreach ($domain['fields'] as $f) $details[$f['name']] = $_POST[$f['name']] ?? '';
        $errors = array_merge($errors, $policy->validate($details + ['service'=>$service['name'] ?? '']));
        if (!$errors) {
            db()->beginTransaction();
            try {
                query('INSERT INTO tickets(user_id,service_id,equipment,symptom,parameters,result) VALUES(?,?,?,?,?,?)',
                    [$user['id'],$service['id'],$_POST['equipment'],$_POST['symptom'],
                     json_encode($details,JSON_UNESCAPED_UNICODE),'']);
                $id = (int)db()->lastInsertId();
                query('INSERT INTO ticket_history(ticket_id,actor_id,new_status,comment) VALUES(?,?,?,?)',
                    [$id,$user['id'],'Новая','Заявка создана']);
                db()->commit();
                go('ticket', $id);
            } catch (Throwable $ex) { db()->rollBack(); throw $ex; }
        }
    }
}

if ($page === 'ticket') {
    $id = (int)($_GET['id'] ?? 0);
    if ($post) {
        require_user(true);
        db()->beginTransaction();
        try {
            $ticket = query('SELECT * FROM tickets WHERE id=? FOR UPDATE', [$id])->fetch();
            if (!$ticket) { db()->rollBack(); fail(404); }
            $target = $_POST['status'] ?? '';
            $expected = ['Новая'=>'В работе','В работе'=>'Завершена'][$ticket['status']] ?? null;
            $technician = (int)($_POST['technician_id'] ?? 0);
            if (!query('SELECT id FROM technicians WHERE id=? AND active=TRUE', [$technician])->fetch())
                $errors[] = 'Назначьте действующего исполнителя.';
            if ($target !== $expected) $errors[] = 'Недопустимый переход статуса.';
            $result = trim($_POST['result'] ?? '');
            $length = mb_strlen($result);
            if ($target === 'Завершена' && ($length < 5 || $length > 2000))
                $errors[] = 'Для завершения опишите результат: от 5 до 2000 символов.';
            if ($length > 2000) $errors[] = 'Результат слишком длинный.';
            if (!$errors) {
                query('UPDATE tickets SET status=?,technician_id=?,result=? WHERE id=?',
                    [$target,$technician,$result,$id]);
                query('INSERT INTO ticket_history(ticket_id,actor_id,old_status,new_status,comment) VALUES(?,?,?,?,?)',
                    [$id,$user['id'],$ticket['status'],$target,$result]);
            }
            db()->commit();
        } catch (Throwable $ex) { db()->rollBack(); throw $ex; }
    }
    $ticket = query("SELECT t.*,s.name AS service,n.name AS technician FROM tickets t
        JOIN services s ON s.id=t.service_id LEFT JOIN technicians n ON n.id=t.technician_id
        WHERE t.id=? AND (?='admin' OR t.user_id=?)", [$id,$user['role'],$user['id']])->fetch();
    if (!$ticket) fail(404);
    $details = json_decode($ticket['parameters'], true, flags:JSON_THROW_ON_ERROR);
    $history = query('SELECT h.*,u.full_name FROM ticket_history h JOIN users u ON u.id=h.actor_id WHERE ticket_id=? ORDER BY h.id', [$id])->fetchAll();
    $technicians = query('SELECT * FROM technicians WHERE active=TRUE')->fetchAll();
}

if ($page === 'list') {
    $condition = $user['role'] === 'admin' ? '1=1' : 't.user_id=?';
    $args = $user['role'] === 'admin' ? [] : [$user['id']];
    $status = $_GET['status'] ?? '';
    if (in_array($status,['Новая','В работе','Завершена'],true)) { $condition .= ' AND t.status=?'; $args[] = $status; }
    $tickets = query('SELECT t.*,u.full_name,s.name AS service,n.name AS technician FROM tickets t
        JOIN users u ON u.id=t.user_id JOIN services s ON s.id=t.service_id
        LEFT JOIN technicians n ON n.id=t.technician_id WHERE '.$condition.' ORDER BY t.id DESC', $args)->fetchAll();
}
if (!in_array($page,['login','register','new','ticket','list'],true)) fail(404);
require __DIR__.'/view.php';
