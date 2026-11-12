getStores().then(console.log);

async function renderStores() {
  const grid = document.getElementById("store-grid");
  try {
    const stores = await getStores();
    grid.innerHTML = stores.map(s => {
      const pct = s.latest.capacityPct;
      const crowd = s.latest.status === "ok"
        ? `${pct}% full (${s.latest.level})`
        : "Camera unavailable";
      return `
        <div class="store-card">
          <div class="store-photo" style="background-color:${crowdColor(pct)}">Store Photo</div>
          <div class="store-info">
            <h3>${s.name}</h3>
            <h4>${s.address}</h4>
            <p>Crowd Level: ${crowd}</p>
          </div>
        </div>`;
    }).join("");
  } catch (err) {
    grid.textContent = "Could not load stores: " + err.message;
  }
}

renderStores();