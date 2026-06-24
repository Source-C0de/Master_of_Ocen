Core Architecture

Celery architecture has 4 main components.

![alt text](image.png)

1. Broker (Message Queue)

The broker is the middleman.

It stores tasks temporarily until workers pick them up.

Popular Brokers
Redis
RabbitMQ
Broker Analogy

Think of it like:

Task inbox
Job queue
Delivery center

API places tasks there.

Workers collect tasks from there.

Example

API:

send_email.delay(user.id)

Task goes into Redis queue.

Worker later executes:

send_email(user.id)


2. Worker

Worker is the actual executor.

It continuously listens to broker queues.

When task arrives:

Worker -> picks task -> executes task
Worker Responsibilities
Execute tasks
Retry failed jobs
Run tasks concurrently
Process multiple queues
Example Worker Command
celery -A app worker --loglevel=info

This starts a worker process.