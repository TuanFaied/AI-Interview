from crewai import LLM, Agent
import os

INTRO_TEMPLATE = (
    "Hello! I'm your AI interviewer. We'll have a short 15-minute audio interview. "
    "I'll start with a quick intro from you, then a few targeted questions with possible follow-ups. Ready?"
)
# Set your Gemini API key
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Initialize Gemini LLM
llm = LLM(model="gemini/gemini-2.0-flash",temperature=0.7)
class InterviewBrain:
    def __init__(self, role: str, difficulty: str, domain: str|None, qas: list[dict]):
        self.role = role
        self.difficulty = difficulty
        self.domain = domain
        self.qas = qas
        self.current_question_index = -1
        self.agent = Agent(
            name="InterviewAgent", 
            role="Interviewer", 
            goal="Conduct live interview",
            backstory=f"Hiring for {role} ({difficulty}) domain={domain}",
            llm=llm
        )
        self.opened = False
        self.last_user_response = None
        self.asked_questions = set()

    def next_prompt(self, user_response: str|None = None) -> str:
        self.last_user_response = user_response
        self.opened = True
        # if not self.opened:
        #     self.opened = True
        #     return "Hello! I'm your AI interviewer. We'll have a short 15-minute audio interview. I'll start with a quick intro from you, then a few targeted questions with possible follow-ups. Ready?\nCould you please introduce yourself briefly?"
        
        # If we have a user response, decide whether to ask a follow-up or move to next question
        if user_response and len(user_response.split()) > 3:  # Only follow up if response has some substance
            # Check if we should ask a follow-up based on response quality
            if len(user_response.split()) < 10:  # Short response might need follow-up
                return "Could you elaborate more on that? Please provide a specific example."
            else:
                # Response is substantial, move to next question
                self.current_question_index += 1
        else:
            # No valid response, just move to next question
            self.current_question_index += 1        
        
        if self.current_question_index < len(self.qas):
            next_question = self.qas[self.current_question_index]["question"]
            # Make sure we don't repeat questions
            if next_question not in self.asked_questions:
                self.asked_questions.add(next_question)
                return next_question
        
        # End of questions
        return "Thank you for your answers. That concludes our interview. Do you have any questions for me?"