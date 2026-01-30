import os
import serial
import serial.tools.list_ports
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import csv
from datetime import datetime
import sys
import subprocess
import re

# なんのデータを取るかのリスト
main_datalist=["ExpDepthM","DepthM","ExpAltM","AltM","Pow","T_in","T_out","Mnu","Lat","Lon","Yaw","VelN","VelE","Y","Mo","D","H","Mi","S","Ms","RolD","PitD","TimeStmp"]

class SerialApp:
    def __init__(self, root):#uiの初期設定節
        self.root = root
        self.root.title("ROV-Logger")
        self.serial_port = None
        self.is_recording = False
        self.csv_file = None
        self.csv_writer = None
        self.create_widgets()#各UIを呼び出し
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):#各種UIのパラメータ設定節
        self.combobox_ports = tk.StringVar()
        self.combobox_ports_menu = tk.OptionMenu(self.root, self.combobox_ports, *self.getPorts())
        self.combobox_ports_menu.pack()
        
        self.button_connect = tk.Button(self.root, text="Connect", command=self.connect_serial)
        self.button_connect.pack()

        self.label_status = tk.Label(self.root, text="Disconnected")
        self.label_status.pack()

        self.textbox_path = tk.Entry(self.root, width=40)
        self.textbox_path.pack()
        self.button_browse = tk.Button(self.root, text="Browse", command=self.browse_folder)
        self.button_browse.pack()

        self.button_record = tk.Button(self.root, text="Record", command=self.toggle_recording)
        self.button_record.pack()

        self.label_record_status = tk.Label(self.root, text="Not Recording")
        self.label_record_status.pack()
    def getPorts(self):#選択肢を取得する処理節
        ports = serial.tools.list_ports.comports()
        #　comポートが検出できない場合ここを変えてみる
        return [port.device for port in ports] if ports else ["検出不可"]
    def connect_serial(self):#選択後つなぐ用の処理節
        selected_port = self.combobox_ports.get()
        if selected_port:
            try:
                self.serial_port = serial.Serial(selected_port, 230400, timeout=1)
                self.label_status.config(text="Connected")
                threading.Thread(target=self.read_serial_data, daemon=True).start()
            except serial.SerialException as e:
                messagebox.showerror("Connection Failed", str(e))
        else:#エラー出力
            messagebox.showwarning("Warning", "Please select a COM port")
    def read_serial_data(self):#ログ出力節
        while self.serial_port.is_open:
            try:
                data = self.serial_port.readline().decode('utf-8').rstrip()
                if data:
                    print(data)
                    sys.stdout.flush()
                    if self.is_recording and self.csv_writer:#recordがtrueのとき
                        self.parse_and_record(data)
            except serial.SerialException:
                messagebox.showerror("Error", "Serial communication error")
                break
    def parse_and_record(self, data):#ログの記述節ここを変えたらインプットの形変えれる
        try:
            dataList=main_datalist
            pattern = "(" + "|".join(dataList) + ")"#datalist使って切り分けるよ、みたいな処理
            split_data = re.split(pattern, data)[1:]
            output_dict = {split_data[i]: split_data[i + 1] for i in range(0, len(split_data), 2)}
            self.csv_writer.writerow([output_dict.get(key, "") for key in dataList])#こうすれば自動で記述してくれるやん
            self.csv_file.flush()
        except Exception:
            messagebox.showerror("Error", "Failed to parse data")
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.textbox_path.insert(0, folder)

    def toggle_recording(self):
        if not self.is_recording:
            if not self.textbox_path.get():
                messagebox.showwarning("Warning", "Please select a folder to save the CSV file.")
                return

            file_path = f"{self.textbox_path.get()}/{datetime.now().strftime('%m-%d-%Y_%H-%M-%S')}.csv"
            try:
                self.csv_file = open(file_path, 'w', newline='')
                self.csv_writer = csv.writer(self.csv_file)
                self.csv_writer.writerow(main_datalist)
                self.label_record_status.config(text="Recording")
                self.is_recording = True
                print(f"Recording started: {file_path}")
                sys.stdout.flush()
            except Exception as e:
                messagebox.showerror("Recording Failed", str(e))
        else:
            self.is_recording = False
            if self.csv_writer:
                self.csv_writer = None
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
            self.label_record_status.config(text="Not Recording")
            print("Recording stopped")
            sys.stdout.flush()

    def on_closing(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.root.destroy()
        os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialApp(root)
    root.mainloop()

    