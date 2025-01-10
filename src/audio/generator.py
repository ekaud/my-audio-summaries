import io
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Literal

from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from promptic import llm
from tenacity import retry, retry_if_exception_type

# Load environment variables
load_dotenv()

# Check for required API keys
if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("Gemini API key not found. Please set GEMINI_API_KEY in .env file")
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")


class DialogueItem(BaseModel):
    """Represents a single line of dialogue with speaker and text"""
    text: str
    speaker: Literal["female-1", "male-1", "female-2"]

    @property
    def voice(self) -> str:
        """Map speaker to OpenAI voice"""
        return {
            "female-1": "alloy",
            "male-1": "onyx",
            "female-2": "shimmer",
        }[self.speaker]

class Dialogue(BaseModel):
    """Complete dialogue structure with planning and lines"""
    scratchpad: str
    dialogue: List[DialogueItem]

def get_mp3(text: str, voice: str, api_key: str = None) -> bytes:
    """Generate MP3 audio from text using OpenAI's text-to-speech"""
    client = OpenAI(
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
    )

    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=voice,
        input=text,
    ) as response:
        with io.BytesIO() as file:
            for chunk in response.iter_bytes():
                file.write(chunk)
            return file.getvalue()

@retry(retry=retry_if_exception_type(ValidationError))
@llm(model="gemini/gemini-1.5-flash-002", api_key=os.getenv("GEMINI_API_KEY"))
def generate_dialogue(text: str) -> Dialogue:
    """
    Your task is to take the input text provided and turn it into an engaging, informative podcast dialogue. 
    The input text may be messy or unstructured, as it could come from a variety of sources like PDFs or web pages. 
    Don't worry about the formatting issues or any irrelevant information; 
    your goal is to extract the key points and interesting facts that could be discussed in a podcast.

    Here is the input text you will be working with:

    <input_text>
    {text}
    </input_text>

    First, carefully read through the input text and identify the main topics, key points, and any interesting facts or anecdotes. 
    Think about how you could present this information in a fun, engaging way that would be suitable for an audio podcast.

    <scratchpad>
    Brainstorm creative ways to discuss the main topics and key points you identified in the input text. 
    Consider using analogies, storytelling techniques, or hypothetical scenarios to make the content more relatable and engaging for listeners.

    Keep in mind that your podcast should be accessible to a general audience, so avoid using too much jargon or assuming prior knowledge of the topic. 
    If necessary, think of ways to briefly explain any complex concepts in simple terms.

    Use your imagination to fill in any gaps in the input text or to come up with thought-provoking questions that could be explored in the podcast. 
    The goal is to create an informative and entertaining dialogue, so feel free to be creative in your approach.

    Write your brainstorming ideas and a rough outline for the podcast dialogue here. 
    Be sure to note the key insights and takeaways you want to reiterate at the end.
    </scratchpad>

    Now that you have brainstormed ideas and created a rough outline, it's time to write the actual podcast dialogue. 
    Aim for a natural, conversational flow between the host and any guest speakers. 
    Incorporate the best ideas from your brainstorming session and make sure to explain any complex topics in an easy-to-understand way.

    <podcast_dialogue>
    Write your engaging, informative podcast dialogue here, based on the key points and creative ideas you came up with during the brainstorming session. 
    Use a conversational tone and include any necessary context or explanations to make the content accessible to a general audience. 
    Use made-up names for the hosts and guests to create a more engaging and immersive experience for listeners. 
    Do not include any bracketed placeholders like [Host] or [Guest]. Design your output to be read aloud -- it will be directly converted into audio.

    Make the dialogue as long and detailed as possible, while still staying on topic and maintaining an engaging flow. 
    Aim to use your full output capacity to create the longest podcast episode you can, while still communicating the key information from the input text in an entertaining way.

    At the end of the dialogue, have the host and guest speakers naturally summarize the main insights and takeaways from their discussion. 
    This should flow organically from the conversation, reiterating the key points in a casual, conversational manner. 
    Avoid making it sound like an obvious recap - the goal is to reinforce the central ideas one last time before signing off.
    </podcast_dialogue>
    """

async def generate_audio_summary(doc) -> tuple[bytes, str]:
    """
    Generate an audio summary from a document.
    
    Args:
        doc: Document object with extracted_text
        
    Returns:
        tuple: (audio_bytes, transcript)
        
    Raises:
        ValueError: If document has no extracted text
        RuntimeError: If audio generation fails
    """
    if not doc.extracted_text:
        raise ValueError(f"Document {doc.title} has no extracted text")
    
    try:
        # Generate dialogue from text
        llm_output = generate_dialogue(doc.extracted_text)
        
        audio = b""
        transcript = ""
        characters = 0

        # Generate audio for each line of dialogue concurrently
        with ThreadPoolExecutor() as executor:
            futures = []
            for line in llm_output.dialogue:
                transcript_line = f"{line.speaker}: {line.text}"
                future = executor.submit(get_mp3, line.text, line.voice)
                futures.append((future, transcript_line))
                characters += len(line.text)

            # Collect results
            for future, transcript_line in futures:
                audio_chunk = future.result()
                audio += audio_chunk
                transcript += transcript_line + "\n\n"

        logger.info(f"Generated {characters} characters of audio for {doc.title}")
        return audio, transcript
        
    except Exception as e:
        logger.error(f"Failed to generate audio for {doc.title}: {str(e)}")
        raise RuntimeError(f"Audio generation failed: {str(e)}") 