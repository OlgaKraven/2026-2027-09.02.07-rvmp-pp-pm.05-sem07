<?php
declare(strict_types=1);
require __DIR__.'/lib.php';
if (PHP_SAPI !== 'cli') { http_response_code(403); exit; }
echo 'Логин администратора: ';
$login = trim(fgets(STDIN));
echo 'Учебный пароль (ввод отображается): ';
$password = trim(fgets(STDIN));
if (!preg_match('/^[A-Za-z0-9]{6,40}$/D', $login) || strlen($password) < 8) {
    exit("Логин не менее 6 латинских символов, пароль не менее 8.\n");
}
query('INSERT INTO users(login,password_hash,full_name,phone,email,role) VALUES(?,?,?,?,?,?)',
    [$login,password_hash($password,PASSWORD_DEFAULT),'Учебный Администратор',
     '8(999)123-45-67','admin@example.test','admin']);
echo "Администратор создан в выбранной учебной базе.\n";
