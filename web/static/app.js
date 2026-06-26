// AUTO-GENERATED from web/src/app.jsx by `node web/build.js`. Do not edit.
// Source for the web UI. Compiled to web/static/app.js by `node web/build.js`.
// Plain React (no JSX runtime import needed — React is a global from vendor/).

const {
  useState,
  useCallback,
  useRef
} = React;
const ACCEPT = ".pdf,.png,.jpg,.jpeg";
function Header() {
  return /*#__PURE__*/React.createElement("header", {
    className: "header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "header-inner"
  }, /*#__PURE__*/React.createElement("h1", null, "🧾 Invoice Extractor"), /*#__PURE__*/React.createElement("p", null, "Drop a PDF or image invoice — get structured data back.", " ", /*#__PURE__*/React.createElement("span", {
    className: "accent"
  }, "Offline · rule-based · no API cost."))));
}
function Dropzone({
  onFile
}) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const onDrop = e => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) onFile(f);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "dropzone" + (dragging ? " dragging" : ""),
    onDragOver: e => {
      e.preventDefault();
      setDragging(true);
    },
    onDragLeave: () => setDragging(false),
    onDrop: onDrop,
    onClick: () => inputRef.current && inputRef.current.click()
  }, /*#__PURE__*/React.createElement("input", {
    ref: inputRef,
    type: "file",
    accept: ACCEPT,
    style: {
      display: "none"
    },
    onChange: e => {
      const f = e.target.files[0];
      if (f) onFile(f);
      e.target.value = "";
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "icon"
  }, "⬆️"), /*#__PURE__*/React.createElement("div", {
    className: "title"
  }, "Drag & drop an invoice here"), /*#__PURE__*/React.createElement("div", {
    className: "hint"
  }, "or click to browse · PDF, PNG, JPG"));
}
function Spinner({
  filename
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "card pad center fade-in"
  }, /*#__PURE__*/React.createElement("div", {
    className: "spinner"
  }), /*#__PURE__*/React.createElement("p", {
    style: {
      fontWeight: 500,
      color: "#334155",
      marginBottom: 0
    }
  }, "Extracting…"), /*#__PURE__*/React.createElement("p", {
    className: "muted truncate",
    style: {
      margin: "4px auto 0"
    }
  }, filename));
}
function ErrorCard({
  error,
  onReset
}) {
  const [showText, setShowText] = useState(false);
  const hasText = error.extracted_text && error.extracted_text.trim().length > 0;
  return /*#__PURE__*/React.createElement("div", {
    className: "error-card fade-in"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row",
    style: {
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 24
    }
  }, "⚠️"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("p", {
    className: "etitle"
  }, error.hint || "Couldn't process the file"), /*#__PURE__*/React.createElement("p", {
    className: "emsg"
  }, error.message), /*#__PURE__*/React.createElement("span", {
    className: "badge err",
    style: {
      marginTop: 12
    }
  }, error.error_type))), /*#__PURE__*/React.createElement("div", {
    className: "row",
    style: {
      marginTop: 20
    }
  }, /*#__PURE__*/React.createElement("button", {
    className: "btn btn-dark",
    onClick: onReset
  }, "Try another file"), hasText && /*#__PURE__*/React.createElement("button", {
    className: "btn btn-ghost",
    onClick: () => setShowText(!showText)
  }, showText ? "Hide extracted text" : "Show extracted text")), hasText && showText && /*#__PURE__*/React.createElement("pre", {
    className: "json fade-in",
    style: {
      marginTop: 16
    }
  }, error.extracted_text));
}
function Stat({
  label,
  value
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "stat"
  }, /*#__PURE__*/React.createElement("div", {
    className: "label"
  }, label), /*#__PURE__*/React.createElement("div", {
    className: "value"
  }, value));
}
function Result({
  data,
  onReset
}) {
  const [showJson, setShowJson] = useState(false);
  const [copied, setCopied] = useState(false);
  const inv = data.invoice;
  const jsonStr = JSON.stringify(inv, null, 2);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(jsonStr);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (e) {
      alert("Copy failed: " + e);
    }
  };
  const download = () => {
    const blob = new Blob([jsonStr], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = (inv.invoice_number || "invoice") + ".json";
    a.click();
    URL.revokeObjectURL(url);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "stack fade-in"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row between"
  }, /*#__PURE__*/React.createElement("div", {
    className: "row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "badge ok"
  }, "✓ Totals reconciled"), /*#__PURE__*/React.createElement("span", {
    className: "muted truncate"
  }, data.filename)), /*#__PURE__*/React.createElement("button", {
    className: "link",
    onClick: onReset
  }, "↻ Extract another")), /*#__PURE__*/React.createElement("div", {
    className: "stat-grid"
  }, /*#__PURE__*/React.createElement(Stat, {
    label: "Vendor",
    value: inv.vendor
  }), /*#__PURE__*/React.createElement(Stat, {
    label: "Invoice #",
    value: inv.invoice_number
  }), /*#__PURE__*/React.createElement(Stat, {
    label: "Date",
    value: inv.date
  }), /*#__PURE__*/React.createElement(Stat, {
    label: "Total",
    value: inv.total + " " + inv.currency
  })), /*#__PURE__*/React.createElement("div", {
    className: "card table-card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "table-wrap"
  }, /*#__PURE__*/React.createElement("table", null, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", null, "Description"), /*#__PURE__*/React.createElement("th", {
    className: "r"
  }, "Qty"), /*#__PURE__*/React.createElement("th", {
    className: "r"
  }, "Unit price"), /*#__PURE__*/React.createElement("th", {
    className: "r"
  }, "Amount"))), /*#__PURE__*/React.createElement("tbody", null, inv.line_items.map((it, i) => /*#__PURE__*/React.createElement("tr", {
    key: i
  }, /*#__PURE__*/React.createElement("td", null, it.description), /*#__PURE__*/React.createElement("td", {
    className: "r num"
  }, it.quantity), /*#__PURE__*/React.createElement("td", {
    className: "r num"
  }, it.unit_price), /*#__PURE__*/React.createElement("td", {
    className: "r num",
    style: {
      fontWeight: 500
    }
  }, it.amount)))), /*#__PURE__*/React.createElement("tfoot", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("td", {
    colSpan: 3
  }, "Total"), /*#__PURE__*/React.createElement("td", {
    className: "r num"
  }, inv.total, " ", inv.currency)))))), /*#__PURE__*/React.createElement("div", {
    className: "row"
  }, /*#__PURE__*/React.createElement("button", {
    className: "btn btn-primary",
    onClick: copy
  }, copied ? "Copied!" : "Copy JSON"), /*#__PURE__*/React.createElement("button", {
    className: "btn btn-secondary",
    onClick: download
  }, "Download JSON"), /*#__PURE__*/React.createElement("button", {
    className: "btn btn-ghost",
    onClick: () => setShowJson(!showJson)
  }, showJson ? "Hide raw JSON" : "Show raw JSON")), showJson && /*#__PURE__*/React.createElement("pre", {
    className: "json fade-in"
  }, jsonStr));
}
function App() {
  const [status, setStatus] = useState("idle");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [filename, setFilename] = useState("");
  const reset = () => {
    setStatus("idle");
    setData(null);
    setError(null);
    setFilename("");
  };
  const handleFile = useCallback(async file => {
    setFilename(file.name);
    setStatus("loading");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        body: form
      });
      const json = await res.json();
      if (json.ok) {
        setData(json);
        setStatus("done");
      } else {
        setError(json);
        setStatus("error");
      }
    } catch (e) {
      setError({
        error_type: "network",
        hint: "Couldn't reach the server.",
        message: String(e)
      });
      setStatus("error");
    }
  }, []);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Header, null), /*#__PURE__*/React.createElement("main", {
    className: "container stack"
  }, status === "idle" && /*#__PURE__*/React.createElement(Dropzone, {
    onFile: handleFile
  }), status === "loading" && /*#__PURE__*/React.createElement(Spinner, {
    filename: filename
  }), status === "error" && /*#__PURE__*/React.createElement(ErrorCard, {
    error: error,
    onReset: reset
  }), status === "done" && /*#__PURE__*/React.createElement(Result, {
    data: data,
    onReset: reset
  }), /*#__PURE__*/React.createElement("p", {
    className: "foot"
  }, "Parsing runs entirely on your machine — no external API, no token cost.")));
}
ReactDOM.createRoot(document.getElementById("root")).render(/*#__PURE__*/React.createElement(App, null));