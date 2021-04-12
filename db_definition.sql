DROP DATABASE IF EXISTS oscap_wrapper;
CREATE DATABASE IF NOT EXISTS oscap_wrapper;
USE oscap_wrapper;

CREATE TABLE scans (
    id   INT(10)      NOT NULL AUTO_INCREMENT,
    slug VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY (id)
);

CREATE TABLE rules (
    id    INT(10)      NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    slug  VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY (id)
);

CREATE TABLE results (
    id    INT(10)      NOT NULL AUTO_INCREMENT,
    value VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY (id)
);

CREATE TABLE rules_scans (
    id        INT(10) NOT NULL AUTO_INCREMENT,
    scan_id   INT(10) NOT NULL,
    rule_id   INT(10) NOT NULL,
    result_id INT(10) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (scan_id)   REFERENCES scans(id),
    FOREIGN KEY (rule_id)   REFERENCES rules(id),
    FOREIGN KEY (result_id) REFERENCES results(id)
);
