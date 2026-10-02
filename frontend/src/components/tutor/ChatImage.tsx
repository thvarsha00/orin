import { useEffect, useState } from "react";
import { ImageOff } from "lucide-react";
import { fetchMessageImage } from "../../services/api";
import { ImageLightbox } from "./ImageLightbox";

interface Props {
  src?: string;          // local preview (message sent in this session)
  messageId?: number;    // saved message: image is loaded from the server
  onLoad?: () => void;
}

/** Image inside a chat bubble: keeps its aspect ratio, rounded, click to enlarge. Never shows raw URLs/base64. */
export function ChatImage({ src, messageId, onLoad }: Props) {
  const [url, setUrl] = useState<string | undefined>(src);
  const [failed, setFailed] = useState(false);
  const [zoom, setZoom] = useState(false);

  useEffect(() => {
    setFailed(false);
    if (src) { setUrl(src); return; }
    if (messageId == null) return;
    let alive = true;
    setUrl(undefined);
    fetchMessageImage(messageId).then((u) => alive && setUrl(u)).catch(() => alive && setFailed(true));
    return () => { alive = false; };
  }, [src, messageId]);

  if (failed) {
    return (
      <div className="flex h-24 w-44 flex-col items-center justify-center gap-1 rounded-2xl border border-line bg-white/[0.03] text-xs text-slate-500">
        <ImageOff size={18} /> Image unavailable
      </div>
    );
  }
  if (!url) return <div className="h-40 w-56 max-w-full animate-pulse rounded-2xl bg-white/5" aria-label="Loading image" />;
  return (
    <>
      <button type="button" onClick={() => setZoom(true)} aria-label="View image larger"
        className="block overflow-hidden rounded-2xl border border-line transition hover:border-accent/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">
        <img src={url} alt="Image attached by the student" onLoad={onLoad} onError={() => setFailed(true)}
          className="block h-auto max-h-72 w-auto max-w-full object-contain" />
      </button>
      {zoom && <ImageLightbox src={url} onClose={() => setZoom(false)} />}
    </>
  );
}
