from typing import List, Union
# from langchain_google_genai import GoogleGenerativeAIEmbeddings


def generate_embedding(data: Union[str, bytes]) -> List[float]:
    """
    Generates a vector embedding for the given data (image or text).

    Args:
        data: The input data. Can be a text string or image bytes/path.

    Returns:
        A list of floats representing the embedding vector.
    """
    # TODO: Implement using Google Gemini or CLIP
    # model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    # embedding = model.embed_query(data) if isinstance(data, str) else model.embed_image(data)

    # Mock return (e.g., 512-dim vector)
    mock_vector = [0.1] * 512
    return mock_vector
