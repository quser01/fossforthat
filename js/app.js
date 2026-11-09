(function () {
  const search = document.getElementById("search");
  const category = document.getElementById("category");
  const difficulty = document.getElementById("difficulty");
  const cards = Array.from(document.querySelectorAll("[data-tool-card]"));
  const empty = document.getElementById("empty-state");
  const countEl = document.getElementById("result-count");

  if (!search || !cards.length) return;

  function normalize(s) {
    return (s || "").toLowerCase().trim();
  }

  function apply() {
    const q = normalize(search.value);
    const cat = category ? category.value : "";
    const diff = difficulty ? difficulty.value : "";
    let shown = 0;

    cards.forEach((card) => {
      const hay = normalize(card.getAttribute("data-search"));
      const cardCat = card.getAttribute("data-category") || "";
      const diffs = (card.getAttribute("data-difficulties") || "").split(",");
      const matchQ = !q || hay.includes(q);
      const matchCat = !cat || cardCat === cat;
      const matchDiff = !diff || diffs.includes(diff);
      const ok = matchQ && matchCat && matchDiff;
      card.hidden = !ok;
      if (ok) shown += 1;
    });

    if (empty) empty.hidden = shown !== 0;
    if (countEl) countEl.textContent = shown + " tool" + (shown === 1 ? "" : "s");
  }

  search.addEventListener("input", apply);
  if (category) category.addEventListener("change", apply);
  if (difficulty) difficulty.addEventListener("change", apply);
  apply();
})();
