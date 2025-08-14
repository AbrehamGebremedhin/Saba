"""
Chat Service for handling conversation logic and command processing.
This service manages the conversation flow, processes user input, and generates responses.
"""
import sys
import asyncio
from services.speech_service import AsyncSpeechService
from services.llm_service import AsyncLLMService, LLMConfig
from tools.agents import AsyncAgentExecutor

class ChatService:
    """
    Service class for handling chat conversations and command processing.
    Separates the conversation logic from UI management.
    """
    
    def __init__(self):
        self.speech_service = AsyncSpeechService()
        self.conversation_history = []
        self.is_active = False
        self.llm_service = AsyncLLMService()
        self.agent_executor = AsyncAgentExecutor(
            llm=self.llm_service._llm,
            verbose=False
        )

    async def initialize(self):
        """Initialize the chat service."""
        print("Chat service initialized")
        
    async def get_welcome_message(self) -> str:
        """Get the welcome message for when the application starts."""
        return "Hello! I'm Saba, your personal assistant. How can I help you today?"
        
    async def process_user_input(self, user_text: str) -> str:
        """
        Process user input and generate a response.
        
        Args:
            user_text (str): The user's spoken input
            
        Returns:
            str: The response text to be synthesized
        """
        if not user_text:
            return None
            
        print(f"Processing user input: {user_text}")
        
        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": user_text})
        
        # Process the command/input
        response = await self._generate_response(user_text)
        
        # Add response to conversation history
        if response:
            # Clean the response before adding to history and returning
            response = self._clean_response(response)
            self.conversation_history.append({"role": "assistant", "content": response})
            
        return response
        
    def _clean_response(self, response: str) -> str:
        """
        Clean the response by removing internal reasoning artifacts.
        
        Args:
            response (str): The raw response from the LLM
            
        Returns:
            str: The cleaned response
        """
        if not response:
            return response
            
        # Split into lines and filter out internal reasoning
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip lines that contain internal reasoning artifacts
            if (line.startswith('**Risk:**') or 
                line.startswith('**Next Step:**') or
                line.startswith('Risk:') or
                line.startswith('Next Step:') or
                'Risk:' in line and ('None detected' in line or 'Low' in line or 'Medium' in line or 'High' in line) or
                'Next Step:' in line and ('Please' in line or 'Suggest' in line or 'provide' in line.lower())):
                continue
            if line:  # Only add non-empty lines
                cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines).strip()
        
    async def _generate_response(self, user_text: str) -> str:
        """
        Generate a response based on user input.
        This is where you can add command processing, AI integration, etc.
        
        Args:
            user_text (str): The user's input text
            
        Returns:
            str: The response text
        """
        user_text_lower = user_text.lower()
        
        # Simple command processing - you can expand this
        if "hello" in user_text_lower or "hi" in user_text_lower:
            # Await the coroutine so we return a string, not a coroutine object
            response = await self.llm_service.acomplete(user_text)
            return self._clean_response(response)
            
        elif "time" in user_text_lower:
            import datetime
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current time is {current_time}"
            
        elif "goodbye" in user_text_lower or "bye" in user_text_lower:
            response = await self.llm_service.acomplete(user_text)
            sys.exit(self._clean_response(response))
        else:
            # Default response for unrecognized input
            agent_response = await self.agent_executor.ainvoke(user_text)
            return self._clean_response(agent_response)

    async def synthesize_response(self, response_text: str, output_file: str = "output.wav"):
        """
        Synthesize the response text to speech.
        
        Args:
            response_text (str): The text to synthesize
            output_file (str): The output audio file name
        """
        if not response_text:
            return
            
        try:
            await self.speech_service.synthesize(response_text, output_prefix="response")
            print(f"Response synthesized: {response_text}")
        except Exception as e:
            print(f"Error synthesizing response: {e}")
            
    def get_conversation_history(self) -> list:
        """Get the conversation history."""
        return self.conversation_history.copy()
        
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
        print("Conversation history cleared")
        
    def start_conversation(self):
        """Mark the conversation as active."""
        self.is_active = True
        print("Conversation started")
        
    def stop_conversation(self):
        """Mark the conversation as inactive."""
        self.is_active = False
        print("Conversation stopped")
