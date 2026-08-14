import sys
import os
import subprocess
import pandas as pd
try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableView, QComboBox, QLabel, QMessageBox
    from PySide6.QtCore import QAbstractTableModel, Qt
except ImportError:
    print("PySide6 is required. Please install it.")
    sys.exit(1)

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            val = self._data.iloc[index.row(), index.column()]
            if pd.isna(val):
                return ""
            if isinstance(val, float):
                return f"{val:.4f}"
            return str(val)
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

class QoRPlotter(QMainWindow):
    def __init__(self, csv_file):
        super().__init__()
        self.setWindowTitle(f"QoR Path Correlation Debugger - {os.path.basename(csv_file)}")
        self.df = pd.read_csv(csv_file)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Controls
        ctrl_layout = QHBoxLayout()
        self.x_axis_cb = QComboBox()
        self.y_axis_cb = QComboBox()
        
        numeric_cols = self.df.select_dtypes(include=['float64', 'int64']).columns
        self.x_axis_cb.addItems(numeric_cols)
        self.y_axis_cb.addItems(numeric_cols)
        
        # Try to set sensible defaults
        slack_cols = [c for c in numeric_cols if 'slack' in c]
        if len(slack_cols) >= 2:
            self.x_axis_cb.setCurrentText(slack_cols[0])
            self.y_axis_cb.setCurrentText(slack_cols[-1])
            
        self.x_axis_cb.currentTextChanged.connect(self.update_plot)
        self.y_axis_cb.currentTextChanged.connect(self.update_plot)
        
        ctrl_layout.addWidget(QLabel("X-Axis:"))
        ctrl_layout.addWidget(self.x_axis_cb)
        ctrl_layout.addWidget(QLabel("Y-Axis:"))
        ctrl_layout.addWidget(self.y_axis_cb)
        layout.addLayout(ctrl_layout)
        
        # Plot
        self.fig = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        layout.addWidget(self.canvas)
        
        # Table
        self.table = QTableView()
        self.model = PandasModel(self.df)
        self.table.setModel(self.model)
        layout.addWidget(self.table)
        
        self.update_plot()
        
    def update_plot(self):
        self.ax.clear()
        x_col = self.x_axis_cb.currentText()
        y_col = self.y_axis_cb.currentText()
        
        if x_col and y_col:
            x_data = self.df[x_col]
            y_data = self.df[y_col]
            self.ax.scatter(x_data, y_data, alpha=0.5)
            
            # Diagonal line
            min_val = min(x_data.min(), y_data.min())
            max_val = max(x_data.max(), y_data.max())
            self.ax.plot([min_val, max_val], [min_val, max_val], 'r--')
            
            self.ax.set_xlabel(x_col)
            self.ax.set_ylabel(y_col)
            self.ax.grid(True)
            self.ax.set_title(f"Correlation: {x_col} vs {y_col}")
            self.fig.tight_layout()
            self.canvas.draw()

def build_and_extract_data(pdk, design):
    print(f"Building and extracting path data for {pdk} {design}...")
    cwd = os.getcwd()
    dump_dir = os.path.join(cwd, f"qor_dumps_{pdk}_{design}")
    os.makedirs(dump_dir, exist_ok=True)
    
    cmd = [
        "bazelisk", "build", 
        "--define=GPL_USE_ENGINE_DEFAULTS=1",
        "--spawn_strategy=local",
        f"--action_env=DUMP_DIR={dump_dir}",
        f"--define=POST_GLOBAL_PLACE_TCL={cwd}/flow/scripts/dump_paths_place.tcl",
        f"--define=POST_GLOBAL_ROUTE_TCL={cwd}/flow/scripts/dump_paths_grt.tcl",
        f"--define=POST_DETAIL_ROUTE_TCL={cwd}/flow/scripts/dump_paths_route.tcl",
        f"//flow/designs/{pdk}/{design}:{design}_route"
    ]
    
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"Error: Build failed for {pdk} {design}.")
        sys.exit(1)
        
    # Aggregate
    try:
        df3 = pd.read_csv(os.path.join(dump_dir, "3_place_timing_paths.csv"))
        df5 = pd.read_csv(os.path.join(dump_dir, "5_grt_timing_paths.csv"))
        df6 = pd.read_csv(os.path.join(dump_dir, "6_route_timing_paths.csv"))
    except Exception as e:
        print(f"Error reading CSVs: {e}")
        sys.exit(1)
        
    df_merged = df3.merge(df5, on=['startpoint', 'endpoint'], how='outer')
    df_merged = df_merged.merge(df6, on=['startpoint', 'endpoint'], how='outer')
    
    out_csv = os.path.join(cwd, f"path_data_{pdk}_{design}.csv")
    df_merged.to_csv(out_csv, index=False)
    print(f"Saved aggregated data to {out_csv}")
    return out_csv

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    csv_file = None
    if len(sys.argv) < 2:
        # Build for both pdks
        csv_sky130 = build_and_extract_data("sky130hd", "gcd")
        csv_asap7 = build_and_extract_data("asap7", "gcd")
        
        # Combine them or just open sky130 by default and let user know
        # For simplicity, let's open sky130 and asap7 in different windows
        w1 = QoRPlotter(csv_sky130)
        w1.resize(1000, 800)
        w1.show()
        
        w2 = QoRPlotter(csv_asap7)
        w2.resize(1000, 800)
        w2.show()
        
        sys.exit(app.exec())
    else:
        csv_file = sys.argv[1]
        window = QoRPlotter(csv_file)
        window.resize(1000, 800)
        window.show()
        sys.exit(app.exec())
