/* SQL Playground - shared site behavior */
(function () {
  "use strict";

  var THEME_KEY = "sqlp-theme";
  var root = document.documentElement;

  function getTheme() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function syncThemeControls(theme) {
    var isDark = theme === "dark";
    var label = isDark ? "Switch to light theme" : "Switch to dark theme";

    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      button.setAttribute("aria-pressed", String(isDark));
      button.setAttribute("aria-label", label);
      button.setAttribute("title", label);
    });

    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute("content", isDark ? "#050B1A" : "#1F6BFF");
    }
  }

  function applyTheme(theme, persist) {
    root.setAttribute("data-theme", theme);

    if (persist) {
      try {
        window.localStorage.setItem(THEME_KEY, theme);
      } catch (error) {
        /* Storage can be disabled; the theme still applies for this page. */
      }
    }

    syncThemeControls(theme);
  }

  function setupTheme() {
    syncThemeControls(getTheme());

    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
      button.addEventListener("click", function () {
        applyTheme(getTheme() === "dark" ? "light" : "dark", true);
      });
    });
  }

  function setupMenus() {
    document.querySelectorAll("[data-menu-toggle]").forEach(function (toggle) {
      var menuId = toggle.getAttribute("aria-controls");
      var menu = menuId ? document.getElementById(menuId) : null;

      if (!menu) {
        return;
      }

      function openMenu() {
        menu.hidden = false;
        menu.classList.add("is-open");
        toggle.setAttribute("aria-expanded", "true");
        toggle.setAttribute("aria-label", "Close menu");
      }

      function closeMenu(returnFocus) {
        if (menu.hidden) {
          return;
        }
        menu.hidden = true;
        menu.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
        if (returnFocus) {
          toggle.focus();
        }
      }

      toggle.addEventListener("click", function () {
        if (menu.hidden) {
          openMenu();
        } else {
          closeMenu(false);
        }
      });

      menu.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
          closeMenu(false);
        });
      });

      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          closeMenu(true);
        }
      });

      document.addEventListener("click", function (event) {
        if (menu.hidden) {
          return;
        }
        if (menu.contains(event.target) || toggle.contains(event.target)) {
          return;
        }
        closeMenu(false);
      });
    });
  }

  function setupHeader() {
    var header = document.querySelector("[data-header]");
    if (!header) {
      return;
    }

    function updateHeader() {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    }

    updateHeader();
    window.addEventListener("scroll", updateHeader, { passive: true });
  }

  function setupPasswordToggles() {
    document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        var wrap = button.closest(".password-wrap");
        var input = wrap ? wrap.querySelector("input") : null;

        if (!input) {
          return;
        }

        var show = input.type === "password";
        input.type = show ? "text" : "password";
        button.setAttribute("aria-pressed", String(show));
        button.setAttribute("aria-label", show ? "Hide password" : "Show password");
      });
    });
  }

  function setupPreview() {
    document.querySelectorAll("[data-preview]").forEach(function (preview) {
      var run = preview.querySelector("[data-preview-run]");
      var empty = preview.querySelector("[data-preview-empty]");
      var result = preview.querySelector("[data-preview-result]");
      var feedback = preview.querySelector("[data-preview-feedback]");
      var status = preview.querySelector("[data-preview-status]");
      var heroPreview = preview.closest(".hero-preview");

      if (!run || !result) {
        return;
      }

      function reserveHeight() {
        if (!window.matchMedia("(min-width: 901px)").matches) {
          if (heroPreview) {
            heroPreview.style.minHeight = "";
          }
          return;
        }

        var emptyHidden = empty ? empty.hidden : null;
        var resultHidden = result.hidden;
        var feedbackHidden = feedback ? feedback.hidden : null;

        if (empty) {
          empty.hidden = true;
        }
        result.hidden = false;
        if (feedback) {
          feedback.hidden = false;
        }

        var reserved = preview.getBoundingClientRect().height + "px";

        if (empty) {
          empty.hidden = emptyHidden;
        }
        result.hidden = resultHidden;
        if (feedback) {
          feedback.hidden = feedbackHidden;
        }
        if (heroPreview) {
          heroPreview.style.minHeight = reserved;
        }
      }

      var resizeTimer;
      reserveHeight();
      window.addEventListener("load", reserveHeight);
      window.addEventListener("resize", function () {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(reserveHeight, 120);
      });

      run.addEventListener("click", function () {
        if (run.getAttribute("aria-busy") === "true") {
          return;
        }

        run.setAttribute("aria-busy", "true");
        run.textContent = "Running";
        if (empty) {
          empty.hidden = true;
        }
        result.hidden = true;
        if (feedback) {
          feedback.hidden = true;
        }

        window.setTimeout(function () {
          run.removeAttribute("aria-busy");
          run.textContent = "Run query";
          result.hidden = false;
          if (feedback) {
            feedback.hidden = false;
          }
          if (status) {
            status.textContent =
              "Query finished. 24 rows returned. Feedback ready.";
          }
        }, 320);
      });
    });
  }

  var COMMON_PASSWORDS = [
    "123456", "1234567", "12345678", "123456789", "1234567890", "123123",
    "12345", "abc123", "password", "password1", "password123", "passw0rd",
    "p@ssw0rd", "qwerty", "qwerty123", "qwertyuiop", "letmein", "welcome",
    "welcome1", "admin", "admin123", "iloveyou", "monkey", "dragon",
    "sunshine", "princess", "football", "baseball", "basketball", "superman",
    "batman", "trustno1", "master", "shadow", "michael", "jennifer",
    "jordan", "harley", "ranger", "hunter", "buster", "soccer", "hockey",
    "killer", "george", "andrew", "charlie", "thomas", "robert", "access",
    "starwars", "whatever", "freedom", "hello", "hello123", "test", "test123",
    "changeme", "secret", "summer", "winter", "spring", "autumn", "computer",
    "internet", "samsung", "google"
  ];

  function normalizeText(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "");
  }

  function longestSharedRun(a, b) {
    var best = 0;
    var previous = [];
    var i;
    var j;

    for (i = 0; i <= b.length; i += 1) {
      previous.push(0);
    }

    for (i = 1; i <= a.length; i += 1) {
      var current = [0];
      for (j = 1; j <= b.length; j += 1) {
        if (a.charAt(i - 1) === b.charAt(j - 1)) {
          current[j] = previous[j - 1] + 1;
          if (current[j] > best) {
            best = current[j];
          }
        } else {
          current[j] = 0;
        }
      }
      previous = current;
    }

    return best;
  }

  function looksLikePersonalInfo(password, values) {
    var normalized = normalizeText(password);
    if (normalized.length < 8) {
      return false;
    }

    return values.some(function (value) {
      var field = normalizeText(value);
      if (field.length < 4) {
        return false;
      }
      if (field.indexOf(normalized) !== -1 || normalized.indexOf(field) !== -1) {
        return true;
      }
      return longestSharedRun(normalized, field) / normalized.length >= 0.7;
    });
  }

  function setupPasswordRules() {
    var rules = document.querySelector("[data-pw-rules]");
    if (!rules) {
      return;
    }

    var form = rules.closest("form");
    var password = form ? form.querySelector("#id_password1") : null;
    if (!form || !password) {
      return;
    }

    var confirm = form.querySelector("#id_password2");
    var match = form.querySelector("[data-pw-match]");
    var ok = rules.querySelector("[data-pw-ok]");
    var items = {};

    rules.querySelectorAll("[data-pw-rule]").forEach(function (item) {
      items[item.getAttribute("data-pw-rule")] = item;
    });

    function valueOf(id) {
      var input = form.querySelector("#" + id);
      return input ? input.value : "";
    }

    function update() {
      var value = password.value;
      var empty = value.length === 0;
      var failed = {
        length: value.length < 8,
        common:
          !empty &&
          COMMON_PASSWORDS.indexOf(value.toLowerCase().trim()) !== -1,
        numeric: !empty && /^[0-9]+$/.test(value),
        similar:
          !empty &&
          looksLikePersonalInfo(value, [
            valueOf("id_username"),
            valueOf("id_email"),
            valueOf("id_first_name"),
            valueOf("id_last_name")
          ])
      };
      var anyFailed = false;

      Object.keys(items).forEach(function (key) {
        var failedNow = !empty && failed[key];
        items[key].hidden = !failedNow;
        if (failedNow) {
          anyFailed = true;
        }
      });

      if (ok) {
        ok.hidden = empty || anyFailed;
      }

      rules.classList.toggle("is-active", !empty);
      password.classList.toggle("is-invalid", !empty && anyFailed);

      if (confirm && match) {
        var mismatch = confirm.value.length > 0 && confirm.value !== value;
        match.hidden = !mismatch;
        confirm.classList.toggle("is-invalid", mismatch);
      }
    }

    password.addEventListener("input", update);
    if (confirm) {
      confirm.addEventListener("input", update);
    }
    ["id_username", "id_email", "id_first_name", "id_last_name"].forEach(
      function (id) {
        var input = form.querySelector("#" + id);
        if (input) {
          input.addEventListener("input", update);
        }
      }
    );

    update();
  }

  function setupReveal() {
    var items = document.querySelectorAll(".reveal");
    if (!items.length) {
      return;
    }

    var reduceMotion =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (item) {
        item.classList.add("is-visible");
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.12 }
    );

    items.forEach(function (item) {
      observer.observe(item);
    });
  }

  function setupClearEditor() {
    document.querySelectorAll("[data-clear-editor]").forEach(function (button) {
      button.addEventListener("click", function () {
        var form = button.closest("form");
        var editor = form ? form.querySelector(".sql-editor") : null;

        if (!editor) {
          return;
        }

        editor.value = "";
        editor.focus();
      });
    });
  }

  setupTheme();
  setupMenus();
  setupHeader();
  setupPasswordToggles();
  setupPasswordRules();
  setupPreview();
  setupClearEditor();
  setupReveal();
})();
