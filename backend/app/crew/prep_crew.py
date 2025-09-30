import os
import json
from crewai import Agent, Crew, Task, LLM
import google.generativeai as genai

# # Configure Gemini
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Set your Gemini API key
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Initialize Gemini LLM
llm = LLM(model="gemini/gemini-2.0-flash",temperature=1.0)
class QuestionPreparationAgent:
    def __init__(self):
        self.agent = Agent(
            role="Question Preparation Specialist",
            goal="Generate relevant interview questions based on role, difficulty, domain, and job description",
            backstory="""You are an expert at creating targeted interview questions that assess 
            candidates' skills, experience, and cultural fit for specific roles. You understand
            how to tailor questions to different seniority levels and industry domains.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def create_task(self, role: str, difficulty: str, domain: str, jd: str) -> Task:
        return Task(
            description=f"""Generate 6-10 interview questions for a {role} position at {difficulty} level.
            Domain: {domain}
            Job Description: {jd}
            
            Create questions that assess:
            1. Technical skills relevant to the role
            2. Behavioral and situational responses
            3. Problem-solving abilities
            4. Cultural fit and motivation
            
            For each question, provide an ideal answer that demonstrates what a strong response would include.
            Format the output as a JSON list with objects containing 'question' and 'ideal_answer' keys.""",
            agent=self.agent,
            expected_output="A JSON list of objects with 'question' and 'ideal_answer' keys",
            async_execution=False
        )

def run_prep(role: str, difficulty: str, domain: str, jd: str) -> list[dict]:
    # Create the agent and task
    prep_agent = QuestionPreparationAgent()
    task = prep_agent.create_task(role, difficulty, domain, jd)
    

    # Execute the task
    try:
        crew = Crew(
            agents=[prep_agent.agent],
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
        return json.loads(text)
        
    except Exception as e:
        print(f"Error in question preparation: {e}")
        # Fallback questions
        return [
            {
                "question": "Tell me about yourself and your experience relevant to this role.",
                "ideal_answer": "A concise summary of professional background, highlighting key experiences and achievements that align with the role requirements."
            },
            {
                "question": "What motivated you to apply for this position?",
                "ideal_answer": "A response that shows understanding of the company/role and connects personal goals with the opportunity."
            },
            {
                "question": "Describe a challenging project you worked on and how you approached it.",
                "ideal_answer": "A specific example that demonstrates problem-solving skills, technical expertise, and collaboration (if applicable)."
            },
            {
                "question": "How do you stay updated with the latest developments in your field?",
                "ideal_answer": "Discussion of specific resources, communities, courses, or practices used for continuous learning."
            },
            {
                "question": "Where do you see yourself in 3-5 years?",
                "ideal_answer": "A response that shows ambition and growth mindset while aligning with potential career paths at the company."
            }
        ]