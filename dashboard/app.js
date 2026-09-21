(function () {
  "use strict";

  const D = DASHBOARD_DATA;
  const COLOR = {
    series1: "#3987e5",
    seriesFill: "rgba(57, 135, 229, 0.16)",
    faint: "rgba(57, 135, 229, 0.20)",
    grid: "#2c2c2a",
    baseline: "#383835",
    textSecondary: "#c3c2b7",
    textMuted: "#898781",
    surface: "#1a1a19",
  };

  const pct = (v, digits = 1) => `${(v * 100).toFixed(digits)}%`;
  const usd = (v, opts = {}) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0, ...opts }).format(v);
  const usdCompact = (v) =>
    new Intl.NumberFormat("en-US", { notation: "compact", style: "currency", currency: "USD", maximumFractionDigits: 1 }).format(v);

  // ---------- Headline cards ----------
  document.getElementById("headline-4pct").textContent = pct(D.headline.fourPctSuccessRate);
  document.getElementById("headline-safe").textContent =
    D.headline.safeWithdrawalRate != null ? pct(D.headline.safeWithdrawalRate, 2) : "N/A";

  // ---------- Assumptions grid ----------
  const a = D.assumptions;
  const assumptionItems = [
    ["Starting Portfolio", usd(a.startingPortfolio)],
    ["Retirement Age", `${a.retirementAge}`],
    ["Time Horizon", `${a.horizonYears} yrs (to age ${a.endAge})`],
    ["Allocation", `${Math.round(a.stockAllocation * 100)}/${Math.round(a.bondAllocation * 100)} Stock/Bond`],
    ["Federal Tax Rate", pct(a.federalTaxRate, 0)],
    ["RMD Start Age", `${a.rmdStartAge} (SECURE 2.0)`],
    ["Traditional / Roth Split", `${Math.round(a.traditionalFraction * 100)}/${Math.round(a.rothFraction * 100)}`],
    ["Simulations", a.nSimulations.toLocaleString()],
  ];
  const grid = document.getElementById("assumptions-grid");
  assumptionItems.forEach(([k, v]) => {
    const item = document.createElement("div");
    item.className = "assumption-item";
    item.innerHTML = `<div class="k">${k}</div><div class="v">${v}</div>`;
    grid.appendChild(item);
  });

  document.getElementById("paths-subtitle").textContent =
    `A random sample of ${D.samplePaths.paths.length} simulated paths at the ` +
    `${pct(D.samplePaths.withdrawalRate, 2)} withdrawal rate, with the median and 10th–90th ` +
    `percentile band across all ${a.nSimulations.toLocaleString()} simulations.`;

  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.color = COLOR.textMuted;

  // ---------- Chart 1: Success rate vs withdrawal rate ----------
  const sweep = D.successSweep;
  const rateLabels = sweep.withdrawalRates.map((r) => pct(r, 2));

  new Chart(document.getElementById("successChart"), {
    type: "line",
    data: {
      labels: rateLabels,
      datasets: [
        {
          label: "Success rate",
          data: sweep.successRates.map((r) => r * 100),
          borderColor: COLOR.series1,
          backgroundColor: COLOR.series1,
          borderWidth: 2.5,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: COLOR.series1,
          pointBorderColor: COLOR.surface,
          pointBorderWidth: 1.5,
          tension: 0.15,
          fill: false,
          order: 1,
        },
        {
          label: "90% target",
          data: sweep.withdrawalRates.map(() => 90),
          borderColor: COLOR.baseline,
          borderWidth: 1.5,
          borderDash: [5, 4],
          pointRadius: 0,
          fill: false,
          order: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          labels: { color: COLOR.textSecondary, usePointStyle: true, boxWidth: 8, padding: 16 },
        },
        tooltip: {
          backgroundColor: "#101010",
          borderColor: COLOR.grid,
          borderWidth: 1,
          titleColor: "#ffffff",
          bodyColor: COLOR.textSecondary,
          padding: 10,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%`,
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: "First-year withdrawal rate", color: COLOR.textSecondary },
          grid: { color: "transparent" },
          ticks: { color: COLOR.textMuted },
        },
        y: {
          min: 0,
          max: 100,
          title: { display: true, text: "Success rate", color: COLOR.textSecondary },
          grid: { color: COLOR.grid },
          ticks: { color: COLOR.textMuted, callback: (v) => `${v}%` },
        },
      },
    },
  });

  // ---------- Chart 2: Sample simulated portfolio paths ----------
  const sp = D.samplePaths;
  const sampleDatasets = sp.paths.map((path, i) => ({
    label: `Sample path ${i + 1}`,
    data: path,
    borderColor: COLOR.faint,
    borderWidth: 1,
    pointRadius: 0,
    fill: false,
    order: 3,
    sample: true,
  }));

  new Chart(document.getElementById("pathsChart"), {
    type: "line",
    data: {
      labels: sp.years,
      datasets: [
        {
          label: "10th percentile",
          data: sp.p10,
          borderColor: "transparent",
          backgroundColor: COLOR.seriesFill,
          borderWidth: 0,
          pointRadius: 0,
          fill: "+1",
          order: 1,
        },
        {
          label: "90th percentile",
          data: sp.p90,
          borderColor: "transparent",
          borderWidth: 0,
          pointRadius: 0,
          fill: false,
          order: 1,
        },
        ...sampleDatasets,
        {
          label: "Median path",
          data: sp.median,
          borderColor: COLOR.series1,
          borderWidth: 2.5,
          pointRadius: 0,
          fill: false,
          order: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "nearest", intersect: false, axis: "x" },
      plugins: {
        legend: {
          labels: {
            color: COLOR.textSecondary,
            usePointStyle: true,
            boxWidth: 8,
            padding: 16,
            filter: (item) => !item.text.startsWith("Sample path") && item.text !== "90th percentile",
          },
          onClick: () => {}, // sample paths aren't in the legend; keep default toggle for the rest
        },
        tooltip: {
          backgroundColor: "#101010",
          borderColor: COLOR.grid,
          borderWidth: 1,
          titleColor: "#ffffff",
          bodyColor: COLOR.textSecondary,
          padding: 10,
          filter: (item) => ["Median path", "10th percentile", "90th percentile"].includes(item.dataset.label),
          callbacks: {
            title: (items) => `Year ${items[0].label}`,
            label: (ctx) => `${ctx.dataset.label}: ${usdCompact(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: "Years into retirement", color: COLOR.textSecondary },
          grid: { color: "transparent" },
          ticks: { color: COLOR.textMuted, maxTicksLimit: 8 },
        },
        y: {
          title: { display: true, text: "Portfolio value", color: COLOR.textSecondary },
          grid: { color: COLOR.grid },
          ticks: { color: COLOR.textMuted, callback: (v) => usdCompact(v) },
        },
      },
    },
  });
})();
