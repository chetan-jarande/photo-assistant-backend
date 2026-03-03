from typing import List, Dict, Any
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import HumanMessage


def detect_entities(image_path: str) -> List[str]:
    """
    Detects objects and entities within an image.

    Args:
        image_path: Path to the image file.

    Returns:
        A list of entity tags (e.g., ["cat", "living room", "sofa"]).
    """
    entities = []

    # TODO: Implement using Gemini Pro Vision or object detection model
    # llm = ChatGoogleGenerativeAI(model="gemini-pro-vision")
    # message = HumanMessage(
    #     content=[
    #         {"type": "text", "text": "List the main objects in this image."},
    #         {"type": "image_url", "image_url": image_path}
    #     ]
    # )
    # response = llm.invoke([message])
    # entities = parse_response(response.content)

    # Mock return
    entities = ["cat", "garden", "flowers", "sunlight"]
    return entities
