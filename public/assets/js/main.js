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

  /* ---- Lightbox galleries (Work page) ---- */
  var galData = document.getElementById("gallery-data");
  var triggers = document.querySelectorAll("[data-gallery]");
  if (galData && triggers.length) {
    var galleries = {};
    try { galleries = JSON.parse(galData.textContent); } catch (_) {}

    var lb = document.createElement("div");
    lb.className = "lb";
    lb.setAttribute("role", "dialog");
    lb.setAttribute("aria-modal", "true");
    lb.setAttribute("aria-label", "Image gallery");
    lb.innerHTML =
      '<div class="lb__stage">' +
      '<button class="lb__close" aria-label="Close">✕</button>' +
      '<button class="lb__nav lb__nav--prev" aria-label="Previous">‹</button>' +
      '<img class="lb__img" alt="">' +
      '<button class="lb__nav lb__nav--next" aria-label="Next">›</button>' +
      '<div class="lb__bar"><span class="lb__cap"></span><span class="lb__count"></span></div>' +
      "</div>";
    document.body.appendChild(lb);

    var imgEl = lb.querySelector(".lb__img");
    var capEl = lb.querySelector(".lb__cap");
    var countEl = lb.querySelector(".lb__count");
    var items = [], i = 0, lastFocus = null;

    function render() {
      var it = items[i];
      if (!it) return;
      imgEl.src = it.src;
      imgEl.alt = it.cap || "";
      capEl.textContent = it.cap || "";
      countEl.textContent = (i + 1) + " / " + items.length;
    }
    function openGal(key, start) {
      items = galleries[key] || [];
      if (!items.length) return;
      i = start || 0;
      lastFocus = document.activeElement;
      render();
      lb.classList.add("open");
      document.body.style.overflow = "hidden";
      lb.querySelector(".lb__close").focus();
    }
    function closeGal() {
      lb.classList.remove("open");
      document.body.style.overflow = "";
      imgEl.src = "";
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    function step(d) { i = (i + d + items.length) % items.length; render(); }

    triggers.forEach(function (t) {
      t.addEventListener("click", function (e) {
        e.preventDefault();
        openGal(t.getAttribute("data-gallery"), +(t.getAttribute("data-start") || 0));
      });
    });
    lb.querySelector(".lb__close").addEventListener("click", closeGal);
    lb.querySelector(".lb__nav--prev").addEventListener("click", function () { step(-1); });
    lb.querySelector(".lb__nav--next").addEventListener("click", function () { step(1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) closeGal(); });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("open")) return;
      if (e.key === "Escape") closeGal();
      else if (e.key === "ArrowRight") step(1);
      else if (e.key === "ArrowLeft") step(-1);
    });
  }

  /* ---- Footer year ---- */
  var y = document.querySelector("[data-year]");
  if (y) y.textContent = new Date().getFullYear();
})();
