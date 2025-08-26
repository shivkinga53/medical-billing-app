# Medical Billing - Claim Assignment Application

This is a full-stack web application designed to automate the assignment of medical billing claims to employees based on a dynamic, multi-strategy rule engine. The application features distinct roles for Admins and Members, a user registration and approval workflow, and a robust process for validating and assigning claims from uploaded files.

---

## ✨ Features

### Admin Role

* **User Management:** View all registered users, activate/deactivate their accounts, and delete users.

* **Employee Configuration:** Edit and assign `role`, `skills`, `max_daily_claims`, `seniority`, and the assignment strategy (`assign_by`) for each member.

* **Two-Step Claim Assignment:**

  * **Upload & Validate:** Upload a `.xlsx` or `.csv` file containing claims. The system performs a "dry run" validation, checking for data integrity and simulating the assignment process.
  * **Review & Execute:** The admin is presented with a clear plan of which claims will be assigned to whom and which cannot. Upon confirmation, the claims are officially created and assigned in the database.

* **View All Claims:** See a detailed list of every claim currently in the database.

### Member Role

* **Account Registration:** New users can register for an account, which awaits admin approval.

* **Personalized Dashboard:** View a list of all claims specifically assigned to them.

* **Claim Management:** Update the status of a claim and edit the most recent note associated with it through a two-step confirmation process.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask, SQLAlchemy, PostgreSQL
* **Frontend:** React (Vite), JavaScript, Axios
* **Core Libraries:** Pandas (for file processing), Bcrypt (for password hashing), PyJWT (for authentication)

---

## 🚀 Getting Started

Follow these instructions to set up and run the project on your local machine.

### Prerequisites

Make sure you have the following software installed:

* Python (version 3.10 or newer)
* Node.js (version 18 or newer)
* PostgreSQL

### 1. Backend Setup

You will need one terminal window for the backend.

**Navigate to the Backend Directory:**

```bash
cd path/to/your/project/backend
```

**Create and Activate a Virtual Environment:**

```bash
# Create the environment (only needs to be done once)
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

**Install Dependencies:**

```bash
pip install -r requirements.txt
```

**Set Up the Database:**

* Make sure your PostgreSQL server is running.
* Create a new database for the project (e.g., `CREATE DATABASE medicaldb;`).

Create a `.env` file in the `backend/` directory by copying the example below and adding your database credentials.

```env
# backend/.env
DATABASE_URL=postgresql://your_postgres_user:your_postgres_password@localhost:5432/medicaldb
JWT_SECRET_KEY=change-this-to-a-very-strong-random-secret
ADMIN_NAME=Admin Name
ADMIN_USERNAME=admin-username
ADMIN_PASSWORD=admin-password
```

**Initialize the Database (One-Time Setup):**

Run these commands to create the database tables, the first admin user, and the initial skills.

```bash
flask db_cli create-admin
flask db_cli create-skills
```

**Start the Backend Server:**

```bash
flask run
```

Your backend API is now running at `http://localhost:5000`. Leave this terminal open.

### 2. Frontend Setup

You will need a second, separate terminal window for the frontend.

**Navigate to the Frontend Directory:**

```bash
cd path/to/your/project/frontend
```

**Install Dependencies:**

```bash
npm install
```

**Set Up Environment Variables:**

Create a `.env` file in the `frontend/` directory. The project is already configured to connect to your backend server running on port 5000.

```env
# frontend/.env
VITE_API_BASE_URL=http://localhost:5000/api
```

**Start the Frontend Server:**

```bash
npm run dev
```

Your frontend application is now running. The terminal will provide you with a local URL, typically `http://localhost:5173`.

---

## 📋 How to Use the Application

1. **Open the App:** Open the frontend URL (e.g., `http://localhost:5173`) in your web browser.

2. **Register a New Member:**

   * Click the "Register" link.
   * Fill in a name, username, and password to create a new member account. You will see a success message indicating the account is awaiting approval.

3. **Log in as Admin:**

   * Navigate to the "Login" page.
   * Use the following credentials:

```
Username: admin
Password: password
```

4. **Activate the New Member:**

   * On the Admin Dashboard, ensure you are on the "User Management" panel.
   * Find the new user you just registered (their status will be "Inactive").
   * Click the "Activate" button.
   * Click the "Edit" button to open the modal. Assign a Role (e.g., "Biller"), select some Skills, and set their Max Daily Claims. Click "Save Changes".

5. **Upload and Assign Claims:**

   * Switch to the "Claim Upload" panel.
   * Select your `.xlsx` or `.csv` file containing claims.
   * Click "Validate File". The application will show you a plan of how the claims will be assigned.
   * Review the plan and click "Confirm & Execute Assignment".

6. **Log in as a Member:**

   * Log out of the Admin account.
   * Log in with the credentials of the member you registered and activated.
   * You will be taken to the Member Dashboard, where you can see and manage the claims that were just assigned to you.
