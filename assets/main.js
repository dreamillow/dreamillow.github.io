(function () {
  "use strict";

  var root = document.documentElement;

  function prefersReducedMotion() {
    return (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  /* Scroll reveal.
     The .js class is what lets the stylesheet hide .reveal elements, so it is
     added ONLY once we know we can also take them back out of hiding. If the
     observer is unavailable or motion is reduced, we bail before adding it and
     the content simply renders. */
  function setUpReveal() {
    var targets = document.querySelectorAll(".reveal");

    if (!targets.length) {
      return;
    }

    if (prefersReducedMotion() || !("IntersectionObserver" in window)) {
      return;
    }

    root.classList.add("js");

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -10% 0px" }
    );

    Array.prototype.forEach.call(targets, function (target) {
      observer.observe(target);
    });
  }

  /* Parallax for the decorative dune layers.
     Purely ornamental: the layers are already in their resting position, so
     doing nothing here leaves a correct, static scene. */
  function setUpParallax() {
    var layers = document.querySelectorAll(".dune[data-speed]");

    if (!layers.length || prefersReducedMotion()) {
      return;
    }

    var ticking = false;

    function update() {
      var offset = window.pageYOffset || root.scrollTop || 0;

      Array.prototype.forEach.call(layers, function (layer) {
        var speed = parseFloat(layer.getAttribute("data-speed")) || 0;
        layer.style.transform = "translate3d(0," + offset * speed + "px,0)";
      });

      ticking = false;
    }

    function onScroll() {
      if (ticking) {
        return;
      }
      ticking = true;
      window.requestAnimationFrame(update);
    }

    if (!window.requestAnimationFrame) {
      return;
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    update();
  }

  setUpReveal();
  setUpParallax();
})();
