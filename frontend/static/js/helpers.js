export const hideToast = (wrapperId) => {
  document.getElementById(wrapperId).classList.remove("show");
  document.getElementById(wrapperId).classList.add("hide");
}

export const showToast = (wrapperId, message, errors) => {
  const errorsEl = document.querySelector(`#${wrapperId} .toast`);
  const errorsContentEl = errorsEl.querySelector(".toast-body");
  if (errors && Object.keys(errors).length > 0) {
    message = Object.keys(errors).map(error => `<p>${error}: ${errors[error]}</p>`).join("");
  }
  errorsContentEl.innerHTML = message || "Something went wrong!. Please try again later";
  errorsEl.classList.add("show");
  errorsEl.classList.remove("hide");
  // setTimeout(() => {
  //   errorsEl.classList.remove("show");
  //   errorsEl.classList.add("hide");
  // }, 5000);
}


export const showOverlay = () =>{
  const showOverlay = document.querySelector("#overlay");
  showOverlay.style.display = "block";
}

export const hideOverlay = ()  =>{
  const showOverlay = document.querySelector("#overlay");
  setInterval(() => showOverlay.style.display = "none", 1000);
}