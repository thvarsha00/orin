import { useEffect, useRef } from "react";
import { X } from "lucide-react";

export function ImageLightbox({ src, onClose }: { src: string; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/85 p-4" role="dialog" aria-modal="true" aria-label="Image preview"
      onClick={onClose}>
      <button ref={closeRef} onClick={onClose} aria-label="Close image"
        className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-full bg-white/10 text-white transition hover:bg-white/20"><X size={18} /></button>
      <img src={src} alt="Attached image, enlarged" onClick={(e) => e.stopPropagation()}
        className="max-h-[90vh] max-w-[95vw] rounded-xl object-contain shadow-2xl" />
    </div>
  );
}
