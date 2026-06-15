#include <Arduino.h>
#include <SPIFFS.h>
#include <GxEPD2_3C.h>

#define CS_PIN   7
#define DC_PIN   6
#define RST_PIN  5
#define BUSY_PIN 4

GxEPD2_3C<GxEPD2_420c,GxEPD2_420c::HEIGHT> display(
  GxEPD2_420c(CS_PIN, DC_PIN, RST_PIN, BUSY_PIN)
);

String incomingFile = "";

void saveImage()
{
  File file = SPIFFS.open("/card.bin", FILE_WRITE);

  if (!file)
  {
    Serial.println("save failed");
    return;
  }

  while (Serial.available())
  {
    file.write(Serial.read());
    delay(1);
  }

  file.close();
  Serial.println("stored");
}

void drawStoredImage()
{
  File file = SPIFFS.open("/card.bin");

  if (!file)
  {
    Serial.println("image missing");
    return;
  }

  display.setFullWindow();
  display.firstPage();

  do
  {
    int x = 0;
    int y = 0;

    while (file.available())
    {
      uint8_t pixel = file.read();

      if (pixel == 0)
        display.drawPixel(x, y, GxEPD_WHITE);
      else if (pixel == 1)
        display.drawPixel(x, y, GxEPD_BLACK);
      else
        display.drawPixel(x, y, GxEPD_RED);

      x++;

      if (x >= display.width())
      {
        x = 0;
        y++;
      }

      if (y >= display.height())
        break;
    }

  } while (display.nextPage());

  file.close();
}

void setup()
{
  Serial.begin(115200);

  if (!SPIFFS.begin(true))
  {
    Serial.println("spiffs error");
    return;
  }

  display.init();

  display.setRotation(1);
  display.setTextColor(GxEPD_BLACK);

  if (SPIFFS.exists("/card.bin"))
  {
    drawStoredImage();
  }

  Serial.println("ready");
}

void loop()
{
  if (Serial.available())
  {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "UPLOAD")
    {
      delay(500);
      saveImage();
      drawStoredImage();
    }

    if (cmd == "REFRESH")
    {
      drawStoredImage();
    }
  }

  delay(100);
}