// Source for the web UI. Compiled to web/static/app.js by `node web/build.js`.
// Plain React (no JSX runtime import needed — React is a global from vendor/).

const { useState, useCallback, useRef } = React;
const ACCEPT = ".pdf,.png,.jpg,.jpeg";

function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        <h1>🧾 Invoice Extractor</h1>
        <p>
          Drop a PDF or image invoice — get structured data back.{" "}
          <span className="accent">Offline · rule-based · no API cost.</span>
        </p>
      </div>
    </header>
  );
}

function Dropzone({ onFile }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) onFile(f);
  };
  return (
    <div
      className={"dropzone" + (dragging ? " dragging" : "")}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current && inputRef.current.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        style={{ display: "none" }}
        onChange={(e) => { const f = e.target.files[0]; if (f) onFile(f); e.target.value = ""; }}
      />
      <div className="icon">⬆️</div>
      <div className="title">Drag &amp; drop an invoice here</div>
      <div className="hint">or click to browse · PDF, PNG, JPG</div>
    </div>
  );
}

function Spinner({ filename }) {
  return (
    <div className="card pad center fade-in">
      <div className="spinner"></div>
      <p style={{ fontWeight: 500, color: "#334155", marginBottom: 0 }}>Extracting…</p>
      <p className="muted truncate" style={{ margin: "4px auto 0" }}>{filename}</p>
    </div>
  );
}

function ErrorCard({ error, onReset }) {
  const [showText, setShowText] = useState(false);
  const hasText = error.extracted_text && error.extracted_text.trim().length > 0;
  return (
    <div className="error-card fade-in">
      <div className="row" style={{ alignItems: "flex-start" }}>
        <div style={{ fontSize: 24 }}>⚠️</div>
        <div style={{ flex: 1 }}>
          <p className="etitle">{error.hint || "Couldn't process the file"}</p>
          <p className="emsg">{error.message}</p>
          <span className="badge err" style={{ marginTop: 12 }}>{error.error_type}</span>
        </div>
      </div>
      <div className="row" style={{ marginTop: 20 }}>
        <button className="btn btn-dark" onClick={onReset}>Try another file</button>
        {hasText && (
          <button className="btn btn-ghost" onClick={() => setShowText(!showText)}>
            {showText ? "Hide extracted text" : "Show extracted text"}
          </button>
        )}
      </div>
      {hasText && showText && <pre className="json fade-in" style={{ marginTop: 16 }}>{error.extracted_text}</pre>}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

function Result({ data, onReset }) {
  const [showJson, setShowJson] = useState(false);
  const [copied, setCopied] = useState(false);
  const inv = data.invoice;
  const jsonStr = JSON.stringify(inv, null, 2);

  const copy = async () => {
    try { await navigator.clipboard.writeText(jsonStr); setCopied(true); setTimeout(() => setCopied(false), 1500); }
    catch (e) { alert("Copy failed: " + e); }
  };
  const download = () => {
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = (inv.invoice_number || "invoice") + ".json"; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="stack fade-in">
      <div className="row between">
        <div className="row">
          <span className="badge ok">✓ Totals reconciled</span>
          <span className="muted truncate">{data.filename}</span>
        </div>
        <button className="link" onClick={onReset}>↻ Extract another</button>
      </div>

      <div className="stat-grid">
        <Stat label="Vendor" value={inv.vendor} />
        <Stat label="Invoice #" value={inv.invoice_number} />
        <Stat label="Date" value={inv.date} />
        <Stat label="Total" value={inv.total + " " + inv.currency} />
      </div>

      <div className="card table-card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Description</th>
                <th className="r">Qty</th>
                <th className="r">Unit price</th>
                <th className="r">Amount</th>
              </tr>
            </thead>
            <tbody>
              {inv.line_items.map((it, i) => (
                <tr key={i}>
                  <td>{it.description}</td>
                  <td className="r num">{it.quantity}</td>
                  <td className="r num">{it.unit_price}</td>
                  <td className="r num" style={{ fontWeight: 500 }}>{it.amount}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={3}>Total</td>
                <td className="r num">{inv.total} {inv.currency}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <div className="row">
        <button className="btn btn-primary" onClick={copy}>{copied ? "Copied!" : "Copy JSON"}</button>
        <button className="btn btn-secondary" onClick={download}>Download JSON</button>
        <button className="btn btn-ghost" onClick={() => setShowJson(!showJson)}>
          {showJson ? "Hide raw JSON" : "Show raw JSON"}
        </button>
      </div>

      {showJson && <pre className="json fade-in">{jsonStr}</pre>}
    </div>
  );
}

function App() {
  const [status, setStatus] = useState("idle");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [filename, setFilename] = useState("");

  const reset = () => { setStatus("idle"); setData(null); setError(null); setFilename(""); };

  const handleFile = useCallback(async (file) => {
    setFilename(file.name);
    setStatus("loading");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/extract", { method: "POST", body: form });
      const json = await res.json();
      if (json.ok) { setData(json); setStatus("done"); }
      else { setError(json); setStatus("error"); }
    } catch (e) {
      setError({ error_type: "network", hint: "Couldn't reach the server.", message: String(e) });
      setStatus("error");
    }
  }, []);

  return (
    <div>
      <Header />
      <main className="container stack">
        {status === "idle" && <Dropzone onFile={handleFile} />}
        {status === "loading" && <Spinner filename={filename} />}
        {status === "error" && <ErrorCard error={error} onReset={reset} />}
        {status === "done" && <Result data={data} onReset={reset} />}
        <p className="foot">Parsing runs entirely on your machine — no external API, no token cost.</p>
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
