# Windows Setup – Face Attendance Backend

The `face-recognition` library depends on **dlib**, which must be **compiled** on your machine. That requires **CMake** and a **C++ compiler** on Windows.

## Option 1: Install build tools (recommended)

### Step 1: Install CMake

1. Download the Windows installer: https://cmake.org/download/  
   Use **“cmake-3.x.x-windows-x86_64.msi”** (64-bit).
2. Run the installer.
3. On the screen **“Add CMake to the system PATH”**, choose **“Add CMake to the system PATH for all users”** (or “for current user”).
4. Finish the installation.

### Step 2: Install Visual Studio Build Tools (C++)

1. Download **Build Tools for Visual Studio**:  
   https://visualstudio.microsoft.com/visual-cpp-build-tools/  
   (or search “Build Tools for Visual Studio”).
2. Run the installer.
3. Select the workload **“Desktop development with C++”**.
4. Install (this can take a few GB and several minutes).

### Step 3: Use a new terminal

Close and reopen PowerShell (or your terminal) so the updated PATH is loaded.

### Step 4: Verify CMake

```powershell
cmake --version
```

You should see a version (e.g. 3.28.x). If you get “not recognized”, CMake is not on PATH; fix the PATH or reinstall CMake and choose the “Add to PATH” option.

### Step 5: Install Python dependencies

From the project root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

`dlib` will compile during this step; it can take several minutes.

---

## Option 2: Use Conda (no Visual Studio)

If you use **Anaconda** or **Miniconda**, you can avoid installing Visual Studio by using conda’s pre-built `dlib`. Do **not** run `pip install -r requirements.txt` after conda install dlib—use the steps below instead:

```powershell
conda create -n attendance python=3.11 -y
conda activate attendance
conda install -c conda-forge dlib
cd C:\Users\hinah\IdeaProjects\attendance\backend
pip install -r requirements-conda.txt
pip install face-recognition --no-deps
```

- **requirements-conda.txt** = same as requirements.txt but **without** face-recognition (so pip never tries to build dlib).
- **pip install face-recognition --no-deps** = installs only `face-recognition` and does **not** reinstall dlib, so the conda dlib is used.

---

## After installation

Set your database URL and run the app:

```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/attendance_db"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

(If you use Option 2, run these in the same conda environment.)
