/* Quentin Fears site interactions. Dependency-free, progressive. */
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

  /* ---- Contact form: submit to FormSubmit (formsubmit.co) via AJAX, inline status.
     No-JS visitors get a normal POST to the same endpoint. ---- */
  var form = document.getElementById("contact-form");
  if (form) {
    var status = form.querySelector(".form-status");
    var action = form.getAttribute("action") || "";
    var ajax = action.replace("formsubmit.co/", "formsubmit.co/ajax/");
    form.addEventListener("submit", function (e) {
      // let it POST normally if the endpoint isn't a FormSubmit URL (e.g. Netlify)
      if (action.indexOf("formsubmit.co/") === -1) return;
      e.preventDefault();
      var honey = form.querySelector('[name="_honey"]');
      if (honey && honey.value) return; // bot
      if (typeof form.checkValidity === "function" && !form.checkValidity()) {
        form.reportValidity();
        return;
      }
      var btn = form.querySelector('button[type="submit"]');
      var data = new FormData(form);
      data.set("_subject", "[" + (data.get("inquiry") || "General") + "] New inquiry via quentinfears.com");
      var label = btn ? btn.innerHTML : "";
      if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
      if (status) { status.textContent = ""; status.className = "form-status"; }
      fetch(ajax, { method: "POST", body: data, headers: { Accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (res && (res.success === true || res.success === "true")) {
            form.reset();
            if (status) { status.textContent = "Thanks, your message is on its way. I'll be in touch soon."; status.className = "form-status form-status--ok"; }
          } else { throw new Error((res && res.message) || "failed"); }
        })
        .catch(function () {
          if (status) { status.textContent = "Something went wrong. Please email hello@quentinfears.com directly."; status.className = "form-status form-status--err"; }
        })
        .finally(function () { if (btn) { btn.disabled = false; btn.innerHTML = label; } });
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

  /* ---- Reel card: swap poster for a self-hosted <video> on click ---- */
  var vreels = document.querySelectorAll(".reel-card[data-video]");
  vreels.forEach(function (r) {
    function play() {
      if (r.dataset.played) return;
      r.dataset.played = "1";
      var media = r.querySelector(".reel-card__media");
      if (!media) return;
      var v = document.createElement("video");
      v.src = r.getAttribute("data-video");
      var poster = r.getAttribute("data-poster");
      if (poster) v.poster = poster;
      v.controls = true;
      v.autoplay = true;
      v.playsInline = true;
      v.setAttribute("playsinline", "");
      v.preload = "metadata";
      v.className = "reel-card__video";
      media.innerHTML = "";
      media.appendChild(v);
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
