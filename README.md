<img width="466" height="234" alt="Screenshot 2026-06-09 042611" src="https://github.com/user-attachments/assets/b3f46b65-6c36-4bf5-84b0-1e01e077bd0f" />
<img width="366" height="234" alt="Screenshot 2026-06-08 041127" src="https://github.com/user-attachments/assets/abca9093-ee12-446b-ae2b-a2354ed8b422" />
<img width="270" height="383" alt="Screenshot 2026-06-05 021201" src="https://github.com/user-attachments/assets/b8bfd7c5-81a2-41d1-a88b-9f2648f6136a" />

# Digital ID Card V1

A custom-built, battery-powered smart ID card built around an ESP32-C3 and an E-ink display. The card is USB-C rechargeable and designed to replace multiple physical cards with one reprogrammable device.

## What It Is

This project is a credit-card-sized electronic badge with its own custom PCB and a 3D-printed enclosure. At its core is an ESP32-C3-MINI-1 microcontroller driving a low-power E-ink (e-paper) display, with an onboard LiPo battery charged over USB-C.

The card has two main use cases:

1. **Digital business card** – displays your name, role, contact details, or a QR code, and can be updated wirelessly instead of reprinting a new card every time your information changes.
2. **All-in-one ID wallet** – stores multiple identity/access cards (e.g. work badge, student ID, membership cards) on a single device, with the display cycling between them so you only need to carry one card instead of several.

An E-ink display was chosen over a standard LCD/OLED screen because it only draws power when the image actually changes, holds its image with zero power once drawn, and stays readable in direct sunlight — all of which make it well suited to something that needs to sit in a wallet or on a lanyard for days at a time on a small battery.

## Why I Made It

Carrying around a stack of physical ID cards, badges, and business cards is inconvenient, and most of them can't be updated once printed. The goal of this project was to build a single reprogrammable card that:

- Reduces the number of physical cards someone needs to carry
- Can be updated instantly (new job title, new contact info, new access card) without reprinting anything
- Runs for an extended period on a small rechargeable battery thanks to the E-ink display
- Demonstrates a complete, real hardware build — schematic, custom PCB, firmware, and a 3D-printed case — as a personal embedded systems / PCB design project

## Hardware Overview

The PCB is built around:

- **ESP32-C3-MINI-1** as the main microcontroller (Wi-Fi/BLE enabled, for future wireless updates)
- **MCP73831** LiPo battery charge controller, fed via **USB-C**
- **AP2112K-3.3** linear regulator to supply a clean 3.3V rail
- An 8-pin header for an **E-ink display module** (generic SPI e-paper panel)
- **Boot** and **Reset** push buttons for the ESP32-C3
- Supporting passives (decoupling capacitors, pull-up/pull-down resistors)

The enclosure is a 3D-printed case (see `Case design/`) sized to hold the PCB and battery like a standard ID card/badge.

## Repository Structure

```
Digital-ID-Card-V1/
├── Case design/     # 3D-printed enclosure design files
├── Firmware/         # ESP32-C3 firmware (C++)
├── PCB/             # KiCad schematic, PCB layout, and project files
└── README.md
```

## Bill of Materials (BOM)

This BOM reflects the components placed on the current PCB revision, extracted directly from the KiCad schematic.

| Ref. Designator(s) | Component | Value / Part Number | Footprint / Package | Qty | Function |
|---|---|---|---|---|---|
| U3 | Microcontroller | ESP32-C3-MINI-1 (Espressif) | ESP32-C3-MINI-1 module | 1 | Main processor, Wi-Fi/BLE, drives the E-ink display |
| U2 | Battery charge controller | MCP73831T-2-OT | SOT-23-5 | 1 | Charges the LiPo battery from USB-C |
| U1 | Voltage regulator | AP2112K-3.3 | SOT-23-5 | 1 | Regulates supply down to 3.3V for the ESP32-C3 |
| J2 | USB connector | USB-C receptacle (USB 2.0, 14-pin) | USB-C SMD receptacle | 1 | Power input / charging / programming |
| J1 | Battery connector | 2-pin JST/header (LiPo battery) | 2.54mm pin header, 1x02 | 1 | Connects to LiPo battery pack |
| E-ink_display1 | Display connector | 8-pin header (generic SPI e-paper) | 2.54mm pin header, 1x08 | 1 | Connects to E-ink display module |
| boot1, reset1 | Push buttons | SW_Push | SMD tactile switch (SW_SPST_TL3342) | 2 | Boot mode select and reset for ESP32-C3 |
| R1, R2 | Resistor | 5.1 kΩ | 0805 SMD | 2 | USB-C CC line pull-downs (configures as device) |
| R3, R4, R5 | Resistor | 10 kΩ | 0805 SMD | 3 | Pull-up/pull-down resistors (boot/reset/strapping) |
| C1, C2, C3 | Capacitor | 10 µF | 0805 SMD | 3 | Power supply decoupling/filtering |

**Not on the PCB BOM (purchased/printed separately):**

| Item | Notes |
|---|---|
| LiPo battery | Connects via J1; capacity depends on case size |
| E-ink display module | Generic SPI e-paper panel, connects via 8-pin header |
| 3D-printed case | See `Case design/` folder for the enclosure files |

## Status

This is a working prototype (V1). Planned improvements include confirming the exact E-ink display model in this BOM and expanding the firmware to support storing/switching between multiple ID profiles.
