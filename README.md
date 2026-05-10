# UPVS - Universal Product Verification System

UPVS is a secure, role-based web application for product authenticity verification.
It combines QR identity, lifecycle tracking, and Solana-backed signatures to reduce counterfeit risk.

## What It Does

- **Admin**: Manage users (create, reset password, delete)
- **Manufacturer**: Generate product QR codes with details
- **Seller**: Verify and mark products as sold
- **Public**: Verify product authenticity from QR code

## Features

✓ Secure password authentication with strong requirements  
✓ Role-based access control (Admin, Manufacturer, Seller, User)  
✓ QR code generation and lifecycle tracking  
✓ Multi-wallet Solana integration (Phantom, Solflare, Backpack, Glow)  
✓ RPC fallback support  
✓ Activity audit logs  
✓ CSRF protection & rate limiting  

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/sarikregmi/UPVS.git
cd UPVS
```

### 2. Setup Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create/edit `.env` file:
```bash
# Required: Set a strong admin password (8+ chars, uppercase, lowercase, digit)
ADMIN_PASSWORD=Admin@Password123

# Optional: Customize these
SECRET_KEY=your-random-secret-key
DEBUG=False
PLATFORM_WALLET=your-solana-wallet
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
PUBLIC_BASE_URL=http://localhost:5000
```

### 5. Run Application
```bash
python app.py
```

Open browser: **http://localhost:5000**

---

## Default Admin Access

**Username:** `emc`  
**Password:** From `.env` file (`ADMIN_PASSWORD`)  

⚠️ Change admin password immediately in production!

---

## Solana Network (Devnet for Testing)

By default, the app uses **Solana Devnet** for safe testing with no real funds:
- No real SOL required
- Get free testnet SOL from [Solana Faucet](https://faucet.solana.com/)
- Use Phantom wallet: switch to Devnet in wallet settings

### Switch to Production (Mainnet)

Edit `.env` file:
```bash
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_RPC_FALLBACKS=https://solana-api.projectserum.com,https://rpc.ankr.com/solana
```

⚠️ **Warning:** Mainnet uses real SOL. Test thoroughly on Devnet first!

---

## Password Requirements

All passwords must have:
- ✓ Minimum 8 characters
- ✓ At least one uppercase letter
- ✓ At least one lowercase letter  
- ✓ At least one digit

Example: `Admin@12345`

---

## Tech Stack

- **Backend:** Flask + Jinja2
- **Database:** SQLite
- **Frontend:** HTML/CSS/JavaScript
- **Blockchain:** Solana Web3.js

---

## Project Structure

```
web3project/
├── app.py              # Flask app entry point
├── web.py              # Routes & views
├── database.py         # Database functions
├── int.py              # QR code generation
├── requirements.txt    # Dependencies
├── .env                # Configuration (create this)
├── templates/          # HTML templates
├── static/             # CSS/JavaScript
└── qr/                 # Generated QR images
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| ADMIN_PASSWORD | ✓ | Random | Admin user password |
| SECRET_KEY | ✗ | Random | Flask session secret |
| DEBUG | ✗ | False | Development mode |
| PLATFORM_WALLET | ✗ | Built-in | Solana wallet for payments |
| SOLANA_RPC_URL | ✗ | Devnet | Primary RPC endpoint (devnet by default) |
| SOLANA_RPC_FALLBACKS | ✗ | Devnet | Backup RPC endpoints (comma-separated) |
| PUBLIC_BASE_URL | ✗ | localhost | Base URL for QR links |

---

## Production Deployment

### Before Deploying:

1. **Generate secure keys:**
   ```bash
   python -c "import os; print(os.urandom(32).hex())"
   ```

2. **Switch to Mainnet** (if using production):
   ```bash
   export SOLANA_RPC_URL="https://api.mainnet-beta.solana.com"
   export SOLANA_RPC_FALLBACKS="https://solana-api.projectserum.com,https://rpc.ankr.com/solana"
   ```

3. **Set environment variables** (use secure method, not .env file):
   ```bash
   export SECRET_KEY="<generated-key>"
   export ADMIN_PASSWORD="<strong-password>"
   export PLATFORM_WALLET="<your-wallet>"
   export PUBLIC_BASE_URL="https://yourdomain.com"
   export DEBUG=False
   ```

4. **Use production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

5. **Enable HTTPS** with reverse proxy (nginx/Apache)

6. **Database:** Use persistent storage location, not temporary

---

## Security Features

✓ **Password Hashing:** Werkzeug bcrypt  
✓ **CSRF Protection:** Flask-WTF  
✓ **Rate Limiting:** 5 req/min for login, 30 req/min for API  
✓ **SQL Injection Prevention:** Parameterized queries  
✓ **Session Security:** HTTPONLY, SECURE, STRICT cookies  
✓ **File Validation:** Secure filename handling  
✓ **Role-Based Access:** Enforced on all endpoints  

---

## Troubleshooting

**Port already in use:**
```bash
python app.py --port 5001
```

**Dependencies error:**
```bash
pip install -r requirements.txt --upgrade
```

**Database locked:**
```bash
rm -f app.db login.db
python app.py  # Recreates fresh databases
```

**Import errors:**
Make sure virtual environment is activated before running.

---

## Important Notes

- This is an MVP implementation
- Use HTTPS in production for security
- Set `PUBLIC_BASE_URL` to your domain
- Regularly backup SQLite database files
- Change all default credentials in production

---

## License

MIT License - See LICENSE file for details
