class LlmResponse:
    def __init__(self, text: str, decision: str, aux_data: dict | None) -> None:
        self.text = text
        self.decision = decision
        self.aux_data = aux_data