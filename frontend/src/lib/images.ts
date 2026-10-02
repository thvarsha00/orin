export const IMAGE_ACCEPT = "image/jpeg,image/png,image/webp";
export const DEFAULT_MAX_IMAGE_MB = 4;   // used until the server reports its own MAX_IMAGE_MB

const OK_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const OK_EXT = /\.(jpe?g|png|webp)$/i;

export function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Returns a student-friendly problem description, or null when the file can be attached. */
export function validateImage(file: File, maxMb: number): string | null {
  const typeOk = OK_TYPES.has(file.type) || (!file.type && OK_EXT.test(file.name));
  if (!typeOk) return "Unsupported file. Please upload a JPG, PNG or WEBP image.";
  if (file.size === 0) return "That image file is empty. Please choose another one.";
  if (file.size > maxMb * 1024 * 1024) return `That image is too large. The limit is ${Number(maxMb.toFixed(1))} MB.`;
  return null;
}
