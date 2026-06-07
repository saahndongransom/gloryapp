# Glory Nursing – Django Website

## Quick Start

### 1. Install dependencies
```bash
pip install django
```

### 2. Run migrations
```bash
cd glorynursing
python manage.py migrate
```

### 3. Start the dev server
```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** in your browser.

---

## Project Structure
```
glorynursing/
├── glorynursing/        # Project config (settings, urls, wsgi)
├── core/
│   ├── views.py         # All page views + program data
│   ├── urls.py          # URL routes
│   ├── templates/core/  # All HTML templates
│   │   ├── base.html           (nav + footer)
│   │   ├── home.html
│   │   ├── programs.html
│   │   ├── program_detail.html
│   │   ├── admissions.html
│   │   ├── about.html
│   │   ├── contact.html
│   │   └── apply.html
│   └── static/core/
│       ├── css/main.css
│       └── js/main.js
└── db.sqlite3
```

## Pages
| URL | Page |
|-----|------|
| / | Home |
| /programs/ | All Programs |
| /programs/cna/ | CNA Detail |
| /programs/cma/ | CMA Detail |
| /programs/hha/ | HHA Detail |
| /programs/bls-cpr/ | BLS/CPR Detail |
| /programs/phlebotomy/ | Phlebotomy Detail |
| /programs/ekg/ | EKG Detail |
| /programs/medical-assistant/ | CCMA Detail |
| /programs/medical-billing-coding/ | CBCS Detail |
| /admissions/ | Admissions |
| /about/ | About Us |
| /contact/ | Contact |
| /apply/ | Apply Now |

## Customization
All program data is in `core/views.py` in the `PROGRAMS` list.
Colors are CSS variables in `core/static/core/css/main.css` under `:root`.

## Production Deployment
1. Set `DEBUG = False` in `settings.py`
2. Change `SECRET_KEY` to a secure value
3. Set `ALLOWED_HOSTS` to your domain
4. Run `python manage.py collectstatic`
5. Serve static files via nginx or WhiteNoise
