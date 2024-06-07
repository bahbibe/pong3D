class AbstractPage extends HTMLElement {
  constructor() {
    super()
  }

  get params() {
    return JSON.parse(this.getAttribute("params"));
  }
}

export { AbstractPage }