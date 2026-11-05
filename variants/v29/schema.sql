CREATE TABLE users (
 id INT PRIMARY KEY AUTO_INCREMENT,
 login VARCHAR(40) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 full_name VARCHAR(120) NOT NULL,
 phone VARCHAR(20) NOT NULL,
 email VARCHAR(120) NOT NULL,
 role VARCHAR(10) NOT NULL DEFAULT 'client',
 CHECK (role IN ('client','admin'))
) ENGINE=InnoDB;

CREATE TABLE services (
 id INT PRIMARY KEY AUTO_INCREMENT,
 name VARCHAR(80) NOT NULL UNIQUE,
 active BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE technicians (
 id INT PRIMARY KEY AUTO_INCREMENT,
 name VARCHAR(120) NOT NULL,
 active BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE tickets (
 id INT PRIMARY KEY AUTO_INCREMENT,
 user_id INT NOT NULL,
 service_id INT NOT NULL,
 technician_id INT NULL,
 equipment VARCHAR(120) NOT NULL,
 symptom TEXT NOT NULL,
 parameters JSON NOT NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'Новая',
 result TEXT NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (user_id) REFERENCES users(id),
 FOREIGN KEY (service_id) REFERENCES services(id),
 FOREIGN KEY (technician_id) REFERENCES technicians(id),
 CHECK (status IN ('Новая','В работе','Завершена'))
) ENGINE=InnoDB;

CREATE TABLE ticket_history (
 id INT PRIMARY KEY AUTO_INCREMENT,
 ticket_id INT NOT NULL,
 actor_id INT NOT NULL,
 old_status VARCHAR(20) NULL,
 new_status VARCHAR(20) NOT NULL,
 comment TEXT NOT NULL,
 changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (ticket_id) REFERENCES tickets(id),
 FOREIGN KEY (actor_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE ticket_reviews (
 id INT PRIMARY KEY AUTO_INCREMENT,
 ticket_id INT NOT NULL UNIQUE,
 user_id INT NOT NULL,
 body VARCHAR(1000) NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (ticket_id) REFERENCES tickets(id),
 FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

INSERT INTO services(name) VALUES ('Ремонт охлаждения'),('Общая диагностика');
INSERT INTO technicians(name) VALUES ('Мастер 29'),('Специалист 29');
