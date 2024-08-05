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
#codegen.py
from pathlib import Path
from math import sqrt
import configparser
from datetime import datetime
import os

def read_coordinates_from_file(file_path):
    coordinates = []
    with open(file_path, 'r') as file:
        #skip the header line
        header = file.readline()
        
        # Read the rest of the lines
        for line in file:
            #split the line by commas and convert each value to float
            xmin, xmax, ymin, ymax = map(float, line.strip().split(','))
            coordinates.append({
                'xmin': xmin,
                'xmax': xmax,
                'ymin': ymin,
                'ymax': ymax
            })
    
    return coordinates

def check_overlap(box1, box2):
    #unpack the coordinates
    #note we skip image_name, prediction, confidence, which first three elements in shield coordinate
    _, _, _, xmin1, xmax1, ymin1, ymax1 = box1
    _, _, _, xmin2, xmax2, ymin2, ymax2 = box2

    #check for overlap
    overlap_x = not (xmin1 > xmax2 or xmax1 < xmin2)
    overlap_y = not (ymin1 > ymax2 or ymax1 < ymin2)

    return overlap_x and overlap_y

def check_for_overlaps(shield_coords):
    for i in range(len(shield_coords) - 1):
        current_box = shield_coords[i]
        next_box = shield_coords[i + 1]
        if check_overlap(current_box, next_box):
            return True
    return False
'''
def find_overlaps(shield_coords):
    overlaps = {}
    for i in range(len(shield_coords)):
        current_box = shield_coords[i]
        overlaps[i] = []
        for j in range(len(shield_coords)):
            if i != j:
                next_box = shield_coords[j]
                if check_overlap(current_box, next_box):
                    overlaps[i].append(j)
    return overlaps
'''

def find_overlaps(shield_coords):
    overlaps = {}
    processed_pairs = set()

    for i in range(len(shield_coords)):
        current_box = shield_coords[i]
        overlaps[i] = []
        for j in range(i + 1, len(shield_coords)):  # Start from i + 1 to avoid double counting
            next_box = shield_coords[j]
            pair = (i, j)
            if pair not in processed_pairs and check_overlap(current_box, next_box):
                overlaps[i].append(j)
                overlaps.setdefault(j, []).append(i)
                processed_pairs.add(pair)
                
    return overlaps

def phantom(countx,count,imgw,imgh,x,y,RI, proj, 
              activity, tally,maxcas,maxbch, 
                        scale,sx,sy,sz,shieldcount,xmins,xmaxs,ymins,ymaxs,shield_coords):



    #print(xmins,xmaxs,ymins,ymaxs)
    #print(shieldcount)

    #print(x,y)

    #file_path = 'shield_coordinates.txt'
    #coordinates = read_coordinates_from_file(file_path)
    #print(coordinates)

    #print(shield_coords)

    #txtfile.write(f'{image_name},{prediction},{confidence},"{xmin},{xmax},{ymin},{ymax}"\n')
    #txtfile.write(f'{xmin},{xmax},{ymin},{ymax}\n')
        

    #create a ConfigParser object
    config = configparser.ConfigParser()

    #read the parameters from the config file
    config.read('config.ini')
    rho1 = config['Parameters']['rho1'] #Lung
    rho2 = config['Parameters']['rho2'] #Heart
    rho3 = config['Parameters']['rho3'] #Blood
    rho4 = config['Parameters']['rho4'] #Disc
    rho5 = config['Parameters']['rho5'] #Vertebrae
    rho6 = config['Parameters']['rho6'] #Vertebrae up
    rho7 = config['Parameters']['rho7'] #Ribs
    rho8 = config['Parameters']['rho8'] #Ribs(1-9)
    rho9 = config['Parameters']['rho9'] #Soft Tissue
    rho10 = config['Parameters']['rho10'] #Skin
    rho11 = config['Parameters']['rho11'] #Skull
    rho12 = config['Parameters']['rho12'] #Brain
    rho13 = config['Parameters']['rho13'] #Facial-bone
    rho14 = config['Parameters']['rho14'] # mat 6 density
    rho15 = config['Parameters']['rho15'] #Arm-bone
    rho16 = config['Parameters']['rho16'] #Leg-bone
    lead = config['Parameters']['lead'] #lead shield material
    leadrho = config['Parameters']['leadrho'] #leadrho -- density of the lead shield
    concrete = config['Parameters']['concrete'] #concrete shield material
    concreterho = config['Parameters']['concreterho'] #concreterho -- density of the concrete shield
    pe = config['Parameters']['pe'] #polyethylene shield material
    perho = config['Parameters']['perho'] #perho -- density of the polyethylene shield
    custom = config['Parameters']['custom'] #custom defined shield material
    customrho = config['Parameters']['customrho'] #customrho -- density of the custom shield
    shieldHeight = config['Parameters']['shieldHeight'] #shield-height in cm
    icntl = config['Parameters']['icntl'] #icntl
    ih2o = config['Parameters']['ih2o'] #ih2o
    #dir = config['Parameters']['dir'] #dir
    dtime = config['Parameters']['dtime'] #dtime
    actlow = config['Parameters']['actlow'] #actlow
    mpi = config['Parameters']['mpi'] #mpi 0 = off / 1 = on
    ncore = config['Parameters']['ncore'] #number of mpi cores
    outfile = config['Parameters']['outfile'] #outfile name
    runphits = config['Parameters']['runphits'] #run phits option 0 = off / 1 = on
    backup = config['Parameters']['backup'] #backup tar.gz option 0 = off / 1 = on


    title='generated by PHITS RAPTOR-AI'
    #new file for each item
    output_dir = Path("working_dir")
    output_dir.mkdir(exist_ok=True)

    genfile_path = output_dir / f'gen_history.txt'
    with open(genfile_path, 'a') as txtfilegen:
        txtfilegen.write(f'latest user generated date: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n')


    shfile_path = output_dir / f'run_pos.sh'
    with open(shfile_path, 'a') as txtfilesh:
        txtfilesh.write(f'phits.sh  position_{count}/position_{count}.inp\n')
        txtfilesh.write(f'mv *.out *.eps ./position_{count}\n')


    position_dir = output_dir / f'position_{count}'
    position_dir.mkdir(parents=True, exist_ok=True)


    file_path = position_dir / f'position_{count}.inp'

    movx = x*int(scale)
    movy = y*int(scale)

    x0 = float(sx)*int(scale)
    y0 = float(sy)*int(scale)
    z0 = float(sz) #*int(scale)  #note the z-value for source will not be scaled

    xsq1 = -2.0 + movx 
    ysq1 = 1.0 + movy
    xsq1rl = 2.0 + movx 

    px1 = -2 + movx
    px2 = 2 + movx

    sx1 = -2.0 + movx
    sy1 = 1.0 + movy

    czx1 = 0.0 + movx
    czy1 = -7.8 + movy
    
    #static parameters
    #icntl = 0
    #ih2o = 69
    stype = 9
    #dir = 1.0
    
    #dtime = -10.00

    
    with open(file_path, 'w') as txtfile:
        if(int(mpi)==1):
            txtfile.write(f"$OMP = {ncore}\n")

        txtfile.write('[ T i t l e ]\n')
        txtfile.write(f"{title}\n")

        txtfile.write('\n')

        txtfile.write('[ P a r a m e t e r s ]\n')

        #txtfile.write('icntl   = ',f'{icntl}\n')
        txtfile.write(f" icntl   =  {icntl}\n")
        txtfile.write(f" maxcas   =  {maxcas}\n")
        txtfile.write(f" maxbch   =  {maxbch}\n")
        txtfile.write(' ireschk  =      1     # (D=0) Restart, 0:Check consistency, 1:No check\n')
        txtfile.write(f" ih2o   =  {ih2o}\n")
        txtfile.write(f" file(6)   =  {outfile}\n")


        txtfile.write('\n')

        txtfile.write('[ S o u r c e ]\n')

        txtfile.write(f" s-type   =  {stype}\n")
        txtfile.write(f" proj   =  {proj}\n")
        txtfile.write(' dir   =   all\n')
        txtfile.write(' r1   =  1.0E-10\n')
        txtfile.write(' r2   =  1.0E-10\n')
        txtfile.write(f" x0   =  {x0}\n")
        txtfile.write(f" y0   =  {y0}\n")
        txtfile.write(f" z0   =  {z0}\n")
        #txtfile.write(f"e0   =  {e0}\n")
        txtfile.write(' e-type   =   28\n')
        txtfile.write(' ni   =  1\n')
        txtfile.write(f" {RI}    {activity}\n")
        txtfile.write(f" dtime   =  {dtime}\n")
        txtfile.write(f" actlow   =  {actlow}\n")

        txtfile.write('\n')

        txtfile.write('[ M a t e r i a l ]\n')
        
        txtfile.write('mat[1]        $TISSUE-SOFT(ICRU-44)\n')
        txtfile.write(' 1000 -10.5\n')
        txtfile.write(' 6000 -25.6\n')
        txtfile.write(' 7000 -2.7\n')
        txtfile.write(' 8000 -60.2\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 15000 -0.2\n')
        txtfile.write(' 16000 -0.3\n')
        txtfile.write(' 17000 -0.2\n')
        txtfile.write(' 19000 -0.2\n')

        txtfile.write('\n')

        txtfile.write('mat[2]        $Heart-tissue(healthy)\n')
        txtfile.write(' 1000 -10.4\n')
        txtfile.write(' 6000 -13.9\n')
        txtfile.write(' 7000 -2.90\n')
        txtfile.write(' 8000 -71.8\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 15000 -0.2\n')
        txtfile.write(' 16000 -0.2\n')
        txtfile.write(' 17000 -0.2\n')
        txtfile.write(' 19000 -0.3\n')

        txtfile.write('\n')
        
        txtfile.write('mat[3]        $Blood(whole)\n')
        txtfile.write(' 1000 -10.2\n')
        txtfile.write(' 6000 -11.0\n')
        txtfile.write(' 7000 -3.3\n')
        txtfile.write(' 8000 -74.5\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 15000 -0.1\n')
        txtfile.write(' 16000 -0.2\n')
        txtfile.write(' 17000 -0.3\n')
        txtfile.write(' 19000 -0.2\n')
        txtfile.write(' 26000 -0.1\n')
        
        txtfile.write('\n')
        
        txtfile.write('mat[4]        $Lung(healthy-inflated)\n')
        txtfile.write(' 1000 -10.3\n')
        txtfile.write(' 6000 -10.5\n')
        txtfile.write(' 7000 -3.1\n')
        txtfile.write(' 8000 -74.9\n')
        txtfile.write(' 11000 -0.2\n')
        txtfile.write(' 15000 -0.2\n')
        txtfile.write(' 16000 -0.3\n')
        txtfile.write(' 17000 -0.3\n')
        txtfile.write(' 19000 -0.2\n')

        txtfile.write('\n')
        
        txtfile.write('mat[5]        $Brain(whole)\n')
        txtfile.write(' 1000 -10.7\n')
        txtfile.write(' 6000 -14.5\n')
        txtfile.write(' 7000 -2.2\n')
        txtfile.write(' 8000 -71.2\n')
        txtfile.write(' 11000 -0.2\n')
        txtfile.write(' 15000 -0.4\n')
        txtfile.write(' 16000 -0.2\n')
        txtfile.write(' 17000 -0.3\n')
        txtfile.write(' 19000 -0.3\n')

        txtfile.write('\n')

        txtfile.write('mat[6]        $Skin\n')
        txtfile.write(' 1000 -10.0\n')
        txtfile.write(' 6000 -20.4\n')
        txtfile.write(' 8000 -64.5\n')
        txtfile.write(' 11000 -0.2\n')
        txtfile.write(' 15000 -0.1\n')
        txtfile.write(' 16000 -0.2\n')
        txtfile.write(' 17000 -0.3\n')
        txtfile.write(' 19000 -0.1\n')

        txtfile.write('\n')
        
        txtfile.write('mat[7]        $Skull(ICRU)\n')
        txtfile.write(' 1000 -5.0\n')
        txtfile.write(' 6000 -21.2\n')
        txtfile.write(' 7000 -4.0\n')
        txtfile.write(' 8000 -43.5\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 12000 -0.2\n')
        txtfile.write(' 15000 -8.1\n')
        txtfile.write(' 16000 -0.3\n')
        txtfile.write(' 20000 -17.6\n')

        txtfile.write('\n')
        
        txtfile.write('mat[8]        $Leg-bone\n')
        txtfile.write(' 1000 -7.0\n')
        txtfile.write(' 6000 -34.5\n')
        txtfile.write(' 7000 -2.8\n')
        txtfile.write(' 8000 -36.8\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 12000 -0.1\n')
        txtfile.write(' 15000 -5.5\n')
        txtfile.write(' 16000 -0.2\n')
        txtfile.write(' 17000 -0.1\n')
        txtfile.write(' 20000 -12.9\n')

        txtfile.write('\n')

        txtfile.write('mat[9]        $Arm-bone\n')
        txtfile.write(' 1000 -6.0\n')
        txtfile.write(' 6000 -31.4\n')
        txtfile.write(' 7000 -3.1\n')
        txtfile.write(' 8000 -36.9\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 12000 -0.1\n')
        txtfile.write(' 15000 -7.0\n')
        txtfile.write(' 16000 -0.2\n')
        txtfile.write(' 20000 -15.2\n')

        txtfile.write('\n')

        txtfile.write('mat[10]        $Facial-bone\n')
        txtfile.write(' 1000 -4.6\n')
        txtfile.write(' 6000 -19.9\n')
        txtfile.write(' 7000 -4.1\n')
        txtfile.write(' 8000 -43.5\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 12000 -0.2\n')
        txtfile.write(' 15000 -8.6\n')
        txtfile.write(' 16000 -0.3\n')
        txtfile.write(' 20000 -18.7\n')

        txtfile.write('\n')

        txtfile.write('mat[11]        $Ribs(1-9)\n')
        txtfile.write(' 1000 -6.4\n')
        txtfile.write(' 6000 -26.3\n')
        txtfile.write(' 7000 -3.9\n')
        txtfile.write(' 8000 -43.6\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 12000 -0.1\n')
        txtfile.write(' 15000 -6.0\n')
        txtfile.write(' 16000 -0.3\n')
        txtfile.write(' 17000 -0.1\n')
        txtfile.write(' 19000 -0.1\n')
        txtfile.write(' 20000 -13.1\n')

        txtfile.write('\n')
        
        txtfile.write('mat[12]        $Ribs(10-12)\n')
        txtfile.write(' 1000 -5.6\n')
        txtfile.write(' 6000 -23.5\n')
        txtfile.write(' 7000 -4.0\n')
        txtfile.write(' 8000 -43.4\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 12000 -0.1\n')
        txtfile.write(' 15000 -7.2\n')
        txtfile.write(' 16000 -0.3\n')
        txtfile.write(' 17000 -0.1\n')
        txtfile.write(' 19000 -0.1\n')
        txtfile.write(' 20000 -15.6\n')

        txtfile.write('\n')
        
        txtfile.write('mat[13]        $Cervical-vertebrae\n')
        txtfile.write(' 1000 -6.3\n')
        txtfile.write(' 6000 -26.1\n')
        txtfile.write(' 7000 -3.9\n')
        txtfile.write(' 8000 -43.6\n')
        txtfile.write(' 11000 -0.1\n')
        txtfile.write(' 12000 -0.1\n')
        txtfile.write(' 15000 -6.1\n')
        txtfile.write(' 16000 -0.3\n')
        txtfile.write(' 17000 -0.1\n')
        txtfile.write(' 19000 -0.1\n')
        txtfile.write(' 20000 -13.3\n')

        txtfile.write('\n')
        
        txtfile.write('mat[14]        $Thoracic/Lumbal-vertebrae\n')
        txtfile.write(' 1000 -7.0\n')
        txtfile.write(' 6000 -28.7\n')
        txtfile.write(' 7000 -3.8\n')
        txtfile.write(' 8000 -43.7\n')
        txtfile.write(' 12000 -0.1\n')
        txtfile.write(' 15000 -5.1\n')
        txtfile.write(' 16000 -0.2\n')
        txtfile.write(' 17000 -0.1\n')
        txtfile.write(' 19000 -0.1\n')
        txtfile.write(' 20000 -11.1\n')

        txtfile.write('\n')
        
        txtfile.write('mat[15]        $Intervertebral-disks\n')
        txtfile.write(' 1000 -9.6\n')
        txtfile.write(' 6000 -9.9\n')
        txtfile.write(' 7000 -2.2\n')
        txtfile.write(' 8000 -74.4\n')
        txtfile.write(' 11000 -0.5\n')
        txtfile.write(' 15000 -2.2\n')
        txtfile.write(' 16000 -0.9\n')
        txtfile.write(' 17000 -0.3\n')

        txtfile.write('\n')
        
        txtfile.write('mat[16]        $AIR-DRY\n')
        txtfile.write(' 6000 -0.000124\n')
        txtfile.write(' 7000 -0.755267\n')
        txtfile.write(' 8000 -0.231781\n')
        txtfile.write(' 18000 -0.012827\n')

        #if(int(shieldcount) > 0):
        #    txtfile.write('\n')
        #    txtfile.write('mat[17]      $shield-material\n')
        #    txtfile.write(f" {shield}\n")
        
        if(int(shieldcount) > 0):
            written_materials = set() #ensures materials will be written only once

            for item in shield_coords:
                image_name, prediction, confidence, xmin, xmax, ymin, ymax = item
                
                if prediction == 'lead' and 'lead' not in written_materials:
                    txtfile.write('\n')
                    txtfile.write('mat[17]      $lead\n')
                    txtfile.write(f" {lead}\n")
                    written_materials.add('lead')
                    
                if prediction == 'concrete' and 'concrete' not in written_materials:
                    txtfile.write('\n')
                    txtfile.write('mat[18]      $concrete\n')
                    txtfile.write(f" {concrete}\n")
                    written_materials.add('concrete')
                    
                if prediction == 'pe' and 'pe' not in written_materials:
                    txtfile.write('\n')
                    txtfile.write('mat[19]      $polyethylene\n')
                    txtfile.write(f" {pe}\n")
                    written_materials.add('pe')
                    
                if prediction == 'custom' and 'custom' not in written_materials:
                    txtfile.write('\n')
                    txtfile.write('mat[20]      $custom-materials\n')
                    txtfile.write(f" {custom}\n")
                    written_materials.add('custom')

        txtfile.write('\n')

        txtfile.write('[ S u r f a c e ]\n')
        
        txtfile.write('$Left-Lung\n')
        txtfile.write(f"100 sq 0.00444444 0.02040816 0.001720426 0 0 0 -1 {xsq1} {ysq1} 21.79084544\n")
        txtfile.write(f"101 px {px1}\n")
        txtfile.write('102 pz 21.79084544\n')

        txtfile.write('$Right-Lung\n')
        txtfile.write(f"110 sq 0.00444444 0.02040816 0.001784477 0 0 0 -1 {xsq1rl} {ysq1} 22.22747566\n")
        txtfile.write(f"111 px {px2}\n")
        txtfile.write('112 pz 22.22747566\n')

        txtfile.write('$Sphere-out-heart\n')
        txtfile.write(f"200 s {sx1} {sy1} 31.5 5.8\n")
        
        txtfile.write('$Heart\n')
        txtfile.write(f"210 s {sx1} {sy1} 31.5 5.748\n")
        txtfile.write(f"211 s {sx1} {sy1} 31.5 4.861\n")

        txtfile.write('$Spine\n')
        txtfile.write(f"300 c/z {czx1} {czy1} 2\n")
        txtfile.write('301 pz 0\n')
        txtfile.write('302 pz 0.4\n') 
        txtfile.write('303 pz 2.7 $1\n') 
        txtfile.write('304 pz 3.1\n') 
        txtfile.write('305 pz 5.4 $2\n') 
        txtfile.write('306 pz 5.8\n') 
        txtfile.write('307 pz 8.1 $3\n') 
        txtfile.write('308 pz 8.5\n') 
        txtfile.write('309 pz 10.8 $4\n') 
        txtfile.write('310 pz 11.2\n') 
        txtfile.write('311 pz 13.5 $5\n') 
        txtfile.write('312 pz 13.9\n') 
        txtfile.write('313 pz 16.2 $6\n') 
        txtfile.write('314 pz 16.6\n') 
        txtfile.write('315 pz 18.9 $7\n') 
        txtfile.write('316 pz 19.3\n') 
        txtfile.write('317 pz 21.6 $8\n') 
        txtfile.write('318 pz 22.0\n') 
        txtfile.write('319 pz 24.3 $9\n') 
        txtfile.write('320 pz 24.7\n') 
        txtfile.write('321 pz 27.0 $10\n') 
        txtfile.write('322 pz 27.4\n') 
        txtfile.write('323 pz 29.7 $11\n') 
        txtfile.write('324 pz 30.1\n') 
        txtfile.write('325 pz 32.4 $12\n') 
        txtfile.write('326 pz 32.8\n') 
        txtfile.write('327 pz 35.1 $13\n') 
        txtfile.write('328 pz 35.5\n') 
        txtfile.write('329 pz 37.8 $14\n') 
        txtfile.write('330 pz 38.2\n') 
        txtfile.write('331 pz 40.5 $15\n') 
        txtfile.write('332 pz 40.9\n') 
        txtfile.write('333 pz 43.2 $16\n') 
        txtfile.write('334 pz 43.6\n') 
        txtfile.write('335 pz 45.9 $17\n') 
        txtfile.write('336 pz 46.1\n') 
        txtfile.write('337 pz 47.9 $18\n') 
        txtfile.write('338 pz 48.1\n') 
        txtfile.write('339 pz 49.9 $19\n') 
        txtfile.write('340 pz 50.1\n') 
        txtfile.write('341 pz 51.9 $20\n') 
        txtfile.write('342 pz 52.1\n') 
        txtfile.write('343 pz 53.9 $21\n') 
        txtfile.write('344 pz 54.1\n') 
        txtfile.write('345 pz 55.9 $22\n') 
        txtfile.write('346 pz 56.1\n') 
        txtfile.write('347 pz 57.9 $23\n') 
        txtfile.write('348 pz 58.1\n') 
        txtfile.write('349 pz 59.9 $24\n')

        txtfile.write('\n')
        
        txtfile.write('$Ribs\n') 
        txtfile.write('$12Rib\n')
        
        xsq2 = 0.0 + movx
        ysq2 = 0.59 + movy
        txtfile.write(f"400 sq 0.00308642 0.010519395 0 0 0 0 -1 {xsq2} {ysq2} 0 $in\n")
        txtfile.write(f"401 sq 0.002878115 0.009263368 0 0 0 0 -1 {xsq2} {ysq2} 0 $out\n")
        txtfile.write('402 pz 15 $313\n') 
        py1 = -2.0 + movy
        txtfile.write(f"480 py {py1}\n")

        xsq3 = 0.0 + movx
        ysq3 = 0.59 + movy
        txtfile.write('$11Rib\n')
        txtfile.write(f"403 sq 0.00308642 0.010519395 0 0 0 0 -1 {xsq3} {ysq3} 0 $in\n")
        txtfile.write(f"404 sq 0.002878115 0.009263368 0 0 0 0 -1 {xsq3} {ysq3} 0 $out\n")
        txtfile.write('405 pz 17.7 $315\n')
        py2 = 0.55 + movy
        txtfile.write(f"490 py {py2}\n")

        xsq4 = 0.0 + movx
        ysq4 = 0.59 + movy
        txtfile.write('$10Rib\n')
        txtfile.write(f"406 sq 0.00308642 0.010519395 0 0 0 0 -1 {xsq4} {ysq4} 0 $in\n")
        txtfile.write(f"407 sq 0.002878115 0.009263368 0 0 0 0 -1 {xsq4} {ysq4} 0 $out\n")
        txtfile.write('408 pz 20.4 $317\n')

        xsq5 = 0.0 + movx
        ysq5 = 0.57 + movy
        txtfile.write('$9Rib\n')
        txtfile.write(f"409 sq 0.003121945 0.010562685 0 0 0 0 -1 {xsq5} {ysq5} 0 $in\n")
        txtfile.write(f"410 sq 0.002910096 0.009299134 0 0 0 0 -1 {xsq5} {ysq5} 0 $out\n")
        txtfile.write('411 pz 23.1 $319\n')

        xsq6 = 0.0 + movx
        ysq6 = 0.475 + movy
        txtfile.write('$8Rib\n')
        txtfile.write(f"412 sq 0.003233681 0.0107944 0 0 0 0 -1 {xsq6} {ysq6} 0 $in\n")
        txtfile.write(f"413 sq 0.00300726 0.009471883 0 0 0 0 -1 {xsq6} {ysq6} 0 $out\n")
        txtfile.write('414 pz 25.69 $321\n')

        xsq7 = 0.0 + movx
        ysq7 = 0.405 + movy
        txtfile.write('$7Rib\n')
        txtfile.write(f"415 sq 0.003439128 0.01116243 0 0 0 0 -1 {xsq7} {ysq7} 0 $in\n")
        txtfile.write(f"416 sq 0.003158999 0.009602272 0 0 0 0 -1 {xsq7} {ysq7} 0 $out\n")
        txtfile.write('417 pz 28.42 $323\n')

        xsq8 = 0.0 + movx
        ysq8 = 0.255 + movy
        txtfile.write('$6Rib\n')
        txtfile.write(f"418 sq 0.003729807 0.011574473 0 0 0 0 -1 {xsq8} {ysq8} 0 $in\n")
        txtfile.write(f"419 sq 0.003406266 0.009890901 0 0 0 0 -1 {xsq8} {ysq8} 0 $out\n")
        txtfile.write('420 pz 31.22 $325\n')

        xsq9 = 0.0 + movx
        ysq9 = 0.05 + movy
        txtfile.write('$5Rib\n')
        txtfile.write(f"421 sq 0.00421031 0.011996607 0 0 0 0 -1 {xsq9} {ysq9} 0 $in\n")
        txtfile.write(f"422 sq 0.003842857 0.010306888 0 0 0 0 -1 {xsq9} {ysq9} 0 $out\n")
        txtfile.write('423 pz 33.96 $327\n')

        xsq10 = 0.0 + movx
        ysq10 = -0.235 + movy
        txtfile.write('$4Rib\n')
        txtfile.write(f"424 sq 0.004827003 0.012667331 0 0 0 0 -1 {xsq10} {ysq10} 0 $in\n")
        txtfile.write(f"425 sq 0.004401307 0.010930249 0 0 0 0 -1 {xsq10} {ysq10} 0 $out\n")
        txtfile.write('426 pz 36.64 $329\n')

        xsq11 = 0.0 + movx
        ysq11 = -0.65 + movy
        txtfile.write('$3Rib\n')
        txtfile.write(f"427 sq 0.006026361 0.013679423 0 0 0 0 -1 {xsq11} {ysq11} 0 $in\n")
        txtfile.write(f"428 sq 0.005501892 0.01194422 0 0 0 0 -1 {xsq11} {ysq11} 0 $out\n")
        txtfile.write('429 pz 39.37 $331\n')

        
        xsq12 = 0.0 + movx
        ysq12 = -1.15 + movy
        txtfile.write('$2Rib\n')
        txtfile.write(f"430 sq 0.008361921 0.015431503 0 0 0 0 -1 {xsq12} {ysq12} 0 $in\n")
        txtfile.write(f"431 sq 0.007514695 0.013364964 0 0 0 0 -1 {xsq12} {ysq12} 0 $out\n")
        txtfile.write('432 pz 42.07 $333\n')

        xsq13 = 0.0 + movx
        ysq13 = -2.1 + movy
        txtfile.write('$1Rib\n')
        txtfile.write(f"433 sq 0.018032466 0.019837334 0 0 0 0 -1 {xsq13} {ysq13} 0 $in\n")
        txtfile.write(f"434 sq 0.015443598 0.016866251 0 0 0 0 -1 {xsq13} {ysq13} 0 $out\n")
        txtfile.write('435 pz 44.77 $335\n')

        xsq14 = 0.0 + movx
        ysq14 = 4.0 + movy

        xsq15 = 0.0 + movx
        ysq15 = 3.0 + movy

        txtfile.write('$Sternum\n')
        txtfile.write(f"450 sq 0.00444444 0.02040816 0.001609643 0 0 0 -1 {xsq14} {ysq14} 21.8\n")
        txtfile.write(f"451 sq 0.00444444 0.02040816 0.001609643 0 0 0 -1 {xsq15} {ysq15} 21.8\n")

        px3 = -2.0 + movx
        px4 = 2.0 + movx

        py3 = 0.0 + movy

        txtfile.write(f"452 px {px3}\n")

        txtfile.write(f"453 px {px4}\n")

        txtfile.write('454 pz 25.6\n')

        txtfile.write('455 pz 46.2\n')

        txtfile.write(f"456 py {py3}\n")

        rcx1 = 0.0 + movx
        rcy1 = -6.5 + movy
        txtfile.write('$Neck\n')
        txtfile.write(f"500 RCC {rcx1} {rcy1} 48 0 0 8 5\n")

        rcx2 = 0.0 + movx
        rcy2 = -6.5 + movy

        txtfile.write('$Neck-skin\n')
        txtfile.write(f"501 RCC {rcx2} {rcy2} 48 0 0 8 5.2045\n")


        xsq16 = 0.0 + movx
        ysq16 = -2.0 + movy

        xsq17 = 0.0 + movx
        ysq17 = -2.0 + movy

        xsq18 = 0.0 + movx
        ysq18 = -2.0 + movy

        xsq19 = 0.0 + movx
        ysq19 = -2.0 + movy

        txtfile.write('$Face\n')
        txtfile.write(f"600 sq 0.020408163 0.01384083 0.031956196 0 0 0 -1 {xsq16} {ysq16} 66.266 $in\n")
        txtfile.write(f"601 sq 0.015625 0.011080332 0.022998638 0 0 0 -1 {xsq17} {ysq17} 66.266 $out\n")
        txtfile.write(f"602 sq 0.020408163 0.01384083 0 0 0 0 -1 {xsq18} {ysq18} 0 $in-cylinder\n")
        txtfile.write(f"603 sq 0.015625 0.011080332 0 0 0 0 -1 {xsq19} {ysq19} 0 $out-cylinder\n")
        txtfile.write('604 pz 56\n') 
        txtfile.write('605 pz 66.266\n')

        py4 = -0.605 + movy
        txtfile.write(f"606 py {py4}\n")


        xsq20 = 0.0 + movx
        ysq20 = -2.0 + movy

        xsq21 = 0.0 + movx
        ysq21 = -2.0 + movy

        txtfile.write('$Head-skin\n')
        txtfile.write(f"608 sq 0.01485579 0.010618268 0.021635842 0 0 0 -1 {xsq20} {ysq20} 66.266 $out\n")
        txtfile.write(f"609 sq 0.01485579 0.010618268 0 0 0 0 -1 {xsq21} {ysq21} 0 $out-cylinder\n")
        txtfile.write('610 pz 55.7955\n')

        rcx3 = -25.3290 + movx
        rcy3 = 0.0 + movy
        rcx4 = -25.3290 + movx
        rcy4 = 0.0 + movy

        txtfile.write('$Left-Arm\n')
        txtfile.write(f"700 RCC {rcx3} {rcy3} -12 0 0 30 4 $Fore\n")
        txtfile.write(f"701 RCC {rcx4} {rcy4} 18 0 0 30 5 $Upper\n")

        rcx5 = -25.3290 + movx
        rcy5 = 0.0 + movy
        rcx6 = -25.3290 + movx
        rcy6 = 0.0 + movy

        txtfile.write('$Left-Arm-bone\n')
        txtfile.write(f"702 RCC {rcx5} {rcy5} -12 0 0 30 3 $Fore\n")
        txtfile.write(f"703 RCC {rcx6} {rcy6} 18 0 0 30 3 $Upper\n")

        rcx7 = 25.3290 + movx
        rcy7 = 0.0 + movy
        rcx8 = 25.3290 + movx
        rcy8 = 0.0 + movy

        txtfile.write('$Right-Arm\n')
        txtfile.write(f"704 RCC {rcx7} {rcy7} -12 0 0 30 4 $Fore\n")
        txtfile.write(f"705 RCC {rcx8} {rcy8} 18 0 0 30 5 $Upper\n")

        rcx9 = 25.3290 + movx
        rcy9 = 0.0 + movy
        rcx10 = 25.3290 + movx
        rcy10 = 0.0 + movy

        txtfile.write('$Right-Arm-bone\n')
        txtfile.write(f"706 RCC {rcx9} {rcy9} -12 0 0 30 3 $Fore\n")
        txtfile.write(f"707 RCC {rcx10} {rcy10} 18 0 0 30 3 $Upper\n")

        txtfile.write('$Arms-skin\n')

        rcx11 = -25.3290  + movx
        rcy11 = 0.0 + movy
        rcx12 = 25.3290 + movx
        rcy12 = 0.0 + movy

        txtfile.write(f"708 RCC {rcx11} {rcy11} -12.1290 0 0 30.1290 4.1290 $Left\n")
        txtfile.write(f"709 RCC {rcx12} {rcy12} -12.1290 0 0 30.1290 4.1290 $Right\n")

        rcx13 = -25.3290 + movx
        rcy13 = 0.0 + movy
        rcx14 = 25.3290 + movx
        rcy14 = 0.0 + movy

        txtfile.write(f"710 RCC {rcx13} {rcy13} 18 0 0 30.1245 5.1245 $Left\n")
        txtfile.write(f"711 RCC {rcx14} {rcy14} 18 0 0 30.1245 5.1245 $Right\n")

        txtfile.write('$Left-Leg\n')

        rcx15 = -11 + movx
        rcy15 = 0.0 + movy
        rcx16 = -11 + movx
        rcy16 = 0.0 + movy

        txtfile.write(f"800 RCC {rcx15} {rcy15} -103.14 0 0 50.035 8 $Lower\n")
        txtfile.write(f"801 RCC {rcx16} {rcy16} -53.105 0 0 50.035 9 $Thigh\n")

        txtfile.write('$Left-Leg-bone\n')

        rcx17 = -11 + movx
        rcy17 = 0.0 + movy
        rcx18 = -11 + movx
        rcy18 = 0.0 + movy
        
        txtfile.write(f"802 RCC {rcx17} {rcy17} -103.14 0 0 50.035 5 $Lower\n")
        txtfile.write(f"803 RCC {rcx18} {rcy18} -53.105 0 0 50.035 5 $Thigh\n")
        
        txtfile.write('$Right-Leg\n')

        rcx19 = 11 + movx
        rcy19 = 0.0 + movy
        rcx20 = 11 + movx
        rcy20 = 0.0 + movy

        txtfile.write(f"804 RCC {rcx19} {rcy19} -103.14 0 0 50.035 8 $Lower\n")
        txtfile.write(f"805 RCC {rcx20} {rcy20} -53.105 0 0 50.035 9 $Thigh\n")

        txtfile.write('$Right-Leg-bone\n')

        rcx21 = 11 + movx
        rcy21 = 0.0 + movy
        rcx22 = 11 + movx
        rcy22 = 0.0 + movy

        txtfile.write(f"806 RCC {rcx21} {rcy21} -103.14 0 0 50.035 5 $Lower\n")
        txtfile.write(f"807 RCC {rcx22} {rcy22} -53.105 0 0 50.035 5 $Thigh\n")


        txtfile.write('$Leg-skin\n')

        rcx23 = -11 + movx
        rcy23 = 0.0 + movy
        rcx24 = 11 + movx
        rcy24 = 0.0 + movy

        txtfile.write(f"808 RCC {rcx23} {rcy23} -103.269 0 0 50.164 8.1290 $Left\n")
        txtfile.write(f"809 RCC {rcx24} {rcy24} -103.269 0 0 50.164 8.1290 $Right\n")

        txtfile.write('$Thigh\n')

        rcx25 = -11 + movx
        rcy25 = 0.0 + movy
        rcx26 = 11 + movx
        rcy26 = 0.0 + movy

        txtfile.write(f"810 RCC {rcx25} {rcy25} -53.105 0 0 50.035 9.1245 $Left\n")
        txtfile.write(f"811 RCC {rcx26} {rcy26} -53.105 0 0 50.035 9.1245 $Right\n")


        txtfile.write('$Trunk\n')

        xsq22 = 0.0 + movx
        ysq22 = 0.0 + movy

        txtfile.write(f"900 sq 0.0025 0.00756144 0 0 0 0 -1 {xsq22} {ysq22} 0\n")
        txtfile.write('901 pz -3.07\n')
        txtfile.write('902 pz 48\n')


        txtfile.write('$Trunk-skin\n')

        xsq23 = 0.0 + movx
        ysq23 = 0.0 + movy

        txtfile.write(f"903 sq 0.002449649 0.007299523 0 0 0 0 -1 {xsq23} {ysq23} 0\n")
        txtfile.write('904 pz -3.2745\n')
        txtfile.write('905 pz 48.2045\n')

        sor = round(sqrt(imgw**2 + imgh**2)*2*int(scale)) #(imgw*imgh*10)*int(scale)


        #******************
        
        #if(shield==1)then:
        if(int(shieldcount) > 0):
            txtfile.write('$Shields\n')
            #for i in range(int(shieldcount)):
            k = 0
            for item in shield_coords:
                image_name, prediction, confidence, xmin, xmax, ymin, ymax = item
                xmins = xmin*int(scale)
                xmaxs = xmax*int(scale)
                ymins = (imgh - ymax)*int(scale)
                ymaxs = (imgh - ymin)*int(scale)
                zmins = float(shieldHeight)/-2.
                zmaxs = float(shieldHeight)/2.
                #write(10,135) "910 RPP",shx,shx+shl, shy,shy+shw,"-110",shz
                txtfile.write(f"91{int(k)} RPP {xmins} {xmaxs} {ymins} {ymaxs} {zmins} {zmaxs}\n")
                k += 1
       

        #**********
       

        txtfile.write('$Outer-boundary\n')
        txtfile.write(f"1990 so {sor}\n")

        txtfile.write('\n')

        txtfile.write('[ C e l l ]\n')
        
        txtfile.write('1990    -1     1990\n')

        txtfile.write('$Left-Lung\n')
        
        txtfile.write(f"100 4 {rho1} -100 -101 102 200\n")
        txtfile.write(f"101 4 {rho1} -110 111 112 200\n")
        
        
        
        txtfile.write(f"200 2 {rho2} -210 211 $heart-tissue\n")

        
        txtfile.write(f"201 3 {rho3} -211 $blood\n")

        txtfile.write('$Spine\n')

        
        txtfile.write(f"300 15 {rho4} -300 301 -302 $Disc-24\n")
        txtfile.write(f"301 14 {rho5} -300 302 -303 $Vertebrae-lumbale-5\n")

        txtfile.write(f"302 15 {rho4} -300 303 -304 $Disc-23\n")
        txtfile.write(f"303 14 {rho5} -300 304 -305 $Vertebrae-lumbale-4\n")

        txtfile.write(f"304 15 {rho4} -300 305 -306 $Disc-22\n")
        txtfile.write(f"305 14 {rho5} -300 306 -307 $Vertebrae-lumbale-3\n")

        txtfile.write(f"306 15 {rho4} -300 307 -308 $Disc-21\n")
        txtfile.write(f"307 14 {rho5} -300 308 -309 $Vertebrae-lumbale-2\n")

        txtfile.write(f"308 15 {rho4} -300 309 -310 $Disc-20\n")
        txtfile.write(f"309 14 {rho5} -300 310 -311 $Vertebrae-lumbale-1\n")

        txtfile.write(f"310 15 {rho4} -300 311 -312 $Disc-19\n")
        txtfile.write(f"311 14 {rho5} -300 312 -313 $Thoracic-vertebrae-2\n")

        txtfile.write(f"312 15 {rho4} -300 313 -314 $Disc-18\n")
        txtfile.write(f"313 14 {rho5} -300 314 -315 $Thoracic-vertebrae-11\n")

        txtfile.write(f"314 15 {rho4} -300 315 -316 $Disc-17\n")
        txtfile.write(f"315 14 {rho5} -300 316 -317 $Thoracic-vertebrae-10\n")

        txtfile.write(f"316 15 {rho4} -300 317 -318 $Disc-16\n")
        txtfile.write(f"317 14 {rho5} -300 318 -319 $Thoracic-vertebrae-9\n")

        txtfile.write(f"318 15 {rho4} -300 319 -320 $Disc-15\n")
        txtfile.write(f"319 14 {rho5} -300 320 -321 $Thoracic-vertebrae-8\n")

        txtfile.write(f"320 15 {rho4} -300 321 -322 $Disc-14\n")
        txtfile.write(f"321 14 {rho5} -300 322 -323 $Thoracic-vertebrae-7\n")

        txtfile.write(f"322 15 {rho4} -300 323 -324 $Disc-13\n")
        txtfile.write(f"323 14 {rho5} -300 324 -325 $Thoracic-vertebrae-6\n")

        txtfile.write(f"324 15 {rho4} -300 325 -326 $Disc-12\n")
        txtfile.write(f"325 14 {rho5} -300 326 -327 $Thoracic-vertebrae-5\n")

        txtfile.write(f"326 15 {rho4} -300 327 -328 $Disc-11\n")
        txtfile.write(f"327 14 {rho5} -300 328 -329 $Thoracic-vertebrae-4\n")

        txtfile.write(f"328 15 {rho4} -300 329 -330 $Disc-10\n")
        txtfile.write(f"329 14 {rho5} -300 330 -331 $Thoracic-vertebrae-3\n")

        txtfile.write(f"330 15 {rho4} -300 331 -332 $Disc-9\n")
        txtfile.write(f"331 14 {rho5} -300 332 -333 $Thoracic-vertebrae-2\n")

        txtfile.write(f"332 15 {rho4} -300 333 -334 $Disc-8\n")
        txtfile.write(f"333 14 {rho5} -300 334 -335 $Thoracic-vertebrae-1\n")


        txtfile.write(f"334 15 {rho4} -300 335 -336 $Disc-7\n")
        txtfile.write(f"335 13 {rho6} -300 336 -337 $Cervical-vertebrae-7\n")

        txtfile.write(f"336 15 {rho4} -300 337 -338 $Disc-6\n")
        txtfile.write(f"337 13 {rho6} -300 338 -339 $Cervical-vertebrae-6\n")

        txtfile.write(f"338 15 {rho4} -300 339 -340 $Disc-5\n")
        txtfile.write(f"339 13 {rho6} -300 340 -341 $Cervical-vertebrae-5\n")

        txtfile.write(f"340 15 {rho4} -300 341 -342 $Disc-4\n")
        txtfile.write(f"341 13 {rho6} -300 342 -343 $Cervical-vertebrae-4\n")

        txtfile.write(f"342 15 {rho4} -300 343 -344 $Disc-3\n")
        txtfile.write(f"343 13 {rho6} -300 344 -345 $Cervical-vertebrae-3\n")

        txtfile.write(f"344 15 {rho4} -300 345 -346 $Disc-2\n")
        txtfile.write(f"345 13 {rho6} -300 346 -347 $Cervical-vertebrae-2\n")

        txtfile.write(f"346 15 {rho4} -300 347 -348 $Disc-1\n")
        txtfile.write(f"347 13 {rho6} -300 348 -349 $Cervical-vertebrae-1\n")

        txtfile.write('$Rib-cage\n')

        txtfile.write(f"400 12 {rho7} 300 400 -401 402 -313 -480 $Rib12\n")
        txtfile.write(f"401 12 {rho7} 300 403 -404 405 -315 -490 $Rib11\n")
        txtfile.write(f"402 12 {rho7} 300 406 -407 408 -317 $Rib10\n")
        txtfile.write(f"403 11 {rho8} 300 409 -410 411 -319 $Rib9\n")
        txtfile.write(f"404 11 {rho8} 300 412 -413 414 -321 $Rib8\n")
        txtfile.write(f"405 11 {rho8} 300 415 -416 417 -323 $Rib7\n")
        txtfile.write(f"406 11 {rho8} 300 418 -419 420 -325 $Rib6\n")
        txtfile.write(f"407 11 {rho8} 300 421 -422 423 -327 $Rib5\n")
        txtfile.write(f"408 11 {rho8} 300 424 -425 426 -329 $Rib4\n")
        txtfile.write(f"409 11 {rho8} 300 427 -428 429 -331 $Rib3\n")
        txtfile.write(f"410 11 {rho8} 300 430 -431 432 -333 $Rib2\n")
        txtfile.write(f"411 11 {rho8} 300 433 -434 435 -335 $Rib1\n")


        txtfile.write('$Sternum\n')



        txtfile.write(f"450 11 {rho8} -450 451 452 -453 454 -455 456 #404 #405 #406 #407 #408 #409 #410 #411\n")
        
        txtfile.write("$Neck\n")
        txtfile.write(f"500 1 {rho9} -500 #335 #336 #337 #338 #339 #340 #341 #342 #343 #344 #345 #346 #347\n")
        txtfile.write(f"501 6 {rho10} 500 -501 $Neck-skin\n")

        txtfile.write("$Head-Neck\n")



        txtfile.write(f"600 7 {rho11} 600 -601 $Skull\n")
        txtfile.write(f"601 5 {rho12} -600 $Brain\n")
        txtfile.write(f"602 10 {rho13} 602 -603 -605 604 606 #600 $Facial-bone\n")
        txtfile.write(f"603 1 {rho9} -603 -605 604 #600 #601 #602 #344 #345 #346 #347 $Soft-tissue\n")
        txtfile.write(f"604 6 {rho14} -608 601 605 $Head-skin\n")
        txtfile.write(f"605 6 {rho14} -609 603 604 -605 $Face-skin\n")
        txtfile.write(f"606 6 {rho14} -609 -604 610 #344 #345 #346 #347 #500 #501 $Lower-face-skin\n")

        #**************************************

        txtfile.write("$Arms\n")

        

        txtfile.write(f"700 1 {rho9} -700 702 $Left-arm-soft-tissue\n")
        txtfile.write(f"701 1 {rho9} -701 703 $Left-arm-soft-tissue\n")
        txtfile.write(f"702 9 {rho15} -702 $Lower-Left-bone\n")
        txtfile.write(f"703 9 {rho15} -703 $Upper-Left-bone\n")
        txtfile.write(f"704 1 {rho9} -704 706 $Lower-Right-tissue\n")
        txtfile.write(f"705 1 {rho9} -705 707 $Upper-Right-tissue\n")
        txtfile.write(f"706 9 {rho15} -706 $Lower-Right-bone\n")
        txtfile.write(f"707 9 {rho15} -707 $Upper-Right-bone\n")

        txtfile.write("$Arms-skin\n")

        txtfile.write(f"708 6 {rho10} 700 -708 $Lower-left\n")
        txtfile.write(f"709 6 {rho10} 704 -709 $Lower-right\n")
        txtfile.write(f"710 6 {rho10} 701 -710 $Upper-left\n")
        txtfile.write(f"711 6 {rho10} 705 -711 $Upper-right\n")

        txtfile.write("$Legs\n")

        txtfile.write(f"800 1 {rho9} -800 802\n")
        txtfile.write(f"801 1 {rho9} -801 803\n")
        txtfile.write(f"802 8 {rho16} -802\n")
        txtfile.write(f"803 8 {rho16} -803\n")
        txtfile.write(f"804 1 {rho9} -804 806\n")
        txtfile.write(f"805 1 {rho9} -805 807\n")
        txtfile.write(f"806 8 {rho16} -806\n")
        txtfile.write(f"807 8 {rho16} -807\n")

        txtfile.write("$Legs-skin\n")

        txtfile.write(f"808 6 {rho14} 800 -808 $Lower-left\n")
        txtfile.write(f"809 6 {rho14} 804 -809 $Lower-right\n")
        txtfile.write(f"810 6 {rho14} 801 -810 $Upper-left\n")
        txtfile.write(f"811 6 {rho14} 805 -811 $Upper-right\n")

        txtfile.write("$Trunk\n")

        txtfile.write(f"900 1 {rho9} -900 901 -902 #100 #101 #200 #201 #300 #301 #302 #303 #304 #305\n")
        txtfile.write("                          #306 #307 #308 #309 #310 #311 #312 #313 #314 #315\n")
        txtfile.write("                          #316 #317 #318 #319 #320 #321 #322 #323 #324 #325\n")
        txtfile.write("                          #326 #327 #328 #329 #330 #331 #332 #333 #334 #335\n")
        txtfile.write("                          #336 #337 #338 #339 #340 #341 #342 #343 #344 #345\n")
        txtfile.write("                          #346 #347 #400 #401 #402 #403 #404 #405 #406 #407\n")
        txtfile.write("                          #408 #409 #410 #411 #450\n")

        txtfile.write("$Trunk-skin\n")

        txtfile.write(f"901 6 {rho14} 900 -903 901 -902\n")
        txtfile.write(f"902 6 {rho14} -903 904 -901 #801 #803 #805 #807 #810 #811\n")
        txtfile.write(f"903 6 {rho14} -903 902 -905 #344 #345 #346 #347 #500 #501\n")


        overlaps_exist = check_for_overlaps(shield_coords)
        if overlaps_exist:
            print("Overlap detected between some boxes.")
        else:
            print("No overlaps detected between the boxes.")

        if(int(shieldcount) > 0):
            overlaps = find_overlaps(shield_coords)
            k=0
            for i in range(len(shield_coords) - 1):

                current_box = shield_coords[i]
                
                next_box = shield_coords[i + 1]
                #depends on the type of shield print the first one

                # Process the current box based on its prediction
                image_name, prediction, confidence, xmin, xmax, ymin, ymax = current_box

                # Prepare the overlap string
                overlap_str = ''
                if overlaps[i]:
                    overlap_str = ' #' + ' #'.join(f"91{j}" for j in overlaps[i])


                # Write the output based on prediction
                if prediction == 'lead':
                    txtfile.write(f"91{k} 17 {leadrho} -91{k}{overlap_str}\n")
                elif prediction == 'concrete':
                    txtfile.write(f"91{k} 18 {concreterho} -91{k}{overlap_str}\n")
                elif prediction == 'pe':
                    txtfile.write(f"91{k} 19 {perho} -91{k}{overlap_str}\n")
                elif prediction == 'custom':
                    txtfile.write(f"91{k} 20 {customrho} -91{k}{overlap_str}\n")

                k += 1

            # Handle the last box separately
            last_box = shield_coords[-1]
            image_name, prediction, confidence, xmin, xmax, ymin, ymax = last_box
            if prediction == 'lead':
                txtfile.write(f"91{k} 17 {leadrho} -91{k}\n")
            elif prediction == 'concrete':
                txtfile.write(f"91{k} 18 {concreterho} -91{k}\n")
            elif prediction == 'pe':
                txtfile.write(f"91{k} 19 {perho} -91{k}\n")
            elif prediction == 'custom':
                txtfile.write(f"91{k} 20 {customrho} -91{k}\n")

#            for item in shield_coords:
#                image_name, prediction, confidence, xmin, xmax, ymin, ymax = item
#                if(prediction=='lead'):
#                    #txtfile.write('\n')
#                    txtfile.write(f"91{k} 17 {leadrho} -91{k}\n")
#                    k += 1
#                if(prediction=='concrete'):
#                    txtfile.write(f"91{k} 18 {concreterho} -91{k}\n")
#                    k += 1
#                if(prediction=='pe'):
#                    txtfile.write(f"91{k} 19 {perho} -91{k}\n")
#                    k += 1
#                if(prediction=='custom'):
#                    txtfile.write(f"91{k} 20 {customrho} -91{k}\n")
#                    k += 1   

        #if(int(shieldcount) > 0):
        #    txtfile.write('$Shields\n')
        #    for i in range(int(shieldcount)):
        #        #write(10,135) "910 RPP",shx,shx+shl, shy,shy+shw,"-110",shz
        #        txtfile.write(f"91{i} 17 {shieldrho} -91{i}\n")

        txtfile.write("$Vaccuum-Air\n")

        txtfile.write("1991 16 -0.00129 -1990 #100 #101 #200 #201 #300 #301 #302 #303 #304 #305 #306 #307 #308\n")
        txtfile.write("           #309 #310 #311 #312 #313 #314 #315 #316 #317 #318 #319 #320 #321\n")
        txtfile.write("           #322 #323 #324 #325 #326 #327 #328 #329 #330 #331 #332 #333 #334\n")
        txtfile.write("           #335 #336 #337 #338 #339 #340 #341 #342 #343 #344 #345 #346 #347\n")
        txtfile.write("           #400 #401 #402 #403 #404 #405 #406 #407 #408 #409 #410 #411 #450\n")
        txtfile.write("           #500 #501 #600 #601 #602 #603 #604 #605 #606 #700 #701 #702 #703\n")
        txtfile.write("           #704 #705 #706 #707 #708 #709 #710 #711 #800 #801 #802 #803 #804\n")
        txtfile.write("           #805 #806 #807 #808 #809 #810 #811 #900 #901 #902 #903\n")

        subsets = []
        if(int(shieldcount) > 0):
            for i in range(int(shieldcount)):
                subsets.append(f"#91{i}")
            output_string = '           ' + ' '.join(subsets)  # Add 5 spaces at the start
                #txtfile.write(f"#91{i}\n")
            txtfile.write(output_string)

        txtfile.write("\n")
        txtfile.write("\n")

        txtfile.write("[ T - Gshow ]\n")
        txtfile.write("    title = generated human phantom xy\n")
        txtfile.write("    mesh =  xyz\n")
        txtfile.write("    x-type =    2\n")
        txtfile.write(f"    xmin =   {0.0:.3f}\n")
        txtfile.write(f"    xmax =   {imgw*int(scale)}\n")
        txtfile.write("    nx =   200\n")
        txtfile.write("    y-type =    2\n")
        txtfile.write(f"    ymin =   {0.0:.3f}\n")
        txtfile.write(f"    ymax =   {imgh*int(scale)}\n")
        txtfile.write("    ny =   100\n")
        txtfile.write("    z-type =    1\n")
        txtfile.write("    nz =    1\n")
        zminstal = float(shieldHeight)/-2.
        zmaxstal = float(shieldHeight)/2.
        txtfile.write(f"   {zminstal-10} {zmaxstal+10}\n")
        txtfile.write("axis =   xy\n")
        txtfile.write("file = top_view.out\n")
        txtfile.write("output =    2\n")
        txtfile.write("epsout =    1\n")

        
        txtfile.write("\n")


        txtfile.write("[ T - Deposit ]\n")
        txtfile.write("    title = selected organ doses in Gy/source\n")
        txtfile.write("    mesh =  reg\n")
        txtfile.write("    reg = 100 101 ( 200 201 ) ( { 300-347 } ) 601 ( { 604-606 } )\n")
        txtfile.write("    volume\n")
        txtfile.write("    reg      vol\n")
        txtfile.write("    100      2.1595E+03  #L-lung\n")
        txtfile.write("    101      2.4672E+03  #R-lung\n")
        txtfile.write("    1000001  8.1061E+02  #heart-tissue-blood\n")
        txtfile.write("    1000002  7.1064E+02  #spine-and-discs\n")
        txtfile.write("    601      1.3751E+03  #brain\n")
        txtfile.write("    1000003  2.2932E+02  #head-face-skin\n")
        txtfile.write("axis =   reg\n")
        txtfile.write(f"file = organ_deposit_{tally}.out\n")
        txtfile.write("unit  =  0\n")
        txtfile.write(f"part  =  {tally}\n")
        txtfile.write("material  =  all\n")
        txtfile.write("output =    dose\n")
        txtfile.write("epsout =    1\n")

        txtfile.write("\n")

        txtfile.write("[ T - Deposit ]\n")
        txtfile.write("    title = dose human phantom xy\n")
        txtfile.write("    mesh =  xyz\n")
        txtfile.write("    x-type =    2\n")
        txtfile.write(f"    xmin =   {0.0:.3f}\n")
        txtfile.write(f"    xmax =   {imgw*int(scale)}\n")
        txtfile.write("    nx =   200\n")
        txtfile.write("    y-type =    2\n")
        txtfile.write(f"    ymin =   {0.0:.3f}\n")
        txtfile.write(f"    ymax =   {imgh*int(scale)}\n")
        txtfile.write("    ny =   100\n")
        txtfile.write("    z-type =    1\n")
        txtfile.write("    nz =    1\n")
        zminstal = float(shieldHeight)/-2.
        zmaxstal = float(shieldHeight)/2.
        txtfile.write(f"   {zminstal-10} {zmaxstal+10}\n")
        txtfile.write("axis =   xy\n")
        txtfile.write("file = top_view_deposit.out\n")
        txtfile.write(f"part =   {tally}\n")
        txtfile.write("material =    all\n")
        txtfile.write("output =    dose\n")
        txtfile.write("unit =    2\n")
        txtfile.write("epsout =    1\n")

        txtfile.write("\n")




    now = datetime.now()
    formatted_datetime = now.strftime('%Y-%m-%d-%H-%M-%S-%f')
    
    #this only run if the option set to on/1
    if(count == countx):
        txtfilesh.close()
        if(int(runphits)==1):
            os.system('cd working_dir && sh run_pos.sh')
        if(int(backup)==1):
                bckfile_path = output_dir / f'backup.sh'
                with open(bckfile_path, 'w') as txtfilebck:    
                    txtfilebck.write(f'tar -cvzf backup_{formatted_datetime}.tar.gz ./*\n')
                txtfilebck.close()
                os.system('cd working_dir && sh backup.sh')

        os.system('echo "-------------------------"')
        os.system('echo "|       RUN DONE        |"')
        os.system('echo "-------------------------"')
                





