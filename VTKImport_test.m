fid = fopen('example-UKF-data.vtk','rb');

str = fgets(fid);
str = fgets(fid);
str = fgets(fid);
str = fgets(fid);
str = fgets(fid);
nvert = sscanf(str,'%*s %d %*s', 1);
sp = ftell(fid);
% read vertices
A = single(fread(fid,nvert*3,'float','b'));
mp = ftell(fid);

str = fgets(fid);
str = fgets(fid);
nlines = sscanf(str,'%*s %d %d');
lines = cell(1,1);
for ij=1:nlines
    K = fread(fid,1,'int','b');
    lines(ij) = {fread(fid,K,'*int','b')};
end
% B = fread(fid,[nlines(1) 4],'*uint8','b');
pstr = fgets(fid);
mmp = ftell(fid);

fclose(fid);

A = reshape(A,3,nvert);
A = A';

% figure
% hold on
% for ij=1:length(lines)
% plot3(A(lines{ij}+1,1),A(lines{ij}+1,2),A(lines{ij}+1,3),'.-r');
% end
% plot3(A(1:10:end,1),A(1:10:end,2),A(1:10:end,3),'.r')
