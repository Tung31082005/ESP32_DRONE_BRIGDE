# Hướng Dẫn Sử Dụng: DroneBridge ESP32-CAM (Phiên Bản Tối Ưu Hóa)

Tài liệu này hướng dẫn cách cài đặt, sử dụng và khắc phục sự cố cho bộ Firmware DroneBridge đặc biệt được tùy biến dành riêng cho ESP32-CAM và ESP32 tiêu chuẩn.

---

## 1. Giới Thiệu Tính Năng Nổi Bật

- **Bản Firmware 2-trong-1 (Universal):** Nạp được cho cả mạch ESP32-CAM (để phát Video FPV) và ESP32 thường (để làm trạm trung chuyển mặt đất).
- **Trang FPV Tùy Chỉnh (`/video.html`):** Tích hợp giao diện điều khiển Camera chuyên nghiệp trên điện thoại (đổi độ phân giải, bật đèn Flash, tạm dừng Camera, chụp ảnh/quay video lưu thẳng vào điện thoại, cảnh báo sóng yếu).
- **Tối ưu năng lượng thông minh:** Ở chế độ sóng siêu xa (ESP-NOW LR), hệ thống tự động ngắt toàn bộ nguồn cấp cho module Camera phần cứng để dồn 100% pin và băng thông cho Telemetry.
- **Dời nút Reset về chân 12:** Khắc phục triệt để lỗi xung đột với mắt Camera trên ESP32-CAM.

---

## 2. Công Cụ Nạp Firmware (FlasherUI)

Trong thư mục dự án đã có sẵn phần mềm **`FlasherUI.exe`**.
1. Cắm mạch ESP32 vào máy tính.
2. Mở `FlasherUI.exe` (Bỏ qua cảnh báo SmartScreen của Windows nếu có).
3. Chọn cổng COM của mạch.
4. Bấm **Xóa Trắng (Erase)** nếu đây là lần đầu tiên nạp mạch hoặc bạn muốn khôi phục cài đặt gốc.
5. Bấm **Nạp Code (Flash)** và chờ đến khi hoàn tất.

---

## 3. Lựa Chọn Chế Độ Bay

Hệ thống hỗ trợ 2 trường phái bay chính. Tùy thuộc vào nhu cầu, bạn hãy cấu hình theo một trong hai cách dưới đây:

### 3.1. Chế Độ 1: Bay Khoảng Cách Ngắn (Có FPV Video)
*Chỉ dùng 1 mạch ESP32-CAM gắn trên Drone. Dùng điện thoại bắt trực tiếp WiFi.*

- **Thiết lập:**
  1. Cấp nguồn, dùng điện thoại bắt mạng WiFi `DroneBridge for ESP32` (Mật khẩu mặc định: `dronebridge`).
  2. Truy cập IP: `192.168.2.1`.
  3. Sửa **UART TX pin** thành `13` và **UART RX pin** thành `14` (Chân MAVLink nối vào Flight Controller).
  4. Bấm Lưu và khởi động lại.
- **Sử dụng:** 
  - Mở QGroundControl (Sẽ tự động nhận tín hiệu qua UDP Port 14550).
  - Mở trình duyệt Web, vào `192.168.2.1/video.html` để xem Video FPV trực tiếp.
  - 👉 **Mẹo:** Khi đang bay theo waypoint tự động và muốn sóng xa hơn, bạn bấm nút **"Tạm dừng Camera"** trên trang Web để giải phóng 90% băng thông WiFi.

### 3.2. Chế Độ 2: Bay Xuyên Vật Cản (Siêu Xa ESP-NOW)
*Bắt buộc phải có 2 mạch ESP32. Chế độ này TẮT HOÀN TOÀN TÍNH NĂNG VIDEO để lấy băng thông.*

**A. Mạch trên Drone (Phát Sóng):**
  1. Dùng điện thoại truy cập `192.168.2.1`.
  2. Đổi **System Mode** thành `ESP-NOW LR Mode AIR`.
  3. Cài **UART TX pin** = `13` và **UART RX pin** = `14`. Bấm Lưu và Reboot. (Lúc này mạch sẽ tàng hình khỏi điện thoại).

**B. Mạch Mặt Đất (Trạm Thu):**
  1. Dùng 1 mạch ESP32 thường, truy cập `192.168.2.1`.
  2. Đổi **System Mode** thành `ESP-NOW LR Mode GND`.
  3. BẮT BUỘC cài đặt các chân giao tiếp để xuất ra cáp (nếu không khai báo, module sóng sẽ tự hủy do lỗi):
     - **UART TX pin** = `17`
     - **UART RX pin** = `16`
  4. Bấm Lưu và Reboot.

**C. Lấy dữ liệu vào QGroundControl:**
  - Vì sóng ESP-NOW chạy ở dải tần LR đặc biệt, trạm mặt đất **không thể phát mạng WiFi**.
  - Bạn phải nối 1 mạch chuyển đổi **USB-to-TTL (CP2102/FT232)** vào chân **16 (RX)** và **17 (TX)** của Trạm Mặt Đất. Cắm cục CP2102 đó vào Máy tính.
  - Mở QGC -> Comm Links -> Thêm cổng Serial mới -> Trỏ vào cổng COM của cục CP2102 (Baudrate 115200).

---

## 4. Xử Lý Sự Cố (Troubleshooting)

**1. Không thể kết nối UART qua cổng Micro-USB có sẵn trên mạch ESP32 mặt đất?**
Cổng USB tích hợp trên mạch WROOM/NodeMCU bị hàn chết vào chân 1 và 3 (Chân xuất Log của hệ điều hành). Nếu bạn truyền dữ liệu bay MAVLink qua cổng này, tín hiệu sẽ bị trộn lẫn với Log báo cáo trạng thái của ESP-IDF gây nhiễu QGC. Bắt buộc phải dùng mạch CP2102 cắm rời vào chân 16, 17.

**2. Làm sao để Reset (Xóa trắng cấu hình) khi lỡ chuyển mạch sang ESP-NOW và bị tàng hình WiFi?**
Ở bản độ này, chân Reset cấu hình đã được dời khỏi chân số 0. Để Hard Reset khôi phục cài đặt gốc: Lấy một sợi dây điện chập chân **G12** xuống chân **GND** và giữ nguyên khoảng 3 giây. Mạch sẽ tự động xóa sạch mọi thứ và trở về phát mạng WiFi `AP Mode`.

**3. Không thấy biểu tượng sóng trên trang Web FPV?**
Do cơ chế tính toán sóng của ESP32, thông số Cường Độ Sóng (RSSI) chỉ được cập nhật mỗi khi có tín hiệu mạng gửi tới. Hãy chắc chắn mạch FC của bạn đã cắm đúng chân TX/RX, tốc độ Baudrate đúng và đang xả dữ liệu đều đặn.
