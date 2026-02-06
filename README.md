# 📚 Study-Notion — AI-Powered Online Learning Platform

> A full-featured Learning Management System (LMS) built with Flask, powered by Google Gemini AI, with YouTube playlist auto-import, interactive quizzes, lecture summaries, and role-based dashboards for students & instructors.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?logo=bootstrap&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Google%20Gemini-AI-4285F4?logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 Overview

**Study-Notion** is a full-stack web application that makes education more accessible, interactive, and personalized. It supports two distinct user roles — **Students** and **Instructors** — each with dedicated dashboards and features.

Instructors can create courses manually or **auto-import an entire YouTube playlist** to instantly generate a course with chapters, video embeds, descriptions, and durations. Students can browse courses, watch embedded lectures, take AI-generated quizzes, and get AI-powered lecture summaries and study notes.

---

## ✨ Features

### 🎓 Student Features
- **Course Catalog** — Browse and filter courses by category (10 pre-seeded categories)
- **Course Enrollment** — One-click enrollment into published courses
- **Video Player** — Embedded YouTube video playback with progress tracking
- **AI-Generated Quizzes** — Auto-generated MCQ quizzes from lecture content using Google Gemini
- **AI Lecture Summaries** — One-click AI-powered lecture summarization
- **AI Study Notes** — Automatically generated study notes from lecture content
- **Progress Tracking** — Per-lecture completion tracking with resume support
- **User Profile** — Profile management with avatar upload

### 👨‍🏫 Instructor Features
- **Instructor Dashboard** — Overview with stats (total courses, enrollments, avg. progress)
- **Course Builder** — Full CRUD for Courses → Sections → Lectures hierarchy
- **YouTube Playlist Import** — Paste a playlist URL to auto-create a course with:
  - Auto-extracted video titles, descriptions, durations, and thumbnails
  - Selectable videos with preview before import
  - Automatic section and lecture creation
- **Course Publishing** — Draft/publish workflow for courses
- **Media Manager** — Upload and manage images and documents
- **Section & Lecture Reordering** — Drag-and-drop ordering via AJAX
- **Quiz Management** — Create, edit, and add questions to quizzes

### 🔐 Authentication & Authorization
- Secure registration with role selection (Student / Instructor)
- Login with session-based authentication (Flask-Login)
- Password hashing with Werkzeug
- Role-based access control with `@instructor_required` decorator
- CSRF protection on all forms (Flask-WTF)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, Flask 3.1, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate |
| **Database** | SQLite (dev), PostgreSQL-ready (psycopg2-binary included) |
| **AI Engine** | Google Gemini API (1.5 Flash / 1.5 Pro) with offline fallbacks |
| **Frontend** | Jinja2 Templates, Bootstrap 5.3, Bootstrap Icons, Custom CSS |
| **YouTube Integration** | yt-dlp for playlist metadata extraction |
| **File Uploads** | Werkzeug secure file handling with UUID naming |
| **Authentication** | Flask-Login sessions, Werkzeug password hashing |
| **Form Handling** | WTForms with CSRF protection |
| **Environment** | python-dotenv for config management |

---

## 📁 Project Structure

```
Study-Notion/
├── main.py                  # App factory, DB init, seed data
├── routes.py                # All 40 route handlers (1600+ lines)
├── models.py                # 14 SQLAlchemy models
├── forms.py                 # 11 WTForms form classes
├── ai_services.py           # Gemini AI integration (quiz, summary, notes)
├── utils.py                 # File upload, YouTube helpers, playlist fetch
├── config.py                # App configuration
├── extensions.py            # Flask extension instances
├── filters.py               # Custom Jinja2 template filters
├── pyproject.toml           # Python project dependencies
├── requirements.txt         # Pinned pip dependencies for deployment
├── pythonanywhere_wsgi.py   # Reference WSGI config for PythonAnywhere
├── serve.py                 # Production launcher (0.0.0.0:5000)
├── start_server.bat         # Windows auto-restart batch script
├── install_service.bat      # NSSM Windows service installer
├── .env                     # Environment variables (API keys)
├── data/
│   └── courses.json         # Seed data (10 categories)
├── instance/
│   └── app.db               # SQLite database file
├── static/
│   ├── css/style.css         # Custom dark-theme CSS (570+ lines)
│   ├── js/main.js            # Client-side JavaScript
│   └── uploads/              # User-uploaded files
│       ├── course_thumbnails/
│       ├── profile_pics/
│       └── media/
├── templates/
│   ├── base.html             # Base layout with navbar & footer
│   ├── index.html            # Landing page
│   ├── login.html            # Login form
│   ├── register.html         # Registration with role selection
│   ├── profile.html          # User profile page
│   ├── course_catalog.html   # Browse courses with category filter
│   ├── course_details.html   # Course overview + enrollment
│   ├── video_player.html     # Lecture video player
│   ├── quiz.html             # AI-generated quiz interface
│   ├── study_notes.html      # AI study notes display
│   ├── lecture_summary.html  # AI lecture summary display
│   ├── view_course.html      # Student course module view
│   ├── view_module.html      # Module lessons list
│   ├── view_lesson.html      # Lesson content viewer
│   ├── take_quiz.html        # Quiz-taking interface
│   ├── edit_module.html      # Module editor
│   ├── edit_lesson.html      # Lesson editor
│   ├── edit_quiz.html        # Quiz editor
│   ├── add_quiz_question.html # Add quiz questions
│   └── instructor/
│       ├── dashboard.html    # Instructor stats & overview
│       ├── courses.html      # Instructor course list
│       ├── course_editor.html # Course create/edit form
│       ├── section_editor.html # Section create/edit
│       ├── lecture_editor.html # Lecture create/edit
│       ├── import_playlist.html # YouTube playlist importer
│       └── media_manager.html # File upload manager
└── logs/
    └── websiteenhancer.log   # Application logs
```

---

## � File Reference

### Backend (Python)

| File | Purpose |
|---|---|
| **`main.py`** | Application entry point. Contains `create_app()` factory function that initializes Flask, registers extensions (SQLAlchemy, Flask-Login, Flask-Migrate), registers the blueprint, **auto-creates the database directory** from the SQLite URI, creates tables via `db.create_all()`, and seeds initial categories from `data/courses.json` using `load_initial_data()`. The module-level `app = create_app()` is guarded inside `if __name__ == '__main__'` so it doesn't execute during WSGI import on production servers. |
| **`routes.py`** | The core routing module (**1,600+ lines**). Defines a single Flask Blueprint `main_bp` with all **40 route handlers** organized into: public routes (landing, catalog, login, register), student routes (enrollment, video player, AI features, quiz-taking), and instructor routes (dashboard, course CRUD, section/lecture management, YouTube import, media manager, AJAX reorder endpoints). Also includes the `@instructor_required` decorator for role-based access control. |
| **`models.py`** | Defines **14 SQLAlchemy ORM models** — `User`, `Category`, `Course`, `Section`, `Lecture`, `Module`, `Lesson`, `Enrollment`, `LectureProgress`, `UserProgress`, `Quiz`, `QuizQuestion`, `QuizOption`, `QuizAttempt`, and `Media`. The `User` model integrates Flask-Login's `UserMixin` and includes Werkzeug password hashing methods (`set_password()`, `check_password()`). Also contains the `load_initial_data()` function that seeds the database with categories from `data/courses.json`. |
| **`forms.py`** | Contains **11 WTForms form classes** with CSRF protection via Flask-WTF: `LoginForm`, `RegistrationForm` (with role selection), `ProfileForm` (with avatar upload), `SearchForm`, `CourseForm`, `SectionForm`, `LectureForm` (with video URL and rich text content), `MediaUploadForm`, `QuizGeneratorForm`, `ModuleForm`, `LessonForm`, `QuizForm`, and `QuizQuestionForm`. Each form defines validators for data integrity (required fields, email format, length constraints, file type restrictions). |
| **`ai_services.py`** | Google Gemini AI integration module (**470 lines**). Exposes three main functions: `generate_quiz()` — creates MCQ quizzes from lecture content, `generate_lecture_summary()` — produces key-point summaries, and `generate_study_notes()` — builds structured study notes. Each function attempts the Gemini API (1.5 Flash → 1.5 Pro fallback) and gracefully falls back to offline-generated content if no API key is set or the API call fails. Includes JSON response parsing, prompt engineering, and error handling with logging. |
| **`utils.py`** | Utility module (**207 lines**). Provides: `save_uploaded_file()` — saves files with UUID renaming to prevent collisions, `allowed_file()` — validates file extensions, `extract_youtube_id()` — extracts video IDs from various YouTube URL formats (watch, short, embed), and `fetch_playlist_data()` — uses **yt-dlp** to extract full metadata (titles, descriptions, durations, thumbnails, video IDs) from a YouTube playlist URL without downloading any video content. |
| **`config.py`** | Application configuration class. Loads environment variables from `.env` via `python-dotenv`. Computes an **absolute path** for the SQLite database (`instance/app.db` relative to the project root) so it works reliably on any platform including PythonAnywhere. Defines: `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, SQLAlchemy pool settings with `pool_recycle` and `pool_pre_ping`, upload folder paths (`course_thumbnails/`, `profile_pics/`, `media/`), allowed file extensions for images (jpg, jpeg, png) and documents (pdf, doc, docx, ppt, pptx), and file size limits (16 MB general, 2 MB images, 10 MB documents). |
| **`extensions.py`** | Initializes Flask extension instances **without binding them to the app** (factory pattern). Creates `db` (SQLAlchemy), `login_manager` (Flask-Login), and `migrate` (Flask-Migrate) objects that are later bound in `main.py` via `init_app()`. This avoids circular imports between modules. |
| **`filters.py`** | Registers custom Jinja2 template filters. Currently provides `nl2br` — converts newline characters (`\n`) to HTML `<br>` tags using `markupsafe.Markup` for safe rendering. Filters are registered via `init_app(app)` called from `main.py`. |
| **`pyproject.toml`** | Python project metadata and dependency manifest. Lists all required packages (Flask, SQLAlchemy, Flask-Login, Flask-WTF, google-generativeai, yt-dlp, etc.) and their minimum versions. Used by `pip` or `uv` for dependency installation. |

### Data & Configuration

| File | Purpose |
|---|---|
| **`data/courses.json`** | Seed data file containing **10 course categories**: Web Development, Data Science, Machine Learning & AI, Mobile Development, DevOps & Cloud, Cybersecurity, Database Management, Programming Languages, Software Engineering, and UI/UX Design. Each category has a name and description. Loaded automatically on first run by `load_initial_data()`. |
| **`.env`** | Environment variables file (not committed to git). Stores `SECRET_KEY` and `GEMINI_API_KEY`. Optionally accepts `DATABASE_URL` to override the default SQLite path (e.g., for PostgreSQL). The app works fully without `GEMINI_API_KEY` — AI features use offline fallbacks. |
| **`instance/app.db`** | SQLite database file auto-created on first run. Stores all application data: users (with hashed passwords), courses, sections, lectures, enrollments, quiz data, progress records, and media references. Located in the `instance/` folder (auto-created by `main.py`). |

### Deployment & Hosting

| File | Purpose |
|---|---|
| **`requirements.txt`** | Pinned pip dependencies generated from the virtual environment. Used by PythonAnywhere and other hosts to install exact package versions. Contains 16 packages including Flask, SQLAlchemy, yt-dlp, google-generativeai, etc. |
| **`pythonanywhere_wsgi.py`** | Reference WSGI configuration file for PythonAnywhere deployment. Copy its contents into the PythonAnywhere WSGI config file. Sets `sys.path`, environment variables, and creates the `application` object via `create_app()`. |
| **`serve.py`** | Production launcher script. Imports `create_app()` and runs the Flask server on `0.0.0.0:5000` with debug disabled. Used for LAN-accessible local hosting. |
| **`start_server.bat`** | Windows batch script for 24/7 local hosting. Runs the Flask server in a loop that auto-restarts on crash with a 5-second delay. |
| **`install_service.bat`** | Windows batch script that uses NSSM (Non-Sucking Service Manager) to install the Flask app as a Windows service that starts automatically on boot. |

### Static Assets

| File | Purpose |
|---|---|
| **`static/css/style.css`** | Custom dark-theme stylesheet (**570+ lines**). Defines CSS custom properties for theming (colors, gradients, spacing), styled components for course cards, video player, quiz interface, dashboards, profile page, and responsive breakpoints. Builds on top of Bootstrap 5.3 with a GitHub-inspired dark color palette. |
| **`static/js/main.js`** | Client-side JavaScript. Handles: auto-dismissing flash messages, file input preview for image uploads, AJAX-based section/lecture reorder drag-and-drop, quiz form validation, video progress tracking via `postMessage`, loading overlays for async operations, and dynamic UI interactions (course filtering, modal controls). |
| **`static/uploads/`** | User-uploaded file storage with three subdirectories: `course_thumbnails/` (course cover images), `profile_pics/` (user avatars), and `media/` (instructor-uploaded documents and images via the media manager). Files are saved with UUID-prefixed names to prevent collisions. |

### Templates

| Template | Purpose |
|---|---|
| **`base.html`** | Master layout template. Defines HTML head (Bootstrap 5.3 CSS, Bootstrap Icons CDN, custom CSS), responsive navbar with role-based navigation links, flash message display, content block, and footer. All other templates extend this via `{% extends "base.html" %}`. |
| **`index.html`** | Landing page. Displays hero section with call-to-action, featured/latest courses grid, platform statistics, and category quick-links. Accessible to all visitors. |
| **`login.html`** | Login form page. Renders `LoginForm` with username and password fields, "Remember Me" checkbox, and link to registration. Handles form validation errors. |
| **`register.html`** | Registration page. Renders `RegistrationForm` with username, email, password/confirm, first/last name fields, and **role selection radio buttons** (Student or Instructor) using custom HTML radio inputs for proper styling. |
| **`profile.html`** | User profile management page. Displays current user info with avatar, renders `ProfileForm` for editing name/email, and allows profile picture upload with image preview. |
| **`course_catalog.html`** | Course browsing page. Shows all published courses as cards with thumbnails, displays a category filter dropdown populated from the database, supports text search, and shows enrollment count per course. |
| **`course_details.html`** | Individual course overview. Shows course title, description, instructor info, section/lecture count, and an "Enroll" button (or "Continue Learning" for enrolled students). Lists all sections and lectures with durations. |
| **`video_player.html`** | Lecture video player page. Embeds YouTube videos via iframe, displays lecture title/description/content, shows progress controls, and provides links to AI features (generate quiz, study notes, lecture summary). Tracks video watch position. |
| **`quiz.html`** | AI-generated quiz display. Shows multiple-choice questions generated by Gemini AI from lecture content, with radio-button answer options and a submit button. Displays score results after submission. |
| **`study_notes.html`** | AI study notes page. Displays structured study notes generated by Gemini AI from lecture content, formatted with headings, bullet points, and key concept highlights. |
| **`lecture_summary.html`** | AI lecture summary page. Shows a concise AI-generated summary of the lecture's key points and takeaways. |
| **`view_course.html`** | Student course view. Lists all modules within an enrolled course, showing completion progress for each module and overall course progress percentage. |
| **`view_module.html`** | Module detail view. Lists all lessons within a module with completion status indicators and links to individual lessons and quizzes. |
| **`view_lesson.html`** | Lesson content viewer. Renders the full lesson content with formatted text, and provides navigation to next/previous lessons within the module. |
| **`take_quiz.html`** | Quiz-taking interface. Presents quiz questions one at a time or all at once with radio-button options, handles form submission, calculates and displays the score with correct/incorrect answer feedback. |
| **`edit_module.html`** | Module editor form (instructor). Renders `ModuleForm` for creating or editing a module's title, description, and order within a course. |
| **`edit_lesson.html`** | Lesson editor form (instructor). Renders `LessonForm` for creating or editing a lesson's title, content (rich text), and display order. |
| **`edit_quiz.html`** | Quiz editor page (instructor). Renders `QuizForm` for editing quiz title/description, lists existing questions with edit/delete options, and links to the add-question page. |
| **`add_quiz_question.html`** | Quiz question form (instructor). Renders `QuizQuestionForm` for adding new multiple-choice questions — input fields for question text, options (one per line), and the correct option number. |

### Instructor Templates (`templates/instructor/`)

| Template | Purpose |
|---|---|
| **`dashboard.html`** | Instructor dashboard. Shows stats cards (total courses, total enrollments, average student progress), lists recent courses with quick-action buttons, and provides prominent "Create New Course" and "Import YouTube Playlist" buttons with inline SVG icons. |
| **`courses.html`** | Instructor course list. Displays all courses created by the logged-in instructor as cards with publish status badges, enrollment counts, and action buttons (edit, publish/unpublish, delete). |
| **`course_editor.html`** | Course create/edit form. Renders `CourseForm` with title, description, category dropdown, thumbnail upload with preview, and publish toggle. Used for both new course creation and editing existing courses. |
| **`section_editor.html`** | Section create/edit form. Renders `SectionForm` for adding or editing a section within a course. Shows the parent course context and handles section ordering. |
| **`lecture_editor.html`** | Lecture create/edit form. Renders `LectureForm` with title, description, YouTube video URL input (with embed preview), rich text content editor, and duration field. Used for both creating and editing lectures within a section. |
| **`import_playlist.html`** | YouTube playlist importer (**350 lines**). Two-step flow: Step 1 — input a YouTube playlist URL and fetch metadata; Step 2 — preview all videos as selectable cards with thumbnails, titles, durations, and descriptions, then import selected videos as a new course. Uses inline SVG YouTube icon and shows loading overlay during fetch. |
| **`media_manager.html`** | File upload and management page. Renders `MediaUploadForm` for uploading images and documents, displays all uploaded files in a grid/list with file type icons, file size, upload date, and delete buttons. Files are organized by type. |

### Logs

| File | Purpose |
|---|---|
| **`logs/websiteenhancer.log`** | Application log file. Records server events, errors, AI API call results, and debug information. Generated automatically by Python's `logging` module configured in the application. |

---

## �🗃️ Database Schema (14 Models)

```
User ─────────────┬──> Enrollment <──── Course ──> Section ──> Lecture
  │                │                      │                       │
  │                │                      ├──> Module ──> Lesson  │
  │                │                      │      └──> Quiz        │
  │                │                      └──> Category           │
  ├──> Media       │                                              │
  ├──> QuizAttempt │                                              │
  └──> UserProgress                       Quiz ──> QuizQuestion ──> QuizOption
                                            │
                                          LectureProgress
```

| Model | Description |
|---|---|
| `User` | Students & instructors with hashed passwords, roles, profile pics |
| `Category` | Course categories (10 pre-seeded: Web Dev, Data Science, ML, etc.) |
| `Course` | Courses with title, description, thumbnail, publish status |
| `Section` | Ordered sections within a course |
| `Lecture` | Video lectures with YouTube embed support, duration tracking |
| `Module` | Alternative module-based course structure |
| `Lesson` | Lessons within modules |
| `Enrollment` | Student-Course enrollment records |
| `LectureProgress` | Per-user lecture watch position & completion |
| `UserProgress` | Module/lesson completion tracking |
| `Quiz` | Quizzes linked to lectures or modules |
| `QuizQuestion` | Multiple-choice questions |
| `QuizOption` | Answer options with correct flag |
| `QuizAttempt` | Student quiz scores & timestamps |
| `Media` | Uploaded files (images, documents) |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/RohanAnil1/Study-Notion.git
cd Study-Notion

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-google-gemini-api-key
```

> **Note:** The app works fully without a Gemini API key — AI features gracefully fall back to offline-generated content. The SQLite database is auto-created at `instance/app.db` — no `DATABASE_URL` needed.

### Run the Application

```bash
python main.py
```

The app will be available at **http://127.0.0.1:5000**

On first run, the database is auto-created and seeded with 10 course categories.

---

## ☁️ Deploy to PythonAnywhere (Free)

This app can be deployed for **free** on [PythonAnywhere](https://www.pythonanywhere.com) with **zero code changes**.

### Step 1 — Create Account
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com) and sign up for a **free Beginner** account
2. Your app will be available at `https://yourusername.pythonanywhere.com`

### Step 2 — Upload Code
Open a **Bash console** from the Dashboard and run:
```bash
git clone https://github.com/RohanAnil1/Study-Notion.git
cd Study-Notion
```

### Step 3 — Create Virtual Environment
```bash
mkvirtualenv --python=/usr/bin/python3.12 studynotion
pip install -r requirements.txt
```

### Step 4 — Configure Web App
1. Go to the **Web** tab → click **Add a new web app**
2. Choose **Manual configuration** → **Python 3.12**
3. Set **Source code** directory: `/home/yourusername/Study-Notion`
4. Set **Virtualenv**: `/home/yourusername/.virtualenvs/studynotion`

### Step 5 — Edit WSGI File
Click the **WSGI configuration file** link on the Web tab and replace its entire contents with:
```python
import sys
import os

project_home = '/home/yourusername/Study-Notion'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['SECRET_KEY'] = 'change-this-to-a-real-secret-key'
os.environ['GEMINI_API_KEY'] = ''  # Optional: add your Gemini API key

from main import create_app
application = create_app()
```
> ⚠️ Replace `yourusername` with your actual PythonAnywhere username.
> 
> **Note:** No `DATABASE_URL` is needed — the app automatically uses an absolute path to `instance/app.db` relative to the project root, and creates the directory if it doesn't exist.

### Step 6 — Static Files
On the **Web** tab, add a static file mapping:
| URL | Directory |
|---|---|
| `/static` | `/home/yourusername/Study-Notion/static` |

### Step 7 — Launch!
Click the green **Reload** button on the Web tab. Your app is now live at:
```
https://yourusername.pythonanywhere.com
```

### Updating After Changes
```bash
# In a PythonAnywhere Bash console:
cd ~/Study-Notion
git pull
# Then click "Reload" on the Web tab
```

> A reference WSGI file is also included at `pythonanywhere_wsgi.py` in the project root.

---

## 🔗 API Routes (40 Endpoints)

### Public Routes
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Landing page with featured courses |
| GET | `/courses` | Course catalog with category filter |
| GET | `/course/<id>` | Course details & enrollment |
| GET/POST | `/register` | User registration |
| GET/POST | `/login` | User login |
| GET | `/logout` | User logout |

### Student Routes (Login Required)
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/profile` | User profile management |
| POST | `/enroll/<id>` | Enroll in a course |
| GET | `/lecture/<id>` | Video player with lecture content |
| POST | `/update-progress` | Save video watch progress |
| GET/POST | `/generate-quiz/<id>` | AI-generated quiz from lecture |
| POST | `/submit-quiz/<id>` | Submit quiz answers |
| GET | `/generate-study-notes/<id>` | AI study notes |
| GET | `/summarize-lecture/<id>` | AI lecture summary |
| GET | `/course/<id>/modules` | View course modules |
| GET | `/module/<id>` | View module lessons |
| GET | `/lesson/<id>` | View lesson content |
| GET/POST | `/quiz/<id>` | Take a quiz |

### Instructor Routes (Instructor Role Required)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/instructor/dashboard` | Instructor dashboard with stats |
| GET | `/instructor/courses` | List instructor's courses |
| GET/POST | `/instructor/course/new` | Create new course |
| GET/POST | `/instructor/course/import-playlist` | **YouTube playlist importer** |
| GET/POST | `/instructor/course/<id>/edit` | Edit course details |
| POST | `/instructor/course/<id>/publish` | Publish/unpublish course |
| POST | `/instructor/course/<id>/delete` | Delete course |
| GET/POST | `/instructor/course/<id>/section/new` | Create section |
| GET/POST | `/instructor/section/<id>/edit` | Edit section |
| POST | `/instructor/section/<id>/delete` | Delete section |
| GET/POST | `/instructor/section/<id>/lecture/new` | Create lecture |
| GET/POST | `/instructor/lecture/<id>/edit` | Edit lecture |
| POST | `/instructor/lecture/<id>/delete` | Delete lecture |
| GET/POST | `/instructor/media` | Media file manager |
| POST | `/instructor/media/<id>/delete` | Delete media file |
| GET | `/instructor/get-media-for-editor` | AJAX media browser |
| POST | `/instructor/reorder-sections` | AJAX section reorder |
| POST | `/instructor/reorder-lectures` | AJAX lecture reorder |
| GET/POST | `/instructor/module/<id>/edit` | Edit module |
| GET/POST | `/instructor/lesson/<id>/edit` | Edit lesson |
| GET/POST | `/instructor/quiz/<id>/edit` | Edit quiz |
| GET/POST | `/instructor/quiz/<id>/question/add` | Add quiz question |

---

## 🤖 AI Features (Google Gemini)

| Feature | Description | Fallback |
|---|---|---|
| **Quiz Generation** | Generates MCQ quizzes from lecture content | Pre-built sample questions |
| **Lecture Summary** | Summarizes lecture content into key points | Truncated content excerpt |
| **Study Notes** | Creates structured study notes with key concepts | Basic content formatting |

All AI features work with **Gemini 1.5 Flash** (preferred) or **Gemini 1.5 Pro**. If no API key is configured, the app seamlessly uses offline fallback content.

---

## 🎬 YouTube Playlist Import

One of the standout features — instructors can **paste a YouTube playlist URL** and the system will:

1. **Fetch** all video metadata using `yt-dlp` (titles, descriptions, durations, thumbnails)
2. **Preview** videos in a selectable grid with thumbnails and details
3. **Auto-create** a full course with:
   - Course title from playlist name
   - One section per selected video
   - Embedded YouTube lectures with correct video IDs
   - Video descriptions as lecture content
   - Accurate duration tracking

---

## 🎨 UI/UX

- **Dark theme** inspired by GitHub's design system
- **Fully responsive** Bootstrap 5.3 layout
- **Bootstrap Icons** for consistent iconography
- **Custom CSS** (570+ lines) with CSS variables for theming
- **Flash messages** for user feedback
- **Loading overlays** for async operations

---

## 📦 Dependencies

```
flask>=3.1.0
flask-sqlalchemy>=3.1.1
flask-login>=0.6.3
flask-wtf>=1.2.2
flask-migrate
werkzeug>=3.1.3
sqlalchemy>=2.0.40
wtforms>=3.2.1
email-validator>=2.2.0
python-dotenv>=1.1.0
google-generativeai>=0.8.5
gunicorn>=23.0.0
psycopg2-binary>=2.9.10
yt-dlp
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) — Lightweight WSGI web framework
- [Bootstrap 5](https://getbootstrap.com/) — CSS framework
- [Google Gemini AI](https://ai.google.dev/) — AI-powered content generation
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube metadata extraction
- [SQLAlchemy](https://www.sqlalchemy.org/) — Python SQL toolkit and ORM
