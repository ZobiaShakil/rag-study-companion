from app.services.llm_service import build_chat_history_for_model


def test_build_chat_history_for_model_excludes_previous_model_answers():
    history = [
        {"role": "user", "parts": ["What is photosynthesis?"]},
        {"role": "model", "parts": ["Photosynthesis is the process plants use to make food."]},
        {"role": "user", "parts": ["What does it produce?"]},
    ]

    sanitized_history = build_chat_history_for_model(history)

    assert sanitized_history == [
        {"role": "user", "parts": ["What is photosynthesis?"]},
        {"role": "user", "parts": ["What does it produce?"]},
    ]
