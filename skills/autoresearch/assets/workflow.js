(() => {
  const navButtons = [...document.querySelectorAll("[data-stage-target]")];
  const stageCards = [...document.querySelectorAll("[data-stage-card]")];
  const detailPanels = [...document.querySelectorAll("[data-stage-detail]")];
  const validStages = navButtons.map((button) => button.dataset.stageTarget);

  if (!validStages.length) return;

  const normalizeStage = (stage) => validStages.includes(stage) ? stage : validStages[0];

  const activateStage = (requestedStage, options = {}) => {
    const stage = normalizeStage(requestedStage);

    navButtons.forEach((button) => {
      const selected = button.dataset.stageTarget === stage;
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
    });

    stageCards.forEach((card) => {
      const selected = card.dataset.stageCard === stage;
      card.classList.toggle("is-active", selected);
      card.setAttribute("aria-current", selected ? "step" : "false");
    });

    detailPanels.forEach((panel) => {
      panel.hidden = panel.dataset.stageDetail !== stage;
    });

    if (options.updateHash !== false) {
      history.replaceState(null, "", `#${stage}`);
    }

    document.querySelectorAll("[data-language-link]").forEach((link) => {
      const base = link.getAttribute("href").split("#")[0];
      link.setAttribute("href", `${base}#${stage}`);
    });

    if (options.scrollDetail) {
      document.querySelector(".details-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  navButtons.forEach((button, index) => {
    button.addEventListener("click", () => activateStage(button.dataset.stageTarget));
    button.addEventListener("keydown", (event) => {
      if (!["ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      let nextIndex = index;
      if (["ArrowDown", "ArrowRight"].includes(event.key)) nextIndex = (index + 1) % navButtons.length;
      if (["ArrowUp", "ArrowLeft"].includes(event.key)) nextIndex = (index - 1 + navButtons.length) % navButtons.length;
      if (event.key === "Home") nextIndex = 0;
      if (event.key === "End") nextIndex = navButtons.length - 1;
      navButtons[nextIndex].focus();
      activateStage(navButtons[nextIndex].dataset.stageTarget);
    });
  });

  stageCards.forEach((card) => {
    const open = () => activateStage(card.dataset.stageCard, { scrollDetail: window.innerWidth < 1320 });
    card.addEventListener("click", (event) => {
      if (event.target.closest("a")) return;
      open();
    });
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open();
      }
    });
  });

  window.addEventListener("hashchange", () => activateStage(location.hash.slice(1), { updateHash: false }));
  activateStage(location.hash.slice(1), { updateHash: false });
})();
