import sys
outfile = sys.argv[1]
infile1 = sys.argv[2]
infile2 = sys.argv[3]

with open(infile1,'rb') as in1, open(infile2,'rb') as in2, open(outfile,'wb') as of:
    of.write(in1.read())
    of.write(in2.read());