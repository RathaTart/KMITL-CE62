V1 = input('Please insert value of Voltage Source V1 = '); 
R1 = input('Please insert value of The Resistor R1 = '); 
C1 = input('Please insert value of The Capacitor C1 = '); 
RL = input('Please insert value of The Resistor Load RL = '); 

w = 10e2:10e3:10e7; 
w1 = w.*(2*pi); 
s = 1i * w1; 

n1 = 1/R1; 
d1 = ((1/R1) + (1/RL) + (s .* C1)); 

tr1 = 20*log10(abs(n1./d1)); 
pr1 = angle(n1./d1); 

figure(1) 
semilogx(w, pr1, 'b'), axis([10e2 10e7 -pi pi]), xlabel('FREQUENCY (Hz)'), ylabel('PHASE (Rad)'), grid