# Topic: Backup, Restore, and Recovery Techniques in PostgreSQL

## Hands-On Lab: From Beginner to Production Engineer

---

# Phase 1: Why Backup and Recovery Exist

Imagine you are a DBA at Netflix.

At 2:00 PM:

```sql
DELETE FROM users;
```

A developer accidentally forgot:

```sql
WHERE id = 100;
```

Instead of deleting one row:

```text
50 million rows deleted ❌
```

Without backup:

```text
Business Down
Customer Data Lost
Possible Legal Issues
```

With backup:

```text
Restore Database
Recover Lost Data
Resume Service
```

---

## Real Production Incidents

Many companies have suffered from:

* Accidental DELETE
* Ransomware attacks
* Disk corruption
* Cloud VM failure
* Data center outage

Backups are your **insurance policy**.

---

# What Can Go Wrong?

```text
             +-------------+
             | PostgreSQL  |
             +-------------+
                    |
    ---------------------------------
    |        |        |            |
    v        v        v            v
Disk Fail  Human   Malware    VM Crash
           Error
```

---

# Types of Recovery

| Recovery Type                 | Example                   |
| ----------------------------- | ------------------------- |
| Full Restore                  | Entire DB lost            |
| Table Restore                 | Recover one table         |
| Point-in-Time Recovery (PITR) | Restore to 2:59 PM        |
| Disaster Recovery             | Restore in another region |

---

# Phase 2: PostgreSQL Backup Architecture

```text
+-------------+
| PostgreSQL  |
+-------------+
      |
      +-------------------+
      |                   |
      v                   v
 Logical Backup      Physical Backup
 (SQL Dump)          (Binary Files)
      |                   |
      v                   v
 pg_dump            pg_basebackup
```

---

## Logical Backup

Exports SQL statements:

```sql
CREATE TABLE users (...);

INSERT INTO users VALUES (...);
```

Advantages:

✅ Portable

✅ Human-readable

✅ Restore selected objects

Disadvantages:

❌ Slow for large databases

---

## Physical Backup

Copies actual data files.

Advantages:

✅ Fast

✅ Exact copy

Disadvantages:

❌ Version dependent

---

# PostgreSQL Backup Tools

| Tool          | Purpose                |
| ------------- | ---------------------- |
| pg_dump       | Backup one database    |
| pg_dumpall    | Backup all databases   |
| pg_restore    | Restore custom backups |
| pg_basebackup | Physical backup        |
| WAL Archiving | PITR                   |

---

# Phase 3: Build It Yourself

---

# Lab Environment

We use Docker:

```text
+----------------+
| pg-primary     |
+----------------+
```

---

# Step 1: Create Lab Database

Enter PostgreSQL:

```bash
docker exec -it pg-primary psql -U postgres
```

Create DB:

```sql
CREATE DATABASE companydb;
```

Connect:

```sql
\c companydb
```

Create table:

```sql
CREATE TABLE employees(
    id SERIAL PRIMARY KEY,
    name TEXT,
    department TEXT
);
```

Insert data:

```sql
INSERT INTO employees(name, department)
VALUES
('Alice','HR'),
('Bob','IT'),
('John','Finance');
```

Verify:

```sql
SELECT * FROM employees;
```

Expected:

```text
 id | name  | department
----+-------+-----------
 1  | Alice | HR
 2  | Bob   | IT
 3  | John  | Finance
```

Exit:

```sql
\q
```

---

# Phase 4: Logical Backup using pg_dump

## Backup Entire Database

Run:

```bash
docker exec pg-primary \
pg_dump -U postgres companydb \
> companydb.sql
```

Verify:

```bash
ls -lh companydb.sql
```

Open file:

```bash
head companydb.sql
```

You will see:

```sql
CREATE TABLE employees ...
```

---

# Internal Flow
<img width="617" height="193" alt="image" src="https://github.com/user-attachments/assets/08b8f1ba-9a69-4018-ba93-ca6e6f12d720" />

```text
Database
   |
   v
pg_dump
   |
   v
SQL File
   |
   v
Disk
```

---

# What Happens Internally?

```text
PostgreSQL
    |
Snapshot Taken
    |
Read Data
    |
Generate SQL
    |
Write File
```

Important:

`pg_dump` does **not** lock the database.

Users can continue working.

---

# Backup Specific Table

```bash
docker exec pg-primary \
pg_dump -U postgres \
-t employees companydb \
> employees.sql
```

---

# Backup Schema Only

```bash
docker exec pg-primary \
pg_dump -U postgres \
-s companydb \
> schema.sql
```

---

# Backup Data Only

```bash
docker exec pg-primary \
pg_dump -U postgres \
-a companydb \
> data.sql
```

---

# Phase 5: Restore Database

---

# Simulate Disaster

Delete table:

```bash
docker exec -it pg-primary \
psql -U postgres -d companydb
```

Execute:

```sql
DROP TABLE employees;
```

Verify:

```sql
\dt
```

No tables.

---

# Restore from SQL Dump

Exit PostgreSQL:

```sql
\q
```

Restore:

```bash
docker exec -i pg-primary \
psql -U postgres companydb \
< companydb.sql
```

Verify:

```bash
docker exec -it pg-primary \
psql -U postgres -d companydb
```

```sql
SELECT * FROM employees;
```

Data restored ✅

---

# Phase 6: Custom Backup Format

PostgreSQL supports:

```text
plain
custom
directory
tar
```

Custom format is production favorite.

Create backup:

```bash
docker exec pg-primary \
pg_dump -U postgres \
-F c companydb \
> companydb.backup
```

Verify:

```bash
file companydb.backup
```

---

# Restore Custom Backup

Create new database:

```bash
docker exec -it pg-primary \
psql -U postgres
```

```sql
CREATE DATABASE restoredb;
\q
```

Restore:

```bash
docker exec -i pg-primary \
pg_restore \
-U postgres \
-d restoredb \
< companydb.backup
```

Verify:

```bash
docker exec -it pg-primary \
psql -U postgres -d restoredb
```

```sql
SELECT * FROM employees;
```

---

# Phase 7: Backup All Databases

```bash
docker exec pg-primary \
pg_dumpall -U postgres \
> full_cluster.sql
```

Contains:

```text
Roles
Databases
Privileges
Data
```

---

# Phase 8: Physical Backup using pg_basebackup

This creates a binary copy.

```bash
docker exec pg-primary \
pg_basebackup \
-U postgres \
-D /tmp/basebackup \
-F p \
-P
```

Options:

| Option | Meaning      |
| ------ | ------------ |
| -D     | Destination  |
| -F p   | Plain format |
| -P     | Progress     |

---

# Internal Physical Backup Flow

```text
Database Files
      |
      v
pg_basebackup
      |
      v
Binary Backup
      |
      v
Disk
```

---

# Phase 9: WAL Archiving and PITR

This is how enterprises recover to exact time.

Example:

```text
2:00 PM Backup
2:15 PM New Orders
2:30 PM Accident
```

Need restore to:

```text
2:29 PM
```

---

# WAL-Based Recovery

```text
Base Backup
      |
      +---- WAL1
      +---- WAL2
      +---- WAL3
      +---- WAL4
```

Replay WAL until:

```text
2:29 PM
```

---

# Enable WAL Archiving

Edit:

```conf
archive_mode = on
archive_command = 'cp %p /archive/%f'
wal_level = replica
```

Restart PostgreSQL.

---

# Recovery Process

```text
Restore Base Backup
        |
Replay WAL Files
        |
Stop at Recovery Time
        |
Database Ready
```

---

# Phase 10: Production Simulation

You are DBA at Amazon.

Environment:

```text
100 TB Database
100 Million Users
24x7 Availability
```

Strategy:

```text
Weekly Full Backup
Daily Incremental Backup
Continuous WAL Archiving
Cross-region Backup
```

---

# Troubleshooting Lab

---

## Backup Fails

Error:

```text
permission denied
```

Check:

```bash
ls -l
```

---

## Restore Fails

Error:

```text
database already exists
```

Fix:

```sql
DROP DATABASE restoredb;
CREATE DATABASE restoredb;
```

---

## Corrupted Backup

Verify:

```bash
pg_restore -l companydb.backup
```

---

# Monitoring Backup

Check running backups:

```sql
SELECT *
FROM pg_stat_progress_basebackup;
```

---

Check WAL generation:

```sql
SELECT pg_current_wal_lsn();
```

---

Measure WAL size:

```sql
SELECT pg_size_pretty(
    pg_wal_lsn_diff(
        pg_current_wal_lsn(),
        '0/0'
    )
);
```

---

# Interview Mastery

### Junior

1. Difference between `pg_dump` and `pg_dumpall`?
2. What is WAL?

### Mid-Level

3. Why use custom backup format?
4. Explain PITR.

### Senior

5. How would you back up a 50 TB database?
6. How do you verify backup integrity?

### Staff Engineer

7. Design backup strategy for multi-region PostgreSQL.

---

# Best Practices

✅ Automate backups with cron/Kubernetes CronJob

✅ Test restores regularly

✅ Store backups offsite

✅ Encrypt backups

✅ Monitor backup success

✅ Retain multiple generations

---

# Bad Practices

❌ Only taking backups

❌ Never testing restores

❌ Keeping backups on same server

❌ Ignoring WAL growth

❌ No recovery documentation

---

# Mini Project: Build Enterprise Backup System

Build:

```text
+----------------+
| PostgreSQL     |
+----------------+
       |
       +---- Daily pg_dump
       |
       +---- Weekly Base Backup
       |
       +---- WAL Archive
       |
       +---- S3 Storage
```

Requirements:

* Daily logical backup
* Weekly physical backup
* WAL archiving
* Backup verification
* Automated restore test

---

# Hands-On Lab — Execute Now

Assuming your `pg-primary` container exists:

```bash
docker exec -it pg-primary psql -U postgres

CREATE DATABASE companydb;
\c companydb

CREATE TABLE employees(
    id SERIAL PRIMARY KEY,
    name TEXT,
    department TEXT
);

INSERT INTO employees(name, department)
VALUES
('Alice','HR'),
('Bob','IT'),
('John','Finance');

SELECT * FROM employees;
\q
```

Then create your first backup:

```bash
docker exec pg-primary \
pg_dump -U postgres companydb \
> companydb.sql

ls -lh companydb.sql
head companydb.sql
```

Paste the outputs here, and we'll continue to **WAL Archiving + Point-in-Time Recovery (PITR)** with a real disaster simulation.
