"""General Gap Analysis logic using Azure OpenAI."""
import tiktoken
from .azure_openai_client import AzureOpenAIClient

# Token limits
MAX_TOKENS_FILE_UPLOAD = 70000  # 70k tokens for file uploads
MAX_CHARS_PASTE_MODE = 21000    # 21k chars for pasted text

# Universal system prompt for gap analysis
SYSTEM_PROMPT = """You are a Gap Analysis Agent. Your task is to compare Document A (Source) against Document B (Target) based on a specific analysis objective.

Input Structure:
- "Document A" and "Document B" may each consist of a single text block or multiple files.
- If multiple files are provided, they will be clearly marked with headers like "## File: filename".
- Treat all content within "Document A" collectively as the "Source State".
- Treat all content within "Document B" collectively as the "Target State" (ideal, requirements, or benchmark).

Core Instruction: Your primary operation is to evaluate how well Document A satisfies or aligns with the criteria, themes, and requirements explicitly stated or clearly implied in Document B, as guided by the analysis objective.

Execution Rules:

Evidence & Scope
Use only information explicitly present in Document A and Document B. Never infer, assume, or invent.
If a key term from the analysis objective is absent from both documents, state this as a fundamental limitation before proceeding.

Gap Classification Logic
For each relevant criterion derived from Document B and the analysis objective, apply this decision tree:
Fully Addressed: Document A contains a direct, complete, and unambiguous match to the criterion from Document B.
Partially Addressed: Document A addresses the criterion but is missing one of these elements: specificity, measurable detail, concrete examples, or a clear process outlined in Document B.
Not Addressed (Gap): The criterion from Document B is not mentioned or supported by any evidence in Document A.
Conflict / Misalignment: Document A directly contradicts a stated requirement or fact in Document B.

Severity Determination Rules
Assign severity only by evaluating the gap's impact on the analysis objective using these anchors:
High: A core, non-negotiable requirement from Document B is missing or contradicted in Document A, making the core objective unachievable.
Medium: An important supporting element is missing or weak, reducing effectiveness or increasing risk for the objective.
Low: The absence or weakness is in a minor, supplementary, or nice-to-have element.
Unspecified: Only use this if the objective provides no context for judging importance (e.g., "list differences").

Recommendation Constraints
Every recommendation must be a direct, logical bridge from the "Evidence" cited to the "Status" assigned.
Recommendations must be actionable on Document A (e.g., "Add a section to Document A that...", "Modify Document A's wording to explicitly state...").
Forbidden: Introducing solutions that require new, unstated resources, goals, or fundamental changes to Document B's stated requirements.

Communication Protocol
Present your analysis in a logical, readable flow suitable for an expert.
Show your work implicitly: Structure your response so that the link between your cited evidence, your classification, and your recommendation is self-evident.
Omit meta-commentary (e.g., "Now I will analyze...").
Operate strictly within these rules and the provided text."""


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: Text to count tokens for
        model: Model name for encoding (default: gpt-4)
        
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for newer models
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def validate_inputs(
    docA: str, 
    docB: str, 
    analysis_objective: str, 
    source: str = "paste"
) -> tuple[bool, str]:
    """
    Validate inputs before analysis.
    
    Args:
        docA: Document A text
        docB: Document B text
        analysis_objective: User's analysis objective
        source: Input source - "paste" for UI text input, "file" for file uploads
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not docA or not docA.strip():
        return False, "Document A is required. Please provide the source/current document."
    
    if not docB or not docB.strip():
        return False, "Document B is required. Please provide the target/ideal/guardrails document."
    
    if not analysis_objective or not analysis_objective.strip():
        return False, "Analysis objective is required. Please describe what to analyze for."
    
    if len(docA.strip()) < 20:
        return False, "Document A seems too short. Please provide a complete document."
    
    if len(docB.strip()) < 20:
        return False, "Document B seems too short. Please provide a complete document."
    
    if len(analysis_objective.strip()) < 5:
        return False, "Analysis objective is too short. Please provide a meaningful objective."
    
    # Source-specific validation
    if source == "paste":
        # Pasted text mode: Use character limit (enforced by UI as well)
        total_length = len(docA) + len(docB) + len(analysis_objective)
        if total_length > MAX_CHARS_PASTE_MODE:
            return False, f"Input too long ({total_length:,} chars). Please shorten to under {MAX_CHARS_PASTE_MODE:,} characters total."
    else:
        # File upload mode: Use token limit
        combined_text = f"{docA}\n\n{docB}\n\n{analysis_objective}"
        token_count = count_tokens(combined_text)
        if token_count > MAX_TOKENS_FILE_UPLOAD:
            return False, f"Uploaded documents exceed {MAX_TOKENS_FILE_UPLOAD:,} tokens ({token_count:,} tokens). Please remove some files to reduce content."
    
    return True, ""


async def analyze_gap(
    docA: str, 
    docB: str, 
    analysis_objective: str,
    source: str = "paste"
) -> str:
    """
    Perform gap analysis between Document A and Document B based on the user's analysis objective.
    
    Args:
        docA: Document A text
        docB: Document B text
        analysis_objective: User's analysis objective
        source: Input source - "paste" for UI text input, "file" for file uploads
        
    Returns:
        Analysis result text
    """
    is_valid, error = validate_inputs(docA, docB, analysis_objective, source)
    if not is_valid:
        raise ValueError(error)
    
    system_prompt = SYSTEM_PROMPT
    user_prompt = f"""
Document A:\n{docA}\n\nDocument B:\n{docB}\n\nAnalysis Objective: {analysis_objective}\n"""

    client = AzureOpenAIClient()
    result = await client.chat_completion(system_prompt, user_prompt)
    return result
