# PostgreSQL Replication + FastAPI

## Build a Production-Style System End-to-End

We are going to build a real architecture used in production:

```text
                    Clients
                       |
                       v
               +---------------+
               |    FastAPI    |
               +---------------+
                 |          |
          Write DB      Read DB
                 |          |
                 v          v
          +-------------+   +-------------+
          | Primary DB  |-->| Replica DB  |
          +-------------+   +-------------+
                  WAL Streaming
```

## What We Will Build

By the end you will have:

✅ PostgreSQL Primary

✅ PostgreSQL Replica

✅ FastAPI Application

✅ SQLAlchemy ORM

✅ Separate Read/Write Connections

✅ Automatic Replication

✅ Production-ready project structure

---

# Phase 1: Why This Architecture Exists

Imagine you work at Netflix:

```text
10M users
```

User actions:

```text
Login
Browse movies
Search movies
Play videos
```

Most requests are **reads**:

```text
95% READS
5% WRITES
```

If all traffic hits one database:

```text
FastAPI
   |
   v
Primary DB
```

Eventually:

❌ CPU high

❌ Slow queries

❌ Downtime

Solution:

```text
Writes → Primary
Reads  → Replica
```

---

# Phase 2: Architecture

```text
                    +------------+
                    |  FastAPI   |
                    +------------+
                       |      |
             Write     |      | Read
                       |      |
                       v      v

               +----------+  +----------+
               | Primary  |->| Replica  |
               +----------+  +----------+
                    WAL Replication
```

---

# Lab Directory Structure

```text
postgres-fastapi-lab/
│
├── docker-compose.yml
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── crud.py
│
└── requirements.txt
```

---

# Phase 3: Build It Yourself

## Step 1: Create Project

```bash
mkdir postgres-fastapi-lab
cd postgres-fastapi-lab

mkdir app
touch docker-compose.yml
touch requirements.txt
```

Verify:

```bash
tree .
```

Expected:

```text
.
├── app
├── docker-compose.yml
└── requirements.txt
```

---

# Step 2: Create Docker Network

```bash
docker network create pg-net
```

---

# Step 3: Start Primary PostgreSQL

```bash
docker run -d \
--name pg-primary \
--network pg-net \
-e POSTGRES_PASSWORD=admin123 \
-p 5432:5432 \
postgres:16
```

Verify:

```bash
docker ps
```

---

# Step 4: Create Replication User

Enter PostgreSQL:

```bash
docker exec -it pg-primary psql -U postgres
```

Create user:

```sql
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'replica123';
```

Verify:

```sql
\du
```

Exit:

```sql
\q
```

---

# Step 5: Enable Replication

Open PostgreSQL config:

```bash
docker exec -it pg-primary bash
```

Find config:

```bash
find / -name postgresql.conf
```

Edit:

```bash
apt update && apt install -y vim
vim /var/lib/postgresql/data/postgresql.conf
```

Ensure:

```conf
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
listen_addresses='*'
```

---

# Configure pg_hba.conf

Open:

```bash
vim /var/lib/postgresql/data/pg_hba.conf
```

Add:

```conf
host replication replicator 0.0.0.0/0 md5
host all all 0.0.0.0/0 md5
```

Restart:

```bash
docker restart pg-primary
```

---

# Phase 4: Build Replica

## Create Base Backup

Run Replica container:

```bash
docker run -d \
--name pg-replica \
--network pg-net \
-e POSTGRES_PASSWORD=admin123 \
postgres:16
```

Stop replica:

```bash
docker stop pg-replica
```

Copy backup:

```bash
docker run --rm \
--network pg-net \
-e PGPASSWORD=replica123 \
postgres:16 \
pg_basebackup \
-h pg-primary \
-D /tmp/backup \
-U replicator \
-v -P -R
```

> In real production, the backup is copied into the replica volume.

---

# Simplified Replica Setup Using Docker Compose

Later we'll automate this.

---

# Phase 5: Create Application Database

Enter primary:

```bash
docker exec -it pg-primary psql -U postgres
```

Create DB:

```sql
CREATE DATABASE appdb;
```

Connect:

```sql
\c appdb
```

Create table:

```sql
CREATE TABLE users(
    id SERIAL PRIMARY KEY,
    name TEXT
);
```

Insert:

```sql
INSERT INTO users(name)
VALUES ('Fahim');
```

Check:

```sql
SELECT * FROM users;
```

---

# Observe WAL Internals

Every insert:

```sql
INSERT INTO users(name)
VALUES ('John');
```

Internally:

```text
Insert Query
    |
Memory Buffer
    |
WAL Buffer
    |
Disk WAL File
    |
Replica Replay
```

---

# Phase 6: FastAPI Application

## Install Python Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

Install packages:

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary
```

Save:

```bash
pip freeze > requirements.txt
```

---

# Create database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

WRITE_DB = "postgresql://postgres:admin123@localhost:5432/appdb"
READ_DB = "postgresql://postgres:admin123@localhost:5432/appdb"

write_engine = create_engine(WRITE_DB)
read_engine = create_engine(READ_DB)

WriteSession = sessionmaker(bind=write_engine)
ReadSession = sessionmaker(bind=read_engine)
```

---

# Create models.py

```python
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
```

---

# Create main.py

```python
from fastapi import FastAPI
from database import WriteSession
from models import User

app = FastAPI()

@app.post("/users")
def create_user(name: str):

    db = WriteSession()

    user = User(name=name)

    db.add(user)
    db.commit()

    return {"message": "created"}
```

---

# Read Endpoint

```python
from database import ReadSession

@app.get("/users")
def get_users():

    db = ReadSession()

    users = db.query(User).all()

    return users
```

---

# Run Application

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

---

# Request Flow

## Write

```text
POST /users
      |
      v
 FastAPI
      |
      v
 Primary DB
      |
      v
 WAL
      |
      v
 Replica
```

---

## Read

```text
GET /users
      |
      v
 FastAPI
      |
      v
 Replica DB
```

---

# Production Scenario

At Amazon:

```text
100k API requests/sec
```

Reads:

```text
Replica Cluster
```

Writes:

```text
Primary Cluster
```

Load balancer decides:

```text
SELECT → Replica

INSERT/UPDATE → Primary
```

---

# Troubleshooting Lab

## Replica not updating

Check:

```sql
SELECT * FROM pg_stat_replication;
```

---

## Check replica status

On replica:

```sql
SELECT pg_is_in_recovery();
```

Expected:

```text
t
```

If:

```text
f
```

Replica became primary.

---

## Replication lag

```sql
SELECT
client_addr,
state,
sync_state
FROM pg_stat_replication;
```

---

# Monitoring Commands

```bash
docker logs pg-primary
docker logs pg-replica
```

```sql
SELECT * FROM pg_stat_replication;
```

```sql
SELECT * FROM pg_stat_wal_receiver;
```

---

# Production Best Practices

✅ Use connection pooling

✅ Use PgBouncer

✅ Use replication slots

✅ Monitor lag

✅ Use backups

✅ Test failover

❌ Never allow application writes to replicas

❌ Never use replicas for transactions requiring strong consistency

---

# Real Production Architecture

```text
                      HAProxy
                          |
                +---------+---------+
                |                   |
                v                   v

         +-------------+     +-------------+
         | FastAPI App |     | FastAPI App |
         +-------------+     +-------------+
                |                   |
                +---------+---------+
                          |
                    PgBouncer
                          |
             +------------+------------+
             |                         |
             v                         v

      +-------------+          +-------------+
      | Primary DB  |--------->| Replica DB  |
      +-------------+          +-------------+
```

# Interactive Lab

Before we continue to a **fully automated Docker Compose setup with Primary + Replica + FastAPI + PgAdmin**, execute only this:

```bash
mkdir postgres-fastapi-lab
cd postgres-fastapi-lab
mkdir app

docker network create pg-net

docker run -d \
--name pg-primary \
--network pg-net \
-e POSTGRES_PASSWORD=admin123 \
-p 5432:5432 \
postgres:16

docker exec -it pg-primary psql -U postgres
```

Then run:

```sql
SHOW wal_level;

CREATE ROLE replicator
WITH REPLICATION LOGIN PASSWORD 'replica123';
```

Paste the output here, and we'll proceed to the fully automated production-grade setup using Docker Compose.
