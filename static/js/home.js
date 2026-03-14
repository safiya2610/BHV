document.addEventListener("DOMContentLoaded", () => {
  const revealNodes = document.querySelectorAll("[data-reveal]");
  if (!revealNodes.length) return;

  revealNodes.forEach((node, index) => {
    node.style.setProperty("--reveal-delay", `${Math.min(index * 90, 360)}ms`);
  });

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        obs.unobserve(entry.target);
      });
    },
    { threshold: 0.2, rootMargin: "0px 0px -10% 0px" }
  );

  revealNodes.forEach((node) => observer.observe(node));
});
