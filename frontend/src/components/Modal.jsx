// generic modal component — supports default and large sizes
export default function Modal({ open, title, onClose, children, size = "default" }) {
  if (!open) return null;

  const sizeClasses =
    size === "large" ? "w-[90vw] h-[85vh] max-w-none" : "max-w-lg w-[90%]";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={(e) => e.target === e.currentTarget && onClose?.()}
    >
      <div className={`bg-white rounded-2xl shadow-2xl overflow-hidden ${sizeClasses}`} role="document">
        {/* header shown only in default modal */}
        {size !== "large" && (
          <header className="flex items-center justify-between bg-bronze-700 text-white px-5 py-3">
            <h2 id="modal-title" className="font-semibold text-lg tracking-tight">
              {title}
            </h2>
            <button
              onClick={onClose}
              className="text-xl hover:text-bronze-200 transition-colors"
              aria-label="Close"
            >
              ×
            </button>
          </header>
        )}

        {/* content area */}
        <div className="flex-1 h-full w-full">{children}</div>
      </div>
    </div>
  );
}
