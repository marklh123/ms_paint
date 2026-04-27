
import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QImage, QPainter, QPen, QBrush, QIcon, QPolygon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel,
                             QWidget, QVBoxLayout, QHBoxLayout, QAction, QFileDialog, QGridLayout, QPushButton,
                             QLineEdit)
from PyQt5.QtCore import Qt, QPoint, QSize
from functools import partial
import os

def load_custom_font(font_path):
    """Loads a custom font into the application's font database."""
    font_id = QtGui.QFontDatabase.addApplicationFont(font_path)

    if font_id == -1:
        print(f"Error: Font '{font_path}' could not be loaded.")
        return None
    # Retrieve the font family name after loading
    families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
    if families:
        return families[0] # Return the family name
    return None

class Canvas(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)

        self.drawing = False
        self.brush_size = 10
        self.brush_color = Qt.black
        self.lastPoint = QPoint()

        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.image.fill(Qt.white)
        self.last_color = Qt.GlobalColor.black
        self.should_draw_shape = False
        self.shape_type = None

        self.sr = None
        self.sc = None
        self.stack = []
        self.need_to_fill = False
        self.old_color = Qt.white

    def floodFill(self):

        self.old_color = self.image.pixelColor(self.sr, self.sc)

        # if already new color, stop before it starts painting
        if self.old_color == self.brush_color:
            return

        self.dfs(self.sr, self.sc)
    def need_to_bucket_fill(self):
        self.need_to_fill = not self.need_to_fill
    def dfs(self, x, y):

        self.stack.append((x, y))

        while self.stack:
            bad_pixel = False

            current_pixel = self.stack.pop()
            cpx, cpy = current_pixel[0], current_pixel[1]

            # reaches a border same color as fill color
            if self.image.pixelColor(cpx, cpy) == self.brush_color:
                bad_pixel = True
            # reaches a border different color as fill color
            elif self.image.pixelColor(cpx, cpy) != self.brush_color and self.image.pixelColor(cpx, cpy) != self.old_color:
                bad_pixel = True

            if not bad_pixel:
                self.image.setPixelColor(cpx, cpy, self.brush_color)
                self.stack.extend([(cpx + 1, cpy), (cpx - 1, cpy), (cpx, cpy + 1), (cpx, cpy - 1)])

        # fill is done, reset everything
        self.update()
        self.need_to_fill = False

    # for painting to be on mouse because layouts
    def resizeEvent(self, event):
        # Create a new image scaled to the new size of the label
        new_image = QImage(self.size(), QImage.Format_RGB32)
        new_image.fill(Qt.white)

        # Paint the old image onto the new one so you don't lose your work
        painter = QPainter(new_image)
        painter.drawImage(QPoint(0, 0), self.image)
        self.image = new_image

    def mousePressEvent(self, event):
        self.drawing = True
        self.lastPoint = event.pos()

        # drawing shapes
        if self.should_draw_shape:
            self.actually_drawing_shape(self.lastPoint.x(),self.lastPoint.y(),self.shape_type)
            self.should_draw_shape = False

        # bucket fill
        if self.need_to_fill:
            self.sr, self.sc = self.lastPoint.x(), self.lastPoint.y()
            self.floodFill()
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drawing:
            painter = QPainter(self.image)

            painter.setPen(QPen(self.brush_color, self.brush_size,
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            painter.drawLine(self.lastPoint, event.pos())
            self.lastPoint = event.pos()

            self.update()
    def mouseReleaseEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        canvas_painter = QPainter(self)

        # draw rectangle  on the canvas
        canvas_painter.drawImage(self.rect(), self.image, self.image.rect())

    # functions for menu bar
    def clear(self):
        # make the whole canvas white
        self.image.save("./undo.png")
        self.image.fill(Qt.white)
        # update
        self.update()
    def save(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.image.save(file_path)
        else:
            print("File path error")
    def undo(self):
        self.image.load("./undo.png")
        self.update()
    def load(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.image.load(file_path)
        else:
            print("File path error")

        self.update()

    def ChangeColor(self,color):
        match color:
            case "red":
                self.brush_color = Qt.red
                self.last_color = Qt.GlobalColor.red
            case "blue":
                self.brush_color = Qt.blue
                self.last_color = Qt.GlobalColor.blue
            case "green":
                self.brush_color = Qt.darkGreen
                self.last_color = Qt.GlobalColor.darkGreen
            case "black":
                self.brush_color = Qt.black
                self.last_color = Qt.GlobalColor.black
            case "yellow":
                self.brush_color = Qt.yellow
                self.last_color = Qt.GlobalColor.yellow
            case "purple":
                self.brush_color = Qt.darkMagenta
                self.last_color = Qt.GlobalColor.darkMagenta
            case "eraser":
                self.brush_color = Qt.white
                self.last_color = Qt.GlobalColor.white
    def ChangeBrushSize(self,box_object):
        text = box_object.text()

        if isinstance(text,str) and text.isdigit():
            s = int(box_object.text())
            self.brush_size = s

    def need_to_draw_shape(self,shape):
        self.should_draw_shape = True
        self.shape_type = shape

    def actually_drawing_shape(self,x,y,shape_type):

        painter = QPainter(self.image)
        painter.setPen(QPen(self.last_color, self.brush_size))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        match shape_type:
            case "square":
                painter.drawRect(x,y,100,100)
            case "circle":
                painter.drawEllipse(x-10,y-10,100,100)
            case "triangle":
                points = QPolygon([
                    QPoint(x, y),
                    QPoint(x-50, y + 100),
                    QPoint(x+50, y + 100)
                ])
                painter.drawPolygon(points)
            case "star":
                points = QPolygon([
                    QPoint(x, y),
                    QPoint(x + 13, y + 38),
                    QPoint(x + 53, y + 38),
                    QPoint(x + 21, y + 62),
                    QPoint(x + 33, y + 100),
                    QPoint(x, y + 76),
                    QPoint(x - 33, y + 100),
                    QPoint(x - 21, y + 62),
                    QPoint(x - 53, y + 38),
                    QPoint(x - 13, y + 38)
                ])
                painter.drawPolygon(points)


        painter.setPen(QPen(self.brush_color, self.brush_size,
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        painter.end()
        self.update()

class MainWindow(QMainWindow):
   def __init__(self):
       super().__init__()
       self.setWindowTitle("Paint")
       self.setGeometry(500,200,800,800)
       self.initUI()

   def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # font
        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images_plus_font_ms_paint/Ldfcomicsans-jj7l.ttf")

        font_family = load_custom_font(font_path)

        # labels

        label_canvas = Canvas("")

        # empty space, can add more possible features here
        label_drawing_options = QLabel()

        label_title = QLabel("Mark Hristov's Paint Application")
        label_title.setStyleSheet(f"""
                               background-color: white; 
                               font-family: '{font_family}'; 
                               font-size: 52px;
                           """)
        label_title.setAlignment(Qt.AlignCenter)

        label_drawing_options.setStyleSheet("background-color: white;")
        label_drawing_options.setAlignment(Qt.AlignCenter)

        # color buttons
        label_color1 = QPushButton()
        label_color1.setStyleSheet("background-color: black;")
        label_color1.clicked.connect(partial(label_canvas.ChangeColor,"black"))
        label_color2 = QPushButton()
        label_color2.setStyleSheet("background-color: red;")
        label_color2.clicked.connect(partial(label_canvas.ChangeColor,"red"))
        label_color3 = QPushButton()
        label_color3.setStyleSheet("background-color: blue;")
        label_color3.clicked.connect(partial(label_canvas.ChangeColor,"blue"))
        label_color4 = QPushButton()
        label_color4.setStyleSheet("background-color: yellow;")
        label_color4.clicked.connect(partial(label_canvas.ChangeColor,"yellow"))
        label_color5 = QPushButton()
        label_color5.setStyleSheet("background-color: green;")
        label_color5.clicked.connect(partial(label_canvas.ChangeColor,"green"))
        label_color6 = QPushButton()
        label_color6.setStyleSheet("background-color: purple;")
        label_color6.clicked.connect(partial(label_canvas.ChangeColor,"purple"))

        # eraser and bucket buttons
        eraser_button = QPushButton()
        eraser_button.setIcon(QIcon("images_plus_font_ms_paint/eraser.png"))
        eraser_button.setFlat(True)
        eraser_button.setIconSize(QSize(70, 40))
        eraser_button.clicked.connect(partial(label_canvas.ChangeColor,"eraser"))
        bucket_button = QPushButton()
        bucket_button.setIcon(QIcon("images_plus_font_ms_paint/bucket.png"))
        bucket_button.setFlat(True)
        bucket_button.setIconSize(QSize(70, 40))

        # fills last color
        bucket_button.clicked.connect(label_canvas.need_to_bucket_fill)

        # brush size type-in box
        brush_size_box = QLineEdit()
        brush_size_box.setPlaceholderText("Font size...")
        brush_size_box.returnPressed.connect(partial(label_canvas.ChangeBrushSize, brush_size_box))

        # shapes
        square_button = QPushButton()
        square_button.setIcon(QIcon("images_plus_font_ms_paint/square.png"))
        square_button.setIconSize(QSize(40, 40))
        square_button.clicked.connect(partial(label_canvas.need_to_draw_shape,"square"))
        circle_button = QPushButton()
        circle_button.setIcon(QIcon("images_plus_font_ms_paint/circle.png"))
        circle_button.setIconSize(QSize(40, 40))
        circle_button.clicked.connect(partial(label_canvas.need_to_draw_shape,"circle"))
        triangle_button = QPushButton()
        triangle_button.setIcon(QIcon("images_plus_font_ms_paint/triangle.png"))
        triangle_button.setIconSize(QSize(40, 40))
        triangle_button.clicked.connect(partial(label_canvas.need_to_draw_shape,"triangle"))
        star_button = QPushButton()
        star_button.setIcon(QIcon("images_plus_font_ms_paint/star.png"))
        star_button.setIconSize(QSize(40, 40))
        star_button.clicked.connect(partial(label_canvas.need_to_draw_shape,"star"))

        # menu bar
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu("File")
        mainMenu.setNativeMenuBar(False) # for macOS keeps menu inside of window
        mainMenu.setStyleSheet((f"""
    QMenuBar {{
        background-color: #f0f0f0;
        font-family: '{font_family}'; /* Change to your font name */
        font-size: 17px;              /* Makes the 'File' text bigger */
        font-weight: regular;
    }}
    QMenu {{
        font-size: 15px;              /* Makes the items INSIDE the menu bigger */
        background-color: white;
        border: 1px solid black;
        font-family: '{font_family}'
        
    }}
"""))

        # export action (save)
        saveAction = QAction("Export", self)
        fileMenu.addAction(saveAction)
        # adding action to the save
        saveAction.triggered.connect(label_canvas.save)

        # import action
        importAction = QAction("Import", self)
        fileMenu.addAction(importAction)
        importAction.triggered.connect(label_canvas.load)

        # clear action
        clearAction = QAction("Clear", self)
        fileMenu.addAction(clearAction)
        # adding action to the clear
        clearAction.triggered.connect(label_canvas.clear)

        # undo clear action
        undoclearAction = QAction("Undo Clear", self)
        fileMenu.addAction(undoclearAction)
        undoclearAction.triggered.connect(label_canvas.undo)

        # layouts

        # color layout
        layout_colors = QGridLayout()
        layout_colors.addWidget(label_color1,0,0)
        layout_colors.addWidget(label_color2,0,1)
        layout_colors.addWidget(label_color3,0,2)
        layout_colors.addWidget(label_color4,1,0)
        layout_colors.addWidget(label_color5,1,1)
        layout_colors.addWidget(label_color6,1,2)

        # eraser and bucket layout
        layout_eraser_and_bucket = QHBoxLayout()
        layout_eraser_and_bucket.addWidget(eraser_button,1)
        layout_eraser_and_bucket.addWidget(bucket_button,1)

        # shape layout
        layout_shapes = QGridLayout()
        layout_shapes.addWidget(square_button,0,0)
        layout_shapes.addWidget(circle_button,0,1)
        layout_shapes.addWidget(triangle_button,1,0)
        layout_shapes.addWidget(star_button,1,1)

        # sidebar layout
        layout_side_bar = QVBoxLayout()
        layout_side_bar.addLayout(layout_colors,1)
        layout_side_bar.addLayout(layout_eraser_and_bucket,1)
        layout_side_bar.addWidget(brush_size_box,1)
        layout_side_bar.addLayout(layout_shapes,1)
        layout_side_bar.addWidget(label_drawing_options,3)

        # second outer layout (sidebar and canvas)
        layout = QHBoxLayout()
        layout.addLayout(layout_side_bar, 1)
        layout.addWidget(label_canvas, 3)

        # final outer layout
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(label_title,1)
        outer_layout.addLayout(layout,5)

        central_widget.setLayout(outer_layout)

def main():
   app = QApplication(sys.argv)
   window = MainWindow()
   window.show()
   sys.exit(app.exec_())

if __name__ == "__main__":
   main()
   app = QtWidgets.QApplication(sys.argv)



