// Theme toggle
const themeToggle = document.querySelector('.theme-toggle');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  themeToggle.textContent = theme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
}

// Init theme from localStorage or system preference
const saved = localStorage.getItem('theme');
if (saved) {
  setTheme(saved);
} else {
  setTheme(prefersDark.matches ? 'dark' : 'light');
}

themeToggle.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  setTheme(current === 'dark' ? 'light' : 'dark');
});

// Mobile menu toggle
const menuBtn = document.querySelector('.mobile-menu-btn');
const nav = document.querySelector('.nav');

if (menuBtn) {
  menuBtn.addEventListener('click', () => {
    nav.classList.toggle('active');
    menuBtn.textContent = nav.classList.contains('active') ? '\u2715' : '\u2630';
  });
}
