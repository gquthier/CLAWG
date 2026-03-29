const menuBtn = document.getElementById("menu-btn");
const menuLinks = document.getElementById("menu-links");

if (menuBtn && menuLinks) {
  menuBtn.addEventListener("click", () => {
    menuLinks.classList.toggle("open");
  });

  menuLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      menuLinks.classList.remove("open");
    });
  });
}

document.querySelectorAll(".copy").forEach((button) => {
  button.addEventListener("click", async () => {
    const id = button.getAttribute("data-copy");
    const codeNode = id ? document.getElementById(id) : null;
    if (!codeNode) return;

    const original = button.textContent;
    try {
      await navigator.clipboard.writeText(codeNode.textContent || "");
      button.textContent = "Copied";
    } catch {
      button.textContent = "Copy failed";
    }

    setTimeout(() => {
      button.textContent = original;
    }, 1500);
  });
});

const revealObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  },
  {
    threshold: 0.15,
    rootMargin: "0px 0px -40px 0px",
  },
);

document.querySelectorAll(".reveal").forEach((node) => revealObserver.observe(node));
