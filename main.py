import os
import sys
import wmi
import json
import time
import psutil
import GPUtil
import winreg
import cpuinfo
import platform
import webbrowser
import subprocess
from pprint import pprint
import config as config_file
from collections import deque
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# IF NVIDIA AVALIABLE
try:
	import pynvml
	pynvml.nvmlInit()
	NVML_AVAILABLE = True
except Exception:
	NVML_AVAILABLE = False
	
def build_stylesheet():
	return f"""
	QWidget#root {{
		background-color: {theme.background()};
		color: {theme.text()};
		font-size: 13px;
	}}
	QTabBar::tab {{
		background: {theme.surface()};
		border: 1px solid {theme.border()};
		padding: 6px 12px;
		border-radius: 6px;
		margin: 2px;
	}}
	QTabWidget::pane {{
		border: none;
		background: {theme.background()};
	}}
	QWidget {{
		background-color: {theme.background()};
		color: {theme.text()};
	}}

	QGroupBox {{
		background: {theme.surface()};
		border: 1px solid {theme.border()};
		border-radius: 10px;
		margin-top: 12px;
		padding: 14px;
		font-weight: 600;
		color: {theme.text()};
	}}

	QGroupBox::title {{
		subcontrol-origin: margin;
		left: 12px;
		padding: 0 6px;
		color: {theme.text_secondary()};
	}}

	QLabel {{
		color: {theme.text()};
	}}

	QPushButton {{
		background: {theme.accent};
		color: black;
		border-radius: 8px;
		padding: 6px 12px;
		font-weight: bold;
	}}

	QPushButton:hover {{
		background: {theme.accent_hover()};
	}}

	QComboBox {{
		background: {theme.surface()};
		border: 1px solid {theme.border()};
		border-radius: 6px;
		padding: 6px;
		color: {theme.text()};
	}}

	QComboBox:hover {{
		border: 1px solid {theme.accent};
	}}

	QComboBox QAbstractItemView {{
		background: {theme.surface()};
		color: {theme.text()};
		border: 1px solid {theme.border()};
	}}

	QTabBar::tab {{
		background: {theme.surface()};
		padding: 6px 12px;
		border: 1px solid {theme.border()};
	}}

	QTabBar::tab:selected {{
		background: {theme.background()};
		color: {theme.accent};
		font-weight: bold;
	}}
	"""

class LanguageManager:
	def __init__(self):
		self.translations = {}
		self.current_language = config_file.default_lang
		self.load_config()

	def load_config(self):
		if os.path.exists(resource_path("files/config.json")):
			try:
				with open(resource_path("files/config.json"), "r", encoding="utf-8") as f:
					config = json.load(f)
					self.current_language = config.get("language", "pt")
			except:
				self.current_language = "pt"
		self.load_language(self.current_language)

	def save_config(self):
		with open(resource_path("files/config.json"), "w", encoding="utf-8") as f:
			json.dump({"language": self.current_language}, f, indent=4)

	def load_language(self, lang_code):
		try:
			arq = resource_path(f"languages/{lang_code}.json")
			with open(arq, "r", encoding="utf-8") as f:
				self.translations = json.load(f)
				self.current_language = lang_code
				self.save_config()
		except:
			self.translations = {}

	def t(self, key):
		return self.translations.get(key, key)

lang = LanguageManager()
c    = wmi.WMI()

class ThemeManager:
	def __init__(self):
		self.file = "theme.json"
		self.theme = "dark"
		self.accent = "#4fc3f7"
		self.load()

	def load(self):
		if os.path.exists(self.file):
			try:
				data = json.load(open(self.file))
				self.theme = data.get("theme", "dark")
				self.accent = data.get("accent", "#4fc3f7")
			except:
				pass

	def save(self):
		json.dump({
			"theme": self.theme,
			"accent": self.accent
		}, open(self.file, "w"), indent=4)

	def background(self):
		return "#121212" if self.theme == "dark" else "#eef1f4"

	def surface(self):
		return "#1b1b1b" if self.theme == "dark" else "#ffffff"

	def text(self):
		return "#ffffff" if self.theme == "dark" else "#1f2328"

	def text_secondary(self):
		return "#b0b0b0" if self.theme == "dark" else "#57606a"

	def border(self):
		return "#3a3a3a" if self.theme == "dark" else "#d8dee4"

	def lighter(self, color, factor=1.2):
		c = QColor(color)
		return c.lighter(int(factor * 100)).name()

	def darker(self, color, factor=1.2):
		c = QColor(color)
		return c.darker(int(factor * 100)).name()

	def card_shadow(self):
		if self.theme == "dark":
			return "none"
		else:
			return "0px 2px 6px rgba(0,0,0,0.08)"

	def text_secondary(self):
		return "#b0b0b0" if self.theme == "dark" else "#57606a"

	def accent_hover(self):
		# versão levemente mais clara da accent
		from PyQt6.QtGui import QColor
		color = QColor(self.accent)
		return color.lighter(120).name()
	
	@property
	def accent_pressed(self):
		return self.darker(self.accent, 1.25)

theme = ThemeManager()

class AccentButton(QPushButton):
	def __init__(self, text=""):
		super().__init__(text)
		self.update_style()

	def update_style(self):
		self.setStyleSheet(f"""
			QPushButton {{
				background-color: {theme.accent};
				color: white;
				border-radius: 6px;
				padding: 8px 14px;
				font-weight: bold;
			}}

			QPushButton:hover {{
				background-color: {theme.accent_hover};
			}}

			QPushButton:pressed {{
				background-color: {theme.accent_pressed};
			}}
		""")

def refresh_accent_colors(widget):
	for child in widget.findChildren(AccentLabel):
		child.update_color()

def apply_theme(app):
	app.setStyleSheet(build_stylesheet())
	refresh_accent_colors(app.activeWindow())

class AccentLabel(QLabel):
	def __init__(self, text=""):
		super().__init__(text)
		self.update_color()

	def update_color(self):
		self.setStyleSheet(f"""
			color: {theme.accent};
			font-weight: bold;
			border: none;
		""")

def blue_label(text=""):
	return AccentLabel(text)

# CPU TAB
def detect_generation(cpu_name):
	cpu_name = cpu_name.lower()

	# INTEL
	if "intel" in cpu_name:

		import re
		match = re.search(r'i[3579]-?(\d{4,5})', cpu_name)

		if match:
			number = match.group(1)
			if len(number) == 4:
				gen = int(number[0])
			else:  # 5 dígitos (10ª gen+)
				gen = int(number[:2])
			return f"{gen}th Gen"

		if "ultra" in cpu_name:
			return "Intel Core Ultra (Meteor Lake)"

		return lang.t("unknown_processor_intel")

	# AMD
	if "ryzen" in cpu_name:

		import re
		match = re.search(r'ryzen\s+\d\s+(\d{4})', cpu_name)

		if match:
			gen = match.group(1)[0]
			return f"Ryzen {gen}000 Series"
		return lang.t("unknown_processor_ryzen")

	return lang.t("unknown")

def detect_cpu_info(cpu_name):
	name = cpu_name.lower()
	# INTEL
	if "intel" in name:
		if " i" in name:
			try:
				model = name.split("-")[1]
			except:
				return (lang.t("unknown"), lang.t("unknown"), lang.t("unknown"))

			# Geração por número
			if model.startswith(("2", "3")):
				return ("Sandy Bridge", "32 nm", "LGA1155")
			if model.startswith("4"):
				return ("Haswell", "22 nm", "LGA1150")
			if model.startswith("5"):
				return ("Broadwell", "14 nm", "LGA1150")
			if model.startswith("6"):
				return ("Skylake", "14 nm", "LGA1151")
			if model.startswith("7"):
				return ("Kaby Lake", "14 nm", "LGA1151")
			if model.startswith("8"):
				return ("Coffee Lake", "14 nm", "LGA1151")
			if model.startswith("9"):
				return ("Coffee Lake Refresh", "14 nm", "LGA1151")
			if model.startswith("10"):
				return ("Comet Lake", "14 nm", "LGA1200")
			if model.startswith("11"):
				return ("Rocket Lake", "14 nm", "LGA1200")
			if model.startswith("12"):
				return ("Alder Lake", "Intel 7 (10nm)", "LGA1700")
			if model.startswith("13"):
				return ("Raptor Lake", "Intel 7 (10nm)", "LGA1700")
			if model.startswith("14"):
				return ("Raptor Lake Refresh", "Intel 7", "LGA1700")

		# Xeon
		if "xeon" in name:
			return ("Xeon Series", "Varies", "Server Socket")
		
		# Pentium / Celeron 
		if "pentium" in name or "celeron" in name:
			return ("Pentium/Celeron", "14 nm", "LGA1151")

		return ("Intel CPU", "Unknown", "Unknown")

	# AMD RYZEN
	if "amd" in name:
		if "ryzen" in name:
			try:
				model = name.split(" ")[-1]
			except:
				return ("Ryzen", "Unknown", "AM4")

			if model.startswith("1"):
				return ("Zen (Ryzen 1000)", "14 nm", "AM4")
			if model.startswith("2"):
				return ("Zen+ (Ryzen 2000)", "12 nm", "AM4")
			if model.startswith("3"):
				return ("Zen 2 (Ryzen 3000)", "7 nm", "AM4")
			if model.startswith("4"):
				return ("Zen 2 APU (Ryzen 4000)", "7 nm", "AM4")
			if model.startswith("5"):
				return ("Zen 3 (Ryzen 5000)", "7 nm", "AM4")
			if model.startswith("6"):
				return ("Zen 3+ (Ryzen 6000)", "6 nm", "AM5")
			if model.startswith("7"):
				return ("Zen 4 (Ryzen 7000)", "5 nm", "AM5")
			if model.startswith("8"):
				return ("Zen 4/5 (Ryzen 8000)", "4-5 nm", "AM5")

		if "threadripper" in name:
			return ("Threadripper", "Varies", "sTRX4 / TR4")

		if "epyc" in name:
			return ("EPYC", "Varies", "SP3/SP5")

		if "fx" in name:
			return ("Bulldozer / Piledriver", "32 nm", "AM3+")

		return ("AMD CPU", "Unknown", "Unknown")

	return ("Unknown CPU", "Unknown", "Unknown")

# CPU TAB
class CPUTab(QWidget):
	def __init__(self):
		super().__init__()

		root_layout = QHBoxLayout()

		# LEFT SIDE (ALL CPU DATA)

		main_layout = QVBoxLayout()

		cpu = cpuinfo.get_cpu_info()

		try:
			win_cpu = c.Win32_Processor()[0]
		except:
			win_cpu = None

		self.cpu_data = {}

		name    = cpu.get("brand_raw", lang.t("unknown"))
		cores   = psutil.cpu_count(logical=False)
		threads = psutil.cpu_count()

		codename, technology, socket = detect_cpu_info(name)
		generation = detect_generation(name)

		family   = cpu.get("family", "N/A")
		model    = cpu.get("model", "N/A")
		stepping = cpu.get("stepping", "N/A")

		freq       = psutil.cpu_freq()
		max_freq   = freq.max if freq else "N/A"
		base_clock = win_cpu.MaxClockSpeed if win_cpu else "N/A"

		# ================= PROCESSOR PROPERTIES =================
		prop_group = QGroupBox(lang.t("tab_processor"))
		prop_group.setProperty("profile", True)

		prop_layout = QGridLayout()
		row = 0

		prop_layout.addWidget(QLabel(lang.t("name")), row, 0)
		prop_layout.addWidget(blue_label(name), row, 1, 1, 5)
		row += 1

		prop_layout.addWidget(QLabel(lang.t("generation")), row, 0)
		prop_layout.addWidget(blue_label(f"{generation} ({codename})"), row, 1, 1, 5)
		row += 1

		prop_layout.addWidget(QLabel(lang.t("socket")), row, 0)
		prop_layout.addWidget(blue_label(str(socket)), row, 1, 1, 5)
		row += 1

		prop_layout.addWidget(QLabel(lang.t("cores")), row, 0)
		prop_layout.addWidget(blue_label(str(cores)), row, 1)

		prop_layout.addWidget(QLabel("Threads:"), row, 2)
		prop_layout.addWidget(blue_label(str(threads)), row, 3)
		row += 1

		prop_layout.addWidget(QLabel(lang.t("family")), row, 0)
		prop_layout.addWidget(blue_label(str(family)), row, 1)

		prop_layout.addWidget(QLabel(lang.t("model")), row, 2)
		prop_layout.addWidget(blue_label(str(model)), row, 3)

		prop_layout.addWidget(QLabel(lang.t("stepping")), row, 4)
		prop_layout.addWidget(blue_label(str(stepping)), row, 5)

		prop_group.setLayout(prop_layout)
		main_layout.addWidget(prop_group)

		clocks_group = QGroupBox(lang.t("clocks"))
		clocks_group.setProperty("profile", True)
		clocks_layout = QGridLayout()

		self.base_clock_label = blue_label(f"{base_clock} MHz")
		self.max_clock_label = blue_label(f"{max_freq} MHz")
		self.current_clock_label = blue_label("...")

		clocks_layout.addWidget(QLabel(lang.t("base_clock")), 0, 0)
		clocks_layout.addWidget(self.base_clock_label, 0, 1)

		clocks_layout.addWidget(QLabel(lang.t("max_clock")), 1, 0)
		clocks_layout.addWidget(self.max_clock_label, 1, 1)

		clocks_layout.addWidget(QLabel(lang.t("speed_clock")), 2, 0)
		clocks_layout.addWidget(self.current_clock_label, 2, 1)

		clocks_group.setLayout(clocks_layout)

		usage_group = QGroupBox(lang.t("use"))
		usage_group.setProperty("profile", True)

		usage_layout = QGridLayout()
		self.usage_label = blue_label("0 %")

		usage_layout.addWidget(QLabel(lang.t("cpu_in_use")), 0, 0)
		usage_layout.addWidget(self.usage_label, 0, 1)

		usage_group.setLayout(usage_layout)

		main_layout.addWidget(clocks_group)
		main_layout.addWidget(usage_group)

		self.export_btn = QPushButton(lang.t("export_data_in_json"))
		self.export_btn.clicked.connect(self.export_json)
		main_layout.addWidget(self.export_btn)
		main_layout.addStretch()

		frame = QFrame()
		frame.setFixedSize(160, 160)
		frame.setProperty("profile", True)

		frame_layout = QVBoxLayout()
		frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

		logo_label = QLabel()
		logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		logo_label.setFixedSize(130, 130)

		name_lower = name.lower()

		if "intel" in name_lower:
			img_path = resource_path("files/images/intel.png")
		elif "amd" in name_lower and "ryzen" not in name_lower:
			img_path = resource_path("files/images/amd.png")
		elif "ryzen" in name_lower:
			img_path = resource_path("files/images/ryzen.jpg")
		else:
			img_path = resource_path("files/images/cpu.png")

		pixmap = QPixmap(img_path)

		if not pixmap.isNull():
			logo_label.setPixmap(
				pixmap.scaled(
					120,
					120,
					Qt.AspectRatioMode.KeepAspectRatio,
					Qt.TransformationMode.SmoothTransformation
				)
			)

		frame_layout.addWidget(logo_label)
		frame.setLayout(frame_layout)

		root_layout.addLayout(main_layout)
		root_layout.addWidget(frame, alignment=Qt.AlignmentFlag.AlignTop)

		self.setLayout(root_layout)

		self.timer = QTimer()
		self.timer.timeout.connect(self.update_dynamic)
		self.timer.start(1000)

	# UPDATE
	def update_dynamic(self):
		freq = psutil.cpu_freq()
		usage = psutil.cpu_percent()

		if freq:
			speed = f"{freq.current:.2f} MHz"
			self.current_clock_label.setText(speed)
			self.cpu_data["Core Speed"] = speed

		usage_value = int(usage)
		usage_text = f"{usage_value} %"

		self.usage_label.setText(usage_text)
		self.cpu_data["CPU Usage"] = usage_text

		if usage_value < 40:
			color = "#4fc3f7"
		elif usage_value <= 80:
			color = "#ffd54f"
		else:
			color = "#ff5252"

		self.usage_label.setStyleSheet(f"color:{color};font-weight:bold;")

	# EXPORT
	def export_json(self):
		file_name, _ = QFileDialog.getSaveFileName(
			self,
			"Save Processor Data",
			"processor_data.json",
			"JSON Files (*.json)"
		)

		if file_name:
			with open(file_name, "w") as f:
				json.dump(self.cpu_data, f, indent=4)

# MAINBOARD
class MainboardTab(QWidget):
	def __init__(self):
		super().__init__()

		main_layout = QVBoxLayout()
		w = wmi.WMI()

		# MOTHERBOARD GROUP

		mb_group = QGroupBox(lang.t("motherboard"))
		mb_group.setProperty("profile", True)
		mb_layout = QGridLayout()

		try:
			board = w.Win32_BaseBoard()[0]
			manufacturer = board.Manufacturer
			model = board.Product
		except:
			manufacturer = "N/A"
			model = "N/A"

		try:
			cpu = w.Win32_Processor()[0]
			bus = f"{cpu.ExtClock} MHz"
		except:
			bus = "N/A"

		mb_data = [
			(lang.t("manufacture"), manufacturer),
			(lang.t("model"), model),
			(lang.t("bus_specs"), bus),
			(lang.t("chipset"), lang.t("chipset_value")),
			(lang.t("southbridge"), lang.t("southbridge_value")),
			(lang.t("lpcio"), lang.t("no_access")),
		]

		for i, (label, value) in enumerate(mb_data):
			mb_layout.addWidget(QLabel(label + ":"), i, 0)
			mb_layout.addWidget(blue_label(str(value)), i, 1)

		mb_group.setLayout(mb_layout)
		main_layout.addWidget(mb_group)

		# LOWER SECTION (BIOS + GRAPHICS)

		lower_layout = QVBoxLayout()

		# BIOS
		bios_group = QGroupBox(lang.t("bios"))
		mb_group.setProperty("profile", True)
		bios_layout = QGridLayout()

		try:
			bios = w.Win32_BIOS()[0]
			brand = bios.Manufacturer
			version = bios.SMBIOSBIOSVersion
			raw_date = bios.ReleaseDate[:8]

			if len(raw_date) == 8:
				date = f"{raw_date[6:8]}/{raw_date[4:6]}/{raw_date[0:4]}"
			else:
				date = "N/A"
		except:
			brand = version = date = "N/A"

		try:
			key = winreg.OpenKey(
				winreg.HKEY_LOCAL_MACHINE,
				r"HARDWARE\DESCRIPTION\System\\CentralProcessor\0"
			)
			microcode, _ = winreg.QueryValueEx(key, "Update Revision")
			microcode = hex(microcode)
		except:
			microcode = "N/A"

		bios_data = [
			(lang.t("brand"), brand),
			(lang.t("version"), version),
			(lang.t("date"), date),
			(lang.t("microcode"), microcode),
		]

		for i, (label, value) in enumerate(bios_data):
			bios_layout.addWidget(QLabel(label), i, 0)
			bios_layout.addWidget(blue_label(str(value)), i, 1)

		bios_group.setLayout(bios_layout)

		# GRAPHICS
		graphics_group = QGroupBox(lang.t("graphics"))
		graphics_group.setProperty("profile", True)
		graphics_layout = QGridLayout()

		try:
			gpu = w.Win32_VideoController()[0]
			bus = "PCI Express"
		except:
			bus = "N/A"

		graphics_data = [
			(lang.t("bus"), bus),
			(lang.t("gpu_larg"), "x16 (Assumed)"),
			(lang.t("gpu_max"), "x16"),
			(lang.t("gpu_speed_now"), lang.t("gpu_speed_now2")),
			(lang.t("gpu_speed_max"), lang.t("gpu_speed_max2")),
		]

		for i, (label, value) in enumerate(graphics_data):
			graphics_layout.addWidget(QLabel(label), i, 0)
			graphics_layout.addWidget(blue_label(str(value)), i, 1)

		graphics_group.setLayout(graphics_layout)

		lower_layout.addWidget(bios_group)
		lower_layout.addWidget(graphics_group)
		main_layout.addLayout(lower_layout)

		self.setLayout(main_layout)

def get_real_ram_info_slots():
	ddr_map  = config_file.ddr_map
	ram_data = {
		"total_size_gb": 0,
		"total_speed_mhz": 0,
		"total_channels": lang.t("unknown"),
		"slots": []
	}

	try:
		modules = c.Win32_PhysicalMemory()
		total_size = 0
		speeds = []

		for mem in modules:
			slot_info = {}
			capacity = int(mem.Capacity) if mem.Capacity else 0
			total_size += capacity

			speed = int(mem.Speed) if getattr(mem, "Speed", None) else 0
			speeds.append(speed)

			mem_type = ddr_map.get(getattr(mem, "SMBIOSMemoryType", 0), lang.t("unknown"))
			manufacturer = getattr(mem, "Manufacturer", lang.t("unknown"))

			slot_info["manufacturer"] = manufacturer
			slot_info["capacity_gb"] = round(capacity / (1024**3), 2)
			slot_info["speed_mhz"] = speed
			slot_info["type"] = mem_type
			slot_info["part_number"] = getattr(mem, "PartNumber", "N/A")
			slot_info["serial_number"] = getattr(mem, "SerialNumber", "N/A")

			ram_data["slots"].append(slot_info)

		ram_data["total_size_gb"] = round(total_size / (1024**3), 2)
		ram_data["total_speed_mhz"] = max(speeds) if speeds else 0

		# Detect channels
		if len(modules) >= 2:
			if len(set([slot["capacity_gb"] for slot in ram_data["slots"]])) == 1:
				ram_data["total_channels"] = "Dual"
			else:
				ram_data["total_channels"] = "Multi"
		else:
			ram_data["total_channels"] = "Single"

	except Exception as e:
		print(lang.t("error_get_ram_info"), e)

	return ram_data

def get_real_ram_info():
	modules = []
	total_capacity = 0
	speeds = []
	speeds2 = []
	mem_type = None

	ram_info = {
		"size": 0,
		"type": lang.t("unknown"),
		"manufacturer": lang.t("unknown"),
		"speed": 0,
		"channel": lang.t("unknown")
	}

	try:
		modules = c.Win32_PhysicalMemory()
		total_size = 0
		manufacturers = set()
		speeds2 = set()

		for mem in modules:
			total_size += int(mem.Capacity)
			manufacturers.add(getattr(mem, "Manufacturer", lang.t("unknown")))
			speeds2.add(getattr(mem, "Speed", 0))

		ram_info["size"] = total_size / (1024**3)  # GBytes
		ram_info["manufacturer"] = ", ".join(manufacturers)
		ram_info["speed"] = max(speeds2) if speeds2 else 0
		ram_info["type"] = getattr(modules[0], "MemoryType", lang.t("unknown"))

		arrays = c.Win32_PhysicalMemoryArray()
		if arrays:
			ram_info["channel"] = f"{getattr(arrays[0], 'MemoryDevices', 0)} Modules"
		else:
			ram_info["channel"] = f"{len(modules)} Modules"

	except Exception as e:
		print(lang.t("error_get_ram_info"), e)

	ddr_map  = config_file.ddr_map

	for mem in c.Win32_PhysicalMemory():
		capacity = int(mem.Capacity)
		total_capacity += capacity

		speeds.append(int(mem.Speed) if mem.Speed else 0)

		if mem.SMBIOSMemoryType in ddr_map:
			mem_type = ddr_map[mem.SMBIOSMemoryType]

		modules.append(capacity)

	total_gb = total_capacity / (1024**3)

	# Detecta channel básico
	channel = "Single"
	if len(modules) >= 2:
		if len(set(modules)) == 1:
			channel = "Dual"
		else:
			channel = "Multi"

	speed = max(speeds) if speeds else 0

	return {
		"info": ram_info,
		"type": mem_type if mem_type else lang.t("unknown"),
		"size": total_gb,
		"channel": channel,
		"speed": speed
	}

def get_dynamic_timings():
	timings = {
		"mem_dram_freq": 0,
		"mem_fsb_dram": "0:0",
		"mem_command_rate": "2T"  # fixo
	}
	try:
		for mem in c.Win32_PhysicalMemory():
			# Frequência DRAM real (MHz)
			timings["mem_dram_freq"] = getattr(mem, "ConfiguredClockSpeed", 0)
			# FSB:DRAM ratio aproximado
			try:
				timings["mem_fsb_dram"] = f"1:{max(1, int(int(timings['mem_dram_freq']) / 100))}"
			except:
				timings["mem_fsb_dram"] = "N/A"
			break  # pega só o primeiro módulo
	except Exception as e:
		print(lang.t("error_get_timming_info"), e)

	return timings

# MemoryTab
class MemoryTab(QWidget):
	def __init__(self):
		super().__init__()
		main_layout = QVBoxLayout()

		self.ram_info = get_real_ram_info()
		self.ram_info_slots = get_real_ram_info_slots()

		self.general_group = QGroupBox()
		self.general_group.setProperty("profile", True)

		general_grid = QGridLayout()
		
		self.type_label = QLabel()
		self.type_value = blue_label()
		
		self.size_label = QLabel()
		self.size_value = blue_label()

		self.channel_label = QLabel()
		self.channel_value = blue_label(self.ram_info_slots["total_channels"])
		
		general_grid.addWidget(self.type_label, 0, 0)
		general_grid.addWidget(self.type_value, 0, 1)
		general_grid.addWidget(self.channel_label, 1, 0)
		general_grid.addWidget(self.channel_value, 1, 1)
		general_grid.addWidget(self.size_label, 2, 0)
		general_grid.addWidget(self.size_value, 2, 1)

		self.general_group.setLayout(general_grid)
		self.timing_group = QGroupBox()
		self.timing_group.setProperty("profile", True)
		timing_grid = QGridLayout()

		self.timing_labels = []
		self.timing_values = []
		timing_keys = [
			"mem_dram_freq",
			"mem_fsb_dram",
			"mem_command_rate"
		]

		for key in timing_keys:
			label = QLabel()
			value = blue_label()
			if key in ["mem_dram_freq"]:
				key_display = f"{key} MHz"
			elif key in ["mem_cas","mem_trcd","mem_trp","mem_tras","mem_trc"]:
				key_display = f"{key} Clocks"
				value.setText("N/A")
			else:
				key_display = key
			label.setText(key_display)
			self.timing_labels.append(label)
			self.timing_values.append(value)
			timing_grid.addWidget(label, len(self.timing_labels)-1, 0)
			timing_grid.addWidget(value, len(self.timing_values)-1, 1)

		self.timing_group.setLayout(timing_grid)

		# ADD GROUPS
		main_layout.addWidget(self.general_group)
		main_layout.addWidget(self.timing_group)
		main_layout.addStretch()
		self.setLayout(main_layout)

		self.apply_language()
		self.update_memory()

		# TIMER
		self.timer = QTimer()
		self.timer.timeout.connect(self.update_memory)
		self.timer.start(1000)

	def update_memory(self):
		mem = psutil.virtual_memory()
		info = self.ram_info

		total_gb = info["size"]
		used_gb = mem.used / (1024**3)
		available_gb = mem.available / (1024**3)
		ram_type = info["type"]
		channel = info["channel"]

		self.type_value.setText(f"{ram_type} ({channel})")
		self.size_value.setText(
			f"{total_gb:.0f} GBytes "
			f"(Used {used_gb:.2f} GB / {mem.percent}% | Free {available_gb:.2f} GB)"
		)

		dynamic_timings = get_dynamic_timings()
		self.timing_values[0].setText(f"{dynamic_timings['mem_dram_freq']} MHz")
		self.timing_values[1].setText(dynamic_timings['mem_fsb_dram'])
		self.timing_values[2].setText(dynamic_timings['mem_command_rate'])

	def apply_language(self):
		self.general_group.setTitle(lang.t("mem_general"))
		self.timing_group.setTitle(lang.t("mem_timings"))
		self.type_label.setText(lang.t("mem_type"))
		self.size_label.setText(lang.t("mem_size"))
		self.channel_label.setText(lang.t("mem_channel"))

		timing_keys = [
			"mem_dram_freq",
			"mem_fsb_dram",
			"mem_command_rate"
		]

		for label, key in zip(self.timing_labels, timing_keys):
			ending = ""
			if key == 'mem_dram_freq':
				ending = " MHz"
				label.setText(lang.t(key + ending))
				continue
			if key in ["mem_cas","mem_trcd","mem_trp","mem_tras","mem_trc"]:
				ending = " Clocks"
				label.setText(lang.t(key + ending))
				continue
			label.setText(lang.t(key + ending))

# SPD TAB
class SPDTab(QWidget):
	def __init__(self):
		super().__init__()
		layout = QVBoxLayout()
		layout.setSpacing(10)

		group = QGroupBox(lang.t("spd_title"))
		group.setProperty("profile", True)
		group_layout = QVBoxLayout()
		group.setLayout(group_layout)

		try:
			ram_modules = c.Win32_PhysicalMemory()
			grid_layout = QGridLayout()
			grid_layout.setSpacing(10)

			if not ram_modules:
				group_layout.addWidget(QLabel(lang.t("no_ram_error")))
			else:
				for i, mem in enumerate(ram_modules):
					card = QGroupBox(f"Slot {i+1}: {getattr(mem, 'DeviceLocator', lang.t("unknown"))}")
					card.setProperty("profile", True)
					card_layout = QGridLayout()

					attrs = {
						lang.t("bank_label"): getattr(mem, "BankLabel", "N/A"),
						lang.t("device_locator"): getattr(mem, "DeviceLocator", "N/A"),
						lang.t("manufacture"): getattr(mem, "Manufacturer", "N/A"),
						lang.t("serial_number"): getattr(mem, "SerialNumber", "N/A"),
						lang.t("capacity_in_gb"): round(int(getattr(mem, "Capacity", 0)) / (1024**3), 2),
						lang.t("speed_in_hz"): getattr(mem, "Speed", "N/A"),
						lang.t("config_clock_speed"): getattr(mem, "ConfiguredClockSpeed", "N/A"),
						lang.t("memory_type"): getattr(mem, "MemoryType", "N/A"),
						lang.t("smbios_type"): getattr(mem, "SMBIOSMemoryType", "N/A"),
						lang.t("form_factor"): getattr(mem, "FormFactor", "N/A"),
						lang.t("data_width"): getattr(mem, "DataWidth", "N/A"),
						lang.t("total_width"): getattr(mem, "TotalWidth", "N/A"),
						lang.t("voltage_set"): getattr(mem, "ConfiguredVoltage", "N/A"),
						lang.t("status"): getattr(mem, "Status", "N/A"),
						lang.t("tag"): getattr(mem, "Tag", "N/A")
					}

					row = 0
					for key, value in attrs.items():
						label_widget = QLabel(f"{key}:")
						label_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
						value_widget = blue_label(str(value))
						value_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

						card_layout.addWidget(label_widget, row, 0)
						card_layout.addWidget(value_widget, row, 1)
						row += 1

					card.setLayout(card_layout)

					grid_row = i // 2
					grid_col = i % 2
					grid_layout.addWidget(card, grid_row, grid_col)

				group_layout.addLayout(grid_layout)

		except Exception as e:
			group_layout.addWidget(QLabel(f"SPD not available: {e}"))

		layout.addWidget(group)
		layout.addStretch()
		self.setLayout(layout)


class GraphicsTab(QWidget):
	def __init__(self):
		super().__init__()

		layout = QVBoxLayout()
		layout.setSpacing(10)

		BASE_DIR = os.path.dirname(os.path.abspath(__file__))
		IMG_DIR = os.path.join(BASE_DIR, "files/images")

		group = QGroupBox(lang.t("tab_graphics"))
		group.setProperty("profile", True)

		group_layout = QVBoxLayout()
		group.setLayout(group_layout)

		try:
			gpus = GPUtil.getGPUs()

			grid_layout = QGridLayout()
			grid_layout.setSpacing(10)

			if not gpus:
				group_layout.addWidget(QLabel(lang.t("tab_graphics")))

			else:
				for i, gpu in enumerate(gpus):

					card = QGroupBox(f"GPU {i}: {gpu.name}")
					card.setProperty("profile", True)

					card_layout = QHBoxLayout()
					info_layout = QGridLayout()
					attrs = {
						lang.t("gpu_name"): gpu.name,
						"UUID": gpu.uuid,
						"GPU ID": gpu.id,
						lang.t("gpu_load"): round(gpu.load * 100, 2),
						lang.t("gpu_memory_total"): gpu.memoryTotal,
						lang.t("gpu_memory_used"): gpu.memoryUsed,
						lang.t("gpu_memory_free"): gpu.memoryFree,
						lang.t("gpu_memory_in_use"): round(
							(gpu.memoryUsed / gpu.memoryTotal) * 100, 2
						) if gpu.memoryTotal else "N/A",
						lang.t("temperacure"): gpu.temperature,
						lang.t("driver"): getattr(gpu, "driver", "N/A"),
						lang.t("display_active"): getattr(gpu, "display_active", "N/A"),
					}
					if NVML_AVAILABLE:
						try:
							handle = pynvml.nvmlDeviceGetHandleByIndex(i)

							mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
							util = pynvml.nvmlDeviceGetUtilizationRates(handle)
							power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000
							power_limit = (
								pynvml.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000
							)
							fan = pynvml.nvmlDeviceGetFanSpeed(handle)
							clocks_graphics = pynvml.nvmlDeviceGetClockInfo(
								handle,
								pynvml.NVML_CLOCK_GRAPHICS
							)
							clocks_mem = pynvml.nvmlDeviceGetClockInfo(
								handle,
								pynvml.NVML_CLOCK_MEM
							)

							attrs.update({
								lang.t("gpu_utilization"): util.gpu,
								lang.t("memory_controller"): util.memory,
								lang.t("power_usage"): round(power, 2),
								lang.t("power_limit"): round(power_limit, 2),
								lang.t("fan_speed"): fan,
								lang.t("graph_clock"): clocks_graphics,
								lang.t("memory_type_clock"): clocks_mem,
								lang.t("vram_used"): round(mem.used / 1024**2),
								lang.t("vram_free"): round(mem.free / 1024**2),
							})

						except Exception:
							pass
					row = 0
					for key, value in attrs.items():
						label_widget = QLabel(f"{key}:")
						label_widget.setAlignment(
							Qt.AlignmentFlag.AlignLeft |
							Qt.AlignmentFlag.AlignVCenter
						)

						value_widget = blue_label(str(value))
						info_layout.addWidget(label_widget, row, 0)
						info_layout.addWidget(value_widget, row, 1)
						row += 1

					card_layout.addLayout(info_layout)

					frame = QFrame()
					frame.setFixedSize(130, 130)
					frame.setProperty("profile", True)

					frame_layout = QVBoxLayout()
					frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

					logo_label = QLabel()
					logo_label.setFixedSize(100, 100)
					logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

					name = gpu.name.lower()

					if "nvidia" in name:
						img_path = resource_path("files/images/nvidia.png")
					elif "amd" in name or "radeon" in name:
						img_path = resource_path("files/images/amd.jpg")
					elif "intel" in name:
						img_path = resource_path("files/images/intel.png")
					else:
						img_path = resource_path("files/images/gpu.png")

					pixmap = QPixmap(img_path)

					if not pixmap.isNull():
						logo_label.setPixmap(
							pixmap.scaled(
								95,
								95,
								Qt.AspectRatioMode.KeepAspectRatio,
								Qt.TransformationMode.SmoothTransformation
							)
						)

					frame_layout.addWidget(logo_label)
					frame.setLayout(frame_layout)

					card_layout.addWidget(frame)

					card.setLayout(card_layout)

					grid_row = i // 2
					grid_col = i % 2
					grid_layout.addWidget(card, grid_row, grid_col)

				group_layout.addLayout(grid_layout)

		except Exception as e:
			group_layout.addWidget(QLabel(f"GPU info not available: {e}"))

		layout.addWidget(group)
		layout.addStretch()
		self.setLayout(layout)

class UsageGraph(QWidget):

	def __init__(self):
		super().__init__()
		self.values = [0]*60

	def add_value(self, v):
		self.values.append(v)
		self.values.pop(0)
		self.update()

	def reset(self):
		self.values = [0]*60
		self.update()

	def paintEvent(self, e):
		from PyQt6.QtGui import QPainter, QPen
		from PyQt6.QtCore import QPointF

		p = QPainter(self)
		p.setRenderHint(QPainter.RenderHint.Antialiasing)

		w = self.width()
		h = self.height()

		step = w/(len(self.values)-1)

		points = []

		for i,v in enumerate(self.values):
			x = i*step
			y = h - (v/100)*h
			points.append(QPointF(x,y))

		pen = QPen(QColor("#3daee9"),2)
		p.setPen(pen)

		for i in range(len(points)-1):
			p.drawLine(points[i],points[i+1])
class DeviceCard(QWidget):
    selected = pyqtSignal(str)

    def __init__(self, name, subtitle="", color="#00bcd4"):
        super().__init__()
        self.device_name = name
        self.selected_state = False

        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10,6,10,6)

        self.dot = QLabel()
        self.dot.setFixedSize(10,10)
        self.dot.setStyleSheet(f"background:{color};border-radius:5px;")

        text_layout = QVBoxLayout()
        self.title = QLabel(name)
        self.subtitle = QLabel(subtitle)
        self.subtitle.setStyleSheet("color:gray;font-size:11px;")
        text_layout.addWidget(self.title)
        text_layout.addWidget(self.subtitle)

        self.graph = UsageGraph()
        self.graph.setFixedSize(80,40)

        layout.addWidget(self.dot)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(self.graph)

        self.update_style()

    def update_style(self):
        if self.selected_state:
            self.setStyleSheet("background:#2a2a2a;border-radius:6px;")
        else:
            self.setStyleSheet("""
                QWidget:hover{
                    background:#202020;
                    border-radius:6px;
                }
            """)

    def set_selected(self, state):
        self.selected_state = state
        self.update_style()

    def mousePressEvent(self, e):
        self.selected.emit(self.device_name)

    def update_value(self, text, value):
        self.subtitle.setText(text)
        self.graph.add_value(value)

# =====================================
# BENCH TAB
# =====================================
class BenchTab(QWidget):
    def __init__(self):
        super().__init__()

        self.current_device = "CPU"
        self.cards = {}
        self.last_net = psutil.net_io_counters()
        self.last_disk = psutil.disk_io_counters()
        self.last_time = time.time()
        self.c = wmi.WMI()  # inicializa WMI

        main_layout = QHBoxLayout(self)

        # ---------------- SIDEBAR ----------------
        self.sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setSpacing(6)
        self.sidebar_layout.setContentsMargins(5,5,5,5)

        def add_card(name, color):
            card = DeviceCard(name, "", color)
            card.selected.connect(self.select_device)
            self.sidebar_layout.addWidget(card)
            self.cards[name] = card

        # cards fixos
        add_card("CPU", "#00bcd4")
        add_card("Memory", "#5c7cfa")
        add_card("Ethernet", "#ff6ec7")
        add_card("GPU", "#b197fc")

        # detectar discos e adicionar cards
        self.real_disks = []
        for i, disk in enumerate(self.c.Win32_DiskDrive()):
            name = disk.Model
            interface = disk.InterfaceType
            self.real_disks.append((name, interface))
            disk_card_name = f"Disk {i} ({name})"
            add_card(disk_card_name, "#ffa500")  # laranja para discos

        self.sidebar_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.sidebar_container)
        scroll.setFixedWidth(350)

        main_layout.addWidget(scroll)

        # ---------------- RIGHT PANEL ----------------
        right_layout = QVBoxLayout()
        self.title = QLabel("CPU")
        self.title.setStyleSheet("font-size:22px;font-weight:bold;")
        self.graph = UsageGraph()
        right_layout.addWidget(self.title)
        right_layout.addWidget(self.graph)

        # ===== INFO GRID =====
        self.info_grid = QGridLayout()
        self.info_grid.setSpacing(15)
        self.info_labels = {}

        def add_info(row, col, name):
            title = QLabel(name)
            title.setStyleSheet("color:gray;font-size:12px;")
            value = QLabel("-")
            value.setStyleSheet("font-size:14px;font-weight:bold;")
            self.info_grid.addWidget(title, row*2, col)
            self.info_grid.addWidget(value, row*2+1, col)
            self.info_labels[name] = value

        add_info(0,0,"Usage")
        add_info(0,1,"Speed")
        add_info(1,0,"Processes")
        add_info(1,1,"Threads")
        add_info(2,0,"Cores")
        add_info(2,1,"Logical")

        right_layout.addLayout(self.info_grid)
        main_layout.addLayout(right_layout)

        # ---------------- TIMER ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_usage)
        self.timer.start(1000)

    # =================================================
    def select_device(self, name):
        for card in self.cards.values():
            card.set_selected(False)
        self.cards[name].set_selected(True)
        self.current_device = name
        self.title.setText(name)
        self.graph.reset()

    # =================================================
    def update_usage(self):
        value = 0

        # ---------- SIDEBAR UPDATE ----------
        cpu = psutil.cpu_percent()
        freq = psutil.cpu_freq()
        self.cards["CPU"].update_value(
            f"{cpu}% {freq.current/1000:.2f} GHz",
            cpu
        )

        net = psutil.net_io_counters()
        up = (net.bytes_sent - self.last_net.bytes_sent)/1024
        down = (net.bytes_recv - self.last_net.bytes_recv)/1024
        self.cards["Ethernet"].update_value(
            f"S:{up:.0f} R:{down:.0f} KB/s",
            min(100,(up+down)/50)
        )
        self.last_net = net

        mem = psutil.virtual_memory()
        self.cards["Memory"].update_value(
            f"{mem.used//(1024**3)}/{mem.total//(1024**3)} GB ({mem.percent}%)",
            mem.percent
        )

        # atualizar discos
        partitions = psutil.disk_partitions()
        for i, part in enumerate(partitions):
            if i >= len(self.real_disks):
                continue
            disk_card_name = f"Disk {i} ({self.real_disks[i][0]})"
            usage = psutil.disk_usage(part.mountpoint)
            if disk_card_name in self.cards:
                self.cards[disk_card_name].update_value(
                    f"{usage.percent}%",
                    usage.percent
                )

        # ================= CPU =================
        if self.current_device == "CPU":
            value = cpu
            speed = freq.current/1000 if freq else 0
            self.info_labels["Usage"].setText(f"{value}%")
            self.info_labels["Speed"].setText(f"{speed:.2f} GHz")
            self.info_labels["Processes"].setText(str(len(psutil.pids())))
            self.info_labels["Threads"].setText(str(psutil.cpu_stats().ctx_switches))
            self.info_labels["Cores"].setText(str(psutil.cpu_count(False)))
            self.info_labels["Logical"].setText(str(psutil.cpu_count()))

        # ================= MEMORY =================
        elif self.current_device == "Memory":
            value = mem.percent
            self.info_labels["Usage"].setText(f"{value}%")
            self.info_labels["Speed"].setText(
                f"{mem.used//(1024**3)} / {mem.total//(1024**3)} GB"
            )
            self.info_labels["Processes"].setText(
                f"{mem.available//(1024**3)} GB free"
            )
            self.info_labels["Threads"].setText("-")
            self.info_labels["Cores"].setText("-")
            self.info_labels["Logical"].setText("-")

        # ================= GPU =================
        elif self.current_device == "GPU":
            try:
                gpu = GPUtil.getGPUs()[0]
                load = int(gpu.load*100)
                temp = gpu.temperature
                self.cards["GPU"].update_value(f"{load}% ({temp}°C)", load)
                value = load
            except:
                value = 0

        self.graph.add_value(value)

class SettingsTab(QWidget):
	def __init__(self, app_reference):
		super().__init__()

		self.app_reference = app_reference

		layout = QVBoxLayout()

		# LANGUAGE
		lang_group = QGroupBox("Language")
		lang_layout = QVBoxLayout()

		self.lang_combo = QComboBox()
		self.lang_combo.addItem("Português", "pt")
		self.lang_combo.addItem("English", "en")

		index = self.lang_combo.findData(lang.current_language)
		if index >= 0:
			self.lang_combo.setCurrentIndex(index)

		self.lang_combo.currentIndexChanged.connect(self.change_language)

		lang_layout.addWidget(self.lang_combo)
		lang_group.setLayout(lang_layout)

		layout.addWidget(lang_group)

		layout.addStretch()

		self.setLayout(layout)

	def change_language(self):
		lang.load_language(self.lang_combo.currentData())
		self.app_reference.refresh_ui()

	def change_color(self, text):
		theme.accent = config_file.COLOR_MAP[text]
		theme.save()

		QApplication.instance().setStyleSheet(build_stylesheet())

		self.app_reference.refresh_ui()

	def update_accent_labels(self, widget):
		for child in widget.findChildren(AccentLabel):
			child.update_color()

	def change_theme(self):
		theme.theme = self.theme_combo.currentData()
		theme.save()

		QApplication.instance().setStyleSheet(build_stylesheet())

class AboutTab(QWidget):
	def __init__(self, app_reference):
		super().__init__()

		self.app_reference = app_reference
		self.contributors = []

		root_layout = QVBoxLayout()
		root_layout.setSpacing(0)
		root_layout.setContentsMargins(0, 0, 0, 0)

		main_layout = QHBoxLayout()
		main_layout.setSpacing(20)
		main_layout.setContentsMargins(20, 20, 20, 20)

		left_card = QFrame()
		left_card.setMinimumWidth(350)
		left_card.setProperty("profile", True)

		left_layout = QVBoxLayout()

		title = QLabel(lang.t("contribuitors"))
		title.setStyleSheet(
			"color:white;font-size:18px;font-weight:bold;border:none;"
		)
		left_layout.addWidget(title)

		self.contrib_list = QListWidget()
		self.contrib_list.setStyleSheet("""
			QListWidget{
				background:#111;
				border:none;
				color:white;
				padding:8px;
			}
			QListWidget::item{
				padding:8px;
				border-radius:6px;
			}
			QListWidget::item:hover{
				background:#222;
			}
		""")

		left_layout.addWidget(self.contrib_list)
		left_card.setLayout(left_layout)

		right_card = QFrame()
		right_card.setMaximumWidth(420)
		right_card.setProperty("profile", True)

		profile_layout = QVBoxLayout()
		profile_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

		# FOTO
		pic_container = QHBoxLayout()
		pic_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

		self.pic = QLabel()
		self.pic.setFixedSize(160, 160)
		self.pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.pic.setProperty("profile", True)

		pic_container.addWidget(self.pic)
		profile_layout.addLayout(pic_container)

		# NAME
		self.name_label = QLabel()
		self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.name_label.setStyleSheet(
			"color:white;font-size:22px;font-weight:600;"
		)
		profile_layout.addWidget(self.name_label)

		# USER
		self.user_label = QLabel()
		self.user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.user_label.setStyleSheet("color:#9aa0a6;")
		profile_layout.addWidget(self.user_label)

		# BIO
		self.bio_label = QLabel()
		self.bio_label.setWordWrap(True)
		self.bio_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.bio_label.setStyleSheet("color:#cccccc;padding:5px 10px;")
		profile_layout.addWidget(self.bio_label)

		# BUTTONS
		btn_layout = QHBoxLayout()

		self.follow_btn = AccentButton(lang.t("profile_button1"))
		self.coffee_btn = AccentButton(lang.t("profile_button2"))

		btn_style = """
			QPushButton{
				background:#242424;
				color:white;
				border-radius:8px;
				padding:8px 14px;
				font-weight:bold;
				border:1px solid #2a2a2a;
			}
			QPushButton:hover{
				background:#4fc3f7;
				color:black;
			}
		"""

		self.follow_btn.setStyleSheet(btn_style)
		self.coffee_btn.setStyleSheet(btn_style)

		btn_layout.addWidget(self.follow_btn)
		btn_layout.addWidget(self.coffee_btn)

		profile_layout.addLayout(btn_layout)

		right_card.setLayout(profile_layout)

		main_layout.addWidget(left_card, 2)
		main_layout.addWidget(right_card, 1)

		footer = QFrame()
		footer.setFixedHeight(32)
		footer.setStyleSheet("""
			QFrame{
				background:#0f0f0f;
				border-top:1px solid #222;
			}
		""")

		footer_layout = QHBoxLayout()
		footer_layout.setContentsMargins(10, 0, 10, 0)

		app_version = config_file.version

		self.footer_label = QLabel(f"{config_file.name}  •  v{app_version}")
		self.footer_label.setStyleSheet("""
			color:#8a8a8a;
			font-size:11px;
		""")

		footer_layout.addStretch()
		footer_layout.addWidget(self.footer_label)
		footer.setLayout(footer_layout)

		root_layout.addLayout(main_layout)
		root_layout.addWidget(footer)

		self.setLayout(root_layout)

		# EVENTS
		self.contrib_list.currentRowChanged.connect(self.update_profile)
		self.follow_btn.clicked.connect(self.open_contact)
		self.coffee_btn.clicked.connect(self.open_coffee)

		# LOAD DATA
		self.load_contributors()

	def load_contributors(self):
		try:
			with open(resource_path("files/contributors.json"), "r", encoding="utf-8") as f:
				data = json.load(f)

			self.contributors = data.get("contributors", [])
			self.contrib_list.clear()

			for c in self.contributors:
				self.contrib_list.addItem(c["name"])

			if self.contributors:
				self.contrib_list.setCurrentRow(0)

		except Exception as e:
			print("contributors.json error:", e)

	def update_profile(self, index):

		if index < 0 or index >= len(self.contributors):
			return

		c = self.contributors[index]

		self.name_label.setText(c.get("name", ""))
		self.user_label.setText(c.get("username", ""))
		self.bio_label.setText(c.get("bio", ""))

		pix = QPixmap(c.get("image", ""))
		if not pix.isNull():
			self.pic.setPixmap(
				pix.scaled(
					self.pic.width(),
					self.pic.height(),
					Qt.AspectRatioMode.KeepAspectRatioByExpanding,
					Qt.TransformationMode.SmoothTransformation
				)
			)

		self.contact_link = c.get("button1_value")
		self.coffee_link = c.get("button2_value")

	# LINKS
	def open_contact(self):
		if hasattr(self, "contact_link") and self.contact_link:
			webbrowser.open(self.contact_link)

	def open_coffee(self):
		if hasattr(self, "coffee_link") and self.coffee_link:
			webbrowser.open(self.coffee_link)
# APP
class PCHApp(QWidget):
	def __init__(self):
		super().__init__()
		self.setWindowTitle(lang.t("app_name") + " - " + config_file.version)
		self.setGeometry(100, 100, 750, 550)
		self.setObjectName("root")
		self.setFixedSize(config_file.window_size[0], config_file.window_size[1])
		self.setStyleSheet("""
			QWidget#root {
				background-color: {theme.background()};
				color: {theme.text()};
				font-size: 13px;
			}
			QTabBar::tab {
				background: #2d2d30;
				padding: 6px 12px;
				border: 1px solid #3c3c3c;
			}
			QTabBar::tab:selected {
				background: #1e1e1e;
				color: #4fc3f7;
				font-weight: bold;
			}
			QGroupBox {
				border: 1px solid #3c3c3c;
				margin-top: 10px;
				font-weight: bold;
			}
		""")

		layout = QVBoxLayout()

		# 🔥 IMPORTANTE: salvar tabs como atributo
		self.tabs = QTabWidget()
		self.tabs.addTab(CPUTab(), "")
		self.tabs.addTab(MainboardTab(), "")
		self.tabs.addTab(MemoryTab(), "")
		self.tabs.addTab(SPDTab(), "")
		self.tabs.addTab(GraphicsTab(), "")
		self.tabs.addTab(BenchTab(), "")
		self.tabs.addTab(SettingsTab(self), "")
		self.tabs.addTab(AboutTab(self), "")

		layout.addWidget(self.tabs)
		self.setLayout(layout)

		# Atualiza nomes das abas
		self.refresh_ui()

	def refresh_ui(self):
		tab_keys = [
			"tab_processor",
			"tab_mainboard",
			"tab_memory",
			"tab_spd",
			"tab_graphics",
			"tab_bench",
			"tab_settings",
			"tab_about"
		]

		for index, key in enumerate(tab_keys):
			if index < self.tabs.count():
				self.tabs.setTabText(index, lang.t(key))

		# 🔥 Atualiza conteúdo interno das abas
		for i in range(self.tabs.count()):
			widget = self.tabs.widget(i)

			if widget and hasattr(widget, "apply_language"):
				widget.apply_language()

		# 🔥 Força repaint geral (garante atualização visual completa)
		QApplication.instance().setStyleSheet(build_stylesheet())

		# atualiza botões accent
		for w in self.findChildren(AccentButton):
			w.update_style()
		self.tabs.update()
		self.update()

	def apply_theme(self):
		QApplication.instance().setStyleSheet(build_stylesheet())

		# atualiza botões accent
		for w in self.findChildren(AccentButton):
			w.update_style()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = PCHApp()
	app.setStyleSheet(build_stylesheet())
	window.show()
	sys.exit(app.exec())