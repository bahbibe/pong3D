import { html, render } from "./html.js";

const parts = () => {
  const el = document.querySelector("#toast-wrapper .toast");
  return (
    el && {
      el,
      title: el.querySelector(".toast-header .me-auto"),
      body: el.querySelector(".toast-body"),
    }
  );
};

/**
 * Show the toast. `errors` are per-field messages from the API
 * ({field: message}); when there are some they replace `message`.
 */
export const showToast = (isError, message, errors) => {
  const toast = parts();
  if (!toast) return;
  toast.el.classList.toggle("text-bg-danger", Boolean(isError));
  toast.el.classList.toggle("text-bg-success", !isError);
  toast.title.textContent = isError ? "Error" : "Success";
  const fields = Object.entries(errors || {});
  if (fields.length > 0) {
    render(toast.body, html`${fields.map(([field, text]) => html`<p>${field}: ${text}</p>`)}`);
  } else {
    toast.body.textContent = message || "Something went wrong!. Please try again later";
  }
  toast.el.classList.add("show");
  toast.el.classList.remove("hide");
};

export const hideToast = () => {
  const toast = parts();
  if (!toast) return;
  toast.el.classList.remove("show");
  toast.el.classList.add("hide");
};

export const toast = {
  error: (message, errors) => showToast(true, message, errors),
  success: (message) => showToast(false, message),
  hide: hideToast,
};
