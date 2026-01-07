"""
Image text extraction for TaskTriage.

Uses Claude's vision API to extract text from handwritten note images.
"""

import base64
import io
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_path

from .config import fetch_api_key, load_model_config, DEFAULT_MODEL
from .prompts import IMAGE_EXTRACTION_PROMPT

# Supported image file extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

# Supported PDF file extensions
PDF_EXTENSIONS = {".pdf"}

# All visual document extensions (images and PDFs)
VISUAL_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS

# Mapping of file extensions to MIME types
MEDIA_TYPE_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def extract_text_from_image(image_path: Path, api_key: str | None = None) -> str:
    """Extract text from an image of handwritten notes using Claude's vision API.

    Supports: PNG, JPEG, GIF, and WebP formats.

    Args:
        image_path: Path to the image file
        api_key: Optional Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)

    Returns:
        Extracted text content from the image

    Raises:
        ValueError: If the image format is not supported
    """
    config = load_model_config()

    # Extract model from config or use default
    model = config.pop("model", DEFAULT_MODEL)

    # Build ChatAnthropic with config parameters
    llm = ChatAnthropic(
        model=model,
        api_key=fetch_api_key(api_key),
        **config
    )

    # Read and encode the image
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")

    # Determine media type based on file extension
    suffix = image_path.suffix.lower()
    media_type = MEDIA_TYPE_MAP.get(suffix)
    if not media_type:
        raise ValueError(
            f"Unsupported image format: {suffix}. "
            f"Supported formats: {', '.join(sorted(IMAGE_EXTENSIONS))}"
        )

    # Create message with image content
    message = HumanMessage(
        content=[
            {"type": "text", "text": IMAGE_EXTRACTION_PROMPT},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{image_data}"},
            },
        ]
    )

    response = llm.invoke([message])
    return response.content


def extract_text_from_pdf(pdf_path: Path, api_key: str | None = None) -> str:
    """Extract text from a PDF document of handwritten notes using Claude's vision API.

    Converts each PDF page to an image and processes with Claude's vision API,
    then concatenates the extracted text from all pages.

    Args:
        pdf_path: Path to the PDF file
        api_key: Optional Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)

    Returns:
        Extracted text content from all PDF pages

    Raises:
        ValueError: If the file is not a PDF
    """
    suffix = pdf_path.suffix.lower()
    if suffix not in PDF_EXTENSIONS:
        raise ValueError(f"Unsupported PDF format: {suffix}. Expected: .pdf")

    config = load_model_config()

    # Extract model from config or use default
    model = config.pop("model", DEFAULT_MODEL)

    # Build ChatAnthropic with config parameters
    llm = ChatAnthropic(
        model=model,
        api_key=fetch_api_key(api_key),
        **config
    )

    # Convert PDF pages to images
    images = convert_from_path(str(pdf_path))

    if not images:
        return ""

    # Extract text from each page
    extracted_texts = []
    for page_num, image in enumerate(images, start=1):
        # Convert PIL Image to bytes and then to base64
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_data = base64.standard_b64encode(image_bytes.getvalue()).decode("utf-8")

        # Create message with page image content
        message = HumanMessage(
            content=[
                {"type": "text", "text": IMAGE_EXTRACTION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"},
                },
            ]
        )

        response = llm.invoke([message])
        extracted_texts.append(response.content)

    # Concatenate text from all pages with page separators
    return "\n---\n".join(extracted_texts)
