# AI Task Service

Микросервис для управления AI-задачами.

## Запуск

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docker:

```bash
docker build -t ai-task-service .
docker run -p 8000:8000 ai-task-service
```
