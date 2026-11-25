import { escapeHTML } from "../escape.js";

/** Markup that is safe to insert: built by html`` or raw(). */
export class SafeHTML {
  constructor(value) {
    this.value = value;
  }

  toString() {
    return this.value;
  }
}

const piece = (value) => {
  if (value instanceof SafeHTML) return value.value;
  if (Array.isArray(value)) return value.map(piece).join("");
  if (value === null || value === undefined || typeof value === "boolean") return "";
  return escapeHTML(value);
};

/**
 * html`<p>${name}</p>`: every interpolated value is escaped, so server and
 * user data can never become markup. Nested html`` templates, raw() and
 * arrays of them (items.map(...)) are inserted as they are. null, undefined
 * and booleans render nothing, so `${cond && html`...`}` works.
 */
export const html = (strings, ...values) =>
  new SafeHTML(
    strings.reduce((out, text, i) => out + text + (i < values.length ? piece(values[i]) : ""), ""),
  );

/** The only way around escaping: trusted static markup, never data. */
export const raw = (markup) => new SafeHTML(String(markup));

/** Replace the content of `el` with a html`` template. */
export const render = (el, template) => {
  if (!(template instanceof SafeHTML)) throw new TypeError("render() takes a html`` template");
  el.innerHTML = template.value;
  return el;
};
