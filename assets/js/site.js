/* Theme switching. The page ships in the dark theme; a choice is remembered
   per browser where storage is available, and the site works without it. */
(function () {
  "use strict";

  var KEY = "rs-theme";
  var root = document.documentElement;

  function read() {
    try {
      return localStorage.getItem(KEY);
    } catch (err) {
      return null;
    }
  }

  function save(value) {
    try {
      localStorage.setItem(KEY, value);
    } catch (err) {
      /* private mode, blocked storage: the choice simply does not persist */
    }
  }

  function paint(theme) {
    root.setAttribute("data-theme", theme);
    var buttons = document.querySelectorAll("[data-theme-set]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute(
        "aria-pressed",
        buttons[i].getAttribute("data-theme-set") === theme ? "true" : "false"
      );
    }
  }

  var stored = read();
  paint(stored === "light" || stored === "dark" ? stored : "dark");

  document.addEventListener("click", function (event) {
    var target = event.target.closest ? event.target.closest("[data-theme-set]") : null;
    if (!target) return;
    var theme = target.getAttribute("data-theme-set");
    paint(theme);
    save(theme);
  });
})();
