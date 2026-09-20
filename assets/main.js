(function () {
  "use strict";

  var root = document.documentElement;
  var targets = document.querySelectorAll(".reveal");

  if (!targets.length) {
    return;
  }

  var reduced =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Only claim the .js contract when we can actually reveal the elements again.
  if (reduced || !("IntersectionObserver" in window)) {
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
})();
