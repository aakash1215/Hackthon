// SHA-256 of the original bytes, computed on the phone before anything is uploaded.
// crypto.subtle needs a secure context (HTTPS), which the hub provides.
export async function sha256Hex(blob) {
  const buf = await blob.arrayBuffer()
  const digest = await crypto.subtle.digest('SHA-256', buf)
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

// 7F3A-9C21-B4: the short code shown to the worker (first 10 hex characters).
export function shortCode(hex, groups = 3) {
  if (!hex) return ''
  const h = hex.toUpperCase()
  const parts = [h.slice(0, 4), h.slice(4, 8), h.slice(8, 10)]
  return parts.slice(0, groups).join('-')
}
