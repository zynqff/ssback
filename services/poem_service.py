class PoemService:
    @staticmethod
    def process_poem_data(poem: dict) -> dict:
        """Обрабатывает данные стиха для отображения."""
        poem['text'] = poem.get('text', '').replace('\\n', '\n')
        poem['line_count'] = len(poem.get('text', '').split('\n'))
        return poem

    @staticmethod
    def process_poems_data(poems: list) -> list:
        """Обрабатывает список стихов."""
        return [PoemService.process_poem_data(poem) for poem in poems]
