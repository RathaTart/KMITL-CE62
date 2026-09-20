%meshtest.m
%Create: 06/01/2024, 08.00 
%Modify: %01076108 Circuits and Electronics in Practice 
%Laboratorys: Basic Electronics and Circuit in Analysis by MATLAB 
%การทดลองเรือง การวเคราะหวงจรไฟฟาและวงจรอเลกทรอนกสดวย MATLAB เบืองตน 
%อาจารยผสอน: ผศ.สรพงษ วชรรตนพรกล 
%Lecturer: Asst.Porf. SORAPONG WACHIRARATTANAPORNKUL %การทดลองส่วนที 1 การวเคราะหวงจรดวยวธ Mesh  
clear all; 
clc; 
V1=input('Plase insert value of Voltage Source V1 = '); 
V2=input('Plase insert value of Voltage Source V2 = '); 
R1=input('Plase insert value of The Resister R1 = '); 
R2=input('Plase insert value of The Resister R2 = '); 
R3=input('Plase insert value of The Resister R3 = ');  
a=[(R1+R3) R3; R3 (R2+R3)] 
b=[V1 R3; V2 (R2+R3)] 
c=[(R1+R3) V1; R3 V2]  
I1=det(b)./det(a) 
I2=det(c)./det(a) 
IR3=I1+I2 