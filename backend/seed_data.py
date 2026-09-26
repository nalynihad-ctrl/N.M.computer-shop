"""Sample product catalogue used to seed the database."""

CATEGORY_META = {
    "CPUs": "cpu.svg",
    "GPUs": "gpu.svg",
    "Motherboards": "motherboard.svg",
    "RAM": "ram.svg",
    "SSD": "ssd.svg",
    "HDD": "hdd.svg",
    "Power Supplies": "psu.svg",
    "PC Cases": "case.svg",
    "Cooling": "cooler.svg",
    "Monitors": "monitor.svg",
    "Keyboards": "keyboard.svg",
    "Mouse": "mouse.svg",
    "Microphones": "microphone.svg",
    "Headsets": "headset.svg",
    "Laptops": "laptop.svg",
    "Accessories": "accessories.svg",
    "Networking": "router.svg",
}

# Every product has a real photograph of the actual item, stored locally under
# backend/static/uploads/ and served via /uploads/. File name => product name.
PRODUCT_IMAGE_FILES = {
    # GPUs
    "NVIDIA GeForce RTX 5070": "nvidia-geforce-rtx-5070.png",
    "NVIDIA GeForce RTX 5080": "nvidia-geforce-rtx-5080.png",
    "AMD Radeon RX 9070 XT": "amd-radeon-rx-9070-xt.jpg",
    "Intel Arc B580": "intel-arc-b580.png",
    "ASUS TUF GeForce RTX 5070 Ti": "asus-tuf-geforce-rtx-5070-ti.png",
    # CPUs
    "AMD Ryzen 7 9800X3D": "amd-ryzen-7-9800x3d.jpg",
    "Intel Core i9-14900K": "intel-core-i9-14900k.png",
    "AMD Ryzen 5 9600X": "amd-ryzen-5-9600x.jpg",
    "Intel Core i5-14600K": "intel-core-i5-14600k.png",
    "AMD Ryzen 9 9950X": "amd-ryzen-9-9950x.png",
    # Motherboards
    "ASUS ROG STRIX B650E-F Gaming": "asus-rog-strix-b650e-f-gaming.png",
    "MSI MAG X670E TOMAHAWK WiFi": "msi-mag-x670e-tomahawk-wifi.png",
    "Gigabyte Z790 AORUS Elite AX": "gigabyte-z790-aorus-elite-ax.png",
    "ASRock B760M Pro RS": "asrock-b760m-pro-rs.png",
    # RAM
    "Corsair Vengeance 32GB DDR5-6000": "corsair-vengeance-32gb-ddr5-6000.webp",
    "G.Skill Trident Z5 RGB 32GB DDR5-6400": "g-skill-trident-z5-rgb-32gb-ddr5-6400.webp",
    "Kingston Fury Beast 16GB DDR4-3200": "kingston-fury-beast-16gb-ddr4-3200.png",
    "Crucial Pro 64GB DDR5-5600": "crucial-pro-64gb-ddr5-5600.png",
    # SSD
    "Samsung 990 PRO 2TB NVMe": "samsung-990-pro-2tb-nvme.jpg",
    "WD_BLACK SN850X 1TB": "wd-black-sn850x-1tb.png",
    "Crucial P3 Plus 1TB": "crucial-p3-plus-1tb.png",
    "Samsung 870 EVO 1TB SATA": "samsung-870-evo-1tb-sata.png",
    # HDD
    "Seagate BarraCuda 4TB": "seagate-barracuda-4tb.png",
    "WD Blue 2TB": "wd-blue-2tb.png",
    "Seagate IronWolf 8TB NAS": "seagate-ironwolf-8tb-nas.png",
    # Power Supplies
    "Corsair RM850x 850W Gold": "corsair-rm850x-850w-gold.webp",
    "EVGA 650 GQ 650W Gold": "evga-650-gq-650w-gold.png",
    "Seasonic FOCUS GX-750": "seasonic-focus-gx-750.png",
    # PC Cases
    "NZXT H5 Flow": "nzxt-h5-flow.png",
    "Lian Li Lancool 216": "lian-li-lancool-216.png",
    "Corsair 4000D Airflow": "corsair-4000d-airflow.png",
    # Cooling
    "Noctua NH-D15": "noctua-nh-d15.jpg",
    "NZXT Kraken 240 AIO": "nzxt-kraken-240-aio.jpg",
    "Thermalright Peerless Assassin 120": "thermalright-peerless-assassin-120.png",
    # Monitors
    "LG UltraGear 27GP850 27\"": "lg-ultragear-27gp850-27.png",
    "Samsung Odyssey G5 32\"": "samsung-odyssey-g5-32.png",
    "Dell S2421HGF 24\"": "dell-s2421hgf-24.png",
    # Keyboards
    "Keychron K8 Pro Wireless": "keychron-k8-pro-wireless.jpg",
    "Razer BlackWidow V4": "razer-blackwidow-v4.png",
    "Logitech G413 SE": "logitech-g413-se.png",
    # Mouse
    "Logitech G502 HERO": "logitech-g502-hero.png",
    "Razer DeathAdder V3": "razer-deathadder-v3.png",
    "Glorious Model O Wireless": "glorious-model-o-wireless.png",
    # Microphones
    "Shure MV7 USB Podcast Mic": "shure-mv7-usb-podcast-mic.jpg",
    "Blue Yeti X USB Mic": "blue-yeti-x-usb-mic.jpg",
    "Audio-Technica AT2020": "audio-technica-at2020.jpg",
    "Razer Seiren V2 X": "razer-seiren-v2-x.jpg",
    "HyperX QuadCast S": "hyperx-quadcast-s.png",
    # Headsets
    "SteelSeries Arctis Nova 7": "steelseries-arctis-nova-7.png",
    "HyperX Cloud II": "hyperx-cloud-ii.png",
    "Razer BlackShark V2": "razer-blackshark-v2.jpg",
    # Laptops
    "ASUS ROG Zephyrus G14": "asus-rog-zephyrus-g14.jpg",
    "Lenovo Legion 5 Pro": "lenovo-legion-5-pro.jpg",
    "Acer Nitro V 15": "acer-nitro-v-15.jpg",
    # Accessories
    "USB-C Docking Hub 8-in-1": "usb-c-docking-hub-8-in-1.png",
    "Logitech C920 HD Webcam": "logitech-c920-hd-webcam.jpg",
    "Arctic MX-6 Thermal Paste": "arctic-mx-6-thermal-paste.png",
    "RGB Gaming Mousepad XL": "rgb-gaming-mousepad-xl.png",
    # Networking
    "TP-Link Archer AX73 WiFi 6": "tp-link-archer-ax73-wifi-6.png",
    "NETGEAR Nighthawk AX5400": "netgear-nighthawk-ax5400.png",
}

# All products share the same sample image per category; easy to swap later.
_PRODUCTS = [
    # GPUs -----------------------------------------------------------------
    ("NVIDIA GeForce RTX 5070", "NVIDIA", "GPUs", 649.99, 699.99, 15, 4.8, 3,
     "The RTX 5070 brings next-generation ray tracing and DLSS 4 to a mainstream price point.",
     {"Memory": "12GB GDDR7", "Interface": "PCIe 5.0 x16", "Ports": "3x DisplayPort 2.1, 1x HDMI 2.1",
      "Power": "250W", "Warranty": "3 Years"}),
    ("NVIDIA GeForce RTX 5080", "NVIDIA", "GPUs", 1199.99, 1299.99, 7, 4.9, 2,
     "Flagship Blackwell gaming performance for 4K and high refresh rate displays.",
     {"Memory": "16GB GDDR7", "Interface": "PCIe 5.0 x16", "Ports": "3x DisplayPort 2.1, 1x HDMI 2.1",
      "Power": "360W", "Warranty": "3 Years"}),
    ("AMD Radeon RX 9070 XT", "AMD", "GPUs", 699.99, 749.99, 12, 4.7, 5,
     "RDNA 4 graphics card with excellent rasterised performance and 16GB of VRAM.",
     {"Memory": "16GB GDDR6", "Interface": "PCIe 5.0 x16", "Ports": "3x DisplayPort 2.1, 1x HDMI 2.1",
      "Power": "304W", "Warranty": "2 Years"}),
    ("Intel Arc B580", "Intel", "GPUs", 249.99, 279.99, 20, 4.5, 12,
     "Budget-friendly 1440p gaming GPU with AV1 encoding and 12GB memory.",
     {"Memory": "12GB GDDR6", "Interface": "PCIe 4.0 x8", "Ports": "3x DisplayPort 2.1, 1x HDMI 2.1",
      "Power": "190W", "Warranty": "3 Years"}),
    ("ASUS TUF GeForce RTX 5070 Ti", "ASUS", "GPUs", 829.99, 899.99, 9, 4.8, 4,
     "Military-grade TUF components with triple axial-tech fans and a metal backplate.",
     {"Memory": "16GB GDDR7", "Interface": "PCIe 5.0 x16", "Ports": "3x DisplayPort 2.1, 1x HDMI 2.1",
      "Power": "300W", "Warranty": "3 Years"}),

    # CPUs -----------------------------------------------------------------
    ("AMD Ryzen 7 9800X3D", "AMD", "CPUs", 479.99, 529.99, 18, 4.9, 1,
     "The undisputed gaming champion with 3D V-Cache and Zen 5 architecture.",
     {"Cores": "8C / 16T", "Base Clock": "4.7 GHz", "Boost Clock": "5.2 GHz",
      "Socket": "AM5", "TDP": "120W", "Warranty": "3 Years"}),
    ("Intel Core i9-14900K", "Intel", "CPUs", 549.99, 629.99, 10, 4.7, 20,
     "24-core unlocked desktop processor for extreme gaming and content creation.",
     {"Cores": "24C / 32T", "Base Clock": "3.2 GHz", "Boost Clock": "6.0 GHz",
      "Socket": "LGA1700", "TDP": "125W", "Warranty": "3 Years"}),
    ("AMD Ryzen 5 9600X", "AMD", "CPUs", 249.99, 279.99, 25, 4.6, 10,
     "Efficient 6-core Zen 5 processor, ideal for mid-range gaming builds.",
     {"Cores": "6C / 12T", "Base Clock": "3.9 GHz", "Boost Clock": "5.4 GHz",
      "Socket": "AM5", "TDP": "65W", "Warranty": "3 Years"}),
    ("Intel Core i5-14600K", "Intel", "CPUs", 289.99, 329.99, 22, 4.6, 18,
     "14-core unlocked CPU delivering strong value for gamers and creators.",
     {"Cores": "14C / 20T", "Base Clock": "3.5 GHz", "Boost Clock": "5.3 GHz",
      "Socket": "LGA1700", "TDP": "125W", "Warranty": "3 Years"}),
    ("AMD Ryzen 9 9950X", "AMD", "CPUs", 649.99, 699.99, 8, 4.8, 6,
     "16-core flagship for heavy multitasking, rendering and streaming.",
     {"Cores": "16C / 32T", "Base Clock": "4.3 GHz", "Boost Clock": "5.7 GHz",
      "Socket": "AM5", "TDP": "170W", "Warranty": "3 Years"}),

    # Motherboards ---------------------------------------------------------
    ("ASUS ROG STRIX B650E-F Gaming", "ASUS", "Motherboards", 259.99, 299.99, 14, 4.7, 9,
     "AM5 ATX board with PCIe 5.0, WiFi 6E and robust VRM cooling.",
     {"Socket": "AM5", "Form Factor": "ATX", "Memory": "4x DDR5 up to 128GB",
      "Expansion": "PCIe 5.0 x16", "Warranty": "3 Years"}),
    ("MSI MAG X670E TOMAHAWK WiFi", "MSI", "Motherboards", 289.99, 319.99, 11, 4.6, 14,
     "Feature-rich AM5 board with PCIe 5.0 M.2 and extended heatsinks.",
     {"Socket": "AM5", "Form Factor": "ATX", "Memory": "4x DDR5 up to 192GB",
      "Expansion": "PCIe 5.0 x16", "Warranty": "3 Years"}),
    ("Gigabyte Z790 AORUS Elite AX", "Gigabyte", "Motherboards", 239.99, 279.99, 13, 4.5, 22,
     "Intel LGA1700 board with DDR5 support and 2.5GbE networking.",
     {"Socket": "LGA1700", "Form Factor": "ATX", "Memory": "4x DDR5 up to 128GB",
      "Expansion": "PCIe 5.0 x16", "Warranty": "3 Years"}),
    ("ASRock B760M Pro RS", "ASRock", "Motherboards", 139.99, 159.99, 30, 4.4, 26,
     "Compact micro-ATX board with DDR5 and PCIe 4.0 for value builds.",
     {"Socket": "LGA1700", "Form Factor": "Micro-ATX", "Memory": "4x DDR5 up to 128GB",
      "Expansion": "PCIe 4.0 x16", "Warranty": "3 Years"}),

    # RAM ------------------------------------------------------------------
    ("Corsair Vengeance 32GB DDR5-6000", "Corsair", "RAM", 109.99, 129.99, 40, 4.8, 7,
     "Low-profile DDR5 kit with tight timings and AMD EXPO support.",
     {"Capacity": "32GB (2x16GB)", "Speed": "6000 MT/s", "Type": "DDR5",
      "Latency": "CL30", "Warranty": "Lifetime"}),
    ("G.Skill Trident Z5 RGB 32GB DDR5-6400", "G.Skill", "RAM", 139.99, 159.99, 25, 4.7, 11,
     "Premium RGB memory kit tuned for Intel XMP 3.0 platforms.",
     {"Capacity": "32GB (2x16GB)", "Speed": "6400 MT/s", "Type": "DDR5",
      "Latency": "CL32", "Warranty": "Lifetime"}),
    ("Kingston Fury Beast 16GB DDR4-3200", "Kingston", "RAM", 49.99, 59.99, 60, 4.6, 30,
     "Reliable plug-and-play DDR4 upgrade for older systems.",
     {"Capacity": "16GB (2x8GB)", "Speed": "3200 MT/s", "Type": "DDR4",
      "Latency": "CL16", "Warranty": "Lifetime"}),
    ("Crucial Pro 64GB DDR5-5600", "Crucial", "RAM", 199.99, 229.99, 15, 4.7, 8,
     "High-capacity DDR5 kit for workstations and heavy multitasking.",
     {"Capacity": "64GB (2x32GB)", "Speed": "5600 MT/s", "Type": "DDR5",
      "Latency": "CL46", "Warranty": "Lifetime"}),

    # SSD ------------------------------------------------------------------
    ("Samsung 990 PRO 2TB NVMe", "Samsung", "SSD", 179.99, 209.99, 30, 4.9, 4,
     "PCIe 4.0 NVMe SSD delivering up to 7450 MB/s sequential reads.",
     {"Capacity": "2TB", "Form Factor": "M.2 2280", "Interface": "PCIe 4.0 x4",
      "Read Speed": "7450 MB/s", "Warranty": "5 Years"}),
    ("WD_BLACK SN850X 1TB", "Western Digital", "SSD", 99.99, 119.99, 45, 4.8, 13,
     "Gaming-focused NVMe SSD with Game Mode 2.0 and low latency.",
     {"Capacity": "1TB", "Form Factor": "M.2 2280", "Interface": "PCIe 4.0 x4",
      "Read Speed": "7300 MB/s", "Warranty": "5 Years"}),
    ("Crucial P3 Plus 1TB", "Crucial", "SSD", 64.99, 79.99, 55, 4.6, 24,
     "Affordable PCIe 4.0 NVMe storage for everyday users.",
     {"Capacity": "1TB", "Form Factor": "M.2 2280", "Interface": "PCIe 4.0 x4",
      "Read Speed": "5000 MB/s", "Warranty": "5 Years"}),
    ("Samsung 870 EVO 1TB SATA", "Samsung", "SSD", 79.99, 89.99, 35, 4.7, 35,
     "Proven SATA SSD for laptops and desktops with 2.5-inch bays.",
     {"Capacity": "1TB", "Form Factor": "2.5 inch", "Interface": "SATA III",
      "Read Speed": "560 MB/s", "Warranty": "5 Years"}),

    # HDD ------------------------------------------------------------------
    ("Seagate BarraCuda 4TB", "Seagate", "HDD", 84.99, 94.99, 40, 4.5, 16,
     "High-capacity 3.5-inch hard drive for bulk storage.",
     {"Capacity": "4TB", "Form Factor": "3.5 inch", "Interface": "SATA III",
      "RPM": "5400 RPM", "Warranty": "2 Years"}),
    ("WD Blue 2TB", "Western Digital", "HDD", 54.99, 64.99, 50, 4.4, 28,
     "Dependable everyday storage drive with low power draw.",
     {"Capacity": "2TB", "Form Factor": "3.5 inch", "Interface": "SATA III",
      "RPM": "7200 RPM", "Warranty": "2 Years"}),
    ("Seagate IronWolf 8TB NAS", "Seagate", "HDD", 179.99, 199.99, 18, 4.7, 19,
     "Purpose-built NAS drive with multi-bay vibration tolerance.",
     {"Capacity": "8TB", "Form Factor": "3.5 inch", "Interface": "SATA III",
      "RPM": "7200 RPM", "Warranty": "3 Years"}),

    # Power Supplies -------------------------------------------------------
    ("Corsair RM850x 850W Gold", "Corsair", "Power Supplies", 139.99, 159.99, 20, 4.8, 6,
     "Fully modular 80 PLUS Gold PSU with silent zero-RPM mode.",
     {"Wattage": "850W", "Efficiency": "80 PLUS Gold", "Modular": "Fully Modular",
      "Fan": "135mm", "Warranty": "10 Years"}),
    ("EVGA 650 GQ 650W Gold", "EVGA", "Power Supplies", 79.99, 94.99, 28, 4.5, 33,
     "Reliable semi-modular PSU for mainstream gaming builds.",
     {"Wattage": "650W", "Efficiency": "80 PLUS Gold", "Modular": "Semi Modular",
      "Fan": "135mm", "Warranty": "5 Years"}),
    ("Seasonic FOCUS GX-750", "Seasonic", "Power Supplies", 109.99, 124.99, 22, 4.7, 21,
     "Compact ATX 3.0 ready unit with excellent ripple suppression.",
     {"Wattage": "750W", "Efficiency": "80 PLUS Gold", "Modular": "Fully Modular",
      "Fan": "120mm", "Warranty": "10 Years"}),

    # PC Cases -------------------------------------------------------------
    ("NZXT H5 Flow", "NZXT", "PC Cases", 89.99, 99.99, 25, 4.6, 15,
     "Airflow-optimised mid-tower with a clean cable management channel.",
     {"Type": "Mid Tower", "Motherboard": "ATX / Micro-ATX / ITX",
      "GPU Clearance": "365mm", "Side Panel": "Tempered Glass", "Warranty": "2 Years"}),
    ("Lian Li Lancool 216", "Lian Li", "PC Cases", 99.99, 114.99, 20, 4.8, 10,
     "High-airflow case with two 160mm ARGB front fans included.",
     {"Type": "Mid Tower", "Motherboard": "E-ATX / ATX / Micro-ATX",
      "GPU Clearance": "392mm", "Side Panel": "Tempered Glass", "Warranty": "2 Years"}),
    ("Corsair 4000D Airflow", "Corsair", "PC Cases", 94.99, 104.99, 30, 4.7, 23,
     "Clean builder-friendly case with a high-airflow front panel.",
     {"Type": "Mid Tower", "Motherboard": "ATX / Micro-ATX / ITX",
      "GPU Clearance": "360mm", "Side Panel": "Tempered Glass", "Warranty": "2 Years"}),

    # Cooling --------------------------------------------------------------
    ("Noctua NH-D15", "Noctua", "Cooling", 109.99, 119.99, 18, 4.9, 27,
     "Dual-tower air cooler with legendary quiet performance.",
     {"Type": "Air Cooler", "Height": "165mm", "Fans": "2x 140mm",
      "TDP": "250W", "Warranty": "6 Years"}),
    ("NZXT Kraken 240 AIO", "NZXT", "Cooling", 139.99, 159.99, 15, 4.6, 17,
     "240mm liquid cooler with an LCD display and quiet pump.",
     {"Type": "Liquid Cooler", "Radiator": "240mm", "Fans": "2x 120mm",
      "Socket": "AM5 / LGA1700", "Warranty": "6 Years"}),
    ("Thermalright Peerless Assassin 120", "Thermalright", "Cooling", 39.99, 49.99, 45, 4.8, 29,
     "Outstanding budget dual-tower cooler with great value.",
     {"Type": "Air Cooler", "Height": "155mm", "Fans": "2x 120mm",
      "TDP": "245W", "Warranty": "3 Years"}),

    # Monitors -------------------------------------------------------------
    ("LG UltraGear 27GP850 27\"", "LG", "Monitors", 349.99, 399.99, 12, 4.7, 12,
     "27-inch QHD IPS gaming monitor with 165Hz and 1ms response.",
     {"Size": "27 inch", "Resolution": "2560x1440", "Refresh Rate": "165Hz",
      "Panel": "IPS", "Warranty": "3 Years"}),
    ("Samsung Odyssey G5 32\"", "Samsung", "Monitors", 299.99, 349.99, 14, 4.5, 20,
     "Immersive 1000R curved QHD panel for gaming and work.",
     {"Size": "32 inch", "Resolution": "2560x1440", "Refresh Rate": "165Hz",
      "Panel": "VA", "Warranty": "3 Years"}),
    ("Dell S2421HGF 24\"", "Dell", "Monitors", 179.99, 199.99, 20, 4.4, 31,
     "Fast 144Hz full-HD gaming display with a slim bezel.",
     {"Size": "24 inch", "Resolution": "1920x1080", "Refresh Rate": "144Hz",
      "Panel": "TN", "Warranty": "3 Years"}),

    # Keyboards ------------------------------------------------------------
    ("Keychron K8 Pro Wireless", "Keychron", "Keyboards", 109.99, 119.99, 22, 4.7, 25,
     "Hot-swappable 75% mechanical keyboard with QMK/VIA support.",
     {"Layout": "75%", "Switch": "Gateron Brown", "Connection": "Bluetooth / USB-C",
      "Backlight": "RGB", "Warranty": "1 Year"}),
    ("Razer BlackWidow V4", "Razer", "Keyboards", 139.99, 159.99, 18, 4.6, 14,
     "Full-size mechanical keyboard with dedicated macro keys.",
     {"Layout": "Full Size", "Switch": "Razer Green", "Connection": "USB-C",
      "Backlight": "Chroma RGB", "Warranty": "2 Years"}),
    ("Logitech G413 SE", "Logitech", "Keyboards", 69.99, 79.99, 30, 4.4, 34,
     "Durable wired mechanical keyboard with PBT keycaps.",
     {"Layout": "Full Size", "Switch": "Tactile Brown", "Connection": "USB",
      "Backlight": "White LED", "Warranty": "2 Years"}),

    # Mouse --------------------------------------------------------------
    ("Logitech G502 HERO", "Logitech", "Mouse", 49.99, 59.99, 40, 4.8, 26,
     "Iconic gaming mouse with the HERO 25K sensor and tunable weights.",
     {"Sensor": "HERO 25K", "DPI": "25600", "Buttons": "11",
      "Connection": "Wired", "Warranty": "2 Years"}),
    ("Razer DeathAdder V3", "Razer", "Mouse", 69.99, 79.99, 28, 4.7, 16,
     "Ultra-light ergonomic mouse with the Focus Pro 30K sensor.",
     {"Sensor": "Focus Pro 30K", "DPI": "30000", "Buttons": "5",
      "Connection": "Wired", "Warranty": "2 Years"}),
    ("Glorious Model O Wireless", "Glorious", "Mouse", 79.99, 89.99, 24, 4.6, 22,
     "Honeycomb-shell wireless mouse weighing only 69 grams.",
     {"Sensor": "BAMF", "DPI": "19000", "Buttons": "6",
      "Connection": "Wireless", "Warranty": "2 Years"}),

    # Microphones ----------------------------------------------------------
    ("Shure MV7 USB Podcast Mic", "Shure", "Microphones", 249.99, 279.99, 14, 4.8, 8,
     "Dynamic USB/XLR podcast microphone with DSP and a built-in audio interface.",
     {"Type": "Dynamic USB/XLR", "Polar Pattern": "Cardioid", "Connection": "USB / XLR",
      "Frequency Response": "20Hz - 20kHz", "Warranty": "2 Years"}),
    ("Blue Yeti X USB Mic", "Logitech", "Microphones", 139.99, 159.99, 20, 4.6, 12,
     "Professional 4-capsule condenser microphone with LED level metering.",
     {"Type": "Condenser", "Polar Pattern": "4 patterns", "Connection": "USB",
      "Bit Depth": "24-bit / 48kHz", "Warranty": "2 Years"}),
    ("Audio-Technica AT2020", "Audio-Technica", "Microphones", 99.99, 119.99, 18, 4.7, 25,
     "Studio-grade side-address condenser microphone for vocals and instruments.",
     {"Type": "Condenser", "Polar Pattern": "Cardioid", "Connection": "XLR",
      "Frequency Response": "20Hz - 20kHz", "Warranty": "2 Years"}),
    ("Razer Seiren V2 X", "Razer", "Microphones", 99.99, 109.99, 22, 4.5, 16,
     "Compact streaming microphone with supercardioid pickup and USB-C output.",
     {"Type": "Condenser", "Polar Pattern": "Supercardioid", "Connection": "USB-C",
      "Bit Depth": "24-bit / 48kHz", "Warranty": "2 Years"}),
    ("HyperX QuadCast S", "HyperX", "Microphones", 139.99, 159.99, 16, 4.6, 20,
     "RGB condenser microphone with anti-vibration shock mount and tap-to-mute.",
     {"Type": "Condenser", "Polar Pattern": "4 patterns", "Connection": "USB-C",
      "Lighting": "RGB", "Warranty": "2 Years"}),

    # Headsets -------------------------------------------------------------
    ("SteelSeries Arctis Nova 7", "SteelSeries", "Headsets", 179.99, 199.99, 16, 4.8, 9,
     "Multi-platform wireless headset with 360 spatial audio.",
     {"Driver": "40mm", "Connection": "2.4GHz / Bluetooth", "Battery": "38 Hours",
      "Microphone": "ClearCast Gen 2", "Warranty": "2 Years"}),
    ("HyperX Cloud II", "HyperX", "Headsets", 89.99, 99.99, 30, 4.7, 32,
     "Comfortable gaming headset with virtual 7.1 surround sound.",
     {"Driver": "53mm", "Connection": "USB / 3.5mm", "Battery": "Wired",
      "Microphone": "Detachable", "Warranty": "2 Years"}),
    ("Razer BlackShark V2", "Razer", "Headsets", 99.99, 119.99, 25, 4.6, 19,
     "Lightweight esports headset with TriForce titanium drivers.",
     {"Driver": "50mm", "Connection": "3.5mm", "Battery": "Wired",
      "Microphone": "HyperClear Cardioid", "Warranty": "2 Years"}),

    # Laptops --------------------------------------------------------------
    ("ASUS ROG Zephyrus G14", "ASUS", "Laptops", 1499.99, 1599.99, 6, 4.8, 5,
     "14-inch gaming laptop with a QHD 165Hz display and RTX graphics.",
     {"CPU": "Ryzen 9 8945HS", "GPU": "RTX 4070", "RAM": "16GB DDR5",
      "Storage": "1TB NVMe", "Display": "14\" QHD 165Hz", "Warranty": "2 Years"}),
    ("Lenovo Legion 5 Pro", "Lenovo", "Laptops", 1199.99, 1349.99, 8, 4.7, 11,
     "16-inch gaming laptop with a bright 500-nit WQXGA panel.",
     {"CPU": "Core i7-13700HX", "GPU": "RTX 4060", "RAM": "16GB DDR5",
      "Storage": "1TB NVMe", "Display": "16\" WQXGA 165Hz", "Warranty": "2 Years"}),
    ("Acer Nitro V 15", "Acer", "Laptops", 749.99, 829.99, 12, 4.4, 21,
     "Entry-level gaming laptop offering great value for 1080p gaming.",
     {"CPU": "Core i5-13420H", "GPU": "RTX 4050", "RAM": "16GB DDR5",
      "Storage": "512GB NVMe", "Display": "15.6\" FHD 144Hz", "Warranty": "2 Years"}),

    # Accessories ----------------------------------------------------------
    ("USB-C Docking Hub 8-in-1", "Anker", "Accessories", 49.99, 59.99, 50, 4.5, 30,
     "Aluminium hub with HDMI, USB-A, SD card and 100W power delivery.",
     {"Ports": "8", "Video": "4K HDMI", "Power Delivery": "100W",
      "Connection": "USB-C", "Warranty": "2 Years"}),
    ("Logitech C920 HD Webcam", "Logitech", "Accessories", 59.99, 69.99, 35, 4.6, 36,
     "Full-HD 1080p webcam with dual microphones for clear calls.",
     {"Resolution": "1080p", "Frame Rate": "30fps", "Microphone": "Stereo",
      "Connection": "USB-A", "Warranty": "2 Years"}),
    ("Arctic MX-6 Thermal Paste", "Arctic", "Accessories", 9.99, 12.99, 80, 4.7, 40,
     "High-performance thermal compound, easy to spread and long lasting.",
     {"Amount": "4g", "Conductivity": "High", "Viscosity": "Medium",
      "Shelf Life": "8 Years", "Warranty": "N/A"}),
    ("RGB Gaming Mousepad XL", "SteelSeries", "Accessories", 24.99, 29.99, 60, 4.5, 38,
     "Extended cloth mousepad with a smooth, low-friction surface.",
     {"Size": "900x400mm", "Surface": "Cloth", "Base": "Non-slip Rubber",
      "Lighting": "RGB", "Warranty": "1 Year"}),

    # Networking -----------------------------------------------------------
    ("TP-Link Archer AX73 WiFi 6", "TP-Link", "Networking", 99.99, 119.99, 20, 4.6, 13,
     "Dual-band WiFi 6 router with 5400 Mbps combined throughput.",
     {"Standard": "WiFi 6", "Bands": "Dual Band", "Speed": "5400 Mbps",
      "Ports": "4x Gigabit LAN", "Warranty": "3 Years"}),
    ("NETGEAR Nighthawk AX5400", "NETGEAR", "Networking", 149.99, 169.99, 15, 4.5, 24,
     "High-performance WiFi 6 router for large homes and gamers.",
     {"Standard": "WiFi 6", "Bands": "Dual Band", "Speed": "5400 Mbps",
      "Ports": "4x Gigabit LAN", "Warranty": "1 Year"}),
]


def _discount(price, old_price):
    if old_price and old_price > price:
        return int(round((old_price - price) / old_price * 100))
    return 0


def build_products():
    """Return a list of product dicts ready to be inserted."""
    import json

    out = []
    for (name, brand, category, price, old_price, stock, rating, days_ago, desc, specs) in _PRODUCTS:
        image = "/uploads/" + PRODUCT_IMAGE_FILES.get(name, CATEGORY_META[category])
        out.append(
            {
                "name": name,
                "brand": brand,
                "category": category,
                "description": desc,
                "price": float(price),
                "old_price": float(old_price) if old_price else 0.0,
                "discount": _discount(price, old_price),
                "image": image,
                "images": json.dumps([image]),
                "stock": int(stock),
                "rating": float(rating),
                "specs": json.dumps(specs),
                "days_ago": int(days_ago),
            }
        )
    return out
