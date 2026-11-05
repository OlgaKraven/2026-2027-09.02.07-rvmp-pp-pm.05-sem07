<?php
declare(strict_types=1);

function db(): PDO {
    static $connection = null;
    if (!$connection) {
        $host = getenv('DB_HOST') ?: '127.0.0.1';
        $port = getenv('DB_PORT') ?: '3306';
        $name = getenv('DB_NAME') ?: 'pm05_php';
        $connection = new PDO("mysql:host=$host;port=$port;dbname=$name;charset=utf8mb4",
            getenv('DB_USER') ?: 'root', getenv('DB_PASSWORD') ?: '',
            [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
             PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
             PDO::ATTR_EMULATE_PREPARES => false]);
    }
    return $connection;
}

function query(string $sql, array $args = []): PDOStatement {
    $statement = db()->prepare($sql);
    $statement->execute($args);
    return $statement;
}

function e(mixed $value): string {
    return htmlspecialchars((string)$value, ENT_QUOTES, 'UTF-8');
}

function fail(int $status): never {
    http_response_code($status);
    exit("Действие недоступно ($status)");
}

function current_user(): array|false {
    return query('SELECT id,login,full_name,role FROM users WHERE id=?',
        [$_SESSION['user_id'] ?? 0])->fetch();
}

function require_user(bool $admin = false): array {
    $user = current_user();
    if (!$user || ($admin && $user['role'] !== 'admin')) fail(403);
    return $user;
}

function go(string $page, int $id = 0): never {
    header('Location: index.php?page='.$page.($id ? '&id='.$id : ''));
    exit;
}

final class DomainPolicy {
    public function __construct(public array $domain) {}

    public function validate(array $values): array {
        $errors = [];
        foreach ($this->domain['fields'] as $field) {
            $value = trim((string)($values[$field['name']] ?? ''));
            $label = $field['label'];
            if ($value === '') {
                if ($field['required'] ?? false) $errors[] = "Заполните поле «{$label}».";
                continue;
            }
            if (mb_strlen($value) > 120) $errors[] = "Поле «{$label}» слишком длинное.";
            if ($field['type'] === 'select' && !in_array($value, $field['choices'], true))
                $errors[] = "Выберите допустимое значение «{$label}».";
            if (isset($field['pattern']) && !preg_match('~'.$field['pattern'].'~u', $value))
                $errors[] = "Проверьте формат «{$label}».";
            if (in_array($field['type'], ['number','integer'], true)) {
                $number = is_numeric($value) ? (float)$value : NAN;
                $valid = is_finite($number)
                    && ($field['type'] !== 'integer' || floor($number) === $number)
                    && $number >= ($field['min'] ?? 0)
                    && $number <= ($field['max'] ?? 100000);
                if (!$valid) $errors[] = "Проверьте число «{$label}».";
            }
        }
        foreach ($this->domain['rules'] ?? [] as $rule) {
            $when = $rule['when'];
            if (($values[$when['field']] ?? '') !== $when['equals']) continue;
            if (isset($rule['require']) && trim((string)($values[$rule['require']] ?? '')) === '')
                $errors[] = $rule['message'];
            if (isset($rule['expect'])) {
                $expect = $rule['expect'];
                if (($values[$expect['field']] ?? '') !== $expect['equals'])
                    $errors[] = $rule['message'];
            }
        }
        return $errors;
    }
}

function registration_errors(array $v): array {
    $errors = [];
    if (!preg_match('/^[A-Za-z0-9]{6,40}$/D', $v['login'] ?? ''))
        $errors[] = 'Логин: от 6 до 40 латинских букв и цифр.';
    $length = mb_strlen($v['password'] ?? '');
    if ($length < 8 || strlen($v['password'] ?? '') > 64) $errors[] = 'Пароль: от 8 символов, не более 64 байт UTF-8.';
    if (!preg_match('/^[А-Яа-яЁё ]{3,120}$/uD', trim($v['full_name'] ?? '')))
        $errors[] = 'ФИО: кириллица и пробелы.';
    if (!preg_match('/^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/D', $v['phone'] ?? ''))
        $errors[] = 'Телефон: 8(999)123-45-67.';
    if (!filter_var($v['email'] ?? '', FILTER_VALIDATE_EMAIL) || strlen($v['email'] ?? '') > 120)
        $errors[] = 'Введите корректную электронную почту.';
    return $errors;
}

function csrf_input(): void {
    echo '<input type="hidden" name="csrf" value="'.e($_SESSION['csrf']).'">';
}

function input(string $name, string $label, string $type = 'text'): void {
    $value = $type === 'password' ? '' : ($_POST[$name] ?? '');
    echo '<label>'.e($label).'<input name="'.e($name).'" type="'.e($type).
        '" value="'.e($value).'" required></label>';
}
