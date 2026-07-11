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

  /* ---- Reel: swap poster for the YouTube embed on click ---- */
  var reels = document.querySelectorAll(".reel[data-yt]");
  reels.forEach(function (r) {
    function play() {
      var id = r.getAttribute("data-yt");
      if (!id || r.dataset.played) return;
      r.dataset.played = "1";
      var f = document.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1&rel=0";
      f.title = "Video player";
      f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      f.allowFullscreen = true;
      r.innerHTML = "";
      r.appendChild(f);
    }
    r.addEventListener("click", play);
    r.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); play(); }
    });
  });

  /* ---- Footer year ---- */
  var y = document.querySelector("[data-year]");
  if (y) y.textContent = new Date().getFullYear();
})();
