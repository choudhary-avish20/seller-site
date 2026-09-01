# Admin Handover Guide

This document describes how to hand off admin/seller access to the store owner securely.

## Overview

- Customers use `login.html` — this is the public login page.
- The store owner uses `admin-login.html` — this page is **not linked from anywhere** on the site. It rejects customer accounts at the login step.
- The admin panel is at `admin-dashboard.html` and is only accessible after logging in via `admin-login.html`.

---

## Handover Steps

### Step 1 — Set credentials on the hosting platform

In your cloud host's dashboard (Railway, Render, Heroku, etc.), set the following environment variables **before** running the seed script:

| Variable | Value |
|---|---|
| `ADMIN_EMAIL` | The owner's email address |
| `ADMIN_PASSWORD` | A temporary password (min 8 characters) |
| `ADMIN_NAME` | The owner's full name |

> Do **not** commit these values to git or put them in `.env` files that get deployed.

### Step 2 — Run the seed script once

Open the hosting platform's shell/console and run:

```bash
python seed_admin.py
```

This creates the seller account with an approved profile. It is safe to run only once — it skips creation if the email already exists.

### Step 3 — Share credentials securely

Send the owner their temporary credentials via a **secure channel**:
- A password manager with sharing (1Password, Bitwarden)
- An encrypted messaging app (Signal, WhatsApp)
- In person

**Do not send credentials in plain email or SMS.**

### Step 4 — Give the owner the admin URL

Share the admin login URL with the owner:

```
https://your-domain.com/admin-login.html
```

Ask them to **bookmark** this URL. It is not linked from any customer-facing page.

### Step 5 — Owner changes their password

Once the owner logs in:

1. They land on the **Admin Dashboard**
2. Click **⚙ Ustawienia** (Settings) in the left sidebar
3. Fill in "Current Password" (the temp one you set), "New Password", and "Confirm New Password"
4. Click **Zmień hasło**

After this step, you no longer know the owner's password. Handover is complete.

---

## If the owner forgets their password

You can reset it by setting new `ADMIN_EMAIL` / `ADMIN_PASSWORD` env vars and running a small script, or by updating the database directly via the hosting platform's console using the same `seed_admin.py` approach (after deleting the old account first, or writing a separate reset script).

---

## Security notes

- The `admin-login.html` URL is security-by-obscurity only. The role check on login is the real guard.
- The backend enforces role checks on every admin API call — a buyer who somehow finds the URL cannot do anything.
- Regularly remind the owner not to share their admin password.
