# UPVS - Universal Product Verification System

UPVS is a role-based web application for product authenticity verification.
It combines QR identity, lifecycle tracking, and Solana-backed signatures to reduce counterfeit risk.

## What It Does

- Admin manages users (create users, reset password, delete users).
- Manufacturer pays and generates product QR codes.
- Seller verifies products and marks sold with payment/signature flow.
- Public users verify authenticity from a QR verification page.

## Core Features

- Unified dashboard UI across landing, login, admin, manufacturer, seller, verification pages.
- Multi-wallet support in browser: Phantom, Solflare, Backpack, Glow, and generic Solana providers.
- RPC fallback logic with active endpoint indicator.
- Verification report with status badges, QR preview, activity timeline, and explorer links.
- Privacy-safe verification output (no username exposure on public verification report).

## Tech Stack

- Backend: Flask + Jinja2
- Database: SQLite
- Frontend: HTML/CSS/JavaScript
- Blockchain: Solana Web3.js + wallet signing

## Project Structure

```
web3project/
|- app.py
|- web.py
|- database.py
|- int.py
|- requirment.txt
|- templates/
|- static/
|- qr/


```
## Quick Start

1. Clone and open project

```bash
git clone https://github.com/sarikregmi/UPVS.git
cd UPVS
```

2. Create and activate virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Mac/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirment.txt
```

4. Run app

```bash
python app.py
```

5. Open in browser

`http://localhost:5000`

## Default Access

- Admin Username: `emc`
- Admin Password: `emc`
- this is default password and username name for testing.

Use admin account to create manufacturer and seller users before demo.

## Environment Variables

- `PUBLIC_BASE_URL`: public HTTPS base URL for QR links in production.
- `SOLANA_RPC_URL`: preferred RPC endpoint.
- `SOLANA_RPC_FALLBACKS`: comma-separated backup RPC endpoints.

Example:

```powershell
$env:PUBLIC_BASE_URL="https://your-domain.com"
$env:SOLANA_RPC_URL="https://your-rpc-provider.example.com"
$env:SOLANA_RPC_FALLBACKS="https://api.devnet.solana.com,https://rpc.ankr.com/solana"
python app.py
```



## Important Repo Context

This repository is an MVP implementation of the core UPVS web product.
It does not include a native mobile app or enterprise ERP integrations.
Blockchain use is focused on payment/signature proofs and can be expanded further in production.
