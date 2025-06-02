# SJCAM-Wireless-Feed
This repository provides tools to capture the wireless live feed from an SJCAM 4000 Air WiFi-enabled action camera

The wireless feed is obtained via RTSP protocol while connected to the camera's wifi on AP Mode.

The camera's IP is 192.168.100.1 and it uses ports 6666 with TCP protocol for sending login information and keep alive packets and 6669 with UDP protocol for receving live feed.

The streaming works with 1-3 seconds of delay using ffmpeg



This work is heavly based on bauripalash CamDumper project 
https://github.com/bauripalash/CamDumper