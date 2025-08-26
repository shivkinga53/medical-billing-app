# Medical Billing - Claim Assignment Application

This is a full‑stack web application designed to automate the assignment of medical billing claims to employees using a dynamic, multi‑strategy rule engine. It includes Admin and Member roles, a registration & approval workflow, and a two‑step upload/validation process for claim files.

---

## Table of Contents

* [Features](#features)

  * [Admin Role](#admin-role)
  * [Member Role](#member-role)
* [Tech Stack](#tech-stack)
* [Getting Started](#getting-started)

  * [Prerequisites](#prerequisites)
  * [Backend Setup](#backend-setup)
  * [Frontend Setup](#frontend-setup)
* [How to Use the Application](#how-to-use-the-application)

---

## ✨ Features

### Admin Role

* **User Management**: View all registered users, activate/deactivate accounts, and delete users.
* **Employee Configuration**: Edit and assign `role`, `skills`, `max_daily_claims`, `seniority`, and the assignment strategy (`assign_by`) for each member.
* **Two-Step Claim Assignment**:

  1. **Upload & Validate**: Upload a `.xlsx` or `.csv` file containing claims. The system performs a dry run that validates data integrity and simulates assignment.
  2. **Review & Execute**: Admins review a proposed assignment plan (which claims can be assigned and to whom). After confirmation, claims are created and assigned in the database.
* **View All Claims**: Detailed list of every claim currently in the database.

### Member Role

* **Account Registration**: New users can register and wait for admin approval.
* **Personalized Dashboard**: Members see claims assigned specifically to them.
* **Claim Management**: Update claim status and edit the most recent note via a two‑step confirmation flow.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask, SQLAlchemy, PostgreSQL
* **Frontend:** React (Vite), JavaScript, Axios
* **Core Libraries:** Pandas (file processing), Bcrypt (password hashing), PyJWT (authentication)

---

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

Make sure the following are installed:

* Python (3.10+)
* Node.js (18+)
* PostgreSQL

---

### 1. Backend Setup

Open a terminal for the backend and run the following:

```bash
# navigate to backend
cd path/to/your/project/backend

# Create the environment (only once)
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Set up the database

1. Ensure PostgreSQL is running.
2. Create a database, e.g.:

```sql
CREATE DATABASE medicaldb;
```

3. Create a `.env` file in the `backend/` directory (copy and update values):

```env
# backend/.env
DATABASE_URL=postgresql://your_postgres_user:your_postgres_password@localhost:5432/medicaldb
JWT_SECRET_KEY=change-this-to-a-very-strong-random-secret
ADMIN_NAME=Admin Name
ADMIN_USERNAME=admin-username
ADMIN_PASSWORD=admin-password
```

#### Initialize the database (one-time setup)

```bash
# Create DB tables, first admin user, and initial skills
flask db_cli create-admin
flask db_cli create-skills
```

#### Start the backend server

```bash
flask run
```

The backend API will be available at `http://localhost:5000`.

---

### 2. Frontend Setup

Open a second terminal for the frontend and run:

```bash
# navigate to frontend
cd path/to/your/project/frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend typically runs at `http://localhost:5173` (the terminal will print the exact URL).

> The frontend is preconfigured to connect to the backend at port `5000`.

---

## 📋 How to Use the Application

1. **Open the app** in your browser (e.g., `http://localhost:5173`).

2. **Register a new Member**

   * Click **Register** and provide a name, username, and password. A success message will indicate the account is awaiting admin approval.

3. **Log in as Admin**

   * Go to the **Login** page.
   * Default admin credentials (development):

     * Username: `admin`
     * Password: `password`

4. **Activate the new Member**

   * In the Admin Dashboard, open **User Management**.
   * Find the newly registered user (status: `Inactive`) and click **Activate**.
   * Click **Edit** to assign a Role (e.g., `Biller`), select Skills, and set **Max Daily Claims**. Then **Save Changes**.

5. **Upload and Assign Claims**

   * Go to **Claim Upload**.
   * Choose your `.xlsx` or `.csv` file and click **Validate File**. The app will show a proposed assignment plan.
   * Review the plan and click **Confirm & Execute Assignment** to create and assign claims.

6. **Log in as the Member**

   * Log out of the Admin account and sign in with the activated member credentials.
   * The Member Dashboard shows assigned claims; members can update statuses and notes as allowed.

---