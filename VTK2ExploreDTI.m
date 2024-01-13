% function A
track_file = 'example-UKF-data.vtk';
[VERT,tracks] = VTKImport(track_file);
ref_file = '';
if(~isempty(ref_file))
    [FA,VDims] = E_DTI_read_nifti_file(ref_file);
else
    VDims = [1 1 1];
    min_p = min(VERT);
    max_p = max(VERT);
    range = round((max_p-min_p)./VDims);
    FA = zeros(range);
    E_DTI_Make_fake_DTI_mat_file_for_ExploreDTI(FA,VDims,[track_file(1:end-4) '_fakeDTI.mat']);
end

min_p = min(VERT);
VERT = VERT-min_p+1;

Tracts = cell(1,length(tracks));
TractL = cell(1,length(tracks));
TractFA = cell(1,length(tracks));
TractFE = cell(1,length(tracks));
TractAng = cell(1,length(tracks));
TractGEO = cell(1,length(tracks));
TractLambdas = cell(1,length(tracks));
TractMD = cell(1,length(tracks));

for tid=1:length(Tracts) 
    indices = tracks{tid};
    tract = VERT(indices,:);
    tract = tract(:,[2 1 3]);  
    tract(:,1) = size(FA,1)-tract(:,1);
%     tract(:,2) = size(FA,2)-tract(:,2);

%     tract = ResampleTract(tract,min(VDims)/2);
    
    Tracts(tid) = {tract};
    lFA = zeros(size(tract,1),1);
    lFE = zeros(size(tract,1),3);
    for ij=1:size(tract,1)
        P = tract(ij,:);
        P = round(P./VDims);
        lFA(ij) = 0.7;%FA(P(1),P(2),P(3));
        if(ij == 1)
            lFE(ij,:) = [1 1 1];
            lFE(ij,:) = abs(lFE(ij,:))./norm(lFE(ij,:),2);
        else
            Pn = tract(ij,:);
            Po = tract(ij-1,:);
            V = Pn-Po;
            V = V./sqrt(sum(V.^2));
            V = abs(V);
            lFE(ij,:) = V;
        end
        if(ij > 1)
           Pold = tract(ij-1,:);
        end
    end
    TractL(tid) = {size(tract,1)};
    TractFA(tid) = {lFA};    
    TractFE(tid) = {lFE};
end

BadIndices = false(size(TractL));
for ij=1:length(TractL)
   if(isempty(TractL{ij}) || TractL{ij} < 2)
       BadIndices(ij) = true;
   end
end

GoodIndices = ~BadIndices;
Tracts = Tracts(GoodIndices);
TractL = TractL(GoodIndices);
TractFA = TractFA(GoodIndices);
TractFE = TractFE(GoodIndices);
TractAng = TractAng(GoodIndices);
TractGEO = TractGEO(GoodIndices);
TractLambdas = TractLambdas(GoodIndices);
TractMD = TractMD(GoodIndices);

FList = (1:length(Tracts))';

save([track_file(1:end-4) '.mat'],'Tracts','TractL','TractFA','TractFE',...
    'TractAng','TractGEO','TractLambdas','TractMD','FList');
% end

function [VERT,EDGES] = VTKImport(vtk_file)
fid = fopen(vtk_file,'rb');

for ij=1:5
    str = fgets(fid);
end
nvert = sscanf(str,'%*s %d %*s', 1);
% read vertices
VERT = single(fread(fid,nvert*3,'float','b'));

while(~feof(fid) && contains(str,'LINES') < 1)
    str = fgets(fid);
end
nlines = sscanf(str,'%*s %d %d');
EDGES = cell(1,1);
for ij=1:nlines
    K = fread(fid,1,'int','b');
    EDGES(ij) = {fread(fid,K,'*int','b')+1};
end

fclose(fid);

VERT = reshape(VERT,3,nvert);
VERT = VERT';

end