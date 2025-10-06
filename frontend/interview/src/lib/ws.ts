export function wsUrl(sessionId: string) {
  const base =  "ws://localhost:8000/ws";
  return `${base}/${sessionId}`;
}