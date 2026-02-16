# 🐳 Docker Compose Cheatsheet

A quick and practical reference for managing your containerized application using **Docker Compose**.
Use this guide to start, stop, rebuild, and manage your database with confidence. 🚀

---

## 🚀 Application Lifecycle

Control the running state of your app and its services.

| Action       | Command                     | Description                                                                      |
| ------------ | --------------------------- | -------------------------------------------------------------------------------- |
| ▶️ Start App | `docker compose up`         | Starts containers in the foreground.                                             |
| 🔄 Rebuild   | `docker compose up --build` | Rebuilds images before starting (use after `pip install` or Dockerfile changes). |
| ⏹️ Stop App  | `docker compose down`       | Stops and removes containers, networks, and default volumes.                     |

### 💡 Pro Tips

* Add `-d` to run in detached mode:

  ```bash
  docker compose up -d
  ```
* View logs:

  ```bash
  docker compose logs -f
  ```

---

## 🗄️ Database Management

> ⚠️ **Note:**
> You only need to run migrations if you’ve modified your Python data models (e.g., `models.py`).

### 1️⃣ Create a Migration File

Generates a new migration script based on model changes:

```bash
docker compose exec web flask db migrate -m "describe_your_change_here"
```

✔️ This compares your current models with the database schema and creates a migration file.

---

### 2️⃣ Apply Migration Changes

Applies pending migrations to the database:

```bash
docker compose exec web flask db upgrade
```

✔️ This updates your actual database schema safely and incrementally.

---

## 🌐 Application Access

Once the app is running, access it in your browser:

* 🌍 **HTTP:** [http://localhost:80](http://localhost:80)
* 🔐 **HTTPS:** [https://localhost:443](https://localhost:443)

---

## 🧰 Common Workflow Example

```bash
# Start the app
docker compose up -d

# If models changed
docker compose exec web flask db migrate -m "add_new_field"
docker compose exec web flask db upgrade

# Stop when finished
docker compose down
```

---

## ✅ Summary

* Use `up` to start your services
* Use `--build` after dependency or Dockerfile changes
* Run migrations only when models change
* Access the app via localhost

Happy coding! 🐳🚀
