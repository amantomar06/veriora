/**
 * AuthentiChain Frontend Controller
 * Handles UI interactions, API calls, QR generation, and state management.
 */

let cachedProducts = [];
let cachedEntities = [];
let cachedChain = [];

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  initializeSystem();
});

async function initializeSystem() {
  await fetchEntities();
  await fetchProducts();
  await fetchBlockchainData();
  
  // Set up periodic sync every 6 seconds
  setInterval(() => {
    fetchBlockchainData(true);
  }, 6000);
}

// Tab Switching
function switchTab(tabName) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

  const targetTab = document.getElementById(`tab-${tabName}`);
  if (targetTab) {
    targetTab.classList.add("active");
  }

  // Highlight active button
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach(btn => {
    if (btn.getAttribute("onclick").includes(`'${tabName}'`)) {
      btn.classList.add("active");
    }
  });

  if (tabName === "explorer") {
    fetchBlockchainData();
  } else if (tabName === "supplychain") {
    updateTransferFormContext();
  }
}

// Fetch Authorized Entities
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
      opt.textContent = `[${e.role}] ${e.name} (${e.location})`;

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

    // Populate quick test sample pills in Verification tab
    const pillsContainer = document.getElementById("quickSamplePills");
    if (pillsContainer) {
      pillsContainer.innerHTML = "";
      cachedProducts.forEach(p => {
        const pill = document.createElement("span");
        pill.className = "pill-item";
        pill.textContent = `🏷️ ${p.brand}: ${p.product_id}`;
        pill.onclick = () => {
          document.getElementById("verifyProductId").value = p.product_id;
          verifyProduct();
        };
        pillsContainer.appendChild(pill);
      });

      // Add a fake sample for testing
      const fakePill = document.createElement("span");
      fakePill.className = "pill-item";
      fakePill.style.color = "#f87171";
      fakePill.textContent = "🚨 Test Fake ID (Unregistered)";
      fakePill.onclick = () => {
        document.getElementById("verifyProductId").value = "PRD-FAKE-000-000";
        verifyProduct();
      };
      pillsContainer.appendChild(fakePill);
    }

    // Populate Supply Chain Product dropdown
    const tfProductSelect = document.getElementById("tfProductId");
    if (tfProductSelect) {
      tfProductSelect.innerHTML = "";
      cachedProducts.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.product_id;
        opt.textContent = `${p.product_name} (${p.product_id}) - Current: ${p.current_status}`;
        tfProductSelect.appendChild(opt);
      });
      updateTransferFormContext();
    }
  } catch (err) {
    console.error("Failed to fetch products:", err);
  }
}

// Fetch Blockchain Ledger & Health
async function fetchBlockchainData(silent = false) {
  try {
    const res = await fetch("/api/chain");
    const data = await res.json();
    cachedChain = data.chain || [];

    // Update Header Pill
    const pill = document.getElementById("chainStatusPill");
    const blockCountLabel = document.getElementById("quickBlockCount");
    const metricBlocks = document.getElementById("metricBlocks");
    const metricHealth = document.getElementById("metricHealth");

    if (blockCountLabel) blockCountLabel.textContent = `Blocks: ${data.length}`;
    if (metricBlocks) metricBlocks.textContent = data.length;

    if (data.is_valid) {
      pill.className = "status-pill";
      pill.innerHTML = `<span style="font-size: 0.6rem;">●</span> Ledger Online: 100% Cryptographically Valid`;
      if (metricHealth) {
        metricHealth.textContent = "100% VALID";
        metricHealth.style.color = "#34d399";
      }
    } else {
      pill.className = "status-pill tampered";
      pill.innerHTML = `⚠️ CORRUPTION DETECTED at Block #${data.faulty_block_index}!`;
      if (metricHealth) {
        metricHealth.textContent = `CORRUPTED (Block #${data.faulty_block_index})`;
        metricHealth.style.color = "#ef4444";
      }
    }

    // Render Blocks in Explorer Tab
    renderBlocks(data.chain, data.faulty_block_index);

    // Update Tamper Select dropdown
    const tamperSelect = document.getElementById("tamperBlockSelect");
    if (tamperSelect && tamperSelect.options.length !== data.chain.length) {
      tamperSelect.innerHTML = "";
      data.chain.forEach(b => {
        if (b.index > 0) { // Skip genesis for better demo
          const opt = document.createElement("option");
          opt.value = b.index;
          opt.textContent = `Block #${b.index} (${b.transactions.length} txs - Hash: ${b.hash.substring(0, 12)}...)`;
          tamperSelect.appendChild(opt);
        }
      });
    }
  } catch (err) {
    if (!silent) console.error("Error fetching blockchain:", err);
  }
}

// Render Block Nodes in Explorer
function renderBlocks(chain, faultyIndex) {
  const container = document.getElementById("blocksContainer");
  if (!container) return;
  container.innerHTML = "";

  chain.forEach((block, idx) => {
    const isCorrupted = (faultyIndex !== null && idx >= faultyIndex);
    const card = document.createElement("div");
    card.className = `block-node ${isCorrupted ? 'tampered' : ''}`;

    const dateStr = new Date(block.timestamp * 1000).toLocaleTimeString();
    const txCount = block.transactions ? block.transactions.length : 0;
    const txSummary = block.transactions.map(t => t.type).join(", ");

    card.innerHTML = `
      <div class="block-header">
        <span class="block-num">${idx === 0 ? '🌱 Genesis' : `Block #${block.index}`}</span>
        <span style="font-size: 0.75rem; color: #a5b4fc;">Nonce: ${block.nonce}</span>
      </div>
      <div class="block-meta">
        <div><strong>Time:</strong> ${dateStr}</div>
        <div><strong>Prev Hash:</strong> ${block.previous_hash.substring(0, 16)}...</div>
        <div><strong>Block Hash:</strong> <span style="color: ${isCorrupted ? '#f87171' : '#34d399'}; font-weight: bold;">${block.hash.substring(0, 18)}...</span></div>
        <div><strong>Merkle Root:</strong> ${block.merkle_root.substring(0, 16)}...</div>
        <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed var(--border-color);">
          <strong>Transactions (${txCount}):</strong>
          <div style="color: #cbd5e1; font-size: 0.75rem; margin-top: 0.2rem;">${txSummary || 'None'}</div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// Consumer Verification Function
async function verifyProduct() {
  const pid = document.getElementById("verifyProductId").value.trim();
  if (!pid) {
    alert("Please enter a Unique Product ID (UPI) to verify.");
    return;
  }

  const resultSection = document.getElementById("verificationResultSection");
  const verdictBanner = document.getElementById("verdictBanner");
  const detailsDiv = document.getElementById("resProductDetails");
  const cryptoDiv = document.getElementById("resCryptoProof");
  const aiDiv = document.getElementById("resAiPrediction");
  const timelineDiv = document.getElementById("provenanceTimeline");

  try {
    const res = await fetch(`/api/product/verify?id=${encodeURIComponent(pid)}`);
    const data = await res.json();

    resultSection.style.display = "block";

    // 1. Verdict Banner
    if (data.is_genuine) {
      verdictBanner.className = "verdict-banner genuine";
      verdictBanner.innerHTML = `
        <span style="font-size: 1.6rem;">🛡️</span>
        <div>
          <div>VERIFIED GENUINE PRODUCT</div>
          <div style="font-size: 0.85rem; font-weight: normal; color: #a7f3d0;">Anchored to Immutable Blockchain Ledger</div>
        </div>
      `;
    } else {
      verdictBanner.className = "verdict-banner counterfeit";
      verdictBanner.innerHTML = `
        <span style="font-size: 1.6rem;">🚨</span>
        <div>
          <div>${data.verdict || 'COUNTERFEIT / UNREGISTERED PRODUCT'}</div>
          <div style="font-size: 0.85rem; font-weight: normal; color: #fecaca;">${data.message || 'Warning: No legitimate cryptographic provenance found.'}</div>
        </div>
      `;
    }

    // 2. Product Specifications
    const prod = data.product_details;
    if (prod) {
      detailsDiv.innerHTML = `
        <div><strong>Product:</strong> ${prod.product_name}</div>
        <div><strong>Brand:</strong> ${prod.brand}</div>
        <div><strong>Batch No:</strong> ${prod.batch_number}</div>
        <div><strong>Mfg Date:</strong> ${prod.manufacture_date}</div>
        <div><strong>Current Custodian:</strong> ${prod.current_owner}</div>
        <div><strong>Current Status:</strong> <span class="pill-item">${prod.current_status}</span></div>
        <div><strong>Checkpoint Location:</strong> ${prod.current_location}</div>
      `;
    } else {
      detailsDiv.innerHTML = `<span style="color: #f87171;">No registered product specification exists for ID ${pid}.</span>`;
    }

    // 3. Cryptographic Proof
    if (data.is_genuine && data.block_confirmations) {
      const firstBlock = data.block_confirmations[0];
      cryptoDiv.innerHTML = `
        <div><strong>Genesis Anchor:</strong> Block #${firstBlock.block_index}</div>
        <div><strong>Block Hash:</strong> <span style="font-size: 0.75rem;">${firstBlock.block_hash}</span></div>
        <div><strong>Authenticity Hash:</strong> <span style="font-size: 0.75rem;">${data.authenticity_hash}</span></div>
        <div><strong>Total On-Chain Confirmations:</strong> ${data.block_confirmations.length} Blocks</div>
        <div style="color: #34d399; font-weight: 500; margin-top: 0.4rem;">✔ Digital Signatures Validated</div>
      `;
    } else {
      cryptoDiv.innerHTML = `<span style="color: #f87171;">Cryptographic proof absent. Zero block confirmations found.</span>`;
    }

    // 4. AI Prediction Breakdown
    const ai = data.ai_prediction;
    if (ai) {
      aiDiv.innerHTML = `
        <div><strong>AI Confidence:</strong> <span style="font-size: 1.1rem; font-weight: bold; color: ${ai.authenticity_percentage > 70 ? '#34d399' : '#f87171'}">${ai.authenticity_percentage}%</span></div>
        <div><strong>Risk Tier:</strong> ${ai.risk_tier}</div>
        <div><strong>Serial Entropy:</strong> ${ai.entropy} bits</div>
        <div style="margin-top: 0.5rem; font-size: 0.78rem;">
          <strong>Indicators:</strong>
          <ul style="padding-left: 1rem; margin-top: 0.25rem;">
            ${(ai.positive_indicators || []).map(i => `<li style="color: #34d399;">✔ ${i}</li>`).join("")}
            ${(ai.risk_flags || []).map(f => `<li style="color: #f87171;">✖ ${f}</li>`).join("")}
          </ul>
        </div>
      `;
    }

    // 5. Timeline of Custody
    timelineDiv.innerHTML = "";
    if (data.history && data.history.length > 0) {
      data.history.forEach(tx => {
        const item = document.createElement("div");
        item.className = "timeline-item";
        const dateStr = new Date(tx.timestamp * 1000).toLocaleString();
        const p = tx.payload || {};
        item.innerHTML = `
          <div class="timeline-dot"></div>
          <div class="timeline-content">
            <div style="font-weight: bold; color: #818cf8;">${tx.type.replace(/_/g, " ")}</div>
            <div class="timeline-time">${dateStr}</div>
            <div style="margin-top: 0.3rem;">
              ${p.location ? `<strong>Location:</strong> ${p.location}<br>` : ''}
              ${p.product_name ? `<strong>Registered:</strong> ${p.product_name} (${p.brand})<br>` : ''}
              ${p.next_status ? `<strong>New Status:</strong> ${p.next_status}<br>` : ''}
              <span style="font-family: monospace; font-size: 0.7rem; color: var(--text-muted);">TxID: ${tx.tx_id || 'TX-ANCHORED'}</span>
            </div>
          </div>
        `;
        timelineDiv.appendChild(item);
      });
    } else {
      timelineDiv.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">No historical custody transactions recorded for this item.</div>`;
    }

    // Render QR Code Preview
    renderSvgQrCode("qrCodeContainer", pid);
    document.getElementById("qrDetails").innerHTML = `Digital Product Token: <strong>${pid}</strong>`;

  } catch (err) {
    console.error("Verification error:", err);
    alert("Verification request failed. Check server connection.");
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

    // Display Certificate
    document.getElementById("mfrEmptyState").style.display = "none";
    document.getElementById("mfrSuccessBox").style.display = "block";

    document.getElementById("certBlockIndex").textContent = data.mining.block_index;
    document.getElementById("certPid").textContent = data.product_id;
    document.getElementById("certTxId").textContent = data.transaction.tx_id;
    document.getElementById("certBlockHash").textContent = data.mining.block_hash;
    document.getElementById("certSignature").textContent = data.transaction.execution_result.authenticity_hash || "SIGNATURE_VERIFIED_ON_CHAIN";

    renderSvgQrCode("certQrSvg", data.product_id);
    document.getElementById("certQrCaption").textContent = data.product_id;

    // Refresh products and chain
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
    // Pre-select sender that matches current owner if possible
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
      feedback.style.background = "rgba(239, 68, 68, 0.2)";
      feedback.style.border = "1px solid #ef4444";
      feedback.style.color = "#f87171";
      feedback.style.padding = "1rem";
      feedback.style.borderRadius = "8px";
      feedback.innerHTML = `<strong>Smart Contract Exception:</strong> ${data.error}`;
      return;
    }

    feedback.style.background = "rgba(16, 185, 129, 0.2)";
    feedback.style.border = "1px solid #10b981";
    feedback.style.color = "#34d399";
    feedback.style.padding = "1rem";
    feedback.style.borderRadius = "8px";
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
    pidInput.value = firstProd ? firstProd.product_id : "PRD-APPL-GENUINE-SAMPLE";
    brandSelect.value = "Apple";
    priceInput.value = "49.99"; // Extreme undercutting
    locInput.value = "BestBuy Retail Store #442, San Francisco, CA";
  } else if (type === "CLONED_QR") {
    const firstProd = cachedProducts[0];
    pidInput.value = firstProd ? firstProd.product_id : "PRD-APPL-SAMPLE";
    brandSelect.value = "Apple";
    priceInput.value = "1199.00";
    locInput.value = "Tokyo, Japan"; // Distant location scanned instantly
  } else if (type === "FORGED_SERIAL") {
    pidInput.value = "PRD-0000-AAAA-1111"; // Extremely low entropy
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
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
        <div>
          <div style="font-size: 1.1rem; font-weight: bold; color: ${isSafe ? '#34d399' : '#f87171'};">
            ${data.classification}
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">${data.ai_model_name}</div>
        </div>
        <div style="font-size: 2rem; font-weight: 800; color: ${isSafe ? '#34d399' : '#f87171'};">
          ${data.authenticity_percentage}%
        </div>
      </div>

      <div style="font-size: 0.85rem; line-height: 1.8;">
        <div><strong>Shannon Entropy:</strong> ${data.entropy} bits (Threshold: &gt; 2.5)</div>
        <div><strong>Assessed Risk Tier:</strong> ${data.risk_tier}</div>

        <div style="margin-top: 0.75rem;">
          <strong>Model Reasoning & Feature Indicators:</strong>
          <ul style="padding-left: 1.25rem; margin-top: 0.25rem;">
            ${(data.positive_indicators || []).map(i => `<li style="color: #34d399;">✔ ${i}</li>`).join("")}
            ${(data.risk_flags || []).map(f => `<li style="color: #f87171;">✖ ${f}</li>`).join("")}
          </ul>
        </div>
      </div>
    `;
  } catch (err) {
    console.error(err);
    alert("AI Prediction inference failed.");
  }
}

// Tamper Attack Execution (Deliverable 7)
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
    statusLog.style.background = "rgba(239, 68, 68, 0.2)";
    statusLog.style.border = "1px solid #ef4444";
    statusLog.style.color = "#f87171";
    statusLog.style.padding = "1rem";
    statusLog.style.borderRadius = "8px";
    statusLog.style.fontSize = "0.9rem";
    statusLog.innerHTML = `
      <strong>🚨 Tamper Attack Succeeded on Block #${blockIdx}!</strong><br>
      The blockchain verification engine recomputed hashes across all blocks:<br>
      <em>&rarr; ${data.validation_message}</em><br>
      Notice how the chain above immediately turned <strong>RED</strong>. All downstream blocks are invalid!
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
    statusLog.style.background = "rgba(16, 185, 129, 0.2)";
    statusLog.style.border = "1px solid #10b981";
    statusLog.style.color = "#34d399";
    statusLog.style.padding = "1rem";
    statusLog.style.borderRadius = "8px";
    statusLog.style.fontSize = "0.9rem";
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

// Pure SVG Pseudo-QR Code Generator for zero-dependency offline rendering
function renderSvgQrCode(containerId, text) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Generate deterministic 21x21 QR-like matrix from text hash
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
      // Finder patterns (3 corners 7x7)
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
