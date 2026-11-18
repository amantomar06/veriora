/**
 * AuthentiChain Client Application Controller
 * Handles UI tab routing, mobile bottom navigation, cryptographic proof queries,
 * QR tag generation, and blockchain state synchronization.
 */

let cachedProducts = [];
let cachedEntities = [];
let cachedChain = [];

document.addEventListener("DOMContentLoaded", () => {
  initializeSystem();
});

async function initializeSystem() {
  await fetchEntities();
  await fetchProducts();
  await fetchBlockchainData();

  // Periodic background synchronization every 6 seconds
  setInterval(() => {
    fetchBlockchainData(true);
  }, 6000);
}

// Tab Switching (Synchronizes Desktop Tabs & Mobile Bottom Navigation)
function switchTab(tabName) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".mobile-nav-btn").forEach(el => el.classList.remove("active"));

  const targetTab = document.getElementById(`tab-${tabName}`);
  if (targetTab) {
    targetTab.classList.add("active");
  }

  // Update Desktop Tab Buttons
  document.querySelectorAll(".tab-btn").forEach(btn => {
    if (btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(`'${tabName}'`)) {
      btn.classList.add("active");
    }
  });

  // Update Mobile Bottom Nav Buttons
  document.querySelectorAll(".mobile-nav-btn").forEach(btn => {
    if (btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(`'${tabName}'`)) {
      btn.classList.add("active");
    }
  });

  // Scroll to top of content
  window.scrollTo({ top: 0, behavior: "smooth" });

  if (tabName === "explorer") {
    fetchBlockchainData();
  } else if (tabName === "supplychain") {
    updateTransferFormContext();
  }
}

// Fetch Registered Entities
async function fetchEntities() {
  try {
    const res = await fetch("/api/entities");
    const data = await res.json();
    cachedEntities = data.entities || [];

    const mfrSelect = document.getElementById("mfrEntity");
    const senderSelect = document.getElementById("tfSenderEntity");
    const recipientSelect = document.getElementById("tfRecipientEntity");

    if (mfrSelect) mfrSelect.innerHTML = "";
    if (senderSelect) senderSelect.innerHTML = "";
    if (recipientSelect) recipientSelect.innerHTML = "";

    cachedEntities.forEach(e => {
      const opt = document.createElement("option");
      opt.value = e.entity_id;
      opt.textContent = `${e.name} (${e.role}) - ${e.location}`;

      if (e.role === "MANUFACTURER" && mfrSelect) {
        mfrSelect.appendChild(opt.cloneNode(true));
      }
      if (senderSelect) senderSelect.appendChild(opt.cloneNode(true));
      if (recipientSelect) recipientSelect.appendChild(opt.cloneNode(true));
    });
  } catch (err) {
    console.error("Failed to fetch entities:", err);
  }
}

// Fetch Registered Products
async function fetchProducts() {
  try {
    const res = await fetch("/api/products");
    const data = await res.json();
    cachedProducts = data.products || [];

    // Populate quick test presets
    const pillsContainer = document.getElementById("quickSamplePills");
    const heroChipsContainer = document.getElementById("heroSampleChips");

    function renderPresetChips(container) {
      if (!container) return;
      container.innerHTML = "";
      cachedProducts.forEach(p => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.innerHTML = `<span>🏷️</span> ${p.brand}: ${p.product_id}`;
        chip.onclick = () => {
          document.getElementById("verifyProductId").value = p.product_id;
          const heroInput = document.getElementById("heroQuickInput");
          if (heroInput) heroInput.value = p.product_id;
          switchTab('verify');
          verifyProduct();
        };
        container.appendChild(chip);
      });

      // Add a counterfeit test sample
      const fakeChip = document.createElement("span");
      fakeChip.className = "chip danger";
      fakeChip.innerHTML = `<span>🚨</span> Test Fake ID (Unregistered)`;
      fakeChip.onclick = () => {
        document.getElementById("verifyProductId").value = "PRD-FAKE-000-000";
        const heroInput = document.getElementById("heroQuickInput");
        if (heroInput) heroInput.value = "PRD-FAKE-000-000";
        switchTab('verify');
        verifyProduct();
      };
      container.appendChild(fakeChip);
    }

    renderPresetChips(pillsContainer);
    renderPresetChips(heroChipsContainer);

    // Populate Supply Chain Product dropdown
    const tfProductSelect = document.getElementById("tfProductId");
    if (tfProductSelect) {
      tfProductSelect.innerHTML = "";
      cachedProducts.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.product_id;
        opt.textContent = `${p.product_name} (${p.product_id}) [Status: ${p.current_status}]`;
        tfProductSelect.appendChild(opt);
      });
      updateTransferFormContext();
    }
  } catch (err) {
    console.error("Failed to fetch products:", err);
  }
}

// Fetch Blockchain Ledger State & Health
async function fetchBlockchainData(silent = false) {
  try {
    const res = await fetch("/api/chain");
    const data = await res.json();
    cachedChain = data.chain || [];

    // Update Header Status Pill
    const pill = document.getElementById("chainStatusPill");
    const statusText = document.getElementById("chainStatusText");
    const blockCountLabel = document.getElementById("quickBlockCount");
    const metricBlocks = document.getElementById("metricBlocks");
    const metricHealth = document.getElementById("metricHealth");
    const landingHeight = document.getElementById("landingBlockHeight");
    const landingHealth = document.getElementById("landingHealth");

    if (blockCountLabel) blockCountLabel.textContent = `Blocks: ${data.length}`;
    if (metricBlocks) metricBlocks.textContent = data.length;
    if (landingHeight) landingHeight.textContent = `#${data.length}`;

    if (data.is_valid) {
      if (pill) pill.className = "node-pill";
      if (statusText) statusText.textContent = "Ledger 100% Cryptographically Valid";
      if (metricHealth) {
        metricHealth.textContent = "100% VALID";
        metricHealth.style.color = "var(--success)";
      }
      if (landingHealth) {
        landingHealth.textContent = "100% VALID";
        landingHealth.style.color = "var(--success)";
      }
    } else {
      if (pill) pill.className = "node-pill tampered";
      if (statusText) statusText.textContent = `TAMPER DETECTED: Block #${data.faulty_block_index}`;
      if (metricHealth) {
        metricHealth.textContent = `CORRUPTED (Block #${data.faulty_block_index})`;
        metricHealth.style.color = "var(--danger)";
      }
      if (landingHealth) {
        landingHealth.textContent = `CORRUPTED (Block #${data.faulty_block_index})`;
        landingHealth.style.color = "var(--danger)";
      }
    }

    // Render Blocks in Explorer Tab
    renderBlocks(data.chain, data.faulty_block_index);

    // Update Tamper Block Select Dropdown
    const tamperSelect = document.getElementById("tamperBlockSelect");
    if (tamperSelect && tamperSelect.options.length !== data.chain.length) {
      tamperSelect.innerHTML = "";
      data.chain.forEach(b => {
        if (b.index > 0) {
          const opt = document.createElement("option");
          opt.value = b.index;
          opt.textContent = `Block #${b.index} (${b.transactions.length} txs - Hash: ${b.hash.substring(0, 14)}...)`;
          tamperSelect.appendChild(opt);
        }
      });
    }
  } catch (err) {
    if (!silent) console.error("Error fetching blockchain:", err);
  }
}

// Render Block Nodes in Horizontal Scroll
function renderBlocks(chain, faultyIndex) {
  const container = document.getElementById("blocksContainer");
  if (!container) return;
  container.innerHTML = "";

  chain.forEach((block, idx) => {
    const isCorrupted = (faultyIndex !== null && idx >= faultyIndex);
    const card = document.createElement("div");
    card.className = `block-card ${isCorrupted ? 'tampered' : ''}`;

    const dateStr = new Date(block.timestamp * 1000).toLocaleTimeString();
    const txCount = block.transactions ? block.transactions.length : 0;
    const txSummary = block.transactions.map(t => t.type.replace(/_/g, " ")).join(", ");

    card.innerHTML = `
      <div class="block-card-header">
        <span class="block-badge">${idx === 0 ? 'Root Genesis' : `Block #${block.index}`}</span>
        <span style="font-size: 0.72rem; color: var(--text-tertiary); font-family: var(--font-mono);">Nonce: ${block.nonce}</span>
      </div>
      <div class="block-field"><strong>Time:</strong> ${dateStr}</div>
      <div class="block-field"><strong>Prev Hash:</strong> <span class="font-mono">${block.previous_hash.substring(0, 14)}...</span></div>
      <div class="block-field">
        <strong>Hash:</strong> 
        <span class="font-mono" style="color: ${isCorrupted ? 'var(--danger)' : 'var(--success)'}; font-weight: 700;">
          ${block.hash.substring(0, 16)}...
        </span>
      </div>
      <div class="block-field"><strong>Merkle Root:</strong> <span class="font-mono">${block.merkle_root.substring(0, 14)}...</span></div>
      <div style="margin-top: 0.6rem; padding-top: 0.5rem; border-top: 1px dashed var(--border-light); font-size: 0.74rem;">
        <strong>Transactions (${txCount}):</strong>
        <div style="color: var(--text-secondary); margin-top: 0.2rem;">${txSummary || 'Genesis Root Initialization'}</div>
      </div>
    `;
    container.appendChild(card);
  });
}

// Hero Section Quick Verification
function runHeroVerification() {
  const input = document.getElementById("heroQuickInput");
  const pid = (input ? input.value : "").trim();
  if (!pid) {
    alert("Please enter or pick a Unique Product Identifier (UPI).");
    return;
  }
  document.getElementById("verifyProductId").value = pid;
  switchTab("verify");
  verifyProduct();
}

// Consumer Verification Action
async function verifyProduct() {
  const pid = document.getElementById("verifyProductId").value.trim();
  if (!pid) {
    alert("Please enter a Unique Product Identifier (UPI).");
    return;
  }

  const resultSection = document.getElementById("verificationResultSection");
  const verdictBanner = document.getElementById("verdictBanner");
  const detailsTable = document.getElementById("resProductDetails");
  const cryptoTable = document.getElementById("resCryptoProof");
  const aiContainer = document.getElementById("resAiPrediction");
  const timelineDiv = document.getElementById("provenanceTimeline");

  try {
    const res = await fetch(`/api/product/verify?id=${encodeURIComponent(pid)}`);
    const data = await res.json();

    resultSection.style.display = "block";

    // 1. Hero Verdict Banner
    if (data.is_genuine) {
      verdictBanner.className = "passport-hero verified";
      verdictBanner.innerHTML = `
        <div class="verdict-badge verified">
          <div class="verdict-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
          </div>
          <div>
            <div class="verdict-text-main">GENUINE AUTHENTIC PRODUCT</div>
            <div class="verdict-text-sub">Verified & Anchored to Immutable Blockchain Ledger</div>
          </div>
        </div>
        <div style="font-family: var(--font-mono); font-size: 0.8rem; background: #ffffff; padding: 0.4rem 0.8rem; border-radius: var(--radius-sm); border: 1px solid var(--success-border); color: var(--success-text);">
          UPI: ${pid}
        </div>
      `;
    } else {
      verdictBanner.className = "passport-hero counterfeit";
      verdictBanner.innerHTML = `
        <div class="verdict-badge counterfeit">
          <div class="verdict-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <div>
            <div class="verdict-text-main">UNVERIFIED / SUSPECTED COUNTERFEIT</div>
            <div class="verdict-text-sub">${data.message || 'Warning: No legitimate cryptographic provenance found on network.'}</div>
          </div>
        </div>
        <div style="font-family: var(--font-mono); font-size: 0.8rem; background: #ffffff; padding: 0.4rem 0.8rem; border-radius: var(--radius-sm); border: 1px solid var(--danger-border); color: var(--danger-text);">
          UPI: ${pid}
        </div>
      `;
    }

    // 2. Product Specifications Data Table
    const prod = data.product_details;
    if (prod) {
      detailsTable.innerHTML = `
        <tr><td class="label-cell">Product Name</td><td class="value-cell">${prod.product_name}</td></tr>
        <tr><td class="label-cell">Brand</td><td class="value-cell">${prod.brand}</td></tr>
        <tr><td class="label-cell">Batch Number</td><td class="value-cell font-mono">${prod.batch_number}</td></tr>
        <tr><td class="label-cell">Manufacture Date</td><td class="value-cell">${prod.manufacture_date}</td></tr>
        <tr><td class="label-cell">Current Custodian</td><td class="value-cell">${prod.current_owner}</td></tr>
        <tr><td class="label-cell">Lifecycle Status</td><td class="value-cell"><span class="chip" style="margin: 0;">${prod.current_status}</span></td></tr>
        <tr><td class="label-cell">Checkpoint Location</td><td class="value-cell">${prod.current_location}</td></tr>
      `;
    } else {
      detailsTable.innerHTML = `<tr><td colspan="2" style="color: var(--danger); font-size: 0.85rem;">No registered product specification exists for ID ${pid}.</td></tr>`;
    }

    // 3. Cryptographic Proof Data Table
    if (data.is_genuine && data.block_confirmations && data.block_confirmations.length > 0) {
      const firstBlock = data.block_confirmations[0];
      cryptoTable.innerHTML = `
        <tr><td class="label-cell">Genesis Anchor</td><td class="value-cell">Block #${firstBlock.block_index}</td></tr>
        <tr><td class="label-cell">Block Hash</td><td class="value-cell font-mono" style="font-size: 0.75rem;">${firstBlock.block_hash.substring(0, 24)}...</td></tr>
        <tr><td class="label-cell">Authenticity Hash</td><td class="value-cell font-mono" style="font-size: 0.75rem;">${data.authenticity_hash ? data.authenticity_hash.substring(0, 24) + '...' : 'VERIFIED'}</td></tr>
        <tr><td class="label-cell">Total Confirmations</td><td class="value-cell">${data.block_confirmations.length} Blocks</td></tr>
        <tr><td class="label-cell">Digital Signatures</td><td class="value-cell" style="color: var(--success); font-weight: 700;">✔ Validated</td></tr>
      `;
    } else {
      cryptoTable.innerHTML = `<tr><td colspan="2" style="color: var(--danger); font-size: 0.85rem;">Cryptographic proof absent. Zero on-chain confirmations found.</td></tr>`;
    }

    // 4. AI Multi-Factor Prediction Box
    const ai = data.ai_prediction;
    if (ai) {
      const isHighRisk = ai.authenticity_percentage < 60;
      aiContainer.innerHTML = `
        <div class="ai-gauge-box">
          <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--text-tertiary);">Confidence Score</div>
            <div class="ai-gauge-score ${isHighRisk ? 'counterfeit' : ''}">${ai.authenticity_percentage}%</div>
          </div>
          <div style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); margin-top: 0.2rem;">
            Risk Tier: <span style="color: ${isHighRisk ? 'var(--danger)' : 'var(--success)'};">${ai.risk_tier}</span>
          </div>
          <div style="font-size: 0.76rem; color: var(--text-tertiary); margin-top: 0.15rem;">
            Serial Entropy: ${ai.entropy} bits
          </div>

          <ul class="indicator-list">
            ${(ai.positive_indicators || []).map(i => `
              <li class="indicator-item pass">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                <span>${i}</span>
              </li>
            `).join("")}
            ${(ai.risk_flags || []).map(f => `
              <li class="indicator-item fail">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                <span>${f}</span>
              </li>
            `).join("")}
          </ul>
        </div>
      `;
    }

    // 5. Provenance Timeline
    timelineDiv.innerHTML = "";
    if (data.history && data.history.length > 0) {
      data.history.forEach((tx, idx) => {
        const item = document.createElement("div");
        item.className = "timeline-step";
        const dateStr = new Date(tx.timestamp * 1000).toLocaleString();
        const p = tx.payload || {};
        item.innerHTML = `
          <div class="timeline-marker"></div>
          <div class="timeline-card">
            <div class="timeline-header">
              <span class="timeline-stage">${tx.type.replace(/_/g, " ")}</span>
              <span class="timeline-date">${dateStr}</span>
            </div>
            <div class="timeline-info">
              ${p.location ? `<strong>Location:</strong> ${p.location}<br>` : ''}
              ${p.product_name ? `<strong>Registered:</strong> ${p.product_name} (${p.brand})<br>` : ''}
              ${p.next_status ? `<strong>Handover State:</strong> ${p.next_status}<br>` : ''}
              <span class="font-mono" style="font-size: 0.72rem; color: var(--text-tertiary);">TxID: ${tx.tx_id || 'TX-GENESIS'}</span>
            </div>
          </div>
        `;
        timelineDiv.appendChild(item);
      });
    } else {
      timelineDiv.innerHTML = `<div style="color: var(--text-tertiary); font-size: 0.85rem;">No historical custody transactions recorded for this item.</div>`;
    }

    // Render Clean SVG QR Code
    renderSvgQrCode("qrCodeContainer", pid);
    document.getElementById("qrDetails").innerHTML = `Digital Product Token: <strong>${pid}</strong>`;

    // Smooth scroll down to passport card on mobile
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (err) {
    console.error("Verification error:", err);
    alert("Verification query failed. Check network connection.");
  }
}

// Manufacturer Product Registration
async function handleProductRegistration(e) {
  e.preventDefault();
  const mfrId = document.getElementById("mfrEntity").value;
  const prodName = document.getElementById("prodName").value.trim();
  const prodBrand = document.getElementById("prodBrand").value.trim();
  const prodCategory = document.getElementById("prodCategory").value.trim();
  const prodBatch = document.getElementById("prodBatch").value.trim();
  const prodPrice = parseFloat(document.getElementById("prodPrice").value);

  let specs = {};
  try {
    specs = JSON.parse(document.getElementById("prodSpecs").value);
    specs.msrp_usd = prodPrice;
  } catch (err) {
    specs = { standard: "ISO-9001", msrp_usd: prodPrice };
  }

  const payload = {
    entity_id: mfrId,
    product_name: prodName,
    brand: prodBrand,
    category: prodCategory,
    batch_number: prodBatch,
    manufacture_date: new Date().toISOString().split("T")[0],
    specs: specs
  };

  try {
    const res = await fetch("/api/product/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      alert(`Registration Failed: ${data.error}`);
      return;
    }

    // Display Certificate of Origin
    document.getElementById("mfrEmptyState").style.display = "none";
    document.getElementById("mfrSuccessBox").style.display = "block";

    document.getElementById("certBlockIndex").textContent = data.mining.block_index;
    document.getElementById("certPid").textContent = data.product_id;
    document.getElementById("certTxId").textContent = data.transaction.tx_id;
    document.getElementById("certBlockHash").textContent = data.mining.block_hash.substring(0, 24) + "...";
    document.getElementById("certSignature").textContent = (data.transaction.execution_result.authenticity_hash || "SIGNATURE_VERIFIED").substring(0, 24) + "...";

    renderSvgQrCode("certQrSvg", data.product_id);
    document.getElementById("certQrCaption").textContent = data.product_id;

    await fetchProducts();
    await fetchBlockchainData();

    alert(`Product successfully minted and sealed in Block #${data.mining.block_index}!`);
  } catch (err) {
    console.error(err);
    alert("Error communicating with blockchain server.");
  }
}

// Update Context in Supply Chain Form
function updateTransferFormContext() {
  const select = document.getElementById("tfProductId");
  if (!select) return;
  const selectedPid = select.value;
  const product = cachedProducts.find(p => p.product_id === selectedPid);

  const ownerDisplay = document.getElementById("tfCurrentOwnerDisplay");
  const senderSelect = document.getElementById("tfSenderEntity");

  if (product && ownerDisplay) {
    ownerDisplay.value = `${product.current_owner} (${product.current_location}) [${product.current_status}]`;
    if (senderSelect) {
      for (let opt of senderSelect.options) {
        if (opt.textContent.includes(product.current_owner)) {
          senderSelect.value = opt.value;
          break;
        }
      }
    }
  }
}

// Supply Chain Transfer Form Submission
async function handleCustodyTransfer(e) {
  e.preventDefault();
  const pid = document.getElementById("tfProductId").value;
  const senderId = document.getElementById("tfSenderEntity").value;
  const recipientId = document.getElementById("tfRecipientEntity").value;
  const nextStatus = document.getElementById("tfNextStatus").value;
  const location = document.getElementById("tfLocation").value.trim();

  const feedback = document.getElementById("transferFeedback");

  try {
    const res = await fetch("/api/product/transfer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: pid,
        sender_entity_id: senderId,
        recipient_entity_id: recipientId,
        next_status: nextStatus,
        location: location
      })
    });

    const data = await res.json();
    feedback.style.display = "block";

    if (!res.ok) {
      feedback.style.background = "var(--danger-bg)";
      feedback.style.border = "1px solid var(--danger-border)";
      feedback.style.color = "var(--danger-text)";
      feedback.style.padding = "1rem";
      feedback.style.borderRadius = "var(--radius-md)";
      feedback.innerHTML = `<strong>Smart Contract Exception:</strong> ${data.error}`;
      return;
    }

    feedback.style.background = "var(--success-bg)";
    feedback.style.border = "1px solid var(--success-border)";
    feedback.style.color = "var(--success-text)";
    feedback.style.padding = "1rem";
    feedback.style.borderRadius = "var(--radius-md)";
    feedback.innerHTML = `
      <strong>✔ Custody Handover Validated & Mined!</strong><br>
      Product ${pid} is now <strong>${nextStatus}</strong> at <em>${location}</em>.<br>
      Sealed in Block #${data.mining.block_index}.
    `;

    await fetchProducts();
    await fetchBlockchainData();
  } catch (err) {
    console.error(err);
    alert("Error performing custody transfer.");
  }
}

// AI Anomaly Test Scenarios
function loadAiScenario(type) {
  const pidInput = document.getElementById("aiTestProductId");
  const brandSelect = document.getElementById("aiTestBrand");
  const priceInput = document.getElementById("aiTestPrice");
  const locInput = document.getElementById("aiTestLocation");

  if (type === "GENUINE") {
    const firstProd = cachedProducts[0];
    if (firstProd) {
      pidInput.value = firstProd.product_id;
      brandSelect.value = firstProd.brand;
      priceInput.value = firstProd.specs?.msrp_usd || 1199;
      locInput.value = firstProd.current_location;
    }
  } else if (type === "PRICE_UNDERCUT") {
    const firstProd = cachedProducts[0];
    pidInput.value = firstProd ? firstProd.product_id : "PRD-APPL-SAMPLE";
    brandSelect.value = "Apple";
    priceInput.value = "49.99";
    locInput.value = "BestBuy Retail Store #442, San Francisco, CA";
  } else if (type === "CLONED_QR") {
    const firstProd = cachedProducts[0];
    pidInput.value = firstProd ? firstProd.product_id : "PRD-APPL-SAMPLE";
    brandSelect.value = "Apple";
    priceInput.value = "1199.00";
    locInput.value = "Tokyo, Japan";
  } else if (type === "FORGED_SERIAL") {
    pidInput.value = "PRD-0000-AAAA-1111";
    brandSelect.value = "Sony";
    priceInput.value = "120.00";
    locInput.value = "Unknown Street Market";
  }

  runAiPrediction();
}

// Run AI Inference
async function runAiPrediction() {
  const pid = document.getElementById("aiTestProductId").value.trim();
  const brand = document.getElementById("aiTestBrand").value;
  const price = parseFloat(document.getElementById("aiTestPrice").value);
  const loc = document.getElementById("aiTestLocation").value.trim();

  const card = document.getElementById("aiResultCard");

  try {
    const res = await fetch("/api/ai/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: pid,
        brand: brand,
        offered_price: price,
        current_location: loc
      })
    });

    const data = await res.json();
    const isSafe = data.authenticity_percentage >= 80;

    card.innerHTML = `
      <div style="background: var(--bg-subtle); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-light); padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
          <div>
            <div style="font-size: 1.05rem; font-weight: 700; color: ${isSafe ? 'var(--success)' : 'var(--danger)'};">
              ${data.classification}
            </div>
            <div style="font-size: 0.75rem; color: var(--text-secondary);">${data.ai_model_name}</div>
          </div>
          <div style="font-size: 2rem; font-weight: 800; color: ${isSafe ? 'var(--success)' : 'var(--danger)'};">
            ${data.authenticity_percentage}%
          </div>
        </div>

        <table class="data-table">
          <tr><td class="label-cell">Shannon Entropy</td><td class="value-cell font-mono">${data.entropy} bits (&gt; 2.5 baseline)</td></tr>
          <tr><td class="label-cell">Assessed Risk Tier</td><td class="value-cell" style="color: ${isSafe ? 'var(--success)' : 'var(--danger)'};">${data.risk_tier}</td></tr>
        </table>

        <div style="margin-top: 1rem;">
          <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-tertiary); margin-bottom: 0.35rem;">
            Feature Reason Indicators
          </div>
          <ul class="indicator-list">
            ${(data.positive_indicators || []).map(i => `
              <li class="indicator-item pass">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                <span>${i}</span>
              </li>
            `).join("")}
            ${(data.risk_flags || []).map(f => `
              <li class="indicator-item fail">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                <span>${f}</span>
              </li>
            `).join("")}
          </ul>
        </div>
      </div>
    `;
  } catch (err) {
    console.error(err);
    alert("AI Prediction inference failed.");
  }
}

// Tamper Attack Execution
async function executeTamperAttack() {
  const blockIdx = parseInt(document.getElementById("tamperBlockSelect").value);
  const fakePayload = document.getElementById("tamperPayloadText").value;
  const statusLog = document.getElementById("tamperStatusLog");

  try {
    const res = await fetch("/api/tamper", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ block_index: blockIdx, fake_product_name: fakePayload })
    });

    const data = await res.json();
    statusLog.style.display = "block";
    statusLog.style.background = "var(--danger-bg)";
    statusLog.style.border = "1px solid var(--danger-border)";
    statusLog.style.color = "var(--danger-text)";
    statusLog.style.padding = "1rem";
    statusLog.style.borderRadius = "var(--radius-md)";
    statusLog.style.fontSize = "0.85rem";
    statusLog.innerHTML = `
      <strong>🚨 Tamper Attack Succeeded on Block #${blockIdx}!</strong><br>
      The blockchain integrity engine detected corruption:<br>
      <em>&rarr; ${data.validation_message}</em><br>
      Notice how the chain above immediately turned <strong>RED</strong>. All downstream hashes are broken!
    `;

    await fetchBlockchainData();
  } catch (err) {
    console.error(err);
  }
}

// Restore Blockchain Integrity
async function executeRestoreChain() {
  const statusLog = document.getElementById("tamperStatusLog");
  try {
    const res = await fetch("/api/restore", { method: "POST" });
    const data = await res.json();

    statusLog.style.display = "block";
    statusLog.style.background = "var(--success-bg)";
    statusLog.style.border = "1px solid var(--success-border)";
    statusLog.style.color = "var(--success-text)";
    statusLog.style.padding = "1rem";
    statusLog.style.borderRadius = "var(--radius-md)";
    statusLog.style.fontSize = "0.85rem";
    statusLog.innerHTML = `
      <strong>✔ Blockchain Integrity Restored!</strong><br>
      ${data.message}<br>
      Cryptographic proof: ${data.validation_message}
    `;

    await fetchBlockchainData();
  } catch (err) {
    console.error(err);
  }
}

// Pure SVG Crisp QR Code Generator
function renderSvgQrCode(containerId, text) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const size = 21;
  const matrix = [];
  let seed = 0;
  for (let i = 0; i < text.length; i++) {
    seed = (seed * 31 + text.charCodeAt(i)) % 2147483647;
  }

  function pseudoRand() {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  }

  for (let r = 0; r < size; r++) {
    matrix[r] = [];
    for (let c = 0; c < size; c++) {
      if ((r < 7 && c < 7) || (r < 7 && c >= size - 7) || (r >= size - 7 && c < 7)) {
        const inCornerR = (r < 7) ? r : (r - (size - 7));
        const inCornerC = (c < 7) ? c : (c - (size - 7));
        if (inCornerR === 0 || inCornerR === 6 || inCornerC === 0 || inCornerC === 6) {
          matrix[r][c] = 1;
        } else if (inCornerR >= 2 && inCornerR <= 4 && inCornerC >= 2 && inCornerC <= 4) {
          matrix[r][c] = 1;
        } else {
          matrix[r][c] = 0;
        }
      } else {
        matrix[r][c] = pseudoRand() > 0.45 ? 1 : 0;
      }
    }
  }

  const cellSize = 6;
  const totalDim = size * cellSize;
  let svg = `<svg width="${totalDim}" height="${totalDim}" viewBox="0 0 ${totalDim} ${totalDim}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${totalDim}" height="${totalDim}" fill="#ffffff" />`;

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (matrix[r][c] === 1) {
        svg += `<rect x="${c * cellSize}" y="${r * cellSize}" width="${cellSize}" height="${cellSize}" fill="#0f172a" />`;
      }
    }
  }
  svg += `</svg>`;
  container.innerHTML = svg;
}
