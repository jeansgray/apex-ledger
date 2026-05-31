/**
 * Nebula gate + holo tile panel controller (dashboard + docs).
 */
(function () {
  const deck = document.getElementById("holo-deck");
  if (!deck) return;

  const panels = {};
  deck.querySelectorAll(".holo-tile[data-panel]").forEach((tile) => {
    const id = tile.dataset.panel;
    panels[id] = document.getElementById("holo-panel-" + id);
  });

  let active = null;

  function setTileState(id, on) {
    const tile = deck.querySelector(`[data-panel="${id}"]`);
    if (tile) tile.classList.toggle("active", on);
  }

  function closeAll() {
    Object.entries(panels).forEach(([id, el]) => {
      if (!el) return;
      el.hidden = true;
      el.classList.remove("open");
      setTileState(id, false);
    });
    active = null;
  }

  function openPanel(id) {
    const panel = panels[id];
    if (!panel) return;
    if (active === id) {
      closeAll();
      return;
    }
    Object.entries(panels).forEach(([pid, el]) => {
      if (!el) return;
      const show = pid === id;
      el.hidden = !show;
      el.classList.toggle("open", show);
      setTileState(pid, show);
    });
    active = id;
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  deck.addEventListener("click", (e) => {
    const tile = e.target.closest(".holo-tile");
    if (!tile || !document.body.classList.contains("gate-open")) return;
    openPanel(tile.dataset.panel);
  });

  deck.querySelectorAll(".holo-tile").forEach((tile) => {
    tile.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openPanel(tile.dataset.panel);
      }
    });
  });

  document.querySelectorAll("[data-close-panel]").forEach((btn) => {
    btn.addEventListener("click", () => closeAll());
  });

  window.ApexPortal = { openPanel, closeAll };
})();
