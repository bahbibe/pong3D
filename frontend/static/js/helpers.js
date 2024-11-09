export const hideToast = () => {
  document.querySelector(`#toast-wrapper .toast`).classList.remove("show");
  document.querySelector(`#toast-wrapper .toast`).classList.add("hide");
}

export const showToast = (isError, message, errors) => {
  const errorsEl = document.querySelector(`#toast-wrapper .toast`);
  if (isError) {
    errorsEl.classList.add("text-bg-danger");
    errorsEl.classList.remove("text-bg-success");
    document.querySelector(`#toast-wrapper .toast-header .me-auto`).innerHTML = "Error";
  } else {
    errorsEl.classList.remove("text-bg-danger");
    errorsEl.classList.add("text-bg-success");
    document.querySelector(`#toast-wrapper .toast-header .me-auto`).innerHTML = "Success";
  }
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
  setInterval(() => showOverlay.style.display = "none", 100);
}