import { createContext, useCallback, useContext, useMemo, useState } from "react";

const ToastContext = createContext(null);

function Toast({ toast }) {
  return (
    <div className={`toast ${toast.type || "success"}`} role="status">
      <span className="toast-icon">{toast.type === "error" ? "!" : "✓"}</span>
      <span>{toast.message}</span>
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const push = useCallback((message, type = "success", duration = 2600) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), duration);
  }, []);

  const value = useMemo(
    () => ({
      show: (msg, type) => push(msg, type || "success"),
      success: (msg) => push(msg, "success"),
      error: (msg) => push(msg, "error"),
    }),
    [push]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-stack">
        {toasts.map((t) => (
          <Toast key={t.id} toast={t} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}