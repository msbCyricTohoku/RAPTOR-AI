'''
 * RAPTOR-AI
 * Developed by: Mehrdad S. Beni and Hiroshi Watabe -- 2024

 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import subprocess
import os
import csv
from pathlib import Path
from codegen import phantom  #this calls the human phantom generator module

class InferenceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RAPTOR-AI")
        self.root.geometry("1280x800")  #change this to match your desired resolution and screen size
        
        #self.root.iconbitmap("icon.ico")
        icon_path = os.path.abspath("resources/icon.ico")  #load the icon for Raptor-Ai
        icon = ImageTk.PhotoImage(Image.open(icon_path))
        self.root.wm_iconphoto(True, icon)
	
	#change the background color of the main gui
        #root.configure(bg="#FFFFFF")
        
        style = ttk.Style()
        style.theme_use('default')

        style.configure("TFrame", background="#000000")
        style.configure("TLabel", background="#000000", foreground="#4de0eb")
        style.configure("TButton", background="#444444", foreground="#4de0eb")
        style.configure("TEntry", fieldbackground="#444444", foreground="#4de0eb")
        style.map("TEntry", 
          fieldbackground=[("disabled", "#444444"), ("focus", "#555555")],
          foreground=[("disabled", "#888888"), ("focus", "#4de0eb")])

        self.input_image_path = None
        self.output_image_path = None

        #these are the user controlled paramters from the gui
        self.radioisotope = tk.StringVar(value="Cs-137")
        self.particle = tk.StringVar(value="photon")
        self.activity = tk.StringVar(value="1000")
        self.tally = tk.StringVar(value="photon")
        self.maxcas = tk.StringVar(value="1000")
        self.maxbch = tk.StringVar(value="10")
        self.scale = tk.StringVar(value="1")
        self.sx = tk.StringVar(value="0.0")
        self.sy = tk.StringVar(value="0.0")
        self.sz = tk.StringVar(value="10.0")


        #this create the GUI frame for tk app
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(side=tk.TOP, pady=10)

        self.image_frame = tk.Frame(root)
        self.image_frame.pack(side=tk.TOP, pady=10)

        self.entry_frame = tk.Frame(root)
        self.entry_frame.pack(side=tk.TOP, pady=10)
    

        self.upload_btn = tk.Button(self.button_frame, text="Open", command=self.upload_image)
        self.upload_btn.pack(side=tk.LEFT, padx=10)

        self.run_inference_btn = tk.Button(self.button_frame, text="Run", command=self.run_inference)
        self.run_inference_btn.pack(side=tk.LEFT, padx=10)
        self.run_inference_btn.config(state=tk.DISABLED)

        self.about_btn = tk.Button(self.button_frame, text="About", command=self.show_about)
        self.about_btn.pack(side=tk.LEFT, padx=10)

        self.quit_btn = tk.Button(self.button_frame, text="Quit", command=root.quit)
        self.quit_btn.pack(side=tk.LEFT, padx=10)

        self.original_label = tk.Label(self.image_frame, text="User Features")
        self.original_label.grid(row=0, column=0, padx=10, pady=10)
        self.original_image_label = tk.Label(self.image_frame)
        self.original_image_label.grid(row=1, column=0, padx=10, pady=10)

        self.image_dimensions_label = tk.Label(self.image_frame, text="")
        self.image_dimensions_label.grid(row=2, column=0, padx=10, pady=10)

        self.inferred_label = tk.Label(self.image_frame, text="Detected Features")
        self.inferred_label.grid(row=0, column=1, padx=10, pady=10)
        self.inferred_image_label = tk.Label(self.image_frame)
        self.inferred_image_label.grid(row=1, column=1, padx=10, pady=10)
        
        #adding labels to the GUI for user controlled parameters
        custom_labels = [
            ("Radioisotope:", self.radioisotope),
            ("Particle:", self.particle),
            ("Activity (Bq):", self.activity),
            ("Tally:", self.tally),
            ("maxcas:", self.maxcas),
            ("maxbch:", self.maxbch),
            ("Scale (> 1):", self.scale),
            ("SX (cm):", self.sx),
            ("SY (cm):", self.sy),
            ("SZ (cm):", self.sz)
        ]


        #here we focus on a 2x5 grid considering the current supported user parameters controlled through the gui
        self.entries = []
        for i in range(5):
            label = tk.Label(self.entry_frame, text=custom_labels[i][0])
            label.grid(row=i, column=0, padx=10, pady=5)
            entry = tk.Entry(self.entry_frame, textvariable=custom_labels[i][1])
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries.append(entry)
        
        for i in range(5, 10):
            label = tk.Label(self.entry_frame, text=custom_labels[i][0])
            label.grid(row=i-5, column=2, padx=10, pady=5)
            entry = tk.Entry(self.entry_frame, textvariable=custom_labels[i][1])
            entry.grid(row=i-5, column=3, padx=10, pady=5)
            self.entries.append(entry)

    def upload_image(self):
        self.input_image_path = filedialog.askopenfilename()
        if self.input_image_path:
            
            img = Image.open(self.input_image_path)
            
            self.original_image_width, self.original_image_height = img.size
            
            #this reports the size of the image to the user which determine the simulation domain size in cm
            self.image_dimensions_label.config(text=f"Domain dimensions: Width: {self.original_image_width} cm, Height: {self.original_image_height} cm")
            
            self.display_image(self.input_image_path, self.original_image_label)
            self.run_inference_btn.config(state=tk.NORMAL)



    def run_inference(self):
        yolov5_path = 'yolov5'
        weights_path = 'trained_model/raptor-20240725.pt'
        source_dir = self.input_image_path
        output_dir = 'output'

        #change --conf value if you wish to tweak the confidence for detected marks
        subprocess.run([
            'python', f'{yolov5_path}/detect.py',
            '--weights', weights_path,
            '--img', '640',
            '--conf', '0.7',
            '--source', source_dir,
            '--project', output_dir,
            '--name', 'results',
            '--save-csv'
        ])

        output_base_dir = Path(output_dir)
        all_dirs = [d for d in output_base_dir.iterdir() if d.is_dir() and d.name.startswith('results')]

        latest_dir = max(all_dirs, key=os.path.getmtime)
        csv_file = latest_dir / 'predictions.csv'
        center_coords_file = latest_dir / 'center_coordinates.txt'
        #this file saves the shield coordinate in a shield_coordinate.txt 
        shield_coords_file = latest_dir / 'shield_coordinates.txt'

        #the detected box center will be determined and used as the location of human phantom on the defined domain
        def compute_center(xmin, ymin, xmax, ymax):
            center_x = (xmin + xmax) / 2
            center_y = (ymin + ymax) / 2
            # Flip y-axis
            flipped_center_y = self.original_image_height - center_y
            return center_x, flipped_center_y

        #pass the variables for shield to the codegen module call
        def sheild_coordinate_pass(xmin, xmax, ymin, ymax):
            xmins = xmin
            xmaxs = xmax
            ymins = ymin
            ymaxs = ymax
            return xmins, xmaxs, ymins, ymaxs

        #this is to save the xmin, xmax, ymin, ymax of the shield, given the shiled assumed to be a slab
        def save_shield_coordinates(coords):
            with open(shield_coords_file, 'w') as txtfile:
                #txtfile.write('Image Name,Prediction,Confidence,Coordinates (xmin,xmax,ymin,ymax)\n')
                txtfile.write('xmin,xmax,ymin,ymax\n')
                for item in coords:
                    image_name, prediction, confidence, xmin, xmax, ymin, ymax = item
                    #txtfile.write(f'{image_name},{prediction},{confidence},"{xmin},{xmax},{ymin},{ymax}"\n')
                    txtfile.write(f'{xmin},{xmax},{ymin},{ymax}\n')

        #here the coordinate of the detected boxes will be saved into a csv file
        center_coords = []
        #here the coordinate of the detected sheild box will be saved to a txt file
        shield_coords = []

        with open(csv_file, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            
            countx = 0
            shieldcount = 0 #initialize a counter fo the shield
            for row in csvreader:
                image_name = row['Image Name']
                prediction = row['Prediction']
                confidence = row['Confidence']
                coordinates = row['Coordinates'].strip('"').split(',')
                
                xmin, ymin, xmax, ymax = map(float, coordinates)
                #center_x, center_y = compute_center(xmin, ymin, xmax, ymax)
                
                #center_coords.append((image_name, prediction, confidence, center_x, center_y))
            
                #here we check if the prediction is actually shield
                #if prediction == 'shield':
                if prediction in ['lead', 'concrete', 'pe', 'custom']:
                    shieldcount += 1

                    xmins, xmaxs, ymins, ymaxs = sheild_coordinate_pass(xmin, xmax, ymin, ymax)

                    shield_coords.append((image_name, prediction, confidence, xmin, xmax, ymin, ymax))
                else:
                    countx += 1
                    center_x, center_y = compute_center(xmin, ymin, xmax, ymax)
                    center_coords.append((image_name, prediction, confidence, center_x, center_y))

        print("Total number of positions detected and processed:", countx)
        print("Total number of shields detected and processed:", shieldcount)
        
        #here the center coordinate will be sorted by x and y
        center_coords.sort(key=lambda x: (x[3], x[4]))
        save_shield_coordinates(shield_coords)

        
        #here write the sorted center coordinates to the text file and generate a new file for each item
        with open(center_coords_file, 'w') as txtfile:
            txtfile.write('x,y\n')
            count = 0
            for item in center_coords:
                count += 1
                image_name, prediction, confidence, center_x, flipped_center_y = item
                txtfile.write(f'{center_x},{flipped_center_y}\n')

                phantom(countx,count,self.original_image_width, self.original_image_height,center_x, flipped_center_y, 
                        self.radioisotope.get(), self.particle.get(), 
                        self.activity.get(), self.tally.get(), 
                        self.maxcas.get(), self.maxbch.get(), 
                        self.scale.get(), self.sx.get(), 
                        self.sy.get(), self.sz.get(),shieldcount,xmins,xmaxs,ymins,ymax,shield_coords)



        #inferred image path from the latest results directory
        inferred_image_path = latest_dir / Path(self.input_image_path).name
        if inferred_image_path.exists():
            self.display_image(inferred_image_path, self.inferred_image_label)

    def display_image(self, image_path, label):
        max_width, max_height = 400, 400
        img = Image.open(image_path)

        #here determines the scaling factor while preserving aspect ratio -- note this preserve aspect ratio
        width_ratio = max_width / img.width
        height_ratio = max_height / img.height
        scaling_factor = min(width_ratio, height_ratio)

        #here determines the new dimensions
        new_width = int(img.width * scaling_factor)
        new_height = int(img.height * scaling_factor)

        #here the image will be resized
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        img = ImageTk.PhotoImage(img)
        label.configure(image=img)
        label.image = img


    def show_about(self):
        messagebox.showinfo("RAPTOR-AI", "RAPTOR-AI\nVersion 1.0\nDeveloped by:\nMehrdad S. Beni\nHiroshi Watabe\nTohoku University, 2024")


if __name__ == "__main__":
    root = tk.Tk()
    app = InferenceApp(root)
    root.mainloop()
