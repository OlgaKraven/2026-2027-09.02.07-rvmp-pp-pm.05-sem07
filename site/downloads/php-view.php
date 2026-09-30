<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><?= e($domain['title']) ?> — ПМ.05</title><link rel="stylesheet" href="style.css"></head>
<body><main><header><p>ПМ.05 · Проектирование и разработка информационных систем</p><h1><?= e($domain['title']) ?></h1></header>
<nav><?php if ($user): ?>
<a href="index.php"><?= $user['role'] === 'admin' ? 'Очередь заявок' : 'Мои заявки' ?></a>
<a href="index.php?page=new">Создать заявку</a><span><?= e($user['full_name'].' · '.$user['role']) ?></span>
<form action="index.php?page=logout" method="post"><?php csrf_input(); ?><button>Выйти</button></form>
<?php else: ?><a href="index.php?page=login">Вход</a><a href="index.php?page=register">Регистрация</a><?php endif ?></nav>
<?php if ($errors): ?><section class="error" role="alert"><h2>Проверьте введённые данные</h2><ul><?php foreach ($errors as $error): ?><li><?= e($error) ?></li><?php endforeach ?></ul></section><?php endif ?>
<?php if (in_array($page,['login','register'],true)): ?>
<section><h2><?= $page === 'register' ? 'Регистрация клиента' : 'Вход в систему' ?></h2>
<form method="post"><?php csrf_input(); input('login','Логин'); input('password','Пароль','password'); ?>
<?php if ($page === 'register'): input('full_name','ФИО'); input('phone','Телефон: 8(999)123-45-67'); input('email','Электронная почта','email'); endif ?>
<button><?= $page === 'register' ? 'Создать пользователя' : 'Войти' ?></button></form>
<p><a href="index.php?page=<?= $page === 'register' ? 'login' : 'register' ?>"><?= $page === 'register' ? 'Уже зарегистрированы? Вход' : 'Ещё не зарегистрированы? Регистрация' ?></a></p></section>
<?php elseif ($page === 'new'): ?>
<section><h2>Новая заявка</h2><form method="post"><?php csrf_input(); input('equipment','Оборудование и модель'); ?>
<label>Неисправность<textarea name="symptom" required><?= e($_POST['symptom'] ?? '') ?></textarea></label>
<label>Услуга<select name="service_id" required><option value="">Выберите услугу</option><?php foreach ($services as $s): ?><option value="<?= $s['id'] ?>" <?= (string)$s['id'] === ($_POST['service_id'] ?? '') ? 'selected' : '' ?>><?= e($s['name']) ?></option><?php endforeach ?></select></label>
<?php foreach ($domain['fields'] as $f): ?><label><?= e($f['label']) ?>
<?php if ($f['type'] === 'select'): ?><select name="<?= e($f['name']) ?>"><option value="">Выберите значение</option><?php foreach ($f['choices'] as $choice): ?><option <?= ($_POST[$f['name']] ?? '') === $choice ? 'selected' : '' ?>><?= e($choice) ?></option><?php endforeach ?></select>
<?php else: ?><input name="<?= e($f['name']) ?>" value="<?= e($_POST[$f['name']] ?? '') ?>" type="<?= in_array($f['type'],['integer','number'],true) ? 'number' : 'text' ?>" step="<?= $f['type'] === 'integer' ? '1' : 'any' ?>"><?php endif ?></label><?php endforeach ?>
<button>Отправить заявку</button></form></section>
<?php elseif ($page === 'list'): ?>
<section><h2><?= $user['role'] === 'admin' ? 'Очередь заявок' : 'Мои заявки' ?></h2>
<form method="get"><input type="hidden" name="page" value="list"><label>Статус<select name="status"><option value="">Все</option><?php foreach (['Новая','В работе','Завершена'] as $s): ?><option <?= $status === $s ? 'selected' : '' ?>><?= e($s) ?></option><?php endforeach ?></select></label><button>Применить фильтр</button></form>
<?php foreach ($tickets as $t): ?><article><h3><a href="index.php?page=ticket&amp;id=<?= $t['id'] ?>">Заявка №<?= $t['id'] ?> · <?= e($t['equipment']) ?></a></h3><p><?= e($t['service']) ?> · <strong><?= e($t['status']) ?></strong></p><p>Клиент: <?= e($t['full_name']) ?> · Исполнитель: <?= e($t['technician'] ?: 'Не назначен') ?></p></article><?php endforeach ?>
<?php if (!$tickets): ?><p>Заявок по выбранным условиям нет.</p><?php endif ?></section>
<?php elseif ($page === 'ticket'): ?>
<section><h2>Заявка №<?= $ticket['id'] ?> · <?= e($ticket['status']) ?></h2><p><?= e($ticket['equipment'].' · '.$ticket['service']) ?></p><p><?= e($ticket['symptom']) ?></p>
<dl><?php foreach ($domain['fields'] as $f): ?><dt><?= e($f['label']) ?></dt><dd><?= e($details[$f['name']] ?: 'Не указано') ?></dd><?php endforeach ?></dl>
<p>Исполнитель: <?= e($ticket['technician'] ?: 'Не назначен') ?></p><p>Результат: <?= e($ticket['result'] ?: 'Работа ещё не завершена') ?></p>
<?php if ($user['role'] === 'admin' && $ticket['status'] !== 'Завершена'): ?>
<form method="post"><?php csrf_input(); ?><label>Исполнитель<select name="technician_id"><option value="">Назначьте исполнителя</option><?php foreach ($technicians as $n): ?><option value="<?= $n['id'] ?>" <?= $ticket['technician_id'] === $n['id'] ? 'selected' : '' ?>><?= e($n['name']) ?></option><?php endforeach ?></select></label>
<input type="hidden" name="status" value="<?= $ticket['status'] === 'Новая' ? 'В работе' : 'Завершена' ?>">
<label>Описание результата<textarea name="result"><?= e($_POST['result'] ?? $ticket['result']) ?></textarea></label>
<button><?= $ticket['status'] === 'Новая' ? 'Принять в работу' : 'Завершить заявку' ?></button></form><?php endif ?></section>
<section><h2>История обработки</h2><?php foreach ($history as $h): ?><article><p><?= e($h['changed_at'].' · '.$h['full_name']) ?></p><p><?= e($h['old_status'] ?: 'Создание') ?> → <strong><?= e($h['new_status']) ?></strong></p><p><?= e($h['comment']) ?></p></article><?php endforeach ?></section>
<?php endif ?>
<footer>Учебная демонстрация · версия 1.0 · отдельная учебная база данных</footer></main></body></html>
