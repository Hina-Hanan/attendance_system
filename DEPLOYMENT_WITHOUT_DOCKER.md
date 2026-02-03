# Deploy Without Docker

This guide deploys the Face Attendance app **without using Docker**:

- **Option 1:** Frontend on **Vercel**, backend on **Railway**, database on **Neon or Supabase** (Sections 1–4).
- **Option 2 (GCP):** Backend on a **Compute Engine VM**, frontend in a **Cloud Storage bucket**, database on **Cloud SQL (PostgreSQL)** (Section 6).

---

## 1. Database (PostgreSQL)

Use a free managed Postgres so you don’t run a database server yourself.

### Option A: Neon

1. Go to [neon.tech](https://neon.tech) and sign up.
2. Create a project and copy the **connection string** (e.g. `postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`).
3. Keep it for the backend env in step 3.

### Option B: Supabase

1. Go to [supabase.com](https://supabase.com) and create a project.
2. **Settings → Database** → copy the **URI** (connection string).
3. Use it as `DATABASE_URL` for the backend.

---

## 2. Backend (Railway)

Railway runs your Python backend with **Nixpacks** (no Docker image to maintain). The repo already has `backend/nixpacks.toml` and `backend/Procfile`.

1. **Push your code** to GitHub (if not already).

2. Go to [railway.app](https://railway.app) → **Start a New Project** → **Deploy from GitHub repo** and select your repo.

3. **Add a service** for the backend:
   - **New → GitHub Repo** (same repo).
   - In the new service: **Settings** → set **Root Directory** to `backend`.
   - Railway will detect Python and use `nixpacks.toml` (installs CMake/GCC for dlib).

4. **Variables** (Settings → Variables):
   - `DATABASE_URL` = your Neon or Supabase connection string.
   - `SECRET_KEY` = a long random string (e.g. from `openssl rand -hex 32`).
   - `CORS_ORIGINS` = `["https://your-frontend.vercel.app"]` (replace with your real Vercel URL after step 3; you can add it later and redeploy).

5. **Deploy**: Railway builds and runs the backend. Note the **public URL** (e.g. `https://your-app.railway.app`). Your API will be at `https://your-app.railway.app/api/v1`.

6. **Optional – PostgreSQL on Railway:**  
   You can add **Postgres** from Railway’s dashboard and use the generated `DATABASE_URL` instead of Neon/Supabase.

---

## 3. Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.

2. **Add New Project** → import the same GitHub repo.

3. **Configure:**
   - **Root Directory:** set to `frontend` (so Vercel runs build inside the frontend folder).
   - **Build Command:** `npm run build`.
   - **Output Directory:** `build`.

4. **Environment variable:**
   - Name: `REACT_APP_API_URL`  
   - Value: `https://your-backend.railway.app/api/v1` (the backend URL from step 2, with `/api/v1`).

5. Deploy. Vercel will build and give you a URL like `https://your-app.vercel.app`.

6. **CORS:** In Railway, set `CORS_ORIGINS` to include your Vercel URL, e.g.  
   `["https://your-app.vercel.app"]`  
   then redeploy the backend.

---

## 4. Summary

| Part      | Where        | What you do |
|----------|--------------|-------------|
| Database | Neon or Supabase | Create project, copy connection string. |
| Backend  | Railway      | Deploy from GitHub, root `backend`, set `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`. |
| Frontend | Vercel       | Deploy from GitHub, set `REACT_APP_API_URL` to backend `/api/v1` URL. |

No Docker is required on your machine or on these platforms for this setup.

---

## 5. Optional: Backend on a VPS (Ubuntu)

If you prefer a VPS (e.g. DigitalOcean, EC2) instead of Railway:

1. Create an Ubuntu 22.04 server and SSH in.

2. Install system packages and Python:
   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3.11-venv python3-pip postgresql-client build-essential cmake
   ```

3. Clone the repo and use the backend folder:
   ```bash
   git clone https://github.com/your-username/attendance.git
   cd attendance/backend
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Create `.env` with `DATABASE_URL` (e.g. Neon/Supabase), `SECRET_KEY`, and `CORS_ORIGINS`.

5. Run with gunicorn (same as Railway):
   ```bash
   gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

6. Put a process manager (e.g. systemd) and optionally Nginx in front. Database can stay on Neon/Supabase.

---

## 6. GCP: Backend on VM, Frontend in Bucket, Database on Cloud SQL

You can run everything on Google Cloud: **backend on a Compute Engine VM**, **frontend static files in a Cloud Storage bucket**, and **database on Cloud SQL (PostgreSQL)**. No Docker required.

### Database on GCP: Cloud SQL (PostgreSQL)

Use **Cloud SQL for PostgreSQL** so you don’t run or maintain a database server yourself.

1. In **Google Cloud Console** → **SQL** → **Create instance** → choose **PostgreSQL**.
2. Set a root password, pick a region (same as your VM is best), and choose a small machine (e.g. shared-core).
3. Under **Connections**, enable **Public IP** if your VM will use it, or use **Private IP** if the VM is in the same VPC (recommended for production).
4. Create a database (e.g. `attendance_db`) and a user if needed. Copy the **connection name** (e.g. `project:region:instance`) or build the connection string:
   - Format: `postgresql://USER:PASSWORD@PUBLIC_OR_PRIVATE_IP:5432/attendance_db`
   - For Cloud SQL with public IP, use the instance’s public IP. Add your VM’s external IP to **Authorized networks** if you use public IP.
5. Use this as `DATABASE_URL` on your backend VM.

**Why not run Postgres on the same VM?** You can, but Cloud SQL gives you backups, patches, and high availability without extra work. For a small project, Cloud SQL is the recommended option on GCP.

---

### Backend on a Compute Engine VM

1. **Create a VM** (e.g. **e2-medium**, Ubuntu 22.04), in the **same region** as your Cloud SQL instance. Allow HTTP/HTTPS traffic if you’ll put a load balancer or direct traffic to it.

2. **SSH into the VM** and install dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3.11-venv python3-pip build-essential cmake
   ```

3. **Clone and run the backend:**
   ```bash
   git clone https://github.com/your-username/attendance.git
   cd attendance/backend
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create `/home/your-user/attendance/backend/.env`** with:
   - `DATABASE_URL` = Cloud SQL connection string from above
   - `SECRET_KEY` = a long random string
   - `CORS_ORIGINS` = `["https://your-frontend-domain.com","http://your-bucket-website-url"]` (see frontend step for URLs)

5. **Run with gunicorn** (for testing):
   ```bash
   gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

6. **Production:** Use **systemd** to run gunicorn on boot and optionally put **Nginx** in front (reverse proxy, SSL). Open firewall for port 8000 (or 80/443 if using Nginx).

7. **Public URL:** Either assign a static external IP and use `http://VM_EXTERNAL_IP:8000`, or put the VM behind a **Load Balancer** with an HTTPS certificate.

---

### Frontend in a Cloud Storage bucket

1. **Build the frontend locally** (or on a build machine) with the backend API URL:
   ```bash
   cd attendance/frontend
   REACT_APP_API_URL=https://your-backend-url/api/v1 npm run build
   ```
   Replace `your-backend-url` with your VM’s URL or load balancer URL (e.g. `https://api.yourdomain.com`).

2. **Create a bucket** in the same GCP project (e.g. `your-app-frontend`). Choose a region.

3. **Upload the build output:**
   ```bash
   gsutil -m cp -r build/* gs://your-app-frontend/
   ```

4. **Make the bucket serve a static website:**
   - In Console: **Cloud Storage** → your bucket → **Configuration** tab → **Edit website configuration**.
   - Set **Main page** to `index.html`, **404 page** to `index.html` (for React Router if you add it later).
   - Or with gsutil:
     ```bash
     gsutil web set -m index.html -e index.html gs://your-app-frontend
     ```

5. **Make objects public** (so the browser can load JS/CSS):
   ```bash
   gsutil iam ch allUsers:objectViewer gs://your-app-frontend
   ```
   The site will be at: `http://storage.googleapis.com/your-app-frontend/index.html` or the bucket’s **Website endpoint** shown in the bucket details.

6. **HTTPS / custom domain (optional):** Use **Cloud Load Balancing** with a **Backend bucket** pointing to this bucket and add an **SSL certificate** so the frontend is served over `https://yourdomain.com`.

---

### GCP summary

| Part      | Where              | What you do |
|----------|--------------------|-------------|
| Database | **Cloud SQL** (PostgreSQL) | Create instance, create DB/user, get connection string. Use it as `DATABASE_URL` on the VM. |
| Backend  | **Compute Engine VM**      | Ubuntu, install Python + build-essential + cmake, clone repo, `.env` with `DATABASE_URL` and CORS, run gunicorn (and systemd + Nginx for production). |
| Frontend | **Cloud Storage bucket**   | Build with `REACT_APP_API_URL`, upload `build/` to bucket, set bucket as static website, make objects public. Optionally put a Load Balancer in front for HTTPS. |

---

## Troubleshooting

- **Backend build fails on Railway (dlib):** Ensure Root Directory is `backend` so `nixpacks.toml` is used. The first build can take several minutes.
- **CORS errors in browser:** Add the exact frontend URL (e.g. `https://your-app.vercel.app`) to `CORS_ORIGINS` and redeploy the backend.
- **Frontend can’t reach API:** Confirm `REACT_APP_API_URL` is set in Vercel (and rebuilt) and points to `https://your-backend.railway.app/api/v1`.
