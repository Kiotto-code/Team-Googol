#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <QRCodeGenerator.h> // 使用这个库

// --- 引脚定义 (根据您提供的连接) ---
// ST7735S -> ESP32-CAM
#define TFT_CS    15  // CS -> GPIO 15
#define TFT_DC    2   // DC -> GPIO 2
#define TFT_RST   12  // RST -> GPIO 12
#define TFT_SCL   14  // SCL -> GPIO 14 (硬件SPI中的SCK)
#define TFT_SDA   13  // SDA -> GPIO 13 (硬件SPI中的MOSI)

// 创建一个Adafruit_ST7735对象
Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS, TFT_DC, TFT_SDA, TFT_SCL, TFT_RST);

// --- 二维码配置 ---
const char *qrText = "https://www.google.com";

// 创建一个QRCodeGenerator实例
QRCode qrcode;

/**
 * @brief 使用 QRCodeGenerator 库生成二维码，并在TFT屏幕上绘制出来
 * @param text 要编码成二维码的字符串
 */
void displayQrCode(const char *text) {
  // 1. 为二维码数据分配内存缓冲区
  // qrcode_getBufferSize(3) 中的 '3' 是二维码的版本，决定了其大小和数据容量。
  // 对于一个简单的网址，版本3通常足够了。
  uint8_t qrcodeData[qrcode_getBufferSize(3)];

  // 2. 生成二维码数据
  // qrcode_initText() 将文本编码到缓冲区中
  // ECC_LOW, MEDIUM, HIGH, QUARTILE 是纠错等级
  qrcode_initText(&qrcode, qrcodeData, 3, ECC_MEDIUM, text);

  // 3. 计算绘制参数
  int qrSize = qrcode.size; // 获取二维码尺寸 (例如 29x29)
  int screenWidth = tft.width();
  int screenHeight = tft.height();

  // 计算每个模块（二维码的小黑/白块）应该画多大
  int moduleSize = 4; // 您可以调整这个值来改变二维码的大小
  if (qrSize * moduleSize > min(screenWidth, screenHeight)) {
      moduleSize = min(screenWidth, screenHeight) / qrSize;
  }

  // 计算二维码图像的总大小
  int imageSize = qrSize * moduleSize;

  // 计算偏移量，使二维码在屏幕上居中显示
  int xOffset = (screenWidth - imageSize) / 2;
  int yOffset = (screenHeight - imageSize) / 2;
  
  // 4. 开始在屏幕上绘制
  tft.fillScreen(ST77XX_WHITE); // 先用白色清屏

  for (int y = 0; y < qrSize; y++) {
    for (int x = 0; x < qrSize; x++) {
      // 使用 qrcode_getModule() 检查模块颜色 (true 代表黑色)
      if (qrcode_getModule(&qrcode, x, y)) {
        tft.fillRect(xOffset + x * moduleSize, yOffset + y * moduleSize, moduleSize, moduleSize, ST77XX_BLACK);
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("TFT QR Code Generator");

  tft.initR(INITR_BLACKTAB);
  tft.setRotation(1);
  
  tft.fillScreen(ST77XX_BLACK);
  tft.setCursor(10, 10);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.println("Generating QR...");
  delay(1000);

  // 生成并显示二维码
  displayQrCode(qrText);
}

void loop() {
  // 留空
  delay(5000);
}