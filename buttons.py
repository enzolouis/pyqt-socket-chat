import PyQt6.QtWidgets as widgets
import PyQt6.QtGui as gui
import PyQt6.QtCore as core


class GenericButton(widgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(core.Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("border:none")

class HoverButton(GenericButton):
    def __init__(self, stylesheet, bg, fg, bg_end, fg_end, border, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.transition = core.QVariantAnimation(
            startValue=gui.QColor(bg_end),
            endValue=gui.QColor(bg),
            valueChanged=self._on_value_changed,
            duration=200,
        )#self.transition.setLoopCount(2)

        self.stylesheet = stylesheet
        self.bg = bg
        self.fg = fg
        self.bg_end = bg_end
        self.fg_end = fg_end
        self.border = border

        self.upgradeStyleSheet(self.bg, self.fg, f"2px solid {self.border}") # bg_end as border

    def _on_value_changed(self, bg):
        fg = self.fg if self.transition.direction() == core.QAbstractAnimation.Direction.Forward else self.fg_end
        #border = self.bg# if self.transition.direction() == core.QAbstractAnimation.Direction.Forward else self.bg_end

        self.upgradeStyleSheet(bg.name(), fg, f"2px solid {self.border}")

    def upgradeStyleSheet(self, bg, fg, border="none"):
        self.setStyleSheet("*{"+ self.stylesheet + "background-color:" + bg + ";color:" + fg + ";border:" + border + "}")

    def enterEvent(self, event):
        """ https://doc.qt.io/qt-5/qwidget.html#enterEvent """
        self.transition.setDirection(core.QAbstractAnimation.Direction.Backward)
        self.transition.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """ https://doc.qt.io/qt-5/qwidget.html#leaveEvent """
        self.transition.setDirection(core.QAbstractAnimation.Direction.Forward)
        self.transition.start()
        super().leaveEvent(event)


class AppButton(HoverButton):
    def __init__(self, icon_name:str, icon_size:tuple, fixed_size:tuple, bg, border="none", *args, **kwargs):
        super().__init__("border: none;border-radius:10px;", bg, "#dddddd", "#dddddd", bg, border, *args, **kwargs) # "" : content (nothing)
        self.setIcon(gui.QIcon(icon_name))
        self.setIconSize(core.QSize(*icon_size))
        self.setFixedSize(*fixed_size)