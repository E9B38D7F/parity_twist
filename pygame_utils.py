import pygame as p


def print_text(string, size, colour, x_centre, y_centre, screen):
    font = p.font.SysFont("menlo", size, True, False)
    text = font.render(string, 0, p.Color(colour))
    text_rect = text.get_rect(center=(x_centre, y_centre))
    screen.blit(text, text_rect)

def expand_rect(rect, epsilon):
    return p.Rect(
        rect.x - epsilon,
        rect.y - epsilon,
        rect.w + 2 * epsilon,
        rect.h + 2 * epsilon
    )


class Box:
    def __init__(self, x, y, w, h, screen, text=''):
        self.x_mid = x + w // 2
        self.y_mid = y + h // 2
        self.rect = p.Rect(x, y, w, h)
        self.color = p.Color("Black")
        self.text = text
        self.active = False
        self.screen = screen
        self.draw()

    def draw(self):
        p.draw.rect(self.screen, "#FFEEFF", expand_rect(self.rect, 6))
        p.draw.rect(self.screen, "#000000", expand_rect(self.rect, 3))
        p.draw.rect(self.screen, self.color, self.rect)
        print_text(
            self.text,
            24,
            "#FF0000",
            self.x_mid,
            self.y_mid,
            self.screen
        )


class InputBox(Box):
    # This one taken from github, thank you
    def __init__(self, x, y, w, h, screen, text=''):
        super().__init__(x, y, w, h, screen, text=text)

    def handle_event(self, event, screen):
        if event.type == p.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            if self.active:
                self.color = p.Color("Orange")
            else:
                self.color = p.Color("Black")
            self.draw()
        if event.type == p.KEYDOWN:
            if self.active:
                if event.key == p.K_RETURN:
                     pass
                elif event.key == p.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
            self.draw()


class OptionBox(Box):
    def __init__(self, x, y, w, h, screen, text=''):
        super().__init__(x, y, w, h, screen, text=text)
        self.active = False
        self.others = [] # These are the mutually exclusive buttons

    def handle_event(self, event, others):
        if event.type == p.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                for other in self.others:
                    if other is not self:
                        other.active = False
                        other.color = p.Color("Black")
                        other.draw()
                self.color = p.Color("Orange")
                self.draw()
