<div align="center">

# ⚔️ DevArena

### Level Up Your Code Through Peer Review

[![Deploy](https://github.com/oksentiukpn/__devarena__/actions/workflows/deploy.yml/badge.svg)](https://github.com/oksentiukpn/__devarena__/actions/workflows/deploy.yml)

**DevArena** is a community-driven platform where developers share projects, get constructive peer reviews, and compete in real-time coding battles. Whether you're looking to sharpen your skills, showcase your architecture, or prove yourself in a head-to-head challenge — this is your arena.

[Live Demo](https://devarena.pp.ua) · [Report Bug](https://github.com/oksentiukpn/__devarena__/issues)

</div>

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Setup & Installation](#-setup--installation)
- [Environment Variables](#-environment-variables)
- [Docker Compose Cheatsheet](#-docker-compose-cheatsheet)
- [Database Management](#-database-management)
- [CLI Commands](#-cli-commands)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Project Structure](#-project-structure)
- [License](#-license)

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📰 **Project Feed** | Share code snippets or full project architectures with syntax highlighting. A smart feed algorithm prioritizes posts in languages you use most. |
| 💬 **Constructive Peer Review** | Request specific feedback — Code Quality, Performance, Architecture, or Security — and receive inline comments from the community. |
| ⚔️ **Coding Battles** | Compete head-to-head in real-time coding challenges. Set a time limit, language, and difficulty, then let the community vote on the cleanest solution. |
| 🏆 **Reputation & Leaderboards** | Earn points for participating in battles and receiving positive reactions on your posts. |
| 🔐 **Authentication** | Secure email/password registration alongside seamless Google OAuth 2.0 login. |
| 📧 **Daily Prompts** | Opt-in for daily email challenges delivered via Resend API to keep your coding streak alive. |
| 🗺️ **SEO Ready** | Auto-generated `sitemap.xml` and `robots.txt` for search engine discoverability. |

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.10, Flask, SQLAlchemy ORM, Flask-Migrate, Flask-WTF |
| **Frontend** | HTML / Jinja2, Tailwind CSS v4, Vanilla JavaScript, Highlight.js |
| **Database** | PostgreSQL 18 |
| **Infrastructure** | Docker (multi-stage build), Docker Compose, Nginx (reverse proxy + SSL + rate limiting), Gunicorn |
| **Auth** | Session-based auth, Google OAuth 2.0 (Authlib) |
| **Email** | Resend API |
| **CI/CD** | GitHub Actions → SSH deploy to VPS |

---

## 🏗️ Architecture

```
/dev/null/architecture.txt#L1-15
                    ┌──────────────┐
                    │   Browser    │
                    └──────┬───────┘
                           │ HTTPS (443)
                    ┌──────▼───────┐
                    │    Nginx     │  Rate Limiting · SSL Termination
                    │  (Alpine)    │  Security Headers · Proxy
                    └──────┬───────┘
                           │ HTTP (5000)
                    ┌──────▼───────┐
                    │  Gunicorn    │  5 Workers
                    │  Flask App   │  Blueprints: main, auth, challenges
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ PostgreSQL   │  Users · Posts · Battles · Votes
                    │   (Alpine)   │  Reactions · Comments
                    └──────────────┘
```

---

## 🚀 Setup & Installation

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

### 1. Clone the Repository

```
git clone https://github.com/oksentiukpn/__devarena__.git
cd __devarena__
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```
# Flask
SECRET_KEY=your_super_secret_key_here
FLASK_DEBUG=True

# PostgreSQL
POSTGRES_USER=devarena_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=devarena_db

# Google OAuth 2.0
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Email (Resend)
EMAIL_API_KEY=your_resend_api_key
```

> **Note:** `DATABASE_URL` is constructed automatically by Docker Compose from the Postgres credentials above.

### 3. Generate Local SSL Certificates

Nginx requires SSL certificates. For local development, generate self-signed ones:

```
mkdir -p nginx/certs
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 -keyout nginx/certs/key.pem \
  -out nginx/certs/cert.pem -subj "/CN=localhost"
```
## ! But cloudflare certs recommended for production !
### 4. Build & Start

```
docker compose up -d --build
```

This single command will:
1. **Build Tailwind CSS** — compiles and minifies your styles in a Node.js Alpine container
2. **Build the Python image** — installs dependencies, copies the compiled CSS
3. **Start all services** — PostgreSQL, Flask (Gunicorn), and Nginx
4. **Run database migrations** — automatically via `entrypoint.sh`

### 5. Open in Browser

| Protocol | URL |
|---|---|
| 🔐 HTTPS | [https://localhost](https://localhost) |
| 🌐 HTTP | [http://localhost](http://localhost) *(redirects to HTTPS)* |

> Accept the self-signed certificate warning in your browser for local development.

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Flask secret key for session signing and CSRF protection |
| `FLASK_DEBUG` | ❌ | Set to `True` for development mode (default: `False`) |
| `POSTGRES_USER` | ✅ | PostgreSQL username |
| `POSTGRES_PASSWORD` | ✅ | PostgreSQL password |
| `POSTGRES_DB` | ✅ | PostgreSQL database name |
| `GOOGLE_CLIENT_ID` | ✅ | Google OAuth 2.0 Client ID |
| `GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth 2.0 Client Secret |
| `EMAIL_API_KEY` | ✅ | Resend API key for daily prompt emails |

---

## 🐳 Docker Compose Cheatsheet

| Action | Command | Description |
|---|---|---|
| ▶️ Start | `docker compose up -d` | Start all containers in background |
| 🔄 Rebuild | `docker compose up -d --build` | Rebuild images and restart (after dependency or Dockerfile changes) |
| ⏹️ Stop | `docker compose down` | Stop and remove containers and networks |
| 📜 Logs | `docker compose logs -f web` | Follow real-time Flask application logs |
| 🐚 Shell | `docker compose exec web bash` | Open a shell inside the web container |

---

## 🗄️ Database Management

> ⚠️ Only run migrations if you've modified models in `app/models.py`.

**Create a migration** (after modifying models):

```
docker compose exec web flask db migrate -m "describe_your_change_here"
```

**Apply pending migrations:**

```
docker compose exec web flask db upgrade
```

**Rollback last migration:**

```
docker compose exec web flask db downgrade
```

---

## 📧 CLI Commands

DevArena includes custom Flask CLI commands for managing the daily prompt email system.

**Send daily prompt to all subscribed users:**

```
docker compose exec web flask send-daily-prompt
```

**Send prompt to a specific user (interactive):**

```
docker compose exec web flask send-prompt-to
```

You will be prompted to enter the user's email address.

---

## 🚢 CI/CD Pipeline

The project uses **GitHub Actions** for automated deployments. On every push to `main`:

1. Code is checked out
2. SSH connection is established to the production VPS
3. Latest code is pulled via `git pull`
4. Containers are rebuilt and restarted with `docker compose up -d --build`

Required GitHub Secrets: `HOST`, `USERNAME`, `KEY`

---

## 📁 Project Structure

```
/dev/null/tree.txt#L1-43
__devarena__/
├── .github/
│   └── workflows/
│       └── deploy.yml            # GitHub Actions CI/CD
├── app/
│   ├── auth/
│   │   ├── routes.py             # Login, Register, Google OAuth, Logout
│   │   └── utils.py              # @login_required decorator
│   ├── challenges/
│   │   ├── __init__.py           # Challenges Blueprint
│   │   └── routes.py             # Battle CRUD, Arena, Voting, Review
│   ├── main/
│   │   ├── form.py               # WTForms (PostForm, BattleForm)
│   │   ├── routes.py             # Feed, Posts, Profile, SEO routes
│   │   └── search_engine.py      # Search prototype
│   ├── static/
│   │   ├── src/input.css         # Tailwind CSS source
│   │   └── css/output.css        # Compiled CSS (generated)
│   ├── templates/
│   │   ├── auth/                 # Login & Register pages
│   │   ├── email/                # Daily prompt email template
│   │   ├── main/                 # Profile, Arena, Review, etc.
│   │   ├── base.html             # Base layout
│   │   ├── feed.html             # Project feed
│   │   ├── battles.html          # Battles listing
│   │   └── post.html             # Create post
│   ├── __init__.py               # App factory (create_app)
│   └── models.py                 # SQLAlchemy models
├── migrations/                   # Flask-Migrate (Alembic)
├── nginx/
│   ├── nginx.conf                # Nginx config (SSL, rate limiting)
│   └── certs/                    # SSL certificates (gitignored)
├── config.py                     # App configuration from env
├── docker-compose.yml            # Service orchestration
├── Dockerfile                    # Multi-stage build (Node + Python)
├── entrypoint.sh                 # Wait for DB + migrate + start Gunicorn
├── requirements.txt              # Python dependencies
├── package.json                  # Node.js / Tailwind CSS
└── run.py                        # App entry point + CLI commands
```

---

## 🔒 Security Highlights

- **CSRF Protection** — Flask-WTF across all forms
- **Rate Limiting** — Nginx: 50 req/s general, 1 req/s on auth routes
- **Security Headers** — `X-Frame-Options`, `X-XSS-Protection`, `X-Content-Type-Options`, `HSTS`
- **Secure Sessions** — `HttpOnly`, `Secure`, `SameSite=Lax` cookie flags
- **Password Hashing** — Werkzeug's `generate_password_hash` / `check_password_hash`
- **Hidden Files Blocked** — Nginx denies access to `.env`, `.git`, etc.
- **ProxyFix Middleware** — Correct handling of `X-Forwarded-Proto` behind reverse proxy

---

## 📄 License

This project is proprietary and confidential unless otherwise specified.

---

<div align="center">

**Built with ☕ and competitive spirit.**

⭐ Star the repo if you like the project!

</div>
