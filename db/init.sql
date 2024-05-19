CREATE USER ${DB_REPL_USER} WITH REPLICATION ENCRYPTED PASSWORD '${DB_REPL_PASSWORD}';
SELECT pg_create_physical_replication_slot('replication_slot');

\connect ${DB_DATABASE}
CREATE TABLE phones(
  id SERIAL PRIMARY KEY,
  number VARCHAR(100) NOT NULL
);
CREATE TABLE emails(
  id SERIAL PRIMARY KEY,
  address VARCHAR(255) NOT NULL
);

INSERT INTO emails (address) VALUES ('123qwerty@test.com'), ('ANNA2@yandex.ru');
INSERT INTO phones (number) VALUES ('89617891234'), ('+7-913-684-31-55');


