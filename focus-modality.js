"use strict";

(() => {
  const root = document.documentElement;
  root.dataset.focusInput = "pointer";
  document.addEventListener("pointerdown", () => {
    root.dataset.focusInput = "pointer";
  }, true);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Tab") root.dataset.focusInput = "keyboard";
  }, true);
})();
