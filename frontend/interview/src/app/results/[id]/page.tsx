"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

interface Message {
  id: number;
  session_id: string;
  who: string;
  text: string;
  ts: string;
}

interface QAItem {
  id: number;
  session_id: string;
  question: string;
  ideal_answer: string;
  order_idx: number;
  ts: string;
}

interface Evaluation {
  technical: number;
  communication: number;
  confidence: number;
  strengths: string;
  summary: string;
  rubric?: string;
}

interface QAPair {
  question: Message;
  answers: Message[];
  expectedAnswer: string;
  questionNumber: number;
}

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [questions, setQuestions] = useState<QAItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"evaluation" | "qa">("evaluation");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch evaluation results
        const evalResponse = await fetch(`http://localhost:8000/results/${params.id}`);
        if (evalResponse.ok) {
          const evalData = await evalResponse.json();
          setEvaluation(evalData);
        }
        
        // Fetch interview messages/transcript
        const messagesResponse = await fetch(`http://localhost:8000/sessions/${params.id}/messages`);
        if (messagesResponse.ok) {
          const messagesData = await messagesResponse.json();
          setMessages(messagesData);
        }
        
        // Fetch prepared questions
        const questionsResponse = await fetch(`http://localhost:8000/sessions/${params.id}/questions`);
        if (questionsResponse.ok) {
          const questionsData = await questionsResponse.json();
          setQuestions(questionsData);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    if (params?.id) {
      fetchData();
    }
  }, [params?.id]);

  // Group messages by question-answer pairs
  const getQAPairs = (): QAPair[] => {
    const pairs: QAPair[] = [];

    // Sort messages by timestamp
    const sortedMessages = [...messages].sort(
      (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime()
    );

    const sortedQuestions = [...questions].sort(
      (a,b)=>  a.order_idx - b.order_idx
    );

    const candidateMessages = sortedMessages.filter(m=>m.who === "candidate");

    for(let i=0; i<sortedQuestions.length; i++) {
      const q = sortedQuestions[i];
      const answer = candidateMessages[i];

      pairs.push({
        question: {
          id: q.id,
          session_id: q.session_id,
          who: "interviewer",
          text: q.question,
          ts: q.ts, 
        },
        answers: answer ? [answer] : [],
        expectedAnswer: q.ideal_answer,
        questionNumber: i + 1,
      });
    }
    return pairs;
    // questions
    //   .sort((a, b) => a.order_idx - b.order_idx)
    //   .forEach((q, index) => {
    //     const nextQuestion = questions[index + 1];

    //     // Candidate answers that fall between this question and the next
    //     const answers = sortedMessages.filter(m => {
    //       if (m.who !== "candidate") return false;

    //       const ts = new Date(m.ts).getTime();
    //       const thisQ = new Date(q.session_id ? q.session_id : 0).getTime(); // dummy fallback

    //       const afterThis = true; // since /messages has no explicit interviewer question ts
    //       const beforeNext = nextQuestion
    //         ? ts < new Date(sortedMessages.find(m => m.text.includes(nextQuestion.question))?.ts || Infinity).getTime()
    //         : true;

    //       return afterThis && beforeNext;
    //     });

    //     pairs.push({
    //       question: {
    //         id: q.id,
    //         session_id: q.session_id,
    //         who: "interviewer",
    //         text: q.question,
    //         ts: new Date().toISOString(), // fake timestamp (since API doesn’t return one)
    //       },
    //       answers,
    //       expectedAnswer: q.ideal_answer,
    //       questionNumber: index + 1,
    //     });
    //   });

    // return pairs;
  };


  const qaPairs = getQAPairs();

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading interview results...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Interview Results</h1>
          <p className="text-gray-600">Session ID: {params.id}</p>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex">
              <button
                className={`flex-1 py-4 px-6 text-center font-medium text-sm ${
                  activeTab === "evaluation"
                    ? "border-b-2 border-blue-500 text-blue-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab("evaluation")}
              >
                Evaluation Summary
              </button>
              <button
                className={`flex-1 py-4 px-6 text-center font-medium text-sm ${
                  activeTab === "qa"
                    ? "border-b-2 border-blue-500 text-blue-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab("qa")}
              >
                Questions & Answers
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === "evaluation" && evaluation && (
              <div className="space-y-6">
                {/* Evaluation Scores */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="text-3xl font-bold text-blue-600">{evaluation.technical}</div>
                      <div className="text-sm text-blue-800 font-medium">Technical Knowledge</div>
                      <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${evaluation.technical}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="text-3xl font-bold text-green-600">{evaluation.communication}</div>
                      <div className="text-sm text-green-800 font-medium">Communication</div>
                      <div className="w-full bg-green-200 rounded-full h-2 mt-2">
                        <div 
                          className="bg-green-600 h-2 rounded-full" 
                          style={{ width: `${evaluation.communication}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <div className="text-3xl font-bold text-yellow-600">{evaluation.confidence}</div>
                      <div className="text-sm text-yellow-800 font-medium">Confidence</div>
                      <div className="w-full bg-yellow-200 rounded-full h-2 mt-2">
                        <div 
                          className="bg-yellow-600 h-2 rounded-full" 
                          style={{ width: `${evaluation.confidence}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Strengths and Summary */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Strengths</h3>
                    <div className="prose prose-sm">
                      <p className="text-gray-700">{evaluation.strengths}</p>
                    </div>
                  </div>
                  
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Overall Summary</h3>
                    <div className="prose prose-sm">
                      <p className="text-gray-700">{evaluation.summary}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "qa" && (
              <div className="space-y-8">
                {qaPairs.map((pair, index) => (
                  <div key={pair.questionNumber} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                    {/* Question Header */}
                    <div className="bg-blue-50 px-6 py-4 border-b border-blue-100">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-medium">
                            {index + 1}
                          </span>
                          <h3 className="text-lg font-semibold text-blue-900">Interviewer's Question</h3>
                        </div>
                        <span className="text-sm text-blue-700">
                          {new Date(pair.question.ts).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                    
                    {/* Question Content */}
                    <div className="p-6">
                      <div className="prose prose-lg max-w-none">
                        <p className="text-gray-800 text-lg leading-relaxed">{pair.question.text}</p>
                      </div>
                    </div>

                    {/* Candidate's Answer */}
                    <div className="border-t border-gray-100">
                      <div className="bg-green-50 px-6 py-3">
                        <h4 className="text-md font-semibold text-green-900">Your Answer</h4>
                      </div>
                      <div className="p-6">
                        {pair.answers.length > 0 ? (
                          pair.answers.map((answer, answerIndex) => (
                            <div key={answerIndex} className="mb-4 last:mb-0">
                              <div className="prose prose-lg max-w-none">
                                <p className="text-gray-700 leading-relaxed">{answer.text}</p>
                              </div>
                              <p className="text-xs text-gray-500 mt-2">
                                Answered at {new Date(answer.ts).toLocaleTimeString()}
                              </p>
                            </div>
                          ))
                        ) : (
                          <div className="text-center py-4">
                            <p className="text-gray-500 italic">No answer provided for this question</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Expected Answer */}
                    {pair.expectedAnswer && (
                      <div className="border-t border-gray-100">
                        <div className="bg-purple-50 px-6 py-3">
                          <h4 className="text-md font-semibold text-purple-900">Expected Answer</h4>
                        </div>
                        <div className="p-6">
                          <div className="prose prose-lg max-w-none">
                            <p className="text-gray-700 leading-relaxed">{pair.expectedAnswer}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {qaPairs.length === 0 && (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">💬</div>
                    <h3 className="text-xl font-semibold text-gray-600 mb-2">No Questions Found</h3>
                    <p className="text-gray-500">The interview transcript doesn't contain any question-answer pairs.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => router.push('/')}
            className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Start New Interview
          </button>
          <button
            onClick={() => window.print()}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Print Results
          </button>
        </div>
      </div>
    </main>
  );
}