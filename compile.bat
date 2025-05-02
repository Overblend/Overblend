@echo off
pyinstaller --onefile --noconsole home.py ^
  --exclude-module torch ^
  --exclude-module tensorflow ^
  --icon=icons/icon.ico ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\decord.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\avcodec-58.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\avdevice-58.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\avfilter-7.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\avformat-58.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\avutil-56.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\msvcp140.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\postproc-55.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\swresample-3.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\swscale-5.dll;decord" ^
  --add-data "C:\Users\leman\AppData\Local\Programs\Python\Python39\Lib\site-packages\decord\vcruntime140.dll;decord"
