import json
from typing import List, Dict, Any


class DatasetUtils:
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """Loads a JSON file and returns its content."""
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str) -> None:
        """Saves data to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def get_paragraphs(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts paragraphs from the dataset."""
        return data.get('paragraphs', [])

    @staticmethod
    def get_questions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts questions from the dataset."""
        paragraphs = DatasetUtils.get_paragraphs(data)
        questions = []
        for paragraph in paragraphs:
            questions.extend(paragraph.get('qas', []))
        return questions

    @staticmethod
    def get_answers(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts answers from the dataset."""
        questions = DatasetUtils.get_questions(data)
        answers = []
        for question in questions:
            answers.extend(question.get('answers', []))
        return answers

    @staticmethod
    def filter_questions_by_difficulty(data: Dict[str, Any], difficulty: str) -> List[Dict[str, Any]]:
        """Filters questions by difficulty level."""
        questions = DatasetUtils.get_questions(data)
        return [q for q in questions if q.get('difficulty', '').lower() == difficulty.lower()]

    @staticmethod
    def filter_questions_by_type(data: Dict[str, Any], q_type: str) -> List[Dict[str, Any]]:
        """Filters questions by type."""
        questions = DatasetUtils.get_questions(data)
        return [q for q in questions if q.get('type', '').lower() == q_type.lower()]

    @staticmethod
    def filter_answers_by_rating(data: Dict[str, Any], rating: int) -> List[Dict[str, Any]]:
        """Filters answers by rating."""
        answers = DatasetUtils.get_answers(data)
        return [a for a in answers if a.get('rating', 0) == rating]
