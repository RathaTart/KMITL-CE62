%plot motion field from MV stored in two coloumns

function []=plot_MV_function(dy,dx,bsize,mvy,mvx);
[r,c]=size(mvy);
[x,y]=meshgrid(0:bsize:(c-1)*bsize,0:bsize:(r-1)*bsize);
x=x+bsize/2; y=y+bsize/2;
quiver(x,y,mvx,mvy,0);

axis ij
axis([0,dx-1,0,dy-1])