// Compile web/src/app.jsx -> web/static/app.js (plain browser JS, no JSX).
// Run:  node web/build.js
// Uses the bundled Babel standalone in web/buildtools/ so no npm install is needed.

const fs = require("fs");
const path = require("path");

const root = __dirname;
const Babel = require(path.join(root, "buildtools", "babel.min.js"));

const srcPath = path.join(root, "src", "app.jsx");
const outPath = path.join(root, "static", "app.js");

const source = fs.readFileSync(srcPath, "utf8");
const { code } = Babel.transform(source, {
  // classic runtime -> React.createElement(...) using the global UMD `React`,
  // so the output runs as a plain <script> with no module imports.
  presets: [["react", { runtime: "classic" }]],
  filename: "app.jsx",
});

const banner = "// AUTO-GENERATED from web/src/app.jsx by `node web/build.js`. Do not edit.\n";
fs.writeFileSync(outPath, banner + code, "utf8");
console.log("wrote " + path.relative(root, outPath) + " (" + code.length + " chars)");
