# UserBot Setup Instructions

Welcome to your Python/Pyrogram Telegram Userbot.
This bot uses **Pyrogram** via API ID and API HASH to log in as your real account.

## Prerequisites
- Python 3.8 or higher installed.
- A Telegram account.

---

## Step 1: Get API Credentials (API_ID and API_HASH)
1. Go to [https://my.telegram.org/auth](https://my.telegram.org/auth) and log in with your phone number.
2. Click on **API development tools**.
3. Create a new application (you can enter any random App name and Short name).
4. Once created, you will see your **App api_id** and **App api_hash**.
5. Save these securely.

---

## Step 2: Install Dependencies
Open your terminal and navigate to this folder. Run:
```bash
pip install -r requirements.txt
```

---

## Step 3: Run the Bot
You must provide the API ID and API HASH as environment variables or export them before running the script.

**For Mac/Linux:**
```bash
export API_ID="your_api_id_here"
export API_HASH="your_api_hash_here"
python bot.py
```

**For Windows (PowerShell):**
```powershell
$env:API_ID="your_api_id_here"
$env:API_HASH="your_api_hash_here"
python bot.py
```

---

## Step 4: Login (String Session Generation)
When you run `python bot.py` for the first time:
1. It will ask for your phone number (with country code, e.g., `+1234567890`).
2. Telegram will send a login code to your Telegram app (or via SMS).
3. Enter the code in the terminal.
4. If you have Two-Step Verification (2FA) enabled, it will prompt for your cloud password.

Once successful, a file named `my_userbot.session` will be created in this folder, and you won't need to log in again.

---

## 24/7 Hosting (Keep it alive forever!)

If you run the bot on your own computer, it will turn off as soon as you close your terminal or turn off your PC. To run it `24/7` without interruption, you have 3 options:

### Option A: The Docker Cloud Method (Easiest & Automatic 24/7)
I have built a `Dockerfile` into this project. Platforms like **Render.com**, **Railway.app**, or **Koyeb** can run it automatically forever for free.
1. Make an account on [Render](https://render.com) and click **New > Web Service**.
2. Connect your GitHub account and select this repository.
3. Render will auto-detect the `Dockerfile` and build it.
4. **CRITICAL:** Ensure `my_userbot.session` and `users.db` are uploaded so it doesn't ask you to login again.
5. Deploy it! It will run endlessly in the cloud without ever dropping.

### Option B: Use a Free Cloud Host (Render / Railway / Heroku Python ENV)
**Note**: You will need to upload your `my_userbot.session` file along with your code to the host so it doesn't ask for a login code again. 
1. Create a GitHub repository with this code AND the `my_userbot.session` file.
2. Link the repository to a free tier service like Render.com
3. Set the start command to: `python bot.py`
4. Set the Environment Variables (`API_ID` & `API_HASH`) in the Render dashboard.
5. Deploy! It will now run 24/7 in the cloud.

### Option B: Use a cheap VPS (Virtual Private Server)
If you have a Linux VPS (Ubuntu/Debian):
1. SSH into your VPS.
2. Clone or upload these files to your server (including the session file).
3. Install Python and dependencies: `sudo apt install python3 python3-pip && pip3 install -r requirements.txt`
4. Install `screen` or `tmux` so it runs in the background even when you disconnect: 
```bash
sudo apt install tmux
tmux new -s userbot
export API_ID="your_api_id"
export API_HASH="your_api_hash"
python3 bot.py
```
5. Press `CTRL+B`, then hit `D` to detach the screen. The bot is now running perfectly in the background forever.

**Disclaimer:** The `.hack` command is purely a visual simulation and a prank. It **does not** collect real private data or perform any malicious actions. Do not abuse Telegram API rate limits by spamming commands.
