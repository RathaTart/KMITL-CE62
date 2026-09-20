% exhaustive search block matching (EBMA) algorithm with half-pel accuracy
% Modified from EBMA_integer(..)
% Yao Wang, 10/8/2003, Polytechnic University
%
function [vm,hm,pframe]=EBMA_half(refframe, newframe, row, col, bsize, vrange, hrange, vm, hm, pframe);

%up sample refframe using bilinear interpolation
row2=row*2; col2=col*2;

refframe2(1:2:row2,1:2:col2)=refframe(1:row,1:col);
refframe2(1:2:row2,2:2:col2-2)=(refframe(1:row,1:col-1)+refframe(1:row,2:col))/2;
refframe(1:2:row2,col2)=refframe(1:row,col);

refframe2(2:2:row2-2,1:2:col2)=(refframe(1:row-1,1:col)+refframe(2:row,1:col))/2;
refframe2(row2,1:2:col2)=refframe(row,1:col);
refframe2(2:2:row2-2,2:2:col2-2)=(refframe(1:row-1,1:col-1)+...
   refframe(1:row-1,2:col)+refframe(2:row,1:col-1)+refframe(2:row,2:col))/4;
refframe2(2:2:row2-2,col2)=(refframe(1:row-1,col)+refframe(2:row,col))/2;
refframe2(row2,2:2:col2-2)=(refframe(row,1:col-1)+refframe(row,2:col))/2;
refframe2(row2,col2)=refframe(row,col);

%figure; imshow(uint8(refframe2)); title('Upsampled Target Image');

bsize1=bsize-1;
br=0;
for r=1:bsize:row-bsize1
   br=br+1;
   bc=0;
   for c=1:bsize:col-bsize1
      bc=bc+1;
         
      
      %assuming vm,hm store initial motion field
      v0=vm(br,bc);
      h0=hm(br,bc);
      x=newframe(r:r+bsize1, c:c+bsize1)-refframe2(2*(r+v0)-1:2:2*(r+v0+bsize1)-1, 2*(c+h0)-1:2:2*(c+h0+bsize1)-1);
      err0=sum(sum(abs(x)));
      minerr=err0;
      vmin=v0;hmin=h0;
      

      for v=-vrange+v0:0.5:vrange+v0
         for h=-hrange+h0:0.5:hrange+h0
            if ((r+v>=1) & (r+v<=row-bsize1) & (c+h>=1) & (c+h<=col-bsize1))
               x=newframe(r:r+bsize1, c:c+bsize1)- ...
                  refframe2(2*(r+v)-1:2:2*(r+v+bsize1)-1, 2*(c+h)-1:2:2*(c+h+bsize1)-1);
               err=sum(sum(abs(x))); 
               
               if (err<minerr)
                  minerr=err;
                  hmin=h; vmin=v;
               end;       
            end
         end     %the motion search window    
      end
      
      if (minerr>(err0-100))%favor 0 MV if error is similar
         hmin=h0;
         vmin=v0;
         minerr=err0;
      end;
      
      vm(br,bc)=vmin;
      hm(br,bc)=hmin;  
      pframe(r:r+bsize1, c:c+bsize1)=refframe2(2*(r+vmin)-1:2:2*(r+vmin+bsize1)-1, 2*(c+hmin)-1:2:2*(c+hmin+bsize1)-1);
      
   end
   %display the result for last block of each row 
   disp([r,c,br,bc,vmin,hmin, minerr]);
end

