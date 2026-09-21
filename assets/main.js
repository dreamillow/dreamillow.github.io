(function () {
  "use strict";

  var root = document.documentElement;
  var revealTargets = [];
  var duneLayers = [];
  var ticking = false;

  function prefersReducedMotion() {
    return (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  /* Reveal is decided from geometry, not from a callback.
     An earlier version trusted IntersectionObserver to report; headless Chrome
     reports "not intersecting" once and then stays silent through a hash jump,
     which left the whole page blank. Measuring rectangles ourselves cannot fail
     that way, and we already run a scroll loop for the parallax. */
  function updateReveal() {
    if (!revealTargets.length) {
      return;
    }

    var viewport = window.innerHeight || root.clientHeight;
    var pending = [];

    for (var i = 0; i < revealTargets.length; i++) {
      var target = revealTargets[i];
      var box = target.getBoundingClientRect();

      if (box.top < viewport * 0.9 && box.bottom > 0) {
        target.classList.add("is-visible");
      } else {
        pending.push(target);
      }
    }

    revealTargets = pending;
  }

  function updateParallax() {
    if (!duneLayers.length) {
      return;
    }

    var offset = window.pageYOffset || root.scrollTop || 0;

    for (var i = 0; i < duneLayers.length; i++) {
      var layer = duneLayers[i];
      var speed = parseFloat(layer.getAttribute("data-speed")) || 0;
      layer.style.transform = "translate3d(0," + offset * speed + "px,0)";
    }
  }

  function onScroll() {
    if (ticking) {
      return;
    }

    ticking = true;
    window.requestAnimationFrame(function () {
      updateReveal();
      updateParallax();
      ticking = false;
    });
  }

  function start() {
    /* Reached only from inside an animation frame, so by now we know frames
       actually run here. That is the moment it becomes safe to let the
       stylesheet hide anything: the same frame reveals whatever is already on
       screen, so nothing flashes and nothing can get stranded invisible.

       Checking that requestAnimationFrame merely *exists* is not enough — it
       exists in headless Chrome under a virtual clock and never fires, which
       is how this page rendered completely blank. */
    var targets = document.querySelectorAll(".reveal");

    if (targets.length) {
      revealTargets = Array.prototype.slice.call(targets);
      root.classList.add("js");
      updateReveal();
    }

    duneLayers = Array.prototype.slice.call(
      document.querySelectorAll(".dune[data-speed]")
    );
    updateParallax();

    if (revealTargets.length || duneLayers.length) {
      window.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("resize", onScroll, { passive: true });

      /* A hash jump taken while the page is still loading moves the viewport
         without emitting a scroll event, so opening /#contact directly would
         otherwise land on a section that never un-hides. */
      window.addEventListener("load", onScroll);
      window.addEventListener("hashchange", onScroll);
    }
  }

  function init() {
    /* Reduced motion means the visitor asked us not to animate at all, so we
       leave the .js class off and the stylesheet never hides content. */
    if (prefersReducedMotion() || !window.requestAnimationFrame) {
      return;
    }

    window.requestAnimationFrame(start);
  }

  init();
})();
