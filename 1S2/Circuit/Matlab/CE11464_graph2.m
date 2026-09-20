V1=input('Plase insert value of Voltage Source V1 = '); 
R1=input('Plase insert value of The Resister R1 = '); 
C1=input('Plase insert value of The Capacitor C1 = '); 
RL=input('Plase insert value of The Resister Load RL = '); 

w=10e2:10e3:10e7; 
w1=w.*(2.*pi); 
s=j*w1; 

n1=1/R1; 
d1=((1/R1)+(1/RL)+(s.*C1)); 
tr1=20.*log10(abs(n1./d1)); 
double pr1=phase(n1./d1); 

figure(1) 
semilogx(w,tr1,'b'),
axis([10e2 10e7 -60 20]),
xlabel('FREQUENCY(Hz)'),
ylabel('MAGNITUDE(dB)'),
grid