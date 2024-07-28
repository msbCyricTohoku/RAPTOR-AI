* RAPTOR-AI -- Draw/Track/Model
* Developed by: Mehrdad S. Beni and Hiroshi Watabe, 2024

RAPTOR-AI model that takes user input images marked with "x" (note must be drawn) locations on the uploaded image. The program is coupled with a custom-trained AI model that automatically detects and track these drawn locations. Based on these locations, the program then generates anthropomorphic phantom with that respective drawn and tracked locations. 

The model was developed on and for GNU/Linux operating systems ONLY. 

How to:

1. sudo apt update
2. sudo apt upgrade
3. sudo apt install python3 python3-pip python3-tk python3-pil python3-pil.imagetk python3-venv
4. python3 -m venv .venv
5. source .venv/bin/activate
6. run "make install", this installs all the dependencies (note if you have conflict, just keep using your own version of libs)
7. run "make" -- you will see the GUI of the RAPTOR-AI
8. click on "open" navigate to "test" folder containing the images.
9. as an example select "cyrric_marked2.png" and open.
10. change the parameter for your Monte Carlo model such as isotope, maxcas, etc.
11. click on "Run" -- wait for the run to complete and you must be able to see the detected features on the right side. The marks are detected by the trained AI model.
12. you can close the program. Your generated scripts can be found under "working_dir" folder. Also, the detected feature image can be found under "output" folder. 
13. open "config.ini", you can turn on the "runphits" function so that the program automatically runs all your generated scripts for every detected position automatically. (set the value to 1 to turn on)
14. considering the "backup" option, the program automatically generates a tar.gz backup of your "working_dir" for you. (set the value to 1 to turn on)

Should you encounter any bugs or issues, please do not hesitate to contact me via email.

enjoy!
20240725
