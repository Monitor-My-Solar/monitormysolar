# Changelog for release 2.5.0 
Hours and hours of work has gone into this release to ensure stability and cross compatibility. We are only human and mistakes do happen. If you happen to find a bug please submit a bug report via our contact us or the web portal.
## iOS and Android Apps 
Both of these are in public beta, they are nearly finished and will be released at the same time as the V2 of the web portal. When V2 of the web portal launches Every current user will get two months Silver subscription for free this will enable you all to see the live data on the website and apps. once the free trial is over we will revert to the same graduality that the manufacturer offers for both stored and displaying data.
## Fixes:
- Memory leak when connecting to EG4 or Lux power, where on reconnection after 10 or so tries the dongle would reboot in panic
- Retry logic in Lux/EG4 Connection where by it would never reconnect or the socket would become lost
- MQTT Services reconnection where a reconnection event would trigger a panic 
- LED logic where occasionally LED'S would get stuck in the off mode 
- Restart/Reset Button, this now does as it was intended. single press will instigate a reboot (LED will flash green before reboot), long press will restore to factory settings 
- local domain MDNS corrected dongle will now search for other dongles on the network and name itself accordingly ```monitormysolar.local, monitormysolar-1.local```
- Webservices, pages and various bugs around the UX. 
- Settings not setting via the MQTT reliably this has now been completely re written solving the timing issue previously faced 
- NTP service not responding 
- Status topic not reporting correctly 
- WiFi not connecting correctly 
- TLS based issues where there are strict memory requirements. This is part of the memory leak issue but is now resolved


## Changes 
- Wifi LED will now follow the following procedure: 
  - On == Connected 
  - Off == Disconnected/not retrying
  - Flashing == Disconnected/Retrying 
- Setup process now includes picking a region please pick the closet timezone to you
- Setup process now requires a pin number of the dongle to be given to link to a plant or check the plant its registered too. For legacy users without the pin number please contact us for your pin number
- No more UI/UX updates. All files are now stored in flash and part of the firmware file. a single firmware now does everything 
- API Endpoints will be exposed and explained on the knowledge base in due course 
- Additional config added for Ethernet. Standard dongles will have no use for this feature. 
- Added support for Multicast for the IHD 

## New Features 
### Advanced settings 
- Local Firmware uploader, this is for beta firmware or if the OTA update fails you can download the FW from here and update 
- Change the local MQTT DongleID, this is if you get a replacement dongle and you need to keep the HA data the same or you want to use the original dongleID you can now set this in advanced settings this has to be in the correct format ```dongle-F0:F5:BD:23:9A:2C```
- Change the local Client ID for MQTT. 
- Make the manufacturers' connection (Lux/EG4) Read only. No settings can be changed when this is enabled
- Have the dongle keep the inverter to NTP time. With this enabled and the region correctly set, the dongle will keep the inverters time correct to the region and DST without the need for user intervention
- Scheduled settings page, this is in anticipation for the ability to be able to set daily, weekly, monthly settings on the web portal. all config will be done server side but the dongle will manage the schedule 
