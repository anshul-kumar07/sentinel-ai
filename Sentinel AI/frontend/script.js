// INTRO FLOW
const startBtn = document.getElementById("startBtn");
const intro = document.getElementById("intro");
const app = document.getElementById("app");
const imageInput = document.querySelector('input[type="file"]');
const ocrBlock = document.getElementById("ocrBlock");
const ocrText = document.getElementById("ocrText");

startBtn.addEventListener("click", () => {
  intro.classList.add("fade-out");

  setTimeout(() => {
    intro.style.display = "none";
    app.classList.remove("hidden");
    app.classList.add("fade-in");
  }, 1200);
});


// ANALYZE MESSAGE
async function analyzeMessage() {
  const message = document.getElementById("messageInput").value.trim();
  const btn = document.getElementById("analyzeBtn");

  if (!message) {
    alert("Please paste a message.");
    return;
  }

  btn.innerText = "Analyzing...";
  btn.disabled = true;

  try {
    const res = await fetch("http://127.0.0.1:5000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    const data = await res.json();
    renderResult(data);

  } catch (err) {
    alert("Backend not responding.");
  }

  btn.innerText = "Analyze Message";
  btn.disabled = false;
}

// OCR IMAGE ANALYSIS
imageInput.addEventListener("change", async () => {
  const file = imageInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("image", file);

  ocrBlock.classList.remove("hidden");
  ocrText.value = "Extracting text from image...";
  document.getElementById("outputCard").classList.add("hidden");

  try {
    const res = await fetch("http://127.0.0.1:5000/analyze-image", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    // ✅ SHOW OCR TEXT
    if (data.extracted_text && data.extracted_text.trim() !== "") {
      ocrText.value = data.extracted_text;
    
      // OPTIONAL: auto-fill message box
      document.getElementById("messageInput").value = data.extracted_text;
    } else {
      ocrText.value = "No readable text detected.";
    }

  } catch (err) {
    ocrText.value = "OCR failed. Backend not responding.";
  }
});


// RENDER RESULT (SMOOTH + RIGHT SIDE)
function renderResult(data) {
  const output = document.getElementById("outputCard");
  const shell = document.querySelector(".app-shell");

  output.classList.remove("hidden");
  shell.classList.add("expanded");

  document.getElementById("riskTitle").innerText =
    `Overall Risk: ${data.overall_risk}`;

  const list = document.getElementById("reasonList");
  list.innerHTML = "";

  data.analysis.forEach((item, i) => {
    const div = document.createElement("div");
    div.className = "reason-card";
    div.style.animationDelay = `${i * 0.25}s`;

    div.innerHTML = `
      <span>${i + 1}️⃣ ${item.title}</span>
      <p>${item.text}</p>
    `;

    list.appendChild(div);
  });

  document.getElementById("recommendationText").innerText =
    data.recommendation;
// CONFIDENCE SCORE BAR
const score = data.confidence_score || 0;
const percent = Math.min(score, 100);

const fill = document.getElementById("confidenceFill");
const label = document.getElementById("confidencePercent");

label.innerText = `${percent}%`;
fill.style.width = `${percent}%`;

// Color logic based on risk
if (percent < 30) {
  fill.style.backgroundColor = "#2ecc71"; // green
} else if (percent < 60) {
  fill.style.backgroundColor = "#f1c40f"; // yellow
} else if (percent < 80) {
  fill.style.backgroundColor = "#e67e22"; // orange
} else {
  fill.style.backgroundColor = "#e74c3c"; // red
}

}
