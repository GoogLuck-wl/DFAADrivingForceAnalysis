function SWAP = getSWAP(P)
% getSWAP function is used to calculate SWAP;
% a is the weight decay parameter [0,1];
daysOfYear = 209;
for t=1:length(P)
    if P(t)<0
        P(t)=NaN;
    end
end
%% Calculate WAP
a = 0.9; % Weight parameter
N = 44;  % Number of periods
omega = zeros(N+1, 1);
for n = 0:N     
    omega(n+1) = (1-a)*a^n;
end
ndays = length(P) - N;
WAP = zeros(ndays, 1);
for idays = 1:ndays    
    for n = 0:N 
        WAP(idays) = WAP(idays) + omega(n+1)*P(idays+N-n);  
    end
end
% Remove the other values from the first year
WAP=WAP(daysOfYear-N+1 :end ,1);
%% Normalize WAP -> SWAP
XS = WAP;
SWAP = zeros(length(XS), 1);
for m=1:length(WAP)
    if isnan(WAP(m))
        SWAP = NaN(length(XS), 1);
    else
       for is = 1:daysOfYear   
           tind = is:daysOfYear:length(XS);    
           Xn = XS(tind);                      
           zeroa = find(Xn == 0);           
           Xn_nozero = Xn;    
           Xn_nozero(zeroa) = [];   
           if any(Xn_nozero < 0) 
               error('Data contains negative values. All values must be non-negative for gamma distribution fitting.');
           end
           if isempty(Xn_nozero)
               continue;
           end
           q = length(zeroa) / length(Xn);
           parm = gamfit(Xn_nozero);    
           Gam_xs = q + (1-q) * gamcdf(Xn, parm(1), parm(2));    
           SWAP(tind) = norminv(Gam_xs);
       end
    end
end    
end