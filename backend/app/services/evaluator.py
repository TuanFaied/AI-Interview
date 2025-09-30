import os
import json
from crewai import Agent, Crew, Task,LLM
import google.generativeai as genai
from sqlmodel import Session, select

from ..models import InterviewSession, QAItem, Message, Evaluation

os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
# Initialize Gemini LLM
llm = LLM(model="gemini/gemini-2.0-flash",temperature=1.0)

class EvaluationAgent:
    def __init__(self):
        self.agent = Agent(
            role="Interview Evaluation Specialist",
            goal="Evaluate interview transcripts and provide comprehensive scoring and feedback",
            backstory="""You are an expert at analyzing interview performance, with deep knowledge 
            of hiring practices across various industries. You can accurately assess technical knowledge, 
            communication skills, confidence levels, and provide constructive feedback that helps 
            candidates understand their strengths and areas for improvement.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )
    

    def create_evaluation_task(self, qas: list[dict], role: str, difficulty: str, domain: str) -> Task:
        return Task(
            description=f"""Evaluate this interview for a {role} position at {difficulty} level.
            Domain: {domain or "Not specified"}
            
            Here are the Q&A pairs:
            {json.dumps(qas, indent=2)}
            
            Provide a comprehensive evaluation with:
            1. Technical knowledge score (0-100)
            2. Communication skills score (0-100)
            3. Confidence level score (0-100)
            4. Key strengths demonstrated
            5. Overall summary of performance
            6. Rubric or detailed breakdown of evaluation criteria
            
            Format your response as valid JSON with these exact keys:
            technical, communication, confidence, strengths, summary, rubric""",
            agent=self.agent,
            expected_output="A valid JSON object with evaluation results",
            async_execution=False
        )

def build_qas(session_id: str, db: Session) -> list[dict]:
        qas = db.exec(
            select(QAItem).where(QAItem.session_id == session_id).order_by(QAItem.order_idx)
        ).all()
        msgs = db.exec(
            select(Message).where(Message.session_id == session_id, Message.who == "candidate").order_by(Message.ts)
        ).all()

        # Pair questions with candidate answers in order
        qas_structured = []
        for idx, q in enumerate(qas):
            candidate_answer = msgs[idx].text if idx < len(msgs) else None
            qas_structured.append({
                "question": q.question,
                "ideal_answer": q.ideal_answer,
                "candidate_answer": candidate_answer
            })
        return qas_structured

def evaluate_transcript(session_id: str, role: str, difficulty: str, domain: str|None,db:Session) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # fallback naive heuristic if no key provided
        import random
        return {
            "technical": random.randint(55,85),
            "communication": random.randint(55,85),
            "confidence": random.randint(55,85),
            "strengths": "Shows good grasp of fundamentals; answers structured.",
            "summary": "Overall competent performance with room for deeper examples.",
            "rubric": json.dumps({"note":"heuristic"})
        }

    qas_structured = build_qas(session_id, db)
    # Create the evaluation agent and task
    evaluation_agent = EvaluationAgent()
    task = evaluation_agent.create_evaluation_task(qas_structured, role, difficulty, domain)
    
    try:
        # Execute the evaluation task
        crew = Crew(
            agents=[evaluation_agent.agent],
            tasks=[task],
            verbose=True
        )
        result = crew.kickoff()
        text = str(result)
        
        # Clean the response (remove markdown code blocks if present)
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse the JSON response
        evaluation_data = json.loads(text)
         # Convert lists to strings for database storage
        if isinstance(evaluation_data.get("strengths"), list):
            evaluation_data["strengths"] = ", ".join(evaluation_data["strengths"])
        
        if isinstance(evaluation_data.get("rubric"), (dict, list)):
            evaluation_data["rubric"] = json.dumps(evaluation_data["rubric"])
        
        # Ensure all required fields are present
        required_fields = ["technical", "communication", "confidence", "strengths", "summary", "rubric"]
        for field in required_fields:
            if field not in evaluation_data:
                raise ValueError(f"Missing required field: {field}")
                
        return evaluation_data
        
    except Exception as e:
        print(f"Error in evaluation: {e}")
        # Fallback evaluation
        return {
            "technical": 70, 
            "communication": 70, 
            "confidence": 70,
            "strengths": "Clear communication and good foundational knowledge.",
            "summary": "Solid overall performance with potential for growth in specific areas.",
            "rubric": json.dumps({
                "technical": "Assessed based on relevance and depth of technical responses",
                "communication": "Evaluated clarity, structure, and effectiveness of communication",
                "confidence": "Measured by assertiveness and conviction in responses",
                "note": "fallback evaluation due to processing error"
            })
        }