"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AudioStreamer from "@/components/AudioStreamer";
import { wsUrl } from "@/lib/ws";

export default function InterviewPage() {
  const params = useParams();
  const [ready, setReady] = useState(false);
  
  useEffect(() => {
    setReady(true);
  }, []);

  if (!params?.id) {
    return <div>Loading...</div>;
  }

  return (
    <main className="mx-auto max-w-3xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Live Interview</h1>
      {ready && <AudioStreamer wsUrl={wsUrl(params.id as string)} />}
      <p className="text-sm text-gray-500">Audio only. Ensure your microphone is enabled.</p>
      <a className="underline" href={`/results/${params.id}`}>View Results</a>
    </main>
  );
}