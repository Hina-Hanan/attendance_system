# Step-by-Step: Deploy on GCP (VM + Bucket + Cloud SQL)

Follow these steps in order. Replace placeholders like `YOUR_PROJECT_ID`, `your-bucket-name`, and passwords with your own values.

---

## Prerequisites

- Google Cloud account ([console.cloud.google.com](https://console.cloud.google.com))
- Your code pushed to GitHub (or another repo the VM can clone)
- (Optional) [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed locally for `gcloud` and `gsutil` commands

---

## Step 1: Create a project and enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Create a new project or select one: **Select a project** → **New Project** → name it (e.g. `face-attendance`) → **Create**. Note the **Project ID** (e.g. `face-attendance-123456`).
3. Enable required APIs:
   - **APIs & Services** → **Library**.
   - Search and enable:
     - **Compute Engine API**
     - **Cloud SQL Admin API**
     - **Cloud Storage API**
   - Or with gcloud (replace `YOUR_PROJECT_ID`):
     ```bash
     gcloud services enable compute.googleapis.com sqladmin.googleapis.com storage.googleapis.com --project=YOUR_PROJECT_ID
     ```

---

## Step 2: Create the database (Cloud SQL PostgreSQL)

### 2.1 Create the Cloud SQL instance

1. In Console go to **SQL** (search “SQL” in the top bar) → **Create instance**.
2. Choose **PostgreSQL**.
3. **Instance ID:** e.g. `attendance-db`.
4. **Password:** set and **save** the root password (you’ll need it for `DATABASE_URL`).
5. **Region:** pick one (e.g. `us-central1`). You’ll use the **same region** for the VM later.
6. **Machine type:** e.g. **Shared core** → **1 vCPU** (enough for small usage).
7. Under **Connections:**
   - Enable **Public IP**.
   - **Authorized networks:** leave empty for now; you’ll add the VM’s IP after Step 3.
8. Click **Create instance**. Wait until the instance is ready (green check).

### 2.2 Create the database and get connection details

1. Open your instance → **Databases** tab → **Create database**.
2. **Database name:** `attendance_db` → **Create**.
3. Go to **Overview** tab. Note:
   - **Public IP address** (e.g. `34.1.2.3`).
4. **Connection string** will look like:
   ```text
   postgresql://postgres:YOUR_ROOT_PASSWORD@PUBLIC_IP:5432/attendance_db
   ```
   Replace `YOUR_ROOT_PASSWORD` and `PUBLIC_IP`. Save this as `DATABASE_URL` for the backend (you’ll use it in Step 3).

### 2.3 Allow the VM to connect (after you have the VM IP)

- After creating the VM in Step 3, note its **External IP**.
- In Cloud SQL → your instance → **Connections** → **Networking** → **Add network**.
- **Name:** e.g. `backend-vm`. **Network:** your VM’s external IP (e.g. `1.2.3.4/32`). **Save.**

---

## Step 3: Create the backend VM and run the app

### 3.1 Create the VM

1. Go to **Compute Engine** → **VM instances** → **Create instance**.
2. **Name:** e.g. `attendance-backend`.
3. **Region and zone:** same **region** as Cloud SQL (e.g. `us-central1-a`).
4. **Machine type:** e.g. **e2-medium** (2 vCPU, 4 GB memory; needed for face_recognition/dlib).
5. **Boot disk:** **Change** → **Ubuntu** → **Ubuntu 22.04 LTS** → **Select**.
6. **Firewall:** check **Allow HTTP traffic** and **Allow HTTPS traffic** (so you can open port 8000 or put a load balancer in front later).
7. Click **Create**. Wait until the VM has a green status. Note its **External IP** (e.g. `34.56.78.90`).

### 3.2 Add VM IP to Cloud SQL (authorized network)

- As in **2.3**, add this VM’s external IP to Cloud SQL **Authorized networks** so the VM can connect to the database.

### 3.3 SSH into the VM

- On the VM row, click **SSH** → **Open**. A browser terminal opens.

### 3.4 Install system packages (copy-paste in SSH)

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git build-essential cmake
```

### 3.5 Clone the repo and install Python dependencies

Replace `https://github.com/YOUR_USERNAME/YOUR_REPO.git` with your repo URL.

```bash
cd $HOME
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git attendance
cd attendance/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

(This may take several minutes while dlib/face_recognition build.)

### 3.6 Create the `.env` file on the VM

```bash
nano .env
```

Paste the following and **edit** the values:

```env
DATABASE_URL=postgresql://postgres:YOUR_ROOT_PASSWORD@CLOUD_SQL_PUBLIC_IP:5432/attendance_db
SECRET_KEY=your-long-random-secret-key-change-this
CORS_ORIGINS=["http://storage.googleapis.com/YOUR_BUCKET_NAME","http://YOUR_BUCKET_NAME.storage.googleapis.com"]
```

- Replace `YOUR_ROOT_PASSWORD` and `CLOUD_SQL_PUBLIC_IP` with the Cloud SQL password and public IP from Step 2.
- Replace `YOUR_BUCKET_NAME` with the bucket name you’ll use in Step 4 (e.g. `face-attendance-frontend`). You can refine CORS later after the bucket is created.

Save: **Ctrl+O**, **Enter**, **Ctrl+X**.

### 3.7 Test the backend

```bash
source venv/bin/activate
gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

- In the VM’s **Firewall**, open port **8000**: **VPC network** → **Firewall** → **Create firewall rule**:
  - Name: `allow-backend-8000`
  - Targets: All instances (or the `attendance-backend` tag)
  - Source IP ranges: `0.0.0.0/0`
  - Protocols and ports: **tcp:8000** → **Create**.

Then in your browser open: `http://VM_EXTERNAL_IP:8000/docs`. You should see the API docs. Stop the server with **Ctrl+C**.

### 3.8 Run backend permanently with systemd

```bash
sudo nano /etc/systemd/system/attendance-backend.service
```

Paste (adjust `YOUR_USER` to the VM username, e.g. `your_username` from the SSH prompt):

```ini
[Unit]
Description=Face Attendance Backend
After=network.target

[Service]
User=YOUR_USER
Group=YOUR_USER
WorkingDirectory=/home/YOUR_USER/attendance/backend
Environment="PATH=/home/YOUR_USER/attendance/backend/venv/bin"
ExecStart=/home/YOUR_USER/attendance/backend/venv/bin/gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Save and exit. Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable attendance-backend
sudo systemctl start attendance-backend
sudo systemctl status attendance-backend
```

Your backend URL is: **`http://VM_EXTERNAL_IP:8000`** (API base: `http://VM_EXTERNAL_IP:8000/api/v1`).

---

## Step 4: Frontend in a Cloud Storage bucket

### 4.1 Create the bucket

1. **Cloud Storage** → **Buckets** → **Create**.
2. **Name:** e.g. `face-attendance-frontend` (must be globally unique).
3. **Region:** same as your VM/Cloud SQL is fine.
4. **Create**.

### 4.2 Build the frontend locally (on your PC)

On your **local machine** (where your repo is), in the project root:

```bash
cd frontend
set REACT_APP_API_URL=http://VM_EXTERNAL_IP:8000/api/v1
npm run build
```

- Replace `VM_EXTERNAL_IP` with the backend VM’s external IP (e.g. `34.56.78.90`).  
- On Linux/macOS use: `export REACT_APP_API_URL=http://VM_EXTERNAL_IP:8000/api/v1` then `npm run build`.

This produces a `build/` folder.

### 4.3 Upload the build to the bucket

From your **local machine** (with gcloud/gsutil configured, or use Console upload):

```bash
gsutil -m cp -r build/* gs://face-attendance-frontend/
```

Replace `face-attendance-frontend` with your bucket name.

### 4.4 Set the bucket as a static website

```bash
gsutil web set -m index.html -e index.html gs://face-attendance-frontend
```

(Replace bucket name if different.)

### 4.5 Make the bucket contents public

```bash
gsutil iam ch allUsers:objectViewer gs://face-attendance-frontend
```

### 4.6 Get the frontend URL

- **Option A:** Website URL format:  
  `http://storage.googleapis.com/face-attendance-frontend/index.html`  
  or (depending on region):  
  `http://face-attendance-frontend.storage.googleapis.com/index.html`
- **Option B:** In Console: **Cloud Storage** → your bucket → **Configuration** tab → **Website configuration** → note the **Main page** URL.

Use this URL to open your app. It will call the backend at `http://VM_EXTERNAL_IP:8000/api/v1`.

### 4.7 Update CORS on the backend (if needed)

If the browser blocks requests (CORS error), on the **VM** edit `.env` and set `CORS_ORIGINS` to the exact frontend URL you use, e.g.:

```env
CORS_ORIGINS=["http://storage.googleapis.com/face-attendance-frontend","http://face-attendance-frontend.storage.googleapis.com"]
```

Then restart the backend:

```bash
sudo systemctl restart attendance-backend
```

---

## Step 5: Quick checklist

| Item | What to check |
|------|----------------|
| Cloud SQL | Instance running, DB `attendance_db` exists, VM IP in **Authorized networks**. |
| Backend VM | `attendance-backend.service` is active, port 8000 open in firewall, `http://VM_IP:8000/docs` loads. |
| Frontend bucket | `build/` uploaded, website config set, public access on, frontend URL loads and shows the app. |
| CORS | Backend `.env` has the frontend origin(s) in `CORS_ORIGINS`. |

---

## Optional: Reserve a static IP for the backend VM

1. **VPC network** → **IP addresses** → **Reserve external static address**.
2. Attach it to the `attendance-backend` VM (edit VM → **Networking** → replace **Ephemeral** with this static IP).
3. Use this IP in `REACT_APP_API_URL` and in Cloud SQL authorized networks so it doesn’t change after VM restart.

---

## Optional: HTTPS for frontend (Load Balancer + backend bucket)

1. **Network Services** → **Load balancing** → **Create load balancer** → **HTTP(S) load balancing**.
2. **Backend:** Add a **Backend bucket** → select your frontend bucket.
3. **Frontend:** Add frontend (e.g. HTTP or HTTPS). For HTTPS, create or use a certificate.
4. Use the load balancer IP (or domain) as your frontend URL and add that URL to backend `CORS_ORIGINS`.

---

## Troubleshooting

- **Backend can’t connect to Cloud SQL:** Check Cloud SQL **Authorized networks** includes the VM’s external IP. Check `DATABASE_URL` (password, IP, database name).
- **Frontend shows but API calls fail:** Check `REACT_APP_API_URL` was set when you ran `npm run build` (must be `http://VM_IP:8000/api/v1`). Check CORS: backend `CORS_ORIGINS` must include the exact frontend origin (e.g. `http://storage.googleapis.com` or the bucket URL).
- **502 / connection refused:** Ensure firewall allows **tcp:8000** and `sudo systemctl status attendance-backend` is active.
- **dlib/face_recognition build fails on VM:** Ensure `build-essential` and `cmake` are installed (`sudo apt install -y build-essential cmake`). Use at least e2-medium for enough memory during build.
