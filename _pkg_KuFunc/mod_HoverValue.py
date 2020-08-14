'''

hover UI with one key press that shows knobs to change value

'''


__VERSION__=0.0


def _version_():
	ver='''

	version 0.0
	- hover UI with one key press that shows knobs to change value
	- knobs procedurally generated based on the node class selected

	'''
	return ver




#------------------------------------------------------------------------------
#-Module Import
#------------------------------------------------------------------------------




import nuke, nukescripts
import os
import pprint
from kputl import joinPath, dprint, DEBUG_PRINT
from Qt import QtWidgets, QtGui, QtCore




#-------------------------------------------------------------------------------
#-Global Variables
#-------------------------------------------------------------------------------




# Knob_Class: Qt_Knob
KNOBS_QT = {
	'Array_Knob': 'Knob_Array',
	'Boolean_Knob': 'Knob_Boolean',
	'Channel_Knob': 'Knob_Channel',
	'Enumeration_Knob': 'Knob_Enumeration',
	'PyScript_Knob': 'Knob_PyScript',
	'Int_Knob': 'Knob_Int',
	'XY_Knob': 'Knob_XY',
	'Double_Knob': 'Knob_Array',
	'WH_Knob': 'Knob_Array',
	'AColor_Knob': 'Knob_Array'
}


KNOBS_NK = {
	'Blur': ['size', 'filter'],
	'Grade': ['blackpoint', 'whitepoint', 'black', 'white', 'multiply', 'add', 'gamma'],
	'Dilate': ['size'],
	'Saturation': ['saturation', 'mode'],
	'Defocus': ['defocus', 'ratio'],
	'ZDefocus2': ['center', 'dof', 'size', 'max_size'],
	'Multiply': ['value'],
	'EXPTool': ['red'],
	'Colorspace': ['colorspace_in', 'colorspace_out'],
	'OCIOColorSpace': ['in_colorspace', 'out_colorspace'],
	'OCIOLogConvert': ['operation'],
	'Log2Lin': ['operation'],
	'Transform': ['translate', 'rotate', 'scale', 'invert_matrix']
}


USER_LABEL = {
	'EXPTool': [('red', 'stops')],

}


DIR_ICON = joinPath(os.path.dirname(nuke.EXE_PATH), 'plugins', 'icons')




#------------------------------------------------------------------------------
#-Core Module UI
#------------------------------------------------------------------------------




class Core_HoverValue(QtWidgets.QDialog):
	def __init__(self):
		super(Core_HoverValue, self).__init__()

		# Widgets
		self.node_icon = QtWidgets.QLabel()
		self.title = QtWidgets.QLabel('<b>HoverValue</b>')
		self.btn_showPanel = QtWidgets.QPushButton('Edit in Properties Panel')
		self.btn_showPanel.clicked.connect(self.open_ControlPanel)

		# Layout
		self.layout_title = QtWidgets.QHBoxLayout()
		self.layout_title.addWidget(self.node_icon)
		self.layout_title.addWidget(self.title)
		self.layout_title.addStretch()

		self.group_knobs = QtWidgets.QGroupBox()
		self.layout_knobs = QtWidgets.QGridLayout()
		self.group_knobs.setLayout(self.layout_knobs)
		
		self.layout_master = QtWidgets.QVBoxLayout()
		self.layout_master.addLayout(self.layout_title)
		self.layout_master.addWidget(self.group_knobs)
		self.layout_master.addWidget(self.btn_showPanel)
		self.layout_master.addStretch()

		self.setLayout(self.layout_master)
		self.setWindowTitle('HoverValue v%s' % __VERSION__)
		self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)

		self.setDefaults()


	# Move window with left click and keep default mouse event
	# https://stackoverflow.com/questions/37718329/pyqt5-draggable-frameless-window
	# 
	def mouseMoveEvent(self, event):
		super(Core_HoverValue, self).mouseMoveEvent(event)
		if self.leftClick == True: 
			delta = QtCore.QPoint (event.globalPos() - self.oldPos)
			#print(delta)
			self.move(self.x() + delta.x(), self.y() + delta.y())
			self.oldPos = event.globalPos()

	def mousePressEvent(self, event):
		self.oldPos = event.globalPos()
		super(Core_HoverValue, self).mousePressEvent(event)
		if event.button() == QtCore.Qt.LeftButton:
			self.leftClick = True

	def mouseReleaseEvent(self, event):
		super(Core_HoverValue, self).mouseReleaseEvent(event)
		self.leftClick = False


	def keyPressEvent(self, event):
		'''override return key pressed'''

		if event.key() == QtCore.Qt.Key_Enter:
			pass

		# print event.key().name()`


	def setDefaults(self):
		'''sets default values'''

		pass

	def run(self):
		'''run instant'''


		if len(nuke.selectedNodes())>0:
			if nuke.selectedNode().Class() not in KNOBS_NK.keys():
				nuke.selectedNode().showControlPanel()
				print("Selected node not in database, show control panel instead")
			else:
				_sel_node, _ls_knobs = self.get_nuke_knobs()
				print _sel_node.name(), _ls_knobs

				self.build_qt_knob(_sel_node, _ls_knobs)
				self.set_qt_knob(_sel_node, _ls_knobs)

				self.move(QtGui.QCursor.pos()+QtCore.QPoint(-200,-12))
				self.raise_()
				self.show()
		else:
			nuke.message("Please select a node")

	def closeEvent(self, event):
		self.remove_widgets()
		print "close"

	def get_nuke_knobs(self):
		'''get the selected node and its knobs
		return: (tuple), (obj) node object, (list of str) knob names 
		'''

		_n = nuke.selectedNode()
		_nodename = _n.name()
		_knobs = KNOBS_NK[_n.Class()]
		self.group_knobs.setTitle(_nodename)
		self.node_icon.setPixmap(QtGui.QPixmap(joinPath(DIR_ICON, '%s.png' % _n.Class())))

		return _n, _knobs

	def build_qt_knob(self, node, ls_knobs):
		'''build qt widgets base on given nuke knob
		@node: (obj) selected node
		@ls_knobs: (list of str) list of knobs
		'''

		self.remove_widgets()

		build_string_label = """
		{k}_label=Knob_Label('{label}',nuke_knob='{k}')
		self.layout_knobs.addWidget({k}_label, {row}, 0)
		""".replace('\t','')
		
		build_string_widgets = """
		{k}_qtknob={w}(nuke_knob='{k}')
		self.layout_knobs.addWidget({k}_qtknob, {row}, 1)
		""".replace('\t','')

		for row, k in enumerate(ls_knobs):
			# _ls_widget = get_qt_knob(node, k)
			_this_qt_knob = get_qt_knob(node,k)
			LS_NO_LABEL = ['Boolean_Knob']
			_this_knob_label = get_knob_label(node,k) if node[k].Class() not in LS_NO_LABEL else ''
			
			# Build label for this row at col=0
			exec(build_string_label.format(k=k,label=_this_knob_label,row=row))
			exec(build_string_widgets.format(k=k, w=_this_qt_knob, row=row))
		


	def set_qt_knob(self, node, ls_knobs):
		'''set initial settings for qt widgets
		@node: (obj) node object
		@ls_knobs: (list) list of knobs
		'''

		_thisLayout = self.layout_knobs

		dict_qt_knobs = {}

		# pair knob and knobWidgets
		for k in ls_knobs:		
			ls_qt_knobs = []
			
			for w in range(_thisLayout.count()):

				if _thisLayout.itemAt(w):
					_this_qt_knob = _thisLayout.itemAt(w).widget()

					if k == _this_qt_knob.nuke_knob and 'label' not in _this_qt_knob.nuke_knob:
						# print _this_qt_knob.nuke_knob
						ls_qt_knobs.append(_this_qt_knob)

			dict_qt_knobs[k]=ls_qt_knobs

		# Set Settings
		for k in ls_knobs:
			_this_knob_class = node.knob(k).Class()

			if  _this_knob_class in ['Array_Knob', 'AColor_Knob', 'Double_Knob', 'WH_Knob']:
				val_knob = node[k].value()
				val_min = node[k].min()
				val_max = node[k].max()

				for w in dict_qt_knobs[k]:
					w.set_range(val_min, val_max)
					w.set_value(val_knob)

			elif _this_knob_class in ['Enumeration_Knob']:
				val_knob = node[k].value()
				val_list = node[k].values()
				
				val_list = [v.split('\t')[0] for v in val_list]
				val_list = [v.split('/')[-1] for v in val_list]
				
				val_knob = val_knob.split('\t')[0]
				val_knob = val_knob.split('/')[-1]

				for w in dict_qt_knobs[k]:
					w.set_list(val_list)
					w.set_value(val_knob)

			else:
				val_knob = node[k].value()

				for w in dict_qt_knobs[k]:
					w.set_value(val_knob)

		# pprint.pprint(dict_qt_knobs)

	def remove_widgets(self):
		'''remove the widgets from layout'''
		_thisLayout = self.layout_knobs
		for w in range(_thisLayout.count()):
			child = _thisLayout.itemAt(w)
			if child.widget():
				child.widget().deleteLater()
		# self.minimumSizeHint()


	def open_ControlPanel(self):
		'''show given node in property panel'''
		_thisNode = nuke.toNode(self.group_knobs.title())
		_thisNode.showControlPanel()
		self.close()

	def print_widgets(self):
		'''get all widgets in a layout'''
		_thisLayout = self.layout_knobs
		
		for w in range(_thisLayout.count()):
			if _thisLayout.itemAt(w):
				print(_thisLayout.indexOf(_thisLayout.itemAt(w).widget()), _thisLayout.itemAt(w).widget().nuke_knob)
	



#-------------------------------------------------------------------------------
#-Supporting Functions
#-------------------------------------------------------------------------------




def get_knob_label(node, knob):
	'''get the label of a node with given node and knobname
	@node: (obj) node object
	@knob: (str) knob in name string
	return: (str) label of the node, if none, use node name
	'''

	_label = node.knob(knob).label()
	_thisKnobLabel = _label if _label else knob

	# Replace knob_label with user_label
	if node.Class() in USER_LABEL.keys():
		_user_label = USER_LABEL[node.Class()]
		for u in _user_label:
			_thisKnobLabel = _thisKnobLabel.replace(*u)

	return _thisKnobLabel


def get_qt_knob(node, knob):
	'''get the cooresponding qt widget base on given knob and node
	@node: (obj) node object
	@knob: (str) knob in name string
	return: (list of str) list of Qt widget as string
	'''

	_thisKnobClass = node.knob(knob).Class()
	_thisQtKnob = KNOBS_QT[_thisKnobClass]

	return _thisQtKnob


def dynamic_decimals(v):
	'''dynamically change decimals with given input'''
	precision = len(str(v).split('.')[1].rstrip('0')) if v != 0.0 else 0
	return int(precision)


def set_nuke_knob(qt_knob,k,v):
	'''sets value on nuke knob
	@qt_knob: (obj) current qt_knob object
	@k: (str) name of the knob
	@v: value of the knob
	'''

	node = nuke.toNode(qt_knob.parent().title())
	node[k].setValue(v)




#-------------------------------------------------------------------------------
#-Custom Widgets
#-------------------------------------------------------------------------------




class Knob_Label(QtWidgets.QLabel):
	def __init__(self, text, nuke_knob=''):
		super(Knob_Label, self).__init__()

		# Instance ID
		self.nuke_knob = nuke_knob+'_label'
		self.Class = 'Knob_Label'

		# Instance properties
		self.setText(text)
		self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)


class Knob_Array(QtWidgets.QWidget):
	'''Knob_Slider + Knob_EditBox'''
	def __init__(self ,nuke_knob=''):
		super(Knob_Array, self).__init__()
		
		# Instance ID
		self.nuke_knob = nuke_knob
		self.Class = 'Knob_Array'

		# Instance properties
		self.editbox = Knob_EditBox(self.nuke_knob)
		self.slider = Knob_Slider(self.nuke_knob)

		self.editbox.editingFinished.connect(self.onChanged)
		self.slider.valueChanged.connect(self.onChanged)

		self.layout = QtWidgets.QHBoxLayout()
		self.layout.addWidget(self.editbox)
		self.layout.addWidget(self.slider)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)

		self.setDefaults()

	def setDefaults(self):
		'''get value from nuke knob when initialized'''
		
		pass

	def set_range(self, min, max):
		'''set range for slider'''
		_precision = self.slider.PRECISION
		self.slider.setRange(min*_precision, max*_precision)

	def set_value(self, v):
		self.slider.set_value(v)
		self.editbox.setDecimals(dynamic_decimals(v))
		self.editbox.set_value(v)

	def onChanged(self):
		'''when editbox or slider is edited and change each other values'''
		_sender = self.sender()
		_v = _sender.get_value()
		_dec = dynamic_decimals(_v)

		# avoid infinit recursion
		if isinstance(_sender, Knob_EditBox):
			self.editbox.setDecimals(_dec)
			self.slider.set_value(_v)
		elif isinstance(_sender, Knob_Slider):
			self.editbox.setDecimals(_dec)
			self.editbox.set_value(_v)

		# Change nuke_knob value
		set_nuke_knob(self, self.nuke_knob, _v)


class Knob_XY(QtWidgets.QWidget):
	def __init__(self, nuke_knob=''):
		super(Knob_XY, self).__init__()

		# Instance ID
		self.nuke_knob = nuke_knob
		self.Class = 'Knob_XY'
		
		# Instance properties
		self.knob_x = Knob_DoubleSpin(self.nuke_knob)
		self.knob_x.editingFinished.connect(self.onChanged)
		self.knob_y = Knob_DoubleSpin(self.nuke_knob)
		self.knob_y.editingFinished.connect(self.onChanged)
		self.layout = QtWidgets.QHBoxLayout()
		self.layout.addWidget(QtWidgets.QLabel('x'))
		self.layout.addWidget(self.knob_x)
		self.layout.addWidget(QtWidgets.QLabel('y'))
		self.layout.addWidget(self.knob_y)
		self.layout.addStretch()
		self.layout.setContentsMargins(0,0,0,0)
		self.setLayout(self.layout)

	def set_value(self, v):
		'''set value x and y'''
		
		self.knob_x.setDecimals(dynamic_decimals(v[0]))
		self.knob_x.setValue(float(v[0]))
		self.knob_y.setDecimals(dynamic_decimals(v[1]))
		self.knob_y.setValue(float(v[1]))

	def get_value(self):
		'''set value x and y
		return: (x,y)
		'''

		return self.knob_x, self.knob_y

	def onChanged(self):
		_sender = self.sender()
		_v = _sender.get_value()
		_sender.setDecimals(dynamic_decimals(_v))

		# set nuke knob value
		set_nuke_knob(self, self.nuke_knob, _v)



class Knob_Enumeration(QtWidgets.QWidget):
	def __init__(self, nuke_knob=''):
		super(Knob_Enumeration, self).__init__()

		# Instance ID
		self.nuke_knob = nuke_knob
		self.Class = 'Knob_Enumeration'

		# Instance properties

		arrow = u'\u25b2' if 'out' in self.nuke_knob else u'\u25bc'

		self.combobox = QtWidgets.QComboBox()
		self.combobox.setMaximumWidth(200)
		self.combobox.currentIndexChanged.connect(self.onChanged)
		self.swap = QtWidgets.QPushButton(arrow)
		self.swap.clicked.connect(self.set_swap)
		self.swap.setMaximumWidth(32)

		self.layout = QtWidgets.QHBoxLayout()
		self.setLayout(self.layout)
		self.layout.setContentsMargins(0, 0, 0, 0)

		self.layout.addWidget(self.combobox)
		
		if 'colorspace' in nuke_knob.lower():
			self.layout.addWidget(self.swap)

		self.layout.addStretch()
	
	def set_swap(self):
		'''swap colorspace with adjsent qt_knob'''

		_this_value = self.combobox.currentText()
		_ls_qt_knobs =[w for w in self.parent().children() if isinstance(w, self.__class__)]

		_value_A = _ls_qt_knobs[0].combobox.currentText()
		_value_B = _ls_qt_knobs[1].combobox.currentText()

		_ls_qt_knobs[0].set_value(_value_B)
		_ls_qt_knobs[1].set_value(_value_A)

	def set_list(self, ls):
		'''sets dropdown list'''
		self.combobox.clear()
		self.combobox.addItems(ls)

	def set_value(self, i):
		'''set current item'''
		_idx = self.combobox.findText(i)
		self.combobox.setCurrentIndex(_idx)

	def onChanged(self):
		# set nuke_knob value
		_v = self.sender().currentText()
		set_nuke_knob(self, self.nuke_knob, str(_v))


class Knob_Boolean(QtWidgets.QCheckBox):
	def __init__(self, nuke_knob=''):
		super(Knob_Boolean, self).__init__()

		# Instance ID
		self.nuke_knob = nuke_knob
		self.Class = 'Knob_Boolean'

		# Instance properties
		self.stateChanged.connect(self.onChanged)

	def set_value(self, v):
		self.node = self.parent().title()
		self.setText(nuke.toNode(self.node)[self.nuke_knob].label())
		
		_state = QtCore.Qt.Checked if v == True else QtCore.Qt.Unchecked
		self.setCheckState(_state)

	def onChanged(self):

		# change nuke knob value
		_state = sender().checkState()
		_v = True if _state is QtCore.Qt.Checked else False
		set_nuke_knob(self, self.nuke_knob, _v)


class Knob_PyScript(QtWidgets.QPushButton):
	def __init__(self, nuke_knob=''):
		super(Knob_PyScript, self).__init__()

		# Instance ID
		self.nuke_knob = nuke_knob
		self.Class = 'Knob_PyScript'

		# Instance properties


class Knob_Channel(QtWidgets.QComboBox):
	def __init__(self, nuke_knob=''):
		super(Knob_Channel, self).__init__()
		
		# Instance ID
		self.nuke_knob = nuke_knob
		self.Class = 'Knob_Channel'

		# Instance properties


class Knob_Int(QtWidgets.QSpinBox):
	def __init__(self, nuke_knob=''):
		super(Knob_Enumeration, self).__init__()
		
		# Instance ID
		self.nuke_knob = nuke_knob
		self.Class = 'Knob_Int'

		# Instance properties


class Knob_WH(QtWidgets.QSlider):
	def __init__(self, nuke_knob=''):
		super(Knob_WH, self).__init__()

		# Instance ID
		self.nuke_knob = nuke_knob
		self.Class = 'Knob_WH'

		# Instance properties




#-------------------------------------------------------------------------------
#-Custom Widget Components (make up the Custom Widget qt_knob)
#-------------------------------------------------------------------------------




class Knob_Slider(QtWidgets.QSlider):
	def __init__(self, nuke_knob=''):
		super(Knob_Slider, self).__init__(QtCore.Qt.Horizontal)

		# Instance ID
		self.Class = 'Knob_Slider'
		self.PRECISION = 10000.0000

		# Instance properties
		self.setRange(-6*self.PRECISION,6*self.PRECISION)
		self.setMinimumWidth(250)

	def set_value(self, v):
		'''sets value and convert to int'''
		self.setValue(int(v*self.PRECISION))

	def get_value(self):
		'''get value and covert to float'''
		_v = float(self.value()/self.PRECISION)
		return _v
		

class Knob_EditBox(QtWidgets.QDoubleSpinBox):
	def __init__(self, nuke_knob=''):
		super(Knob_EditBox, self).__init__()

		# Instance ID
		self.nuke_knob = nuke_knob+"_editbox"
		self.Class = 'Knob_EditBox'

		# Instance properties
		self.setSingleStep(0.0001)
		self.setDecimals(4)
		self.setRange(-10000.0000, 10000.0000)
		self.setFixedSize(72,20)
		self.setButtonSymbols(self.NoButtons)

	def set_value(self, v):
		'''sets value'''
		self.setValue(float(v))

	def get_value(self):
		'''get value'''
		return self.value()
	


class Knob_DoubleSpin(QtWidgets.QDoubleSpinBox):
	def __init__(self, nuke_knob=''):
		super(Knob_DoubleSpin, self).__init__()

		# Instance ID
		self.nuke_knob = nuke_knob+'doublespin'
		self.Class = 'Knob_DoubleSpin'
		
		# Instance properties
		self.setMaximumWidth(72)
		self.setSingleStep(0.0001)
		self.setDecimals(4)
		self.setRange(-10000000,10000000)

	def get_value(self):
		return self.value()






#-------------------------------------------------------------------------------
#-Instancing
#-------------------------------------------------------------------------------




HoverValue = Core_HoverValue()




#-------------------------------------------------------------------------------
#-Notes
#-------------------------------------------------------------------------------




'''

Nodes: knobs (class)
Summerized Knob Classes: WH_Knob, AColor_Knob, Array_Knob, XY_Knob, Enumeration_Knob

Blur: size
Grade: blackpoint, whitepoint, lift, gain, multiply, offset, gamma
Dilate: size
Saturation: saturation, mode
Defocus: defocus, aspect ratio
ZDefocus: center, dof, size, max_size
Multiply: value
Transform: translate, rotate, scale


knobs - QtWidgets

String_Knob - QLineEdit
File_Knob - QLineEdit, QPushbutton
Array_Knob - QSlider
Boolean_Knob - QCheckBox
Channel_Knob - QComboBox
Enumeration_Knob - QComboBox
PyScript_Knob - QPushbutton
Int_Knob - QSpinBox
XY_Knob - QDoubleSpinBox, QDoubleSpinBox
'''


def get_knobInfo():
	'''get the name, label, class and cooresponding Qt widget of a node and knob
	
	return:
		NodeClass
		<knob_name>: <knob label>, <KNOB_Class>, <QtWidget>, ...
	
	'''

	for n in nuke.selectedNodes():
		thisNodeClass = n.Class()

		print '\n\n', thisNodeClass, '\n'
		
		if thisNodeClass in KNOBS_NK.keys():
			for k in KNOBS_NK[thisNodeClass]:
				thisType = ""
				thisKnobClass = n.knob(k).Class()
				thisKnobLabel = n.knob(k).label() if n.knob(k).label() else k
				if k in KNOBS_NK[thisNodeClass]:
					thisType = "\t%s: %s, %s, %s" % (k, thisKnobLabel, thisKnobClass, ', '.join(KNOBS_QT[thisKnobClass]))
		
					print thisType




'''

NodeClass
	<knob_name>: <knob label>, <KNOB_Class>, <QtWidget>, ...

--------------------



Transform 

	translate: translate, XY_Knob, QDoubleSpinBox, QDoubleSpinBox
	rotate: rotate, Double_Knob, QSlider
	scale: scale, WH_Knob, QSlider


Multiply 

	value: value, AColor_Knob, QSlider


ZDefocus2 

	center: focus plane (C), Array_Knob, QSlider
	dof: depth of field, Array_Knob, QSlider
	size: size, WH_Knob, QSlider
	max_size: maximum, WH_Knob, QSlider


Defocus 

	defocus: defocus, Array_Knob, QSlider
	ratio: aspect ratio, Array_Knob, QSlider


Blur 

	size: size, WH_Knob, QSlider


Dilate 

	size: size, WH_Knob, QSlider


Saturation 

	saturation: saturation, Array_Knob, QSlider
	mode: luminance math, Enumeration_Knob, QComboBox


Grade 

	blackpoint: blackpoint, AColor_Knob, QSlider
	whitepoint: whitepoint, AColor_Knob, QSlider
	black: lift, AColor_Knob, QSlider
	white: gain, AColor_Knob, QSlider
	multiply: multiply, AColor_Knob, QSlider
	add: offset, AColor_Knob, QSlider
	gamma: gamma, AColor_Knob, QSlider


'''


class TestClass(QtWidgets.QDialog):
	'''for testing out custom widgets'''
	def __init__(self):
		super(TestClass, self).__init__()

		# Widgets
		self.testWidgetA = Knob_XY(nuke_knob='size')
		self.testWidgetB = Knob_Array(nuke_knob='blackpoint')


		# Layout
		self.layout_master = QtWidgets.QVBoxLayout()
		self.layout_master.addWidget(self.testWidgetA)
		self.layout_master.addWidget(self.testWidgetB)


		self.resize(500,100)
		self.setLayout(self.layout_master)
		self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Popup)

		self.setDefaults()


	def setDefaults(self):
		'''sets default values'''

		pass

	def run(self):
		self.show()

TestWidget = TestClass()