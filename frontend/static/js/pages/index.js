export { HomePage } from "./HomePage.js"
export { NotFoundPage } from "./NotFoundPage.js"
export { ChatPage } from "./ChatPage.js"
export { LoginPage } from "./LoginPage.js"
export { ProfilePage } from "./ProfilePage.js"
export { RankingPage } from "./RankingPage.js"
export { Home } from "./Home.js"
export { SettingsPage } from "./Settings.js"
export { SearchPage } from "./SearchPage.js"
export { FriendPage } from "./friendPage.js"
import { ErrorToast } from "../components/ErrorToast.js"

window.customElements.define("error-toast", ErrorToast);