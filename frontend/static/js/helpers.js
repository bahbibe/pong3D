export { hideToast, showToast } from "./core/toast.js";

import { overlay } from "./core/overlay.js";

export const showOverlay = () => overlay.show();
export const hideOverlay = () => overlay.hide();
