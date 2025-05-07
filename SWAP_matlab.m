clc;
clear;
%% Prepare for data traversal
datapre = 'E:\'; % Specify the folder containing batch data
fileetplist = dir(fullfile(datapre, '*.tif'));
k = length(fileetplist);
file_name1 = {fileetplist.name};
disp(file_name1);
%% Data storage
predata = [];
for i = 1:k
   [datapre,Rpre] = readgeoraster(fullfile('E:\',file_name1{1,i}));
   predata(:,:,i) = datapre;
end
%% Read data by pixel and import it into the function
clearvars fileetplist datapre
SWAP_f = [];
[a, b, c] = size(predata);
prereshape = reshape(predata, [a*b, c]).'; % Reshape into a matrix of (days ¡Á pixels)
clearvars predata  

% Create a matrix to store SWAP results for each pixel
SWAP_f = NaN(a*b, 4598); % Initialize with NaN

for i = 1:a*b
    % Extract daily data for the current pixel
    pixelData = prereshape(:, i);
    % Call the getSWAP function to calculate SWAP
    pixelSWAP = getSWAP(pixelData);
    if iscolumn(pixelSWAP)
        pixelSWAP = pixelSWAP';
    end
    SWAP_f(i, :) = pixelSWAP;
    disp(['Processed pixel: ', num2str(i)]);
end
%% Output storage
swap = reshape(SWAP_f, [a, b, 4598]); % Reshape SWAP results to match the original image dimensions
[a,R]=readgeoraster('E:\PRE.tif'); % Get projection information first
info=geotiffinfo('E:\PRE.tif');
% Save results
str = 'SWAP';
for i = 210:k
    file_name1{1,i} = [str,file_name1{1,i}(4:end)];
    file_name_s = fullfile('E:\',file_name1{1,i});
    geotiffwrite(file_name_s, swap(:,:,i-209), R, 'GeoKeyDirectoryTag', info.GeoTIFFTags.GeoKeyDirectoryTag);
  
end
