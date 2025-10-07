



class Text:
    def __init__(self):
        self.content = ""
        self.styling: list[tuple[int, int, dict[str]]] = []
        self.lines: list[tuple[int, dict[str]]] = []


class TextViewer:
    def __init__(self):
        self.text = Text()
        self.width = 80
        self.height = 40

        self.tabsize = 4

        


