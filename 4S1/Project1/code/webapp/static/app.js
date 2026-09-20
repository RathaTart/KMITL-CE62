/* Results explorer. Every number rendered here comes from /api/analysis, which
   reads the run artifacts — nothing is hard-coded, so the page cannot drift from
   what was measured. */

let LANG = localStorage.getItem("lisa_lang") || "en";
let A = null;          // analysis payload
let ROWS = [];         // current browse rows
let PIPE = [];         // saved BLIP-2 -> DINO -> SAM comparison rows
let FILE = null;       // pending upload
let POLL = null;
let VIEW_TASK = null;
let VIEW_INDEX = -1;

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const T = (k) => (I18N[LANG] && I18N[LANG][k]) || I18N.en[k] || k;
const n1 = (v) => (v === null || v === undefined ? "—" : (100 * v).toFixed(1));
const f1 = (v) => (v === null || v === undefined ? "—" : v.toFixed(1));
const esc = (s) =>
  String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ---------------- language ---------------- */
function applyLang() {
  document.documentElement.lang = LANG;
  $("#lang-en").setAttribute("aria-pressed", LANG === "en");
  $("#lang-th").setAttribute("aria-pressed", LANG === "th");
  document.title = T("title");
  $$("[data-i]").forEach((el) => { el.textContent = T(el.dataset.i); });
  $("#custom-prompt").placeholder = T("y_custom_ph");
  updateTrySystem();
  if (A) { renderResults(); renderPipeline(); renderFilters(); renderBrowse(); renderChips(); }
  if ($("#viewer").classList.contains("on")) refreshViewerNav();
  updateStatus();
}
function setLang(l) { LANG = l; localStorage.setItem("lisa_lang", l); applyLang(); }

/* ---------------- tabs ---------------- */
$$("nav.tabs button").forEach((b) => {
  b.onclick = () => {
    $$("nav.tabs button").forEach((x) => x.setAttribute("aria-selected", x === b));
    $$("section.panel").forEach((p) => p.classList.remove("on"));
    $("#panel-" + b.dataset.tab).classList.add("on");
  };
});

/* ---------------- charts ---------------- */
function bars(rows, labw) {
  const grid = `<div class="gridline"><i style="left:25%"></i><i style="left:50%"></i><i style="left:75%"></i></div>`;
  const body = rows.map((r) => `
    <div class="row">
      <div class="lab">${esc(r.label)}${r.sub ? ` <i>${esc(r.sub)}</i>` : ""}</div>
      <div class="track" data-tip="${esc(r.tip)}">${grid}<div class="bar" style="width:${Math.max(0, Math.min(100, r.value)).toFixed(2)}%"></div></div>
      <div class="val">${r.value.toFixed(1)}</div>
    </div>`).join("");
  return `<div style="--labw:${labw}px">${body}
    <div class="axis" aria-hidden="true"><div></div>
      <div class="ticks"><i style="left:0">0</i><i style="left:25%">25</i>
      <i style="left:50%">50</i><i style="left:75%">75</i><i style="left:100%">100</i></div>
      <div></div></div></div>`;
}

const PROMPT_LABEL = () => ({
  p1_referring: T("lbl_p1"), p2_explicit: T("lbl_p2"),
  p3_reasoning: T("lbl_p3"), custom: T("lbl_custom"),
  expression: T("e_expression"), all_people: T("e_all_people"),
});

function renderBenchmark() {
  const p1s = A.summary.camouflage;
  const p2s = A.summary.blip2_grounded_sam;
  if (!p1s || !p2s) return;
  const p1 = p1s.overall, p2 = p2s.overall;
  const stageVram = Math.max(...Object.values(p2s.components || {}).map((c) => c.peak_vram_gb || 0));

  $("#bench-system-cards").innerHTML = `
    <article class="bench-system p1"><span class="bench-badge">P1</span><div>
      <h3>LISA-7B-v1</h3><p>${esc(T("m_p1_desc"))}</p></div></article>
    <article class="bench-system p2"><span class="bench-badge">P2</span><div>
      <h3>BLIP-2/Q-Former → Grounding DINO → SAM</h3><p>${esc(T("m_p2_desc"))}</p></div></article>`;

  const rows = [
    ["gIoU", n1(p1.gIoU), n1(p2.gIoU), "p2"],
    ["cIoU", n1(p1.cIoU), n1(p2.cIoU), "p1"],
    [T("k_dice"), n1(p1.mean_dice), n1(p2.mean_dice), "p2"],
    ["IoU ≥ 0.5", n1(p1.iou_at_50) + "%", n1(p2.iou_at_50) + "%", "p2"],
    [T("m_emit"), n1(p1.seg_emit_rate) + "%", n1(p2.seg_emit_rate) + "%", "p1"],
    [T("m_time"), f1(p1.mean_latency_s) + " s", f1(p2.mean_latency_s) + " s*", "caveat"],
    [T("m_vram"), p1s.peak_vram_gb.toFixed(2) + " GB", stageVram.toFixed(2) + " GB*", "caveat"],
    [T("m_arch"), T("m_one_model"), T("m_three_models"), ""],
  ];
  $("#benchmark-table").innerHTML =
    `<thead><tr><th>${esc(T("m_metric"))}</th><th>P1 · LISA</th><th>P2 · BLIP-2 → DINO → SAM</th></tr></thead><tbody>` +
    rows.map(([metric, one, two, winner]) => `<tr><td>${esc(metric)}</td>
      <td class="n ${winner === "p1" ? "win" : winner === "caveat" ? "caveat" : ""}">${esc(one)}</td>
      <td class="n ${winner === "p2" ? "win" : winner === "caveat" ? "caveat" : ""}">${esc(two)}</td></tr>`).join("") +
    "</tbody>";
}

function renderExternalBenchmarks() {
  const block = $("#external-benchmark-block");
  const surveillance = (A.external || {}).mots_surveillance_person60;
  const entries = Object.entries(A.external || {}).filter(
    ([task, summary]) => task !== "mots_surveillance_person60" && summary);
  block.style.display = entries.length || surveillance ? "" : "none";
  renderSurveillanceBenchmark(surveillance);
  if (!entries.length) { $("#external-benchmarks").innerHTML = ""; return; }
  const caseLabel = (name) => ({
    multi_target: T("e_multi"), single_in_crowd: T("e_single"), no_target: T("e_none"),
    all_people: T("e_all_people"), tiny_le_32px: T("e_tiny"), small_33_64px: T("e_small"),
  }[name] || name.replaceAll("_", " "));
  const fill = (template, values) => Object.entries(values).reduce(
    (text, [key, value]) => text.replaceAll(`{${key}}`, value), template);

  $("#external-benchmarks").innerHTML = entries.map(([task, summary]) => {
    const p1 = summary.systems.p1.overall, p2 = summary.systems.p2.overall;
    const p1Wins = p1.gIoU > p2.gIoU;
    const groups = task === "mots_small_person"
      ? summary.systems.p1.by_difficulty : summary.systems.p1.by_case_type;
    const p2Groups = task === "mots_small_person"
      ? summary.systems.p2.by_difficulty : summary.systems.p2.by_case_type;
    const rows = [
      ["gIoU", n1(p1.gIoU), n1(p2.gIoU)],
      ["cIoU", n1(p1.cIoU), n1(p2.cIoU)],
      [T("k_dice"), n1(p1.mean_dice), n1(p2.mean_dice)],
      [T("e_coverage"), n1(p1.mean_instance_coverage_50), n1(p2.mean_instance_coverage_50)],
      [T("e_no_target"), p1.no_target_accuracy == null ? "—" : n1(p1.no_target_accuracy),
        p2.no_target_accuracy == null ? "—" : n1(p2.no_target_accuracy)],
      [T("m_time"), f1(p1.mean_latency_s) + " s", f1(p2.mean_latency_s) + " s*"],
    ];
    const breakdown = Object.entries(groups || {}).map(([name, one]) => {
      const two = p2Groups[name];
      return `<tr><td>${esc(caseLabel(name))}</td><td class="n">${one.n_images}</td>
        <td class="n">${n1(one.gIoU)}</td><td class="n">${n1(two && two.gIoU)}</td></tr>`;
    }).join("");
    const finding = task === "grefcoco"
      ? fill(T("e_gref_find"), {
          p1Coverage: n1(p1.mean_instance_coverage_50),
          p2NoTarget: n1(p2.no_target_accuracy),
          p2Emit: n1(p2.seg_emit_rate),
        })
      : fill(T("e_mots_find"), {
          p2Wins: summary.paired.p2_better,
          n: summary.n_items,
          delta: (100 * summary.paired.mean_iou_delta_p2_minus_p1).toFixed(1),
          p1Tiny: n1(groups.tiny_le_32px && groups.tiny_le_32px.mean_instance_coverage_50),
          p2Tiny: n1(p2Groups.tiny_le_32px && p2Groups.tiny_le_32px.mean_instance_coverage_50),
        });
    const next = T(task === "grefcoco" ? "e_gref_next" : "e_mots_next");
    return `<article class="external-card">
      <div class="external-head"><div><span class="eyebrow">${esc(T(task === "grefcoco" ? "e_language" : "e_cctv"))}</span>
        <h3>${esc(summary.dataset_label)}</h3></div>
        <span class="result-pill ${p1Wins ? "p1" : "p2"}">${p1Wins ? "P1" : "P2"} ${esc(T("e_wins"))}</span></div>
      <p>${esc(summary.selection)}</p>
      <div class="tw"><table><thead><tr><th>${esc(T("m_metric"))}</th><th>P1 · LISA</th><th>P2 · BLIP-2 → DINO → SAM</th></tr></thead><tbody>
        ${rows.map(([metric, one, two]) => `<tr><td>${esc(metric)}</td><td class="n">${esc(one)}</td><td class="n">${esc(two)}</td></tr>`).join("")}
      </tbody></table></div>
      <div class="tw breakdown"><table><thead><tr><th>${esc(T("e_group"))}</th><th>n</th><th>P1 gIoU</th><th>P2 gIoU</th></tr></thead>
        <tbody>${breakdown}</tbody></table></div>
      <div class="external-insight"><strong>${esc(T("e_find_h"))}</strong><p>${esc(finding)}</p></div>
      <div class="external-insight next"><strong>${esc(T("e_next_h"))}</strong><p>${esc(next)}</p></div>
      <button class="small external-open" data-task="${task}">${esc(T("e_browse"))}</button>
    </article>`;
  }).join("");
  $$(".external-open").forEach((button) => {
    button.onclick = () => {
      $("nav.tabs button[data-tab='browse']").click();
      $("#f-system").value = "both";
      renderFilters();
      $("#f-task").value = button.dataset.task;
      renderFilters();
      loadRows();
    };
  });
}

function renderSurveillanceBenchmark(summary) {
  const root = $("#surveillance-benchmark");
  if (!summary) { root.style.display = "none"; return; }
  root.style.display = "";
  const systems = [
    ["p1", "P1 · LISA"],
    ["p2", "P2 · BLIP-2 → DINO → SAM"],
    ["p2_direct", "P2-direct · person → DINO → SAM"],
  ];
  const values = systems.map(([id, label]) => [id, label, summary.systems[id].overall]);
  const best = [...values].sort((a, b) => b[2].person_recall_50 - a[2].person_recall_50)[0];
  const p2 = summary.systems.p2.overall;
  const direct = summary.systems.p2_direct.overall;
  const resources = summary.resources || {};
  const systemVram = {
    p1: resources.p1 && resources.p1.peak_vram_gb,
    p2: Math.max(...[resources.blip2, resources.grounding, resources.sam]
      .map((stage) => (stage && stage.peak_vram_gb) || 0)),
    p2_direct: Math.max(...[resources.direct_grounding, resources.direct_sam]
      .map((stage) => (stage && stage.peak_vram_gb) || 0)),
  };
  const metricRows = [
    [T("s_gt_people"), ...values.map(([, , v]) => v.gt_people.toLocaleString())],
    [T("s_detected"), ...values.map(([, , v]) => v.detected_people_50.toLocaleString())],
    [T("s_missed"), ...values.map(([, , v]) => v.missed_people_50.toLocaleString())],
    [T("s_person_recall"), ...values.map(([, , v]) => n1(v.person_recall_50))],
    ["gIoU", ...values.map(([, , v]) => n1(v.gIoU))],
    [T("s_pixel_precision"), ...values.map(([, , v]) => n1(v.mean_precision))],
    [T("s_fp_pixels"), ...values.map(([, , v]) => v.false_positive_pixels.toLocaleString())],
    [T("m_time"), ...values.map(([id, , v]) => f1(v.mean_latency_s) + (id.startsWith("p2") ? " s*" : " s"))],
    [T("m_vram"), ...values.map(([id]) => systemVram[id] ? systemVram[id].toFixed(2) + " GB*" : "—")],
  ];
  const sizes = ["tiny_le_32px", "small_33_64px", "large_gt_64px"];
  const sizeLabels = {tiny_le_32px:T("e_tiny"), small_33_64px:T("e_small"), large_gt_64px:T("s_large")};
  const sizeRows = sizes.map((size) => {
    const base = values[0][2].by_person_size[size];
    return [sizeLabels[size], base.gt_people,
      ...values.map(([, , v]) => n1(v.by_person_size[size].person_recall_50))];
  });
  const fill = (template, replacements) => Object.entries(replacements).reduce(
    (text, [key, value]) => text.replaceAll(`{${key}}`, value), template);
  const finding = fill(T("s_finding"), {
    people: values[0][2].gt_people.toLocaleString(),
    best: best[1], bestRecall: n1(best[2].person_recall_50),
    deltaRecall: (100 * (direct.person_recall_50 - p2.person_recall_50)).toFixed(1),
    deltaIoU: (100 * (direct.gIoU - p2.gIoU)).toFixed(1),
  });
  root.innerHTML = `<div class="shead compact-head">
      <p class="eyebrow">${esc(T("s_eye"))}</p><h2>${esc(T("s_h"))}</h2><p>${esc(T("s_p"))}</p>
    </div>
    <div class="surveillance-systems">${values.map(([id, label]) => `<div class="surveillance-system ${id}">
      <span>${esc(id === "p2_direct" ? "ABLATION" : id.toUpperCase())}</span><strong>${esc(label)}</strong></div>`).join("")}</div>
    <div class="tw"><table class="surveillance-table"><thead><tr><th>${esc(T("m_metric"))}</th>
      ${values.map(([, label]) => `<th>${esc(label)}</th>`).join("")}</tr></thead><tbody>
      ${metricRows.map((row) => `<tr>${row.map((cell, i) => `<${i ? "td" : "th"} class="${i ? "n" : ""}">${esc(cell)}</${i ? "td" : "th"}>`).join("")}</tr>`).join("")}
    </tbody></table></div>
    <div class="tw"><table class="surveillance-table size-table"><thead><tr><th>${esc(T("s_person_size"))}</th><th>${esc(T("s_gt_people"))}</th>
      ${values.map(([, label]) => `<th>${esc(label)}</th>`).join("")}</tr></thead><tbody>
      ${sizeRows.map((row) => `<tr>${row.map((cell, i) => `<${i ? "td" : "th"} class="${i ? "n" : ""}">${esc(cell)}</${i ? "td" : "th"}>`).join("")}</tr>`).join("")}
    </tbody></table></div>
    <div class="external-insight"><strong>${esc(T("e_find_h"))}</strong><p>${esc(finding)}</p></div>
    <div class="external-insight next"><strong>${esc(T("s_rule_h"))}</strong><p>${esc(T("s_rule"))}</p></div>
    <button class="small" id="surveillance-open">${esc(T("s_browse"))}</button>`;
  $("#surveillance-open").onclick = () => {
    $("nav.tabs button[data-tab='browse']").click();
    $("#f-system").value = "all3";
    renderFilters();
    $("#f-task").value = "mots_surveillance_person60";
    renderFilters();
    loadRows();
  };
}

/* ---------------- results tab ---------------- */
function renderResults() {
  const camo = A.summary.camouflage, o = camo && camo.overall;
  if (!o) return;
  const best = Object.entries(camo.by_prompt).sort((a, b) => b[1].gIoU - a[1].gIoU)[0];

  $("#camo-stats").innerHTML = [
    { k: T("k_giou"), n: n1(o.gIoU), s: `${n1(o.iou_at_50)}% ${T("k_usable")}`, hero: 1 },
    { k: T("k_ciou"), n: n1(o.cIoU), s: "Σinter ÷ Σunion", hero: 1 },
    { k: T("k_best_prompt"), n: n1(best[1].gIoU), s: PROMPT_LABEL()[best[0]] || best[0] },
    { k: T("k_emit"), n: n1(o.seg_emit_rate) + "%", s: `${o.n_images} / ${o.n_images}` },
    { k: T("k_vram"), n: camo.peak_vram_gb.toFixed(1), s: "GB · " + camo.gpu.replace("NVIDIA ", "") },
    { k: T("k_latency"), n: f1(o.mean_latency_s), s: "s · " + Math.round(camo.total_wall_s / 60) + " min " + T("k_wall") },
  ].map((s) => `<div class="stat${s.hero ? " hero" : ""}">
      <div class="stat-k">${esc(s.k)}</div><div class="stat-n">${esc(s.n)}</div>
      <div class="stat-s">${esc(s.s)}</div></div>`).join("");

  renderBenchmark();
  renderExternalBenchmarks();

  /* prompt chart + table */
  const PL = PROMPT_LABEL();
  const bp = Object.entries(camo.by_prompt).sort((a, b) => b[1].gIoU - a[1].gIoU);
  $("#prompt-chart").innerHTML = bars(bp.map(([pid, m]) => ({
    label: PL[pid] || pid, sub: pid.split("_")[0],
    value: 100 * m.gIoU,
    tip: `${pid}\ngIoU ${n1(m.gIoU)} · cIoU ${n1(m.cIoU)}\n${n1(m.iou_at_50)}% ≥ 0.5`,
  })), LANG === "th" ? 150 : 175);

  const presets = A.prompt_presets || {};
  $("#prompt-table").innerHTML =
    `<thead><tr><th>${T("p_tbl_prompt")}</th><th>gIoU</th><th>cIoU</th><th>${T("k_dice")}</th>
     <th>${T("k_prec")}</th><th>${T("k_rec")}</th><th>IoU≥0.5</th></tr></thead><tbody>` +
    ["p1_referring", "p2_explicit", "p3_reasoning"].filter((p) => camo.by_prompt[p]).map((pid) => {
      const m = camo.by_prompt[pid];
      const top = pid === bp[0][0];
      return `<tr class="${top ? "best" : ""}">
        <td>“${esc(presets[pid] || pid)}”</td>
        <td class="n">${n1(m.gIoU)}</td><td class="n">${n1(m.cIoU)}</td>
        <td class="n">${n1(m.mean_dice)}</td><td class="n">${n1(m.mean_precision)}</td>
        <td class="n">${n1(m.mean_recall)}</td><td class="n">${n1(m.iou_at_50)}%</td></tr>`;
    }).join("") + "</tbody>";

  /* pattern ranking */
  $("#pattern-chart").innerHTML = bars(A.patterns.map((p) => ({
    label: p.name, sub: p.pattern.replace("dataset", ""),
    value: p.miou,
    tip: `${p.name}\nmean IoU ${p.miou.toFixed(1)} · n=${p.n}` +
         (p.contrast != null ? `\ncontrast ${p.contrast.toFixed(1)}` : "") +
         (p.area_pct != null ? ` · target ${p.area_pct.toFixed(2)}%` : ""),
  })), LANG === "th" ? 175 : 200);

  /* correlations */
  const verdict = (r) => {
    const a = Math.abs(r);
    return a >= 0.7 ? T("v_strong") : a >= 0.4 ? T("v_moderate") : a >= 0.2 ? T("v_weak") : T("v_negligible");
  };
  const pill = (r) => {
    const a = Math.abs(r);
    return a >= 0.4 ? "mid" : "lo";
  };
  $("#corr-table").innerHTML =
    `<thead><tr><th>${T("t_pred")}</th><th>${T("t_rho")}</th><th>${T("t_verdict")}</th></tr></thead><tbody>` +
    A.correlations.map((c) => `<tr><td><code>${esc(c.key)}</code></td>
      <td class="n">${c.rho >= 0 ? "+" : "−"}${Math.abs(c.rho).toFixed(3)}</td>
      <td><span class="pill ${pill(c.rho)}">${esc(verdict(c.rho))}</span></td></tr>`).join("") +
    `<tr><td><code>gt_fragmentation</code></td><td class="n">−0.088</td>
      <td><span class="pill lo">${esc(T("v_negligible"))}</span></td></tr></tbody>`;

  /* fragmentation */
  $("#frag-chart").innerHTML = bars(A.fragmentation.map((f) => ({
    label: f.band + " " + (LANG === "th" ? "ชิ้น" : f.band === "1" ? "piece" : "pieces"),
    sub: "n=" + f.n, value: f.miou,
    tip: `${f.band} ${T("f_band")}\nmean IoU ${f.miou.toFixed(2)} · n=${f.n}`,
  })), LANG === "th" ? 150 : 165);

  /* calibration */
  const rs = A.summary.reasonseg && A.summary.reasonseg.overall;
  const paper = [["OVSeg", 28.5, 18.6], ["SEEM", 25.5, 21.2],
                 ["LISA-7B", 44.4, 46.0], ["LISA-7B (ft)", 52.9, 54.0]];
  $("#calib-table").innerHTML =
    `<thead><tr><th>${T("c_method")}</th><th>gIoU</th><th>cIoU</th><th>${T("c_source")}</th></tr></thead><tbody>` +
    paper.map(([m, g, c]) => `<tr><td>${esc(m)}</td><td class="n">${g.toFixed(1)}</td>
      <td class="n">${c.toFixed(1)}</td><td class="muted">Lai et al. 2024</td></tr>`).join("") +
    (rs ? `<tr class="rule best"><td>LISA-7B-v1 — ${esc(T("c_thisrun"))}</td>
      <td class="n">${n1(rs.gIoU)}</td><td class="n">${n1(rs.cIoU)}</td>
      <td class="muted">${rs.n_images} ${esc(T("k_images"))}, seed 0</td></tr>` : "") +
    "</tbody>";

  /* drone — percentages come from the server, which knows the frame sizes */
  const dr = {};
  (A.drone_area || []).forEach((r) => {
    dr[r.item_id] = dr[r.item_id] || {};
    dr[r.item_id][r.prompt_id] = r.pct;
  });
  const dkeys = Object.keys(dr);
  if (dkeys.length) {
    const pct = (v) => (v == null ? "—" : v.toFixed(2) + "%");
    $("#drone-table").innerHTML =
      `<thead><tr><th>${T("d_still")}</th><th>${T("lbl_p1")}</th><th>${T("lbl_p2")}</th>
       <th>${T("lbl_p3")}</th></tr></thead><tbody>` +
      dkeys.map((k) => `<tr><td><code>${esc(k)}</code></td>
          <td class="n">${pct(dr[k].p1_referring)}</td>
          <td class="n">${pct(dr[k].p2_explicit)}</td>
          <td class="n">${pct(dr[k].p3_reasoning)}</td></tr>`).join("") + "</tbody>";
  }
}

/* ---------------- BLIP-2 -> DINO -> SAM pipeline ---------------- */
function pipelineMetric(label, value, suffix = "", better = false) {
  return `<div><b>${esc(label)}</b><span class="${better ? "better" : ""}">${esc(value)}${esc(suffix)}</span></div>`;
}

function setPipelineCase(row) {
  if (!row) return;
  const item = row.item_id, prompt = row.prompt_id;
  const q = new URLSearchParams({ item, prompt });
  const image = (stage) => `/api/pipeline/image?${q.toString()}&stage=${stage}`;
  const pattern = item.split("_")[0];
  const delta = row.iou_delta_vs_lisa || 0;
  const pipeBetter = delta > 1e-12, lisaBetter = delta < -1e-12;

  $("#pipe-pattern").textContent = (A.pattern_names && A.pattern_names[pattern]) || pattern;
  $("#pipe-id").textContent = item;
  $("#pipe-question").textContent = `BLIP-2: “${row.instruction}” · LISA: “${row.lisa_instruction}”`;
  [["pipe-original", "original"], ["pipe-dino", "dino"], ["pipe-sam", "sam"],
   ["pipe-sam-compare", "sam"], ["pipe-lisa", "lisa"]].forEach(([id, stage]) => {
    const img = $("#" + id); img.src = image(stage); img.alt = `${item} — ${stage}`;
  });

  $("#pipe-answer").textContent = row.answer || "—";
  $("#pipe-query").textContent = row.grounding_query || "—";
  $("#pipe-blip-time").textContent = `${row.blip2_latency_s.toFixed(2)} s`;
  const maxScore = row.box_scores.length ? Math.max(...row.box_scores) : null;
  $("#pipe-boxes").textContent = T("x_boxes").replace("{n}", row.n_boxes == null ? 0 : row.n_boxes) +
    (maxScore == null ? "" : ` · max ${maxScore.toFixed(2)}`);
  $("#pipe-dino-time").textContent = `${row.grounding_latency_s.toFixed(2)} s`;
  $("#pipe-sam-time").textContent = `${row.sam_latency_s.toFixed(2)} s`;

  $("#pipe-metrics").innerHTML =
    pipelineMetric(T("x_iou"), n1(row.iou), "", pipeBetter) +
    pipelineMetric(T("x_dice"), n1(row.dice), "", row.lisa_dice != null && row.dice > row.lisa_dice) +
    pipelineMetric(T("x_total"), row.latency_s.toFixed(2), " s");
  $("#lisa-metrics").innerHTML =
    pipelineMetric(T("x_iou"), n1(row.lisa_iou), "", lisaBetter) +
    pipelineMetric(T("x_dice"), n1(row.lisa_dice), "", row.lisa_dice != null && row.lisa_dice > row.dice) +
    pipelineMetric(T("x_total"), row.lisa_latency_s == null ? "—" : row.lisa_latency_s.toFixed(2), row.lisa_latency_s == null ? "" : " s");

  const result = $("#pipe-win");
  result.className = "result-pill " + (pipeBetter ? "win" : lisaBetter ? "loss" : "");
  result.textContent = pipeBetter ? T("x_won") : lisaBetter ? T("x_lost") : T("x_tied");
  const reading = pipeBetter
    ? T("x_case_better").replace("{delta}", (100 * delta).toFixed(1))
    : lisaBetter
      ? T("x_case_worse").replace("{delta}", (100 * -delta).toFixed(1))
      : T("x_case_tie");
  $("#pipe-reading p").textContent = reading;
}

function selectPipelineRow(row) {
  if (!row) return;
  $("#pipe-item").value = row.item_id;
  $("#pipe-prompt").value = row.prompt_id;
  setPipelineCase(row);
}

function renderPipeline() {
  if (!A || !PIPE.length) return;
  const summary = A.summary.blip2_grounded_sam;
  const p = summary.overall, l = summary.lisa_matched.overall;
  const paired = summary.paired_analysis.overall;
  $("#pipeline-stats").innerHTML = [
    { k: "gIoU · P2", n: n1(p.gIoU), s: `P1 ${n1(l.gIoU)}`, hero: 1 },
    { k: "cIoU · P2", n: n1(p.cIoU), s: `P1 ${n1(l.cIoU)}` },
    { k: LANG === "th" ? "P2 ชนะเป็นคู่" : "P2 paired wins", n: paired.pipeline_better, s: `P1 ${paired.lisa_better} · ${LANG === "th" ? "เสมอ" : "ties"} ${paired.ties}`, hero: 1 },
    { k: "IoU ≥ 0.5 · P2", n: n1(p.iou_at_50) + "%", s: `P1 ${n1(l.iou_at_50)}%`, hero: 1 },
  ].map((s) => `<div class="stat${s.hero ? " hero" : ""}"><div class="stat-k">${esc(s.k)}</div>
    <div class="stat-n">${esc(s.n)}</div><div class="stat-s">${esc(s.s)}</div></div>`).join("");

  const itemEl = $("#pipe-item"), promptEl = $("#pipe-prompt");
  const previousItem = itemEl.value, previousPrompt = promptEl.value;
  const items = [...new Set(PIPE.map((r) => r.item_id))].sort();
  itemEl.innerHTML = items.map((id) => {
    const pattern = id.split("_")[0];
    const name = (A.pattern_names && A.pattern_names[pattern]) || pattern;
    return `<option value="${esc(id)}">${esc(id)} · ${esc(name)}</option>`;
  }).join("");
  const PL = PROMPT_LABEL();
  promptEl.innerHTML = ["p1_referring", "p2_explicit", "p3_reasoning"]
    .map((id) => `<option value="${id}">${esc(PL[id] || id)}</option>`).join("");

  const defaultRow = [...PIPE].sort((a, b) => b.iou_delta_vs_lisa - a.iou_delta_vs_lisa)[0];
  itemEl.value = items.includes(previousItem) ? previousItem : defaultRow.item_id;
  promptEl.value = ["p1_referring", "p2_explicit", "p3_reasoning"].includes(previousPrompt)
    ? previousPrompt : defaultRow.prompt_id;
  const row = PIPE.find((r) => r.item_id === itemEl.value && r.prompt_id === promptEl.value);
  setPipelineCase(row || defaultRow);
}

[$("#pipe-item"), $("#pipe-prompt")].forEach((el) => {
  el.onchange = () => setPipelineCase(PIPE.find((r) =>
    r.item_id === $("#pipe-item").value && r.prompt_id === $("#pipe-prompt").value));
});
$("#pipe-best").onclick = () => selectPipelineRow([...PIPE].sort((a, b) => b.iou_delta_vs_lisa - a.iou_delta_vs_lisa)[0]);
$("#pipe-worst").onclick = () => selectPipelineRow([...PIPE].sort((a, b) => a.iou_delta_vs_lisa - b.iou_delta_vs_lisa)[0]);

/* ---------------- browse ---------------- */
function renderFilters() {
  const tl = TASK_LABEL[LANG] || TASK_LABEL.en;
  const sy = $("#f-system"), systemPrev = sy.value;
  sy.innerHTML = `<option value="both">${esc(T("b_both"))}</option>
                  <option value="p1">P1 · LISA</option>
                  <option value="p2">P2 · BLIP-2 → DINO → SAM</option>
                  <option value="p2_direct">P2-direct · person → DINO → SAM</option>
                  <option value="all3">${esc(T("s_all3"))}</option>`;
  sy.value = ["both", "p1", "p2", "p2_direct", "all3"].includes(systemPrev) ? systemPrev : "both";

  const ts = $("#f-task"), prev = ts.value;
  const sharedTasks = ["camouflage", "grefcoco", "mots_small_person", "mots_surveillance_person60"];
  const availableTasks = sy.value === "p2"
    ? sharedTasks : sy.value === "p2_direct" || sy.value === "all3"
      ? ["mots_surveillance_person60"] : [...sharedTasks, "reasonseg", "drone"];
  ts.innerHTML = availableTasks
    .filter((t) => A.counts[t] > 0)
    .map((t) => `<option value="${t}">${esc(tl[t])}</option>`).join("");
  if (availableTasks.includes(prev)) ts.value = prev;

  const pat = $("#f-pattern"), pprev = pat.value;
  pat.innerHTML = `<option value="">${esc(T("b_all"))}</option>` +
    A.patterns.map((p) => `<option value="${p.pattern}">${esc(p.name)}</option>`).join("");
  if (pprev) pat.value = pprev;
  pat.disabled = ts.value !== "camouflage";

  const PL = PROMPT_LABEL();
  const pr = $("#f-prompt"), rprev = pr.value;
  const ids = ts.value === "reasonseg" ? ["paper_query"]
    : ts.value === "grefcoco" ? ["expression"]
    : ["mots_small_person", "mots_surveillance_person60"].includes(ts.value) ? ["all_people"]
    : ["p1_referring", "p2_explicit", "p3_reasoning"];
  pr.innerHTML = `<option value="">${esc(T("b_all"))}</option>` +
    ids.map((i) => `<option value="${i}">${esc(PL[i] || i)}</option>`).join("");
  if (rprev) pr.value = rprev;

  const so = $("#f-sort"), sprev = so.value;
  so.innerHTML = `<option value="desc">IoU — ${esc(T("b_desc"))}</option>
                  <option value="asc">IoU — ${esc(T("b_asc"))}</option>`;
  so.value = sprev || "asc";
}

async function loadRows() {
  const task = $("#f-task").value;
  const q = new URLSearchParams({
    task, system: $("#f-system").value, sort: "iou",
    desc: $("#f-sort").value === "desc" ? "1" : "0",
  });
  if (task === "camouflage" && $("#f-pattern").value) q.set("pattern", $("#f-pattern").value);
  if ($("#f-prompt").value) q.set("prompt", $("#f-prompt").value);
  const r = await fetch("/api/items?" + q);
  const j = await r.json();
  ROWS = j.rows;
  renderBrowse();
}

function renderBrowse() {
  const task = $("#f-task").value;
  $("#b-count").textContent = T("b_count").replace("{n}", ROWS.length);
  if (!ROWS.length) { $("#browse-table").innerHTML = `<tbody><tr><td>${esc(T("b_none"))}</td></tr></tbody>`; return; }
  const PL = PROMPT_LABEL();
  const scored = ROWS.some((r) => r.iou != null);
  $("#browse-table").innerHTML =
    `<thead><tr><th>${T("b_system")}</th><th>${T("b_item")}</th><th>${T("b_prompt")}</th>` +
    (scored ? `<th>IoU</th><th>${T("k_dice")}</th><th>${T("k_prec")}</th><th>${T("k_rec")}</th>` : "") +
    `<th>${T("y_maskpx")}</th><th>${T("y_time")}</th></tr></thead><tbody>` +
    ROWS.map((r, i) => {
      const cls = r.iou == null ? "" : r.iou >= 0.5 ? "hi" : r.iou >= 0.25 ? "mid" : "lo";
      return `<tr class="click" data-i="${i}">
        <td><span class="pill system-pill ${r.system}">${r.system.toUpperCase()}</span></td>
        <td><code>${esc(r.item_id)}</code></td>
        <td>${esc(PL[r.prompt_id] || r.prompt_id)}</td>` +
        (scored ? `<td class="n"><span class="pill ${cls}">${r.iou == null ? "—" : n1(r.iou)}</span></td>
          <td class="n">${n1(r.dice)}</td><td class="n">${n1(r.precision)}</td>
          <td class="n">${n1(r.recall)}</td>` : "") +
        `<td class="n">${r.pred_area == null ? "—" : r.pred_area.toLocaleString()}</td>
         <td class="n">${f1(r.latency_s)}${r.system.startsWith("p2") ? "*" : ""}</td></tr>`;
    }).join("") + "</tbody>";
  $$("#browse-table tr.click").forEach((tr) => {
    tr.onclick = () => openViewer(task, ROWS[+tr.dataset.i], +tr.dataset.i);
  });
}

["f-system", "f-task", "f-pattern", "f-prompt", "f-sort"].forEach((id) => {
  document.addEventListener("change", (e) => {
    if (e.target.id === id) {
      if (id === "f-system" || id === "f-task") renderFilters();
      loadRows();
    }
  });
});

/* ---------------- viewer ---------------- */
function refreshViewerNav() {
  const total = ROWS.length;
  $("#v-prev").disabled = VIEW_INDEX <= 0;
  $("#v-next").disabled = VIEW_INDEX < 0 || VIEW_INDEX >= total - 1;
  $("#v-prev").setAttribute("aria-label", T("v_prev"));
  $("#v-next").setAttribute("aria-label", T("v_next"));
  $("#v-position").textContent = T("v_position")
    .replace("{current}", VIEW_INDEX + 1).replace("{total}", total);
}

function openViewer(task, row, index = null) {
  VIEW_TASK = task;
  VIEW_INDEX = index == null ? ROWS.indexOf(row) : index;
  const PL = PROMPT_LABEL();
  $("#v-title").textContent = row.item_id;
  $("#v-sub").textContent = `${row.system.toUpperCase()} · ${PL[row.prompt_id] || row.prompt_id} · ${task}`;
  $("#v-img").alt = row.item_id;
  $("#v-img").src = `/api/overlay?system=${encodeURIComponent(row.system)}&task=${encodeURIComponent(task)}&item=${encodeURIComponent(row.item_id)}&prompt=${encodeURIComponent(row.prompt_id)}&kind=both`;

  const hasGt = row.iou != null;
  $("#v-legend").innerHTML =
    `<span><i class="sw" style="background:var(--accent)"></i>${esc(T("v_pred"))}</span>` +
    (hasGt ? `<span><i class="sw" style="background:var(--truth)"></i>${esc(T("v_truth"))}</span>` : "");

  const kv = [];
  if (hasGt) {
    kv.push(["IoU", n1(row.iou)]);
    kv.push([T("k_dice"), n1(row.dice)]);
    kv.push([T("k_prec"), n1(row.precision)]);
    kv.push([T("k_rec"), n1(row.recall)]);
    if (row.instance_coverage_50 != null) kv.push([T("e_coverage"), n1(row.instance_coverage_50)]);
    if (row.detected_people_50 != null) kv.push([T("s_detected"), row.detected_people_50]);
    if (row.missed_people_50 != null) kv.push([T("s_missed"), row.missed_people_50]);
  }
  if (row.target_count != null) kv.push([T("e_targets"), row.target_count]);
  if (row.people_in_image != null) kv.push([T("e_people"), row.people_in_image]);
  if (row.smallest_person_height_px != null) kv.push([T("e_smallest"), row.smallest_person_height_px.toFixed(1) + " px"]);
  kv.push([T("y_maskpx"), row.pred_area == null ? "—" : row.pred_area.toLocaleString()]);
  if (hasGt) kv.push([T("v_truth"), row.gt_area == null ? "—" : row.gt_area.toLocaleString()]);
  kv.push([T("y_time") + (row.system.startsWith("p2") ? "*" : ""), f1(row.latency_s)]);
  $("#v-kv").innerHTML = kv.map(([k, v]) =>
    `<div><b>${esc(k)}</b><span>${esc(v)}</span></div>`).join("");

  $("#v-instruction").innerHTML = `<b>${esc(T("v_instruction"))}</b>${esc(row.instruction || "—")}` +
    (row.expression ? `<div class="muted" style="margin-top:.5rem">${esc(T("e_expression"))}: ${esc(row.expression)}</div>` : "");
  const ans = (row.answer || "").replace(/^.*ASSISTANT:\s*/s, "").replace(/<\/s>$/, "").trim();
  $("#v-answer").innerHTML = `<b>${esc(T("v_answer"))}</b>${esc(ans || "—")}` +
    (hasGt ? "" : `<div class="muted" style="margin-top:.5rem">${esc(T("v_nogt"))}</div>`);

  $("#viewer").classList.add("on");
  refreshViewerNav();
}
function moveViewer(step) {
  const next = VIEW_INDEX + step;
  if (next < 0 || next >= ROWS.length) return;
  openViewer(VIEW_TASK, ROWS[next], next);
}
$("#v-prev").onclick = () => moveViewer(-1);
$("#v-next").onclick = () => moveViewer(1);
$("#v-close").onclick = () => $("#viewer").classList.remove("on");
$("#viewer").onclick = (e) => { if (e.target.id === "viewer") $("#viewer").classList.remove("on"); };
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") $("#viewer").classList.remove("on");
  if (!$("#viewer").classList.contains("on")) return;
  if (e.key === "ArrowLeft") { e.preventDefault(); moveViewer(-1); }
  if (e.key === "ArrowRight") { e.preventDefault(); moveViewer(1); }
});

/* ---------------- try it ---------------- */
function renderChips() {
  const PL = PROMPT_LABEL();
  const presets = A ? A.prompt_presets : {};
  $("#preset-chips").innerHTML = ["p1_referring", "p2_explicit", "p3_reasoning", "car_explicit"]
    .filter((p) => presets[p])
    .map((p) => `<label class="chip${p === "p2_explicit" ? " on" : ""}">
      <input type="checkbox" value="${p}" ${p === "p2_explicit" ? "checked" : ""}>
      <span>${esc(PL[p] || (p === "car_explicit" ? (LANG === "th" ? "ยานพาหนะที่ถูกพราง" : "hidden vehicle") : p))}</span></label>`)
    .join("");
  $$("#preset-chips .chip").forEach((c) => {
    c.querySelector("input").onchange = (e) => c.classList.toggle("on", e.target.checked);
  });
}

const drop = $("#drop");
drop.onclick = () => $("#file").click();
drop.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("#file").click(); } };
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => {
  e.preventDefault(); drop.classList.add("over");
}));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => {
  e.preventDefault(); drop.classList.remove("over");
}));
drop.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files && e.dataTransfer.files[0];
  if (f) takeFile(f);
});
$("#file").onchange = (e) => { if (e.target.files[0]) takeFile(e.target.files[0]); };

function takeFile(f) {
  if (!f.type.startsWith("image/")) { showErr(T("y_err") + " — not an image file"); return; }
  FILE = f;
  $("#try-preview").src = URL.createObjectURL(f);
  $("#try-config").style.display = "";
  $("#try-results").innerHTML = "";
  $("#try-noiou").style.display = "none";
  hideErr();
}
$("#try-reset").onclick = () => {
  FILE = null; $("#try-config").style.display = "none";
  $("#file").value = ""; $("#try-results").innerHTML = "";
  $("#try-noiou").style.display = "none"; hideErr();
};

function showErr(m) { const e = $("#try-error"); e.textContent = m; e.style.display = ""; }
function hideErr() { $("#try-error").style.display = "none"; }

function updateTrySystem() {
  const selector = $("#try-system");
  if (!selector) return;
  const isP2 = selector.value === "p2";
  $("#try-system-help").textContent = T(isP2 ? "y_p2_help" : "y_p1_help");
  $("#tokens").disabled = isP2;
}
$("#try-system").onchange = updateTrySystem;

$("#run").onclick = async () => {
  if (!FILE) return;
  hideErr();
  const fd = new FormData();
  fd.append("image", FILE);
  fd.append("system", $("#try-system").value);
  $$("#preset-chips input:checked").forEach((i) => fd.append("presets", i.value));
  const custom = $("#custom-prompt").value.trim();
  if (custom) fd.append("prompt", custom);
  fd.append("max_new_tokens", $("#tokens").value || "32");

  $("#run").disabled = true;
  $("#run").textContent = T("y_running");
  $("#prog").style.display = "";
  $("#prog i").style.width = "0%";
  $("#run-status").innerHTML = `<span class="spin"></span>${esc(T("y_queued"))}`;
  $("#try-results").innerHTML = "";

  try {
    const r = await fetch("/api/segment", { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "request failed");
    poll(j.job_id);
  } catch (err) {
    showErr(T("y_err") + " — " + err.message);
    resetRun();
  }
};

function resetRun() {
  $("#run").disabled = false;
  $("#run").textContent = T("y_run");
  $("#run-status").innerHTML = "";
  $("#prog").style.display = "none";
}

function poll(jid) {
  clearInterval(POLL);
  POLL = setInterval(async () => {
    let j;
    try { j = await (await fetch("/api/job/" + jid)).json(); }
    catch { return; }

    const total = j.total || 1, done = j.done || 0;
    $("#prog i").style.width = Math.round((done / total) * 100) + "%";
    const msg = j.state === "loading" ? T("y_loadmodel")
      : j.state === "queued" ? T("y_queued") : (j.message || j.state);
    $("#run-status").innerHTML = j.state === "done" || j.state === "error"
      ? "" : `<span class="spin"></span>${esc(msg)}`;

    if (j.results && j.results.length) renderTryResults(j.results);

    if (j.state === "done") {
      clearInterval(POLL);
      $("#prog i").style.width = "100%";
      resetRun();
      $("#try-noiou").style.display = "";
    } else if (j.state === "error") {
      clearInterval(POLL);
      showErr(T("y_err") + " — " + (j.message || ""));
      resetRun();
    }
  }, 1200);
}

function renderTryResults(results) {
  const PL = PROMPT_LABEL();
  $("#try-results").innerHTML = results.map((r) => {
    const system = r.system || "p1";
    const frag = r.components >= 4
      ? `<div class="note warn" style="margin:10px 0 0"><p>${esc(T("y_frag_warn").replace("{n}", r.components))}</p></div>`
      : r.components === 1
        ? `<div class="note good" style="margin:10px 0 0"><p>${esc(T("y_frag_ok"))}</p></div>` : "";
    const ans = (r.answer || "").replace(/^.*ASSISTANT:\s*/s, "").replace(/<\/s>$/, "").trim();
    return `<div class="card">
      ${r.overlay ? `<img src="data:image/jpeg;base64,${r.overlay}" alt="">` : ""}
      <div class="cb">
        <h4><span class="pill system-pill ${esc(system)}">${esc(system.toUpperCase())}</span> ${esc(PL[r.prompt_id] || r.prompt_id)}</h4>
        <p class="muted" style="font-size:.8rem">“${esc(r.prompt)}”</p>
        ${r.emitted_seg ? "" : `<div class="err">${esc(T("y_result_none"))}</div>`}
        <div class="kv" style="margin-top:10px">
          <div><b>${esc(T("y_maskpx"))}</b><span>${r.mask_px.toLocaleString()}</span></div>
          <div><b>${esc(T("y_maskpct"))}</b><span>${r.mask_pct.toFixed(2)}</span></div>
          <div><b>${esc(T("y_comps"))}</b><span>${r.components}</span></div>
          ${system === "p2" ? `<div><b>${esc(T("y_boxes"))}</b><span>${r.n_boxes == null ? "—" : r.n_boxes}</span></div>` : ""}
          <div><b>${esc(system === "p2" ? T("y_component_time") : T("y_time"))}</b><span>${r.latency_s}</span></div>
          ${system === "p2" ? `<div><b>${esc(T("y_wall_time"))}</b><span>${r.wall_time_s == null ? "—" : r.wall_time_s}</span></div>` : ""}
        </div>
        <div class="quote"><b>${esc(T("y_answer"))}</b>${esc(ans || "—")}</div>
        ${system === "p2" ? `<div class="quote" style="margin-top:8px"><b>${esc(T("y_query"))}</b>${esc(r.grounding_query || "—")}</div>` : ""}
        ${frag}
      </div></div>`;
  }).join("");
}

/* ---------------- status ---------------- */
async function updateStatus() {
  try {
    const s = await (await fetch("/api/status")).json();
    const dot = $("#gpudot"), txt = $("#gputext");
    if (s.viewer_only) {
      dot.className = "dot ok";
      txt.textContent = LANG === "th" ? "ดูผลทดลองที่บันทึกไว้" : "Saved experiment viewer";
      $("#run").disabled = true;
      $("#run-status").className = "legacy-viewer-note";
      $("#run-status").textContent = LANG === "th" ? "หน้านี้แสดงผลทดลองเดิม การรันทำนายภาพใหม่ต้องใช้ cenara70hx แยกต่างหาก จึงไม่มีโมเดลรันบนเครื่องนี้" : "This page displays saved experiments. New-image inference must run separately on cenara70hx; this viewer does not load a local model.";
      return;
    }
    if (!s.cuda) { dot.className = "dot err"; txt.textContent = T("gpu_none"); return; }
    dot.className = "dot " + (s.busy ? "busy" : s.model_loaded ? "ok" : "");
    const state = s.busy ? T("gpu_busy") : s.model_loaded ? T("model_ready") : T("model_cold");
    txt.textContent = `${s.gpu.replace("NVIDIA ", "")} · ${state}`;
  } catch { /* server not up yet */ }
}
setInterval(updateStatus, 4000);

/* ---------------- boot ---------------- */
$("#lang-en").onclick = () => setLang("en");
$("#lang-th").onclick = () => setLang("th");

(async function boot() {
  const [analysisResponse, pipelineResponse] = await Promise.all([
    fetch("/api/analysis"), fetch("/api/pipeline"),
  ]);
  if (!analysisResponse.ok || !pipelineResponse.ok) {
    const message = document.createElement('div'); message.className='legacy-error';
    message.textContent='Saved-result API is unavailable. Open this page through portal_server.py, not python -m http.server. / ไม่พบ API ผลทดลอง กรุณาเปิดผ่าน portal_server.py';
    document.body.prepend(message); return;
  }
  A = await analysisResponse.json();
  PIPE = (await pipelineResponse.json()).rows || [];
  applyLang();
  renderFilters();
  renderChips();
  await loadRows();
})();
