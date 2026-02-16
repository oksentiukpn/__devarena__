
🐳 Docker Compose Cheatsheet
🚀 Application Lifecycle
Manage the running state of your containerized application.
| Action | Command | Notes |
|---|---|---|
| Start App | docker compose up | Starts containers in the foreground. |
| Rebuild | docker compose up --build | Use after pip install or Dockerfile changes. |
| Stop App | docker compose down | Stops and removes containers/networks. |
🗄️ Database Management
> Note: These commands are optional. You only need to run migrations if you have modified your Python data models (e.g., models.py).
> 
1. Create Migration File
Generates a new migration script based on your model changes.
docker compose exec web flask db migrate -m "describe_your_change_here"

2. Apply Changes
Applies the pending migration script to the actual database.
docker compose exec web flask db upgrade

🌐 Access
Once the app is running, you can access it here:
 * HTTP: http://localhost:80
 * HTTPS: https://localhost:443
