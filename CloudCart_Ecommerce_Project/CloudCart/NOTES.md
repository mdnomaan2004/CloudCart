# CloudCart — Code Notes for Beginners

## A. How a website works
1. The browser requests a URL such as `/products`.
2. Flask receives that request and runs the matching Python route.
3. The route reads data from the database.
4. Flask sends an HTML template back to the browser.
5. CSS controls the appearance; JavaScript adds browser-side interactions.

## B. Important files
- `app.py`: the backend. It defines database tables, URLs (routes), login and order logic.
- `templates/`: HTML templates. Jinja expressions such as `{{ product.name }}` insert values sent by Flask.
- `static/css/style.css`: visual design rules.
- `static/js/main.js`: small interactive browser behaviours.
- `requirements.txt`: libraries Python needs.
- `instance/cloudcart.db`: local SQLite database created automatically.

## C. Python / Flask concepts in app.py
- `Flask(__name__)`: creates the web application.
- `@app.route("/")`: connects a URL to a Python function.
- `methods=["GET", "POST"]`: allows the page to display a form (GET) and receive submitted form data (POST).
- `request.form`: reads values submitted by an HTML form.
- `render_template(...)`: renders an HTML file from `templates/`.
- `redirect(url_for(...))`: sends the browser to another route.
- `flash(...)`: stores a one-time message for the next page.
- `login_required`: prevents visitors who are not logged in from opening a protected page.
- `session`: stores small per-browser data. Here it stores the cart.
- `abort(403)` / `abort(404)`: returns an HTTP error response.
- `if __name__ == "__main__"`: runs the local development server when app.py is started directly.

## D. Database concepts
- A model class represents a database table.
- `db.Column(...)` defines a column.
- `primary_key=True` makes a unique row identifier.
- `db.ForeignKey(...)` links a row to another table.
- `db.relationship(...)` lets Python navigate related records.
- `db.create_all()` creates tables if they do not exist.
- `db.session.add(...)` stages a new record.
- `db.session.commit()` saves changes.
- SQLite is used locally so the project starts without installing a database server. Later, we can connect MySQL by setting `DATABASE_URL`.

## E. Frontend concepts
- HTML gives the page its structure: headings, forms, buttons and product cards.
- CSS selectors choose what to style. For example, `.product-card` styles every element with that class.
- CSS Grid and Flexbox arrange content into responsive layouts.
- Media queries change the layout for smaller screens.
- JavaScript can listen for events such as clicks and input changes.
- `data-*` attributes store small values in HTML for JavaScript to read.

## F. E-commerce flow
1. A product is read from the `Product` table.
2. Add-to-cart sends a POST request to `/cart/add/<product_id>`.
3. Flask updates the cart in the session.
4. Checkout requires a logged-in user.
5. Flask creates an `Order` and its `OrderItem` records.
6. Stock is reduced and the cart is cleared.

## G. Important security learning
This is a learning starter, not production-ready software. Before public launch:
- Replace the development secret key with a long random secret.
- Never commit `.env`, database files or passwords to GitHub.
- Turn off debug mode.
- Add CSRF protection to forms.
- Add rate limiting and stronger validation.
- Use HTTPS and secure cookie settings.
- Protect and change the demo admin credentials.
- Use a production database and backups.
- Integrate a trusted payment provider only when ready.

## H. Useful commands
```powershell
python app.py
pip install -r requirements.txt
git init
git add .
git commit -m "Initial CloudCart project"
```
