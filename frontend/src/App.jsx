import { useState } from "react";
import { analyzeSales } from "./api";

function App() {
  const [file, setFile] = useState(null);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const selected = event.target.files?.[0];
    if (!selected) {
      setFile(null);
      return;
    }
    const allowed = [".csv", ".xlsx"];
    const isAllowed = allowed.some((ext) =>
      selected.name.toLowerCase().endsWith(ext)
    );
    if (!isAllowed) {
      setError("Only .csv and .xlsx files are allowed.");
      setFile(null);
      return;
    }
    setError("");
    setFile(selected);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    setSummary("");

    if (!file) {
      setError("Please upload a sales file.");
      return;
    }
    if (!email) {
      setError("Please enter a recipient email.");
      return;
    }

    try {
      setLoading(true);
      const data = await analyzeSales(file, email);
      setSummary(data.summary);
      setMessage(data.message || "Summary generated and email sent.");
    } catch (err) {
      const serverMessage =
        err.response?.data?.detail || "Something went wrong. Please try again.";
      setError(serverMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "radial-gradient(circle at top, #f5f7ff 0, #e0e7ff 40%, #eef2ff 100%)",
        padding: "2rem"
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "640px",
          background: "white",
          borderRadius: "18px",
          boxShadow:
            "0 18px 45px rgba(15, 23, 42, 0.16), 0 0 0 1px rgba(148, 163, 184, 0.16)",
          padding: "2.5rem 2.75rem"
        }}
      >
        <h1
          style={{
            fontSize: "1.75rem",
            margin: 0,
            marginBottom: "0.35rem",
            color: "#0f172a"
          }}
        >
          Sales Insight Automator
        </h1>
        <p
          style={{
            margin: 0,
            marginBottom: "1.75rem",
            color: "#64748b",
            fontSize: "0.95rem"
          }}
        >
          Upload your sales CSV or Excel file and receive an AI-generated,
          executive-ready summary directly in your inbox.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "grid", gap: "1.25rem" }}>
          <div>
            <label
              htmlFor="file"
              style={{
                display: "block",
                marginBottom: "0.35rem",
                fontWeight: 600,
                fontSize: "0.9rem",
                color: "#0f172a"
              }}
            >
              Sales file (.csv or .xlsx)
            </label>
            <input
              id="file"
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
              style={{
                width: "100%",
                padding: "0.45rem 0.75rem",
                borderRadius: "0.6rem",
                border: "1px solid #cbd5f5",
                backgroundColor: "#f9fafb"
              }}
            />
          </div>

          <div>
            <label
              htmlFor="email"
              style={{
                display: "block",
                marginBottom: "0.35rem",
                fontWeight: 600,
                fontSize: "0.9rem",
                color: "#0f172a"
              }}
            >
              Recipient email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="vp.sales@example.com"
              style={{
                width: "100%",
                padding: "0.6rem 0.75rem",
                borderRadius: "0.6rem",
                border: "1px solid #cbd5f5",
                backgroundColor: "#f9fafb"
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: "0.5rem",
              padding: "0.7rem 1.4rem",
              borderRadius: "999px",
              border: "none",
              background:
                "linear-gradient(135deg, #4f46e5 0%, #6366f1 40%, #22c55e 100%)",
              color: "white",
              fontWeight: 600,
              fontSize: "0.95rem",
              cursor: loading ? "default" : "pointer",
              opacity: loading ? 0.8 : 1,
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.4rem"
            }}
          >
            {loading ? (
              <>
                <span
                  style={{
                    width: "16px",
                    height: "16px",
                    borderRadius: "999px",
                    border: "2px solid rgba(255,255,255,0.5)",
                    borderTopColor: "white",
                    animation: "spin 0.8s linear infinite"
                  }}
                />
                Analyzing data…
              </>
            ) : (
              "Analyze & Send Summary"
            )}
          </button>
        </form>

        {error && (
          <div
            style={{
              marginTop: "1.5rem",
              padding: "0.9rem 1rem",
              borderRadius: "0.75rem",
              backgroundColor: "#fef2f2",
              color: "#b91c1c",
              fontSize: "0.9rem",
              border: "1px solid #fecaca"
            }}
          >
            {error}
          </div>
        )}

        {message && (
          <div
            style={{
              marginTop: "1.5rem",
              padding: "0.9rem 1rem",
              borderRadius: "0.75rem",
              backgroundColor: "#ecfdf5",
              color: "#166534",
              fontSize: "0.9rem",
              border: "1px solid #bbf7d0"
            }}
          >
            {message}
          </div>
        )}

        {summary && (
          <div
            style={{
              marginTop: "1.25rem",
              padding: "1rem",
              borderRadius: "0.75rem",
              backgroundColor: "#f8fafc",
              border: "1px solid #e2e8f0",
              maxHeight: "260px",
              overflowY: "auto",
              fontSize: "0.9rem",
              whiteSpace: "pre-wrap"
            }}
          >
            <strong style={{ display: "block", marginBottom: "0.4rem" }}>
              Preview of AI summary
            </strong>
            {summary}
          </div>
        )}
      </div>

      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
}

export default App;

