from sotapapers.modules.llm_client import LLMClient
from sotapapers.core.settings import Settings
from sotapapers.utils.pdf_utils import get_full_text_from_pdf

import loguru
import requests
from pathlib import Path

class LlamaCppClient(LLMClient):
    def __init__(self, settings: Settings, logger: loguru.logger, system_prompt: str, temperature: float = 0.7):
        super().__init__(settings, logger)
        self.file_text = None
        self.system_prompt = system_prompt
        self.temperature = temperature

    def attach_file(self, file_path: Path):
        if not file_path.exists():
            self.logger.error(f"File {file_path} does not exist")
            return
        
        if file_path.suffix == '.pdf':
            self.file_text = get_full_text_from_pdf(file_path)
        
    def run(self, prompt: str, role: str = "user") -> tuple[str, str]:
        url = self.settings.config.llm.clients.llama_cpp.params.server
        model = self.settings.config.llm.clients.llama_cpp.model.name
        max_tokens = self.settings.config.llm.clients.llama_cpp.model.max_tokens

        if self.file_text is not None:
            prompt = f"Answer the question based on the following text:\n\n{self.file_text}\n\n{prompt}"

        data = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "options": {
                "temperature": self.temperature,
                "num_predict": max_tokens
            }
        }
        self.logger.debug(f"LlamaCppClient: Sending data to LLM: {data}")

        response = requests.post(url, json=data)
        json_data = response.json()
        if 'choices' in json_data:
            c = json_data['choices']
            result_str = c[0]['message']['content']

            if '</think>' in result_str:
                thoughts_str = result_str.split('</think>')[0]
                result_str = result_str.split('</think>')[1]
            else:
                thoughts_str = ''
                result_str = result_str
            return thoughts_str, result_str
        else:
            # get error message
            error_message = json_data.get('error', {}).get('message', 'Unknown error')
            self.logger.error(f"Error: {error_message}")
            return '', error_message

if __name__ == "__main__":
    settings = Settings(Path("sotapapers/configs"))
    logger = loguru.logger
    client = LlamaCppClient(settings, logger, "answer in three sentences at most.")
    print(client.run("What is the capital of France?"))