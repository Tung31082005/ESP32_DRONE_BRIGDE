import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial.tools.list_ports
import subprocess
import threading
import os

class FlasherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DroneBridge ESP32 Flasher UI")
        self.root.geometry("650x500")
        self.root.configure(bg="#f0f0f0")
        
        # Tiêu đề
        title = tk.Label(root, text="CÔNG CỤ NẠP FIRMWARE ESP32", font=("Helvetica", 16, "bold"), bg="#f0f0f0", fg="#333")
        title.pack(pady=15)
        
        # Khu vực chọn cổng COM
        frame1 = tk.Frame(root, bg="#f0f0f0")
        frame1.pack(pady=10)
        tk.Label(frame1, text="🔌 Chọn Cổng COM:", font=("Helvetica", 11), bg="#f0f0f0").pack(side=tk.LEFT)
        self.com_combo = ttk.Combobox(frame1, values=self.get_com_ports(), state="readonly", width=15, font=("Helvetica", 11))
        self.com_combo.pack(side=tk.LEFT, padx=10)
        if self.com_combo['values']:
            self.com_combo.current(0)
        
        refresh_btn = tk.Button(frame1, text="🔄 Làm mới", font=("Helvetica", 10), command=self.refresh_ports)
        refresh_btn.pack(side=tk.LEFT)

        # Khu vực Nút bấm chức năng
        frame2 = tk.Frame(root, bg="#f0f0f0")
        frame2.pack(pady=15)
        
        btn_erase = tk.Button(frame2, text="🧹 Xóa Trắng (Erase)", font=("Helvetica", 11, "bold"), bg="#ff9800", fg="white", width=20, command=self.erase_flash)
        btn_erase.pack(side=tk.LEFT, padx=10)
        
        btn_flash = tk.Button(frame2, text="⚡ Nạp Code (Flash)", font=("Helvetica", 11, "bold"), bg="#4caf50", fg="white", width=20, command=self.flash_firmware)
        btn_flash.pack(side=tk.LEFT, padx=10)
        
        btn_monitor = tk.Button(frame2, text="🔍 Xem Log (Monitor)", font=("Helvetica", 11, "bold"), bg="#2196f3", fg="white", width=20, command=self.monitor)
        btn_monitor.pack(side=tk.LEFT, padx=10)
        
        # Bảng điều khiển Console
        tk.Label(root, text="Trạng thái thực thi (Console):", font=("Helvetica", 10, "bold"), bg="#f0f0f0").pack(anchor=tk.W, padx=15)
        self.console = scrolledtext.ScrolledText(root, width=80, height=15, bg="#1e1e1e", fg="#4caf50", font=("Consolas", 10))
        self.console.pack(padx=15, pady=5)
        
        self.process = None

    def get_com_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def refresh_ports(self):
        self.com_combo['values'] = self.get_com_ports()
        if self.com_combo['values']:
            self.com_combo.current(0)
        else:
            self.com_combo.set('')
            self.log("[-] Không tìm thấy mạch ESP32 nào được cắm vào.")
            
    def log(self, text):
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        
    def run_command(self, cmd_str, is_monitor=False):
        if not self.com_combo.get():
            messagebox.showerror("Lỗi", "Vui lòng cắm mạch ESP32 và chọn cổng COM!")
            return
            
        # Lệnh nạp môi trường ESP-IDF (Dùng cmd.exe để gọi export.bat)
        idf_export = r'call "C:\Espressif\frameworks\esp-idf-v5.5.4\export.bat" >nul 2>&1 && '
        full_cmd = idf_export + cmd_str
            
        if is_monitor:
            port = self.com_combo.get()
            self.log(f"[*] Đang mở cửa sổ Monitor cho cổng {port}...")
            # Mở một cửa sổ CMD mới để chạy monitor vì nó tương tác liên tục
            os.system(f'start cmd.exe /c "{idf_export} idf.py -p {port} monitor"')
            return

        def target():
            self.log(f"\n[>>>] Đang chạy lệnh: {cmd_str}")
            self.log("-" * 60)
            
            # Khởi chạy tiến trình
            self.process = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            for line in self.process.stdout:
                self.console.insert(tk.END, line)
                self.console.see(tk.END)
                
            self.process.wait()
            self.log("-" * 60)
            if self.process.returncode == 0:
                self.log(f"[HOÀN TẤT] Lệnh thực thi thành công! 🚀")
            else:
                self.log(f"[LỖI] Lệnh thất bại (Mã lỗi: {self.process.returncode}) ❌")
            
        # Chạy trong luồng phụ để không đơ giao diện
        threading.Thread(target=target, daemon=True).start()

    def erase_flash(self):
        port = self.com_combo.get()
        self.run_command(f"idf.py -p {port} erase-flash")

    def flash_firmware(self):
        port = self.com_combo.get()
        self.run_command(f"idf.py -p {port} flash")

    def monitor(self):
        self.run_command("", is_monitor=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlasherApp(root)
    root.mainloop()
