document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    document.querySelectorAll(".alert").forEach(el => {
      el.style.transition = "opacity 0.6s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 650);
    });
  }, 4500);

  renderWalletSupport("walletStatus");
  renderRpcSupport("rpcStatus");
});


function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = "Copied!";
    btn.style.color = "var(--green)";
    setTimeout(() => { btn.textContent = orig; btn.style.color = ""; }, 2000);
  });
}


function getPhantomProvider() {
  if (window.phantom && window.phantom.solana && window.phantom.solana.isPhantom) {
    return window.phantom.solana;
  }
  if (window.solana && window.solana.isPhantom) {
    return window.solana;
  }
  return null;
}


function getWalletProvider() {
  const providers = [
    { name: "Phantom", provider: window.phantom && window.phantom.solana },
    { name: "Solflare", provider: window.solflare },
    { name: "Backpack", provider: window.backpack && window.backpack.solana },
    { name: "Glow", provider: window.glow && window.glow.solana },
    { name: "Generic Solana Wallet", provider: window.solana },
  ];

  for (const entry of providers) {
    const provider = entry.provider;
    if (provider && typeof provider.connect === "function") {
      return { name: entry.name, provider };
    }
  }

  return null;
}


function setActiveWalletProvider(provider, name) {
  window.APP_ACTIVE_WALLET_PROVIDER = provider || null;
  window.APP_ACTIVE_WALLET_NAME = name || null;
}


async function connectPhantom(statusEl) {
  const wallet = getWalletProvider();
  if (!wallet) {
    const message = "No supported Solana wallet found. Install Phantom, Solflare, or Backpack and refresh the page.";
    if (statusEl) {
      statusEl.textContent = message;
      statusEl.style.color = "var(--red)";
    } else {
      alert(message);
    }
    return null;
  }

  try {
    const response = await wallet.provider.connect({ onlyIfTrusted: false });
    setActiveWalletProvider(wallet.provider, wallet.name);
    if (statusEl) {
      statusEl.textContent = `Connected: ${wallet.name}`;
      statusEl.style.color = "var(--green)";
    }
    return response.publicKey.toString();
  } catch (error) {
    const message = error && error.message ? error.message : "Wallet connection was rejected.";
    if (statusEl) {
      statusEl.textContent = message;
      statusEl.style.color = "var(--red)";
    }
    console.error(error);
    return null;
  }
}


async function connectWallet(statusEl) {
  return connectPhantom(statusEl);
}


function getRpcEndpoints() {
  const configured = window.APP_CONFIG && Array.isArray(window.APP_CONFIG.rpcEndpoints)
    ? window.APP_CONFIG.rpcEndpoints.filter(Boolean)
    : [];

  const defaults = [
    "https://api.devnet.solana.com",
    "https://solana-api.projectserum.com",
    "https://rpc.ankr.com/solana",
    "https://api.mainnet-beta.solana.com",
  ];

  return [...configured, ...defaults].filter((value, index, list) => list.indexOf(value) === index);
}


function createConnection(url) {
  const { Connection, clusterApiUrl } = solanaWeb3;
  if (url === "devnet" || url === "testnet" || url === "mainnet-beta") {
    return new Connection(clusterApiUrl(url), "confirmed");
  }
  return new Connection(url, "confirmed");
}


async function getConnectionWithBlockhash() {
  const endpoints = getRpcEndpoints();
  let lastError = null;

  for (const endpoint of endpoints) {
    try {
      const connection = createConnection(endpoint);
      const { blockhash } = await connection.getLatestBlockhash();
      return { connection, blockhash, endpoint };
    } catch (error) {
      lastError = error;
      console.warn(`RPC blockhash failed for ${endpoint}`, error);
    }
  }

  throw lastError || new Error("Unable to fetch a recent blockhash.");
}


async function sendSolFee(recipientAddress, amountSol, labelEl) {
  const pubkey = await connectPhantom(labelEl);
  if (!pubkey) return null;

  try {
    const { PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } = solanaWeb3;
    const provider = window.APP_ACTIVE_WALLET_PROVIDER || getWalletProvider()?.provider || window.solana;
    const fromPubkey = new PublicKey(pubkey);
    const toPubkey   = new PublicKey(recipientAddress);
    const lamports   = Math.round(amountSol * LAMPORTS_PER_SOL);

    const { connection: rpcConnection, blockhash, endpoint } = await getConnectionWithBlockhash();
    const tx = new Transaction({ recentBlockhash: blockhash, feePayer: fromPubkey });
    tx.add(SystemProgram.transfer({ fromPubkey, toPubkey, lamports }));

    if (!provider || typeof provider.signTransaction !== "function") {
      throw new Error("Selected wallet does not support transaction signing in this browser.");
    }

    const signedTx = await provider.signTransaction(tx);
    const signature = await rpcConnection.sendRawTransaction(signedTx.serialize());
    const latest = await rpcConnection.getLatestBlockhash();
    await rpcConnection.confirmTransaction(
      {
        signature,
        blockhash: latest.blockhash,
        lastValidBlockHeight: latest.lastValidBlockHeight,
      },
      "confirmed"
    );

    if (labelEl) {
      labelEl.textContent = "✓ " + signature.slice(0, 20) + "…";
      labelEl.style.color = "var(--green)";
    }
    console.log(`Payment RPC endpoint: ${endpoint}`);
    return signature;
  } catch (e) {
    console.error(e);
    if (labelEl) {
      labelEl.textContent = e && e.message ? e.message : "Transaction failed";
      labelEl.style.color = "var(--red)";
    }
    return null;
  }
}


function renderWalletSupport(targetId) {
  const target = document.getElementById(targetId);
  if (!target) {
    return;
  }

  const wallet = getWalletProvider();
  target.textContent = wallet ? `Wallet: ${wallet.name} ready` : "Wallet: not connected";
}


function renderRpcSupport(targetId) {
  const target = document.getElementById(targetId);
  if (!target) {
    return;
  }

  const endpoints = getRpcEndpoints();
  const activeEndpoint = window.APP_LAST_RPC_ENDPOINT || endpoints[0] || "not configured";
  target.textContent = `RPC: ${activeEndpoint}`;
}
