# Running IndicEdgeBench on the Acer (Windows 11): step-by-step

Work through this list from top to bottom and tick each box as you go. Type the commands into **PowerShell** (Start menu → type "PowerShell" → open it). Every step ends with a ✅ **Check**, so you know it worked before moving on.

**What you need:** about 15 GB of free disk space, the charger plugged in, and 2–4 hours for the full run (most of it is unattended).

---

## Part A: One-time installs (about 15 min)

### ☐ A1. Install Python 3.12
1. Go to <https://www.python.org/downloads/windows/> and download **Python 3.12.x, Windows installer (64-bit)**.
2. Run it. On the first screen, **tick "Add python.exe to PATH"**, then click *Install Now*.

✅ **Check:** open a **new** PowerShell window and run:
```powershell
python --version
```
It should print `Python 3.12.x`. If it opens the Microsoft Store instead, reinstall and make sure the PATH box is ticked.

### ☐ A2. Install Git for Windows
1. Download from <https://git-scm.com/download/win> and run the installer. **Keep all the default options.** They include *Git Credential Manager*, which shows the GitHub sign-in and account-picker window.

✅ **Check:** in a new PowerShell window:
```powershell
git --version
git credential-manager --version
```
Both should print a version number.

---

## Part B: Get the code, signed in as pammy01 (about 5 min)

### ☐ B1. Choose a folder and clone
```powershell
cd $HOME\Desktop
git clone https://github.com/pammy01/IndicEdgeBench.git
cd IndicEdgeBench
```
If a GitHub sign-in window appears, choose **Sign in with your browser** and log in as **pammy01**. If it shows an **account picker**, choose **pammy01**.

✅ **Check:** `dir` lists `README.md`, `indicedgebench`, `configs` and the other project folders.

### ☐ B2. Lock this folder to Pammy / pammy01

Run these **inside the IndicEdgeBench folder**. They change only this repo, not your other projects:
```powershell
git config user.name "Pammy"
git config user.email "pammy7296@gmail.com"
git config user.useConfigOnly true
git config core.hooksPath scripts/git-hooks
```
This turns on three safety checks that stay active for every later commit and push in this folder:
- commits must be made as **Pammy &lt;pammy7296@gmail.com&gt;**
- commit messages may not contain a co-author or AI attribution
- pushes may only go to **pammy01/IndicEdgeBench**

### ☐ B3. Pin the GitHub account

Make sure pammy01's login is saved:
```powershell
git ls-remote origin
```
If a sign-in window appears, log in as **pammy01** in the browser. Then see how Git Credential Manager saved the account:
```powershell
git credential-manager github list
```
It prints either `pammy01` or the number `211810066`. Both are the same account. Pin **exactly what it printed**:
```powershell
git config credential.https://github.com.username <what it printed>
```
For example: `git config credential.https://github.com.username pammy01`

✅ **Check:**
```powershell
git config --local --list
```
You should see `user.name=Pammy`, `user.email=pammy7296@gmail.com`, `core.hookspath=scripts/git-hooks` and `credential.https://github.com.username=...`.

---

## Part C: Install the benchmark (about 5–10 min)

### ☐ C1. Run the setup script
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```
This creates a private Python environment in `.venv` and installs everything, including a ready-made llama.cpp, so no Visual Studio is needed. It then runs the tests and prints your laptop's details.

✅ **Check:** near the end it prints `17 passed`, followed by a block like this:
```text
"cpu": "12th Gen Intel(R) Core(TM) i5-12xxxH",
"ram_gb": 15.7,
"hf_token": "missing (fallback set will be used)"
```
If you see red errors, check the **Troubleshooting** section at the bottom.

### ☐ C2. Activate the environment
Do this every time you open a new PowerShell window for this project:
```powershell
.\.venv\Scripts\Activate.ps1
```
✅ **Check:** the prompt now starts with `(.venv)`.

---

## Part D: Turn on the real MILU questions (optional, recommended; about 5 min)

Without this, the run uses the 30 bundled questions per language. With it, it uses 200 real MILU questions per language, which gives much stronger results.

### ☐ D1. Get access (free)
1. Create or log in to an account at <https://huggingface.co>.
2. Open <https://huggingface.co/datasets/ai4bharat/MILU> and click **Agree and access repository**. Approval is instant.
3. Go to **Settings → Access Tokens → Create new token**, choose type **Read**, and copy the token. It starts with `hf_`.

### ☐ D2. Save the token
```powershell
notepad .env
```
Change the line to `HF_TOKEN=hf_yourTokenHere`, save, and close Notepad. `.env` is ignored by git, so the token never gets uploaded.

✅ **Check:**
```powershell
python -m indicedgebench info
```
It should now say `"hf_token": "found (MILU enabled)"`.

---

## Part E: Run the pilot (2–4 hours, mostly unattended)

### ☐ E1. Prepare the laptop
- Plug in the charger.
- Settings → System → Power → Power mode: **Best performance**.
- Close Chrome, Teams and other heavy apps.
- Settings → System → Power → Screen and sleep: set **"Make my device sleep after" to Never** while plugged in.

### ☐ E2. Start the run
```powershell
python -m indicedgebench run configs\pilot.yaml
```
What happens:
1. It freezes the question set.
2. It downloads each model the first time it's needed. That's about 11 GB in total, and the download is usually the slowest part.
3. It evaluates **7 configurations**: Qwen2.5-1.5B at F16/Q8/Q4/Q2, and Llama-3.2-1B at F16/Q8/Q4. Each runs Hindi, Tamil and English, with a 20-second cool-down between configurations.
4. It writes the report.

**If it stops** (sleep, Wi-Fi drop, you closed the window), just run the **same command** again. Finished parts are skipped and the download resumes.

✅ **Check:** the last line printed is `results\pilot\REPORT.md`. Open the report with:
```powershell
notepad results\pilot\REPORT.md
```
The plots are in `results\pilot\plots\`.

### ☐ E3. (Optional) Thread-count experiment

The i5 H-series mixes fast P-cores with efficient E-cores. To test whether using only the 4 P-cores is faster, copy the config:
```powershell
copy configs\pilot.yaml configs\pilot_4threads.yaml
notepad configs\pilot_4threads.yaml
```
Set `run_name: pilot_4threads` and `n_threads: 4`, then run it the same way. Models are reused, so nothing new is downloaded.

---

## Part F: Send the results back to GitHub (about 2 min)

```powershell
git add results\pilot
git status
git commit -m "Add Windows laptop pilot results"
git push
```
✅ **Check:** the push ends with `main -> main`. If the safety checks block anything, a message starting with `BLOCKED:` explains why. Re-check Part B in that case.

Once the pilot results are pushed, the slides can be rebuilt with these numbers (see `docs/eval1/build_deck.js`).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` opens the Microsoft Store | Reinstall Python with **Add python.exe to PATH** ticked, then open a *new* PowerShell window |
| `running scripts is disabled on this system` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer `Y`, then retry |
| Setup fails on `llama-cpp-python` | Check you have Python **3.10–3.13** (`python --version`). 3.14 has no prebuilt wheel yet; install 3.12 |
| `Read timed out` during setup | Slow internet; just run the setup script again |
| Model download very slow or stops | Re-run the same `run` command; downloads resume where they stopped |
| `BLOCKED: COMMITTER... expected 'Pammy <pammy7296@gmail.com>'` | Redo step B2 inside the IndicEdgeBench folder |
| `BLOCKED: credential account...` | Redo step B3 |
| GitHub asks for a password in the terminal | Close it, run `git ls-remote origin` again, and use the browser sign-in as pammy01 |
| Laptop is very hot or numbers look noisy | Increase `cooldown_s` in the config (for example to 60) and re-run with `--force` |
| A config shows "failed" in the output | Open `results\pilot\logs\<model>__<quant>.log` and check its last lines for the error |
