// The full-page loading overlay (one, in index.html).
const element = () => document.getElementById("overlay");

export const overlay = {
  show() {
    const el = element();
    if (el) el.style.display = "block";
  },
  hide() {
    const el = element();
    if (el) el.style.display = "none";
  },
};
