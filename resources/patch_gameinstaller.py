import sys
if __name__ == '__main__':
    infile = sys.argv[1]
    outfile = sys.argv[2]
    with open(infile, 'rb') as inf:
        in_bin = inf.read()
    i = len(in_bin) - 1
    while i >= 0 and in_bin[i] != ord('}'):
        i -= 1
    assert i > 0
    t = 1
    while i > 0 and t > 0:
        i -= 1
        if in_bin[i] == ord('}'):
            t += 1
        elif in_bin[i] == ord('{'):
            t -= 1
    assert t == 0
    
    with open(outfile,'wb') as outf:
        outf.write(b'//' + in_bin[i:])