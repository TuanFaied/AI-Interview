"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

// Add type definitions for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export default function AudioStreamer({ wsUrl, sessionId }: { wsUrl: string; sessionId: string }) {
  const router = useRouter();
  const wsRef = useRef<WebSocket | null>(null);
  const [transcripts, setTranscripts] = useState<string[]>([]);
  const [status, setStatus] = useState<string>("connecting");
  const [remaining, setRemaining] = useState<number>(15 * 60);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const maxConnectionAttempts = 3;
  const [debugInfo, setDebugInfo] = useState<string[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [spaceBarPrompt, setSpaceBarPrompt] = useState(false);
  const [currentAnswer, setCurrentAnswer] = useState<string>("");

  const addDebugInfo = (message: string) => {
    console.log(message);
    setDebugInfo(prev => [...prev.slice(-20), `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const connectWebSocket = () => {
    try {
      if (connectionAttempts >= maxConnectionAttempts) {
        setStatus("connection_failed");
        return;
      }

      setStatus("connecting");
      addDebugInfo("Connecting to WebSocket...");
      
      if (wsRef.current) wsRef.current.close();
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        addDebugInfo("WebSocket connection opened");
        setStatus("live");
        setConnectionAttempts(0);
        initializeSpeechRecognition();
      };

      wsRef.current.onclose = (event) => {
        addDebugInfo(`WebSocket connection closed: ${event.code} - ${event.reason}`);
        setStatus("closed");
        stopSpeechRecognition();
      };

      wsRef.current.onerror = (error) => {
        addDebugInfo("WebSocket error occurred");
        console.error("WebSocket error:", error);
        setStatus("error");
      };

      wsRef.current.onmessage = (ev) => {
        if (typeof ev.data === "string") {
          const msg = JSON.parse(ev.data);
          addDebugInfo(`Received message: ${msg.type}`);

          if (msg.type === "transcript") {
            const newTranscript = `${msg.data.who.toUpperCase()}: ${msg.data.text}`;
            setTranscripts((t) => [...t, newTranscript]);
          } else if (msg.type === "interviewer_text") {
            const newTranscript = `INTERVIEWER: ${msg.data.text}`;
            setTranscripts((t) => [...t, newTranscript]);
            setCurrentQuestion(msg.data.text);
            setIsListening(false);
            setSpaceBarPrompt(false);
          } else if (msg.type === "interviewer_audio") {
            handleAudioPlayback(msg.data.url);
          } else if (msg.type === "timer") {
            setRemaining(msg.data.remaining);
          } else if (msg.type === "status") {
            setStatus(msg.data.message || "closed");
            if (["Interview completed", "finished"].includes(msg.data.message)) {
              stopSpeechRecognition();
              addDebugInfo("Interview finished, redirecting to results page...");
              setTimeout(() => {
                router.push(`/results/${sessionId}`);
              }, 1500);
            }
          }
        }
      };
    } catch (error) {
      addDebugInfo(`Error creating WebSocket: ${error}`);
      console.error("Error creating WebSocket:", error);
      setStatus("error");
    }
  };

  const initializeSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      addDebugInfo("SpeechRecognition API not supported in this browser");
      setStatus("error");
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = "en-US";

    recognitionRef.current.onstart = () => {
      setIsRecording(true);
      addDebugInfo("Speech recognition started");
    };
    
    recognitionRef.current.onend = () => {
      setIsRecording(false);
      addDebugInfo("Speech recognition ended");
    };
    
    recognitionRef.current.onerror = (event: any) => {
      addDebugInfo(`Speech recognition error: ${event.error}`);
    };

    recognitionRef.current.onresult = (event: any) => {
      let interim = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          setCurrentAnswer(prev => (prev + " " + transcript).trim());
        } else {
          interim += transcript + " ";
        }
      }

      setInterimTranscript(interim.trim());
    };
  };

  const startSpeechRecognition = () => {
    if (!recognitionRef.current) return;

    if (isRecording) {
      addDebugInfo("Speech recognition already running, skipping start()");
      return;
    }

    try {
      recognitionRef.current.start();
      setIsListening(true);
      addDebugInfo("Started speech recognition");
    } catch (error) {
      console.error("Error starting speech recognition:", error);
      addDebugInfo(`Error starting speech recognition: ${error}`);
    }
  };


  const stopSpeechRecognition = () => {
    if (recognitionRef.current && isRecording) {
      try {
        recognitionRef.current.stop();
        setIsListening(false);
        addDebugInfo("Stopped speech recognition");
      } catch (error) {
        console.error("Error stopping speech recognition:", error);
        addDebugInfo(`Error stopping speech recognition: ${error}`);
      }
    }
  };

  const handleAudioPlayback = (url: string) => {
    setIsListening(false);
    setSpaceBarPrompt(false);
    
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
    }
    
    if (!audioRef.current) {
      audioRef.current = new Audio();
      audioRef.current.onended = () => {
        addDebugInfo("Interviewer audio ended, enabling listening");
        if (!isRecording) {
          startSpeechRecognition();
        }
        setSpaceBarPrompt(true);
      };

    }
    
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    audioRef.current.src = url;
    audioRef.current.play().catch((error) => {
      addDebugInfo(`Audio playback error: ${error}`);
      setTimeout(() => {
        startSpeechRecognition();
        setSpaceBarPrompt(true);
      }, 1000);
    });
  };

  const handleSpaceBarPress = () => {
    if (isListening) {
      if (currentAnswer.trim() && wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: "candidate_text",
          data: { text: currentAnswer.trim() }
        }));
        addDebugInfo(`Sent candidate response: ${currentAnswer.trim()}`);
      }

      stopSpeechRecognition();
      setInterimTranscript("");
      setCurrentAnswer("");
      setSpaceBarPrompt(false);
    }
  };

  const handleFinishInterview = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "control",
        data: { action: "stop" }
      }));
      addDebugInfo("Sent finish interview request");
    } else {
      // If WebSocket is not available, redirect directly
      router.push(`/results/${sessionId}`);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && isListening) {
        e.preventDefault();
        handleSpaceBarPress();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isListening, currentAnswer]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      stopSpeechRecognition();
    };
  }, [wsUrl]);

  return (
    <div className="space-y-4 p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-center">Live Interview</h1>
      
      <div className="text-sm bg-gray-100 p-2 rounded">
        Status: <b>{status}</b> · Time left: {Math.floor(remaining / 60)}:
        {String(remaining % 60).padStart(2, "0")}
        {isListening && <span className="ml-2 text-red-500">● Listening</span>}
      </div>

      <div className="bg-white border rounded p-4 h-80 overflow-auto">
        <div className="text-sm whitespace-pre-wrap">
          {transcripts.map((t, i) => (
            <div key={i} className="mb-2">{t}</div>
          ))}
          {currentAnswer && (
            <div className="mb-2 text-gray-800">
              CANDIDATE (answer): {currentAnswer}
            </div>
          )}
          {interimTranscript && (
            <div className="mb-2 text-gray-500 italic">
              (in progress): {interimTranscript}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-4 h-4 rounded-full ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-300'}`}></div>
          <span className="text-sm">
            {isRecording ? "Recording audio" : "Not recording"}
          </span>
        </div>

        <div className="flex gap-2">
          {spaceBarPrompt && (
            <div className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded text-sm">
              Press Spacebar when finished speaking
            </div>
          )}
          
          <button
            onClick={handleFinishInterview}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
          >
            Finish Interview
          </button>
        </div>
      </div>

      {status === "error" && (
        <div className="bg-red-100 border border-red-200 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Connection Error</p>
          <p>There was a problem connecting to the interview server. Please try again.</p>
        </div>
      )}

      {/* Debug information panel (can be hidden in production) */}
      <details className="bg-gray-100 p-2 rounded text-xs">
        <summary className="cursor-pointer">Debug Information</summary>
        <div className="mt-2 max-h-40 overflow-auto">
          {debugInfo.map((info, i) => (
            <div key={i}>{info}</div>
          ))}
        </div>
      </details>
    </div>
  );
}