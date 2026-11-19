// CloudCart browser-side enhancements.
// The core shopping cart is handled by Flask; this file improves the interface.

document.addEventListener("DOMContentLoaded", () => {
  // Mobile navigation: show/hide the menu when the hamburger button is clicked.
  const menuButton = document.querySelector(".menu-toggle");
  const navigation = document.querySelector(".main-nav");

  if (menuButton && navigation) {
    menuButton.addEventListener("click", () => {
      const isOpen = navigation.classList.toggle("open");
      menuButton.setAttribute("aria-expanded", String(isOpen));
      menuButton.textContent = isOpen ? "×" : "☰";
    });
  }

  // Flash messages can be dismissed by the visitor.
  document.querySelectorAll(".flash-close").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest(".flash")?.remove();
    });
  });

  // Automatically hide temporary feedback after a few seconds.
  document.querySelectorAll(".flash").forEach((message) => {
    window.setTimeout(() => message.remove(), 6000);
  });
});
