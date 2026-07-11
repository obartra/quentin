/* Quentin Fears — site interactions. Dependency-free, progressive. */
(function () {
  "use strict";

  /* ---- Mobile nav toggle ---- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.getAttribute("data-open") === "true";
      nav.setAttribute("data-open", String(!open));
      toggle.setAttribute("aria-expanded", String(!open));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.setAttribute("data-open", "false");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---- Reveal on scroll ---- */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  }

  /* ---- Contact form: friendly no-backend fallback via mailto ---- */
  var form = document.getElementById("contact-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      // If the form has a real action endpoint configured, let it submit normally.
      if (form.getAttribute("action") && form.getAttribute("action").indexOf("mailto:") !== 0) return;
      e.preventDefault();
      var data = new FormData(form);
      var type = data.get("inquiry") || "General";
      var name = data.get("name") || "";
      var org = data.get("org") || "";
      var email = data.get("email") || "";
      var message = data.get("message") || "";
      var subject = encodeURIComponent("[" + type + "] Inquiry from " + name);
      var body = encodeURIComponent(
        "Inquiry type: " + type + "\nName: " + name + "\nOrganization: " + org +
        "\nEmail: " + email + "\n\n" + message
      );
      window.location.href = "mailto:hello@quentinfears.com?subject=" + subject + "&body=" + body;
    });
  }

  /* ---- Footer year ---- */
  var y = document.querySelector("[data-year]");
  if (y) y.textContent = new Date().getFullYear();
})();
