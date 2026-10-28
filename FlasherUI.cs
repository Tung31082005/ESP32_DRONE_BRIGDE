using System;
using System.Diagnostics;
using System.IO.Ports;
using System.Drawing;
using System.Windows.Forms;
using System.Threading;

namespace ESP32Flasher
{
    public class FlasherForm : Form
    {
        private ComboBox comComboBox;
        private Button refreshBtn;
        private Button eraseBtn;
        private Button flashBtn;
        private Button monitorBtn;
        private RichTextBox consoleBox;
        private Process currentProcess;

        public FlasherForm()
        {
            this.Text = "CÔNG CỤ NẠP FIRMWARE ESP32";
            this.Size = new Size(700, 550);
            this.BackColor = Color.FromArgb(240, 240, 240);
            this.StartPosition = FormStartPosition.CenterScreen;

            Label titleLabel = new Label();
            titleLabel.Text = "CÔNG CỤ NẠP FIRMWARE ESP32";
            titleLabel.Font = new Font("Arial", 16, FontStyle.Bold);
            titleLabel.AutoSize = true;
            titleLabel.Location = new Point(160, 20);
            this.Controls.Add(titleLabel);

            Label comLabel = new Label();
            comLabel.Text = "🔌 Chọn Cổng COM:";
            comLabel.AutoSize = true;
            comLabel.Location = new Point(30, 75);
            comLabel.Font = new Font("Arial", 10);
            this.Controls.Add(comLabel);

            comComboBox = new ComboBox();
            comComboBox.DropDownStyle = ComboBoxStyle.DropDownList;
            comComboBox.Location = new Point(180, 72);
            comComboBox.Width = 120;
            comComboBox.Font = new Font("Arial", 10);
            this.Controls.Add(comComboBox);

            refreshBtn = new Button();
            refreshBtn.Text = "🔄 Làm mới";
            refreshBtn.Location = new Point(310, 70);
            refreshBtn.Width = 100;
            refreshBtn.Height = 30;
            refreshBtn.Click += new EventHandler(RefreshPorts);
            this.Controls.Add(refreshBtn);

            eraseBtn = new Button();
            eraseBtn.Text = "🧹 Xóa Trắng (Erase)";
            eraseBtn.BackColor = Color.Orange;
            eraseBtn.ForeColor = Color.White;
            eraseBtn.Font = new Font("Arial", 10, FontStyle.Bold);
            eraseBtn.Location = new Point(30, 130);
            eraseBtn.Width = 180;
            eraseBtn.Height = 40;
            eraseBtn.Click += new EventHandler(EraseClick);
            this.Controls.Add(eraseBtn);

            flashBtn = new Button();
            flashBtn.Text = "⚡ Nạp Code (Flash)";
            flashBtn.BackColor = Color.Green;
            flashBtn.ForeColor = Color.White;
            flashBtn.Font = new Font("Arial", 10, FontStyle.Bold);
            flashBtn.Location = new Point(240, 130);
            flashBtn.Width = 180;
            flashBtn.Height = 40;
            flashBtn.Click += new EventHandler(FlashClick);
            this.Controls.Add(flashBtn);

            monitorBtn = new Button();
            monitorBtn.Text = "🔍 Xem Log (Monitor)";
            monitorBtn.BackColor = Color.DodgerBlue;
            monitorBtn.ForeColor = Color.White;
            monitorBtn.Font = new Font("Arial", 10, FontStyle.Bold);
            monitorBtn.Location = new Point(450, 130);
            monitorBtn.Width = 180;
            monitorBtn.Height = 40;
            monitorBtn.Click += new EventHandler(MonitorClick);
            this.Controls.Add(monitorBtn);

            Label consoleLabel = new Label();
            consoleLabel.Text = "Trạng thái thực thi (Console):";
            consoleLabel.AutoSize = true;
            consoleLabel.Location = new Point(30, 190);
            consoleLabel.Font = new Font("Arial", 10, FontStyle.Bold);
            this.Controls.Add(consoleLabel);

            consoleBox = new RichTextBox();
            consoleBox.Location = new Point(30, 220);
            consoleBox.Size = new Size(620, 260);
            consoleBox.BackColor = Color.Black;
            consoleBox.ForeColor = Color.LightGreen;
            consoleBox.Font = new Font("Consolas", 10);
            consoleBox.ReadOnly = true;
            this.Controls.Add(consoleBox);

            RefreshPorts(null, null);
        }

        private void RefreshPorts(object sender, EventArgs e)
        {
            comComboBox.Items.Clear();
            string[] ports = SerialPort.GetPortNames();
            foreach (string port in ports)
            {
                comComboBox.Items.Add(port);
            }
            if (comComboBox.Items.Count > 0)
            {
                comComboBox.SelectedIndex = 0;
            }
            else
            {
                Log("[-] Không tìm thấy mạch ESP32 nào được cắm vào.");
            }
        }

        private void Log(string text)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action<string>(Log), new object[] { text });
                return;
            }
            consoleBox.AppendText(text + Environment.NewLine);
            consoleBox.ScrollToCaret();
        }

        private void RunCommand(string cmd, bool isMonitor)
        {
            if (comComboBox.SelectedItem == null)
            {
                MessageBox.Show("Vui lòng cắm mạch ESP32 và chọn cổng COM!", "Lỗi", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            string port = comComboBox.SelectedItem.ToString();
            string idfExport = @"call ""C:\Espressif\frameworks\esp-idf-v5.5.4\export.bat"" >nul 2>&1 && ";
            
            if (isMonitor)
            {
                Log(string.Format("[*] Đang mở cửa sổ Monitor cho cổng {0}...", port));
                Process.Start("cmd.exe", string.Format("/c \"{0} idf.py -p {1} monitor\"", idfExport, port));
                return;
            }

            string fullCmd = string.Format("{0} idf.py -p {1} {2}", idfExport, port, cmd);

            Thread t = new Thread(() =>
            {
                Log(string.Format("\n[>>>] Đang chạy lệnh: idf.py -p {0} {1}", port, cmd));
                Log(new String('-', 60));
                
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = "cmd.exe";
                psi.Arguments = string.Format("/c \"{0}\"", fullCmd);
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.RedirectStandardError = true;
                psi.CreateNoWindow = true;

                currentProcess = new Process();
                currentProcess.StartInfo = psi;
                
                currentProcess.OutputDataReceived += (s, ev) => { if (ev.Data != null) Log(ev.Data); };
                currentProcess.ErrorDataReceived += (s, ev) => { if (ev.Data != null) Log(ev.Data); };

                currentProcess.Start();
                currentProcess.BeginOutputReadLine();
                currentProcess.BeginErrorReadLine();
                
                currentProcess.WaitForExit();
                
                Log(new String('-', 60));
                if (currentProcess.ExitCode == 0)
                    Log("[HOÀN TẤT] Lệnh thực thi thành công! 🚀");
                else
                    Log(string.Format("[LỖI] Lệnh thất bại (Mã lỗi: {0}) ❌", currentProcess.ExitCode));
            });
            t.IsBackground = true;
            t.Start();
        }

        private void EraseClick(object sender, EventArgs e) { RunCommand("erase-flash", false); }
        private void FlashClick(object sender, EventArgs e) { RunCommand("flash", false); }
        private void MonitorClick(object sender, EventArgs e) { RunCommand("monitor", true); }

        [STAThread]
        public static void Main()
        {
            Application.EnableVisualStyles();
            Application.Run(new FlasherForm());
        }
    }
}
