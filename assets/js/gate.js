/* Soft password gate. NOTE: this is a client-side gate for keeping a
   work-in-progress out of casual view — it is NOT real security. The password
   is present in this file, so anyone who reads the source can bypass it. For
   true protection, use host-level auth (Cloudflare Access, Netlify password,
   a server, etc.). */
(function () {
  "use strict";
  var KEY = "qf-access";
  // password: "fearless" (base64-encoded here to keep it out of plain sight)
  var PW = "ZmVhcmxlc3M=";

  if (sessionStorage.getItem(KEY) === "1") {
    document.documentElement.classList.remove("locked");
    return;
  }

  function build() {
    var gate = document.createElement("div");
    gate.className = "gate";
    gate.innerHTML =
      '<div class="gate__card">' +
      '<p class="eyebrow">Private preview</p>' +
      '<h1>Quentin Fears</h1>' +
      '<p>Enter the password to continue.</p>' +
      '<form autocomplete="off"><input type="password" aria-label="Password" placeholder="Password" autocomplete="off"><button type="submit" class="btn btn--gold">Enter</button></form>' +
      '<p class="gate__err" role="alert" aria-live="polite"></p>' +
      "</div>";
    document.body.appendChild(gate);

    var form = gate.querySelector("form");
    var input = gate.querySelector("input");
    var err = gate.querySelector(".gate__err");

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var ok;
      try { ok = input.value === atob(PW); } catch (_) { ok = false; }
      if (ok) {
        sessionStorage.setItem(KEY, "1");
        document.documentElement.classList.remove("locked");
        gate.parentNode.removeChild(gate);
      } else {
        err.textContent = "Incorrect password.";
        input.value = "";
        input.focus();
      }
    });
    setTimeout(function () { input.focus(); }, 60);
  }

  if (document.body) build();
  else document.addEventListener("DOMContentLoaded", build);
})();
