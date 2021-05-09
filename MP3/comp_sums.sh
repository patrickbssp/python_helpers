md5sum Take1/* > Take1.md5; md5sum Take2/* > Take2.md5; tkdiff Take1.md5 Take2.md5;sed s/Take2/Take1/ Take2.md5 > Take2_ed.md5;mv Take2_ed.md5 Take2.md5; tkdiff Take1.md5 Take2.md5
md5sum *.wav > wav.md5; more wav.md5
