# CloudCart — E-Commerce Learning Project

CloudCart is a full-stack learning project built with HTML, CSS, JavaScript, Python Flask and SQLAlchemy. It includes a product catalogue, search/filter, session cart, customer accounts, simulated checkout, order history and an admin product area.

## 1. Requirements
- Python 3.10 or newer
- VS Code (recommended)
- A browser

## 2. Run locally on Windows (PowerShell)
Open PowerShell inside the `CloudCart` folder:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Open .env and change SECRET_KEY and ADMIN_PASSWORD before using the app
python app.py
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Open `http://127.0.0.1:5000` in your browser.

The first run creates a local SQLite database at `instance/cloudcart.db` and inserts sample products and a demo administrator.

## 3. Demo administrator
- Email: `admin@cloudcart.local`
- Password: `Admin@12345`

Change the password before using this outside your own local demo. The admin page is at `/admin`.

## 4. What works
- Browse products, search by name and filter by category
- Open a product details page
- Add items to cart, change quantities and remove items
- Register, log in and log out
- Checkout with delivery details
- Place a demo order and see order history
- Admin can create, edit and delete eligible products

**Payment is simulated.** This project does not process real payments or collect card details.

## 5. Folder structure
```text
CloudCart/
├── app.py                  # Flask app, routes, database models and seed data
├── requirements.txt        # Python packages
├── .env.example            # Example configuration
├── .gitignore              # Files Git should ignore
├── README.md               # Setup and project overview
├── NOTES.md                # Beginner-friendly code notes
├── instance/               # Created automatically; local database lives here
├── templates/              # HTML pages rendered by Flask
└── static/
    ├── css/style.css       # All website styling
    └── js/main.js          # Browser-side interactions
```

## 6. Next development stages
1. Learn the frontend and Flask routes.
2. Replace SQLite with MySQL for database practice.
3. Add automated tests and CSRF protection.
4. Add Docker and Docker Compose.
5. Push to GitHub.
6. Deploy to AWS (EC2 or another suitable service).
7. Add Jenkins CI/CD and monitoring.

Do not deploy this starter unchanged to production. Before public deployment, configure a strong secret key, use HTTPS, add CSRF protection, validate all inputs, secure admin access, use production database credentials and turn off Flask debug mode.
