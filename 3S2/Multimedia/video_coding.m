function video_coding(Anchor_Img, Predict_Img)

QP = input('Enter quantization factor (1 to 100):\n');
Anchor_Img = double(Anchor_Img);
Predict_Img = double(Predict_Img);
total_num = size(Anchor_Img,1) * size(Anchor_Img,2);
Qmatrix = ones(8,8) * QP;

close all;

% =====================
% ORIGINAL IMAGE PATH
% =====================
figure; imshow(uint8(Anchor_Img));
title('Original Image');

% DCT on original
Orig_dct = my_blockdct(Anchor_Img);
figure; imshow(uint8(abs(Orig_dct)/max(max(abs(Orig_dct)))*255));
title('DCT of Original Image');

% Quantize
QOrig_dct = my_blockquant(Orig_dct, Qmatrix);
num_zeros_QOrig = sum(sum(abs(QOrig_dct) > 0));
fprintf('Non-zero DCT coefficients in original image: %.4f%%\n', ...
    num_zeros_QOrig/total_num*100);
figure; imshow(uint8(abs(QOrig_dct)/max(max(abs(QOrig_dct))+eps)*255));
title('Quantized DCT of Original Image');

% Reconstruct
Recon_image = my_blockidct(QOrig_dct);
figure; imshow(uint8(Recon_image));
title('Reconstructed Image from Quantized DCT');

PSNR_orig = 10*log10(255^2 / mean(mean((Anchor_Img - Recon_image).^2)));
fprintf('PSNR (DCT on original image): %.4f dB\n', PSNR_orig);

% =====================
% ERROR IMAGE PATH
% =====================
Err_Img = Anchor_Img - Predict_Img;
figure; imshow(uint8(Err_Img + 128));
title('Original Error Image');

% DCT on error
Err_dct = my_blockdct(Err_Img);
figure; imshow(uint8(abs(Err_dct)/max(max(abs(Err_dct))+eps)*255));
title('DCT of Error Image');

% Quantize
QErr_dct = my_blockquant(Err_dct, Qmatrix);
num_zeros_QErr = sum(sum(abs(QErr_dct) > 0));
fprintf('Non-zero DCT coefficients in error image: %.4f%%\n', ...
    num_zeros_QErr/total_num*100);
figure; imshow(uint8(abs(QErr_dct)/max(max(abs(QErr_dct))+eps)*255));
title('Quantized DCT of Error Image');

% Reconstruct error
Recon_err = my_blockidct(QErr_dct);
figure; imshow(uint8(Recon_err + 128));
title('Reconstructed Error Image');

% Final reconstructed image
Recon_final = Predict_Img + Recon_err;
figure; imshow(uint8(Recon_final));
title('Reconstructed Image with Prediction');

PSNR_err = 10*log10(255^2 / mean(mean((Anchor_Img - Recon_final).^2)));
fprintf('PSNR (DCT on error image): %.4f dB\n', PSNR_err);

end

% =============================
% Helper: Block DCT (no toolbox)
% =============================
function out = my_blockdct(img)
    [rows, cols] = size(img);
    out = zeros(rows, cols);
    for r = 1:8:rows
        for c = 1:8:cols
            re = min(r+7, rows);
            ce = min(c+7, cols);
            block = img(r:re, c:ce);
            out(r:re, c:ce) = my_dct2(block);
        end
    end
end

% =============================
% Helper: Block IDCT (no toolbox)
% =============================
function out = my_blockidct(img)
    [rows, cols] = size(img);
    out = zeros(rows, cols);
    for r = 1:8:rows
        for c = 1:8:cols
            re = min(r+7, rows);
            ce = min(c+7, cols);
            block = img(r:re, c:ce);
            out(r:re, c:ce) = my_idct2(block);
        end
    end
end

% =============================
% Helper: Block Quantize
% =============================
function out = my_blockquant(img, Qmatrix)
    [rows, cols] = size(img);
    out = zeros(rows, cols);
    for r = 1:8:rows
        for c = 1:8:cols
            re = min(r+7, rows);
            ce = min(c+7, cols);
            block = img(r:re, c:ce);
            out(r:re, c:ce) = quan_dct(block, Qmatrix);
        end
    end
end

% =============================
% 2D DCT (no toolbox)
% =============================
function D = my_dct2(block)
    [M, N] = size(block);
    D = zeros(M, N);
    for u = 0:M-1
        for v = 0:N-1
            if u == 0, cu = 1/sqrt(M); else, cu = sqrt(2/M); end
            if v == 0, cv = 1/sqrt(N); else, cv = sqrt(2/N); end
            s = 0;
            for x = 0:M-1
                for y = 0:N-1
                    s = s + block(x+1,y+1) * ...
                        cos((2*x+1)*u*pi/(2*M)) * ...
                        cos((2*y+1)*v*pi/(2*N));
                end
            end
            D(u+1, v+1) = cu * cv * s;
        end
    end
end

% =============================
% 2D IDCT (no toolbox)
% =============================
function block = my_idct2(D)
    [M, N] = size(D);
    block = zeros(M, N);
    for x = 0:M-1
        for y = 0:N-1
            s = 0;
            for u = 0:M-1
                for v = 0:N-1
                    if u == 0, cu = 1/sqrt(M); else, cu = sqrt(2/M); end
                    if v == 0, cv = 1/sqrt(N); else, cv = sqrt(2/N); end
                    s = s + cu * cv * D(u+1,v+1) * ...
                        cos((2*x+1)*u*pi/(2*M)) * ...
                        cos((2*y+1)*v*pi/(2*N));
                end
            end
            block(x+1, y+1) = s;
        end
    end
end