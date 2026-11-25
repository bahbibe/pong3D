// ESLint for the frontend modules (run by pre-commit; see .pre-commit-config.yaml).
import { realpathSync } from "node:fs";
import { createRequire } from "node:module";

// There is no package.json: pre-commit installs ESLint and these two packages
// together in its own Node env. Load them from next to the running eslint.
const require = createRequire(realpathSync(process.argv[1]));
const js = require("@eslint/js");
const globals = require("globals");

export default [
  { ignores: ["static/vendor/**"] },
  js.configs.recommended,
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: "module",
      globals: {
        ...globals.browser,
        // Bootstrap's bundle, loaded by a <script> tag in index.html.
        bootstrap: "readonly",
      },
    },
    rules: {
      eqeqeq: ["error", "always"],
      "no-console": ["error", { allow: ["warn", "error"] }],
      "no-unused-vars": ["error", { argsIgnorePattern: "^_", caughtErrors: "none" }],
      "prefer-const": "error",
      "no-var": "error",
    },
  },
  // This config file itself runs in Node.
  { files: ["eslint.config.js"], languageOptions: { globals: globals.node } },
];
