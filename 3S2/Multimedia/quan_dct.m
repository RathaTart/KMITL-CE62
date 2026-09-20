%This function performs quantization on an image block
%Yao Wang, Polytechnic University, 10/8/2003
function Qimg=quan_dct(Img,Qmatrix)

Qimg=round(Img./Qmatrix).*Qmatrix;
