# Flask RESTful APIs (Auth + Dashboard)

A Flask app that provides authentication APIs (email/password + Google OAuth), email verification, password reset, JWT-protected profile endpoints, and a simple dashboard UI that shows real stats (total visits + active sessions).


##Postman API Documentation
https://documenter.getpostman.com/view/53408260/2sBXikpXfy

##Live Deployment
https://flask-restful-apis-1.onrender.com

## Features
- Register + email verification (OTP code)
- Login with email + password (email format validation)
- Google OAuth login
- JWT auth (`Authorization: Bearer <token>`)
- Profile view/update
- Change password
- Forgot/reset password (OTP code)
- Dashboard UI with real stats:
- Total Visits (login count)
- Active Sessions (server-side tracked sessions)

## Project Structure
- `app/__init__.py` Flask app factory + DB/mail config
- `app/models.py` SQLAlchemy models (`User`, `UserSession`)
- `app/auth/routes.py` Auth API routes + session tracking + stats endpoint
- `app/main/routes.py` Web pages (login/register/dashboard templates)
- `app/templates/` HTML pages
- `app/static/js/` frontend JS for auth + dashboard

## Environment Variables (.env)

Required:
- `SECRET_KEY`
- `SQLALCHEMY_DATABASE_URI`

Email (for verification + reset codes):
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_SENDER_NAME`
- `MAIL_SENDER_MAIL`

Google OAuth (optional):
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI` (example: `https://your-domain.com/api/auth/login/google/callback`)
- `FRONTEND_URL` (example: `https://your-domain.com`)

## Run Locally
```bash
pip install -r requirements.txt
python run.py
```

Open:
- Web UI: `http://localhost:5000/login`
- API base: `http://localhost:5000/api/auth`

## API Routes (Base: /api/auth)
- `POST /register` `{email, username, password}`
- `POST /verify-email` `{email, code}`
- `POST /resend-code` `{email}`
- `POST /login` `{email, password}`
- `GET /login/google`
- `GET /login/google/callback`
- `POST /logout` (Bearer token)
- `GET /profile` (Bearer token)
- `PUT /profile` (Bearer token) `{username?, email?}`
- `POST /change-password` (Bearer token) `{current_password, new_password}`
- `POST /request-reset-password` `{email}`
- `POST /reset-password` `{email, code, new_password}`
- `GET /user/stats` (Bearer token)

## Notes
- Logout revokes the current server-side session linked to the JWT.
- Dashboard fetches stats from `GET /api/auth/user/stats`.



