import pygame
import typing
import src.utils as utils


_CACHED_FONTS = {}  # (name, size) -> Font
_SIZE_MAPPING = {"S": 16, "M": 24, "L": 32, "H": 64}


def load_font(name, size) -> pygame.font.Font:
    if isinstance(size, str):
        size = _SIZE_MAPPING[size.upper()]
    key = name, size
    if key not in _CACHED_FONTS:
        filepath = utils.asset_path(f"assets/{name}.ttf")
        _CACHED_FONTS[key] = pygame.font.Font(filepath, size)
    return _CACHED_FONTS[key]


class TextRenderer:

    def __init__(self, text: str, size: typing.Union[int, str], color=(255, 255, 255), bg_color=None,
                 font_name="alagard", y_kerning=0, alignment=-1):
        self._text = text
        self._text_size = size
        self._text_color = color
        self._bg_color = bg_color
        self._text_font_name = font_name
        self._text_y_kerning = y_kerning
        self._alignment = alignment

        # cached stuff
        self._text_font = load_font(font_name, size)
        self._cached_text_surfaces = None

        self._last_drawn_at_rect = None

    def _refresh(self, force=False):
        if force:
            self._cached_text_surfaces = None
            self._text_font = None

        if self._cached_text_surfaces is None or self._text_font is None:
            self._text_font = load_font(self._text_font_name, self._text_size)
            self._cached_text_surfaces = []
            for line in self._text.split("\n"):
                surf = self._text_font.render(line, False, self._text_color, self._bg_color)
                self._cached_text_surfaces.append(surf)

    def get_size(self):
        self._refresh()
        w, h = 0, 0
        for line_img in self._cached_text_surfaces:
            w = max(w, line_img.get_width())
            if h > 0:
                h += self._text_y_kerning
            h += line_img.get_height()
        return w, h

    def get_alignment(self) -> int:
        return self._alignment

    def draw(self, dest_surf: pygame.Surface, xy):
        self._refresh()
        x, y = xy
        w, h = self.get_size()
        for line_img in self._cached_text_surfaces:
            if self._alignment == -1:  # left aligned
                x_to_use = x
            elif self._alignment == 1:  # right aligned
                x_to_use = x + w - line_img.get_width()
            else:  # centered
                x_to_use = int(x + w / 2 - line_img.get_width() / 2)
            dest_surf.blit(line_img, (x_to_use, y))
            y += line_img.get_height() + self._text_y_kerning

        self._last_drawn_at_rect = (x, xy[1], w, h)

    def draw_with_center_at(self, dest_surf, xy):
        self._refresh()
        w, h = self.get_size()
        xy_to_use = xy[0] - w // 2, xy[1] - h // 2
        self.draw(dest_surf, xy_to_use)

    def get_last_drawn_rect(self):
        return self._last_drawn_at_rect

    def set_text(self, new_text):
        if new_text != self._text:
            self._text = new_text
            self._cached_text_surfaces = None

    def get_text(self):
        return self._text

    def set_color(self, color, bg_color="nochange"):
        if self._text_color != color or (bg_color != "nochange" and bg_color != self._bg_color):
            self._text_color = color
            self._bg_color = self._bg_color if bg_color == "nochange" else bg_color
            self._cached_text_surfaces = None
            self._text_font = None

    def set_size(self, size):
        if self._text_size != size:
            self._text_size = size
            self._cached_text_surfaces = None
            self._text_font = None